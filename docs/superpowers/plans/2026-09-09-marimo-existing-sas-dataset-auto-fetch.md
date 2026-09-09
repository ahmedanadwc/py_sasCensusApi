# Marimo Existing SAS Dataset Auto-Fetch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Marimo Step 2 automatically display an existing configured SAS dataset when connected, matching the Streamlit behavior without treating the dataset as a completed macro execution.

**Architecture:** Keep the behavior inside the reactive `step2_view` cell. Use the current form values (or defaults before submission), guard the fetch with both “form not submitted” and `sas_backend.is_connected`, and populate the existing status/log/preview render slots only for a non-empty DataFrame. Preserve the submitted-form path as the authoritative macro execution flow.

**Tech Stack:** Python 3.13+, Marimo, pandas DataFrames, pytest, existing `SASBackend.fetch_dataframe`.

---

### Task 1: Add regression tests for Marimo auto-fetch behavior

**Files:**
- Create: `tests/test_marimo_existing_dataset_auto_fetch.py`

- [ ] **Step 1: Add source-level tests for the connected and disconnected branches**

Create the test module with assertions against the `step2_view` source:

```python
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
    assert "if step2_form.value is not None:" in text
    assert "elif sas_backend.is_connected:" in text
    assert "existing_df = sas_backend.fetch_dataframe(out_tbl, out_lib)" in text


def test_auto_fetch_renders_existing_dataset_status_log_and_preview():
    text = step2_view_source()
    assert "Fetched existing SAS data set" in text
    assert '"📋 SAS Log (auto-fetch)"' in text
    assert "mo.ui.table(existing_df, pagination=True)" in text
    assert "Loaded existing dataset" in text


def test_submitted_step_two_path_remains_macro_execution_path():
    text = step2_view_source()
    submitted_branch = text[
        text.index("if step2_form.value is not None:") :
        text.index("elif sas_backend.is_connected:")
    ]
    assert "step2_res = sas_backend.submit_code(sas_code_step2)" in submitted_branch
    assert "sas_backend.fetch_dataframe(out_tbl, out_lib)" in submitted_branch
```

- [ ] **Step 2: Run the focused tests and confirm the current implementation is covered**

Run:

```powershell
python -m pytest -q tests\test_marimo_existing_dataset_auto_fetch.py
```

Expected: PASS for the existing preliminary auto-fetch implementation. If an assertion fails, use that failure to identify the exact rendering or branch difference before changing application code.

- [ ] **Step 3: Commit the regression tests**

```powershell
git add tests\test_marimo_existing_dataset_auto_fetch.py
git commit -m "test: cover Marimo existing dataset auto-fetch" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 2: Align the Marimo Step 2 implementation with the approved behavior

**Files:**
- Modify: `src/py_sascensusapi/app.py:step2_view`

- [ ] **Step 1: Inspect the existing Step 2 render slots and preserve the submitted path**

Keep these existing invariants while editing:

```python
step2_exec_status = None
step2_log_display = None
step2_table_view = None

out_tbl = step2_vals["p_outDsName"]
out_lib = step2_vals["p_outLibName"]

if step2_form.value is not None:
    # submit_code(...) remains the only macro execution path
```

Do not move the fetch before the `step2_form.value is not None` branch, because a submitted form must not be mistaken for an auto-fetch render.

- [ ] **Step 2: Implement the guarded existing-dataset fetch**

Use this exact branch shape for the non-submitted case:

```python
elif sas_backend.is_connected:
    existing_df = sas_backend.fetch_dataframe(out_tbl, out_lib)
    if existing_df is not None and not existing_df.empty:
        step2_exec_status = mo.md(
            "✅ **Step 2: Fetched existing SAS data set** — no macro execution needed."
        )
        step2_log_display = mo.accordion({
            "📋 SAS Log (auto-fetch)": mo.ui.code_editor(
                value=(
                    f"/* Loaded existing dataset {out_lib}.{out_tbl} "
                    "from active SAS session */"
                ),
                language="sql",
                disabled=True,
            )
        })
        step2_table_view = mo.vstack([
            mo.md(
                f"#### 📊 Dataset Preview: `{out_lib}.{out_tbl}` "
                f"({len(existing_df)} rows, {len(existing_df.columns)} columns)"
            ),
            mo.ui.table(existing_df, pagination=True),
        ])
```

This ensures disconnected sessions do not call the backend, empty/missing datasets do not produce a success message, and the existing form/code preview remains visible.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
python -m pytest -q tests\test_marimo_existing_dataset_auto_fetch.py tests\test_marimo_connection_ui_guard.py
```

Expected: all focused source-level tests pass.

- [ ] **Step 4: Commit the implementation**

```powershell
git add src\py_sascensusapi\app.py
git commit -m "feat: auto-fetch existing SAS data in Marimo Step 2" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

### Task 3: Validate notebook syntax, Marimo structure, and full behavior

**Files:**
- Test: `tests/test_marimo_existing_dataset_auto_fetch.py`
- Test: `tests/test_marimo_connection_ui_guard.py`
- Test: existing project test suite

- [ ] **Step 1: Compile the Marimo source**

Run:

```powershell
python -m py_compile src\py_sascensusapi\app.py
```

Expected: exit code 0 with no syntax errors.

- [ ] **Step 2: Run Marimo’s notebook check**

Run:

```powershell
python -m marimo check src\py_sascensusapi\app.py
```

Expected: Marimo reports the notebook is valid and exits successfully.

- [ ] **Step 3: Run the complete test suite**

Run:

```powershell
python -m pytest -q
```

Expected: all project tests pass, including the new auto-fetch regression tests.

- [ ] **Step 4: Review the final diff and working tree**

Run:

```powershell
git --no-pager diff HEAD~2 -- src\py_sascensusapi\app.py tests\test_marimo_existing_dataset_auto_fetch.py
git status --short --branch
```

Confirm that only the intended application/test changes are part of the feature commits and that existing session artifacts and generated directories remain untouched.
