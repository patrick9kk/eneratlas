import gzip
import io
import json
from pathlib import Path
import pytest
from shapely.geometry import Point, Polygon
from eneratlas.geometry import decode_geometry, esri_shape, normalized
from eneratlas.catalog import Importer, discovery, stable_id
from eneratlas.store import initialize, connect
from eneratlas.server import create_app


@pytest.fixture
def sample(tmp_path):
    db=tmp_path/'test.db';initialize(db)
    manifest=tmp_path/'managed/sample';manifest.mkdir(parents=True)
    features=[{'type':'Feature','properties':{'OBJECTID':1,'Nome':'Usina São José','CEG':'UFV.PE.0001','UF':'PE','texto':'=1+1'},'geometry':{'type':'Point','coordinates':[-35,-8]}}, {'type':'Feature','properties':{'OBJECTID':2,'Nome':'Linha próxima','CEG':'UFV.PE.0001','UF':'PE'},'geometry':{'type':'LineString','coordinates':[[-35.001,-8.001],[-34.999,-7.999]]}}, {'type':'Feature','properties':{'OBJECTID':3,'Nome':'Sem posição'},'geometry':None}]
    (manifest/'dados.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features}),encoding='utf-8')
    item={'id':'sample','name':'Usinas','source':'LOCAL','url':'https://example.org/source','meta':{'fields':[{'name':'Nome','alias':'Nome oficial'}]},'file':'dados.geojson','state':'completo','expected':3}
    (manifest/'layer.json').write_text(json.dumps(item),encoding='utf-8')
    importer=Importer(db,[tmp_path],tmp_path/'state.json');importer.run()
    app=create_app(db,importer,Path(__file__).resolve().parents[1],tmp_path)
    client=app.test_client();client.environ_base['HTTP_HOST']='localhost'
    return db,importer,client,manifest


def test_crs_holes_and_disjoint_rings():
    raw={'rings':[[[0,0],[10,0],[10,10],[0,10],[0,0]],[[2,2],[8,2],[8,8],[2,8],[2,2]],[[3,3],[4,3],[4,4],[3,4],[3,3]],[[20,0],[21,0],[21,1],[20,1],[20,0]]]}
    g=esri_shape(raw)
    assert g.area==66
    assert not g.covers(Point(2.5,2.5))
    assert g.covers(Point(3.5,3.5))
    g,note=decode_geometry({'x':-3896182.18,'y':-893463.75},True,{'wkid':3857})
    assert g.x==pytest.approx(-35,abs=.00001)
    assert g.y==pytest.approx(-8,abs=.00001)
    with pytest.raises(ValueError,match='CRS'):
        decode_geometry({'x':1,'y':2},True)


def test_repair_and_bounds():
    g,note=decode_geometry({'type':'Polygon','coordinates':[[[0,0],[2,2],[2,0],[0,2],[0,0]]]})
    assert g.is_valid and note
    with pytest.raises(ValueError,match='limites'):
        decode_geometry({'type':'Point','coordinates':[400,600]})


def test_import_idempotent_and_rollback(sample):
    db,imp,client,manifest=sample
    with connect(db) as c:
        assert c.execute('select count(*) from features').fetchone()[0]==3
        ids=[r[0] for r in c.execute('select id from features')]
    imp.run()
    with connect(db) as c: assert [r[0] for r in c.execute('select id from features')]==ids
    (manifest/'dados.geojson').write_text('{"features":[{"properties":{"Nome":"Novo"}},',encoding='utf-8')
    imp.run()
    with connect(db) as c:
        assert c.execute('select count(*) from features').fetchone()[0]==3
        assert c.execute('select count(*) from spatial').fetchone()[0]==2
    assert imp.state['errors']


def test_multimember_gzip_and_native_crs(tmp_path):
    folder=tmp_path/'managed/native';folder.mkdir(parents=True)
    first=b'{"features":[{"attributes":{"OBJECTID":1},"geometry":{"x":-35,"y":-8}}'
    second=b',{"attributes":{"OBJECTID":2},"geometry":null}]}'
    (folder/'dados.esrijson.gz').write_bytes(gzip.compress(first)+gzip.compress(second))
    item={'id':'native','name':'Reservatório','source':'ANEEL','url':'https://example.org/0','state':'completo','file':'dados.esrijson.gz','meta':{'extent':{'spatialReference':{'wkid':4674}}},'expected':2}
    (folder/'layer.json').write_text(json.dumps(item),encoding='utf-8')
    db=tmp_path/'db';initialize(db);imp=Importer(db,[tmp_path],tmp_path/'status.json');imp.run()
    assert not imp.state['errors']
    with connect(db) as c: assert c.execute('select count,located from layers').fetchone()[:]==(2,1)


def test_queries_detail_join_and_export(sample):
    db,imp,c,_=sample
    r=c.get('/api/features?q=saojose').json
    assert r['total']==1
    fid=r['items'][0]['id']
    detail=c.get(f'/api/features/{fid}').json
    assert detail['aliases']['Nome']=='Nome oficial'
    assert detail['geometry']['coordinates']==[-35,-8]
    assert c.get(f'/api/related/{fid}').json['items'][0]['name']=='Linha próxima'
    assert c.get('/api/features?located=0').json['total']==1
    assert len(c.get('/api/map?bbox=-35.01,-8.01,-34.99,-7.99').json['features'])==2
    assert c.get('/api/map?bbox=1,1,-1,-1').status_code==400
    assert 'Usina São José' in c.get('/api/export.csv?q=saojose').data.decode('utf-8-sig')


def test_spatial_and_security(sample):
    _,_,c,_=sample
    token=c.get('/api/status').json['token']
    assert c.post('/api/sync').status_code==403
    assert c.get('/api/status',headers={'Host':'evil.test'}).status_code==403
    assert c.post('/api/sync',headers={'X-EnerAtlas-Token':token,'Origin':'https://evil.test'}).status_code==403
    body={'feature':1,'mode':'near','radius_km':.5,'layers':['sample']}
    r=c.post('/api/compare',json=body,headers={'X-EnerAtlas-Token':token})
    assert r.status_code==200
    assert len(r.json['items'])==1
    assert r.json['items'][0]['distance_km']<.001
    body['radius_km']=-2
    assert c.post('/api/compare',json=body,headers={'X-EnerAtlas-Token':token}).status_code==400


def test_csv_import_and_documented_source(sample):
    _,imp,c,_=sample;token=c.get('/api/status').json['token']
    r=c.post('/api/import',data={'name':'Meu projeto','source_url':'https://example.org/public','description':'Cadastro próprio; dados de teste','longitude':'lon','latitude':'lat','file':(io.BytesIO('nome;lon;lat\nProjeto;-40;-10\nOutro;;\n'.encode()),'local.csv')},headers={'X-EnerAtlas-Token':token})
    assert r.status_code==200
    # Wait for the asynchronous import before assertions.
    imp.lock.acquire();imp.lock.release()
    rows=c.get('/api/features?source=LOCAL&q=projeto').json
    assert rows['total']==1


def test_explicit_field_join_without_geometry_inference(sample):
    _,_,c,_=sample;token=c.get('/api/status').json['token']
    response=c.post('/api/join',json={'feature':1,'field':'CEG','layer':'sample','target_field':'CEG'},headers={'X-EnerAtlas-Token':token})
    assert response.status_code==200
    assert len(response.json['items'])==1
    assert response.json['items'][0]['name']=='Linha próxima'
    assert 'não' in response.json['note']
    response=c.post('/api/join',json={'feature':1,'field':'CEG','layer':'sample','target_field':'CEG"),1); DROP TABLE features; --'},headers={'X-EnerAtlas-Token':token})
    assert response.status_code==200 and response.json['items']==[]
    assert c.get('/api/features').json['total']==3


def test_portable_raster_survives_without_original_source(tmp_path):
    from eneratlas.raster import prepare_rasters
    from PIL import Image
    target=tmp_path/'rasters';target.mkdir()
    Image.new('RGBA',(1,1),(10,20,30,255)).save(target/'ipa_total.png')
    previous=[{'id':'ipa_total','url':'/raster/ipa_total.png','bounds':[[-35,-77],[7,-27]]}]
    (target/'catalog.json').write_text(json.dumps(previous),encoding='utf-8')
    assert prepare_rasters([],tmp_path)==previous
    assert json.loads((target/'catalog.json').read_text())==previous
