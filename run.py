#!/usr/bin/env python3
"""Convenience launcher used by Docker and local development."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable when launched directly.
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.__main__ import main


if __name__ == "__main__":
    main()
