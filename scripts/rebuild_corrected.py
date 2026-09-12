"""Replay the diagnosed winding correction into a separate candidate scene."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("rebuild.py")), init_globals={
    "CORRECT_WINDING": True, "OUTPUT_SUBDIR": "rebuild-corrected"
})
