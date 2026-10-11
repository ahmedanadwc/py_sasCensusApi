"""Dev launcher: `streamlit run streamlit_app.py` (the app itself lives in the package)."""
import runpy
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

runpy.run_module("py_sascensusapi.app", run_name="__main__")
