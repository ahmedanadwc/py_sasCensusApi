from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "src" / "py_sascensusapi" / "app.py"


def source() -> str:
    return APP_PATH.read_text(encoding="utf-8")


def step2_view_source() -> str:
    text = source()
    start = text.index("def step2_view(")
    end = text.index("\n\n@app.cell", start)
    return text[start:end]


def test_step_two_auto_fetches_only_before_submission_while_connected():
    text = step2_view_source()
    assert "step2_form.value is not None" in text
    assert "step2_form.value is None" in text
    assert "sas_backend.is_connected" in text
    assert "existing_df = sas_backend.fetch_dataframe(out_tbl, out_lib)" in text


def test_auto_fetch_renders_existing_dataset_status_log_and_preview():
    text = step2_view_source()
    assert "Fetched existing SAS data set" in text
    assert '"📋 SAS Log (auto-fetch)"' in text
    assert "mo.ui.table(existing_df, pagination=True)" in text
    assert "Loaded existing dataset" in text


def test_auto_fetch_skips_disconnected_and_empty_datasets():
    text = step2_view_source()
    assert "and sas_backend.is_connected" in text
    assert "if existing_df is not None and not existing_df.empty:" in text


def test_submitted_step_two_path_remains_macro_execution_path():
    text = step2_view_source()
    assert "step2_res = sas_backend.submit_code(sas_code_step2)" in text
    assert "step2_df = (" in text
    assert "if step2_res[\"success\"]" in text
