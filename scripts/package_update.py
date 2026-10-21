"""Pacote de atualização do executável, sem duplicar nem alterar as bases."""
import hashlib
import sys
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from eneratlas import __version__


def main():
    root=Path(__file__).resolve().parents[1]
    archive=root.parent/f'EnerAtlas-Atualizacao-{__version__}.zip'
    instructions=f'''ENERATLAS {__version__} — ATUALIZACAO

1. Encerre o aplicativo pelo botao de energia no cabecalho.
2. Extraia este ZIP e copie EnerAtlas.exe para a pasta do aplicativo anterior.
3. Substitua somente o executavel. Preserve a pasta data e abra EnerAtlas.exe.

Autoria na interface: Patrick Maximo Cordeiro.
Recursos: cores das linhas por tensao em kV, nome e tensao ao passar o mouse,
e seletor de mapa de ruas, imagem de satelite ou fundo desligado.
Satelite requer internet. Os registros e geometrias locais sao preservados.

Mapa publico: https://patrick9kk.github.io/eneratlas/
Pacote inicial completo: https://github.com/patrick9kk/eneratlas/releases/tag/v1.0.0
'''
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.write(root/'dist/EnerAtlas.exe','EnerAtlas.exe')
        z.writestr('COMO-ATUALIZAR.txt',instructions)
        z.write(root/'CHANGELOG.md','CHANGELOG.md')
        z.write(root/'docs/FONTES.md','FONTES.md')
        z.write(root/'LICENSE','LICENSE')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
    with archive.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf-8')
    print(archive)


if __name__=='__main__':main()
