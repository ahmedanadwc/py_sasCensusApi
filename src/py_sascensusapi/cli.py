import argparse
import os
import subprocess
import sys
from pathlib import Path

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="py-sascensusapi",
        description="Launch Marimo Studio for SAS Census API",
    )
    parser.add_argument(
        "--mode",
        choices=["edit", "run"],
        default="edit",
        help="Launch in interactive 'edit' mode or web application 'run' mode (default: edit)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=2718,
        help="Port to serve Marimo on (default: 2718)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    app_path = Path(__file__).parent / "app.py"

    cmd = [
        sys.executable,
        "-m",
        "marimo",
        args.mode,
        str(app_path),
        "--port",
        str(args.port),
        "--host",
        args.host,
    ]

    print(f"Starting Marimo in '{args.mode}' mode...")
    print(f"File: {app_path}")
    print(f"Serving at: http://{args.host}:{args.port}")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
