import csv
import io
import json
import math
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context
from shapely import from_wkb
from shapely.geometry import mapping
from shapely.ops import transform
from .geometry import measurements, metric_transform, normalized, style_for
from .store import connect, layer_dict
from .catalog import stable_id


def create_app(db_path, importer, assets, data_dir):
    app = Flask(__name__, static_folder=str(Path(assets) / 'static'), template_folder=str(Path(assets) / 'templates'))
    app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024
    token = secrets.token_urlsafe(32)
    data_dir = Path(data_dir)

    @app.before_request
    def local_only():
        # Host and Origin checks prevent a remote page from controlling a local
        # import service through DNS rebinding or cross-origin form submission.
        if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
            return jsonify(error='Acesso somente local'), 403
        if request.method == 'POST':
            origin = request.headers.get('Origin')
            if origin and urlsplit(origin).netloc != request.host:
                return jsonify(error='Origem não autorizada'), 403
            if not secrets.compare_digest(request.headers.get('X-EnerAtlas-Token', ''), token):
                return jsonify(error='Recarregue a página para continuar'), 403

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://tile.openstreetmap.org; connect-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'"
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(ValueError)
    def bad_value(error):
        return jsonify(error=str(error)), 400

    @app.get('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    @app.get('/api/status')
    def status():
        with connect(db_path) as db:
            summary = dict(db.execute('SELECT sum(count) registros,sum(located) localizados,count(*) camadas,sum(issues) alertas FROM layers').fetchone())
        return jsonify(importer=importer.state, summary=summary, token=token, update=getattr(app, 'update_state', {'running': False}), version='1.0.0')

    @app.get('/api/layers')
    def layers():
        with connect(db_path) as db:
            return jsonify([layer_dict(r) for r in db.execute('SELECT * FROM layers ORDER BY source,name')])

    def filters(args, spatial=False):
        clauses, params = ['1=1'], []
        ids = [x for x in args.get('layers', '').split(',') if x]
        if ids:
            clauses.append('f.layer_id IN (' + ','.join('?' for _ in ids) + ')')
            params.extend(ids)
        if args.get('q'):
            clauses.append('f.search LIKE ?')
            params.append('%' + normalized(args['q']) + '%')
        if args.get('source'):
            clauses.append('l.source=?')
            params.append(args['source'])
        if args.get('uf'):
            clauses.append('upper(f.uf)=?')
            params.append(args['uf'].upper())
        if args.get('status'):
            clauses.append('f.status=?')
            params.append(args['status'])
        if args.get('located') == '1':
            clauses.append('f.geom IS NOT NULL')
        if args.get('located') == '0':
            clauses.append('f.geom IS NULL')
        if spatial and args.get('bbox'):
            bounds = [float(x) for x in args['bbox'].split(',')]
            if len(bounds) != 4 or not all(math.isfinite(x) for x in bounds) or bounds[0] > bounds[2] or bounds[1] > bounds[3]:
                raise ValueError('Limites do mapa inválidos')
            clauses.append('f.id IN (SELECT id FROM spatial WHERE maxx>=? AND minx<=? AND maxy>=? AND miny<=?)')
            params.extend([bounds[0],bounds[2],bounds[1],bounds[3]])
        return ' AND '.join(clauses), params

    def brief(row):
        return {k: row[k] for k in ('id','layer_id','name','uf','status','source','layer_name')} | {'located': row['geom'] is not None}

    select = 'SELECT f.*,l.name layer_name,l.source,l.style FROM features f JOIN layers l ON l.id=f.layer_id '

    @app.get('/api/options')
    def options():
        where, params = filters(request.args)
        with connect(db_path) as db:
            values = {}
            for field in ('uf', 'status'):
                values[field] = [r[0] for r in db.execute(f'SELECT DISTINCT f.{field} FROM features f JOIN layers l ON l.id=f.layer_id WHERE {where} AND f.{field}<>\'\' ORDER BY 1 LIMIT 500', params)]
        return jsonify(values)

    @app.get('/api/features')
    def feature_list():
        where, params = filters(request.args)
        limit = min(200, max(1, int(request.args.get('limit', 50))))
        offset = max(0, int(request.args.get('offset', 0)))
        with connect(db_path) as db:
            total = db.execute('SELECT count(*) FROM features f JOIN layers l ON l.id=f.layer_id WHERE ' + where, params).fetchone()[0]
            rows = db.execute(select + 'WHERE ' + where + ' ORDER BY f.id LIMIT ? OFFSET ?', params + [limit, offset])
            return jsonify(total=total, items=[brief(r) for r in rows], offset=offset, limit=limit)

    @app.get('/api/map')
    def map_data():
        where, params = filters(request.args, spatial=True)
        zoom = min(20, max(1, float(request.args.get('zoom', 4))))
        limit = 1800
        tolerance = 360 / (256 * 2 ** zoom) * 1.3
        result = []
        with connect(db_path) as db:
            layer_ids = [x for x in request.args.get('layers','').split(',') if x]
            rows, truncated = [], False
            if layer_ids and layer_ids != ['__none__']:
                budget = max(1, limit // len(layer_ids))
                for layer_id in layer_ids:
                    subset = list(db.execute(select + 'WHERE f.geom IS NOT NULL AND ' + where + ' AND f.layer_id=? ORDER BY f.id LIMIT ?', params+[layer_id,budget+1]))
                    truncated |= len(subset)>budget
                    rows.extend(subset[:budget])
            else:
                rows = list(db.execute(select + 'WHERE f.geom IS NOT NULL AND ' + where + ' ORDER BY f.id LIMIT ?', params + [limit + 1]))
                truncated = len(rows)>limit
            for row in rows[:limit]:
                geom = from_wkb(row['geom']).simplify(tolerance, preserve_topology=True)
                result.append({'type': 'Feature', 'geometry': mapping(geom), 'properties': brief(row) | {'style': json.loads(row['style'])}})
        return jsonify(type='FeatureCollection', features=result, truncated=truncated, limit=limit)

    @app.get('/api/features/<int:fid>')
    def feature_detail(fid):
        with connect(db_path) as db:
            row = db.execute(select + 'WHERE f.id=?', (fid,)).fetchone()
            if not row:
                return jsonify(error='Registro não encontrado. Atualize a consulta.'), 404
            layer = db.execute('SELECT * FROM layers WHERE id=?', (row['layer_id'],)).fetchone()
            geom = from_wkb(row['geom']) if row['geom'] is not None else None
            attrs = json.loads(row['attrs'])
            meta = json.loads(layer['metadata'])
            aliases = {f['name']: f.get('alias', f['name']) for f in meta.get('fields', [])}
            domains = {f['name']: {str(x['code']): x['name'] for x in (f.get('domain') or {}).get('codedValues', [])} for f in meta.get('fields', [])}
            decoded = {k: domains.get(k, {}).get(str(v)) for k, v in attrs.items() if domains.get(k, {}).get(str(v))}
            result = brief(row) | {'attributes': attrs, 'aliases': aliases, 'decoded': decoded, 'note': row['note'], 'measurements': measurements(geom), 'source_url': layer['url'], 'updated': layer['updated'], 'geometry': mapping(geom) if geom is not None else None, 'style': json.loads(layer['style'])}
            return jsonify(result)

    @app.get('/api/related/<int:fid>')
    def related(fid):
        with connect(db_path) as db:
            rows = db.execute('''SELECT DISTINCT f.*,l.name layer_name,l.source,l.style,b.kind match_kind,b.value match_value
                FROM identifiers a JOIN identifiers b ON a.kind=b.kind AND a.value=b.value
                JOIN features f ON f.id=b.feature_id JOIN layers l ON l.id=f.layer_id
                WHERE a.feature_id=? AND b.feature_id<>? ORDER BY f.id LIMIT 201''', (fid,fid)).fetchall()
            return jsonify(items=[brief(r) | {'basis': r['match_kind'] + ': ' + r['match_value']} for r in rows[:200]], truncated=len(rows)>200, note='Identificadores iguais geram vínculos para conferência. CNPJ relaciona o agente, não comprova o mesmo projeto. ObjectID e nomes não são usados para unir projetos.')

    @app.post('/api/compare')
    def compare():
        value = request.get_json()
        fid, mode = int(value['feature']), value.get('mode', 'near')
        if mode not in ('near','intersects','within'):
            raise ValueError('Operação não reconhecida')
        radius = float(value.get('radius_km', 10))
        if not math.isfinite(radius) or not 0 <= radius <= 100:
            raise ValueError('Distância deve estar entre 0 e 100 km')
        target_layers = value.get('layers', [])
        if not target_layers:
            raise ValueError('Selecione ao menos uma camada de destino')
        with connect(db_path) as db:
            row = db.execute('SELECT * FROM features WHERE id=?', (fid,)).fetchone()
            if row is None or row['geom'] is None:
                raise ValueError('O projeto selecionado não possui geometria publicada')
            selected = from_wkb(row['geom'])
            west,south,east,north = selected.bounds
            delta = radius / 110 if mode == 'near' else 0
            dx = delta / max(0.1, math.cos(math.radians((south+north)/2)))
            clauses, params = filters({'layers': ','.join(target_layers)})
            candidates = list(db.execute(select + 'WHERE ' + clauses + ' AND f.id<>? AND f.id IN (SELECT id FROM spatial WHERE maxx>=? AND minx<=? AND maxy>=? AND miny<=?) ORDER BY f.id LIMIT 5001', params+[fid,west-dx,east+dx,south-delta,north+delta]))
            project = metric_transform(selected)
            local = transform(project, selected) if mode == 'near' else None
            results = []
            for candidate in candidates[:5000]:
                geom = from_wkb(candidate['geom'])
                distance = None
                if mode == 'near':
                    distance = local.distance(transform(project, geom)) / 1000
                    hit = distance <= radius
                elif mode == 'within':
                    hit = selected.covers(geom)
                else:
                    hit = selected.intersects(geom)
                if hit:
                    results.append(brief(candidate) | {'distance_km': distance})
            results.sort(key=lambda x: (x['distance_km'] or 0, x['id']))
        return jsonify(items=results, candidate_limit=5000, truncated=len(candidates)>5000, mode=mode, note='Geometria integral; distâncias aproximadas em projeção azimutal equidistante local (WGS84). Uso exploratório, sujeito à precisão e data das fontes.')

    @app.post('/api/join')
    def join_fields():
        value = request.get_json()
        with connect(db_path) as db:
            row = db.execute('SELECT attrs FROM features WHERE id=?', (int(value['feature']),)).fetchone()
            if not row:
                raise ValueError('Selecione um registro válido')
            attrs = json.loads(row['attrs'])
            field, target = value.get('field',''), value.get('target_field','')
            key = normalized(attrs.get(field))
            if not key or key in ('null','nan'):
                raise ValueError('Campo de origem vazio ou não encontrado')
            if not target:
                raise ValueError('Informe o campo de destino')
            db.create_function('norm', 1, normalized, deterministic=True)
            json_path = '$.' + json.dumps(target,ensure_ascii=False)
            rows = list(db.execute(select + 'WHERE f.layer_id=? AND f.id<>? AND norm(json_extract(f.attrs,?))=? ORDER BY f.id LIMIT 201', (value['layer'],int(value['feature']),json_path,key)))
        return jsonify(items=[brief(r) | {'basis':field+' = '+target+': '+str(attrs[field])} for r in rows[:200]],truncated=len(rows)>200,note='Igualdade normalizada dos campos escolhidos, sem unir registros nem atribuir geometria. Confirme identidade, unidade e versão; nomes ou números coincidentes não comprovam o mesmo projeto.')

    @app.get('/api/export.csv')
    def export_csv():
        where, params = filters(request.args)
        def generate():
            stream = io.StringIO(newline='')
            writer = csv.writer(stream, delimiter=';')
            writer.writerow(['id_eneratlas','fonte','camada','nome','uf','situacao','possui_geometria','atributos_json'])
            yield '\ufeff' + stream.getvalue()
            with connect(db_path) as db:
                for row in db.execute(select + 'WHERE ' + where + ' ORDER BY f.id', params):
                    stream.seek(0); stream.truncate()
                    values = [row['id'],row['source'],row['layer_name'],row['name'],row['uf'],row['status'],row['geom'] is not None,row['attrs']]
                    # Avoid spreadsheet formulas when opening original source text.
                    writer.writerow(["'" + str(v) if str(v).startswith(('=', '+', '-', '@')) else v for v in values])
                    yield stream.getvalue()
        return Response(stream_with_context(generate()), mimetype='text/csv; charset=utf-8', headers={'Content-Disposition': 'attachment; filename=eneratlas_consulta.csv'})

    @app.post('/api/sync')
    def sync():
        return jsonify(started=importer.start())

    @app.post('/api/roots')
    def roots():
        path = Path(request.get_json().get('path', '')).expanduser().resolve()
        if not path.is_dir():
            raise ValueError('Pasta não encontrada')
        if str(path) not in [str(x) for x in importer.roots]:
            importer.roots.insert(0, path)
        (data_dir / 'sources.local.json').write_text(json.dumps([str(p) for p in importer.roots],ensure_ascii=False,indent=2), encoding='utf-8')
        return jsonify(started=importer.start())

    @app.post('/api/import')
    def import_file():
        upload = request.files.get('file')
        if upload is None or Path(upload.filename).suffix.lower() not in ('.geojson','.json','.csv'):
            raise ValueError('Envie GeoJSON ou CSV UTF-8')
        name = request.form.get('name') or Path(upload.filename).stem
        item_id = stable_id('local:' + name)
        folder = data_dir / 'managed' / item_id
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / ('dados' + Path(upload.filename).suffix.lower())
        temp = folder / 'upload.tmp'
        upload.save(temp)
        if path.suffix != '.csv':
            import ijson
            with temp.open('rb') as stream:
                kind = next(ijson.items(stream, 'type'), None)
            if kind != 'FeatureCollection':
                temp.unlink()
                raise ValueError('GeoJSON deve ser FeatureCollection em WGS84 (EPSG:4326)')
        temp.replace(path)
        item = {'id':item_id,'name':name,'source':'LOCAL','url':request.form.get('source_url', ''),'meta':{'description': request.form.get('description', 'Arquivo importado pelo usuário')},'file':path.name,'state':'completo','longitude':request.form.get('longitude'),'latitude':request.form.get('latitude')}
        (folder/'layer.json').write_text(json.dumps(item,ensure_ascii=False),encoding='utf-8')
        return jsonify(started=importer.start(), id=item_id)

    @app.post('/api/update')
    def update():
        from .updater import start_update
        return jsonify(started=start_update(app, db_path, importer, data_dir, request.get_json().get('layers', [])))

    @app.get('/api/rasters')
    def rasters():
        path = data_dir / 'rasters' / 'catalog.json'
        return jsonify(json.loads(path.read_text(encoding='utf-8')) if path.exists() else [])

    @app.get('/raster/<name>')
    def raster_image(name):
        return send_from_directory(data_dir / 'rasters', name)

    @app.post('/api/shutdown')
    def shutdown():
        app.shutdown_requested = True
        return jsonify(message='Encerrando. Você pode fechar esta aba.')

    return app
