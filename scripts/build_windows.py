"""Build reproduzível do executável (executar em Windows)."""
import os
import subprocess
import sys
from pathlib import Path

def main():
    if os.name != 'nt':
        raise SystemExit('Construa o executável Windows no Windows.')
    root=Path(__file__).resolve().parents[1]
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onefile','--windowed','--name','EnerAtlas','--add-data',str(root/'static')+';static','--add-data',str(root/'templates')+';templates','--collect-all','rasterio','--collect-data','pyproj','--collect-submodules','ijson.backends','--hidden-import','eneratlas.vendor.arcgis',str(root/'launch.py')]
    if (root/'static/icon.ico').exists():
        command[3:3]=['--icon',str(root/'static/icon.ico')]
    subprocess.run(command,cwd=root,check=True)
    with (root/'dist/DEPENDENCIAS.txt').open('w',encoding='utf-8') as f:
        subprocess.run([sys.executable,'-m','pip','freeze'],stdout=f,check=True)
    print(root/'dist/EnerAtlas.exe')

if __name__=='__main__':main()
