# Onde encontrar os dados atualizados de cada base

Este é o guia de referência para obter novas versões dos dados do EnerAtlas. **Busque as versões atuais nos portais oficiais abaixo.** Os arquivos em GitHub Pages e nas releases são snapshots: correspondem à data de sua publicação e não se tornam atuais apenas por abrir ou recarregar o mapa.

Endereços e metadados principais conferidos em **21/10/2026**. A disponibilidade e os caminhos podem mudar; se um link direto deixar de funcionar, comece pelo portal da instituição.

## Acesso rápido

| Base | Onde encontrar a versão publicada pela instituição | O que procurar |
|---|---|---|
| **EPE** | [WebMapEPE](https://gisepeprd2.epe.gov.br/webmapepe/) | Geração, linhas de transmissão, subestações, planejamento e recursos energéticos. |
| **ANEEL** | [SIGEL — mapa oficial](https://sigel.aneel.gov.br/portal/apps/webappviewer/index.html?id=c1716d81d491426197bf497ace41db8d) | Empreendimentos, componentes, reservatórios e áreas especiais. |
| **ONS** | [Linhas de Transmissão da Rede de Operação](https://dados.ons.org.br/dataset/linha-transmissao) | CSV, XLSX, Parquet e dicionários de dados do cadastro de linhas. |

## 1. EPE — WebMapEPE

**Portal:** [abrir o WebMapEPE](https://gisepeprd2.epe.gov.br/webmapepe/).

Encontre a camada desejada no mapa e consulte os metadados e as opções de download/exportação disponibilizadas pela EPE. Não confunda a camada de infraestrutura existente com a expansão planejada: ambas devem conservar sua identificação no EnerAtlas.

**Catálogo técnico:** [serviços ArcGIS da pasta SMA](https://gisepeprd2.epe.gov.br/arcgis/rest/services/SMA).

Atalhos das camadas de transmissão utilizadas no projeto:

| Camada | Serviço oficial |
|---|---|
| Linhas de transmissão existentes | [Sistema Elétrico Existente — camada 9](https://gisepeprd2.epe.gov.br/arcgis/rest/services/SMA/Webmap_EPE_Sistema_Eletrico_Existente/MapServer/9) |
| Subestações existentes | [Sistema Elétrico Existente — camada 8](https://gisepeprd2.epe.gov.br/arcgis/rest/services/SMA/Webmap_EPE_Sistema_Eletrico_Existente/MapServer/8) |
| Linhas de transmissão planejadas | [Sistema Elétrico Planejado — camada 9](https://gisepeprd2.epe.gov.br/arcgis/rest/services/SMA/Webmap_EPE_Sistema_Eletrico_Planejado/MapServer/9) |
| Subestações planejadas | [Sistema Elétrico Planejado — camada 8](https://gisepeprd2.epe.gov.br/arcgis/rest/services/SMA/Webmap_EPE_Sistema_Eletrico_Planejado/MapServer/8) |

Para outras camadas, use o catálogo SMA e o link da fonte na ficha técnica do EnerAtlas. Os metadados retornam em JSON acrescentando `?f=pjson` à URL da camada. Consulte descrição, campos, CRS, limites de consulta e datas disponibilizadas. Não se presume uma periodicidade única de atualização para todas as camadas da EPE.

## 2. ANEEL — SIGEL

**Portal:** [abrir o SIGEL](https://sigel.aneel.gov.br/portal/apps/webappviewer/index.html?id=c1716d81d491426197bf497ace41db8d).

Para consultar as fontes técnicas e os identificadores das camadas:

| Serviço | Conteúdo |
|---|---|
| [Camadas_Downloads — FeatureServer](https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Camadas_Downloads/FeatureServer) | Empreendimentos, aerogeradores, distribuição e reservatórios, conforme o catálogo vigente. |
| [Camadas_SIPH — FeatureServer](https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/Camadas_SIPH/FeatureServer) | Curvas de nível, barragens, canais, eixos, linhas, subestações e outros componentes de aproveitamentos hidrelétricos. |
| [Áreas_Especiais — MapServer](https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/%C3%81reas_Especiais/MapServer) | Camadas territoriais e ambientais publicadas no SIGEL; confira também a instituição responsável em cada metadado. |
| [DUP — MapServer](https://sigel.aneel.gov.br/arcgis/rest/services/PORTAL/DUP/MapServer) | Declarações de utilidade pública, conforme as camadas publicadas. |

Abra o serviço e selecione a camada pelo nome e ID. Use `?f=pjson` para ler os metadados. Quando presentes, confira as datas de edição do serviço e os campos de atualização do próprio registro; eles podem representar referências diferentes. Não se presume que todas as camadas estejam atualizadas na mesma data.

Camadas volumosas exigem download em lotes. Uma resposta isolada da operação `query` pode conter apenas parte dos registros devido ao limite do serviço. O coletor do EnerAtlas verifica IDs e contagem; não trate uma única resposta limitada como a base completa. Falha de geometria deve ser registrada, sem inventar coordenadas nem apagar os atributos recuperados.

## 3. ONS — linhas de transmissão

**Página principal:** [Linhas de Transmissão da Rede de Operação](https://dados.ons.org.br/dataset/linha-transmissao).

Na seção **Dados e recursos**, escolha o formato desejado e confira a descrição, a última atualização e o dicionário. O portal informa atualização diária. Não há histórico de versões neste conjunto; arquive suas próprias coletas se precisar comparar períodos.

**API para descobrir os recursos atuais:** [catálogo CKAN do conjunto](https://dados.ons.org.br/api/3/action/package_show?id=linha-transmissao).

Leia `result.resources` e escolha o recurso pelo campo `format` — por exemplo, `CSV`. Use o endereço retornado em `url`; consulte `last_modified` quando informado. Essa descoberta é preferível a manter um endereço fixo se o ONS reorganizar seus arquivos.

Atalhos encontrados no catálogo durante a conferência:

- [CSV — LINHA_TRANSMISSAO.csv](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.csv)
- [Excel — LINHA_TRANSMISSAO.xlsx](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.xlsx)
- [Parquet — LINHA_TRANSMISSAO.parquet](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/LINHA_TRANSMISSAO.parquet)
- [Dicionário de dados em PDF](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/DicionarioDados_Linha_Transmissao.pdf)
- [Dicionário de dados em JSON](https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/linha_transmissao/DicionarioDados_Linha_Transmissao.json)

O CSV é UTF-8, delimitado por ponto e vírgula. Esse cadastro não fornece os traçados geográficos usados no mapa; ele permanece consultável em tabela. Não gere linhas a partir dos nomes dos terminais. Preserve a atribuição ao ONS e consulte a licença CC-BY indicada no portal.

## 4. Como incorporar as versões novas no EnerAtlas

### Pelo aplicativo Windows

1. Abra o aplicativo e marque as camadas oficiais que deseja atualizar.
2. Acesse **Fontes & dados → Atualizar camadas marcadas**. A operação consulta a URL ArcGIS cadastrada de cada camada EPE/ANEEL e descobre o CSV ONS pelo catálogo CKAN.
3. Aguarde o download e a indexação. Confira erros, contagens, disponibilidade de geometria e a ficha da camada. A data de indexação indica quando o arquivo foi processado, não quando a instituição atualizou os dados.
4. Para arquivos já baixados, use **Adicionar pasta** e **Sincronizar**. Esse caminho lê os arquivos locais; não busca novas versões pela internet.
5. Para uma nova camada que ainda não está cadastrada, use **Importar camada** com GeoJSON WGS84 ou CSV UTF-8 e registre URL, licença e data. Arquivos em outros formatos precisam ser convertidos antes da importação.

O botão de atualização não descobre automaticamente serviços novos nem substitui URLs de serviços desativados. Nesses casos, consulte o portal oficial, documente o novo endereço e adapte o cadastro/coletor. Veja [Atualização e operação](ATUALIZACAO.md).

### Para atualizar o mapa público

Depois de baixar e indexar os arquivos no aplicativo local:

```powershell
python scripts/export_site.py --database data/eneratlas.db --output site
git add site
git commit -m "Atualiza snapshot das bases oficiais"
git push
```

Confira antes `site/snapshot.json`, a cobertura e os limites da versão online. O workflow publica o snapshot após o push. Somente alterar a interface ou recarregar a página **não** atualiza o conteúdo das bases.

## 5. Fundos de ruas e satélite

OpenStreetMap e Esri World Imagery são fundos consultados pela interface conforme a opção escolhida. Não são cadastros de projetos e não substituem EPE, ANEEL ou ONS. A atualização das imagens depende de seus provedores e varia por local; não é uma imagem em tempo real. Referências, créditos e condições de uso estão em [Fontes e licenças](FONTES.md).

## O que registrar em cada nova coleta

Registre a instituição, URL do portal e do recurso/camada, ID da camada, data e hora de obtenção, data de atualização informada pela fonte, licença, CRS, contagem de registros e limitações ou falhas. Preserve os arquivos originais. Datas ausentes devem permanecer como não informadas; nunca substitua uma data de atualização ausente pela data do download.
