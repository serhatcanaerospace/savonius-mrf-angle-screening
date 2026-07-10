"""Compatibility launcher for the -90 degree case."""
import runpy
import sys
from pathlib import Path

if len(sys.argv) == 1:
    sys.argv.append(str(Path(__file__).resolve().parents[1] / "savonius_mrf_rot90cw"))
runpy.run_path(str(Path(__file__).with_name("analyze_blade.py")), run_name="__main__")
