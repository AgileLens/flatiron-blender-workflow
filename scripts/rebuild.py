"""Replays the successful live MCP geometry steps in a fresh Blender GUI scene."""
from pathlib import Path
import json, runpy, bpy
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT / "outputs" / globals().get("OUTPUT_SUBDIR", "rebuild")
BASE.mkdir(parents=True, exist_ok=True)
if globals().get("BACK_MEDALLIONS", False) and not globals().get("CORRECT_WINDING", False):
    raise ValueError("Medallion backing requires the diagnosed winding correction first")
source=(ROOT/"scripts"/"flatiron_base.py").read_text()
if globals().get("CORRECT_WINDING", False):
    source=runpy.run_path(str(ROOT/"scripts"/"winding.py"))["corrected_source"](source)
(BASE/"flatiron.py").write_text(source)
steps=json.loads((ROOT/"scripts"/"live_steps.json").read_text())
for index, step in enumerate(steps):
    if globals().get("BACK_MEDALLIONS", False) and index == len(steps)-1:
        marker="\ns=bpy.context.scene\n"
        if step.count(marker) != 1:
            raise ValueError("Final replay step changed; refusing an unverified backing insertion")
        repair="\nrunpy.run_path(str(ROOT/'scripts'/'backed_rings.py'))['apply_to_blender']()\n"
        step=step.replace(marker, repair+marker, 1)
        save="bpy.ops.wm.save_as_mainfile("
        if step.count(save) != 1:
            raise ValueError("Final replay save changed; refusing an unverified insertion")
        note="s['validation_status']='Opt-in candidate: winding repaired and raised medallions backed; original acceptance does not transfer.'\n"
        step=step.replace(save,note+save,1)
    exec(step.replace("${base}",str(BASE)),globals())
