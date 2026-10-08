# Graph Report - py_sasCensusApi  (2026-10-02)

## Corpus Check
- 42 files · ~27,721 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .graphify-bak 1, .lock 1)

## Summary
- 178 nodes · 221 edges · 23 communities (7 shown, 16 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8806b79a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- streamlit_app.py
- fetch_census_catalog
- The tools
- graft-hooks.cjs
- test_streamlit_connection_visibility.py
- SASBackend
- AGENTS.md
- test_sas_backend_cache.py
- find_row_index
- GEMINI.md
- CBP 2000 Examples File List
- graft
- Codacy Rules (AI behavior config)
- Plan: Streamlit AgGrid Content-Width
- copilot-instructions.md
- Plan: Sequential Wizard Navigation
- Plan: Streamlit Session Environment Visibility
- py-sascensusapi
- rules/graphify.md
- workflows/graphify.md
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `SASBackend` - 12 edges
2. `_load_highest_unlocked_step()` - 9 edges
3. `The tools` - 7 edges
4. `FakeSAS` - 6 edges
5. `graft` - 6 edges
6. `best()` - 4 edges
7. `entry()` - 4 edges
8. `best()` - 4 edges
9. `entry()` - 4 edges
10. `fetch_census_catalog()` - 4 edges

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

## Communities (23 total, 16 thin omitted)

### Community 0 - "streamlit_app.py"
Cohesion: 0.09
Nodes (6): _resolve_sas_project_root(), highest_unlocked_step(), extract_sas_config_names(), find_step3_tables(), highest_unlocked_step(), normalize_selected_row()

### Community 2 - "The tools"
Cohesion: 0.15
Nodes (12): 1 · `graft ask "<question>" --source`: locate + understand (the default), 2 · `graft grep "<pattern>"`: exhaustive find, 3 · `graft skeleton <file>`: a file's API at a glance, 4 · `graft callers <symbol>`: the exact edges, 5 · `graft map`: orientation for an unfamiliar repo or area, 6 · Lifecycle: `graft build` / `graft check`, graft, Report what graft saved, every turn (+4 more)

### Community 3 - "graft-hooks.cjs"
Cohesion: 0.10
Nodes (20): best(), entry(), { execFileSync }, fromPkg(), fs, globalRoot(), newer(), path (+12 more)

### Community 4 - "test_streamlit_connection_visibility.py"
Cohesion: 0.18
Nodes (9): _load_highest_unlocked_step(), test_connection_unlocks_dataset_catalog_step(), test_disconnect_relocks_wizard_even_with_previous_results(), test_endpoint_unlocks_query_builder_step(), test_failed_step2_result_does_not_unlock_dataset_profile_step(), test_failed_step3_result_does_not_unlock_catalog_search_step(), test_initial_state_unlocks_only_connection_step(), test_step2_result_unlocks_dataset_profile_step() (+1 more)

### Community 7 - "test_sas_backend_cache.py"
Cohesion: 0.14
Nodes (6): main(), FakeSAS, FakeSD, make(), test_disk_cache_survives_new_backend_and_force_refresh_bypasses(), test_second_fetch_hits_cache_and_modify_time_invalidates()

### Community 10 - "CBP 2000 Examples File List"
Cohesion: 0.50
Nodes (4): CBP 2000 Examples File List, CBP 2000 Geographies, CBP 2000 Groups, CBP 2000 Variables

### Community 11 - "graft"
Cohesion: 0.50
Nodes (3): npx, graft, @nanonets/graft

## Knowledge Gaps
- **37 isolated node(s):** `path`, `fs`, `{ pathToFileURL }`, `{ execFileSync }`, `path` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 93 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SASBackend` connect `SASBackend` to `streamlit_app.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **What connects `path`, `fs`, `{ pathToFileURL }` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `streamlit_app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08858858858858859 - nodes in this community are weakly interconnected._
- **Should `graft-hooks.cjs` be split into smaller, more focused modules?**
  _Cohesion score 0.10344827586206896 - nodes in this community are weakly interconnected._
- **Should `SASBackend` be split into smaller, more focused modules?**
  _Cohesion score 0.12380952380952381 - nodes in this community are weakly interconnected._
- **Should `test_sas_backend_cache.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1437908496732026 - nodes in this community are weakly interconnected._