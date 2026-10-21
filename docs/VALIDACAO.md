# Validação

Execute `python -m pytest -q` na raiz. A suíte usa dados sintéticos, não depende dos portais oficiais e verifica comportamentos:

- Preservação da prévia raster portátil sem o arquivo original.
- CRS projetado para WGS84 e rejeição de CRS ausente.
- Anéis Esri multipartes, buracos e ilhas.
- Correção topológica sinalizada e coordenadas fora dos limites rejeitadas.
- Importação idempotente, contagens e rollback de substituição corrompida.
- JSON em GZIP com múltiplos membros e geometria ausente.
- Busca sem acentos, ficha, aliases, vínculos por identificador e exportação.
- Cruzamento espacial com distância conhecida e validação de raio.
- Rejeição de Host/Origin externo e mutação sem token.
- CSV próprio com coordenadas explícitas e proveniência.
- Cruzamento explícito por campo sem atribuir geometria e com proteção contra injeção no caminho JSON.

O workflow de CI executa os testes em Windows/Python 3.14. Publicação no Pages ocorre em um workflow separado, com permissões limitadas à implantação do site.

Testes de navegador verificam mapa, consulta, ficha, personalização e versão pública, e são registrados no relatório da entrega. As contagens reais variam enquanto novos downloads são concluídos. Consulte `COBERTURA.json` do pacote e `site/snapshot.json` da publicação; totais não são instalações únicas, pois fontes e camadas podem se sobrepor.

O executável é validado iniciando o servidor empacotado, consultando endpoints e abrindo a interface. Isso demonstra funcionamento neste Windows x64; não equivale a certificação de todas as versões do Windows ou a validação cadastral/engenharia dos dados oficiais.

## Versão 1.1.0

Dez testes automatizados passaram. O teste opcional `tests/browser_visuals.py` usa Playwright com Edge no Windows e verifica cores distintas para tensões reais visíveis, normalização de valores como `500` e `500.0`, ausência de tensão, mouse real sobre uma linha, nome/kV, carregamento dos mosaicos de satélite, persistência e fundo desligado. Executado localmente e na URL pública sem erros JavaScript.

```powershell
python -m pip install playwright
python tests/browser_visuals.py --url https://patrick9kk.github.io/eneratlas/
```

Campos reconhecidos incluem `Tensao`, `TENSAO_KV` e `val_niveltensao_kv`; potência em MW/MVA não é usada como tensão. Valores ausentes ou zero recebem cinza tracejado. A legenda descreve as classes presentes nos componentes exibidos na vista atual.
