#!/usr/bin/env python3
"""Run one Obsidian sync pass, or defer to the existing continuous writer."""
from pathlib import Path
import subprocess
import sys


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if '--continuous' in args:
        print('single-sync.py is one-shot; use continuous-sync.py for the supervisor.', file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, str(Path(__file__).with_name('bootstrap-vault.py')), *args]).returncode


if __name__ == '__main__':
    sys.exit(main())
