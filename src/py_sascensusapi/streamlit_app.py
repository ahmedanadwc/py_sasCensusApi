import os
import sys
from pathlib import Path

# Ensure package root is in sys.path
_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

# Forward to root streamlit_app implementation or re-use directly
_ROOT_APP = Path(__file__).resolve().parent.parent.parent / "streamlit_app.py"
if _ROOT_APP.exists():
    with open(_ROOT_APP, "r", encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, str(_ROOT_APP), "exec"))
