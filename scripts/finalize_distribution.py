"""Atualiza arquivos pequenos no ZIP sem recomprimir o banco e divide para Releases.

O ZIP resultante é validado por CRC. A cópia de membros comprimidos usa
metadados ZipInfo do próprio zipfile; nenhum conteúdo externo é executado.
"""
import copy
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

def finalize(root, destination, archive):
    root,destination,archive=Path(root).resolve(),Path(destination).resolve(),Path(archive).resolve()
    replacements={'EnerAtlas/EnerAtlas.exe':root/'dist/EnerAtlas.exe','EnerAtlas/README.md':root/'README.md'}
    for p in (root/'docs').glob('*'):
        if p.is_file():replacements['EnerAtlas/docs/'+p.name]=p
    temp=archive.with_suffix('.finalizando.zip')
    with zipfile.ZipFile(archive) as old,zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as new,archive.open('rb') as raw:
        entries=sorted(old.infolist(),key=lambda x:x.header_offset)
        for index,info in enumerate(entries):
            if info.filename in replacements:continue
            end=entries[index+1].header_offset if index+1<len(entries) else old.start_dir
            raw.seek(info.header_offset)
            clone=copy.copy(info);clone.header_offset=new.fp.tell()
            remaining=end-info.header_offset
            while remaining:
                chunk=raw.read(min(8*1024**2,remaining))
                if not chunk:raise ValueError('ZIP original truncado')
                new.fp.write(chunk);remaining-=len(chunk)
            new.filelist.append(clone);new.NameToInfo[clone.filename]=clone
        new.start_dir=new.fp.tell();new._didModify=True
        for name,path in replacements.items():
            new.write(path,name)
            target=destination/Path(name).relative_to('EnerAtlas')
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
    with zipfile.ZipFile(temp) as z:
        assert z.testzip() is None
        with (root/'dist/EnerAtlas.exe').open('rb') as stream:
            expected=hashlib.file_digest(stream,'sha256').hexdigest()
        assert hashlib.sha256(z.read('EnerAtlas/EnerAtlas.exe')).hexdigest()==expected
    temp.replace(archive)
    with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
    parts=[]
    with archive.open('rb') as stream:
        for number in range(1,100):
            block=stream.read(1024**3)
            if not block:break
            part=archive.parent/(archive.name+f'.part{number:03}')
            part.write_bytes(block);parts.append(part)
    hashes=[]
    for p in parts:
        with p.open('rb') as stream:hashes.append(hashlib.file_digest(stream,'sha256').hexdigest()+'  '+p.name)
    (archive.parent/'EnerAtlas-SHA256SUMS.txt').write_text('\n'.join(hashes+[digest+'  '+archive.name])+'\n',encoding='utf-8')
    cmd=['@echo off','setlocal','cd /d "%~dp0"','if exist "'+archive.name+'" (echo O ZIP ja existe. Use o arquivo existente ou outra pasta. & pause & exit /b 1)']
    for part in parts:cmd.append('if not exist "'+part.name+'" (echo Falta '+part.name+'. Baixe todas as partes na mesma pasta. & pause & exit /b 1)')
    cmd+=['echo Reunindo o pacote. Aguarde...','copy /b '+ '+'.join('"'+p.name+'"' for p in parts)+' "'+archive.name+'" >nul','if errorlevel 1 (echo Nao foi possivel reunir. Verifique espaco livre. & pause & exit /b 1)', 'powershell -NoProfile -Command "if ((Get-FileHash -LiteralPath \''+archive.name+'\' -Algorithm SHA256).Hash -ne \''+digest+'\') {exit 1}"','if errorlevel 1 (echo O hash nao confere. Preserve os arquivos e baixe as partes novamente. & pause & exit /b 1)','echo Pacote conferido. Extraia o ZIP e abra EnerAtlas.exe.','start "" "'+archive.name+'"','pause']
    join=archive.parent/'Reunir-EnerAtlas.cmd';join.write_bytes(('\r\n'.join(cmd)+'\r\n').encode('ascii'))
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest,'parts':[p.name for p in parts],'exe_sha256':expected}),flush=True)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    finalize(root,root.parent/'EnerAtlas-Windows',root.parent/'EnerAtlas-Windows-portatil.zip')
