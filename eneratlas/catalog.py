"""Adaptadores extensíveis; arquivos em gravação nunca são importados."""
import csv
import gzip
import hashlib
import json
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import ijson
from .geometry import decode_geometry, normalized, style_for
from .store import connect


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def stable_id(value):
    return hashlib.sha256(value.encode()).hexdigest()[:20]


def discovery(roots):
    found = {}
    for root in roots:
        root = Path(root)
        for source, folder in [('EPE', root / 'webmapepe'), ('ANEEL', root / 'aneel_ons' / 'aneel')]:
            # Also accepts the extracted source folder itself.
            if root.name.lower() == ('webmapepe' if source == 'EPE' else 'aneel'):
                folder = root
            if not folder.exists():
                continue
            for metadata_file in folder.glob('camadas/*/*/metadados.json'):
                try:
                    meta = read_json(metadata_file)
                    if meta.get('type') in ('Group Layer','Raster Layer'):
                        continue
                    data = next((metadata_file.parent / n for n in ('dados.geojson', 'dados.geojson.gz', 'dados.esrijson.gz') if (metadata_file.parent / n).is_file()), None)
                    url = meta.get('_url')
                    # Download metadata does not store the URL. Service metadata
                    # plus inventory are resolved below without guessing endpoints.
                    result = metadata_file.parent / 'resultado_coleta.json'
                    entry = read_json(result) if result.exists() else {}
                    if not entry:
                        inventories = [folder / 'inventario.json'] if source == 'EPE' else list(folder.parent.glob('inventario_aneel*.json'))
                        for inv in inventories:
                            for item in read_json(inv).get('camadas', []):
                                if (folder / item.get('pasta', '__none__')).resolve() == metadata_file.parent.resolve():
                                    entry = item
                                    break
                            if entry:
                                break
                    url = entry.get('url', url)
                    if not url and source == 'ANEEL':
                        mapa = folder/'metadados/mapa.json'
                        if mapa.exists():
                            def walk(layers):
                                for layer in layers:
                                    if layer.get('url') and str(layer['url']).rsplit('/',1)[-1] == str(meta.get('id')) and layer.get('title') == meta.get('name'):
                                        return layer['url']
                                    child = walk(layer.get('layers', []))
                                    if child:
                                        return child
                            url = walk(read_json(mapa).get('operationalLayers', []))
                    url = url or f'{source}:{metadata_file.parent.name}'
                    found[stable_id(url)] = {'id': stable_id(url), 'name': meta.get('name', metadata_file.parent.name), 'source': source, 'url': url, 'meta': meta, 'file': data, 'state': entry.get('status', 'aguardando_download'), 'expected': entry.get('registros')}
                except (OSError, ValueError):
                    continue
        ons = root / 'aneel_ons' / 'ons' / 'arquivos' / 'LINHA_TRANSMISSAO.csv'
        if root.name == 'aneel_ons':
            ons = root / 'ons/arquivos/LINHA_TRANSMISSAO.csv'
        if ons.is_file():
            url = 'https://dados.ons.org.br/dataset/linha-transmissao'
            found[stable_id(url)] = {'id': stable_id(url), 'name': 'Linhas de transmissão — cadastro ONS', 'source': 'ONS', 'url': url, 'meta': {'description': 'Cadastro tabular sem geometria publicada neste recurso. Não são criados trajetos a partir dos nomes dos terminais.'}, 'file': ons, 'state': 'completo'}
        # Managed updates and user imports have a manifest, independent of source
        # folder layouts. Explicit later roots override older source snapshots.
        for manifest in root.glob('managed/*/layer.json'):
            try:
                item = read_json(manifest)
                item['file'] = manifest.parent / item['file']
                found[item['id']] = item
            except (ValueError, OSError, KeyError):
                continue
    return list(found.values())


def features(item):
    path = item['file']
    if path.suffix.lower() == '.csv':
        with path.open(encoding='utf-8-sig', newline='') as stream:
            sample = stream.read(8192)
            stream.seek(0)
            delimiter = ';' if sample.count(';') > sample.count(',') else ','
            for attrs in csv.DictReader(stream, delimiter=delimiter):
                raw = None
                lon, lat = item.get('longitude'), item.get('latitude')
                if lon and lat and attrs.get(lon) and attrs.get(lat):
                    try:
                        raw = {'type': 'Point', 'coordinates': [float(attrs[lon].replace(',', '.')), float(attrs[lat].replace(',', '.'))]}
                    except ValueError:
                        pass
                yield attrs, raw
    else:
        op = gzip.open if path.suffix == '.gz' else open
        with op(path, 'rb') as stream:
            for feature in ijson.items(stream, 'features.item', use_float=True):
                yield feature.get('attributes') or feature.get('properties') or {}, feature.get('geometry')


def first(attrs, keys, fallback=''):
    values = {normalized(k): v for k, v in attrs.items()}
    for key in keys:
        value = values.get(normalized(key))
        if value is not None and str(value).strip():
            return str(value).strip()
    return fallback


ID_FIELDS = {'ceg': 'CEG', 'codequipamento': 'COD_EQUIPAMENTO', 'cnpj': 'CNPJ', 'idempreendimento': 'ID_EMPREENDIMENTO', 'eolversaoid': 'ID_EMPREENDIMENTO', 'idse': 'ID_SE', 'idlt': 'ID_LT'}


class Importer:
    def __init__(self, db_path, roots, state_path):
        self.db_path, self.roots, self.state_path = Path(db_path), list(roots), Path(state_path)
        self.lock = threading.Lock()
        self.state = {'running': False, 'message': 'Pronto', 'errors': []}

    def publish(self, **kwargs):
        self.state.update(kwargs, updated=datetime.now(timezone.utc).isoformat())
        temp = self.state_path.with_suffix('.tmp')
        temp.write_text(json.dumps(self.state, ensure_ascii=False), encoding='utf-8')
        temp.replace(self.state_path)

    def start(self):
        if not self.lock.acquire(blocking=False):
            return False
        threading.Thread(target=self._run, daemon=True).start()
        return True

    def run(self):
        if not self.lock.acquire(blocking=False):
            return
        self._run()

    def _run(self):
        try:
            self.publish(running=True, message='Descobrindo bases locais', errors=[], processed=0)
            items = discovery(self.roots)
            # Essential infrastructure appears first; multi-million-row terrain
            # and administrative layers load last, without blocking map use.
            def priority(x):
                n = normalized(x['name'])
                return (3 if any(k in n for k in ('curvasdenivel', 'barragemlinha', 'rodovia')) else 0 if x['source'] == 'ONS' else 1 if any(k in n for k in ('eolica', 'fotovolta', 'subest', 'transmiss', 'hidrel', 'usina')) else 2, x['name'])
            items.sort(key=priority)
            with connect(self.db_path) as db:
                # Remove obsolete placeholders only when they have never held
                # records. Completed offline layers remain available.
                known = [x['id'] for x in items]
                if known:
                    db.execute('DELETE FROM layers WHERE count=0 AND state<>\'indexado\' AND id NOT IN (' + ','.join('?' for _ in known) + ')', known)
                for item in items:
                    db.execute('INSERT INTO layers(id,name,source,url,metadata,style,state) VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,metadata=excluded.metadata,url=excluded.url', (item['id'],item['name'],item['source'],item['url'],json.dumps(item.get('meta', {}),ensure_ascii=False),json.dumps(style_for(item['name'])),item['state']))
            for index, item in enumerate(items):
                if not item['file'] or not str(item['state']).startswith('completo'):
                    continue
                try:
                    self.load(item)
                except Exception as error:
                    errors = self.state['errors'] + [{'layer': item['name'], 'error': str(error)}]
                    self.publish(errors=errors)
                    with connect(self.db_path) as db:
                        db.execute('UPDATE layers SET error=? WHERE id=?', (str(error), item['id']))
                self.publish(processed=index + 1, total=len(items))
            self.publish(running=False, message='Bases locais sincronizadas' if not self.state['errors'] else 'Sincronização concluída com pendências')
        except Exception as error:
            self.publish(running=False, message=str(error), errors=self.state.get('errors', []) + [{'error': traceback.format_exc()}])
        finally:
            self.lock.release()

    def load(self, item):
        path = Path(item['file'])
        signature = str(path.resolve()) + ':' + str(path.stat().st_size) + ':' + str(path.stat().st_mtime_ns)
        signature += ':' + stable_id(json.dumps(item.get('meta', {}), sort_keys=True))
        with connect(self.db_path) as db:
            prev = db.execute('SELECT signature FROM layers WHERE id=?', (item['id'],)).fetchone()
            if prev and prev[0] == signature:
                return
            self.publish(message='Indexando ' + item['name'], layer=item['name'], rows=0)
            # Transaction per layer: readers see the previous complete snapshot
            # until all replacement rows and the spatial index are committed.
            db.execute('DELETE FROM spatial WHERE id IN (SELECT id FROM features WHERE layer_id=?)', (item['id'],))
            db.execute('DELETE FROM identifiers WHERE feature_id IN (SELECT id FROM features WHERE layer_id=?)', (item['id'],))
            db.execute('DELETE FROM features WHERE layer_id=?', (item['id'],))
            count = located = issues = 0
            native = '.esrijson' in path.name
            meta = item.get('meta', {})
            sr = (meta.get('extent') or {}).get('spatialReference') or meta.get('spatialReference')
            for attrs, raw in features(item):
                note = None
                try:
                    geom, note = decode_geometry(raw, native=native, sr=sr)
                except Exception as error:
                    geom, note = None, str(error)
                name = first(attrs, ['Nome', 'nom_linhadetransmissao', 'nom_empreendimento', 'nom_usina', 'NM_MUN', 'NOME_UC', 'NOME_TI', 'NOME_RESP', 'CEG', 'id_empreendimento'], item['name'] + ' #' + str(count + 1))
                uf = first(attrs, ['UF', 'UF1', 'sigla_uf', 'id_estado_terminalde', 'estado'])
                status = first(attrs, ['FASE', 'SITUACAO', 'STATUS', 'OPERACAO_COMERCIAL', 'OPERACAO'])
                oid = first(attrs, ['OBJECTID', 'FID', 'id', 'cod_equipamento'], str(count + 1))
                bounds = list(geom.bounds) if geom is not None else [None] * 4
                search = normalized(' '.join(str(v) for v in attrs.values() if v is not None))
                cursor = db.execute('INSERT INTO features(layer_id,oid,name,uf,status,search,attrs,geom,note,minx,miny,maxx,maxy) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', (item['id'],oid,name,uf,status,search,json.dumps(attrs,ensure_ascii=False,separators=(',', ':')),geom.wkb if geom is not None else None,note,*bounds))
                fid = cursor.lastrowid
                if geom is not None:
                    db.execute('INSERT INTO spatial VALUES(?,?,?,?,?)', (fid,bounds[0],bounds[2],bounds[1],bounds[3]))
                    located += 1
                for key, value in attrs.items():
                    kind = ID_FIELDS.get(normalized(key))
                    if kind and value is not None and normalized(value) not in ('', '0', 'null', 'na', 'nan'):
                        # ANEEL internal IDs have a scoped namespace; CEG/CNPJ
                        # are national. No implicit name-based project merging.
                        scope = item['source'] + ':' if kind.startswith('ID_') else ''
                        db.execute('INSERT INTO identifiers VALUES(?,?,?)', (fid,scope + kind,normalized(value)))
                issues += bool(note)
                count += 1
                if count % 5000 == 0:
                    self.publish(rows=count)
            if item.get('expected') is not None and count != item['expected']:
                raise ValueError(f'Contagem diverge do inventário: {count} / {item["expected"]}; versão anterior preservada')
            db.execute('UPDATE layers SET signature=?,state=?,count=?,located=?,issues=?,updated=?,file=?,error=NULL WHERE id=?', (signature,'indexado',count,located,issues,datetime.now(timezone.utc).isoformat(),str(path),item['id']))
