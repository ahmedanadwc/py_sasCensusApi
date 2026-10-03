from functools import cache
from pathlib import Path
import ast
from urllib.parse import unquote

import pandas as pd


APP_PATH = Path(__file__).parents[1] / "streamlit_app.py"


@cache
def _load_function(name):
    source = APP_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    namespace = {"pd": pd, "unquote": unquote}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(APP_PATH), "exec"), namespace)
    return namespace[name]


def _load_highest_unlocked_step():
    return _load_function("highest_unlocked_step")


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
    assert highest_unlocked_step(False, None) == 0


def test_connection_unlocks_dataset_catalog_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(True, None) == 1


def test_step2_result_unlocks_dataset_profile_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(True, {"res": {"success": True}}) == 2


def test_failed_step2_result_does_not_unlock_dataset_profile_step():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(True, {"res": {"success": False}}) == 1


def test_disconnect_relocks_wizard_even_with_previous_results():
    highest_unlocked_step = _load_highest_unlocked_step()
    assert highest_unlocked_step(False, {"res": {"success": True}}) == 0


def test_step3_row_id_field_resets_when_selected_dataset_changes():
    source = APP_PATH.read_text(encoding="utf-8")
    assert 'key=f"step3_row_id_{selected_row_id}"' in source
    assert 'key="step3_row_id"' not in source


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


def test_names_to_csv_joins_selected_name_values():
    names_to_csv = _load_function("names_to_csv")
    rows = [{"Name": "P010014", "Label": "x"}, {"Name": " P010015 "}, {"name": "NAME"}, {"Name": "P010014"}, {"Name": ""}]
    assert names_to_csv(rows) == "P010014,P010015,NAME"
    assert names_to_csv([]) == ""


def test_selected_rows_to_list_accepts_dataframe_list_and_none():
    selected_rows_to_list = _load_function("selected_rows_to_list")
    assert selected_rows_to_list(None) == []
    assert selected_rows_to_list(pd.DataFrame({"Name": ["A", "B"]})) == [{"Name": "A"}, {"Name": "B"}]
    assert selected_rows_to_list([{"Name": "A"}]) == [{"Name": "A"}]


def test_variables_grid_uses_multiple_selection_and_feeds_get_clause():
    source = APP_PATH.read_text(encoding="utf-8")
    assert 'selection_mode="multiple"' in source
    assert 'get_default = q_fields.get("get", "get=")' in source
    assert "P010014,P010015" not in source


def test_parse_example_url_splits_clauses():
    parse_example_url = _load_function("parse_example_url")
    parsed = parse_example_url(
        "https://api.census.gov/data/2000/dec/sf1?get=P001001,NAME&for=county:*&in=state:09&key=abc"
    )
    assert parsed == {
        "base_url": "https://api.census.gov/data/2000/dec/sf1?",
        "get": "get=P001001,NAME",
        "for": "for=county:*",
        "in": "in=state:09",
    }


def test_parse_example_url_handles_missing_and_multiple_in_clauses():
    parse_example_url = _load_function("parse_example_url")
    parsed = parse_example_url("https://x.test/data?get=A&for=tract:*&in=state:06&in=county:037")
    assert parsed["in"] == "in=state:06&in=county:037"
    assert parse_example_url("https://x.test/data?get=A")["for"] == ""
