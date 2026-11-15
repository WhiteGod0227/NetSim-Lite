"""Create the deployment source ZIP without dependencies, media, or secrets."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib

root = Path(__file__).resolve().parents[1]
files = [root / name for name in ['Dockerfile', '.dockerignore', '.env.example', '.gitignore', 'compose.yaml', 'render.yaml', 'DEPLOYMENT.md', 'README.md', 'start.ps1']]
for folder in ['backend', 'frontend/src', 'frontend/tests', 'tests']:
    files.extend(p for p in (root / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files.extend(root / 'frontend' / name for name in ['package.json', 'package-lock.json', 'index.html', 'tsconfig.json', 'vite.config.ts', 'playwright.config.ts'])
files.append(Path(__file__).resolve())
archive = root / 'NetSim_Lite_Deploy.zip'
with ZipFile(archive, 'w', ZIP_DEFLATED) as output:
    for file in sorted(set(files)):
        output.write(file, file.relative_to(root).as_posix())
with ZipFile(archive) as output:
    assert output.testzip() is None
    assert not any(name.endswith('.env') or 'node_modules/' in name or '.venv/' in name for name in output.namelist())
    print(f'Verified {len(output.namelist())} release files.')
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(root / 'NetSim_Lite_Deploy.sha256').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
print(f'{archive.name}: {archive.stat().st_size:,} bytes; SHA-256 {digest}')
