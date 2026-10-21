"""Atualiza a interface pública preservando o snapshot de dados publicado."""
import shutil
from pathlib import Path


def sync():
    root=Path(__file__).resolve().parents[1]
    target=root/'site'
    target.mkdir(exist_ok=True)
    shutil.copytree(root/'static',target/'static',dirs_exist_ok=True)
    html=(root/'templates/index.html').read_text(encoding='utf-8').replace('="/static/','="./static/')
    (target/'index.html').write_text(html,encoding='utf-8')


if __name__=='__main__':sync()
