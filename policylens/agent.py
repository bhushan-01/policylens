"""
Legacy entry point — redirects to the Evidence Tribunal.

The old free-form tool-calling agent is replaced by an adversarial proof ledger
(`policylens.tribunal`). Keep this module so existing `python -m policylens.agent`
and docs links still work.
"""

from __future__ import annotations

import sys

from policylens.tribunal import main as tribunal_main


def main():
    # Preserve `--workflow` as a quiet alias for offline tribunal markdown.
    args = [a for a in sys.argv[1:] if a != "--workflow"]
    tribunal_main(args)


if __name__ == "__main__":
    main()
