import json

from py_sascensusapi import geo_lookup as geo


def _rows():
    return geo.flatten_hierarchy(json.loads(geo.find_geo_json().read_text(encoding="utf-8")))


def test_flatten_gives_one_full_path_per_state():
    rows = _rows()
    assert len(rows) >= 50
    ct = next(r for r in rows if r["state_fips"] == "09")
    assert ct == {
        "region": "Northeast",
        "region_id": "1",
        "division": "New England",
        "division_id": "1",
        "state": "Connecticut",
        "state_fips": "09",
        "state_abbrev": "CT",
    }


def test_options_cascade_from_regions_to_divisions_to_states():
    rows = _rows()
    assert geo.division_options(rows, []) == []
    divisions = geo.division_options(rows, ["Northeast (1)"])
    assert divisions == ["New England (1)", "Middle Atlantic (2)"]
    states = geo.state_options(rows, ["New England (1)"])
    assert "Connecticut - CT (09)" in states and "New Jersey - NJ (34)" not in states


def test_build_selection_drops_states_whose_parents_are_not_selected():
    rows = _rows()
    selection = geo.build_selection(
        rows, ["Northeast (1)"], ["New England (1)"], ["Connecticut - CT (09)", "Maine - ME (23)", "New Jersey - NJ (34)"]
    )
    assert [r["state_abbrev"] for r in selection] == ["CT", "ME"]


def test_in_clause_uses_state_fips_and_is_empty_without_selection():
    rows = _rows()
    selection = geo.build_selection(
        rows, ["Northeast (1)"], ["New England (1)"], ["Connecticut - CT (09)", "Maine - ME (23)"]
    )
    assert geo.in_clause(selection) == "in=state:09,23"
    assert geo.in_clause([]) == ""


def test_labels_show_the_key_next_to_the_name():
    rows = _rows()
    ct = next(r for r in rows if r["state_fips"] == "09")
    assert geo.region_label(ct) == "Northeast (1)"
    assert geo.division_label(ct) == "New England (1)"
    assert geo.state_label(ct) == "Connecticut - CT (09)"


def test_parse_state_fips_reads_state_values_and_ignores_other_parts():
    assert geo.parse_state_fips("in=state:09,23, 5") == ["09", "23", "05"]
    assert geo.parse_state_fips("in=state:06&in=county:037") == ["06"]
    assert geo.parse_state_fips("in=county:037") == []
    assert geo.parse_state_fips("in=state:*") == ["*"]
    assert geo.parse_state_fips("") == []


def test_selection_from_in_clause_reports_unknown_values():
    rows = _rows()
    selection, unmatched = geo.selection_from_in_clause(rows, "in=state:09,23,99")
    assert [r["state_abbrev"] for r in selection] == ["CT", "ME"]
    assert unmatched == ["99"]
    all_states, _ = geo.selection_from_in_clause(rows, "in=state:*")
    assert len(all_states) == len(rows)


def test_merge_in_clause_replaces_state_part_and_keeps_others():
    rows = _rows()
    selection, _ = geo.selection_from_in_clause(rows, "in=state:09,23")
    assert geo.merge_in_clause("in=state:01&in=county:037", selection) == "in=state:09,23&in=county:037"
    assert geo.merge_in_clause("in=state:01", []) == ""
    assert geo.merge_in_clause("", selection) == "in=state:09,23"
