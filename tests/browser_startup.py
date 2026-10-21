"""Validacao opcional da abertura com base e componentes no navegador real."""
import argparse
import json
from pathlib import Path
import time

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8769')
    parser.add_argument('--screenshot', type=Path)
    args = parser.parse_args()
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless=True)
        page = browser.new_page(viewport={'width':1500,'height':950})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        # Uma selecao vazia da sessao anterior nao deve abrir o mapa vazio.
        page.add_init_script("localStorage.setItem('eneratlas.layers','[]')")
        start = time.monotonic()
        page.goto(args.url, wait_until='domcontentloaded')
        page.wait_for_function("() => layers.length>0 && active.size>0 && /componentes nesta vista/.test(document.getElementById('visible-count').textContent)", timeout=20000)
        result = page.evaluate("({layers:layers.length,active:active.size,visible:document.getElementById('visible-count').textContent,records:document.getElementById('total-records').textContent})")
        result['seconds'] = round(time.monotonic() - start, 2)
        assert result['records'] != '0'
        assert page.evaluate('group.getLayers().length+clusters.getLayers().length') > 0
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(args.screenshot))
        assert not errors, errors
        print(json.dumps(result, ensure_ascii=True))
        browser.close()


if __name__ == '__main__':
    main()
