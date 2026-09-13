"""Replay winding repair and supported medallions into a separate scene."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("rebuild.py")), init_globals={
    "CORRECT_WINDING": True, "BACK_MEDALLIONS": True,
    "OUTPUT_SUBDIR": "rebuild-supported"
})
