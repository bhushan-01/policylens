"""Filesystem locations, independent of the current working directory."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
EVALS_DIR = ROOT / "evals"
EXAMPLES_DIR = ROOT / "examples"
