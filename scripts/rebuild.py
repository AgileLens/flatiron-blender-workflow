"""Replays the successful live MCP geometry steps in a fresh Blender GUI scene."""
from pathlib import Path
import json, runpy, bpy
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT / "outputs" / globals().get("OUTPUT_SUBDIR", "rebuild")
BASE.mkdir(parents=True, exist_ok=True)
source=(ROOT/"scripts"/"flatiron_base.py").read_text()
if globals().get("CORRECT_WINDING", False):
    source=runpy.run_path(str(ROOT/"scripts"/"winding.py"))["corrected_source"](source)
(BASE/"flatiron.py").write_text(source)
for step in json.loads((ROOT/"scripts"/"live_steps.json").read_text()):
    exec(step.replace("${base}",str(BASE)),globals())
