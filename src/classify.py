"""
Simple PolicyLens CLI: describe a product → retrieve + answer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from answer import main as answer_main


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/classify.py \"Your AI product description\"")
        print('Example: python src/classify.py "We build CV screening software for HR teams"')
        sys.exit(1)
    answer_main()
