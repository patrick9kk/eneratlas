"""Snapshot consistente, sem caminhos pessoais, e pacote portátil com SHA-256."""
import argparse
import hashlib
import json
import shutil
import sqlite3
import zipfile
from datetime import datetime, timezone
from pathlib import Path

def package(root, destination, database):
    root,destination,database=Path(root).resolve(),Path(destination).resolve(),Path(database).resolve()
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'data/rasters').mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/'dist/EnerAtlas.exe',destination/'EnerAtlas.exe')
    shutil.copy2(root/'dist/DEPENDENCIAS.txt',destination/'DEPENDENCIAS.txt')
    for name in ('README.md','LICENSE'):
        shutil.copy2(root/name,destination/name)
    shutil.copytree(root/'docs',destination/'docs',dirs_exist_ok=True)
    shutil.copytree(root/'static/vendor',destination/'licencas',dirs_exist_ok=True)
    for p in (database.parent/'rasters').glob('*'):
        if p.is_file():shutil.copy2(p,destination/'data/rasters'/p.name)
    with sqlite3.connect(database) as source,sqlite3.connect(destination/'data/eneratlas.db') as target:
        source.backup(target,pages=8192)
        target.execute('PRAGMA secure_delete=ON')
        for lid,signature,file in target.execute('SELECT id,signature,file FROM layers').fetchall():
            if signature and len(signature)!=64:
                signature=hashlib.sha256(signature.encode()).hexdigest()
            target.execute('UPDATE layers SET signature=?,file=? WHERE id=?',(signature,Path(file).name if file else None,lid))
        target.commit()
        target.execute('VACUUM')
        target.row_factory=sqlite3.Row
        layers=[dict(r) for r in target.execute('SELECT id,name,source,state,count,located,issues,updated,error FROM layers ORDER BY source,name')]
        assert target.execute('PRAGMA quick_check').fetchone()[0]=='ok'
    coverage={'generated_utc':datetime.now(timezone.utc).isoformat(),'version':'1.0.0','indexed_layers':sum(l['state']=='indexado' for l in layers),'rows':sum(l['count'] for l in layers),'located':sum(l['located'] for l in layers),'layers':layers,'note':'Snapshot das camadas concluídas. Downloads pendentes, inclusive curvas de nível, não são apresentados como completos. Novos dados podem ser importados e atualizados no aplicativo. Não conta instalações únicas.'}
    (destination/'COBERTURA.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    (destination/'LEIA-ME.txt').write_text('ENERATLAS\n\nAbra EnerAtlas.exe. O navegador é a interface; o processamento é local.\nMantenha a pasta data junto do executável. Use o botão de energia para encerrar.\n\nMapa público: https://patrick9kk.github.io/eneratlas/\nDocumentação: https://github.com/patrick9kk/eneratlas\n\nCOBERTURA.json informa exatamente as camadas presentes neste pacote.\nA coleta original de curvas de nível ainda não está concluída.\nDados completos, limitações e fontes: README.md e docs/FONTES.md.\n',encoding='utf-8')
    archive=destination.parent/'EnerAtlas-Windows-portatil.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p in sorted(destination.rglob('*')):
            if p.is_file() and p.suffix not in ('.lock',) and not p.name.endswith(('-wal','-shm')):
                print('Empacotando',p.name,flush=True)
                z.write(p,Path('EnerAtlas')/p.relative_to(destination))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    with archive.open('rb') as stream:
        checksum=hashlib.file_digest(stream,'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(checksum+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':checksum,'rows':coverage['rows'],'layers':coverage['indexed_layers']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--destination',type=Path,required=True);p.add_argument('--database',type=Path,required=True);a=p.parse_args();package(a.root,a.destination,a.database)
