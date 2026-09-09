# Sequential Wizard Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate Streamlit sidebar and forward navigation so users can only enter steps whose prerequisites are complete.

**Architecture:** Add a pure `highest_unlocked_step` helper near `set_step()` that evaluates the current SAS connection and existing session-state result fields. Use its result for sidebar button disabling and guard every forward transition with the same prerequisite checks, while preserving backward navigation and existing step operations.

**Tech Stack:** Python, Streamlit, pytest.

---

### Task 1: Add unlock-rule tests

**Files:**
- Modify: `tests/test_streamlit_connection_visibility.py`
- Modify: `streamlit_app.py`

- [ ] **Step 1: Add a testable unlock helper contract**

Add tests that import the helper without executing Streamlit UI code. The helper
must accept explicit state values so its rules can be tested independently:

```python
from streamlit_app import highest_unlocked_step


def test_only_step_one_is_unlocked_initially():
    assert highest_unlocked_step(
        sas_connected=False,
        step2_result=None,
        step3_result=None,
        picked_endpoint="",
    ) == 0


def test_connection_unlocks_step_two():
    assert highest_unlocked_step(
        sas_connected=True,
        step2_result=None,
        step3_result=None,
        picked_endpoint="",
    ) == 1


def test_step_two_result_unlocks_step_three():
    assert highest_unlocked_step(
        sas_connected=True,
        step2_result={"success": True},
        step3_result=None,
        picked_endpoint="",
    ) == 2


def test_step_three_result_unlocks_step_four():
    assert highest_unlocked_step(
        sas_connected=True,
        step2_result={"success": True},
        step3_result={"success": True},
        picked_endpoint="",
    ) == 3


def test_endpoint_unlocks_step_five():
    assert highest_unlocked_step(
        sas_connected=True,
        step2_result={"success": True},
        step3_result={"success": True},
        picked_endpoint="https://api.census.gov/data/2000/dec/sf1?",
    ) == 4


def test_disconnect_relocks_steps_after_step_one():
    assert highest_unlocked_step(
        sas_connected=False,
        step2_result={"success": True},
        step3_result={"success": True},
        picked_endpoint="https://api.census.gov/data/2000/dec/sf1?",
    ) == 0
```

- [ ] **Step 2: Run the tests before implementation**

Run:

```powershell
python -m pytest -q tests/test_streamlit_connection_visibility.py
```

Expected: collection fails because `highest_unlocked_step` does not yet exist.

### Task 2: Implement centralized unlock logic

**Files:**
- Modify: `streamlit_app.py:157-160`

- [ ] **Step 1: Add the pure helper**

Add this function immediately before `set_step()`:

```python
def highest_unlocked_step(
    sas_connected: bool,
    step2_result: dict | None,
    step3_result: dict | None,
    picked_endpoint: str,
) -> int:
    """Return the highest step index currently available to the user."""
    if not sas_connected:
        return 0
    if step2_result is None:
        return 1
    if step3_result is None:
        return 2
    if not picked_endpoint.strip():
        return 3
    return 4
```

- [ ] **Step 2: Run the helper tests**

Run:

```powershell
python -m pytest -q tests/test_streamlit_connection_visibility.py
```

Expected: all unlock-rule tests pass.

### Task 3: Gate sidebar and forward navigation

**Files:**
- Modify: `streamlit_app.py:164-175, 343-344, 452-453, 522-523, 586-587`

- [ ] **Step 1: Compute the current unlocked step before rendering navigation**

Immediately before `with st.sidebar:`, add:

```python
unlocked_step = highest_unlocked_step(
    sas_connected=sas_backend.is_connected,
    step2_result=st.session_state.step2_result,
    step3_result=st.session_state.step3_result,
    picked_endpoint=st.session_state.picked_endpoint,
)
```

- [ ] **Step 2: Disable locked sidebar buttons**

Add `disabled=i > unlocked_step` to the existing `st.button` call:

```python
if st.button(
    f"{prefix}Step {i+1}: {s['short']}",
    key=f"nav_btn_{i}",
    use_container_width=True,
    type="primary" if is_active else "secondary",
    disabled=i > unlocked_step,
):
    set_step(i)
```

- [ ] **Step 3: Guard each forward transition**

Use the same `unlocked_step` value for each Next button:

```python
if st.button("Next: Collect Dataset Catalog >", type="primary", use_container_width=True):
    if unlocked_step >= 1:
        set_step(1)
```

Apply the equivalent guard for transitions to steps 2, 3, and 4. Do not add
guards to Back buttons. The endpoint application action already sets
`picked_endpoint` before rerunning, so Step 5 becomes available automatically.

- [ ] **Step 4: Run tests and compile**

Run:

```powershell
python -m pytest -q tests/test_streamlit_connection_visibility.py
python -m py_compile streamlit_app.py src\py_sascensusapi\streamlit_app.py
```

Expected: all tests pass and both entry points compile without errors.

### Task 4: Review and commit the implementation

**Files:**
- Modify: `streamlit_app.py`
- Modify: `tests/test_streamlit_connection_visibility.py`

- [ ] **Step 1: Inspect the diff**

Run:

```powershell
git --no-pager diff -- streamlit_app.py tests/test_streamlit_connection_visibility.py
```

Confirm the diff contains only the helper, navigation gates, and focused tests.

- [ ] **Step 2: Run the full available test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Commit**

```powershell
git add streamlit_app.py tests/test_streamlit_connection_visibility.py
git commit -m "feat: enforce sequential Streamlit wizard navigation`n`nCo-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
