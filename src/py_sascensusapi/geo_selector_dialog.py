"""Cascading Region > Division > State multi-select dialog."""

from __future__ import annotations

from typing import Callable

import streamlit as st

from py_sascensusapi.geo_lookup import (
    build_selection,
    division_options,
    load_geo_rows,
    region_options,
    state_options,
)

REGIONS_KEY = "geo_dlg_regions"
DIVISIONS_KEY = "geo_dlg_divisions"
STATES_KEY = "geo_dlg_states"


def _prune(key: str, options: list[str]) -> None:
    """Drop selected values that are no longer valid options (cascading reset)."""
    st.session_state[key] = [v for v in st.session_state.get(key, []) if v in options]


def _seed_from_selection(selection: list[dict]) -> None:
    """Pre-fill the dialog from the last applied selection when it opens."""
    if REGIONS_KEY in st.session_state:
        return
    st.session_state[REGIONS_KEY] = list(dict.fromkeys(r["region"] for r in selection))
    st.session_state[DIVISIONS_KEY] = list(dict.fromkeys(r["division"] for r in selection))
    st.session_state[STATES_KEY] = list(
        dict.fromkeys(f"{r['state']} ({r['state_abbrev']})" for r in selection)
    )


@st.dialog("Select Geography", width="large")
def geo_selector_dialog(on_apply: Callable[[list[dict]], None] | None = None) -> None:
    """Pick regions, then divisions, then states; Apply stores the full paths and reruns the app."""
    rows = load_geo_rows()
    _seed_from_selection(st.session_state.get("geo_selection") or [])

    col_region, col_division, col_state = st.columns(3)

    with col_region:
        regions_all = region_options(rows)
        _prune(REGIONS_KEY, regions_all)
        regions = st.multiselect("Regions", regions_all, key=REGIONS_KEY)

    with col_division:
        divisions_all = division_options(rows, regions)
        _prune(DIVISIONS_KEY, divisions_all)
        divisions = st.multiselect(
            "Divisions", divisions_all, key=DIVISIONS_KEY, disabled=not regions
        )

    with col_state:
        states_all = state_options(rows, divisions)
        _prune(STATES_KEY, states_all)
        states = st.multiselect("States", states_all, key=STATES_KEY, disabled=not divisions)

    selection = build_selection(rows, regions, divisions, states)
    st.caption(f"{len(selection)} state(s) selected")

    if st.button("Apply", type="primary", disabled=not selection, key="geo_dlg_apply"):
        st.session_state.geo_selection = selection
        if on_apply is not None:
            on_apply(selection)
        st.rerun()
