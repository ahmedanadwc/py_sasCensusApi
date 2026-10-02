import argparse
import subprocess
import sys
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="py-sascensusapi",
        description="Launch Streamlit app for SAS Census API",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to serve Streamlit on (default: 8501)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    app_path = Path(__file__).parent / "streamlit_app.py"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(args.port),
        "--server.address",
        args.host,
    ]

    print("Starting Streamlit...")
    print(f"File: {app_path}")
    print(f"Serving at: http://{args.host}:{args.port}")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
