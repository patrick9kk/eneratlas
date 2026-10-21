# Fontes, proveniência e licenças

**Para obter versões novas:** [guia com os endereços oficiais e o procedimento por base](ONDE_ATUALIZAR_AS_BASES.md).

Inventário inicial em 21/10/2026. As datas de atualização dos registros oficiais variam; a data de indexação do aplicativo não é a data de validade do dado.

| Fonte | Endereço | Uso e atualização |
|---|---|---|
| EPE / WebMapEPE | https://gisepeprd2.epe.gov.br/webmapepe/ | Camadas públicas ArcGIS; metadados, aliases, contagens e IDs preservados pela coleta. Atualização sob demanda pela URL de cada camada. |
| ANEEL / SIGEL | https://sigel.aneel.gov.br/portal/apps/webappviewer/index.html?id=c1716d81d491426197bf497ace41db8d | Camadas públicas de empreendimentos, componentes SIPH e áreas especiais. Algumas geometrias retornam erro na origem; atributos são preservados e a ausência é registrada. |
| ONS / Linha de Transmissão | https://dados.ons.org.br/dataset/linha-transmissao | CSV oficial sem geometria, consultado como tabela. A API CKAN informa recursos, descrição, licença e datas. |
| ONS / catálogo CKAN | https://dados.ons.org.br/api/3/action/package_show?id=linha-transmissao | Descoberta do CSV atualizado e registro da resposta de proveniência. O catálogo da coleta original declara CC-BY. Observe a versão e os termos retornados pelo catálogo atual. |
| Esri / World Imagery | https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer | Imagens de satélite/aéreas sob demanda; créditos atuais do serviço: Esri, Vantor, Earthstar Geographics e GIS User Community. Termos dos provedores preservados. Não redistribuímos os mosaicos nem realizamos cache em massa. |
| OpenStreetMap | https://www.openstreetmap.org/copyright | Fundo cartográfico via mosaicos públicos; atribuição na tela. ODbL. Internet necessária para o fundo, sem coleta em massa. |

Os endereços individuais das camadas EPE e ANEEL constam na ficha e no catálogo do snapshot. A interface nunca oculta a fonte por trás de uma ficha consolidada. Bases EPE e ANEEL são republicadas com atribuição, para consulta pública dos dados disponibilizados; não se atribui a elas a licença MIT do código. Consulte os termos e metadados das instituições antes de reutilizar comercialmente ou redistribuir um novo conjunto. O snapshot mantém atributos oficiais e geometrias derivadas para consulta, sem afirmar titularidade sobre as bases.

## Bibliotecas e referências primárias

- Python / Flask: https://flask.palletsprojects.com/en/stable/
- Waitress: https://docs.pylonsproject.org/projects/waitress/en/stable/
- Leaflet 1.9.4: https://leafletjs.com/reference.html — BSD-2-Clause, licença distribuída em `static/vendor/LEAFLET-LICENSE.txt`.
- Leaflet.markercluster 1.5.3: https://github.com/Leaflet/Leaflet.markercluster — MIT, licença distribuída em `static/vendor/MARKERCLUSTER-LICENSE.txt`.
- Shapely: https://shapely.readthedocs.io/en/stable/ — análise de geometrias; GEOS.
- pyproj: https://pyproj4.github.io/pyproj/stable/ — transformações explícitas de CRS; PROJ.
- Rasterio: https://rasterio.readthedocs.io/en/stable/ — leitura e reprojeção do IPA Total; GDAL.
- PyInstaller: https://pyinstaller.org/en/stable/usage.html — empacotamento Windows.

Dependências diretas têm versões fixadas nos arquivos de requisitos. O build gera `DEPENDENCIAS.txt` com todas as versões resolvidas e copia os avisos de bibliotecas do empacotamento. Os vetores SVG dos componentes e a marca EnerAtlas fazem parte do código MIT.

## Novas fontes

Para cada nova fonte, registre entidade responsável, URL original, URL do recurso, licença/termos, data da obtenção, cobertura, CRS, unidades, identificadores e limitações. A importação própria inclui campos para URL e descrição, armazenados no manifesto local. Nunca deduza que coordenadas sem CRS são WGS84; o importador nativo rejeita essa ambiguidade. CSV só recebe geometria se o usuário informar explicitamente as colunas de longitude e latitude em graus WGS84.

O aplicativo não consulta geocodificação externa, não busca imagens de empreendimentos e não envia dados locais às fontes. O fundo de ruas solicita mosaicos OSM; a opção Satélite solicita imagens do serviço Esri World Imagery. A escolha de fundo é salva no navegador. Imagens têm resolução e datas variáveis por local; não são em tempo real. O modo Sem mapa de fundo dispensa essas requisições. requisições aos provedores de dados acontecem quando a atualização é solicitada.

## Referência do fundo de satélite

Serviço e créditos: https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer?f=pjson . Orientação oficial de atribuição: https://support.esri.com/en-us/knowledge-base/what-is-the-correct-way-to-cite-an-arcgis-online-basema-000012040 . Endpoint e mosaico de teste verificados via HTTP 200 em 21/10/2026. As imagens ficam somente como fundo visual, sem alterar os dados das linhas.
