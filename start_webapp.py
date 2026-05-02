#!/usr/bin/env python3
"""
start_webapp.py — Launch the KPVS Web Interface
================================================
Usage:
  python start_webapp.py                    # http://localhost:8000
  python start_webapp.py --port 8080
  python start_webapp.py --host 0.0.0.0    # network-accessible

Opens the browser automatically unless --no-browser is passed.
"""

import argparse
import os
import sys
import webbrowser
from threading import Timer

# ── project root on path ─────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def open_browser(url: str, delay: float = 1.5) -> None:
    """Open browser after a short delay to let server start."""
    def _open():
        webbrowser.open(url)
    Timer(delay, _open).start()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="KPVS Web Interface — Key Person Vulnerability Simulator"
    )
    parser.add_argument("--host",       default="127.0.0.1",
                        help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port",       type=int, default=8000,
                        help="Port to bind (default: 8000)")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open browser automatically")
    parser.add_argument("--reload",     action="store_true",
                        help="Enable auto-reload for development")
    parser.add_argument("--log-level",  default="info",
                        choices=["debug","info","warning","error"],
                        help="Uvicorn log level (default: info)")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"

    print(f"""
╔══════════════════════════════════════════════════════════╗
║   KPVS Web Interface v1.1.0                              ║
║   Key Person Vulnerability Simulator                     ║
║   MTS Research Programme — Working Paper 5               ║
╠══════════════════════════════════════════════════════════╣
║   URL   : {url:<49}║
║   Reports stored in : reports/                           ║
║   JSON runs stored  : runs/                              ║
╠══════════════════════════════════════════════════════════╣
║   Press Ctrl+C to stop                                   ║
╚══════════════════════════════════════════════════════════╝
""")

    if not args.no_browser:
        open_browser(url)

    import uvicorn
    uvicorn.run(
        "kpvs.webapp.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
