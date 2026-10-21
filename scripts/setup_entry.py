"""Entrada do instalador Windows empacotado; nao exige Python no destino."""
import os
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))
    powershell = Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.call([
        str(powershell), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        str(root / 'scripts/setup_windows.ps1'), *sys.argv[1:],
    ])
    if result and '-checkonly' not in [arg.lower() for arg in sys.argv[1:]]:
        input('Falha na instalacao. Pressione Enter para fechar...')
    return result


if __name__ == '__main__':
    raise SystemExit(main())
