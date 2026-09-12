import bpy,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def tick():
 p=ROOT/'outputs/job.py'
 if p.exists():
  code=p.read_text();p.rename(ROOT/'outputs/last_job.py')
  try: exec(compile(code,str(p),'exec'),{'ROOT':ROOT,'__name__':'__main__'})
  except Exception: traceback.print_exc()
  print('JOB_DONE',flush=True)
 return 1.0
bpy.app.timers.register(tick,first_interval=2.0,persistent=True)
