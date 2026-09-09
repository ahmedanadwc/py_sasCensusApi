import os
import sys
from pathlib import Path

# Ensure 'src' is in sys.path so py_sascensusapi can be imported without pip install -e .
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path and SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
if "picked_endpoint" not in st.session_state:
    st.session_state.picked_endpoint = "https://api.census.gov/data/2000/dec/sf1?"
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
if "step5_result" not in st.session_state:
    st.session_state.step5_result = None

# Step Metadata Definition
STEPS = [
    {"short": "Connect", "full": "🔌 SAS Session", "desc": "Connection & Macro Autocall Setup"},
    {"short": "Catalog", "full": "📂 Collect All Datasets", "desc": "Download & Parse Full Inventory"},
    {"short": "Profile", "full": "🔍 Dataset Info", "desc": "Metadata & Geography Profile"},
    {"short": "Search", "full": "🔎 Catalog Quick-Lookup", "desc": "Interactive Search & Endpoint Picker"},
    {"short": "Query", "full": "📊 Query Builder", "desc": "Chunked Census Data API Query"},
]

def set_step(idx: int):
    st.session_state.step = idx
    st.rerun()

def highest_unlocked_step(
    sas_connected: bool,
    step2_result: dict | None,
    step3_result: dict | None,
    endpoint_selected: bool,
    picked_endpoint: str,
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
    if not result_succeeded(step3_result):
        return 2
    if not endpoint_selected:
        return 3
    return 4


# -----------------------------------------------------------------------------
# Sidebar: Quick Navigation & Session Summary
# -----------------------------------------------------------------------------
unlocked_step = highest_unlocked_step(
    sas_backend.is_connected,
    st.session_state.step2_result,
    st.session_state.step3_result,
    st.session_state.endpoint_selected,
    st.session_state.picked_endpoint,
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
    st.caption(f"🔗 **Target**: `{st.session_state.picked_endpoint[:38]}...`")

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
        col_cfg, col_cfgfile = st.columns([1, 2])
        with col_cfg:
            cfg_select = st.selectbox(
                "SAS Configuration (cfgname)",
                options=["oda", "ssh", "default"],
                index=0,
                key="step1_cfg_select",
            )
        with col_cfgfile:
            cfgfile_input = st.text_input(
                "Custom sascfg File Path (cfgfile, optional)",
                value=DEFAULT_SAS_CFGFILE,
                placeholder=r"e.g. C:\Users\user\sascfg_personal.py",
                key="step1_cfgfile"
            )

        col_connBtns = st.columns([1,2])
        with col_connBtns[0]:
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
                st.session_state.sas_status_msg = f"⚪ {msg}"
                st.session_state["sas_connected"] = False
                st.session_state.env_init_msg = ""
                st.session_state.step = 0
                st.rerun()

        st.markdown("---")
        # -------------------------------------------------------------------------
        # UI that should only appear after a successful SAS connection
        # -------------------------------------------------------------------------
        if sas_backend.is_connected:
            st.markdown("---")
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

            # -----------------------------------------------------------------
            # Initialise SAS Autocall & libnames (still inside the guard)
            # -----------------------------------------------------------------
            col_init, _ = st.columns([2, 2])
            with col_init:
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

            # Show SAS log if a step‑1 run already happened
            if st.session_state.step1_result is not None:
                env_res = st.session_state.step1_result["res"]
                with st.expander(
                    f"📋 SAS Log ({len(env_res.get('log', '').splitlines())} lines)",
                    expanded=False,
                ):
                    st.code(env_res.get("log", ""), language="sas")

        # Show any init‑message
        if st.session_state.env_init_msg:
            st.info(st.session_state.env_init_msg)

        st.markdown("---")
        col_tip, col_next = st.columns([3, 1])
        with col_tip:
            st.caption("💡 *Tip: If running offline without SAS, you can still configure parameters and download SAS scripts in subsequent steps.*")
        with col_next:
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

        with st.form("step2_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_outLibName = st.text_input("Output SAS Library (p_outLibName)", value=DEFAULT_OUT_LIB)
            with col2:
                p_outDsName = st.text_input("Output Dataset Name (p_outDsName)", value=DEFAULT_OUT_DS)

            p_dataJsonURL = st.text_input("Census Catalog JSON URL (p_dataJsonURL)", value=DEFAULT_DATA_JSON_URL)
            p_reportOutputPath = st.text_input("Report Output Path (p_reportOutputPath)", value="&g_outputRoot")

            submit_step2 = st.form_submit_button("▶ Submit & Run in SAS", type="primary")

        sas_code_step2 = f"""/* Step 2: Collect all Census Data API datasets metadata */
%censusapi_getAllDataSets(
    p_outLibName={p_outLibName}
  , p_outDsName={p_outDsName}
  , p_dataJsonURL=%str({p_dataJsonURL})
  , p_reportOutputPath={p_reportOutputPath}
);
"""
        # Check for existing dataset only once if not already fetched or executed
        if st.session_state.step2_result is None and sas_backend.is_connected:
            existing_df = sas_backend.fetch_dataframe(p_outDsName, p_outLibName)
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

        if submit_step2:
            if not sas_backend.is_connected:
                st.warning("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
            else:
                with st.spinner("Running %censusapi_getAllDataSets in SAS..."):
                    res = sas_backend.submit_code(sas_code_step2)
                    df = sas_backend.fetch_dataframe(p_outDsName, p_outLibName) if res.get("success", False) else None
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

            df = st.session_state.step2_result.get("df")
            if df is not None and not df.empty:
                st.markdown(f"#### 📊 Dataset Preview: `{st.session_state.step2_result['lib']}.{st.session_state.step2_result['ds']}` ({len(df)} rows, {len(df.columns)} columns)")
                # Build selectable grid using AgGrid
                gb = GridOptionsBuilder.from_dataframe(df)
                gb.configure_selection(selection_mode="single", use_checkbox=False)
                grid_options = gb.build()
                grid_res = AgGrid(
                    df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    height=400,
                    fit_columns_on_grid_load=True,
                )
                selected = grid_res["selected_rows"]
                if selected:
                    st.session_state["selected_row"] = selected[0]

        st.markdown("#### 📝 Generated SAS Code Preview:")
        st.code(sas_code_step2, language="sas")

        st.download_button(
            label="💾 Download .sas Script",
            data=sas_code_step2.encode("utf-8"),
            file_name="step2_getAllDataSets.sas",
            mime="text/plain",
        )

        st.markdown("---")
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("< Back: SAS Connection", use_container_width=True):
                set_step(0)
        with col_next:
            if st.button("Next: Dataset Profile >", type="primary", use_container_width=True):
                if unlocked_step >= 2:
                    set_step(2)

    # -------------------------------------------------------------------------
    # STEP 3: Dataset Profile & Metadata (%censusapi_getDsFullInfo)
    # -------------------------------------------------------------------------
    elif st.session_state.step == 2:
        st.markdown("### 🔍 Step 3: Dataset Profile & Metadata (%censusapi_getDsFullInfo)")
        st.markdown(
            "Pulls complete metadata for a specific dataset row from `_API_ALL_DATA`, including all supported variables, "
            "valid geography levels, and sample API queries into individual SAS tables and an Excel report."
        )

        with st.form("step3_form"):
            col1, col2 = st.columns(2)
            with col1:
                p_apiListingLibName = st.text_input("Catalog Libname (p_apiListingLibName)", value=DEFAULT_OUT_LIB)
            with col2:
                p_apiListingDsName = st.text_input("Catalog Dataset Name (p_apiListingDsName)", value=DEFAULT_OUT_DS)

            col3, col4 = st.columns(2)
            with col3:
                p_dsRowId = st.number_input("Dataset _ROWID_ (p_dsRowId)", value=3, min_value=1, max_value=100000, step=1)
            with col4:
                p_reportOutputPath = st.text_input("Report Output Path (p_reportOutputPath)", value="&g_outputRoot", key="step3_out_path")

            submit_step3 = st.form_submit_button("▶ Submit & Run in SAS", type="primary")

        sas_code_step3 = f"""/* Step 3: Compose complete Profile of the specified dataset */
%censusapi_getDsFullInfo(
    p_apiListingLibName={p_apiListingLibName}
  , p_apiListingDsName={p_apiListingDsName}
  , p_dsRowId={p_dsRowId}
  , p_reportOutputPath={p_reportOutputPath}
);
"""
        if submit_step3:
            if not sas_backend.is_connected:
                st.warning("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
            else:
                with st.spinner("Running %censusapi_getDsFullInfo in SAS..."):
                    res = sas_backend.submit_code(sas_code_step3)
                    st.session_state.step3_result = {"res": res}

        if st.session_state.step3_result:
            r = st.session_state.step3_result["res"]
            if r["success"]:
                st.success("✅ **Step 3 Profile executed successfully!** (0 SAS errors)")
            else:
                st.error(f"❌ **Execution finished with errors** ({len(r.get('errors', []))} error lines found)")

            with st.expander(f"📋 SAS Log ({len(r.get('log', '').splitlines())} lines)", expanded=False):
                st.code(r.get("log", ""), language="sas")

        st.markdown("#### 📝 Generated SAS Code Preview:")
        st.code(sas_code_step3, language="sas")

        st.download_button(
            label="💾 Download .sas Script",
            data=sas_code_step3.encode("utf-8"),
            file_name="step3_getDsFullInfo.sas",
            mime="text/plain",
        )

        st.markdown("---")
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("< Back: Collect Datasets", use_container_width=True):
                set_step(1)
        with col_next:
            if st.button("Next: Search Catalog >", type="primary", use_container_width=True):
                if unlocked_step >= 3:
                    set_step(3)

    # -------------------------------------------------------------------------
    # STEP 4: Interactive Census Catalog Quick-Lookup
    # -------------------------------------------------------------------------
    elif st.session_state.step == 3:
        st.markdown("### 🔎 Step 4: Interactive Census Catalog Quick-Lookup")
        st.markdown(
            "Search the Census API catalog to find the exact base URL endpoint for decennial censuses, ACS, or CPS. "
            "Selecting an endpoint automatically configures Step 5."
        )

        col_q, col_yr, col_sbtn = st.columns([3, 1, 1])
        with col_q:
            search_query = st.text_input(
                "🔎 Search Census Datasets (Keyword or Topic)",
                value=st.session_state.get("step4_query", "sf1"),
                placeholder="e.g. decennial, sf1, cps, acs5",
                key="step4_query",
            )
        with col_yr:
            year_val = st.selectbox(
                "Vintage Year Filter",
                options=["All", "2022", "2021", "2020", "2019", "2010", "2000"],
                index=0,
                key="step4_year",
            )
        with col_sbtn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            run_search = st.button("Search Catalog", type="primary", use_container_width=True)

        selected_yr = year_val if year_val != "All" else None
        results = search_datasets(search_query, year=selected_yr, max_results=20)

        endpoint_options = {}
        for r in results:
            if r.get("endpoint"):
                label = f"[{r.get('vintage', 'N/A')}] {r.get('title', '')[:65]} ({r.get('dataset_name', '')})"
                endpoint_options[label] = r.get("endpoint")

        st.markdown("#### 🎯 Matching Endpoints:")
        if endpoint_options:
            selected_label = st.selectbox(
                "Select Matched Endpoint",
                options=list(endpoint_options.keys()),
                key="step4_selected_label",
            )
            selected_url = endpoint_options.get(selected_label, "")
            st.markdown(f"**Selected Endpoint**: `{selected_url}`")

            if st.button("📋 Apply Endpoint to Step 5 Query Builder", type="success", use_container_width=False):
                st.session_state.picked_endpoint = selected_url
                st.session_state.endpoint_selected = True
                st.success(f"Applied: {selected_url}")
                if highest_unlocked_step(
                    sas_backend.is_connected,
                    st.session_state.step2_result,
                    st.session_state.step3_result,
                    st.session_state.endpoint_selected,
                    st.session_state.picked_endpoint,
                ) >= 4:
                    set_step(4)
        else:
            st.info("No endpoints matching your query. Enter a keyword above (e.g. 'sf1', 'acs5', 'dec') and click **Search Catalog**.")

        st.markdown("---")
        col_back, col_next = st.columns([1, 1])
        with col_back:
            if st.button("< Back: Dataset Profile", use_container_width=True):
                set_step(2)
        with col_next:
            if st.button("Next: Query Builder >", type="primary", use_container_width=True):
                if unlocked_step >= 4:
                    set_step(4)

    # -------------------------------------------------------------------------
    # STEP 5: Build & Submit Data API Query (%censusapi_submitDataApiQuery)
    # -------------------------------------------------------------------------
    elif st.session_state.step == 4:
        st.markdown("### 📊 Step 5: Build & Submit Data API Query (%censusapi_submitDataApiQuery)")
        st.markdown(
            "Submits requests to the Census Data API, automatically splitting large variable lists into chunks "
            "(up to `p_maxVarCount` variables per call), parsing JSON responses into SAS datasets, and merging the chunks."
        )

        with st.form("step5_form"):
            p_apiBaseURL = st.text_input(
                "API Base URL (p_apiBaseURL)",
                value=st.session_state.picked_endpoint,
                help="Base endpoint URL configured from Step 4 or entered manually",
            )
            p_apiGetClause = st.text_area(
                "get= Variables Clause (p_apiGetClause)",
                value="get=P010014,P010015,P010010,P010011,P010012,P010013,P010003,NAME",
                height=90,
            )
            col_for, col_in = st.columns(2)
            with col_for:
                p_apiForClause = st.text_input(
                    "for= Geography Clause (p_apiForClause)",
                    value="for=zip code tabulation area (3 digit) (or part):*",
                )
            with col_in:
                p_apiInClause = st.text_input(
                    "in= Geography Filter Clause (p_apiInClause)",
                    value="in=state:09,23,25,33,44,50",
                )

            col_uid, col_outds = st.columns(2)
            with col_uid:
                p_dsUniqueId = st.text_input("Dataset Unique ID (p_dsUniqueId)", value="_114_dec_2000")
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

            submit_step5 = st.form_submit_button("▶ Submit & Run in SAS", type="primary")

        sas_code_step5 = f"""/* Step 5: Submit Census Data API Query with Variable Chunking */
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
        if submit_step5:
            if not sas_backend.is_connected:
                st.warning("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
            else:
                with st.spinner("Submitting chunked API queries via SAS macro..."):
                    res = sas_backend.submit_code(sas_code_step5)
                    df = None
                    parts = p_outDsName.split(".")
                    libref = parts[0] if len(parts) > 1 else "WORK"
                    tbl = parts[1] if len(parts) > 1 else parts[0]
                    if res["success"]:
                        df = sas_backend.fetch_dataframe(tbl, libref)
                    st.session_state.step5_result = {
                        "res": res,
                        "df": df,
                        "ds_name": p_outDsName,
                    }

        if st.session_state.step5_result:
            r = st.session_state.step5_result["res"]
            if r["success"]:
                st.success("✅ **Step 5 Query executed successfully!** (0 SAS errors)")
            else:
                st.error(f"❌ **Query finished with errors** ({len(r.get('errors', []))} error lines found)")

            with st.expander(f"📋 SAS Log ({len(r.get('log', '').splitlines())} lines)", expanded=False):
                st.code(r.get("log", ""), language="sas")

            df = st.session_state.step5_result.get("df")
            if df is not None and not df.empty:
                st.markdown(f"#### 📊 SAS Dataset Table: `{st.session_state.step5_result['ds_name']}` ({len(df)} rows, {len(df.columns)} columns)")
                st.dataframe(df, use_container_width=True)
            elif df is not None and df.empty:
                st.info(f"ℹ️ Output table `{st.session_state.step5_result['ds_name']}` exists but is empty.")

        st.markdown("#### 📝 Generated SAS Code Preview:")
        st.code(sas_code_step5, language="sas")

        st.download_button(
            label="💾 Download .sas Script",
            data=sas_code_step5.encode("utf-8"),
            file_name="step5_submitDataApiQuery.sas",
            mime="text/plain",
        )

        st.markdown("---")
        col_back, _ = st.columns([1, 1])
        with col_back:
            if st.button("< Back: Search Endpoints", use_container_width=True):
                set_step(3)
