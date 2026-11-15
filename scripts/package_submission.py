"""Create a portable source archive and validate generated document structure."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json
from docx import Document
from pptx import Presentation

root=Path(__file__).resolve().parents[1]
out=root/'deliverables'
required=['NetSim_Lite_Report.docx','NetSim_Lite_Report.pdf','NetSim_Lite_Presentation.pptx','NetSim_Lite_Demo.webm']
for filename in required:
 assert (out/filename).stat().st_size>1000,filename
doc=Document(out/'NetSim_Lite_Report.docx')
assert len(doc.inline_shapes)==8
prs=Presentation(out/'NetSim_Lite_Presentation.pptx')
assert len(prs.slides)==14
for i,slide in enumerate(prs.slides,1):
 assert slide.has_notes_slide,f'Slide {i} lacks notes'
 for shape in slide.shapes:
  assert shape.left>=0 and shape.top>=0,(i,shape.name,'negative position')
  assert shape.left+shape.width<=prs.slide_width+10,(i,shape.name,'right overflow')
  assert shape.top+shape.height<=prs.slide_height+10,(i,shape.name,'bottom overflow')

files=[]
for folder in ['backend','tests','scripts','frontend/src','frontend/tests','frontend/scripts']:
 files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(root/p for p in ['.gitignore','README.md','BUGFIXES.md','start.ps1','project-guide.txt','Dockerfile','.dockerignore','.env.example','compose.yaml','render.yaml','DEPLOYMENT.md','app.py','requirements.txt','.python-version','vercel.json','.vercelignore'])
files.extend(p for p in (root/'frontend').iterdir() if p.is_file())
files.extend(p for p in out.iterdir() if p.suffix in ['.md','.json'])
archive=out/'NetSim_Lite_Source.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
 for p in sorted(set(files)):z.write(p,p.relative_to(root).as_posix())
with ZipFile(archive) as z:
 assert z.testzip() is None
 assert 'frontend/package-lock.json' in z.namelist()
 assert 'backend/core.py' in z.namelist()
 assert not any('/node_modules/' in n or '/.venv/' in n for n in z.namelist())
 count=len(z.namelist())
result={'docx_images':len(doc.inline_shapes),'pptx_slides':len(prs.slides),'pptx_bounds':'pass','pptx_notes':'all 14 slides','source_archive_files':count,'source_archive_crc':'pass','identity_placeholders':'Awaiting user details; editable in submission-details.json','native_office_rendering':'Not available; review DOCX/PPTX in Office before institutional submission.'}
(out/'verification/document-validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
checksums=[]
for p in sorted(out.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS.txt':checksums.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(out).as_posix()}')
(out/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
