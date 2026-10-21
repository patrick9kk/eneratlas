"""Prévia georreferenciada do raster oficial IPA; sem criar vetores artificiais."""
import json
import logging
from pathlib import Path


def prepare_rasters(roots, data_dir):
    target = Path(data_dir) / 'rasters'
    target.mkdir(parents=True, exist_ok=True)
    catalog = []
    try:
        import numpy as np
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.warp import calculate_default_transform, reproject, transform_bounds
        from PIL import Image
        for root in roots:
            root = Path(root)
            folder = root if root.name == 'webmapepe' else root/'webmapepe'
            path = folder/'rasters_IPA_oficial.zip'
            if not path.exists():
                continue
            uri = 'zip://' + path.resolve().as_posix() + '!zipfolder/IPA_Total.tif'
            with rasterio.open(uri) as src:
                if src.crs is None:
                    raise ValueError('Raster IPA sem CRS declarado')
                bounds = transform_bounds(src.crs,'EPSG:4326',*src.bounds)
                crs, width, height = calculate_default_transform(src.crs,'EPSG:4326',src.width,src.height,*src.bounds)
                scale = min(1, 2048/max(width,height))
                out_width,out_height = max(1,int(width*scale)),max(1,int(height*scale))
                affine = crs * crs.scale(width/out_width,height/out_height)
                raster = np.full((out_height,out_width),np.nan,dtype='float32')
                reproject(source=rasterio.band(src,1),destination=raster,src_transform=src.transform,src_crs=src.crs,dst_transform=affine,dst_crs='EPSG:4326',src_nodata=src.nodata,dst_nodata=np.nan,resampling=Resampling.nearest)
                valid = np.isfinite(raster)
                lo,hi = float(np.nanmin(raster)),float(np.nanmax(raster))
                t = np.nan_to_num((raster-lo)/max(hi-lo,1))
                rgba = np.zeros((*raster.shape,4),dtype='uint8')
                rgba[:,:,0] = 240-125*t
                rgba[:,:,1] = 218-155*t
                rgba[:,:,2] = 154-112*t
                rgba[:,:,3] = valid.astype('uint8')*200
                Image.fromarray(rgba).save(target/'ipa_total.png')
                catalog = [{'id':'ipa_total','name':'IPA Total — intensidade exploratória','source':'EPE','url':'/raster/ipa_total.png','bounds':[[bounds[1],bounds[0]],[bounds[3],bounds[2]]],'min':lo,'max':hi,'crs':str(src.crs),'description':'Prévia raster oficial reprojetada para visualização, com rampa sequencial. Não representa potência instalada; valores e unidade devem ser conferidos na documentação IPA/EPE. Resolução de tela limitada a 2048 pixels.'}]
            break
    except Exception:
        logging.exception('Prévia raster indisponível')
    (target/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False),encoding='utf-8')
    return catalog
