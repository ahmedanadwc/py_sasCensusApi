# Marimo Existing SAS Dataset Auto-Fetch

## Goal

Match the Streamlit Step 2 behavior in the Marimo notebook by automatically
checking for the configured output SAS dataset when Step 2 is displayed and
the user has not submitted the Step 2 form.

## Behavior

- The current Step 2 form values are used for `p_outLibName` and
  `p_outDsName`. Defaults are used before the form has a value.
- Auto-fetch runs only when:
  - `step2_form.value is None`, and
  - `sas_backend.is_connected` is true.
- Auto-fetch calls
  `sas_backend.fetch_dataframe(out_tbl, out_lib)`.
- When a non-empty DataFrame is returned, Step 2 displays:
  - a success message explaining that existing SAS data was loaded without
    macro execution;
  - a read-only SAS-log-style note identifying the loaded dataset; and
  - a paginated dataset preview.
- A missing or empty dataset produces no success-shaped status and leaves the
  generated SAS code and form available.
- When the form is submitted, the existing behavior remains authoritative:
  run the Step 2 macro when connected, display its result/log, and fetch the
  output dataset only after a successful execution.
- Auto-fetch is display-only. It does not mark the Step 2 macro as executed and
  does not unlock later wizard steps by itself.
- Backend fetch errors continue to follow the backend's existing behavior; this
  change does not add broad exception swallowing or fabricate a successful
  result.

## Scope and implementation shape

The change is limited to the Marimo `step2_view` cell in
`src/py_sascensusapi/app.py`. Existing reactive form dependencies and the
connection guard remain in place. A small source-level regression test module
will verify the connected and disconnected branches, the non-empty-data
rendering, and the submitted-form path.

## Validation

Run the project test suite, compile the notebook source, and run Marimo's
notebook check:

```text
python -m pytest -q
python -m py_compile src\py_sascensusapi\app.py
python -m marimo check src\py_sascensusapi\app.py
```
