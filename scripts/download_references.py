"""Download the credited original reference set into ignored outputs/references."""
from pathlib import Path
import json,urllib.request
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/references';out.mkdir(parents=True,exist_ok=True)
for item in json.loads((ROOT/'docs/photo-sources.json').read_text()):
 p=out/item['input']
 if p.exists():continue
 req=urllib.request.Request(item['download'],headers={'User-Agent':'FlatironBlenderWorkflow/1.0 (https://github.com/AgileLens/flatiron-blender-workflow)'})
 with urllib.request.urlopen(req,timeout=60) as response:
  if not response.headers.get('Content-Type','').startswith('image/'):raise RuntimeError('Expected image response')
  data=response.read()
 p.write_bytes(data);print(item['input'],item['artist'],item['license'])
