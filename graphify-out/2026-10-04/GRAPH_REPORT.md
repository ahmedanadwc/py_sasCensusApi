# Graph Report - py_sasCensusApi  (2026-10-04)

## Corpus Check
- 44 files · ~32,849 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .graphify-bak 1, .lock 1)

## Summary
- 265 nodes · 390 edges · 25 communities (12 shown, 13 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cd9795de`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- streamlit_app.py
- test_geo_lookup.py
- The tools
- graft-hooks.cjs
- test_streamlit_connection_visibility.py
- SASBackend
- AGENTS.md
- test_sas_backend_cache.py
- geo_lookup.py
- GEMINI.md
- CBP 2000 Examples File List
- graft
- Codacy Rules (AI behavior config)
- Plan: Streamlit AgGrid Content-Width
- copilot-instructions.md
- Plan: Sequential Wizard Navigation
- Plan: Streamlit Session Environment Visibility
- py-sascensusapi
- test_geo_selector_cascade.py
- rules/graphify.md
- workflows/graphify.md
- CLAUDE.md
- sas_backend.py

## God Nodes (most connected - your core abstractions)
1. `load_geo_rows()` - 12 edges
2. `SASBackend` - 12 edges
3. `render_geo_multiselects()` - 11 edges
4. `division_options()` - 8 edges
5. `state_options()` - 8 edges
6. `_rows()` - 8 edges
7. `region_label()` - 7 edges
8. `division_label()` - 7 edges
9. `build_selection()` - 7 edges
10. `cascade_from_regions()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `_app()` --calls--> `load_geo_rows()`  [INFERRED]
  tests/test_geo_selector_cascade.py → src/py_sascensusapi/geo_lookup.py
- `_app()` --calls--> `render_geo_multiselects()`  [INFERRED]
  tests/test_geo_selector_cascade.py → src/py_sascensusapi/geo_selector_dialog.py
- `_seeded_app()` --calls--> `load_geo_rows()`  [INFERRED]
  tests/test_geo_selector_cascade.py → src/py_sascensusapi/geo_lookup.py
- `_seeded_app()` --calls--> `selection_from_in_clause()`  [INFERRED]
  tests/test_geo_selector_cascade.py → src/py_sascensusapi/geo_lookup.py
- `apply_geo_selection()` --calls--> `merge_in_clause()`  [EXTRACTED]
  streamlit_app.py → src/py_sascensusapi/geo_lookup.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Census Business Patterns 2000 Dataset Components** — cbp_2000_exmpls, cbp_2000_geos, cbp_2000_grps, cbp_2000_vars [EXTRACTED 1.00]

## Communities (25 total, 13 thin omitted)

### Community 0 - "streamlit_app.py"
Cohesion: 0.07
Nodes (11): apply_geo_selection(), extract_sas_config_names(), find_row_index(), find_step3_tables(), highest_unlocked_step(), names_to_csv(), normalize_selected_row(), parse_example_url() (+3 more)

### Community 1 - "test_geo_lookup.py"
Cohesion: 0.19
Nodes (9): main(), _rows(), test_build_selection_drops_states_whose_parents_are_not_selected(), test_flatten_gives_one_full_path_per_state(), test_in_clause_uses_state_fips_and_is_empty_without_selection(), test_labels_show_the_key_next_to_the_name(), test_merge_in_clause_replaces_state_part_and_keeps_others(), test_options_cascade_from_regions_to_divisions_to_states() (+1 more)

### Community 2 - "The tools"
Cohesion: 0.15
Nodes (12): 1 · `graft ask "<question>" --source`: locate + understand (the default), 2 · `graft grep "<pattern>"`: exhaustive find, 3 · `graft skeleton <file>`: a file's API at a glance, 4 · `graft callers <symbol>`: the exact edges, 5 · `graft map`: orientation for an unfamiliar repo or area, 6 · Lifecycle: `graft build` / `graft check`, graft, Report what graft saved, every turn (+4 more)

### Community 3 - "graft-hooks.cjs"
Cohesion: 0.10
Nodes (20): best(), entry(), { execFileSync }, fromPkg(), fs, globalRoot(), newer(), path (+12 more)

### Community 4 - "test_streamlit_connection_visibility.py"
Cohesion: 0.14
Nodes (11): _load_function(), _load_highest_unlocked_step(), test_connection_unlocks_dataset_catalog_step(), test_disconnect_relocks_wizard_even_with_previous_results(), test_failed_step2_result_does_not_unlock_dataset_profile_step(), test_initial_state_unlocks_only_connection_step(), test_names_to_csv_joins_selected_name_values(), test_parse_example_url_handles_missing_and_multiple_in_clauses() (+3 more)

### Community 5 - "SASBackend"
Cohesion: 0.10
Nodes (3): _read_parquet(), SASBackend, _write_parquet()

### Community 7 - "test_sas_backend_cache.py"
Cohesion: 0.21
Nodes (5): FakeSAS, FakeSD, make(), test_disk_cache_survives_new_backend_and_force_refresh_bypasses(), test_second_fetch_hits_cache_and_modify_time_invalidates()

### Community 8 - "geo_lookup.py"
Cohesion: 0.08
Nodes (23): build_selection(), division_label(), division_options(), find_geo_json(), flatten_hierarchy(), in_clause(), load_geo_rows(), merge_in_clause() (+15 more)

### Community 10 - "CBP 2000 Examples File List"
Cohesion: 0.50
Nodes (4): CBP 2000 Examples File List, CBP 2000 Geographies, CBP 2000 Groups, CBP 2000 Variables

### Community 11 - "graft"
Cohesion: 0.50
Nodes (3): npx, graft, @nanonets/graft

### Community 20 - "test_geo_selector_cascade.py"
Cohesion: 0.44
Nodes (7): _app(), _run(), test_clearing_regions_clears_everything_below(), test_dialog_preselects_states_and_parents_from_in_clause(), test_removing_a_division_removes_only_its_states(), test_removing_a_region_removes_its_divisions_and_states_only(), _values()

### Community 24 - "sas_backend.py"
Cohesion: 0.11
Nodes (3): fetch_census_catalog(), search_datasets(), _resolve_sas_project_root()

## Knowledge Gaps
- **37 isolated node(s):** `path`, `fs`, `{ pathToFileURL }`, `{ execFileSync }`, `path` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 128 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SASBackend` connect `SASBackend` to `sas_backend.py`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `load_geo_rows()` connect `geo_lookup.py` to `test_geo_selector_cascade.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `load_geo_rows()` (e.g. with `_app()` and `_seeded_app()`) actually correct?**
  _`load_geo_rows()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `render_geo_multiselects()` (e.g. with `cascade_from_divisions()` and `cascade_from_regions()`) actually correct?**
  _`render_geo_multiselects()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `path`, `fs`, `{ pathToFileURL }` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `streamlit_app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07407407407407407 - nodes in this community are weakly interconnected._
- **Should `graft-hooks.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.10344827586206896 - nodes in this community are weakly interconnected._