import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from eneratlas.startup import acquire_data_lock, choose_data_dir, find_running


def test_installed_data_without_arguments(tmp_path):
    base = tmp_path / 'program'
    base.mkdir()
    data = tmp_path / 'actual-data'
    data.mkdir()
    (base / 'INSTALACAO.json').write_text(json.dumps({'data':str(data)}))
    assert choose_data_dir(None, base, True) == data.resolve()
    assert choose_data_dir(tmp_path / 'explicit', base, True) == (tmp_path / 'explicit').resolve()
    assert choose_data_dir(None, base, False) == (base / 'data').resolve()


def test_portable_and_installed_fallback(tmp_path):
    base = tmp_path / 'portable'
    base.mkdir()
    installed = tmp_path / 'local/EnerAtlas/data'
    installed.mkdir(parents=True)
    (installed / 'eneratlas.db').touch()
    assert choose_data_dir(None, base, True, tmp_path / 'local') == installed.resolve()
    (base / 'data').mkdir()
    (base / 'data/eneratlas.db').touch()
    assert choose_data_dir(None, base, True, tmp_path / 'local') == (base / 'data').resolve()


def test_repeated_lock_does_not_write_before_locking(tmp_path):
    lock = acquire_data_lock(tmp_path)
    try:
        with pytest.raises(OSError):
            acquire_data_lock(tmp_path)
        assert (tmp_path / 'app.lock').stat().st_size == 1
    finally:
        lock.close()


def test_repeated_launch_reuses_same_catalog(tmp_path):
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, str(root / 'launch.py'), '--data-dir', str(tmp_path),
               '--no-browser', '--no-autodiscover', '--port', '0']
    process = subprocess.Popen(command, cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        deadline = time.monotonic() + 25
        url = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail('Primeira instancia encerrou prematuramente')
            url = find_running(tmp_path, 0)
            if url:
                break
            time.sleep(.1)
        assert url, 'Servidor nao iniciou'
        state = json.loads((tmp_path / 'runtime.json').read_text())
        second = subprocess.run(command, cwd=root, capture_output=True, timeout=15)
        assert second.returncode == 0, second.stderr.decode(errors='replace')
        assert json.loads((tmp_path / 'runtime.json').read_text()) == state
        assert process.poll() is None
        with urlopen(url + '/api/status') as response:
            assert json.load(response)['application'] == 'EnerAtlas'
        assert find_running(tmp_path.parent / 'different-data', int(url.rsplit(':',1)[1])) is None
    finally:
        process.terminate()
        process.wait(timeout=10)
