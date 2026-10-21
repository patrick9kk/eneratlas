"""Gera o instalador leve; o aplicativo e os dados vem das releases oficiais."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    if os.name != 'nt':
        raise SystemExit('Construa o instalador Windows no Windows.')
    root = Path(__file__).resolve().parents[1]
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onefile', '--console', '--name', 'Instalar-EnerAtlas',
        '--add-data', str(root / 'scripts/setup_windows.ps1') + ';scripts',
        '--icon', str(root / 'static/icon.ico'),
        str(root / 'scripts/setup_entry.py'),
    ], cwd=root, check=True)
    print(root / 'dist/Instalar-EnerAtlas.exe')


if __name__ == '__main__':
    main()
