# Graph Report - py_sasCensusApi  (2026-10-03)

## Corpus Check
- 41 files · ~26,066 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .graphify-bak 1, .lock 1)

## Summary
- 194 nodes · 239 edges · 23 communities (9 shown, 14 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `22f08654`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- sas_backend.py
- The tools
- graft-hooks.cjs
- test_streamlit_connection_visibility.py
- SASBackend
- AGENTS.md
- test_sas_backend_cache.py
- streamlit_app.py
- GEMINI.md
- CBP 2000 Examples File List
- graft
- Codacy Rules (AI behavior config)
- Plan: Streamlit AgGrid Content-Width
- copilot-instructions.md
- Plan: Sequential Wizard Navigation
- Plan: Streamlit Session Environment Visibility
- py-sascensusapi
- cli.py
- rules/graphify.md
- workflows/graphify.md
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `SASBackend` - 12 edges
2. `_load_highest_unlocked_step()` - 7 edges
3. `The tools` - 7 edges
4. `FakeSAS` - 6 edges
5. `_load_function()` - 6 edges
6. `graft` - 6 edges
7. `_read_parquet()` - 5 edges
8. `_write_parquet()` - 5 edges
9. `best()` - 4 edges
10. `entry()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Plan: Streamlit AgGrid Content-Width` --references--> `Spec: Streamlit AgGrid Content-Width Design`  [EXTRACTED]
  docs/superpowers/plans/2026-09-11-streamlit-aggrid-content-width.md → docs/superpowers/specs/2026-09-11-streamlit-aggrid-content-width-design.md
- `Plan: Sequential Wizard Navigation` --references--> `Spec: Sequential Wizard Navigation Design`  [EXTRACTED]
  docs/superpowers/plans/2026-09-09-sequential-wizard-navigation.md → docs/superpowers/specs/2026-09-09-sequential-wizard-navigation-design.md
- `Plan: Streamlit Session Environment Visibility` --references--> `Spec: Streamlit Session Environment Visibility Design`  [EXTRACTED]
  docs/superpowers/plans/2026-09-09-streamlit-session-environment-visibility.md → docs/superpowers/specs/2026-09-09-streamlit-session-environment-visibility-design.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Census Business Patterns 2000 Dataset Components** — cbp_2000_exmpls, cbp_2000_geos, cbp_2000_grps, cbp_2000_vars [EXTRACTED 1.00]

## Communities (23 total, 14 thin omitted)

### Community 0 - "sas_backend.py"
Cohesion: 0.11
Nodes (3): fetch_census_catalog(), search_datasets(), _resolve_sas_project_root()

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
Cohesion: 0.23
Nodes (5): FakeSAS, FakeSD, make(), test_disk_cache_survives_new_backend_and_force_refresh_bypasses(), test_second_fetch_hits_cache_and_modify_time_invalidates()

### Community 8 - "streamlit_app.py"
Cohesion: 0.08
Nodes (10): extract_sas_config_names(), find_row_index(), find_step3_tables(), highest_unlocked_step(), names_to_csv(), normalize_selected_row(), parse_example_url(), render_grid() (+2 more)

### Community 10 - "CBP 2000 Examples File List"
Cohesion: 0.50
Nodes (4): CBP 2000 Examples File List, CBP 2000 Geographies, CBP 2000 Groups, CBP 2000 Variables

### Community 11 - "graft"
Cohesion: 0.50
Nodes (3): npx, graft, @nanonets/graft

## Knowledge Gaps
- **37 isolated node(s):** `path`, `fs`, `{ pathToFileURL }`, `{ execFileSync }`, `path` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 101 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SASBackend` connect `SASBackend` to `sas_backend.py`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `_read_parquet()` connect `SASBackend` to `sas_backend.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **What connects `path`, `fs`, `{ pathToFileURL }` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `sas_backend.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10541310541310542 - nodes in this community are weakly interconnected._
- **Should `graft-hooks.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.10344827586206896 - nodes in this community are weakly interconnected._
- **Should `test_streamlit_connection_visibility.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `SASBackend` be split into smaller, more focused modules?**
  _Cohesion score 0.10461538461538461 - nodes in this community are weakly interconnected._