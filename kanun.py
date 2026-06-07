#!/usr/bin/env python3
"""
Kanun Patrika - Single Executable Entry Point
Bundles everything into one .exe file.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path


def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def get_exe_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def load_env_file(path: Path):
    """Load .env file, ALWAYS overriding existing env vars."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()


def main():
    base = get_base_path()
    exe_dir = get_exe_dir()

    # Fix Windows console encoding for Nepali text
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Load .env FIRST — next to the exe, then bundled fallback
    load_env_file(exe_dir / ".env")
    load_env_file(base / ".env")

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

    # Import and run the app
    from app import app
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"\n  Kanun Patrika - Nepal Supreme Court Najir Search")
    print(f"  Starting on http://{host}:{port}")
    print(f"  Press Ctrl+C to stop\n")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
