# py_sasCensusApi

[![CI](https://github.com/ahmedanadwc/py_sasCensusApi/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmedanadwc/py_sasCensusApi/actions/workflows/ci.yml)

A **Streamlit‑based wizard** for configuring and running the U.S. Census API via **SASPy**, giving developers a quick, visual way to explore the Census API catalog, pick variables, and generate queries. It guides you through SAS session connection, catalog download, dataset profiling, and query generation, all from a friendly web UI.

---

## 📦 Overview

- **Step 1** – Connect to a SAS session (or work offline).
- **Step 2** – Pull the full Census API catalog into a SAS dataset.
- **Step 3** – Explore variables, groups, geographies and craft a query.
- **Step 4** – Execute the query and export results.

The app ships with a minimal Python wrapper (`py_sascensusapi`) that abstracts SAS‑macro calls, plus utility functions for geography selection.

---

## 🚀 Installation

```bash
# Clone the repo
git clone https://github.com/ahmedanadwc/py_sasCensusApi.git
cd py_sasCensusApi

# Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/Scripts/activate  # Windows PowerShell
# or: source .venv/bin/activate  # Unix

# Install required packages
pip install -r requirements.txt
```

> **Note** – The repository ignores the large `graphify-out/` folder via `.gitignore` to keep the repo lightweight.

---

## 🎮 Running the app

```bash
streamlit run streamlit_app.py
```

Open the URL shown by Streamlit (usually `http://localhost:8501`) in your browser and follow the on‑screen wizard.

---

## 🧪 Testing

The project uses **pytest** for unit tests located in the `tests/` directory.

```bash
pytest -q
```

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically runs these tests on every push and pull request.

---

## 🛡️ CI Badge

![CI](https://github.com/ahmedanadwc/py_sasCensusApi/actions/workflows/ci.yml/badge.svg)

---

## 🔍 Analysis

* **Purpose**: Provide an interactive web UI for configuring SASPy and querying the US Census API.
* **Key components**:
  - `streamlit_app.py`: UI orchestration, step navigation, SAS session state handling.
  - `py_sascensusapi` package:
    - `sas_backend.py`: Wrapper around SASPy for connection, code submission, data fetch.
    - `census_catalog.py`: Downloads and parses the Census `data.json` catalog.
    - `geo_lookup.py` & `geo_selector_dialog.py`: Helpers for geography selection and query construction.
  - `graphify` assets: optional knowledge‑graph of the codebase for future introspection (excluded from repo via `.gitignore`).
* **Workflow**:
  1. **Connect** – Select `sascfg` file, connect via SASPy, set macro autocall paths.
  2. **Catalog** – Run `%censusapi_getAllDataSets` macro; results stored in `APILIB._API_ALL_DATA`.
  3. **Profile** – Pick a dataset row; discover related SAS tables (`_VARS`, `_GRPS`, `_GEOS`, `_EXMPLS`).
  4. **Query** – Choose variables, geographies, build `GET … FOR … IN …` clause; optionally edit via dialog.
  5. **Execute** – Run `%censusapi_getDsFullInfo` macro; fetch results into pandas for download.

The app is designed for **rapid prototyping** of Census queries while leveraging existing SAS macros, making it useful for analysts who already work in a SAS environment.

## ✨ Features

- Developers want a quick, visual way to explore the Census API catalog, pick variables, and generate exact SAS macro calls without hand‑crafting the query strings.
- Offline / export mode: Even without a live SAS session, the wizard can generate the SAS code for later execution.

## How it works under the hood

1. SASPy establishes a Python‑to‑SAS bridge (`sas_backend.connect`).
2. The `%censusapi_getAllDataSets` macro builds a master dataset of all available Census endpoints.
3. When a dataset row is selected, `find_step3_tables()` inspects `SASHELP.VTABLE` to locate the corresponding SAS tables (`_VARS`, `_GRPS`, …).
4. The UI renders these tables with Ag‑Grid, allowing multi‑row selection and variable filtering.
5. Geography selections are turned into an `in=` clause via `merge_in_clause()` and stored in `st.session_state.step3_query_fields`.
6. Finally, the composed query is passed to `%censusapi_getDsFullInfo`, and the result is returned to Python as a Pandas DataFrame for inspection/export.

## Core components

| Component | Role |
|---|---|
| `streamlit_app.py` | UI layer that orchestrates the wizard, defines step navigation, and calls helper functions from the package. |
| `py_sascensusapi/sas_backend.py` | Thin wrapper around SASPy that handles connection, runs SAS code, and fetches data frames. |
| `py_sascensusapi/census_catalog.py` | Implements `search_datasets()` – parses the JSON catalog and returns a tidy DataFrame for Step 2. |
| `py_sascensusapi/geo_selector_dialog.py` | Opens a modal dialog to let users pick states/counties/etc. – the geography selector used in Step 3. |

## 📦 Utility: `geo_lookup.py`

Utility functions that translate UI selections into the `in=` clause of the Census API request.

### Intended use‑case

- Data analysts who prefer SAS (or have existing SAS macros) but need to pull Census data programmatically.
- Developers want a quick, visual way to explore the Census API catalog, pick variables, and generate the exact SAS macro calls without hand‑crafting the query strings.
- Offline / export mode: Even without a live SAS session, the wizard can generate the SAS code for later execution.

### How it works under the hood

1. SASPy establishes a Python‑to‑SAS bridge (`sas_backend.connect`).
2. The `%censusapi_getAllDataSets` macro builds a master dataset of all available Census endpoints.
3. When a dataset row is selected, `find_step3_tables()` inspects `SASHELP.VTABLE` to locate the corresponding SAS tables (`_VARS`, `_GRPS`, …).
4. The UI renders these tables with Ag‑Grid, allowing multi‑row selection and variable filtering.
5. Geography selections are turned into an `in=` clause via `merge_in_clause()` and stored in `st.session_state`.

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
