"""Conversão explícita de CRS; análise usa a geometria integral, nunca a de tela."""
import math
import re
import unicodedata
from functools import lru_cache
from pyproj import CRS, Geod, Transformer
from shapely import make_valid, STRtree
from shapely.geometry import shape, Point, MultiPoint, MultiLineString, Polygon, MultiPolygon
from shapely.ops import transform


def normalized(value):
    text = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', text)


@lru_cache(maxsize=128)
def transformer(source, target='EPSG:4326'):
    return Transformer.from_crs(source, target, always_xy=True).transform


def esri_shape(g):
    if 'x' in g:
        return Point(g['x'], g['y'])
    if 'points' in g:
        return MultiPoint([p[:2] for p in g['points']])
    if 'paths' in g:
        return MultiLineString([[p[:2] for p in line] for line in g['paths'] if len(line) > 1])
    if 'rings' in g:
        # Esri rings can be multipart, holes or nested islands. Find containment,
        # rather than relying on inconsistent winding in third-party services.
        rings = sorted([Polygon([p[:2] for p in ring]) for ring in g['rings'] if len(ring) >= 4], key=lambda p: -abs(p.area))
        tree = STRtree(rings)
        parents, depth = [], []
        for i, ring in enumerate(rings):
            point = Point(ring.exterior.coords[0])
            containing = [int(j) for j in tree.query(point) if j < i and rings[j].covers(point)]
            parent = min(containing, key=lambda j: rings[j].area) if containing else None
            parents.append(parent)
            depth.append(depth[parent] + 1 if parent is not None else 0)
        children = {}
        for j, parent in enumerate(parents):
            if parent is not None and depth[j] % 2:
                children.setdefault(parent, []).append(rings[j].exterior.coords)
        polygons = [Polygon(ring.exterior.coords, children.get(i, [])) for i, ring in enumerate(rings) if depth[i] % 2 == 0]
        return MultiPolygon(polygons) if len(polygons) != 1 else polygons[0]
    if all(k in g for k in ('xmin', 'ymin', 'xmax', 'ymax')):
        from shapely.geometry import box
        return box(g['xmin'], g['ymin'], g['xmax'], g['ymax'])
    raise ValueError('Geometria Esri não suportada: ' + ', '.join(g))


def decode_geometry(raw, native=False, sr=None):
    if not raw:
        return None, None
    geom = esri_shape(raw) if native else shape(raw)
    repaired = not geom.is_valid
    if repaired:
        geom = make_valid(geom)
    if native:
        ref = raw.get('spatialReference') or sr or {}
        wkid = ref.get('latestWkid') or ref.get('wkid')
        if ref.get('wkt'):
            crs = ref['wkt']
        elif wkid:
            crs = f'EPSG:{3857 if wkid in (102100, 102113, 900913) else wkid}'
        else:
            raise ValueError('CRS não informado; coordenadas não foram presumidas')
        geom = transform(transformer(crs), geom)
    if geom.is_empty:
        return None, 'Geometria vazia'
    bounds = geom.bounds
    if not all(math.isfinite(v) for v in bounds) or bounds[0] < -180 or bounds[2] > 180 or bounds[1] < -90 or bounds[3] > 90:
        raise ValueError('Coordenadas fora dos limites WGS84')
    return geom, 'Topologia corrigida para análise; arquivo original preservado' if repaired else None


def metric_transform(geom):
    c = geom.representative_point()
    crs = CRS.from_proj4(f'+proj=aeqd +lat_0={c.y:.8f} +lon_0={c.x:.8f} +datum=WGS84 +units=m')
    return transformer('EPSG:4326', crs.to_string())


def measurements(geom):
    if geom is None:
        return {}
    geod = Geod(ellps='WGS84')
    result = {'tipo': geom.geom_type, 'centro': list(geom.representative_point().coords[0])[:2]}
    if 'Polygon' in geom.geom_type:
        from shapely.geometry.polygon import orient
        oriented = orient(geom) if geom.geom_type == 'Polygon' else MultiPolygon([orient(p) for p in geom.geoms])
        area, perimeter = geod.geometry_area_perimeter(oriented)
        result.update(area_km2=abs(area) / 1e6, perimetro_km=perimeter / 1000)
    elif 'Line' in geom.geom_type:
        result['comprimento_km'] = geod.geometry_length(geom) / 1000
    return result


STYLES = [
    ('eolica', 'Eólica', '#00a6a0', 'wind'), ('aerogerador', 'Aerogerador', '#008c84', 'wind'),
    ('fotovolta', 'Solar', '#e5a51a', 'sun'), ('ufv', 'Solar', '#e5a51a', 'sun'),
    ('subest', 'Subestação', '#d36c43', 'substation'), ('transmiss', 'Transmissão', '#7956c8', 'tower'),
    ('termel', 'Termelétrica', '#ce6a54', 'factory'), ('termele', 'Termelétrica', '#ce6a54', 'factory'),
    ('nuclear', 'Nuclear', '#9b65b2', 'atom'), ('hidrel', 'Hidrelétrica', '#347fc0', 'water'),
    ('aproveitamento', 'Hidrelétrica', '#347fc0', 'water'), ('cgh', 'Hidrelétrica', '#347fc0', 'water'),
    ('barragem', 'Barragem', '#497ba4', 'dam'), ('reservat', 'Reservatório', '#459cd0', 'water'),
    ('casadeforca', 'Casa de força', '#426eb6', 'factory'), ('canal', 'Canal', '#419fc1', 'water'),
    ('curvadenivel', 'Curva de nível', '#b48a5c', 'contour'), ('curvasdenivel', 'Curva de nível', '#b48a5c', 'contour'),
    ('indigena', 'Terra indígena', '#528653', 'leaf'), ('quilomb', 'Quilombola', '#9a7c45', 'leaf'),
    ('uc', 'Área protegida', '#588b54', 'leaf'), ('conserv', 'Área protegida', '#588b54', 'leaf'),
    ('bioma', 'Bioma', '#75a861', 'leaf'), ('rodovia', 'Rodovia', '#898074', 'road'),
    ('gasoduto', 'Gasoduto', '#b07b48', 'pipe'), ('petroleo', 'Petróleo e gás', '#a27751', 'pipe'),
    ('municip', 'Município', '#6f8393', 'area'), ('estad', 'Limite territorial', '#6f8393', 'area'),
]


def style_for(name):
    n = normalized(name)
    for token, label, color, icon in STYLES:
        if token in n:
            return {'tipo': label, 'color': color, 'icon': icon}
    return {'tipo': 'Componente', 'color': '#637e91', 'icon': 'pin'}
