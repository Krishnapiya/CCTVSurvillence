#!/usr/bin/env python3
"""Run one master sync cycle from the command line (no API server required)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Allow running as: python scripts/run_master_sync.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.master_sync_agent import run_master_sync_cycle


def main() -> int:
    result = asyncio.run(run_master_sync_cycle())
    print(json.dumps(result, indent=2, default=str))
    if result.get("error"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
