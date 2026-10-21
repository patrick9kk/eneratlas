"""Atualização sob demanda; grava cópias gerenciadas e preserva os originais."""
import importlib.util
import json
import logging
import threading
import urllib.request
from pathlib import Path
from .store import connect

LOCK = threading.Lock()


def start_update(app, db_path, importer, data_dir, layer_ids):
    if not layer_ids:
        raise ValueError('Selecione as camadas que deseja baixar novamente')
    if not LOCK.acquire(blocking=False):
        return False
    def work():
        app.update_state = {'running': True, 'message': 'Consultando fontes oficiais', 'errors': []}
        try:
            from .vendor import arcgis
            arcgis.ROOT = Path(data_dir)
            arcgis.FORCE_REFRESH = True
            with connect(db_path) as db:
                selected = list(db.execute('SELECT * FROM layers WHERE id IN (' + ','.join('?' for _ in layer_ids) + ')', layer_ids))
            for layer in selected:
                try:
                    app.update_state['message'] = 'Baixando ' + layer['name']
                    folder = Path(data_dir) / 'managed' / layer['id']
                    folder.mkdir(parents=True, exist_ok=True)
                    if layer['source'] == 'ONS':
                        catalog_url = 'https://dados.ons.org.br/api/3/action/package_show?id=linha-transmissao'
                        catalog = arcgis.request(catalog_url)
                        resource = next(r for r in catalog['result']['resources'] if r.get('format','').lower() == 'csv')
                        req = urllib.request.Request(resource['url'], headers={'User-Agent':'EnerAtlas/1.0 (public energy data)'})
                        with urllib.request.urlopen(req, timeout=120) as response, (folder/'dados.csv.tmp').open('wb') as out:
                            import shutil
                            shutil.copyfileobj(response,out)
                        # Validate header and at least one complete data row.
                        import csv
                        with (folder/'dados.csv.tmp').open(encoding='utf-8-sig') as stream:
                            reader = csv.DictReader(stream,delimiter=';')
                            if 'cod_equipamento' not in reader.fieldnames or not next(reader,None):
                                raise ValueError('CSV ONS incompatível ou vazio; versão anterior preservada')
                        (folder/'dados.csv.tmp').replace(folder/'dados.csv')
                        (folder/'catalogo_fonte.json').write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8')
                        filename, meta = 'dados.csv', json.loads(layer['metadata'])
                    elif layer['source'] in ('EPE','ANEEL') and layer['url'].startswith('https://'):
                        url = layer['url']
                        meta = arcgis.request(url + '?f=json')
                        service = {'title': layer['source'], 'url': url.rsplit('/',1)[0]}
                        # Collector chooses its own ID/name folder. Its final
                        # result is exposed only after count and ID verification.
                        entry = arcgis.download_layer(service,meta,folder)
                        if not entry.get('status','').startswith('completo'):
                            raise RuntimeError(entry.get('erro','Coleta incompleta'))
                        actual = Path(data_dir) / entry['pasta']
                        filename = str((actual/entry.get('arquivo_geometria','dados.geojson')).relative_to(folder))
                    else:
                        raise ValueError('Fonte local: substitua o arquivo ou faça uma nova importação')
                    item = {'id':layer['id'],'name':layer['name'],'source':layer['source'],'url':layer['url'],'meta':meta,'state':'completo','file':filename}
                    (folder/'layer.json').write_text(json.dumps(item,ensure_ascii=False),encoding='utf-8')
                except Exception as error:
                    logging.exception('Falha na atualização de %s', layer['name'])
                    app.update_state['errors'].append({'layer':layer['name'],'error':str(error)})
            app.update_state.update(running=False,message='Downloads concluídos; sincronizando índice')
            importer.start()
        finally:
            app.update_state['running'] = False
            LOCK.release()
    threading.Thread(target=work,daemon=True).start()
    return True
