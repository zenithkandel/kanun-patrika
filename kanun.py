#!/usr/bin/env python3
"""
Kanun Patrika - Single Executable Entry Point
Bundles everything into one .exe file.
"""

import os
import sys
import tempfile
import shutil
import sqlite3
from pathlib import Path


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def main():
    base = get_base_path()

    # When frozen, extract assets to a temp directory
    if getattr(sys, 'frozen', False):
        work_dir = Path(tempfile.gettempdir()) / "kanun_patrika"
        work_dir.mkdir(exist_ok=True)

        # Copy database if not present
        db_dest = work_dir / "decisions.db"
        db_source = base / "decisions.db"
        if not db_dest.exists() and db_source.exists():
            shutil.copy2(db_source, db_dest)

        os.chdir(str(work_dir))
    else:
        os.chdir(str(base))

    # Set environment
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")

    # Load .env if present (dev mode)
    env_file = base / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if key not in os.environ:
                    os.environ[key] = val

    # Import and run the app
    from app import app
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"\n  कानून पत्रिका — Nepal Supreme Court Nājir Search")
    print(f"  Starting on http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
