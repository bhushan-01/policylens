"""Environment/config loading: process env plus the project's .env file (never committed)."""

from __future__ import annotations

import os

from policylens.paths import ROOT


def load_env() -> dict[str, str]:
    values = dict(os.environ)
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            values.setdefault(key.strip(), val.strip().strip('"').strip("'"))
    return values
