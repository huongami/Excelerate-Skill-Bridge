#!/usr/bin/env python3
"""Start Jinder: python start.py [--demo] [--port 8095] [--reset-db]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jinder.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
