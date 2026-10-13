"""Generate the delivery manifest and ZIP, excluding local caches and private data."""
from hashlib import sha256
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.build', '.git', '.venv', 'node_modules', '__pycache__',
            '.pytest_cache', 'dist', 'backups'}
MANIFEST = ROOT / '文件校验SHA256.txt'


def include(path):
    rel = path.relative_to(ROOT)
    return (path.is_file() and not path.is_symlink()
            and not any(part in EXCLUDED for part in rel.parts)
            and path.name not in {'.env', '.DS_Store', 'test-results.xml'}
            and path.suffix not in {'.pyc', '.zip'}
            and not path.name.startswith('~$'))


files = sorted(p for p in ROOT.rglob('*') if include(p) and p != MANIFEST)
MANIFEST.write_text(''.join(f'{sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT).as_posix()}\n'
                            for p in files), encoding='utf-8')
archive = ROOT.parent / f'{ROOT.name}-交付包.zip'
with ZipFile(archive, 'w', ZIP_DEFLATED) as z:
    for path in [*files, MANIFEST]:
        z.write(path, Path(ROOT.name) / path.relative_to(ROOT))
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert sum('/01-提交文档/' in n and n.endswith('.docx') for n in z.namelist()) == 13
    assert any(n.endswith('/backend/static/index.html') for n in z.namelist())
print(f'Packaged {len(files) + 1} files: {archive} ({archive.stat().st_size:,} bytes)')
