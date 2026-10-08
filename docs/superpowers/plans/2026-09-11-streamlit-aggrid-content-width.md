# Streamlit AgGrid Content-Width Column Sizing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Streamlit dataset preview size every AgGrid column to its longest header or cell value while preserving selection and horizontal scrolling.

**Architecture:** Keep the existing grid in `streamlit_app.py`. Attach a `JsCode` callback to `firstDataRendered`, collect every column ID, and call `autoSizeColumns` after row data is available. Keep `fit_columns_on_grid_load=False` so viewport fitting does not override content sizing.

**Tech Stack:** Python, Streamlit, `st-aggrid`, JavaScript injected through `JsCode`.

---

### Task 1: Update the AgGrid content-sizing callback

**Files:**
- Modify: `streamlit_app.py:460-484`

- [ ] **Step 1: Confirm the current grid behavior**

Read the existing dataset preview block and verify it uses `GridOptionsBuilder.from_dataframe(df)`, `fit_columns_on_grid_load=False`, and a JavaScript callback.

- [ ] **Step 2: Replace the callback with post-render sizing**

Use the following callback and attach it to `firstDataRendered`:

```python
auto_size_columns = JsCode(
    """
    function(params) {
        const columnIds = [];
        params.api.getColumns().forEach(column => {
            columnIds.push(column.getColId());
        });
        params.api.autoSizeColumns(columnIds, true);
    }
    """
)
grid_options = gb.build()
grid_options["firstDataRendered"] = auto_size_columns
```

Keep the existing `allow_unsafe_jscode=True` and `fit_columns_on_grid_load=False` arguments in the `AgGrid` call. The JavaScript boolean must be lowercase `true`.

- [ ] **Step 3: Inspect the focused diff**

Run:

```powershell
git --no-pager diff -- streamlit_app.py
```

Expected: only the AgGrid callback/event configuration changes; unrelated working-tree modifications remain untouched.

- [ ] **Step 4: Run available validation**

Run:

```powershell
uv run python -m compileall streamlit_app.py
```

Expected: the file compiles without syntax errors. If `uv` is unavailable, run the repository's configured Python executable with `python -m compileall streamlit_app.py`.

- [ ] **Step 5: Commit the implementation**

```powershell
git add streamlit_app.py
git commit -m "fix: autosize Streamlit AgGrid columns" -m "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
