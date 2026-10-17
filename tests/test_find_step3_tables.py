from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from py_sascensusapi.app import find_step3_tables, resolve_step3_uid, _clean_df_for_grid


def test_find_step3_tables_exact_match():
    # Simulated VTABLE member names
    mock_members = pd.DataFrame({
        "memname": [
            "_45_CPS_1995_VARS",
            "_45_CPS_1995_GRPS",
            "_45_CPS_1995_GEOS",
            "_45_CPS_1995_EXMPLS",
            "OTHER_TABLE",
        ]
    })
    with patch("py_sascensusapi.app.sas_backend.fetch_dataframe", return_value=mock_members):
        found = find_step3_tables(ds_unique_id="_45_CPS_1995", libname="APILIB")
        assert found == {
            "Variables": "_45_CPS_1995_VARS",
            "Groups": "_45_CPS_1995_GRPS",
            "Geographies": "_45_CPS_1995_GEOS",
            "Sample Queries": "_45_CPS_1995_EXMPLS",
        }


def test_find_step3_tables_truncated_32_chars():
    # In SAS, member names are capped at 32 chars:
    # Full: _1234_INTERNATIONAL_DATABASE_2020_EXMPLS (40 chars)
    # Truncated by SAS to 32 chars: _1234_INTERNATIONAL_DATABASE_20
    long_uid = "_1234_INTERNATIONAL_DATABASE_2020"
    mock_members = pd.DataFrame({
        "memname": [
            f"{long_uid}_VARS"[:32],
            f"{long_uid}_GRPS"[:32],
            f"{long_uid}_GEOS"[:32],
            f"{long_uid}_EXMPLS"[:32],
        ]
    })
    with patch("py_sascensusapi.app.sas_backend.fetch_dataframe", return_value=mock_members):
        found = find_step3_tables(ds_unique_id=long_uid, libname="APILIB")
        assert len(found) == 4
        assert found["Variables"] == f"{long_uid}_VARS"[:32]
        assert found["Sample Queries"] == f"{long_uid}_EXMPLS"[:32]


def test_find_step3_tables_by_row_id():
    # When ds_unique_id differs in formatting or is empty, but row_id is provided
    mock_members = pd.DataFrame({
        "memname": [
            "_789_DEC_SF1_2000_VARS",
            "_789_DEC_SF1_2000_GRPS",
            "_789_DEC_SF1_2000_GEOS",
            "_789_DEC_SF1_2000_EXMPLS",
        ]
    })
    with patch("py_sascensusapi.app.sas_backend.fetch_dataframe", return_value=mock_members):
        found = find_step3_tables(row_id=789, libname="MYLIB")
        assert found == {
            "Variables": "_789_DEC_SF1_2000_VARS",
            "Groups": "_789_DEC_SF1_2000_GRPS",
            "Geographies": "_789_DEC_SF1_2000_GEOS",
            "Sample Queries": "_789_DEC_SF1_2000_EXMPLS",
        }


def test_resolve_step3_uid():
    mock_df = pd.DataFrame({
        "_ROWID_": ["1", "2", "45"],
        "ds_unique_id": ["_1_DEC_2000", "_2_ACS_2010", "_45_CPS_1995"],
    })
    with patch("streamlit.session_state", {"step2_result": {"df": mock_df}}):
        resolved = resolve_step3_uid("45", default_uid="fallback")
        assert resolved == "_45_CPS_1995"

        missing = resolve_step3_uid("999", default_uid="fallback")
        assert missing == "fallback"


def test_clean_df_for_grid():
    df = pd.DataFrame({
        "str_col": ["a", "b"],
        "obj_col": [{"x": 1}, None],
        "date_col": pd.date_range("2020-01-01", periods=2),
    })
    cleaned = _clean_df_for_grid(df)
    assert cleaned["obj_col"].iloc[0] == "{'x': 1}"
    assert cleaned["obj_col"].iloc[1] == ""
    assert isinstance(cleaned["date_col"].iloc[0], str)
