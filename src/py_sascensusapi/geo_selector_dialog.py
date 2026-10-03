"""Cascading Region > Division > State multi-select dialog."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from py_sascensusapi.geo_lookup import (
    build_selection,
    division_label,
    division_options,
    load_geo_rows,
    region_label,
    region_options,
    selection_from_in_clause,
    state_label,
    state_options,
)

REGIONS_KEY = "geo_dlg_regions"
DIVISIONS_KEY = "geo_dlg_divisions"
STATES_KEY = "geo_dlg_states"
RESEED_KEY = "geo_dlg_reseed"
INITIAL_KEY = "geo_dlg_initial"
UNMATCHED_KEY = "geo_dlg_unmatched"


def _keep_valid(key: str, options: list[str]) -> None:
    """Keep only the selected values of `key` that are still valid options."""
    st.session_state[key] = [v for v in st.session_state.get(key, []) if v in options]


def cascade_from_regions() -> None:
    """on_change for Regions: drop divisions, then states, whose parents are no longer selected."""
    rows = load_geo_rows()
    _keep_valid(DIVISIONS_KEY, division_options(rows, st.session_state.get(REGIONS_KEY, [])))
    cascade_from_divisions()


def cascade_from_divisions() -> None:
    """on_change for Divisions: drop states whose division is no longer selected."""
    rows = load_geo_rows()
    _keep_valid(STATES_KEY, state_options(rows, st.session_state.get(DIVISIONS_KEY, [])))


def seed_from_selection(selection: list[dict]) -> None:
    """Pre-fill the widgets from `selection` when the dialog is (re)opened."""
    if REGIONS_KEY in st.session_state and not st.session_state.get(RESEED_KEY):
        return
    st.session_state[REGIONS_KEY] = list(dict.fromkeys(region_label(r) for r in selection))
    st.session_state[DIVISIONS_KEY] = list(dict.fromkeys(division_label(r) for r in selection))
    st.session_state[STATES_KEY] = list(dict.fromkeys(state_label(r) for r in selection))
    st.session_state[RESEED_KEY] = False


def render_geo_multiselects(rows: list[dict]) -> list[dict]:
    """Render the three linked multiselects and return the selected full paths.

    Removing a parent value (via the widget's x or Clear) immediately removes its children and
    grandchildren through the on_change callbacks, so no orphaned selections remain.
    """
    col_region, col_division, col_state = st.columns(3)

    with col_region:
        regions = st.multiselect(
            "Regions", region_options(rows), key=REGIONS_KEY, on_change=cascade_from_regions
        )
    with col_division:
        divisions = st.multiselect(
            "Divisions",
            division_options(rows, regions),
            key=DIVISIONS_KEY,
            on_change=cascade_from_divisions,
            disabled=not regions,
        )
    with col_state:
        states = st.multiselect(
            "States", state_options(rows, divisions), key=STATES_KEY, disabled=not divisions
        )

    # build_selection also requires each state's parents to be selected, as a final safeguard
    return build_selection(rows, regions, divisions, states)


@st.dialog("Select Geography", width="large")
def geo_selector_dialog(on_apply: Callable[[list[dict]], None] | None = None) -> None:
    """Pick regions, then divisions, then states; Apply stores the full paths and reruns the app."""
    rows = load_geo_rows()
    seed_from_selection(st.session_state.get(INITIAL_KEY) or [])

    unmatched = st.session_state.get(UNMATCHED_KEY) or []
    if unmatched:
        st.warning(
            "These in= values are not in the lookup and will be dropped on Apply: " + ", ".join(unmatched)
        )

    selection = render_geo_multiselects(rows)
    st.caption(f"{len(selection)} state(s) selected")

    if st.button("Apply", type="primary", disabled=not selection, key="geo_dlg_apply"):
        st.session_state.geo_selection = selection
        if on_apply is not None:
            on_apply(selection)
        st.rerun()


def open_geo_dialog(
    in_clause_text: str, on_apply: Callable[[list[dict]], None] | None = None
) -> None:
    """Open the dialog pre-selected from the current in= clause text (e.g. the p_apiInClause field)."""
    selection, unmatched = selection_from_in_clause(load_geo_rows(), in_clause_text)
    st.session_state[INITIAL_KEY] = selection
    st.session_state[UNMATCHED_KEY] = unmatched
    st.session_state[RESEED_KEY] = True
    geo_selector_dialog(on_apply)
