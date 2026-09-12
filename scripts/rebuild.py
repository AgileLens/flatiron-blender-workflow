"""Replays the successful live MCP geometry steps in a fresh Blender GUI scene."""
from pathlib import Path
import json, bpy
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT / "outputs" / "rebuild"
BASE.mkdir(parents=True, exist_ok=True)
import shutil
shutil.copy2(ROOT/"scripts"/"flatiron_base.py", BASE/"flatiron.py")
for step in json.loads((ROOT/"scripts"/"live_steps.json").read_text()):
    exec(step.replace("${base}",str(BASE)),globals())
