# Arquitetura

## Fluxo local

`Fontes oficiais / arquivos próprios → adaptadores → arquivos completos → transação por camada → SQLite + RTree → API loopback → Leaflet`

`launch.py` inicia um servidor Waitress restrito a `127.0.0.1`, abre o navegador e coordena sincronização. Duas instâncias não indexam a mesma pasta: bloqueio de arquivo é mantido pelo sistema operacional. Uma segunda abertura reaproveita o endereço da instância existente.

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `catalog.py` | Descobrir bases e manifestos, ler streaming JSON/GZIP/CSV, preservar atributos, indexar transacionalmente. |
| `geometry.py` | EsriJSON para Shapely, anéis com buracos e ilhas, CRS explícito, classificação de componentes e medidas geodésicas. |
| `store.py` | Esquema SQLite e RTree, modo WAL para leitura durante escrita. |
| `server.py` | Filtros, paginação, fichas, vínculos, análises, exportações e operações locais. |
| `updater.py` | Recoletar camadas selecionadas, validar resultados e expor apenas snapshots concluídos. |
| `vendor/arcgis.py` | Coletor da coleta original, versionado junto ao aplicativo; consultas adaptativas, IDs, contagem e retomada. |
| `raster.py` | Prévia raster IPA em WGS84; não usa seus pixels para simular geometria de projetos. |
| `static/app.js` | Interface comum, mapas, ícones SVG, agrupamento visual, ficha e cruzamento. |
| `static/online-api.js` | Adaptador de consulta estática para GitHub Pages; não executa análises que exigem geometria integral. |
| `scripts/export_site.py` | Snapshot web em blocos JSON/GZIP com catálogo e cobertura explícita. |

## Persistência

- `layers`: origem, URL, metadados oficiais completos, estilo padrão, estado, assinatura do arquivo, contagens, problemas de geometria e data de indexação.
- `features`: atributos JSON integrais, nome e campos de busca derivados, UF/situação quando reconhecidos, WKB WGS84, observação e envelope.
- `spatial`: RTree de envelopes dos registros com geometria.
- `identifiers`: chaves normalizadas de CEG, CNPJ, código ONS e IDs internos da ANEEL, com namespace da fonte para evitar colisões indevidas.
- `data/managed/`: atualizações e arquivos próprios com `layer.json` contendo proveniência.
- `data/rasters/`: prévias PNG e catálogo georreferenciado.
- `sources.local.json`, `runtime.json`, logs e estado de importação são exclusivamente locais e ficam fora do Git.

Arquivos temporários e downloads não concluídos não são indexados. A substituição ocorre numa transação por camada. Erro de parsing ou divergência de contagem provoca rollback, preservando o índice anterior. Assinatura usa caminho, tamanho, data de modificação e metadados; não substitui um hash de integridade. Os pacotes distribuídos recebem SHA-256.

GeoJSON é interpretado conforme RFC 7946, longitude/latitude WGS84. EsriJSON requer `wkid`, `latestWkid` ou WKT nos metadados. Coordenadas Z/M originais ficam nos arquivos de coleta; análises espaciais são 2D. Medidas não incorporam relevo, altitude ou distância de circuito elétrico.

## Limites e desempenho

A importação lê um registro por vez; um registro individual muito complexo ainda pode consumir memória. Escrita WAL permite consultar camadas já concluídas durante o processamento de outras. Camadas de terreno e grandes bases administrativas são processadas depois da infraestrutura essencial.

Mapa simplifica somente para renderização e usa até 1.800 componentes, com aviso. Grupos de marcadores são apenas agregação visual: não modificam os projetos. Análises consultam envelopes no RTree e aplicam predicados na geometria integral. O limite de 5.000 candidatos é declarado na resposta e na interface; resultados parciais não são completos.

UF e situação são derivados de campos reconhecidos e podem ficar vazios. Filtro de UF usa o campo administrativo declarado, não atribuição espacial. Para polígonos, “dentro” usa `covers`, incluindo bordas. Interseção também inclui toque de borda. Distância é a menor distância 2D entre geometrias na projeção local.

## Segurança local e publicação

Servidor loopback, Host/Origin validados, mutações com token por sessão, CSP e queries parametrizadas. Nenhum shell é executado por dados enviados pela interface. Uploads aceitam somente CSV/JSON/GeoJSON e têm limite de 256 MB; pastas locais podem conter fontes maiores. O serviço foi concebido para uso pessoal local, não deve ser exposto em uma rede.

GitHub Pages publica apenas arquivos estáticos versionados. Não existe backend remoto, autenticação nem upload público. As bases grandes locais, credenciais e configurações particulares não são commitadas. O executável usa o mesmo código Python e inclui suas dependências; o navegador é apenas a interface.
