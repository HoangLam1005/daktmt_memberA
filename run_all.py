"""Run all A experiments. Requires dependencies in requirements.txt."""
from pathlib import Path
import subprocess,sys,json,hashlib
ROOT=Path(__file__).resolve().parent

def make_manifest():
    files={}
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.name!='delivery_manifest.json' and not path.name.endswith('.inspect.ndjson'):
            files[str(path.relative_to(ROOT))]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    (ROOT/'delivery_manifest.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
    print(f'Delivery manifest: {len(files)} files')

def main():
    # Registry is deliberately NOT regenerated: the reviewed CSV is authoritative.
    for script in ['verification.py','generate_reference.py','make_figures.py','build_report.py','validate_delivery.py']:
        subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT,check=True)
    make_manifest()
if __name__=='__main__':main()
