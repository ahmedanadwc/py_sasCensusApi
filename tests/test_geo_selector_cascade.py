import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

SRC = str(Path(__file__).parents[1] / "src")


def _app():
    import streamlit as st
    from py_sascensusapi.geo_lookup import load_geo_rows
    from py_sascensusapi.geo_selector_dialog import render_geo_multiselects

    selection = render_geo_multiselects(load_geo_rows())
    st.write("STATES=" + ",".join(r["state_abbrev"] for r in selection))


def _run():
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    at = AppTest.from_function(_app, default_timeout=30)
    at.run()
    at.multiselect(key="geo_dlg_regions").set_value(["Northeast (1)", "Midwest (2)"]).run()
    at.multiselect(key="geo_dlg_divisions").set_value(["New England (1)", "East North Central (3)"]).run()
    at.multiselect(key="geo_dlg_states").set_value(["Connecticut - CT (09)", "Illinois - IL (17)"]).run()
    return at


def _values(at):
    return (
        at.multiselect(key="geo_dlg_regions").value,
        at.multiselect(key="geo_dlg_divisions").value,
        at.multiselect(key="geo_dlg_states").value,
    )


def test_removing_a_region_removes_its_divisions_and_states_only():
    at = _run()
    at.multiselect(key="geo_dlg_regions").set_value(["Midwest (2)"]).run()
    assert _values(at) == (["Midwest (2)"], ["East North Central (3)"], ["Illinois - IL (17)"])
    assert not at.exception


def test_clearing_regions_clears_everything_below():
    at = _run()
    at.multiselect(key="geo_dlg_regions").set_value([]).run()
    assert _values(at) == ([], [], [])


def test_removing_a_division_removes_only_its_states():
    at = _run()
    at.multiselect(key="geo_dlg_divisions").set_value(["East North Central (3)"]).run()
    assert _values(at) == (["Northeast (1)", "Midwest (2)"], ["East North Central (3)"], ["Illinois - IL (17)"])


def _seeded_app():
    import streamlit as st
    from py_sascensusapi.geo_lookup import load_geo_rows, selection_from_in_clause
    from py_sascensusapi.geo_selector_dialog import render_geo_multiselects, seed_from_selection

    rows = load_geo_rows()
    selection, _ = selection_from_in_clause(rows, "in=state:09,23,17")
    seed_from_selection(selection)
    render_geo_multiselects(rows)


def test_dialog_preselects_states_and_parents_from_in_clause():
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    at = AppTest.from_function(_seeded_app, default_timeout=30)
    at.run()
    assert not at.exception
    assert _values(at) == (
        ["Northeast (1)", "Midwest (2)"],
        ["New England (1)", "East North Central (3)"],
        ["Connecticut - CT (09)", "Maine - ME (23)", "Illinois - IL (17)"],
    )
