"""pytest path setup: make `src/`, `conjectures/`, and the repo root importable."""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for sub in ("", "src", "conjectures"):
    path = os.path.join(ROOT, sub) if sub else ROOT
    if path not in sys.path:
        sys.path.insert(0, path)
