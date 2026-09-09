from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "src" / "py_sascensusapi" / "app.py"


def source() -> str:
    return APP_PATH.read_text(encoding="utf-8")


def test_marimo_tracks_endpoint_selection_and_step_results():
    text = source()
    assert "get_endpoint_selected, set_endpoint_selected = mo.state(False)" in text
    assert "get_step2_result, set_step2_result = mo.state(None)" in text
    assert "get_step3_result, set_step3_result = mo.state(None)" in text
    assert "get_step5_result, set_step5_result = mo.state(None)" in text


def test_marimo_has_streamlit_style_unlock_helper():
    text = source()
    assert "def highest_unlocked_step(" in text
    assert "result_succeeded" in text
    assert "endpoint_selected" in text


def test_navigation_buttons_are_wired_and_boundary_checked():
    text = source()
    assert "on_click=_go_to_step" in text
    assert "if target <= highest_step:" in text
    assert "disabled=idx > highest_step" in text


def test_forward_buttons_require_successful_prior_steps():
    text = source()
    assert "get_step2_result" in text
    assert "get_step3_result" in text
    assert "get_endpoint_selected" in text
    assert "set_step(2)" in text
    assert "set_step(3)" in text
    assert "set_step(4)" in text


def test_step_five_is_returned_and_rendered_by_orchestrator():
    text = source()
    assert "return (step5_card,)" in text
    assert "step5_card," in text[text.index("def wizard_orchestrator("):]
    assert "#step5_card" not in text
