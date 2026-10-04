"""Dataset/schema integrity, source hash checks and finite-value checks."""
from pathlib import Path
import json,hashlib,csv,zipfile,xml.etree.ElementTree as ET
import numpy as np
from parameters import default_parameters
ROOT=Path(__file__).resolve().parent

def check_registry_export():
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with (ROOT/'parameter_registry.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    with zipfile.ZipFile(ROOT/'parameter_registry.xlsx') as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            shared=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        cells={}
        for c in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:c',ns):
            v=c.find('s:v',ns)
            text=v.text if v is not None else ''.join(c.find('s:is',ns).itertext()) if c.find('s:is',ns) is not None else ''
            cells[c.attrib['r']]=shared[int(text)] if c.attrib.get('t')=='s' else text
        for i,row in enumerate(rows,2):
            if cells[f'A{i}']!=row['symbol']:raise RuntimeError('Excel registry symbol mismatch')
            try:
                expected=float(row['value']);actual=float(cells[f'C{i}'])
                if not np.isclose(expected,actual,rtol=1e-12,atol=0):raise RuntimeError('Excel registry numeric mismatch')
            except ValueError:
                if cells[f'C{i}']!=row['value']:raise RuntimeError('Excel registry value mismatch')
    return len(rows)

def main():
    registry_rows=check_registry_export()
    manifest=json.loads((ROOT/'datasets/manifest.json').read_text())
    for file,expected in manifest['files'].items():
        if hashlib.sha256((ROOT/file).read_bytes()).hexdigest()!=expected:raise RuntimeError(f'Hash mismatch {file}')
    counts={};p=default_parameters()
    for file in ['pilot_reference.npz','datasets/candidate_reference.npz']:
        with np.load(ROOT/file,allow_pickle=False) as a:
            for name in a.files:
                if np.issubdtype(a[name].dtype,np.number) and not np.isfinite(a[name]).all():raise RuntimeError(f'Nonfinite {file}:{name}')
            if abs(a['integration_weights'].sum()-a['grid_m'][-1])>1e-12:raise RuntimeError('Bad quadrature length')
            ids=a['trajectory_id'];splits=a['split']
            for group in np.unique(ids):
                if len(np.unique(splits[ids==group]))!=1:raise RuntimeError('Split leakage')
            counts[file]={str(k):int(np.sum(splits==k)) for k in np.unique(splits)}
            if file=='pilot_reference.npz':
                if np.max(abs(a['z']*p.sigma0))>p.mu_s+1e-10:raise RuntimeError('Component bristle bound failed')
                force_norm=np.linalg.norm(a['force'],axis=-1)
                if np.any(force_norm>np.sqrt(2)*p.mu_s*a['Fz'][:,None]+1e-8):raise RuntimeError('Conservative transient force bound failed')
            else:
                meta=json.loads(str(a['metadata_json']))
                fz=np.array([q['Fz'] for q in meta])
                if np.max(abs(a['z_next']*p.sigma0))>p.mu_s+1e-10:raise RuntimeError('Candidate bristle bound failed')
                if np.any(np.linalg.norm(a['force'],axis=-1)>np.sqrt(2)*p.mu_s*fz[:,None]+1e-8):raise RuntimeError('Candidate force bound failed')
    for file in ['model_spec.md','parameter_registry.csv','parameter_registry.xlsx','reference_solver.py','pressure.py',
                 'reference_tests.py','pilot_reference.npz','section_II_B.md','section_III_A_physics.md',
                 'section_V_A_verification.md','reference_verification_report.md','handoff_A.md','contact_patch.png']:
        if not (ROOT/file).is_file():raise RuntimeError(f'Missing deliverable {file}')
    (ROOT/'results/delivery_validation.json').write_text(json.dumps({'finite_arrays':True,'hashes_match':True,'no_group_split_leakage':True,'conservative_force_and_bristle_bounds':True,'Excel_CSV_matching_rows':registry_rows,'counts':counts},indent=2))
    print(json.dumps(counts,indent=2))
if __name__=='__main__':main()
