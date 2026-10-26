"""Valida o guia no aplicativo real e no site estático, com navegador Edge."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def wait_http(url):
    for _ in range(100):
        try:
            with urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(.1)
    raise RuntimeError('Servidor de teste indisponível: ' + url)


def main():
    local_port, web_port = free_port(), free_port()
    processes = []
    with tempfile.TemporaryDirectory(prefix='eneratlas-tutorial-') as data:
        try:
            options = dict(cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            processes.append(subprocess.Popen([sys.executable, 'launch.py', '--data-dir', data,
                '--no-autodiscover', '--no-browser', '--port', str(local_port)], **options))
            processes.append(subprocess.Popen([sys.executable, '-m', 'http.server', str(web_port),
                '--bind', '127.0.0.1', '--directory', 'site'], **options))
            with sync_playwright() as p:
                browser = p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless=True)
                for online, port, count in [(False, local_port, 6), (True, web_port, 5)]:
                    url = f'http://127.0.0.1:{port}/' + ('?online' if online else '')
                    wait_http(url)
                    page = browser.new_page(viewport={'width':1500, 'height':950})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(url, wait_until='domcontentloaded')
                    expect(page.locator('#welcome-dialog')).to_be_visible()
                    expect(page.locator('#welcome-previous')).to_be_disabled()
                    page.locator('#welcome-next').click()
                    expect(page.locator('#welcome-title')).to_have_text('Camadas e busca')
                    page.locator('#welcome-previous').click()
                    expect(page.locator('#welcome-title')).to_have_text('Bem-vindo ao EnerAtlas')
                    for _ in range(count - 1):
                        page.locator('#welcome-next').click()
                    expect(page.locator('#welcome-progress')).to_have_text(f'{count} de {count}')
                    if online:
                        expect(page.locator('#welcome-description')).to_contain_text('aplicativo instalado')
                    else:
                        expect(page.locator('#welcome-title')).to_have_text('Suas bases e atualizações')
                    page.locator('#welcome-next').click()
                    expect(page.locator('#welcome-dialog')).not_to_be_visible()
                    # Sem optar por ocultar, o tutorial aparece na próxima abertura.
                    page.reload(wait_until='domcontentloaded')
                    expect(page.locator('#welcome-dialog')).to_be_visible()
                    page.locator('#welcome-hide').check()
                    page.locator('#welcome-close').click()
                    page.reload(wait_until='domcontentloaded')
                    expect(page.locator('#open-tutorial')).to_be_visible()
                    expect(page.locator('#welcome-dialog')).not_to_be_visible()
                    page.locator('#open-tutorial').click()
                    expect(page.locator('#welcome-title')).to_have_text('Bem-vindo ao EnerAtlas')
                    page.keyboard.press('Escape')
                    expect(page.locator('#welcome-dialog')).not_to_be_visible()
                    page.set_viewport_size({'width':390, 'height':740})
                    page.locator('#open-tutorial').click()
                    box = page.locator('#welcome-dialog').bounding_box()
                    assert box['x'] >= 0 and box['x'] + box['width'] <= 390
                    assert box['y'] >= 0 and box['y'] + box['height'] <= 740
                    assert not errors, errors
                    page.close()
                    print(('Web' if online else 'Instalado') + ': navegação, preferência, reabertura, teclado e tela pequena OK')
                browser.close()
        finally:
            for process in processes:
                process.terminate()
                process.wait(timeout=15)


if __name__ == '__main__':
    main()
