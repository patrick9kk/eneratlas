"""Teste de interação real (opcional: pip install playwright; usa Edge no Windows)."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:8769')
    parser.add_argument('--screenshot',type=Path)
    args=parser.parse_args()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
        page=browser.new_page(viewport={'width':1500,'height':950})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(args.url,wait_until='networkidle')
        page.wait_for_function('() => layers.length>0 && group.getLayers().length>0')
        assert page.evaluate("EnerTransmission.parse('230,0 kV')")=='230'
        assert page.evaluate('EnerTransmission.parse(0)') is None
        assert page.evaluate("EnerTransmission.color(EnerTransmission.parse('500.0'))===EnerTransmission.color('500')")
        assert page.evaluate("EnerTransmission.color('230')!==EnerTransmission.color('500')")
        page.evaluate("active=new Set(layers.filter(l=>l.source==='EPE'&&l.name.includes('Transmissão')).map(l=>l.id));renderLayers();refresh()")
        page.wait_for_function('() => visibleVoltages.length>=3')
        page.wait_for_timeout(250)
        styles=page.evaluate("visibleVoltages.map(v=>({key:v.key,color:v.color}))")
        assert len({v['color'] for v in styles})==len(styles)
        point=page.evaluate('''() => {
          const size=map.getSize();
          for(const collection of group.getLayers())for(const line of collection.getLayers())for(const part of line._parts||[])for(let i=1;i<part.length;i++){
            const q=map.layerPointToContainerPoint(L.point((part[i-1].x+part[i].x)/2,(part[i-1].y+part[i].y)/2)),x=q.x,y=q.y;
            if(x>100&&x<size.x-30&&y>180&&y<size.y-120){const r=document.getElementById('map').getBoundingClientRect();if(document.elementFromPoint(r.x+x,r.y+y)?.tagName==='CANVAS')return {x:r.x+x,y:r.y+y}}
          }return null;
        }''')
        assert point,'Nenhum segmento visível para testar o mouse'
        page.mouse.move(point['x'],point['y'])
        page.locator('.leaflet-tooltip').wait_for(state='visible')
        tooltip=page.locator('.leaflet-tooltip').inner_text()
        assert 'kV' in tooltip and len(tooltip.splitlines()[0])>3
        page.locator('#basemap-select').select_option('satellite')
        page.wait_for_function("() => [...document.querySelectorAll('img.leaflet-tile')].some(i=>i.src.includes('World_Imagery')&&i.complete&&i.naturalWidth>0)",timeout=30000)
        assert page.evaluate('map.hasLayer(satellite)&&!map.hasLayer(tiles)')
        if args.screenshot:
            args.screenshot.parent.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(args.screenshot),full_page=True)
        page.reload(wait_until='networkidle')
        assert page.locator('#basemap-select').input_value()=='satellite'
        page.locator('#basemap-select').select_option('none')
        assert page.evaluate('!map.hasLayer(satellite)&&!map.hasLayer(tiles)')
        assert not errors,errors
        print(json.dumps({'url':args.url,'voltage_styles':styles,'hover':tooltip,'satellite':'loaded','persistence':'passed','javascript_errors':errors},ensure_ascii=True))
        browser.close()


if __name__=='__main__':main()
