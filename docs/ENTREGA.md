# Entrega e evidências — 21/10/2026

## Acessos

- Mapa publicado: https://patrick9kk.github.io/eneratlas/
- Repositório público: https://github.com/patrick9kk/eneratlas
- Distribuição Windows: https://github.com/patrick9kk/eneratlas/releases/latest

## Cobertura desta publicação

O snapshot web contém **108 camadas e 69.076 registros**, sem amostragem dentro das camadas admitidas. O catálogo completo inclui 146 camadas vetoriais/tabulares; as não admitidas na web estão identificadas. Critérios: até 12 mil registros e 32 MB de geometria integral por camada, com simplificação da geometria para consulta visual. O manifesto exato fica em `site/snapshot.json`.

O snapshot local foi indexado com **144 camadas, 1.324.499 registros e 1.155.130 registros com geometria**, incluindo as 550.189 linhas detalhadas de barragem da ANEEL. Os números não representam instalações únicas. Duas camadas da ANEEL ainda aguardavam conclusão da coleta: **Curvas de Nível** e **Divisão Munícipal (IBGE)**. O aplicativo reconhece os respectivos arquivos finais e pode incorporar essas camadas depois. Consulte `COBERTURA.json` do pacote para os números efetivamente distribuídos.

Registros sem geometria continuam disponíveis em tabela. Não foram fabricadas posições para ONS, EPE ou erros da ANEEL. O raster IPA Total é uma prévia georreferenciada separada; não entra na contagem de registros vetoriais.

## Verificações realizadas

- Oito testes automatizados passaram localmente em Windows/Python 3.14; CI Windows também passou.
- Navegador Chromium/Edge: mapa, agrupamento de marcadores, 50 registros por página, ficha real com 35 atributos originais e controles de cruzamento.
- Publicação GitHub Pages: HTTP 200 no endereço público; sem erros JavaScript na abertura, na ficha e no cruzamento por campo.
- Versão estática: leitura de JSON/GZIP, filtros e ficha sem backend Python.
- Executável Windows: inicialização do servidor empacotado, importação nativa EsriJSON em GZIP, conversão EPSG:3857 → EPSG:4326 com coordenada esperada, registro sem geometria e ficha no navegador.
- Executável: leitura e reprojeção do raster IPA oficial com GDAL/PROJ empacotados.
- Pacote: backup SQLite consistente, remoção dos caminhos locais dos controles de indexação, conferência `quick_check`, teste CRC do ZIP e SHA-256.

As imagens `docs/mapa.png` e a consulta pública permitem revisar a interface. Testes não certificam exatidão dos cadastros oficiais, adequação a engenharia, todos os ambientes Windows ou conclusão das duas coletas pendentes. As análises espaciais com geometria integral pertencem ao aplicativo local; a web oferece sobreposição e cruzamento explícito por campo.
