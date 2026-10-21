# Validação

Execute `python -m pytest -q` na raiz. A suíte usa dados sintéticos, não depende dos portais oficiais e verifica comportamentos:

- CRS projetado para WGS84 e rejeição de CRS ausente.
- Anéis Esri multipartes, buracos e ilhas.
- Correção topológica sinalizada e coordenadas fora dos limites rejeitadas.
- Importação idempotente, contagens e rollback de substituição corrompida.
- JSON em GZIP com múltiplos membros e geometria ausente.
- Busca sem acentos, ficha, aliases, vínculos por identificador e exportação.
- Cruzamento espacial com distância conhecida e validação de raio.
- Rejeição de Host/Origin externo e mutação sem token.
- CSV próprio com coordenadas explícitas e proveniência.

O workflow de CI executa os testes em Windows/Python 3.14. Publicação no Pages ocorre em um workflow separado, com permissões limitadas à implantação do site.

Testes de navegador verificam mapa, consulta, ficha, personalização e versão pública, e são registrados no relatório da entrega. As contagens reais variam enquanto novos downloads são concluídos. Consulte `COBERTURA.json` do pacote e `site/snapshot.json` da publicação; totais não são instalações únicas, pois fontes e camadas podem se sobrepor.

O executável é validado iniciando o servidor empacotado, consultando endpoints e abrindo a interface. Isso demonstra funcionamento neste Windows x64; não equivale a certificação de todas as versões do Windows ou a validação cadastral/engenharia dos dados oficiais.
