from functools import cache
from pathlib import Path
import ast


APP_PATH = Path(__file__).parents[1] / "streamlit_app.py"


@cache
def _load_highest_unlocked_step():
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "highest_unlocked_step"
    )
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(APP_PATH), "exec"), namespace)
    return namespace["highest_unlocked_step"]


def test_environment_section_uses_backend_connection_state():
    source = APP_PATH.read_text(encoding="utf-8")
    assert 'if sas_backend.is_connected:' in source
    assert 'if st.session_state.get("sas_connected")' not in source


def test_connect_handler_does_not_mark_failed_connections_active():
    source = APP_PATH.read_text(encoding="utf-8")
    assert 'st.session_state["sas_connected"] = success' in source
    assert 'st.session_state["sas_connected"] = True' not in source


def test_environment_controls_remain_inside_connection_guard():
    source = APP_PATH.read_text(encoding="utf-8")
    guard_start = source.index('if sas_backend.is_connected:')
    section_start = source.index('st.markdown("#### ⚙️ Session Environment Parameters")')
    log_start = source.index('if st.session_state.step1_result is not None:')
    assert guard_start < section_start < log_start


def test_initial_state_unlocks_only_connection_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(False, None, None, False, "") == 0


def test_connection_unlocks_dataset_catalog_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(True, None, None, False, "") == 1


def test_step2_result_unlocks_dataset_profile_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(True, {"res": {"success": True}}, None, False, "") == 2


def test_failed_step2_result_does_not_unlock_dataset_profile_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(True, {"res": {"success": False}}, None, False, "") == 1


def test_step3_result_unlocks_catalog_search_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(
        True,
        {"res": {"success": True}},
        {"res": {"success": True}},
        False,
        " https://api.example.test ",
    ) == 3


def test_failed_step3_result_does_not_unlock_catalog_search_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(
        True,
        {"res": {"success": True}},
        {"res": {"success": False}},
        False,
        " https://api.example.test ",
    ) == 2


def test_endpoint_unlocks_query_builder_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(
        True,
        {"res": {"success": True}},
        {"res": {"success": True}},
        True,
        " https://api.example.test ",
    ) == 4


def test_disconnect_relocks_wizard_even_with_previous_results():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(
        False,
        {"res": {"success": True}},
        {"res": {"success": True}},
        True,
        "https://api.example.test",
    ) == 0


def test_aggrid_autosizes_columns_to_cell_contents():
    source = APP_PATH.read_text(encoding="utf-8")
    assert "from st_aggrid import AgGrid, GridOptionsBuilder, JsCode" in source
    assert "params.api.autoSizeColumns(columnIds, false);" in source
    assert 'grid_options["autoSizeStrategy"] = {"type": "fitCellContents"}' in source
    assert 'grid_options["onGridReady"] = auto_size_columns' in source
    assert "fit_columns_on_grid_load=False" in source
    assert "allow_unsafe_jscode=True" in source


def test_step2_reuses_persisted_selection_when_grid_returns_no_selection():
    source = APP_PATH.read_text(encoding="utf-8")
    assert 'persisted_row = st.session_state.get("selected_row")' in source
    assert 'selected_row = normalize_selected_row(grid_res.get("selected_rows", None))' in source
    assert 'if selected_row is None:\n                    selected_row = persisted_row' in source
    assert 'pre_selected_rows=(' in source
