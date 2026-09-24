from pathlib import Path
import os,sys,json
R=Path(__file__).resolve().parents[1];os.chdir(R);sys.path.insert(0,str(R))
from streamlit.testing.v1 import AppTest
out=[]
for p in [R/'app.py']+sorted((R/'apps').glob('*/app.py')):
 try:
  a=AppTest.from_file(str(p),default_timeout=120).run()
  item={'app':str(p.relative_to(R)),'exceptions':[x.message for x in a.exception],'errors':[x.value for x in a.error],'buttons':[x.label for x in a.button],'contact':any('Interested in this app' in x.value for x in a.header)}
 except Exception as e:item={'app':str(p),'exception':str(e)}
 out.append(item);print(json.dumps(item),flush=True)
assert all(not row.get('exceptions') and not row.get('errors') and not row.get('exception') and row.get('contact') for row in out), out
