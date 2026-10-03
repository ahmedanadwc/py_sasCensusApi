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
    divisions = geo.division_options(rows, ["Northeast"])
    assert divisions == ["New England", "Middle Atlantic"]
    states = geo.state_options(rows, ["New England"])
    assert "Connecticut (CT)" in states and "New Jersey (NJ)" not in states


def test_build_selection_drops_states_whose_parents_are_not_selected():
    rows = _rows()
    selection = geo.build_selection(
        rows, ["Northeast"], ["New England"], ["Connecticut (CT)", "Maine (ME)", "New Jersey (NJ)"]
    )
    assert [r["state_abbrev"] for r in selection] == ["CT", "ME"]


def test_in_clause_uses_state_fips_and_is_empty_without_selection():
    rows = _rows()
    selection = geo.build_selection(
        rows, ["Northeast"], ["New England"], ["Connecticut (CT)", "Maine (ME)"]
    )
    assert geo.in_clause(selection) == "in=state:09,23"
    assert geo.in_clause([]) == ""
