# Marimo Connection UI Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent disconnected users from navigating to or rendering Marimo notebook steps that require an active SAS session.

**Architecture:** Use `sas_backend.is_connected` as the single connection predicate. Pass it into the navigation and orchestrator cells, disable Steps 2–5 while disconnected, render only Step 1 plus a connection prompt in the orchestrator, and add a defensive connection check to the Step 1 forward callback.

**Tech Stack:** Python 3.13+, Marimo 0.24, pytest.

---

### Task 1: Add source-level regression tests

**Files:**
- Create: `tests/test_marimo_connection_ui_guard.py`

- [ ] **Step 1: Write tests for the intended guard structure**

```python
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
    section_start = text.index("# --- Conditional UI guard: only show env params when SAS is connected ---")
    assert "if sas_backend.is_connected:" in text[section_start:]
```

- [ ] **Step 2: Run the tests before implementation**

Run:

```powershell
python -m pytest -q tests/test_marimo_connection_ui_guard.py
```

Expected: the tests fail because the navigation and orchestrator cells do not
yet receive `sas_backend` and the Step 1 callback is not guarded.

### Task 2: Update Marimo navigation and Step 1 callback

**Files:**
- Modify: `src/py_sascensusapi/app.py:86-122, 181-218`

- [ ] **Step 1: Pass connection state into the navigation cell**

Change the cell signature to:

```python
def wizard_navigation_bar(get_step, mo, sas_backend):
```

Use the backend connection state when creating buttons:

```python
btn = mo.ui.button(
    label=label_text,
    disabled=(not sas_backend.is_connected and idx > 0),
)
```

Step 1 remains enabled while disconnected; Steps 2–5 are disabled.

- [ ] **Step 2: Guard Step 1 forward navigation**

Replace the unconditional callback with:

```python
def _go_to_step_two(_):
    if sas_backend.is_connected:
        set_step(1)


btn_next_step1 = mo.ui.button(
    label="Next: Collect Dataset Catalog >",
    kind="warn",
    on_click=_go_to_step_two,
    disabled=not sas_backend.is_connected,
)
```

This prevents stale button events from changing the step after disconnection.

- [ ] **Step 3: Run the focused tests**

Run:

```powershell
python -m pytest -q tests/test_marimo_connection_ui_guard.py
```

Expected: navigation and callback tests pass; the orchestrator test remains
red until Task 3.

### Task 3: Guard the orchestrator

**Files:**
- Modify: `src/py_sascensusapi/app.py:745-779`

- [ ] **Step 1: Receive the backend in the orchestrator cell**

Add `sas_backend` to the `wizard_orchestrator` parameters:

```python
def wizard_orchestrator(
    get_step,
    header_html,
    mo,
    nav_buttons,
    sas_backend,
    step1_card,
    step2_card,
    step3_card,
    step4_card,
    step_nav_view,
):
```

- [ ] **Step 2: Render only Step 1 while disconnected**

Build the content list conditionally:

```python
current_step = get_step()
if sas_backend.is_connected:
    steps_content = [step1_card, step2_card, step3_card, step4_card]
else:
    steps_content = [
        step1_card,
        mo.md("⚠️ Connect to SAS to continue to the next wizard steps."),
    ]

current_step = min(current_step, len(steps_content) - 1)
```

Use `steps_content[current_step]` in the existing wizard window instead of
assuming every step is available. This keeps disconnected rendering limited to
Step 1 while preserving the existing connected layout.

- [ ] **Step 3: Run tests and compile the notebook**

Run:

```powershell
python -m pytest -q tests/test_marimo_connection_ui_guard.py
python -m py_compile src/py_sascensusapi/app.py
```

Expected: all focused tests pass and compilation exits successfully.

### Task 4: Validate and commit

**Files:**
- Modify: `src/py_sascensusapi/app.py`
- Create: `tests/test_marimo_connection_ui_guard.py`

- [ ] **Step 1: Run the full test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Inspect the implementation diff**

Run:

```powershell
git --no-pager diff -- src/py_sascensusapi/app.py tests/test_marimo_connection_ui_guard.py
```

Confirm the diff is limited to connection-gated navigation, orchestrator
rendering, the Step 1 forward guard, and regression tests.

- [ ] **Step 3: Commit the implementation**

```powershell
git add src/py_sascensusapi/app.py tests/test_marimo_connection_ui_guard.py
git commit -m "feat: guard Marimo wizard UI when disconnected`n`nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
