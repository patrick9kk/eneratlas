"""Exercita o instalador real no Windows PowerShell 5.1, sem downloads grandes."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import zipfile

import pytest

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Instalador Windows')
SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/setup_windows.ps1'


def ps(tmp_path, body):
    wrapper = tmp_path / 'test.ps1'
    wrapper.write_text(". '" + str(SCRIPT).replace("'", "''") + "'\n" + body, encoding='utf-8-sig')
    return subprocess.run([
        str(Path(os.environ['SystemRoot']) / 'System32/WindowsPowerShell/v1.0/powershell.exe'),
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(wrapper),
    ], cwd=tmp_path, capture_output=True, text=True)


def asset(path):
    return {'name': path.name, 'digest': 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest(),
            'browser_download_url': 'https://github.com/patrick9kk/eneratlas/releases/download/test/' + path.name}


def test_complete_install_and_reuse(tmp_path):
    cache = tmp_path / 'downloads'
    latest_dir = cache / 'test'
    latest_dir.mkdir(parents=True)
    exe = latest_dir / 'EnerAtlas.exe'
    exe.write_bytes(b'fixture executable, never launched')
    archive_dir = cache / 'acervo-v1.0.0'
    archive_dir.mkdir()
    db = tmp_path / 'original.db'
    with sqlite3.connect(db) as connection:
        connection.execute('CREATE TABLE preservation(value TEXT)')
        connection.execute("INSERT INTO preservation VALUES ('original')")
    archive = tmp_path / 'package.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.write(db, 'EnerAtlas/data/eneratlas.db')
        z.writestr('EnerAtlas/data/rasters/example.txt', 'raster fixture')
    content = archive.read_bytes()
    step = (len(content) + 3) // 4
    parts = []
    for index in range(4):
        part = archive_dir / f'EnerAtlas-Windows-portatil.zip.part{index + 1:03}'
        part.write_bytes(content[index * step:(index + 1) * step])
        parts.append(asset(part))
    manifest = archive_dir / 'EnerAtlas-SHA256SUMS.txt'
    manifest.write_text(hashlib.sha256(content).hexdigest() + '  EnerAtlas-Windows-portatil.zip\n')
    metadata = {'latest': {'tag_name': 'test', 'assets': [asset(exe)]},
                'base': {'assets': [asset(manifest), *parts]}}
    (tmp_path / 'metadata.json').write_text(json.dumps(metadata))
    result = ps(tmp_path, """
$meta = Get-Content metadata.json -Raw | ConvertFrom-Json
function Get-ReleaseMetadata($Tag) { if ($Tag -eq 'latest') { return $meta.latest }; return $meta.base }
function Get-AvailableBytes($Path) { return 100GB }
function Invoke-WebRequest { throw 'Unexpected network download' }
$InstallRoot=Join-Path $PWD 'installed'; $DataRoot=Join-Path $PWD 'data'; $CacheRoot=Join-Path $PWD 'downloads'
$NoLaunch=$true; $NoShortcuts=$true
Install-EnerAtlas | Out-Null
function Get-ReleaseMetadata($Tag) { if ($Tag -ne 'latest') { throw 'Existing data must not fetch old snapshot' }; return $meta.latest }
Install-EnerAtlas | Out-Null
""")
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / 'data/eneratlas.db').read_bytes() == db.read_bytes()
    assert (tmp_path / 'installed/EnerAtlas.exe').read_bytes() == exe.read_bytes()
    assert (tmp_path / 'data/rasters/example.txt').read_text() == 'raster fixture'


def test_bad_hash_and_zip_traversal(tmp_path):
    archive = tmp_path / 'bad.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('../escaped.txt', 'must not escape')
    (tmp_path / 'part').write_bytes(b'bad content')
    result = ps(tmp_path, """
$rejected=$false
try { Join-VerifiedParts @((Join-Path $PWD 'part')) (Join-Path $PWD 'joined.zip') ('0'*64) | Out-Null } catch { $rejected=$true }
if (-not $rejected) { throw 'Incorrect hash accepted' }
$rejected=$false
try { Expand-VerifiedZip (Join-Path $PWD 'bad.zip') (Join-Path $PWD 'extract') } catch { $rejected=$true }
if (-not $rejected) { throw 'Zip traversal accepted' }
""")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (tmp_path / 'escaped.txt').exists()


def test_corrupt_download_preserves_previous_file(tmp_path):
    target = tmp_path / 'EnerAtlas.exe'
    target.write_bytes(b'previous installation')
    result = ps(tmp_path, """
function Invoke-WebRequest { param($Uri,$OutFile,$Headers,$TimeoutSec,[switch]$UseBasicParsing)
    [IO.File]::WriteAllText($OutFile, 'corrupt download')
}
$asset=[pscustomobject]@{name='EnerAtlas.exe';digest=('sha256:'+('0'*64));browser_download_url='https://github.com/patrick9kk/eneratlas/releases/download/test/EnerAtlas.exe'}
$rejected=$false
try { Get-VerifiedAsset $asset $PWD | Out-Null } catch { $rejected=$true }
if (-not $rejected) { throw 'Corrupt download accepted' }
""")
    assert result.returncode == 0, result.stdout + result.stderr
    assert target.read_bytes() == b'previous installation'
