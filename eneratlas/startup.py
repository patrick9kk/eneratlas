"""Localiza os dados instalados e reutiliza uma sessao local identificada."""
import hashlib
import json
import os
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

DEFAULT_PORT = 8769


def data_identity(path):
    return hashlib.sha256(os.path.normcase(str(Path(path).resolve())).encode('utf-8')).hexdigest()


def choose_data_dir(explicit, base, frozen, local_appdata=None):
    if explicit is not None:
        return Path(explicit).resolve()
    base = Path(base)
    if frozen:
        manifest = base / 'INSTALACAO.json'
        if manifest.is_file():
            settings = json.loads(manifest.read_text(encoding='utf-8-sig'))
            if settings.get('data'):
                target = Path(settings['data'])
                if not target.is_absolute():
                    raise ValueError('A pasta de dados no manifesto deve ser absoluta.')
                return target.resolve()
        if (base / 'data/eneratlas.db').is_file():
            return (base / 'data').resolve()
        local = local_appdata or os.environ.get('LOCALAPPDATA')
        if local and (Path(local) / 'EnerAtlas/data/eneratlas.db').is_file():
            return (Path(local) / 'EnerAtlas/data').resolve()
    return (base / 'data').resolve()


def find_running(data_dir, preferred_port=DEFAULT_PORT):
    candidates = []
    state = Path(data_dir) / 'runtime.json'
    try:
        candidates.append(json.loads(state.read_text(encoding='utf-8'))['url'])
    except (OSError, ValueError, KeyError):
        pass
    if preferred_port:
        candidates.append(f'http://127.0.0.1:{preferred_port}')
    # Loopback discovery never uses the machine's HTTP proxy.
    opener = build_opener(ProxyHandler({}))
    for url in dict.fromkeys(candidates):
        parsed = urlsplit(url)
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path not in ('', '/') or parsed.query or parsed.fragment or parsed.username:
            continue
        try:
            with opener.open(url.rstrip('/') + '/api/status', timeout=2) as response:
                status = json.load(response)
            if status.get('application') == 'EnerAtlas' and status.get('data_identity') == data_identity(data_dir):
                return url.rstrip('/')
        except (OSError, URLError, ValueError):
            pass
    return None


def acquire_data_lock(data_dir):
    path = Path(data_dir) / 'app.lock'
    lock = path.open('a+b')
    if path.stat().st_size == 0:
        lock.write(b'1')
        lock.flush()
    lock.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise
    return lock
