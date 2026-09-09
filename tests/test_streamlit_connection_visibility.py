from pathlib import Path


APP_PATH = Path(__file__).parents[1] / "streamlit_app.py"


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
