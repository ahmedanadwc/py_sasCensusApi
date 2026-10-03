from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# Ensure 'src' is in sys.path so py_sascensusapi can be imported without pip install -e .
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path and SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from py_sascensusapi.config import (
    SAS_PROJECT_ROOT,
    DEFAULT_DATA_JSON_URL,
    DEFAULT_OUT_LIB,
    DEFAULT_OUT_DS,
    DEFAULT_MAX_VAR_COUNT,
    DEFAULT_SAS_CFGFILE,
)
from py_sascensusapi.sas_backend import sas_backend
from py_sascensusapi.census_catalog import search_datasets

# Page Configuration
st.set_page_config(
    page_title="US Census SAS API Studio - Setup & Query Wizard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern, premium appearance
st.markdown(
    """
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Studio Header */
    .studio-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #3b82f6 100%);
        color: white;
        padding: 24px 28px;
        border-radius: 12px 12px 0 0;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
        margin-bottom: 0;
    }
    .studio-header h1 {
        margin: 0;
        color: #ffffff !important;
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.3px;
    }
    .studio-header p {
        margin: 4px 0 0 0;
        color: #dbeafe !important;
        font-size: 13.5px;
    }
    .studio-header .badge {
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(6px);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        color: #f8fafc;
        border: 1px solid rgba(255, 255, 255, 0.28);
        font-weight: 500;
    }

    /* Step Navigation Bar */
    .step-nav-bar {
        background: #f8fafc;
        border-left: 1px solid #cbd5e1;
        border-right: 1px solid #cbd5e1;
        border-bottom: 2px solid #e2e8f0;
        padding: 12px 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 0;
    }

    /* Content Card Wrapper */
    .step-card-wrapper {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-top: none;
        border-radius: 0 0 12px 12px;
        padding: 28px;
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.06), 0 8px 10px -6px rgba(0,0,0,0.04);
        margin-bottom: 24px;
    }

    /* Status Badges */
    .status-badge-connected {
        display: inline-block;
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #86efac;
    }
    .status-badge-disconnected {
        display: inline-block;
        background-color: #f1f5f9;
        color: #475569;
        padding: 4px 12px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 13px;
        border: 1px solid #cbd5e1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "step" not in st.session_state:
    st.session_state.step = 0
if "endpoint_selected" not in st.session_state:
    st.session_state.endpoint_selected = False
if "sas_connected" not in st.session_state:
    st.session_state.sas_connected = False
if "sas_status_msg" not in st.session_state:
    st.session_state.sas_status_msg = "⚪ SAS Disconnected (Preview & Code Export mode)"
if "env_init_msg" not in st.session_state:
    st.session_state.env_init_msg = ""
if "step1_result" not in st.session_state:
    st.session_state.step1_result = None
if "step2_result" not in st.session_state:
    st.session_state.step2_result = None
if "step3_result" not in st.session_state:
    st.session_state.step3_result = None
if "step3_selected_vars" not in st.session_state:
    st.session_state.step3_selected_vars = {}
if "step3_query_fields" not in st.session_state:
    st.session_state.step3_query_fields = {}
if "step3_last_example" not in st.session_state:
    st.session_state.step3_last_example = {}
if "step3_vars_grid_gen" not in st.session_state:
    st.session_state.step3_vars_grid_gen = 0
if "step3_result2" not in st.session_state:
    st.session_state.step3_result2 = None

# Step Metadata Definition
STEPS = [
    {"short": "Connect", "full": "🔌 SAS Session", "desc": "Connection & Macro Autocall Setup"},
    {"short": "Catalog", "full": "📂 Collect All Datasets", "desc": "Download & Parse Full Inventory"},
    {"short": "Profile & Query", "full": "🔍 Dataset Info & 📊 Query Builder", "desc": "Metadata & Geography Profile & Chunked Census Data API Query"},
]

# ------------------------------------ Utility Functions ------------------------------------
# ------------------------------------------
# Define a function to set the current step
# ------------------------------------------
def set_step(idx: int):
    st.session_state.step = idx
    st.rerun()

# ------------------------------------------------------------------------------------------------------
# Define a function to determine the highest unlocked step based on SAS connection and previous results
# ------------------------------------------------------------------------------------------------------
def highest_unlocked_step(
    sas_connected: bool,
    step2_result: dict | None,
) -> int:
    def result_succeeded(result: dict | None) -> bool:
        return (
            isinstance(result, dict)
            and isinstance(result.get("res"), dict)
            and bool(result["res"].get("success"))
        )

    if not sas_connected:
        return 0
    if not result_succeeded(step2_result):
        return 1
    return 2

# -----------------------------------------------------------------------------------
# Define a function to extract SAS_config_names from a specified configuration file
# -----------------------------------------------------------------------------------
def extract_sas_config_names(config_path: str) -> list[str]:
    """Extract SAS_config_names from a SASPy configuration file.
    The configuration file is parsed without executing it.
    """
    import ast

    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            is_target = any(
                isinstance(target, ast.Name)
                and target.id == "SAS_config_names"
                for target in node.targets
            )

            if not is_target:
                continue

            try:
                value = ast.literal_eval(node.value)
            except (ValueError, SyntaxError) as exc:
                raise ValueError(
                    "SAS_config_names must contain a literal list or tuple."
                ) from exc

            if not isinstance(value, (list, tuple)):
                raise TypeError(
                    "SAS_config_names must be defined as a list or tuple."
                )

            if not all(isinstance(name, str) for name in value):
                raise TypeError(
                    "Every item in SAS_config_names must be a string."
                )

            return list(value)

    raise KeyError(
        f"SAS_config_names was not found in configuration file: {path}"
    )

#------------------------------------------------------------------------------------
# Define a helper function to normalize a selected row from AgGrid into a dictionary
#--------------------------------------------------------------------------------------------------
# Define a function to read a column value from the selected Step 2 row (case-insensitive)
#--------------------------------------------------------------------------------------------------
def selected_row_value(column: str, default: str = "") -> str:
    """Return the selected catalog row's value for a column, or default if unset/missing."""
    row = st.session_state.get("selected_row") or {}
    for name, value in row.items():
        if str(name).lower() == column.lower():
            return default if value is None or pd.isna(value) else str(value)
    return default

#------------------------------------------------------------------------------------
def normalize_selected_row(selected_rows) -> dict | None:
    """Return the first selected AgGrid row as a dictionary."""
    if selected_rows is None:
        return None

    if isinstance(selected_rows, pd.DataFrame):
        if selected_rows.empty:
            return None
        return selected_rows.iloc[0].to_dict()

    if isinstance(selected_rows, list):
        return selected_rows[0] if selected_rows else None

    if isinstance(selected_rows, dict):
        return selected_rows

    return None

#--------------------------------------------------------------------------------------------------
# Define a function to find the index of a row in a DataFrame based on a normalized row dictionary
#--------------------------------------------------------------------------------------------------
def find_row_index(
    data: pd.DataFrame,
    normalized_row: dict | None,
    key_column: str = "_ROWID_",
) -> int | None:
    """Find the positional DataFrame row index matching a selected row."""
    if not normalized_row or key_column not in data.columns:
        return None

    selected_key = normalized_row.get(key_column)
    matches = data.index[data[key_column].eq(selected_key)]

    if len(matches) == 0:
        return None

    return data.index.get_loc(matches[0])

#--------------------------------------------------------------------------------------------------
# Step 3 result tables created by %censusapi_getDsFullInfo in APILIB.
# Names look like <libref>_<ds_unique_id>_<suffix>, e.g. APILIB._45_CPS_1995_VARS
#--------------------------------------------------------------------------------------------------
STEP3_LIBREF = "APILIB"
STEP3_TABS = [
    ("Variables", "_VARS"),
    ("Groups", "_GRPS"),
    ("Geographies", "_GEOS"),
    ("Sample Queries", "_EXMPLS"),
]

#--------------------------------------------------------------------------------------------------
# Define a function to find the Step 3 table names for a dataset row id
#--------------------------------------------------------------------------------------------------
def find_step3_tables(ds_unique_id: str) -> dict[str, str]:
    """Map each tab label to its APILIB table name by scanning SASHELP.VTABLE.

    A table matches when its name ends with <ds_unique_id><suffix>, with the
    ds_unique_id sanitized the way SAS builds member names (non-word chars -> "_").
    """
    uid = re.sub(r"\W", "_", str(ds_unique_id).strip()).upper()
    if not uid:
        return {}
    members = sas_backend.fetch_dataframe(
        "VTABLE", "SASHELP", ds_opts={"WHERE": f"(libname='{STEP3_LIBREF}')"}
    )
    if members is None or members.empty:
        return {}
    memname_col = next((c for c in members.columns if c.lower() == "memname"), None)
    if memname_col is None:
        return {}
    names = [str(n).strip() for n in members[memname_col]]
    found = {}
    for label, suffix in STEP3_TABS:
        for name in names:
            if name.upper().endswith(f"{uid}{suffix}"):
                found[label] = name
                break
    return found

#--------------------------------------------------------------------------------------------------
# Define helpers to turn grid selections into a comma delimited list of Name values
#--------------------------------------------------------------------------------------------------
def selected_rows_to_list(selected_rows) -> list[dict]:
    """Normalize an AgGrid selected_rows value (DataFrame, list or None) to a list of dicts."""
    if selected_rows is None:
        return []
    if isinstance(selected_rows, pd.DataFrame):
        return selected_rows.to_dict("records")
    if isinstance(selected_rows, dict):
        return [selected_rows]
    return list(selected_rows)


def names_to_csv(rows: list[dict], column: str = "Name") -> str:
    """Join the (case-insensitive) `column` values of the selected rows into a comma delimited string."""
    names: list[str] = []
    for row in rows:
        key = next((k for k in row if str(k).lower() == column.lower()), None)
        value = "" if key is None or row[key] is None else str(row[key]).strip()
        if value and value not in names:
            names.append(value)
    return ",".join(names)

#--------------------------------------------------------------------------------------------------
# Define a function to split a sample Census API URL into the Step 3 query form fields
#--------------------------------------------------------------------------------------------------
def parse_example_url(url: str) -> dict[str, str]:
    """Split an in_exampleURL value into base_url, get, for and in clauses (clauses keep their `name=` prefix).

    Multiple in= parameters are joined with "&"; key= and any other parameters are ignored.
    """
    base, _, query = str(url).strip().partition("?")
    parsed = {"base_url": f"{base}?" if base else "", "get": "", "for": "", "in": ""}
    in_clauses: list[str] = []
    for part in query.split("&"):
        name, _, value = part.partition("=")
        name, value = name.strip().lower(), unquote(value.strip())
        if name == "get":
            parsed["get"] = f"get={value}"
        elif name == "for":
            parsed["for"] = f"for={value}"
        elif name == "in":
            in_clauses.append(f"in={value}")
    parsed["in"] = "&".join(in_clauses)
    return parsed

#--------------------------------------------------------------------------------------------------
# Define a function to display a DataFrame in an AgGrid (optionally with row selection)
#--------------------------------------------------------------------------------------------------
def render_grid(
    df: pd.DataFrame,
    key: str,
    height: int = 450,
    selection_mode: str | None = None,
    pre_selected_rows: list[int] | None = None,
):
    """Show a DataFrame in an AgGrid sized to its cell contents; returns the AgGrid result."""
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(filter=True, sortable=True, resizable=True)
    if selection_mode:
        gb.configure_selection(
            selection_mode=selection_mode,
            use_checkbox=True,
            pre_selected_rows=pre_selected_rows or [],
        )
    auto_size_columns = JsCode(
        """
        function(params) {
            const columnIds = [];
            params.api.getAllGridColumns().forEach(column => {
                columnIds.push(column.getColId());
            });
            params.api.autoSizeColumns(columnIds, false);
        }
        """
    )
    grid_options = gb.build()
    grid_options["autoSizeStrategy"] = {"type": "fitCellContents"}
    grid_options["suppressColumnVirtualisation"] = True
    grid_options["onGridReady"] = auto_size_columns
    grid_options["firstDataRendered"] = auto_size_columns
    # Grids in inactive tabs are hidden (zero width) when they first render, so the
    # initial autosize measures nothing; re-run it when the grid becomes visible.
    grid_options["onGridSizeChanged"] = auto_size_columns
    extra = {"update_on": ["selectionChanged"]} if selection_mode else {}
    return AgGrid(
        df,
        gridOptions=grid_options,
        height=height,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        key=key,
        **extra,
    )

# ------------------------------------ End Utility Functions ------------------------------------

# -----------------------------------------------------------------------------
# Sidebar: Quick Navigation & Session Summary
# -----------------------------------------------------------------------------
unlocked_step = highest_unlocked_step(
    sas_backend.is_connected,
    st.session_state.step2_result,
)

with st.sidebar:
    st.markdown("### 🏛️ Wizard Navigator")
    for i, s in enumerate(STEPS):
        is_active = (st.session_state.step == i)
        prefix = "👉 " if is_active else "   "
        if st.button(
            f"{prefix}Step {i+1}: {s['short']}",
            key=f"nav_btn_{i}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            disabled=i > unlocked_step,
        ):
            if i <= unlocked_step:
                set_step(i)

    st.markdown("---")
    st.markdown("### 🔌 SAS Session Status")
    if sas_backend.is_connected:
        st.success(f"Connected: {sas_backend._cfgname}")
    else:
        st.info("Disconnected (Offline / Code Export Mode)")

    st.markdown("---")
    st.caption(f"📁 **Root**: `{SAS_PROJECT_ROOT.name}`")

# -----------------------------------------------------------------------------
# Header Banner
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="studio-header">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 16px;">
                <span style="font-size: 38px; line-height: 1;">🏛️</span>
                <div>
                    <h1>US Census SAS API Studio</h1>
                    <p>Windows Wizard for Configuring & Executing Census API SAS Macros via SASPy</p>
                </div>
            </div>
            <div class="badge">
                Wizard Flow: Step-by-Step Orchestrator
            </div>
        </div>
    </div>
    <div class="step-nav-bar">
        <div style="font-size: 14px; font-weight: 600; color: #334155;">
            Wizard Navigation:
        </div>
        <div style="font-size: 13px; color: #64748b; font-weight: 500;">
            Step {st.session_state.step + 1} of {len(STEPS)}: <strong>{STEPS[st.session_state.step]['full']}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Container for step contents
card = st.container()

with card:
    # -------------------------------------------------------------------------
    # STEP 1: SASPy Connection & Environment Setup
    # -------------------------------------------------------------------------
    if st.session_state.step == 0:
        st.markdown("### 🔌 Step 1: SASPy Connection & Environment Setup")
        st.markdown(
            "Connect to your SAS instance and configure the required macro autocall directories, "
            "global macro variables, and libnames."
        )

        # Connection status banner
        if sas_backend.is_connected:
            st.markdown(f'<span class="status-badge-connected">🟢 Connected to SAS ({sas_backend._cfgname})</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="status-badge-disconnected">{st.session_state.sas_status_msg}</span>', unsafe_allow_html=True)

        st.markdown("")

        # Connection controls
        s1_col_l, s1_col_r = st.columns([1, 1])
        with s1_col_l:
            cfgfile_input = st.text_input(
                "Custom sascfg File Path (cfgfile)",
                value=DEFAULT_SAS_CFGFILE,
                placeholder=r"e.g. C:\Users\user\sascfg_personal.py",
                key="step1_cfgfile"
            )
            cfg_select = st.selectbox(
                "SAS Configuration (cfgname)",
                #options=["oda", "ssh", "default"],
                options=extract_sas_config_names(cfgfile_input),
                index=0,
                key="step1_cfg_select",
            )
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔌 Connect to SAS", type="primary", use_container_width=True):
                with st.spinner("Connecting to SAS via SASPy..."):
                    success, msg = sas_backend.connect(
                        cfgname=cfg_select,
                        cfgfile=st.session_state.get("step1_cfgfile", DEFAULT_SAS_CFGFILE),
                    )
                    st.session_state.sas_status_msg = (
                        f"🟢 Connected to SAS ({sas_backend._cfgname})" if success else f"🔴 {msg}"
                    )
                    st.session_state["sas_connected"] = success
                st.rerun()
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔌 Disconnect", use_container_width=True):
                msg = sas_backend.disconnect()
                st.session_state.pop("step3_autoload_uid", None)
                st.session_state.sas_status_msg = f"⚪ {msg}"
                st.session_state["sas_connected"] = False
                st.session_state.env_init_msg = ""
                st.session_state.step = 0
                st.rerun()

        # -------------------------------------------------------------------------
        # UI that should only appear after a successful SAS connection
        # -------------------------------------------------------------------------
        if sas_backend.is_connected:

            # -----------------------------------------------------------------
            # Initialise SAS Autocall & libnames (still inside the guard)
            # -----------------------------------------------------------------
            with s1_col_r:
                st.markdown("#### ⚙️ Session Environment Parameters")

                proj_path_input = st.text_input(
                    "SAS Project Root Path (contains code/macros, data, output)",
                    value=str(SAS_PROJECT_ROOT),
                    key="step1_proj_path",
                )

                api_key_input = st.text_input(
                    "Census API Key (masked, assigned to global &g_apiKey)",
                    value=st.session_state.get("step1_api_key", ""),
                    type="password",
                    key="step1_api_key",
                    help="Optional API key from api.census.gov/data/key_signup.html",
                )
                if st.button(
                    "⚙️ Initialize SAS Autocall & Libnames",
                    type="secondary",
                    use_container_width=True,
                ):
                    if not sas_backend.is_connected:
                        st.warning("⚠️ Connect to SAS first before initializing the macro environment.")
                    else:
                        with st.spinner("Setting up SAS environment & macro paths..."):
                            env_res = sas_backend.run_environment_setup(proj_path_input, api_key_input)
                            st.session_state.env_init_msg = (
                                "✅ Macro Autocall paths and APILIB libname successfully initialized!"
                                if env_res["success"]
                                else "⚠️ Setup finished with warnings/errors. Check log."
                            )
                            st.session_state.step1_result = {"res": env_res}
                        st.rerun()

                # Show any init‑message
                if st.session_state.env_init_msg:
                    st.info(st.session_state.env_init_msg)

                # Show SAS log if a step‑1 run already happened
                if st.session_state.step1_result is not None:
                    env_res = st.session_state.step1_result["res"]
                    with st.expander(
                        f"📋 SAS Log ({len(env_res.get('log', '').splitlines())} lines)",
                        expanded=False,
                    ):
                        st.code(env_res.get("log", ""), language="sas")

        st.markdown("---")

        s1_col_tip, s1_col_next = st.columns([3, 1])
        with s1_col_tip:
            st.caption("💡 *Tip: If running offline without SAS, you can still configure parameters and download SAS scripts in subsequent steps.*")
        with s1_col_next:
            if st.button("Next: Collect Dataset Catalog >", type="primary", use_container_width=True):
                if unlocked_step >= 1:
                    set_step(1)

    # -------------------------------------------------------------------------
    # STEP 2: Collect All Datasets (%censusapi_getAllDataSets)
    # -------------------------------------------------------------------------
    elif st.session_state.step == 1:
        st.markdown("### 📂 Step 2: Collect All Datasets (%censusapi_getAllDataSets)")
        st.markdown(
            "Downloads the official Census `data.json` catalog, parses all available API endpoints, vintages, "
            "and titles into a SAS master dataset (`APILIB._API_ALL_DATA`), and produces an Excel inventory."
        )
        # ------------------------------
        # Display form for Step 2 inputs (full width, fields in two columns)
        # ------------------------------
        with st.form("step2_form"):
            s2_f_left, s2_f_right = st.columns(2)
            with s2_f_left:
                p_outLibName = st.text_input("Output SAS Library (p_outLibName)", value=DEFAULT_OUT_LIB)
                p_dataJsonURL = st.text_input("Census Catalog JSON URL (p_dataJsonURL)", value=DEFAULT_DATA_JSON_URL)
            with s2_f_right:
                p_outDsName = st.text_input("Output Dataset Name (p_outDsName)", value=DEFAULT_OUT_DS)
                p_reportOutputPath = st.text_input("Report Output Path (p_reportOutputPath)", value="&g_outputRoot")
            submit_step2 = st.form_submit_button("▶ Submit & Run in SAS", type="primary")
        # -------------------------------------------
        # Display the results of submitting the form
        # -------------------------------------------
        with st.container():
            sas_code_step2 = f"""/* Step 2: Collect all Census Data API datasets metadata */
    %censusapi_getAllDataSets(
        p_outLibName={p_outLibName}
    , p_outDsName={p_outDsName}
    , p_dataJsonURL=%str({p_dataJsonURL})
    , p_reportOutputPath={p_reportOutputPath}
    );
    """
            s2_col_l, s2_col_r = st.columns([1, 1])
            with s2_col_l:
                if submit_step2:
                    if not sas_backend.is_connected:
                        st.warning("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
                    else:
                        with st.spinner("Running %censusapi_getAllDataSets in SAS..."):
                            res = sas_backend.submit_code(sas_code_step2)
                            # Fetch only seleced columns for preview
                            df = sas_backend.fetch_dataframe(p_outDsName, p_outLibName, ds_opts={"KEEP": "_rowid_ ds_unique_id baseurl c_vintage title description modified Spatial microdata_i"}) if res.get("success", False) else None
                            # Store the result in session state
                            st.session_state.step2_result = {
                                "res": res,
                                "df": df,
                                "lib": p_outLibName,
                                "ds": p_outDsName,
                            }

                # Show execution results if available
                if st.session_state.step2_result:
                    r = st.session_state.step2_result["res"]
                    if r.get("success", False):
                        st.success("✅ **Step 2 Macro executed successfully!** (0 SAS errors)")
                    elif r.get("fetched", False):
                        st.success("✅ **Step 2: Fetched existing SAS data set**")
                    else:
                        st.error(f"❌ **Macro finished with errors** ({len(r.get('errors', []))} error lines found)")

                    with st.expander(f"📋 SAS Log ({len(r.get('log', '').splitlines())} lines)", expanded=False):
                        st.code(r.get("log", ""), language="sas")
            with s2_col_r:
                with st.expander("📝 Generated SAS Code Preview & Download", expanded=False):
                    st.code(sas_code_step2, language="sas")
                    st.download_button(
                        label="💾 Download .sas Script",
                        data=sas_code_step2.encode("utf-8"),
                        file_name="step2_getAllDataSets.sas",
                        mime="text/plain",
                    )
        # ------------------------------------------------------------------------
        # Check for existing dataset only once if not already fetched or executed
        # ------------------------------------------------------------------------
        if st.session_state.step2_result is None and sas_backend.is_connected:
            # Fetch only seleced columns for preview
            existing_df = sas_backend.fetch_dataframe(p_outDsName, p_outLibName, ds_opts={"KEEP": "_rowid_ ds_unique_id baseurl c_vintage title description modified Spatial microdata_i"})

            if existing_df is not None and not existing_df.empty:
                st.session_state.step2_result = {
                    "res": {
                        "success": True,
                        "fetched": True,
                        "log": f"/* Loaded existing dataset {p_outLibName}.{p_outDsName} from active SAS session */",
                        "errors": [],
                    },
                    "df": existing_df,
                    "lib": p_outLibName,
                    "ds": p_outDsName,
                }

        # ------------------------------------
        # Show execution results if available
        # ------------------------------------
        if st.session_state.step2_result:
            df = st.session_state.step2_result.get("df")
            if df is not None and not df.empty:
                persisted_row = st.session_state.get("selected_row")
                selected_index = find_row_index(
                    df,
                    persisted_row,
                    key_column="_ROWID_",
                )
                if selected_index is None:
                    persisted_index = st.session_state.get("selected_index")
                    if isinstance(persisted_index, int) and 0 <= persisted_index < len(df):
                        selected_index = persisted_index

                st.markdown(f"#### 📊 Dataset Preview: `{st.session_state.step2_result['lib']}.{st.session_state.step2_result['ds']}` ({len(df)} rows, {len(df.columns)} columns)")
                # Build selectable grid using AgGrid
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_selection(
                    selection_mode="single",
                    use_checkbox=False,
                    pre_selected_rows=(
                        [selected_index] if selected_index is not None else []
                    ),
                )
                auto_size_columns = JsCode(
                    """
                    function(params) {
                        const columnIds = [];
                        params.api.getAllGridColumns().forEach(column => {
                            columnIds.push(column.getColId());
                        });
                        params.api.autoSizeColumns(columnIds, false);
                    }
                    """
                )
                grid_options = gb.build()
                grid_options["autoSizeStrategy"] = {"type": "fitCellContents"}
                grid_options["suppressColumnVirtualisation"] = True
                grid_options["onGridReady"] = auto_size_columns
                grid_options["firstDataRendered"] = auto_size_columns
                grid_res = AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_on=["selectionChanged"],
                    height=400,
                    fit_columns_on_grid_load=False,
                    allow_unsafe_jscode=True,
                    key="data-grid-step2"
                )

                #---------------------------------------------------------------
                # Get selected row and display it
                #---------------------------------------------------------------
                selected_row = normalize_selected_row(grid_res.get("selected_rows", None))
                if selected_row is None:
                    selected_row = persisted_row
                if selected_row is None and selected_index is not None:
                    selected_row = df.iloc[selected_index].to_dict()

                if selected_row is not None:
                    row_id = selected_row["_ROWID_"]
                    ds_unique_id = selected_row["ds_unique_id"]
                    selected_index = find_row_index(
                        df,
                        selected_row,
                        key_column="_ROWID_",
                    )
                    # Store the selected row and index in session state for persistence across steps
                    st.session_state["selected_index"] = selected_index
                    st.session_state["selected_row"] = selected_row
                    st.session_state["selected_row_id"] = row_id
                    st.session_state["selected_ds_unique_id"] = ds_unique_id

                    # ---------------------------------------------------
                    # Display selected row details in a two-column layout
                    # ---------------------------------------------------
                    st.subheader("Selected row")
                    left_column, right_column = st.columns([1,2])
                    with left_column:
                        st.text_input("Rowid",value=str(selected_row.get("_ROWID_", "")),disabled=False)
                        st.text_input("Dataset Unique ID",value=str(selected_row.get("ds_unique_id","")),disabled=False)
                        st.text_input("Base URL",value=str(selected_row.get("BaseURL", "")),disabled=False)
                        st.text_input("Collection Vintage",value=str(selected_row.get("c_vintage", "")),disabled=False)
                        st.text_input("Modified",value=str(selected_row.get("modified", "")),disabled=False)
                        st.text_input("Spatial",value=str(selected_row.get("spatial", "")),disabled=False,)
                        st.text_input("Microdata ID",value=str(selected_row.get("Microdata_i", "")),disabled=False)
                    with right_column:
                        st.text_input("Title",value=str(selected_row.get("title", "")),disabled=False)
                        st.text_area("Description",value=str(selected_row.get("description", "")),height=400, disabled=False)

        st.markdown("---")
        s2_col_back, s2_col_next = st.columns([1, 1])
        with s2_col_back:
            if st.button("< Back: SAS Connection", use_container_width=True):
                set_step(0)
        with s2_col_next:
            if st.button("Next: Dataset Profile & Query Builder>", type="primary", use_container_width=True):
                if unlocked_step >= 2:
                    set_step(2)

    # -------------------------------------------------------------------------
    # STEP 3: Dataset Profile & Metadata (%censusapi_getDsFullInfo)
    #       : & Data API Query Builder (%censusapi_submitDataApiQuery)
    # -------------------------------------------------------------------------
    elif st.session_state.step == 2:
        st.markdown("### 🔍& 📊 Step 3: Dataset Info (%censusapi_getDsFullInfo) & Data API Query Builder (%censusapi_submitDataApiQuery)")
        st.markdown(
            "Pulls complete metadata for a specific dataset row from `_API_ALL_DATA`, including all supported variables, "
            "valid geography levels, and sample API queries into individual SAS tables and an Excel report."
            "Submits requests to the Census Data API, automatically splitting large variable lists into chunks "
            "(up to `p_maxVarCount` variables per call), parsing JSON responses into SAS datasets, and merging the chunks."
        )

        # ------------------------------
        # Display form for Step 3 inputs (full width, fields in two columns)
        # ------------------------------
        with st.form("step3_form"):
            s3_f1_left, s3_f1_right = st.columns(2)
            with s3_f1_left:
                p_apiListingLibName = st.text_input("Catalog Libname (p_apiListingLibName)", value=DEFAULT_OUT_LIB)
                p_apiListingDsName = st.text_input("Catalog Dataset Name (p_apiListingDsName)", value=DEFAULT_OUT_DS)
                submit_step3_1 = st.form_submit_button("▶ Submit & Run in SAS", type="primary")
            with s3_f1_right:
                selected_row_id = st.session_state.get("selected_row_id", 3)
                # Key on the selected row so the field resets when a different dataset is picked in Step 2
                p_dsRowId = st.text_input("Dataset _ROWID_ (p_dsRowId)", value=f"{selected_row_id}", key=f"step3_row_id_{selected_row_id}")
                p_reportOutputPath = st.text_input("Report Output Path (p_reportOutputPath)", value="&g_outputRoot", key="step3_out_path")
                reuse_step3 = st.checkbox(
                    "Reuse existing profile tables (skip the SAS macro if all four exist)", value=True, key="step3_reuse"
                )
        # -------------------------------------------
        # Display the results of submitting the form
        # -------------------------------------------

        s3_col_l, s3_col_r = st.columns(2)

        with s3_col_l:
            sas_code_step3_1 = f"""/* Step 3.1: Compose complete Profile of the specified dataset */
    %censusapi_getDsFullInfo(
        p_apiListingLibName={p_apiListingLibName}
    , p_apiListingDsName={p_apiListingDsName}
    , p_dsRowId={p_dsRowId}
    , p_reportOutputPath={p_reportOutputPath}
    );
    """
            if submit_step3_1:
                if not sas_backend.is_connected:
                    st.warning("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
                else:
                    uid = st.session_state.get("selected_ds_unique_id", "")
                    existing = find_step3_tables(uid) if reuse_step3 else {}
                    if len(existing) == len(STEP3_TABS):
                        res = {
                            "success": True, "has_errors": False, "errors": [], "warnings": [], "lst": "",
                            "log": "Reused existing APILIB profile tables; %censusapi_getDsFullInfo was not re-run.",
                        }
                        found = existing
                    else:
                        with st.spinner("Running %censusapi_getDsFullInfo in SAS..."):
                            res = sas_backend.submit_code(sas_code_step3_1)
                            found = find_step3_tables(uid) if res["success"] else {}
                    with st.spinner("Loading profile tables..."):
                        tables = {
                            label: (table, sas_backend.fetch_dataframe(table, STEP3_LIBREF))
                            for label, table in found.items()
                        }
                    st.session_state.step3_result = {"res": res, "tables": tables, "uid": uid}

            # Auto-load cached profile tables that match the selected ds_unique_id
            current_uid = str(st.session_state.get("selected_ds_unique_id", "") or "")
            loaded = st.session_state.step3_result
            if (
                sas_backend.is_connected
                and current_uid
                and (loaded or {}).get("uid") != current_uid
                and st.session_state.get("step3_autoload_uid") != current_uid
            ):
                st.session_state.step3_autoload_uid = current_uid
                with st.spinner("Checking SAS for existing profile tables..."):
                    found = find_step3_tables(current_uid)
                    if found:
                        st.session_state.step3_result = {
                            "res": {
                                "success": True, "has_errors": False, "errors": [], "warnings": [], "lst": "",
                                "log": f"Loaded existing APILIB profile tables for {current_uid}; macro not re-run.",
                            },
                            "tables": {
                                label: (table, sas_backend.fetch_dataframe(table, STEP3_LIBREF))
                                for label, table in found.items()
                            },
                            "uid": current_uid,
                        }
                    elif loaded and loaded.get("uid") != current_uid:
                        st.session_state.step3_result = None

            if st.session_state.step3_result:
                r = st.session_state.step3_result["res"]
                if r["success"]:
                    st.success("✅ **Step 3.1 Profile executed successfully!** (0 SAS errors)")
                else:
                    st.error(f"❌ **Execution finished with errors** ({len(r.get('errors', []))} error lines found)")

                with st.expander(f"📋 SAS Log ({len(r.get('log', '').splitlines())} lines)", expanded=False):
                    st.code(r.get("log", ""), language="sas")

        with s3_col_r:
            with st.expander("📝 Generated SAS Code Preview", expanded=False):
                st.code(sas_code_step3_1, language="sas")
                st.download_button(
                    label="💾 Download .sas Script",
                    data=sas_code_step3_1.encode("utf-8"),
                    file_name="step3_getDsFullInfo.sas",
                    mime="text/plain",
                )

        # ------------------------------------
        # Profile tables: one grid per tab
        # ------------------------------------
        step3_result = st.session_state.step3_result
        if step3_result and step3_result["res"]["success"]:
            tables = step3_result.get("tables", {})
            tabs = st.tabs([label for label, _ in STEP3_TABS])
            for tab, (label, suffix) in zip(tabs, STEP3_TABS):
                with tab.container():
                    table, df = tables.get(label, (None, None))
                    if table is None:
                        st.info(f"No `{STEP3_LIBREF}` table ending in `{suffix}` was found for this dataset.")
                    elif df is None:
                        st.info(f"Table `{STEP3_LIBREF}.{table}` could not be loaded from SAS.")
                    elif df.empty:
                        st.info(f"Table `{STEP3_LIBREF}.{table}` has no rows.")
                    else:
                        st.caption(f"`{STEP3_LIBREF}.{table}` — {len(df)} rows, {len(df.columns)} columns")
                        if label == "Variables":
                            name_col = next((c for c in df.columns if str(c).lower() == "name"), None)
                            uid_key = str(st.session_state.get("selected_ds_unique_id", ""))
                            chosen = st.session_state.step3_selected_vars.get(uid_key, [])
                            pre = [i for i, n in enumerate(df[name_col]) if str(n).strip() in chosen] if name_col else []
                            gen = st.session_state.step3_vars_grid_gen
                            grid_res = render_grid(
                                df,
                                key=f"data-grid-step3-{label}-{gen}",
                                selection_mode="multiple",
                                pre_selected_rows=pre,
                            )
                            picked = selected_rows_to_list(grid_res.get("selected_rows", None))
                            if picked:
                                names = names_to_csv(picked).split(",")
                                if names != st.session_state.step3_selected_vars.get(uid_key):
                                    st.session_state.step3_selected_vars[uid_key] = names
                                    st.session_state.step3_query_fields.setdefault(uid_key, {})["get"] = "get=" + ",".join(names)
                            n_sel = len(st.session_state.step3_selected_vars.get(uid_key, []))
                            st.caption(f"{n_sel} variable(s) selected - they populate `get=` in the query builder below.")
                            if n_sel and st.button("Clear selected variables", key="step3_clear_vars"):
                                st.session_state.step3_selected_vars[uid_key] = []
                                st.session_state.step3_query_fields.setdefault(uid_key, {})["get"] = "get="
                                st.session_state.step3_vars_grid_gen += 1
                                st.rerun()
                        elif label == "Sample Queries":
                            url_col = next((c for c in df.columns if str(c).lower() == "in_exampleurl"), None)
                            uid_key = str(st.session_state.get("selected_ds_unique_id", ""))
                            last_url = st.session_state.step3_last_example.get(uid_key)
                            pre = [i for i, u in enumerate(df[url_col]) if str(u) == last_url] if url_col and last_url else []
                            grid_res = render_grid(
                                df,
                                key=f"data-grid-step3-{label}",
                                selection_mode="single",
                                pre_selected_rows=pre,
                            )
                            picked = selected_rows_to_list(grid_res.get("selected_rows", None))
                            if picked and url_col:
                                url = str(picked[0].get(url_col, "") or "").strip()
                                if url and url != last_url:
                                    parsed = parse_example_url(url)
                                    fields = st.session_state.step3_query_fields.setdefault(uid_key, {})
                                    fields.update({k: v for k, v in parsed.items() if k != "base_url" or v})
                                    st.session_state.step3_last_example[uid_key] = url
                                    st.rerun()
                            st.caption("Select a sample query to fill the base URL, get=, for= and in= fields below.")
                        else:
                            render_grid(df, key=f"data-grid-step3-{label}")

            if st.button("🔄 Refresh tables from SAS (bypass cache)", key="step3_refresh"):
                for label, (table, _) in tables.items():
                    tables[label] = (table, sas_backend.fetch_dataframe(table, STEP3_LIBREF, force_refresh=True))
                st.rerun()

        st.markdown("---")

        with st.form("step3_form2"):
            # Keys include the selected row so the fields reset when a different dataset is picked in Step 2
            row_key = st.session_state.get("selected_row_id", "none")
            q_fields = st.session_state.step3_query_fields.get(str(st.session_state.get("selected_ds_unique_id", "")), {})

            def field_key(name: str, value: str) -> str:
                # Changing the default (new example/selection) gives the widget a new key so it refreshes
                return f"step3_{name}_{row_key}_{hashlib.md5(value.encode()).hexdigest()[:8]}"

            base_url_default = (q_fields.get("base_url") or selected_row_value("BaseURL")).strip()
            if base_url_default and not base_url_default.endswith("?"):
                base_url_default += "?"
            p_apiBaseURL = st.text_input(
                "API Base URL (p_apiBaseURL)",
                value=base_url_default,
                key=field_key("base_url", base_url_default),
                help="BaseURL of the dataset row selected in Step 2, or of the selected sample query",
            )
            get_default = q_fields.get("get", "get=")
            p_apiGetClause = st.text_area(
                "get= Variables Clause (p_apiGetClause)",
                value=get_default,
                key=field_key("get", get_default),
                help="Populated from the Variables grid selection or the selected sample query",
                height=90,
            )
            col_for, col_in = st.columns(2)
            with col_for:
                for_default = q_fields.get("for", "for=zip code tabulation area (3 digit) (or part):*")
                p_apiForClause = st.text_input(
                    "for= Geography Clause (p_apiForClause)",
                    value=for_default,
                    key=field_key("for", for_default),
                )
            with col_in:
                in_default = q_fields.get("in", "in=state:09,23,25,33,44,50")
                p_apiInClause = st.text_input(
                    "in= Geography Filter Clause (p_apiInClause)",
                    value=in_default,
                    key=field_key("in", in_default),
                )

            col_uid, col_outds = st.columns(2)
            with col_uid:
                p_dsUniqueId = st.text_input(
                    "Dataset Unique ID (p_dsUniqueId)", value=selected_row_value("ds_unique_id"), key=f"step3_ds_uid_{row_key}"
                )
            with col_outds:
                p_outDsName = st.text_input("Output SAS Dataset (p_outDsName)", value="work.sf1_response")

            col_varcnt, col_keyref = st.columns(2)
            with col_varcnt:
                p_maxVarCount = st.slider(
                    "Max Var Count Chunking (p_maxVarCount)",
                    min_value=5,
                    max_value=50,
                    value=DEFAULT_MAX_VAR_COUNT,
                    step=1,
                )
            with col_keyref:
                p_dataApiKey = st.text_input("Census API Key Reference (p_dataApiKey)", value="&g_apiKey")

            submit_step3_2 = st.form_submit_button("▶ Submit & Run in SAS", type="primary")

        # -----------------------------------------------
        # Display the results of submitting the 2nd form
        # -----------------------------------------------
        s3_col_l2, s3_col_r2 = st.columns(2)

        with s3_col_l2:
            sas_code_step3_2 = f"""/* Step 3.2: Submit Census Data API Query with Variable Chunking */
    %censusapi_submitDataApiQuery(
        p_apiBaseURL=%STR({p_apiBaseURL})
    , p_apiGetClause=%STR({p_apiGetClause})
    , p_apiForClause=%bquote({p_apiForClause})
    , p_apiInClause=%bquote({p_apiInClause})
    , p_dsUniqueId={p_dsUniqueId}
    , p_outDsName={p_outDsName}
    , p_dataApiKey={p_dataApiKey}
    , p_maxVarCount={p_maxVarCount}
    );
    """
            if submit_step3_2:
                if not sas_backend.is_connected:
                    st.warning("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
                else:
                    with st.spinner("Submitting chunked API queries via SAS macro..."):
                        res = sas_backend.submit_code(sas_code_step3_2)
                        df = None
                        parts = p_outDsName.split(".")
                        libref = parts[0] if len(parts) > 1 else "WORK"
                        tbl = parts[1] if len(parts) > 1 else parts[0]
                        if res["success"]:
                            df = sas_backend.fetch_dataframe(tbl, libref)
                        st.session_state.step3_result2 = {
                            "res": res,
                            "df": df,
                            "ds_name": p_outDsName,
                        }

            if st.session_state.step3_result2:
                r = st.session_state.step3_result2["res"]
                if r["success"]:
                    st.success("✅ **Step 3.2 Query executed successfully!** (0 SAS errors)")
                else:
                    st.error(f"❌ **Query finished with errors** ({len(r.get('errors', []))} error lines found)")

                with st.expander(f"📋 SAS Log ({len(r.get('log', '').splitlines())} lines)", expanded=False):
                    st.code(r.get("log", ""), language="sas")

                df = st.session_state.step3_result2.get("df")
                if df is not None and not df.empty:
                    st.markdown(f"#### 📊 SAS Dataset Table: `{st.session_state.step3_result2['ds_name']}` ({len(df)} rows, {len(df.columns)} columns)")
                    st.dataframe(df, use_container_width=True)
                elif df is not None and df.empty:
                    st.info(f"ℹ️ Output table `{st.session_state.step3_result2['ds_name']}` exists but is empty.")

        with s3_col_r2:
            with st.expander("📝 Generated SAS Code Preview", expanded=False):
                st.code(sas_code_step3_2, language="sas")
                st.download_button(
                    label="💾 Download .sas Script",
                    data=sas_code_step3_2.encode("utf-8"),
                    file_name="step3_2_submitDataApiQuery.sas",
                    mime="text/plain",
                )

        st.markdown("---")

        s3_col_back, _ = st.columns([1, 1])
        with s3_col_back:
            if st.button("< Back: Collect Datasets", use_container_width=True):
                set_step(1)
