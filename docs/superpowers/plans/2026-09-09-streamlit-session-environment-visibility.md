# Streamlit Session Environment Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure Step 1 displays Session Environment Parameters only when the SAS backend has an active connection.

**Architecture:** Keep `sas_backend.is_connected` as the authoritative render condition. Update the connection handler so the compatibility session-state flag reflects the actual connection result, then validate the source behavior without restructuring the Streamlit app.

**Tech Stack:** Python, Streamlit, pytest or repository Python checks.

---

### Task 1: Add focused source-level regression checks

**Files:**
- Create: `tests/test_streamlit_connection_visibility.py`

- [ ] **Step 1: Write checks for the connection guard and result handling**

```python
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
```

- [ ] **Step 2: Run the focused checks before implementation**

Run:

```powershell
pytest -q tests/test_streamlit_connection_visibility.py
```

Expected: the checks fail because the current connection handler unconditionally
sets `sas_connected` to `True`, and the environment section guard uses session
state rather than `sas_backend.is_connected`.

### Task 2: Fix authoritative connection-state handling

**Files:**
- Modify: `streamlit_app.py:250-337`

- [ ] **Step 1: Store the actual connection result**

Change the Connect button handler from:

```python
st.session_state["sas_connected"] = True
```

to:

```python
st.session_state["sas_connected"] = success
```

- [ ] **Step 2: Guard the environment section with backend state**

Change:

```python
if st.session_state.get("sas_connected"):
```

to:

```python
if sas_backend.is_connected:
```

Keep the environment inputs, initialization button, and SAS log at their
current indentation inside this guard. The initialization action should retain
its defensive `sas_backend.is_connected` check.

- [ ] **Step 3: Run the focused checks**

Run:

```powershell
pytest -q tests/test_streamlit_connection_visibility.py
```

Expected: all checks pass.

### Task 3: Run available validation

**Files:**
- Modify: none

- [ ] **Step 1: Compile the changed application**

Run:

```powershell
python -m py_compile streamlit_app.py src/py_sascensusapi/streamlit_app.py
```

Expected: exit code 0 with no syntax errors.

- [ ] **Step 2: Run the focused test suite**

Run:

```powershell
pytest -q tests/test_streamlit_connection_visibility.py
```

Expected: all tests pass.

- [ ] **Step 3: Inspect the final diff**

Run:

```powershell
git --no-pager diff -- streamlit_app.py tests/test_streamlit_connection_visibility.py
```

Expected: only the connection result assignment, the environment-section
visibility guard, and the focused regression checks are present.
