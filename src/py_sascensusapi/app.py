import marimo

__generated_with = "0.24.0"
app = marimo.App(
    width="full",
    app_title="US Census SAS API Studio - Setup & Query Wizard",
)


@app.cell
def imports():
    import os
    import re
    import pandas as pd
    import marimo as mo
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

    return (
        DEFAULT_DATA_JSON_URL,
        DEFAULT_MAX_VAR_COUNT,
        DEFAULT_OUT_DS,
        DEFAULT_OUT_LIB,
        DEFAULT_SAS_CFGFILE,
        SAS_PROJECT_ROOT,
        mo,
        sas_backend,
        search_datasets,
    )


@app.cell
def wizard_state(mo):
    # Wizard step tracking state (0 to 4)
    get_step, set_step = mo.state(0)
    # Target endpoint passed from Step 4 search
    get_picked_endpoint, set_picked_endpoint = mo.state("https://api.census.gov/data/2000/dec/sf1?")
    return get_picked_endpoint, get_step, set_picked_endpoint, set_step


@app.cell
def _(mo):
    mo.status.toast(
        title="🤖 Marimo Pair Ready",
        description="👋 Connected & ready to pair-program on your Census API Studio notebook!",
        kind="success",
    )
    return


@app.cell
def app_header(mo):
    # Define the HTML for the header section with gradient background and styling
    header_html = mo.md("""
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #3b82f6 100%); color: white; padding: 20px 24px; border-radius: 10px 10px 0 0; box-shadow: 0 4px 12px rgba(0,0,0,0.15); margin-bottom: 0;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <span style="font-size: 34px; line-height: 1;">🏛️</span>
                <div>
                    <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 700; letter-spacing: -0.3px;">
                        US Census SAS API Studio
                    </h1>
                    <p style="margin: 3px 0 0 0; color: #dbeafe; font-size: 13px; font-weight: 400;">
                        Windows Wizard for Configuring & Executing Census API SAS Macros via SASPy
                    </p>
                </div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.15); backdrop-filter: blur(4px); padding: 6px 14px; border-radius: 20px; font-size: 12px; color: #f8fafc; border: 1px solid rgba(255, 255, 255, 0.25);">
                Wizard Flow: Step-by-Step Orchestrator
            </div>
        </div>
    </div>
    """)
    return (header_html,)


@app.cell
def wizard_navigation_bar(get_step, mo):
    # Get the current wizard step index (0 to 4) 
    _nav_step = get_step()

    # Define the Wizard Steps Metadata (Short Label, Full Label)
    steps_meta = [
        ( "Connect", "🔌 SAS Session"),
        ( "Catalog", "📂 Collect All Datasets"),
        ( "Profile", "🔍 Dataset Info"),
        ( "Search", "🔎 Catalog Quick-Lookup"),
        ( "Query", "📊 Query Builder"),
    ]

    # Create the Navigation Buttons for the Wizard Steps
    nav_buttons = []
    for idx, (short_label, full_label) in enumerate(steps_meta):
        is_active = (_nav_step == idx)
        label_text = f"▶ {short_label}" if is_active else short_label
        btn = mo.ui.button(
            label=label_text,
            disabled=True,
        )
        nav_buttons.append(btn)

    # Create the Step Navigation View with Current Step Highlighted 
    step_nav_view = mo.md(
            f"""
            <div style="background: #f1f5f9; border-left: 1px solid #cbd5e1; border-right: 1px solid #cbd5e1; border-bottom: 2px solid #e2e8f0; padding: 10px 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 13px; font-weight: 600; color: #334155;">
                    Wizard Steps:
                </div>
                <div style="font-size: 12px; color: #64748b; font-weight: 500;">
                    Step {_nav_step + 1} of {len(steps_meta)}: <strong>{steps_meta[_nav_step][1]}</strong>
                </div>
            </div>
            """)
    return nav_buttons, step_nav_view


@app.cell
def form_step1_connection_inputs(DEFAULT_SAS_CFGFILE, SAS_PROJECT_ROOT, mo):
    # -------------------------------------------
    # Build the SASPy connection form for Step 1
    # -------------------------------------------

    # Build the SASPy connection definition options
    cfg_select = mo.ui.dropdown(
        options=["oda", "winlocal", "default"],
        value="oda",
        label="SAS Configuration (cfgname)",
    )
    # Define default sascfg file path (optional)
    cfgfile_input = mo.ui.text(
        value=DEFAULT_SAS_CFGFILE,
        label="Custom sascfg File Path (cfgfile, optional)",
        placeholder=r"e.g. C:\Users\user\sascfg_personal.py",
        full_width=True,
    )
    # Define the Connect and Disconnect buttons for SASPy
    btn_connect = mo.ui.run_button(label="🔌 Connect to SAS", kind="success")
    btn_disconnect = mo.ui.run_button(label="🔌 Disconnect", kind="danger")

    # ----------------------------------------------
    # Define the settings needed for the Census API
    # ----------------------------------------------

    # Define the SAS Project Root Path and Census API Key inputs
    proj_path_input = mo.ui.text(
        value=str(SAS_PROJECT_ROOT),
        label="SAS Project Root Path (contains code/macros, data, output)",
        full_width=True,
    )
    # Define the Census API Key input (masked) and assign it to a global variable &g_apiKey
    api_key_input = mo.ui.text(
        value="",
        label="Census API Key (masked, assigned to global &g_apiKey)",
        kind="password",
        full_width=True,
    )
    # Define the Initialize Environment button for Step 1
    btn_init_env = mo.ui.run_button(
        label="⚙️ Initialize SAS Autocall & Libnames",
        kind="warn",
    )
    return (
        api_key_input,
        btn_connect,
        btn_disconnect,
        btn_init_env,
        cfg_select,
        cfgfile_input,
        proj_path_input,
    )


@app.cell
def step1_view(
    api_key_input,
    btn_connect,
    btn_disconnect,
    btn_init_env,
    cfg_select,
    cfgfile_input,
    mo,
    proj_path_input,
    sas_backend,
    set_step,
):
    # Reactive SASPy connection execution
    status_msg = "⚪ SAS Disconnected (Preview & Code Export mode)"
    if btn_connect.value:
        success, msg = sas_backend.connect(cfgname=cfg_select.value, cfgfile=cfgfile_input.value)
        status_msg = f"🟢 Connected to SAS ({sas_backend._cfgname})" if success else f"🔴 {msg}"
    elif btn_disconnect.value:
        msg = sas_backend.disconnect()
        status_msg = f"⚪ {msg}"
    elif sas_backend.is_connected:
        status_msg = f"🟢 Connected to SAS ({sas_backend._cfgname})"

    # Define the environment initialization logic for Step 1
    init_msg = ""
    if btn_init_env.value:
        if sas_backend.is_connected:
            env_res = sas_backend.run_environment_setup(proj_path_input.value, api_key_input.value)
            init_msg = "✅ Macro Autocall paths and APILIB libname successfully initialized!" if env_res["success"] else f"⚠️ Setup finished with warnings/errors. Check log."
        else:
            init_msg = "⚠️ Connect to SAS first before initializing the macro environment."

    btn_next_step1 = mo.ui.button(
        label="Next: Collect Dataset Catalog >",
        kind="warn",
        on_click=lambda _: set_step(1),
    )

    # Compopse the Step 1 card with connection, environment setup, and navigation
    step1_card = mo.vstack([
        mo.md(
            f"""
            ### 🔌 Step 1: SASPy Connection & Environment Setup
            Connect to your SAS instance and configure the required macro autocall directories, global macro variables, and libnames.

            **Current Session Status**: `{status_msg}`
            """
        ),
        mo.hstack([cfg_select, btn_connect, btn_disconnect]),
        cfgfile_input,
        mo.md("---"),
        mo.md("#### Session Environment Parameters"),
        proj_path_input,
        api_key_input,
        mo.hstack([btn_init_env]),
        mo.md(f"**{init_msg}**") if init_msg else mo.md(""),
        mo.md("---"),
        mo.hstack([
            mo.md("💡 *Tip: If running offline without SAS, you can still configure parameters and download SAS scripts.*"),
            btn_next_step1,
        ], justify="space-between"),
    ])
    return (step1_card,)


@app.cell
def form_step2_get_all_datasets(
    DEFAULT_DATA_JSON_URL,
    DEFAULT_OUT_DS,
    DEFAULT_OUT_LIB,
    mo,
):
    # Define the Step 2 form for collecting all datasets metadata
    step2_form = (
        mo.md(
            """
            {p_outLibName}
            {p_outDsName}
            {p_dataJsonURL}
            {p_reportOutputPath}
            """
        )
        .batch(
            p_outLibName=mo.ui.text(value=DEFAULT_OUT_LIB, label="Output SAS Library (p_outLibName)"),
            p_outDsName=mo.ui.text(value=DEFAULT_OUT_DS, label="Output Dataset Name (p_outDsName)"),
            p_dataJsonURL=mo.ui.text(value=DEFAULT_DATA_JSON_URL, label="Census Catalog JSON URL (p_dataJsonURL)", full_width=True),
            p_reportOutputPath=mo.ui.text(value="&g_outputRoot", label="Report Output Path (p_reportOutputPath)", full_width=True),
        )
        .form(
            label="💾 Dataset Collection Parameters",
            submit_button_label="▶ Submit & Run in SAS",
        )
    )
    return (step2_form,)


@app.cell
def step2_view(
    DEFAULT_DATA_JSON_URL,
    DEFAULT_OUT_DS,
    DEFAULT_OUT_LIB,
    mo,
    sas_backend,
    set_step,
    step2_form,
):
    step2_vals = step2_form.value or {
        "p_outLibName": DEFAULT_OUT_LIB,
        "p_outDsName": DEFAULT_OUT_DS,
        "p_dataJsonURL": DEFAULT_DATA_JSON_URL,
        "p_reportOutputPath": "&g_outputRoot",
    }

    sas_code_step2 = f"""/* Step 2: Collect all Census Data API datasets metadata */
    %censusapi_getAllDataSets(
        p_outLibName={step2_vals['p_outLibName']}
      , p_outDsName={step2_vals['p_outDsName']}
      , p_dataJsonURL=%str({step2_vals['p_dataJsonURL']})
      , p_reportOutputPath={step2_vals['p_reportOutputPath']}
    );
    """

    step2_exec_status = None
    step2_log_display = None
    step2_table_view = None

    if step2_form.value is not None:
        if not sas_backend.is_connected:
            step2_exec_status = mo.md("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
        else:
            step2_res = sas_backend.submit_code(sas_code_step2)
            if step2_res["success"]:
                step2_exec_status = mo.md("✅ **Step 2 Macro executed successfully!** (0 SAS errors)")
            else:
                step2_exec_status = mo.md(f"❌ **Macro finished with errors** ({len(step2_res['errors'])} error lines found)")

            step2_log_display = mo.accordion({
                f"📋 SAS Log ({len(step2_res['log'].splitlines())} lines)": mo.ui.code_editor(
                    value=step2_res["log"],
                    language="sql",
                    disabled=True,
                )
            })

            out_tbl = step2_vals["p_outDsName"]
            out_lib = step2_vals["p_outLibName"]
            step2_df = sas_backend.fetch_dataframe(out_tbl, out_lib)
            if step2_df is not None and not step2_df.empty:
                step2_table_view = mo.vstack([
                    mo.md(f"#### 📊 Dataset Preview: `{out_lib}.{out_tbl}` ({len(step2_df)} rows, {len(step2_df.columns)} columns)"),
                    mo.ui.table(step2_df, pagination=True),
                ])

    btn_back_step2 = mo.ui.button(label="< Back: SAS Connection", on_click=lambda _: set_step(0))
    btn_next_step2 = mo.ui.button(label="Next: Dataset Profile >", kind="warn", on_click=lambda _: set_step(2))

    step2_card = mo.vstack([
        mo.md(
            """
            ### 📂 Step 2: Collect All Datasets (%censusapi_getAllDataSets)
            Downloads the official Census `data.json` catalog, parses all available API endpoints, vintages,
            and titles into a SAS master dataset (`APILIB._API_ALL_DATA`), and produces an Excel inventory.
            """
        ),
        step2_form,
        step2_exec_status if step2_exec_status else mo.md(""),
        step2_log_display if step2_log_display else mo.md(""),
        step2_table_view if step2_table_view else mo.md(""),
        mo.md("#### 📝 Generated SAS Code Preview:"),
        mo.ui.code_editor(value=sas_code_step2, language="sql", disabled=True),
        mo.hstack([
            mo.download(
                data=sas_code_step2.encode("utf-8"),
                filename="step2_getAllDataSets.sas",
                label="💾 Download .sas Script",
            ),
        ]),
        mo.md("---"),
        mo.hstack([btn_back_step2, btn_next_step2], justify="space-between"),
    ])
    return (step2_card,)


@app.cell
def form_step3_ds_full_info(DEFAULT_OUT_DS, DEFAULT_OUT_LIB, mo):
    step3_form = (
        mo.md(
            """
            {p_apiListingLibName}
            {p_apiListingDsName}
            {p_dsRowId}
            {p_reportOutputPath}
            """
        )
        .batch(
            p_apiListingLibName=mo.ui.text(value=DEFAULT_OUT_LIB, label="Catalog Libname (p_apiListingLibName)"),
            p_apiListingDsName=mo.ui.text(value=DEFAULT_OUT_DS, label="Catalog Dataset Name (p_apiListingDsName)"),
            p_dsRowId=mo.ui.number(value=3, start=1, stop=100000, step=1, label="Dataset _ROWID_ (p_dsRowId)"),
            p_reportOutputPath=mo.ui.text(value="&g_outputRoot", label="Report Output Path (p_reportOutputPath)", full_width=True),
        )
        .form(
            label="💾 Dataset Profile Parameters",
            submit_button_label="▶ Submit & Run in SAS",
        )
    )
    return (step3_form,)


@app.cell
def step3_view(
    DEFAULT_OUT_DS,
    DEFAULT_OUT_LIB,
    mo,
    sas_backend,
    set_step,
    step3_form,
):
    step3_vals = step3_form.value or {
        "p_apiListingLibName": DEFAULT_OUT_LIB,
        "p_apiListingDsName": DEFAULT_OUT_DS,
        "p_dsRowId": 3,
        "p_reportOutputPath": "&g_outputRoot",
    }

    sas_code_step3 = f"""/* Step 3: Compose complete Profile of the specified dataset */
    %censusapi_getDsFullInfo(
        p_apiListingLibName={step3_vals['p_apiListingLibName']}
      , p_apiListingDsName={step3_vals['p_apiListingDsName']}
      , p_dsRowId={step3_vals['p_dsRowId']}
      , p_reportOutputPath={step3_vals['p_reportOutputPath']}
    );
    """

    step3_exec_status = None
    step3_log_display = None

    if step3_form.value is not None:
        if not sas_backend.is_connected:
            step3_exec_status = mo.md("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
        else:
            step3_res = sas_backend.submit_code(sas_code_step3)
            if step3_res["success"]:
                step3_exec_status = mo.md("✅ **Step 3 Profile executed successfully!** (0 SAS errors)")
            else:
                step3_exec_status = mo.md(f"❌ **Execution finished with errors** ({len(step3_res['errors'])} error lines found)")

            step3_log_display = mo.accordion({
                f"📋 SAS Log ({len(step3_res['log'].splitlines())} lines)": mo.ui.code_editor(
                    value=step3_res["log"],
                    language="sql",
                    disabled=True,
                )
            })

    btn_back_step3 = mo.ui.button(label="< Back: Collect Datasets", on_click=lambda _: set_step(1))
    btn_next_step3 = mo.ui.button(label="Next: Search Catalog >", kind="warn", on_click=lambda _: set_step(3))

    step3_card = mo.vstack([
        mo.md(
            """
            ### 🔍 Step 3: Dataset Profile & Metadata (%censusapi_getDsFullInfo)
            Pulls complete metadata for a specific dataset row from `_API_ALL_DATA`, including all supported variables,
            valid geography levels, and sample API queries into individual SAS tables and an Excel report.
            """
        ),
        step3_form,
        step3_exec_status if step3_exec_status else mo.md(""),
        step3_log_display if step3_log_display else mo.md(""),
        mo.md("#### 📝 Generated SAS Code Preview:"),
        mo.ui.code_editor(value=sas_code_step3, language="sql", disabled=True),
        mo.hstack([
            mo.download(
                data=sas_code_step3.encode("utf-8"),
                filename="step3_getDsFullInfo.sas",
                label="💾 Download .sas Script",
            ),
        ]),
        mo.md("---"),
        mo.hstack([btn_back_step3, btn_next_step3], justify="space-between"),
    ])
    return (step3_card,)


@app.cell
def search_step4_controls(mo):
    search_query_input = mo.ui.text(
        value="sf1",
        label="🔎 Search Census Datasets (Keyword or Topic)",
        placeholder="e.g. decennial, sf1, cps, acs5",
        full_width=True,
    )
    year_select = mo.ui.dropdown(
        options=["All", "2022", "2021", "2020", "2019", "2010", "2000"],
        value="All",
        label="Vintage Year Filter",
    )
    btn_do_search = mo.ui.run_button(label="Search Catalog", kind="warn")
    return btn_do_search, search_query_input, year_select


@app.cell
def step4_search_results(
    btn_do_search,
    mo,
    search_datasets,
    search_query_input,
    year_select,
):
    _ = btn_do_search.value
    # Run catalog search
    search_results = []
    if search_query_input.value:
        selected_yr = year_select.value if year_select.value != "All" else None
        search_results = search_datasets(search_query_input.value, year=selected_yr, max_results=15)

    endpoint_options = {
        f"[{r.get('vintage', 'N/A')}] {r.get('title', '')[:55]} ({r.get('dataset_name', '')})": r.get("endpoint", "")
        for r in search_results if r.get("endpoint")
    }

    first_key = next(iter(endpoint_options.keys())) if endpoint_options else None
    selected_endpoint_picker = mo.ui.dropdown(
        options=endpoint_options,
        value=first_key,
        label="Select Matched Endpoint",
        full_width=True,
    )
    return endpoint_options, selected_endpoint_picker


@app.cell
def step4_view(
    btn_do_search,
    endpoint_options,
    mo,
    search_query_input,
    selected_endpoint_picker,
    set_picked_endpoint,
    set_step,
    year_select,
):
    # Picked endpoint display & transfer button
    active_ep = selected_endpoint_picker.value or "https://api.census.gov/data/2000/dec/sf1?"

    btn_apply_endpoint = mo.ui.button(
        label="📋 Apply Endpoint to Step 5 Query Builder",
        kind="success",
        on_click=lambda _: (set_picked_endpoint(active_ep), set_step(4)),
    )

    btn_back_step4 = mo.ui.button(label="< Back: Dataset Profile", on_click=lambda _: set_step(2))
    btn_next_step4 = mo.ui.button(label="Next: Query Builder >", kind="warn", on_click=lambda _: set_step(4))

    has_results = len(endpoint_options) > 0
    endpoint_display = selected_endpoint_picker if has_results else mo.md("_Enter a query and click **Search Catalog** to view endpoints._")

    step4_card = mo.vstack([
        mo.md(
            """
            ### 🔎 Step 4: Interactive Census Catalog Quick-Lookup
            Search the Census API catalog to find the exact base URL endpoint for decennial censuses, ACS, or CPS.
            Selecting an endpoint automatically configures Step 5.
            """
        ),
        mo.hstack([search_query_input, year_select, btn_do_search]),
        mo.md("#### 🎯 Matching Endpoints:"),
        endpoint_display,
        mo.md(f"**Selected Endpoint**: `{active_ep}`") if active_ep else mo.md(""),
        mo.hstack([btn_apply_endpoint]),
        mo.md("---"),
        mo.hstack([btn_back_step4, btn_next_step4], justify="space-between"),
    ])
    return (step4_card,)


@app.cell
def form_step5_query(DEFAULT_MAX_VAR_COUNT, get_picked_endpoint, mo):
    current_endpoint = get_picked_endpoint()
    step5_form = (
        mo.md(
            """
            {p_apiBaseURL}
            {p_apiGetClause}
            {p_apiForClause}
            {p_apiInClause}

            {p_dsUniqueId}
            {p_outDsName}
            {p_maxVarCount}
            {p_dataApiKey}
            """
        )
        .batch(
            p_apiBaseURL=mo.ui.text(
                value=current_endpoint,
                label="API Base URL (p_apiBaseURL)",
                full_width=True,
            ),
            p_apiGetClause=mo.ui.text_area(
                value="get=P010014,P010015,P010010,P010011,P010012,P010013,P010003,NAME",
                label="get= Variables Clause (p_apiGetClause)",
                full_width=True,
            ),
            p_apiForClause=mo.ui.text(
                value="for=zip code tabulation area (3 digit) (or part):*",
                label="for= Geography Clause (p_apiForClause)",
                full_width=True,
            ),
            p_apiInClause=mo.ui.text(
                value="in=state:09,23,25,33,44,50",
                label="in= Geography Filter Clause (p_apiInClause)",
                full_width=True,
            ),
            p_dsUniqueId=mo.ui.text(value="_114_dec_2000", label="Dataset Unique ID (p_dsUniqueId)"),
            p_outDsName=mo.ui.text(value="work.sf1_response", label="Output SAS Dataset (p_outDsName)"),
            p_maxVarCount=mo.ui.slider(start=5, stop=50, step=1, value=DEFAULT_MAX_VAR_COUNT, label="Max Var Count Chunking (p_maxVarCount)"),
            p_dataApiKey=mo.ui.text(value="&g_apiKey", label="Census API Key Reference (p_dataApiKey)"),
        )
        .form(
            label="💾 Query Builder Parameters",
            submit_button_label="▶ Submit & Run in SAS",
        )
    )
    return (step5_form,)


@app.cell
def step5_view(
    DEFAULT_MAX_VAR_COUNT,
    get_picked_endpoint,
    mo,
    sas_backend,
    set_step,
    step5_form,
):
    def _():
        step5_vals = step5_form.value or {
            "p_apiBaseURL": get_picked_endpoint(),
            "p_apiGetClause": "get=P010014,P010015,P010010,P010011,P010012,P010013,P010003,NAME",
            "p_apiForClause": "for=zip code tabulation area (3 digit) (or part):*",
            "p_apiInClause": "in=state:09,23,25,33,44,50",
            "p_dsUniqueId": "_114_dec_2000",
            "p_outDsName": "work.sf1_response",
            "p_maxVarCount": DEFAULT_MAX_VAR_COUNT,
            "p_dataApiKey": "&g_apiKey",
        }

        out_ds_name_step5 = step5_vals.get("p_outDsName", "work.sf1_response")

        sas_code_step5 = f"""/* Step 5: Submit Census Data API Query with Variable Chunking */
        %censusapi_submitDataApiQuery(
            p_apiBaseURL=%STR({step5_vals['p_apiBaseURL']})
          , p_apiGetClause=%STR({step5_vals['p_apiGetClause']})
          , p_apiForClause=%bquote({step5_vals['p_apiForClause']})
          , p_apiInClause=%bquote({step5_vals['p_apiInClause']})
          , p_dsUniqueId={step5_vals['p_dsUniqueId']}
          , p_outDsName={out_ds_name_step5}
          , p_dataApiKey={step5_vals['p_dataApiKey']}
          , p_maxVarCount={step5_vals['p_maxVarCount']}
        );
        """

        step5_exec_status = None
        step5_log_display = None
        step5_table_view = None

        if step5_form.value is not None:
            if not sas_backend.is_connected:
                step5_exec_status = mo.md("⚠️ **SAS is not connected.** Return to Step 1 and connect via SASPy first.")
            else:
                step5_res = sas_backend.submit_code(sas_code_step5)
                if step5_res["success"]:
                    step5_exec_status = mo.md("✅ **Step 5 Query executed successfully!** (0 SAS errors)")
                else:
                    step5_exec_status = mo.md(f"❌ **Query finished with errors** ({len(step5_res['errors'])} error lines found)")

                step5_log_display = mo.accordion({
                    f"📋 SAS Log ({len(step5_res['log'].splitlines())} lines)": mo.ui.code_editor(
                        value=step5_res["log"],
                        language="sql",
                        disabled=True,
                    )
                })

                parts = out_ds_name_step5.split(".")
                libref = parts[0] if len(parts) > 1 else "WORK"
                tbl = parts[1] if len(parts) > 1 else parts[0]
                step5_df = sas_backend.fetch_dataframe(tbl, libref)
                if step5_df is not None and not step5_df.empty:
                    step5_table_view = mo.vstack([
                        mo.md(f"#### 📊 SAS Dataset Table: `{out_ds_name_step5}` ({len(step5_df)} rows, {len(step5_df.columns)} columns)"),
                        mo.ui.table(step5_df, pagination=True),
                    ])
                elif step5_df is not None and step5_df.empty:
                    step5_table_view = mo.md(f"ℹ️ Output table `{out_ds_name_step5}` exists but is empty.")

        btn_back_step5 = mo.ui.button(label="< Back: Search Endpoints", on_click=lambda _: set_step(3))
        btn_next_step5 = mo.ui.button(label="Next: SAS Execution & Results >", kind="warn", on_click=lambda _: set_step(5))

        step5_card = mo.vstack([
            mo.md(
                """
                ### 📊 Step 5: Build & Submit Data API Query (%censusapi_submitDataApiQuery)
                Submits requests to the Census Data API, automatically splitting large variable lists into chunks
                (up to `p_maxVarCount` variables per call), parsing JSON responses into SAS datasets, and merging the chunks.
                """
            ),
            step5_form,
            step5_exec_status if step5_exec_status else mo.md(""),
            step5_log_display if step5_log_display else mo.md(""),
            step5_table_view if step5_table_view else mo.md(""),
            mo.md("#### 📝 Generated SAS Code Preview:"),
            mo.ui.code_editor(value=sas_code_step5, language="sql", disabled=True),
            mo.hstack([
                mo.download(
                    data=sas_code_step5.encode("utf-8"),
                    filename="step5_submitDataApiQuery.sas",
                    label="💾 Download .sas Script",
                ),
            ]),
            mo.md("---"),
            mo.hstack([btn_back_step5, btn_next_step5], justify="space-between"),
        ])
        return


    _()
    return


@app.cell
def wizard_orchestrator(
    get_step,
    header_html,
    mo,
    nav_buttons,
    step1_card,
    step2_card,
    step3_card,
    step4_card,
    step_nav_view,
):
    current_step = get_step()
    steps_content = [
        step1_card,
        step2_card,
        step3_card,
        step4_card,
        #step5_card,
    ]

    wizard_window = mo.vstack([
        header_html,
        step_nav_view,
        mo.md(
            """
            <div style="background: #ffffff; border-left: 1px solid #cbd5e1; border-right: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; border-radius: 0 0 10px 10px; padding: 24px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);">
            """
        ),
        mo.hstack((nav_buttons,steps_content[current_step]), justify="start", gap=1),

        mo.md("</div>"),
    ])

    wizard_window
    return


if __name__ == "__main__":
    app.run()
