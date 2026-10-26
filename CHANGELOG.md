# Histórico

## 1.1.5 — 2026-10-26

- Tutorial simples na abertura, com explicações de camadas, busca, mapa, satélite, fichas, tabela e cruzamentos.
- Explicações específicas para a versão web e para os recursos locais da instalação.
- Botão Tutorial para rever o guia e opção de não mostrar novamente neste navegador.

## Documentação — 2026-10-26

- Tutorial de uso das versões web e instalada, com passos por função, exemplos de consulta, diferenças de cobertura e solução de problemas comuns.
- Acesso ao tutorial no início do README.

## Instalador — 2026-10-22

- Preserva o caminho da base registrado no manifesto ao atualizar, em vez de voltar ao destino padrão.
- Permite vincular uma base em outra pasta com `-UseExistingLocation`, sem mover ou substituir arquivos.
- Download recomendado aponta para o instalador da release mais recente.


## 1.1.4 — 2026-10-21

- Abertura pelo executável localiza a base indicada no manifesto de instalação, mesmo sem argumentos.
- Reutiliza a sessão da mesma base, com identidade verificada e porta local estável, evitando abrir catálogos vazios em novas sessões.
- Corrige a aquisição do bloqueio antes de escrever no arquivo de trava.
- Inicia com camadas existentes de geração, transmissão e subestações selecionadas; seleção vazia de outra sessão não deixa a próxima abertura sem componentes.
- Consulta espacial usa o índice por registro, evitando percorrer milhões de registros de outras camadas para abrir o mapa.
- Evita repetir a consulta inicial do mapa enquanto a primeira resposta ainda está carregando.


## 1.1.3 — 2026-10-21

- Corrige o envio da origem da página ao OpenStreetMap, exigido para carregar o mapa de ruas, no aplicativo e na versão pública.
- Atualiza a identificação dos arquivos da interface para evitar reutilização de versões antigas pelo navegador.


## 1.1.2 — 2026-10-21

- Contatos públicos de Patrick Maximo Cordeiro na interface: GitHub, LinkedIn e e-mail.
- Links de contato no README e página dedicada em `docs/CONTATO.md`.

## 1.1.1 — 2026-10-21

- Crédito “Desenvolvido por Patrick Maximo Cordeiro” visível na interface pública e local.
- Apresentação do projeto para LinkedIn, com fontes, recursos e links documentados.

## 1.1.0 — 2026-10-21

- Linhas de transmissão coloridas pela tensão nominal em kV, com cores consistentes entre camadas EPE/ANEEL, legenda por tensão visível e classe cinza tracejada para valores ausentes.
- Nome e tensão ao passar o mouse sobre a linha; destaque de espessura sem perder a cor da tensão.
- Seletor de ruas, satélite Esri World Imagery e fundo desligado, com escolha persistida e créditos.
- Atualização da interface pública preservando o snapshot, testes de interação no navegador e novo executável compatível com o banco existente.

## 1.0.0 — 2026-10-21

- Mapa local em Python/Leaflet, acervo EPE/ANEEL/ONS e dados próprios.
- Fichas completas, origem, campos oficiais, personalização e exportação.
- Índice SQLite/RTree com leitura durante importação e substituição transacional.
- Relações por identificadores e cruzamentos espaciais com limites explícitos.
- Atualização sob demanda, reconhecimento de downloads concluídos e prévia raster IPA.
- Executável Windows e consulta pública no GitHub Pages.
- Documentação de fontes, limitações, arquitetura, operação e validação.
