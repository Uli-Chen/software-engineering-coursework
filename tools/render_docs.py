from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os
root=Path(__file__).resolve().parents[1]
python='/Users/chen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
renderer='/Users/chen/.codex/plugins/cache/openai-primary-runtime/documents/26.1011.11113/skills/documents/render_docx.py'
env=dict(os.environ,FONTCONFIG_FILE=str(root/'.build/fonts.conf'))
def render(file):
    output=root/'.build/verified-render'/file.stem
    result=subprocess.run([python,renderer,str(file),'--output_dir',str(output),'--emit_pdf'],env=env,capture_output=True,text=True)
    return file.name,result.returncode,len(list(output.glob('page-*.png'))),result.stderr[-300:]
with ThreadPoolExecutor(3) as pool:
    for result in pool.map(render,sorted((root/'01-提交文档').glob('*.docx'))):print(result,flush=True)
