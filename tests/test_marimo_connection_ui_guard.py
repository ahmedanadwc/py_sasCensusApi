from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "src" / "py_sascensusapi" / "app.py"


def source() -> str:
    return APP_PATH.read_text(encoding="utf-8")


def test_navigation_cell_receives_connection_state_and_disables_later_steps():
    text = source()
    assert "def wizard_navigation_bar(get_step, mo, sas_backend):" in text
    assert "disabled=(not sas_backend.is_connected and idx > 0)" in text


def test_step_one_forward_callback_requires_connection():
    text = source()
    assert "def _go_to_step_two(_):" in text
    assert "if sas_backend.is_connected:" in text
    assert "set_step(1)" in text


def test_orchestrator_accepts_connection_state():
    text = source()
    assert "def wizard_orchestrator(" in text
    assert "sas_backend," in text
    assert 'mo.md("⚠️ Connect to SAS to continue to the next wizard steps.")' in text


def test_environment_parameters_remain_connection_guarded():
    text = source()
    section_start = text.index(
        "# --- Conditional UI guard: only show env params when SAS is connected ---"
    )
    assert "if sas_backend.is_connected:" in text[section_start:]
