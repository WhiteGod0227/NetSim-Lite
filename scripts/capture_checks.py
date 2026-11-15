"""Capture clean, UTF-8 verification logs and preserve command exit codes."""
from pathlib import Path
import json
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
out=root/'deliverables'/'verification'
out.mkdir(parents=True,exist_ok=True)
checks=[('backend-tests',[sys.executable,'-m','unittest','discover','-s','tests','-v'],root),
        ('frontend-build',['cmd','/d','/c','npm.cmd','run','build'],root/'frontend'),
        ('browser-tests',['node','node_modules/@playwright/test/cli.js','test'],root/'frontend')]
results=[]
for name,command,cwd in checks:
 result=subprocess.run(command,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8',errors='replace')
 (out/f'{name}.txt').write_text('Command: '+' '.join(command)+'\nExit code: '+str(result.returncode)+'\n\n'+result.stdout,encoding='utf-8')
 results.append({'check':name,'exit_code':result.returncode})
 print(f'{name}: {result.returncode}',flush=True)
(out/'checks.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
if any(item['exit_code'] for item in results):sys.exit(1)
