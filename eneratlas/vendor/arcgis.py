"""Baixa camadas públicas ArcGIS em lotes, validando IDs e contagens."""
import csv
import contextlib
import gzip
import json
import os
import pathlib
import re
import shutil
import time
import unicodedata
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
COMPRESS_THRESHOLD = 200000
FORCE_REFRESH = False


def request(url, params=None):
    parts = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit((parts.scheme, parts.netloc, urllib.parse.quote(urllib.parse.unquote(parts.path), safe='/'), parts.query, ''))
    data = urllib.parse.urlencode(params).encode() if params else None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Public-energy-data-archive/1.0', 'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req, timeout=60) as response:
                value = json.load(gzip.GzipFile(fileobj=response) if response.headers.get('Content-Encoding') == 'gzip' else response)
            if 'error' in value:
                raise RuntimeError(str(value['error']))
            return value
        except Exception as error:
            if attempt == 1 or isinstance(error, RuntimeError):
                raise
            time.sleep(2 ** attempt)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    for attempt in range(10):
        try:
            tmp.replace(path)
            break
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.05)


def slug(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_')[:110]


def iter_features(path):
    """Lê features JSON/GeoJSON sem manter todas as geometrias na memória."""
    decoder = json.JSONDecoder()
    opener = gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz' else path.open(encoding='utf-8')
    with opener as stream:
        buffer = ''
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                raise ValueError('Colecao GeoJSON sem features')
            buffer += chunk
            match = re.search(r'"features"\s*:\s*\[', buffer)
            if match:
                buffer = buffer[match.end():]
                break
        position = 0
        while True:
            while position < len(buffer) and buffer[position] in ' \n\r\t,':
                position += 1
            if position < len(buffer) and buffer[position] == ']':
                stream.read()
                return
            try:
                feature, end = decoder.raw_decode(buffer, position)
            except json.JSONDecodeError:
                chunk = stream.read(8 * 1024 * 1024)
                if not chunk:
                    raise ValueError('GeoJSON incompleto')
                buffer = buffer[position:] + chunk
                position = 0
                continue
            position = end
            yield feature


def download_layer(service, meta, folder):
    """Evita gravações simultâneas da mesma camada entre processos."""
    dest = folder / (str(meta['id']).zfill(3) + '_' + slug(meta['name']))
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / '.coleta.lock').open('a+b') as lock:
        if lock.tell() == 0:
            lock.write(b'0')
            lock.flush()
        if os.name == 'nt':
            import msvcrt
            while True:
                try:
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    time.sleep(1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        result_file = dest / 'resultado_coleta.json'
        try:
            if not FORCE_REFRESH and result_file.exists():
                cached = json.loads(result_file.read_text(encoding='utf-8'))
                if cached['status'] in ('completo', 'completo_com_falhas_de_geometria'):
                    cached_folder = ROOT / cached['pasta']
                    geo_file = cached.get('arquivo_geometria', cached.get('arquivo_geojson', 'dados.geojson'))
                    if all((cached_folder / name).exists() for name in (geo_file, 'atributos.csv', 'ids_origem.json')):
                        return cached
            entry = _download_layer(service, meta, folder)
            save(result_file, entry)
            return entry
        finally:
            if os.name == 'nt':
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


def _download_layer(service, meta, folder):
    lid = meta['id']
    url = service['url'] + '/' + str(lid)
    entry = {'servico': service['title'], 'id': lid, 'camada': meta['name'], 'tipo': meta.get('type'), 'url': url}
    dest = folder / (str(lid).zfill(3) + '_' + slug(meta['name']))
    save(dest / 'metadados.json', meta)
    if meta.get('type') == 'Group Layer':
        entry['status'] = 'grupo'
        return entry
    if meta.get('type') not in ('Feature Layer', 'Table'):
        entry['status'] = 'imagem_sem_exportacao_vetorial'
        return entry
    try:
        use_where = not any(field['type'] == 'esriFieldTypeOID' for field in meta.get('fields', []))
        if use_where:
            oid = next(field['name'] for field in meta['fields'] if field['name'].upper() in ('OBJECTID', 'FID'))
            count = request(url + '/query', {'f': 'json', 'where': '1=1', 'returnCountOnly': 'true'})['count']
            collected = []
            offset = 0
            while offset < count:
                part = request(url + '/query', {'f': 'json', 'where': '1=1', 'outFields': oid, 'returnGeometry': 'false', 'orderByFields': oid, 'resultOffset': offset, 'resultRecordCount': 2000})
                values = [feature['attributes'][oid] for feature in part.get('features', [])]
                if not values:
                    raise RuntimeError('Paginacao interrompida antes da contagem total')
                collected.extend(values)
                offset += len(values)
            if len(set(collected)) != len(collected):
                raise RuntimeError('Identificadores duplicados na origem')
            ids_result = {'objectIdFieldName': oid, 'objectIds': collected, 'metodo': 'paginacao_ordenada_sem_campo_OID'}
        else:
            ids_result = request(url + '/query', {'f': 'json', 'where': '1=1', 'returnIdsOnly': 'true'})
        ids = sorted(ids_result.get('objectIds') or [])
        oid = ids_result.get('objectIdFieldName')
        count = request(url + '/query', {'f': 'json', 'where': '1=1', 'returnCountOnly': 'true'})['count']
        if count != len(ids):
            raise RuntimeError(f'Contagem {count} diverge dos {len(ids)} IDs')
        native = '/Camadas_SIPH/' in service['url'] or meta['name'].startswith('Reservatórios')
        size_hint = 2000
        had_batch_error = False
        native_header = {'geometryType': meta.get('geometryType'), 'spatialReference': meta.get('sourceSpatialReference') or meta.get('extent', {}).get('spatialReference'), 'fields': meta.get('fields', [])}
        def attributes_fallback(selected, error):
            selection = {'where': oid + ' IN (' + ','.join(map(str, selected)) + ')'} if use_where else {'objectIds': ','.join(map(str, selected))}
            result = request(url + '/query', {'f': 'json', **selection, 'outFields': '*', 'returnGeometry': 'false'})
            features = result.get('features', [])
            if len(features) != 1 or features[0]['attributes'].get(oid) != selected[0]:
                raise RuntimeError('Atributos indisponiveis para ID ' + str(selected[0]))
            attributes = features[0]['attributes']
            feature = {'attributes': attributes, 'geometry': None} if native else {'type': 'Feature', 'id': selected[0], 'properties': attributes, 'geometry': None}
            feature['_coleta_erro_geometria'] = str(error)[:2000]
            print(f'GEOMETRIA INDISPONIVEL {meta["name"]} ID {selected[0]}: atributos preservados', flush=True)
            return [feature]
        def batch(selected):
            nonlocal size_hint, had_batch_error
            selection = {'where': oid + ' IN (' + ','.join(map(str, selected)) + ')'} if use_where else {'objectIds': ','.join(map(str, selected))}
            try:
                options = {'f': 'json' if native else 'geojson', **selection, 'outFields': '*', 'returnGeometry': 'true', 'returnZ': 'true'}
                if native:
                    if meta.get('hasM'):
                        options['returnM'] = 'true'
                else:
                    options['outSR'] = '4326'
                result = request(url + '/query', options)
                if native:
                    native_header.update({key: result[key] for key in ('objectIdFieldName', 'globalIdFieldName', 'geometryType', 'spatialReference', 'hasZ', 'hasM', 'fields', 'fieldAliases', 'displayFieldName', 'transform') if key in result})
            except Exception as error:
                had_batch_error = True
                if count > COMPRESS_THRESHOLD and len(selected) > 32:
                    size_hint = min(size_hint, max(32, len(selected) // 2))
                if len(selected) < 2:
                    return attributes_fallback(selected, error)
                print(f'REDUZINDO LOTE {meta["name"]}: IDs {selected[0]}..{selected[-1]}; {type(error).__name__}: {str(error)[:160]}', flush=True)
                mid = len(selected) // 2
                return batch(selected[:mid]) + batch(selected[mid:])
            chunk = result.get('features', [])
            got = [feature.get('attributes', feature.get('properties', {})).get(oid, feature.get('id')) for feature in chunk]
            if result.get('exceededTransferLimit') or set(got) != set(selected) or len(got) != len(selected):
                if len(selected) < 2:
                    return attributes_fallback(selected, 'Geometria ausente no resultado da consulta')
                mid = len(selected) // 2
                return batch(selected[:mid]) + batch(selected[mid:])
            return chunk
        size = min(25 if meta.get('geometryType') == 'esriGeometryPolygon' else 2000 if count > COMPRESS_THRESHOLD else 1000, meta.get('maxRecordCount', 1000))
        if meta['name'].strip() == 'UF':
            size = 1
        elif native and meta.get('geometryType') == 'esriGeometryPolygon':
            size = min(size, 5)
        size_hint = size
        max_size = size
        fields = [field['name'] for field in meta.get('fields', []) if field['type'] != 'esriFieldTypeGeometry']
        total = 0
        missing = 0
        compact = native or count > COMPRESS_THRESHOLD
        geo_name = ('dados.esrijson' if native else 'dados.geojson') + ('.gz' if compact else '')
        geo_tmp = dest / (geo_name + '.tmp')
        csv_tmp = dest / 'atributos.csv.tmp'
        checkpoint = dest / 'progresso.json'
        ids_file = dest / 'ids_origem.json'
        mode = 'w'
        if not FORCE_REFRESH and checkpoint.exists() and ids_file.exists() and geo_tmp.exists() and csv_tmp.exists():
            prior = json.loads(ids_file.read_text(encoding='utf-8'))
            if sorted(prior['objectIds']) == ids:
                progress = json.loads(checkpoint.read_text(encoding='utf-8'))
                total = progress['registros']
                missing = progress['sem_geometria']
                for path, key in ((geo_tmp, 'geo_bytes'), (csv_tmp, 'csv_bytes')):
                    with path.open('r+b') as stream:
                        stream.truncate(progress[key])
                mode = 'a'
                print(f'RETOMADA {meta["name"]}: {total}/{count}', flush=True)
            del prior
        save(ids_file, ids_result)
        problems_file = dest / 'falhas_geometria.json'
        problems = json.loads(problems_file.read_text(encoding='utf-8')) if mode == 'a' and problems_file.exists() else {}
        with csv_tmp.open(mode, encoding='utf-8-sig', newline='') as stream, geo_tmp.open(mode + 'b') as raw_geo:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
            if not total:
                writer.writeheader()
            batch_number = 0
            while total < len(ids):
                start = total
                if shutil.disk_usage(ROOT).free < 8 * 1024 ** 3:
                    raise RuntimeError('Coleta interrompida com progresso salvo: menos de 8 GiB livres no disco')
                started_batch = time.monotonic()
                had_batch_error = False
                features = batch(ids[start:start + size_hint])
                batch_bytes = 0
                member = gzip.GzipFile(fileobj=raw_geo, mode='wb', compresslevel=2) if compact else contextlib.nullcontext(raw_geo)
                with member as geo:
                    if not total:
                        prefix = json.dumps(native_header, ensure_ascii=False, separators=(',', ':'))[:-1] + ',"features":[\n' if native else '{"type":"FeatureCollection","features":[\n'
                        geo.write(prefix.encode('utf-8'))
                    for feature in features:
                        problem = feature.pop('_coleta_erro_geometria', None)
                        if problem:
                            attributes = feature.get('attributes', feature.get('properties', {}))
                            problems[str(attributes.get(oid, feature.get('id')))] = problem
                        if total:
                            geo.write(b',\n')
                        encoded = json.dumps(feature, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                        geo.write(encoded)
                        batch_bytes += len(encoded)
                        writer.writerow(feature.get('attributes', feature.get('properties', {})))
                        total += 1
                        missing += feature.get('geometry') is None
                raw_geo.flush()
                stream.flush()
                save(problems_file, problems)
                save(checkpoint, {'registros': total, 'sem_geometria': missing, 'geo_bytes': raw_geo.tell(), 'csv_bytes': stream.tell()})
                batch_number += 1
                if count > COMPRESS_THRESHOLD and not had_batch_error:
                    estimated = max(32, min(max_size, int(len(features) * 6 * 1024 ** 2 / max(batch_bytes, 1))))
                    elapsed = time.monotonic() - started_batch
                    if elapsed > 20:
                        size_hint = max(32, min(estimated, size_hint // 2))
                    elif elapsed < 5:
                        size_hint = min(estimated, max_size, max(32, int(size_hint * 1.25)))
                    else:
                        size_hint = min(size_hint, estimated)
                if batch_number % 25 == 0:
                    print(f'PROGRESSO {meta["name"]}: {total}/{count}', flush=True)
            member = gzip.GzipFile(fileobj=raw_geo, mode='wb', compresslevel=2) if compact else contextlib.nullcontext(raw_geo)
            with member as geo:
                if not total:
                    prefix = json.dumps(native_header, ensure_ascii=False, separators=(',', ':'))[:-1] + ',"features":[' if native else '{"type":"FeatureCollection","features":['
                    geo.write(prefix.encode('utf-8'))
                geo.write(b'\n]}')
        assert total == count
        geo_tmp.replace(dest / geo_name)
        csv_tmp.replace(dest / 'atributos.csv')
        save(dest / 'ids_origem.json', ids_result)
        if checkpoint.exists():
            checkpoint.unlink()
        entry.update(status='completo_com_falhas_de_geometria' if problems else 'completo', registros=total, contagem_origem=count, pasta=str(dest.relative_to(ROOT)), bytes_geometria=(dest / geo_name).stat().st_size, arquivo_geometria=geo_name, formato_geometria='EsriJSON' if native else 'GeoJSON', sem_geometria=missing, falhas_geometria=len(problems))
        print(f'OK {total:>7} {service["title"]} / {meta["name"]}', flush=True)
    except Exception as error:
        entry.update(status='erro', erro=str(error))
        print(f'ERRO {meta["name"]}: {error}', flush=True)
    return entry

