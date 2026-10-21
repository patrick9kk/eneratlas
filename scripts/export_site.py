"""Cria snapshot público para GitHub Pages, com limites explícitos por camada."""
import argparse
import gzip
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shapely import from_wkb
from shapely.geometry import mapping
from eneratlas.store import connect, layer_dict
from eneratlas.geometry import measurements


def export(db_path, output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[1]
    shutil.copytree(root/'static',output/'static',dirs_exist_ok=True)
    html=(root/'templates/index.html').read_text(encoding='utf-8').replace('="/static/','="./static/')
    (output/'index.html').write_text(html,encoding='utf-8')
    (output/'.nojekyll').touch()
    (output/'data').mkdir(exist_ok=True)
    catalog=[]
    with connect(db_path) as db:
        for row in db.execute('SELECT * FROM layers ORDER BY source,name'):
            layer=layer_dict(row)
            # Large terrain/administrative geometry is available in the desktop
            # archive. Publish ALL rows of admitted layers, never a silent sample.
            admitted=row['state']=='indexado' and row['count']<=12000 and 'Raster' not in layer['metadata'].get('type','')
            layer.update(online_unavailable=not admitted,chunks=[],online_count=0,online_located=0)
            if not admitted:
                layer['state']='desktop_only'
                catalog.append(layer);continue
            chunk=[]
            def flush():
                if not chunk:return
                name=f'data/{row["id"]}_{len(layer["chunks"]):03}.json.gz'
                with gzip.open(output/name,'wt',encoding='utf-8',compresslevel=9) as stream:
                    json.dump(chunk,stream,ensure_ascii=False,separators=(',',':'))
                layer['chunks'].append(name);chunk.clear()
            meta=layer['metadata']
            aliases={f['name']:f.get('alias',f['name']) for f in meta.get('fields',[])}
            domains={f['name']:{str(v['code']):v['name'] for v in (f.get('domain') or {}).get('codedValues',[])} for f in meta.get('fields',[])}
            for feature in db.execute('SELECT * FROM features WHERE layer_id=? ORDER BY id',(row['id'],)):
                geom=from_wkb(feature['geom']) if feature['geom'] else None
                attrs=json.loads(feature['attrs'])
                simplified=geom.simplify(.002,preserve_topology=True) if geom is not None else None
                chunk.append({'id':feature['id'],'layer_id':row['id'],'layer_name':row['name'],'source':row['source'],'name':feature['name'],'uf':feature['uf'],'status':feature['status'],'located':geom is not None,'search':feature['search'],'attributes':attrs,'aliases':aliases,'decoded':{k:domains.get(k,{}).get(str(v)) for k,v in attrs.items() if domains.get(k,{}).get(str(v))},'note':(feature['note']+'; ' if feature['note'] else '')+'Versão online: geometria simplificada para consulta. Não usar para análise de interseção ou engenharia.','measurements':measurements(geom),'geometry':mapping(simplified) if simplified is not None else None,'bounds':list(geom.bounds) if geom is not None else None,'source_url':row['url'],'updated':row['updated'],'style':layer['style']})
                layer['online_count']+=1
                layer['online_located']+=geom is not None
                if len(chunk)>=1000:flush()
            flush();catalog.append(layer)
    (output/'data/catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    manifest={'generated_utc':datetime.now(timezone.utc).isoformat(),'layers':len(catalog),'online_layers':sum(not l['online_unavailable'] for l in catalog),'online_records':sum(l['online_count'] for l in catalog),'simplification_degrees':.002,'max_layer_rows':12000,'note':'Todas as linhas das camadas admitidas. Camadas maiores, raster e downloads pendentes identificados no catálogo; acervo completo no executável. Código MIT; dados continuam sujeitos às licenças das fontes.'}
    (output/'snapshot.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.database,a.output)
