"""Census region / division / state lookups built from census_reg_div_lkup.json."""

from __future__ import annotations

import json
import re
from pathlib import Path

import streamlit as st

_PKG_DIR = Path(__file__).resolve().parent
GEO_JSON_NAME = "census_reg_div_lkup.json"
# Package folder first, then the repository root (where the file currently lives).
GEO_JSON_CANDIDATES = [_PKG_DIR / GEO_JSON_NAME, _PKG_DIR.parents[1] / GEO_JSON_NAME]


def find_geo_json() -> Path:
    """Return the first existing lookup JSON path, or raise FileNotFoundError."""
    for candidate in GEO_JSON_CANDIDATES:
        if candidate.exists():
            return candidate
    searched = ", ".join(str(c) for c in GEO_JSON_CANDIDATES)
    raise FileNotFoundError(f"{GEO_JSON_NAME} not found (searched: {searched})")


def flatten_hierarchy(data: dict) -> list[dict]:
    """Flatten the region > division > state JSON into one full-path dict per state."""
    rows: list[dict] = []
    for region_id, region in data.get("census_regions", {}).items():
        for division_id, division in region.get("divisions", {}).items():
            for fips, state in division.get("states", {}).items():
                rows.append(
                    {
                        "region": region.get("name", ""),
                        "region_id": str(region_id),
                        "division": division.get("name", ""),
                        "division_id": str(division_id),
                        "state": state.get("name", ""),
                        "state_fips": str(fips),
                        "state_abbrev": state.get("abbreviation", ""),
                    }
                )
    return rows


@st.cache_data(show_spinner=False)
def load_geo_rows(path: str | None = None) -> list[dict]:
    """Load and flatten the lookup JSON once (cached)."""
    json_path = Path(path) if path else find_geo_json()
    with open(json_path, "r", encoding="utf-8") as f:
        return flatten_hierarchy(json.load(f))


def _unique(values) -> list[str]:
    return list(dict.fromkeys(values))


def region_label(row: dict) -> str:
    """Display label for a region option, e.g. 'Northeast (1)'."""
    return f"{row['region']} ({row['region_id']})"


def division_label(row: dict) -> str:
    """Display label for a division option, e.g. 'New England (1)'."""
    return f"{row['division']} ({row['division_id']})"


def state_label(row: dict) -> str:
    """Display label for a state option, e.g. 'Connecticut - CT (09)'."""
    return f"{row['state']} - {row['state_abbrev']} ({row['state_fips']})"


def region_options(rows: list[dict]) -> list[str]:
    return _unique(region_label(r) for r in rows)


def division_options(rows: list[dict], regions: list[str]) -> list[str]:
    """Division labels that belong to any of the selected region labels."""
    return _unique(division_label(r) for r in rows if region_label(r) in regions)


def state_options(rows: list[dict], divisions: list[str]) -> list[str]:
    """State labels that belong to any of the selected division labels."""
    return _unique(state_label(r) for r in rows if division_label(r) in divisions)


def build_selection(
    rows: list[dict], regions: list[str], divisions: list[str], states: list[str]
) -> list[dict]:
    """One full-path dict per selected state, kept only if its region and division are selected too.

    `regions`, `divisions` and `states` are the display labels ('<Name> (key)').
    """
    return [
        dict(r)
        for r in rows
        if region_label(r) in regions and division_label(r) in divisions and state_label(r) in states
    ]


def in_clause(selection: list[dict]) -> str:
    """Build the Census API in= clause from selected states, or '' when nothing is selected."""
    fips = _unique(r["state_fips"] for r in selection)
    return f"in=state:{','.join(fips)}" if fips else ""


_STATE_PART = re.compile(r"^(?:in=)?state:", re.IGNORECASE)


def parse_state_fips(in_text: str) -> list[str]:
    """Extract the state FIPS codes from an in= clause such as 'in=state:09,23' (['*'] for state:*).

    Other in= parameters (county:..., etc.) are ignored; single digits are zero padded.
    """
    fips: list[str] = []
    for part in str(in_text or "").split("&"):
        part = part.strip()
        if _STATE_PART.match(part):
            for value in re.split(r"[,\s]+", part.split(":", 1)[1].strip()):
                if value:
                    fips.append(value if value == "*" else value.zfill(2))
    return _unique(fips)


def selection_from_in_clause(rows: list[dict], in_text: str) -> tuple[list[dict], list[str]]:
    """Map the states in an in= clause to full-path rows; also return values not in the lookup."""
    fips = parse_state_fips(in_text)
    if "*" in fips:
        return [dict(r) for r in rows], []
    known = {r["state_fips"] for r in rows}
    selection = [dict(r) for r in rows if r["state_fips"] in fips]
    return selection, [f for f in fips if f not in known]


def merge_in_clause(existing: str, selection: list[dict]) -> str:
    """Replace the state part of an in= clause with the selection, keeping any other in= parts."""
    others = [
        p.strip()
        for p in str(existing or "").split("&")
        if p.strip() and not _STATE_PART.match(p.strip())
    ]
    return "&".join(part for part in [in_clause(selection), *others] if part)
