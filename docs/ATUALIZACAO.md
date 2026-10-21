# Atualização e operação

## Reabrir bases já baixadas

O EnerAtlas reconhece estas estruturas:

```text
BasesEnergia/
  webmapepe/
    inventario.json
    camadas/<serviço>/<camada>/metadados.json
    camadas/<serviço>/<camada>/dados.geojson
  aneel_ons/
    inventario_aneel*.json
    aneel/camadas/<serviço>/<camada>/metadados.json
    aneel/camadas/<serviço>/<camada>/dados.geojson
    aneel/camadas/<serviço>/<camada>/dados.esrijson.gz
    ons/arquivos/LINHA_TRANSMISSAO.csv
```

Adicione `BasesEnergia` em **Fontes & dados**. O importador também reconhece `resultado_coleta.json` por camada e GZIP com múltiplos membros, utilizado pela coleta retomável. Não é necessário descompactar integralmente os JSON grandes. Downloads incompletos ficam no catálogo aguardando conclusão.

**Sincronizar** só indexa os arquivos locais. Não inicia download pela internet. A descoberta se repete a cada dois minutos; a assinatura evita reprocessar arquivos idênticos. Uma camada anteriormente disponível é preservada no banco se sua pasta original não estiver presente. Para limpar um acervo, use uma nova pasta `--data-dir`, preservando a anterior como backup.

## Recoletar fontes oficiais

Marque as camadas desejadas, abra **Fontes & dados** e use **Atualizar camadas marcadas**. O botão atualiza as camadas cadastradas EPE/ANEEL pela URL ArcGIS e o CSV ONS pelo catálogo CKAN. Não descobre automaticamente novos serviços que ainda não estão no catálogo. Para adicionar uma nova camada de outro serviço, obtenha um GeoJSON/CSV público, documente a fonte e importe o arquivo; um novo adaptador também pode ser implementado.

O download usa `where=1=1`, obtém IDs e contagem e divide lotes quando o serviço limita a resposta. Se uma geometria isolada falhar, tenta recuperar atributos e registra a ausência. A camada não é anunciada como geometricamente completa nesse caso. A atualização fica em `data/managed`, separada da pasta original. Interromper o aplicativo pode deixar checkpoints; uma tentativa posterior pode precisar repetir a camada, e o índice anterior continua disponível.

O banco não faz união ou substituição de registros entre fontes distintas. CNPJ identifica agentes; nomes podem se repetir. ObjectID não é usado como identificador global. Vínculos de engenharia exigem conferência dos campos, versões e datas das bases.

## Arquivos próprios

GeoJSON: FeatureCollection em EPSG:4326, propriedades originais preservadas. CSV: UTF-8 com vírgula ou ponto e vírgula; campos de longitude/latitude são opcionais e precisam ser informados explicitamente. Valores decimais das coordenadas podem usar ponto ou vírgula em campos corretamente delimitados. Registros sem coordenadas permanecem tabelas.

Informe nome, URL e descrição da origem, licença e data. A URL é referência documental, não código executável. A reimportação com o mesmo nome substitui o snapshot dessa camada, por transação. Use nomes distintos para manter versões lado a lado.

## Publicar nova versão web

1. Finalize a sincronização local e verifique os erros no log.
2. Rode `python scripts/export_site.py --database data/eneratlas.db --output site`.
3. Confira `site/snapshot.json` e o catálogo. Teste o site servido por HTTP, não `file://`.
4. Faça commit e push. O workflow Pages publica `site/` automaticamente, sem executar Python no navegador.

O exportador publica todas as linhas de camadas com até 12 mil registros, simplifica a geometria de tela e grava blocos comprimidos de mil registros. Limites estão no próprio manifesto. Camadas maiores continuam listadas com indicação de uso no aplicativo completo. Metadados e dados publicados devem ter origem documentada; nunca inclua dados próprios confidenciais em um snapshot público.

## Build Windows e backup

`python scripts/build_windows.py` cria um executável em `dist/EnerAtlas.exe`. O script é específico de Windows e usa PyInstaller com assets locais e dependências de projeção/raster. O resultado não exige Python instalado. O servidor nunca escuta em `0.0.0.0`.

Feche o aplicativo antes de copiar manualmente `eneratlas.db`; alternativamente use a API de backup do SQLite para obter um snapshot consistente durante leitura. Não copie apenas o arquivo `.db` enquanto há uma transação WAL ativa.

O log fica em `data/eneratlas.log`. Erros de fonte não devem ser tratados como ausência de infraestrutura. Se o índice falhar, preserve os arquivos originais e leia o erro do importador antes de repetir a coleta.
