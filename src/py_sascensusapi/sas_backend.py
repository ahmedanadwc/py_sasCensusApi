import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd

from py_sascensusapi.config import (
    SAS_PROJECT_ROOT,
    SAS_MACRO_DIRS,
    SAS_DATA_ROOT,
    DEFAULT_SAS_CFGFILE,
)

logger = logging.getLogger(__name__)

DF_CACHE_DIR = Path.home() / ".cache" / "py_sascensusapi" / "dataframes"

class SASBackend:
    """Manages the SASPy session and macro executions."""

    def __init__(self, cfgname: str = "oda", cfgfile: Optional[str] = DEFAULT_SAS_CFGFILE) -> None:
        self._sas: Optional[Any] = None
        self._cfgname: Optional[str] = cfgname
        self._cfgfile: Optional[str] = cfgfile if cfgfile else None
        self._df_cache: Dict[str, pd.DataFrame] = {}

    @property
    def is_connected(self) -> bool:
        return self._sas is not None

    def get_session(self) -> Optional[Any]:
        return self._sas

    def connect(self, cfgname: Optional[str] = None, cfgfile: Optional[str] = None) -> Tuple[bool, str]:
        """Establish a connection using SASPy."""
        if cfgname:
            self._cfgname = cfgname
        if cfgfile is not None:
            self._cfgfile = cfgfile.strip() if cfgfile.strip() else None

        try:
            # pyrefly: ignore [missing-import]
            import saspy
            kwargs: Dict[str, Any] = {}
            if self._cfgname:
                kwargs["cfgname"] = self._cfgname
            if self._cfgfile:
                kwargs["cfgfile"] = self._cfgfile

            logger.info(f"Initializing SASsession with kwargs: {kwargs}")
            self._sas = saspy.SASsession(**kwargs)

            info_str = f"cfgname='{self._cfgname}'"
            if self._cfgfile:
                info_str += f", cfgfile='{self._cfgfile}'"
            return True, f"Successfully connected to SAS ({info_str})."
        except Exception as exc:
            self._sas = None
            logger.exception("Failed to connect to SAS: %s", exc)
            return False, f"Failed to connect to SAS: {exc}"

    def disconnect(self) -> str:
        """Disconnect the active SAS session."""
        if self._sas:
            try:
                self._sas.endsas()
            except Exception as exc:
                logger.warning("Error ending SAS session: %s", exc)
            finally:
                self._sas = None
                self._cfgname = None
                self.clear_cache()
            return "SAS session ended."
        return "No active SAS session."

    def run_environment_setup(self, proj_root: str = str(SAS_PROJECT_ROOT), api_key: str = "") -> Dict[str, Any]:
        """Configure SASAUTOS, APILIB libname, and global macro variables."""
        if not self.is_connected:
            return {"success": False, "log": "SAS is not connected."}

        # Normalize slashes for SAS
        clean_root = proj_root.replace("\\", "/")
        macro_paths = ", ".join([f'"{clean_root}/code/macros/{sub}"' for sub in ["censusapi", "etl", "util"]])
        data_path = f"{clean_root}/data"
        out_path = f"{clean_root}/output"

        setup_code = f"""
/* SAS Census API Environment Initialization */
%global g_projRootPath g_apiKey g_outputRoot;
%let g_projRootPath = %str({clean_root});
%let g_outputRoot = %str({out_path});
%let g_apiKey = %str({api_key});
%let g_slash = %str(/);

/* Macro autocall directories */
options sasautos=(SASAUTOS, {macro_paths}) mautosource;

/* Options for Census API parsing */
options validvarname=any nosyntaxcheck dlcreatedir;

/* Assign APILIB libname */
libname apilib "{data_path}";
options fmtsearch=(WORK apilib);
"""
        return self.submit_code(setup_code)

    def submit_code(self, code: str) -> Dict[str, Any]:
        """Submit SAS code and return logs and execution details."""
        if not self.is_connected or self._sas is None:
            return {
                "success": False,
                "log": "Cannot execute: No active SASPy session.",
                "lst": "",
                "has_errors": True,
                "errors": ["No active SAS session"],
            }

        try:
            res = self._sas.submit(code)
            log = res.get("LOG", "")
            lst = res.get("LST", "")

            # Detect errors and warnings in SAS log
            errors = re.findall(r"^ERROR:.*$", log, flags=re.MULTILINE)
            warnings = re.findall(r"^WARNING:.*$", log, flags=re.MULTILINE)

            return {
                "success": len(errors) == 0,
                "log": log,
                "lst": lst,
                "has_errors": len(errors) > 0,
                "errors": errors,
                "warnings": warnings,
            }
        except Exception as exc:
            return {
                "success": False,
                "log": f"Exception during submission: {exc}",
                "lst": "",
                "has_errors": True,
                "errors": [str(exc)],
            }

    def clear_cache(self, disk: bool = False) -> None:
        """Drop cached DataFrames (memory always, parquet files when disk=True)."""
        self._df_cache.clear()
        if disk and DF_CACHE_DIR.exists():
            for f in DF_CACHE_DIR.glob("*.parquet"):
                f.unlink(missing_ok=True)

    def _table_stamp(self, table_name: str, libref: str) -> Optional[str]:
        """Cheap freshness token (modate|nobs) read from SAS; None if unavailable."""
        if self._sas is None:
            return None
        try:
            lib, tbl = libref.upper().replace("'", ""), table_name.upper().replace("'", "")
            self._sas.submit(
                "proc sql noprint; select put(modate, 20.6), put(nobs, 20.) "
                "into :_pyc_mod trimmed, :_pyc_nobs trimmed from dictionary.tables "
                f"where libname='{lib}' and memname='{tbl}' and memtype='DATA'; quit;"
            )
            mod, nobs = self._sas.symget("_pyc_mod"), self._sas.symget("_pyc_nobs")
            return f"{mod}|{nobs}" if mod not in ("", None) else None
        except Exception as exc:
            logger.warning("Could not read freshness stamp for %s.%s: %s", libref, table_name, exc)
            return None

    def fetch_dataframe(
        self,
        table_name: str,
        libref: str = "WORK",
        ds_opts: Dict[str, Any] = None,
        force_refresh: bool = False,
    ) -> Optional[pd.DataFrame]:
        """Retrieve a SAS table into a pandas DataFrame, cached by table, options and modify-time."""
        if not self.is_connected or self._sas is None:
            return None

        stamp = None if force_refresh else self._table_stamp(table_name, libref)
        key = None
        if stamp:
            raw = json.dumps([libref.upper(), table_name.upper(), ds_opts, stamp], sort_keys=True, default=str)
            key = hashlib.sha1(raw.encode("utf-8")).hexdigest()
            if key in self._df_cache:
                return self._df_cache[key].copy()
            parquet = DF_CACHE_DIR / f"{key}.parquet"
            if parquet.exists():
                try:
                    df = pd.read_parquet(parquet)
                    self._df_cache[key] = df
                    return df.copy()
                except Exception as exc:
                    logger.warning("Ignoring unreadable cache file %s: %s", parquet, exc)

        try:
            sas_data = self._sas.sasdata(table_name, libref, dsopts=ds_opts)
            df = sas_data.to_df()
        except Exception as exc:
            logger.warning("Could not convert SAS table %s.%s to DataFrame: %s", libref, table_name, exc)
            return None

        if key is not None and df is not None:
            self._df_cache[key] = df
            try:
                DF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                df.to_parquet(DF_CACHE_DIR / f"{key}.parquet")
            except Exception as exc:
                logger.info("Parquet cache write skipped for %s.%s: %s", libref, table_name, exc)
        return df.copy() if df is not None else None


# Global singleton instance for the Streamlit app
sas_backend = SASBackend()
