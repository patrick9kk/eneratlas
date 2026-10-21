"""Entrada para Python e executável Windows. Servidor restrito a loopback."""
import argparse
import json
import logging
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path
from waitress import create_server
from eneratlas.catalog import Importer
from eneratlas.store import initialize
from eneratlas.server import create_app
from eneratlas.startup import DEFAULT_PORT, acquire_data_lock, choose_data_dir, find_running


def main():
    parser = argparse.ArgumentParser(description='EnerAtlas — mapa local de infraestrutura energética')
    parser.add_argument('--data-dir', type=Path)
    parser.add_argument('--source',type=Path,action='append',default=[])
    parser.add_argument('--port',type=int,default=DEFAULT_PORT)
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--import-only',action='store_true')
    parser.add_argument('--no-autodiscover',action='store_true',help='Não buscar bases nas pastas vizinhas')
    args = parser.parse_args()
    frozen = getattr(sys,'frozen',False)
    base = Path(sys.executable).parent if frozen else Path(__file__).parent
    assets = Path(sys._MEIPASS) if frozen else base
    data_dir = choose_data_dir(args.data_dir, base, frozen)
    data_dir.mkdir(parents=True,exist_ok=True)
    existing = find_running(data_dir, args.port)
    if existing:
        if not args.no_browser and not args.import_only:
            webbrowser.open(existing)
        return
    logging.basicConfig(filename=data_dir/'eneratlas.log',level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',encoding='utf-8')
    # OS-held lock is released even after a crash. Prevent competing indexers.
    try:
        lock = acquire_data_lock(data_dir)
    except OSError:
        # A concurrent launch may still be preparing its HTTP server.
        for _ in range(20):
            existing = find_running(data_dir, args.port)
            if existing:
                if not args.no_browser and not args.import_only:
                    webbrowser.open(existing)
                return
            time.sleep(0.25)
        raise RuntimeError('A base esta em uso. Aguarde a inicializacao do EnerAtlas e tente novamente.')
    roots = [] if args.no_autodiscover else [base.parent,base,base.parent.parent]
    settings = data_dir/'sources.local.json'
    if settings.exists():
        roots += [Path(p) for p in json.loads(settings.read_text(encoding='utf-8'))]
    roots += args.source + [data_dir]
    roots = list(dict.fromkeys(p.resolve() for p in roots if p.exists()))
    db_path = data_dir/'eneratlas.db'
    initialize(db_path)
    importer = Importer(db_path,roots,data_dir/'import_status.json')
    if args.import_only:
        importer.run()
        from eneratlas.raster import prepare_rasters
        prepare_rasters(roots,data_dir)
        return
    app = create_app(db_path,importer,assets,data_dir)
    try:
        server = create_server(app,host='127.0.0.1',port=args.port,threads=8)
    except OSError:
        # Another application may own the preferred port; remember the new URL.
        if args.port != DEFAULT_PORT:
            raise
        server = create_server(app,host='127.0.0.1',port=0,threads=8)
    url = f'http://127.0.0.1:{server.effective_port}'
    (data_dir/'runtime.json').write_text(json.dumps({'url':url,'pid':os.getpid()}),encoding='utf-8')
    importer.start()
    def refresh():
        from eneratlas.raster import prepare_rasters
        prepare_rasters(roots,data_dir)
        while not getattr(app,'shutdown_requested',False):
            for _ in range(120):
                if getattr(app,'shutdown_requested',False):
                    server.close()
                    os._exit(0)
                time.sleep(1)
            if not getattr(app,'update_state',{}).get('running'):
                importer.start()
    threading.Thread(target=refresh,daemon=True).start()
    if not args.no_browser:
        threading.Timer(0.8,lambda:webbrowser.open(url)).start()
    logging.info('Servidor local em %s',url)
    try:
        server.run()
    finally:
        server.close()
        lock.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        logging.exception('Erro de inicialização')
        if os.name == 'nt' and getattr(sys,'frozen',False):
            import ctypes
            ctypes.windll.user32.MessageBoxW(None,str(error),'EnerAtlas — não foi possível iniciar',0x10)
        else:
            raise
