import json
import sqlite3
from pathlib import Path


def connect(path):
    db = sqlite3.connect(str(path), timeout=120)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=120000')
    return db


def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
        CREATE TABLE IF NOT EXISTS layers (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL,
            url TEXT, metadata TEXT NOT NULL DEFAULT '{}', style TEXT NOT NULL,
            signature TEXT, state TEXT NOT NULL DEFAULT 'pendente',
            count INTEGER DEFAULT 0, located INTEGER DEFAULT 0, issues INTEGER DEFAULT 0,
            updated TEXT, file TEXT, error TEXT
        );
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY, layer_id TEXT NOT NULL, oid TEXT, name TEXT,
            uf TEXT, status TEXT, search TEXT, attrs TEXT NOT NULL,
            geom BLOB, note TEXT, minx REAL, miny REAL, maxx REAL, maxy REAL
        );
        CREATE INDEX IF NOT EXISTS feature_layer ON features(layer_id);
        CREATE INDEX IF NOT EXISTS feature_name ON features(name);
        CREATE VIRTUAL TABLE IF NOT EXISTS spatial USING rtree(id,minx,maxx,miny,maxy);
        CREATE TABLE IF NOT EXISTS identifiers (feature_id INTEGER, kind TEXT, value TEXT);
        CREATE INDEX IF NOT EXISTS identifier_lookup ON identifiers(kind,value);
        CREATE INDEX IF NOT EXISTS identifier_feature ON identifiers(feature_id);
        ''')


def layer_dict(row):
    value = dict(row)
    value['style'] = json.loads(value['style'])
    value['metadata'] = json.loads(value['metadata'])
    value.pop('signature', None)
    value.pop('file', None)
    return value
