# Tutorial do EnerAtlas — versão web e aplicativo instalado

**Desenvolvido por Patrick Maximo Cordeiro.**

Guia baseado nas funções da versão 1.1.4. Documentação revisada em 26/10/2026.

O EnerAtlas permite explorar a infraestrutura energética brasileira, consultar fichas técnicas e relacionar dados da EPE, ANEEL, ONS e arquivos próprios. Este tutorial acompanha os nomes dos botões da interface.

## 1. Escolha como usar

| O que deseja fazer | Versão web | Aplicativo instalado |
|---|---|---|
| Consultar mapa, filtros, tabela e fichas | Sim, nas camadas publicadas | Sim, nas bases instaladas |
| Ver satélite, nomes de linhas e cores por tensão | Sim | Sim |
| Personalizar ícones e cores | Sim | Sim |
| Cruzar campos de duas camadas | Sim, nas camadas disponíveis online | Sim |
| Buscar proximidade, interseção e elementos dentro de um projeto | Não | Sim |
| Importar arquivos e atualizar fontes oficiais | Não | Sim |
| Usar sem internet | Não conte com acesso offline | Sim, com dados instalados e fundo desligado |

**Web:** abra o [mapa público](https://patrick9kk.github.io/eneratlas/) em um navegador atualizado. A faixa **VERSÃO WEB** identifica essa modalidade. A publicação depende da disponibilidade do GitHub Pages; se aparecer 404, consulte a seção de problemas ao final.

**Instalado:** abra o atalho **EnerAtlas** na área de trabalho ou no menu Iniciar. O navegador será aberto em um endereço local, normalmente `http://127.0.0.1:8769`. O programa e o processamento rodam no seu computador. Aguarde o catálogo e os números do acervo carregarem. Uma instalação com base configurada deve reutilizá-la automaticamente.

Ainda não instalou? Consulte a [instalação no Windows](INSTALACAO_WINDOWS.md). Instalar somente o programa, com a opção `-AppOnly`, deixa o acervo vazio até você importar ou vincular dados.

## 2. Entenda a tela

- **Esquerda:** busca, filtros, lista de camadas e aba **Cruzar dados**.
- **Centro:** mapa, controles de aproximação, escolha de fundo, legenda e botão **Registros**.
- **Direita:** ficha técnica do componente selecionado. Sem seleção, mostra os totais do acervo.
- **Parte inferior:** quantidade de componentes na vista e mensagens de carregamento ou sincronização.
- **Cabeçalho do aplicativo instalado:** **Fontes & dados**, **Importar camada**, **Sincronizar** e **⏻**.

O total do acervo é diferente da quantidade desenhada na vista atual. Um registro pode existir na base sem ter coordenadas.

## 3. Ative camadas e navegue

1. Na aba **Camadas**, use **Filtrar camadas…** para encontrar, por exemplo, transmissão, subestações, eólicas ou solares.
2. Marque a caixa da camada desejada. Você pode sobrepor várias fontes e tipos de componente.
3. Arraste o mapa para mover e use a roda do mouse ou os botões **+ / −** para aproximar e afastar.
4. Clique nos agrupamentos numerados de pontos para explorar os componentes.
5. Use **⌂** para voltar ao enquadramento do Brasil.
6. Use **Limpar** para desmarcar as camadas e começar outra seleção.

**Filtrar camadas…** muda a lista do catálogo. A busca **Nome, CEG, agente ou município…** filtra os registros consultados. Se nenhuma camada estiver marcada, não haverá componentes para mostrar.

Na web, camadas indicadas como **Acervo completo no executável** não podem ser ativadas nessa versão. No aplicativo, **Aguardando download / indexação** indica que a camada ainda não está pronta para consulta.

O mapa exibe até **1.800 componentes por consulta**, distribuídos pelas camadas selecionadas. Se aparecer um aviso de limite, aproxime o mapa ou reduza as camadas. A tabela permite consultar os demais registros da seleção.

## 4. Pesquise e aplique filtros

1. Marque as camadas que deseja pesquisar.
2. Digite um nome, CEG, agente ou município na busca principal.
3. Em **Todas as fontes**, escolha EPE, ANEEL, ONS ou LOCAL, se necessário.
4. No campo **UF**, informe a sigla com duas letras, como `PA` ou `MG`.
5. Em **Todos os registros**, escolha **Com geometria** ou **Sem geometria**.
6. Em **Situação**, use o valor exato informado pela fonte. No aplicativo local, podem aparecer sugestões.

Os filtros se combinam e afetam o mapa, a tabela e a exportação da consulta. Para ampliar os resultados, apague o texto, limpe UF e Situação e volte às opções gerais dos seletores.

**Exemplo:** marque uma camada de subestações, informe `PA` e abra **Registros**. Clique em uma linha da tabela para examinar a ficha.

## 5. Veja linhas de transmissão e imagem de satélite

As linhas de transmissão recebem cores conforme a **tensão nominal em kV**. Passe o mouse sobre uma linha para ver seu nome e sua tensão. A legenda mostra as classes presentes na vista. Valores sem tensão identificada aparecem em cinza tracejado.

Tensão em **kV** e potência em **MW** são grandezas diferentes: a classificação de cores das linhas usa tensão.

No seletor acima do mapa, escolha:

- **Mapa de ruas:** contexto cartográfico do OpenStreetMap.
- **Imagem de satélite:** imagens do Esri World Imagery.
- **Sem mapa de fundo:** mantém os componentes sem carregar imagens externas; útil para uso local sem internet.

Ruas e satélite exigem internet. A imagem de satélite tem data e resolução variáveis e não é uma transmissão ao vivo. A escolha do fundo fica salva no navegador utilizado.

## 6. Consulte a ficha técnica

1. Clique em um componente do mapa ou em uma linha de **Registros**.
2. Confira nome, fonte, camada, UF e tipo no painel à direita.
3. Leia **Geometria**, quando disponível: medidas calculadas e ponto de referência.
4. Em **Atributos originais**, consulte os valores publicados pela fonte. Use **Encontrar campo…** para localizar um atributo.
5. Confira **Vínculos por identificador**, a data de indexação e o link da fonte, quando presente.

Botões da ficha:

| Botão | Função |
|---|---|
| **Localizar** | Enquadra a geometria do registro no mapa; fica desabilitado se não houver geometria |
| **Cruzar →** | Abre a aba de cruzamentos usando o registro como origem |
| **Ficha JSON** | Baixa a ficha, com atributos e metadados disponíveis |
| **✕** | Fecha o painel da ficha |

**Não informado** significa que o atributo não contém um valor disponível. A data de indexação registra quando o dado entrou no índice; não representa necessariamente a data de atualização da instituição.

Vínculos por CNPJ indicam relação com um agente. Eles não provam que dois registros representam o mesmo empreendimento. Na web, os vínculos automáticos consideram os registros das camadas já carregadas no navegador.

## 7. Consulte a tabela e exporte

1. Clique em **Registros**, acima do mapa.
2. Confira projeto, fonte, camada, UF, situação e disponibilidade de geometria.
3. Use **Anterior** e **Próxima** para navegar; cada página mostra até 50 registros.
4. Clique em um registro para abrir sua ficha.
5. Clique em **Exportar consulta CSV** para baixar os registros da consulta, incluindo as outras páginas.

O CSV respeita as camadas e os filtros da consulta, mas não fica limitado ao enquadramento visível do mapa. Na web, a exportação contém somente os dados disponíveis no snapshot publicado.

**Dados ONS:** o CSV de linhas de transmissão utilizado não publica traçados. Esses registros podem ser consultados na tabela e cruzados por campos; o aplicativo não cria linhas fictícias para posicioná-los.

## 8. Cruze dados por campo — web e instalado

Use esse recurso quando duas bases possuem valores comparáveis, como um identificador de empreendimento.

1. Abra a ficha de um registro de origem.
2. Clique em **Cruzar →** ou na aba **Cruzar dados**.
3. Vá até **Cruzar por campo**.
4. Escolha o **Campo do registro selecionado**.
5. Escolha a **Camada de destino**.
6. Informe o **Nome exato do campo de destino**; os nomes técnicos aparecem nas fichas e podem ser sugeridos pela interface.
7. Clique em **Cruzar campos →**.
8. Abra as correspondências ou use **Exportar CSV**.

**Exemplo:** se origem e destino tiverem um campo CEG, compare esse campo entre as duas camadas. Verifique antes se os valores usam o mesmo conceito.

A comparação usa igualdade normalizada de texto, sem exigir a mesma apresentação de maiúsculas, acentos e pontuação. Ela não faz uma busca aproximada por nomes semelhantes. A lista retorna até 200 correspondências, com indicação quando o resultado é parcial; a exportação desse cruzamento contém os resultados retornados. Confira os resultados na fonte: uma coincidência isolada não comprova identidade entre projetos.

## 9. Faça cruzamentos espaciais — somente instalado

1. Abra a ficha de um registro com geometria e clique em **Cruzar →**.
2. Em **Relação**, escolha uma opção da tabela abaixo.
3. Para proximidade, informe **Distância em km**, entre 0 e 100.
4. Selecione as **Camadas de destino**. Segure **Ctrl** para escolher mais de uma.
5. Clique em **Cruzar camadas →**.
6. Abra as fichas dos resultados ou use **Exportar cruzamento CSV**.

| Relação | Pergunta que responde |
|---|---|
| **Até uma distância** | Quais componentes estão até o raio escolhido da geometria de origem? |
| **Interseção de geometrias** | Quais componentes tocam ou cruzam a geometria de origem? |
| **Dentro do projeto selecionado** | Quais componentes estão contidos na geometria de origem? |

**Exemplo:** selecione uma usina, escolha **Até uma distância**, informe `10` km e selecione camadas de subestações como destino. Os resultados mostram proximidade espacial; isso não comprova conexão elétrica ou capacidade de atendimento.

O cruzamento usa a geometria integral do índice local. A seleção de destino é própria desse formulário; os filtros de busca do explorador não definem o conjunto da análise espacial. Há limite de **5.000 candidatos**. Se o resultado for indicado como parcial, reduza o raio ou as camadas. Medidas são exploratórias e dependem da precisão das fontes.

## 10. Personalize os símbolos

1. Na lista de camadas, clique na engrenagem **⚙** ao lado da camada.
2. Escolha a cor e o ícone.
3. Clique em **Aplicar estilo**.

Existem símbolos para eólica (`wind`), solar (`sun`), transmissão (`tower`), subestação (`substation`), água (`water`), barragem (`dam`) e outros tipos. As opções aparecem com esses nomes na interface atual.

As preferências ficam no navegador usado naquele endereço; não alteram os arquivos da fonte nem a aparência dos outros usuários. Nas linhas classificadas por tensão, a cor automática de kV prevalece sobre a cor personalizada da camada.

## 11. Importe seus arquivos — somente instalado

1. Clique em **Importar camada** no cabeçalho.
2. Escolha um **GeoJSON** em WGS84/EPSG:4326 ou um **CSV UTF-8**, de até 256 MB.
3. Preencha o nome da camada.
4. Documente o endereço da fonte, descrição, data e licença.
5. Para CSV com coordenadas, informe os nomes das colunas de longitude e latitude.
6. Clique em **Importar e indexar →**, aguarde e marque a nova camada no catálogo.

CSV sem coordenadas entra como tabela e continua disponível para fichas e cruzamento por campo. Para atualizar uma camada própria, importe novamente com o mesmo nome; use outro nome se quiser manter versões lado a lado.

## 12. Sincronize e atualize as bases — somente instalado

São duas operações diferentes:

| Operação | O que faz |
|---|---|
| **Sincronizar** | Lê arquivos locais concluídos e indexa os que mudaram; não baixa dados da internet |
| **Fontes & dados → Atualizar camadas marcadas** | Consulta as fontes oficiais das camadas selecionadas, baixa e reindexa seus dados |

Para usar uma coleta já baixada, abra **Fontes & dados**, informe a pasta das bases e clique em **Adicionar pasta**. A pasta precisa seguir a estrutura de coleta reconhecida; para arquivos avulsos, use **Importar camada**. A sincronização local também ocorre automaticamente a cada dois minutos enquanto o aplicativo está aberto.

Para atualizar pela internet:

1. Marque no explorador somente as camadas que deseja atualizar.
2. Abra **Fontes & dados**.
3. Clique em **Atualizar camadas marcadas**.
4. Acompanhe o estado e os possíveis erros nessa janela.
5. Aguarde download e indexação. Camadas volumosas podem levar horas; a versão anterior continua consultável durante a atualização.

Abrir o programa não inicia uma recoleta automática das instituições. O atualizador trabalha com camadas já cadastradas, sem descobrir automaticamente novos serviços.

Consulte [onde encontrar os dados atualizados](ONDE_ATUALIZAR_AS_BASES.md) e [os procedimentos de atualização](ATUALIZACAO.md). Na versão web, o acervo muda quando o mantenedor publica um novo snapshot.

## 13. Raster, uso offline e encerramento

**Raster:** no aplicativo, uma prévia georreferenciada do **IPA Total** pode aparecer na lista quando o arquivo oficial estiver presente e reconhecido. Marque sua caixa para sobrepor a imagem. Essa prévia não está no snapshot web.

**Sem internet:** abra a instalação com a base já disponível e escolha **Sem mapa de fundo**. Consultas, fichas e análises usam o índice local. Download de atualizações, ruas, satélite e abertura dos sites das fontes precisam de conexão.

**Encerrar:** no aplicativo instalado, aguarde as operações em andamento e clique em **⏻** no cabeçalho. Fechar apenas a aba do navegador deixa o processo local ativo. Na versão web, basta fechar a aba.

## 14. Resolva problemas comuns

| O que aparece | Como proceder |
|---|---|
| **404** no link público | A publicação do GitHub Pages está indisponível. O mantenedor precisa verificar o deploy e eventuais restrições da conta. Use a instalação local enquanto isso; importar dados não corrige esse 404 |
| Imagens de fundo com **403 / Access blocked** | Atualize o aplicativo ou recarregue a página atualizada. Teste satélite ou **Sem mapa de fundo** e verifique a conexão. A falha do fundo não significa perda das bases |
| **0 camadas / 0 registros** no instalado | Abra pelo atalho da instalação. Se instalou só o programa, importe ou vincule uma base. Se já possuía dados, confira o caminho registrado em `INSTALACAO.json` conforme o guia de instalação; preserve a base existente |
| Há camadas, mas nada no mapa | Marque uma camada com geometria, limpe os filtros e volte à visão do Brasil. Consulte também **Registros** |
| Registro sem localização | Abra pela tabela e consulte os atributos. A fonte pode não ter publicado geometria |
| Não encontra um projeto | Amplie fontes e filtros, confira a disponibilidade da camada e procure na tabela. O acervo web é menor que o local e o mapa possui limite por vista |
| Cruzamento não funciona na web | Use **Cruzar por campo** ou abra o instalado para análise espacial |
| **Aplicativo desconectado** | Reabra o atalho EnerAtlas; o servidor local pode ter sido encerrado |
| Atualização demorada ou com erro | Confira o estado em **Fontes & dados** e a disponibilidade da fonte. Não interprete falha de coleta como ausência de infraestrutura |

## 15. Entenda a cobertura e as fontes

A web usa um **snapshot**: um retrato dos dados publicado em determinada data. Consulte [snapshot.json](../site/snapshot.json) para saber a cobertura e a data dessa publicação. Camadas grandes, raster e downloads pendentes podem aparecer apenas como referência ao aplicativo completo.

As geometrias web são simplificadas para visualização e não devem ser usadas para medir distâncias ou deduzir interseções de engenharia. O aplicativo instalado consulta o acervo que efetivamente está indexado naquela instalação; ele não garante, por si só, que todas as fontes estejam atualizadas.

O projeto é independente e preserva a origem dos registros. Uma instalação pode aparecer em mais de uma instituição. Confira datas, unidades, licenças e atributos antes de usar os dados em decisões técnicas.

- [Fontes e licenças](FONTES.md)
- [Onde atualizar EPE, ANEEL e ONS](ONDE_ATUALIZAR_AS_BASES.md)
- [Instalação no Windows](INSTALACAO_WINDOWS.md)
- [Atualização e backup](ATUALIZACAO.md)
- [Repositório EnerAtlas](https://github.com/patrick9kk/eneratlas)

**Contato:** [GitHub](https://github.com/patrick9kk) · [LinkedIn](https://www.linkedin.com/in/patrick-maximo-serafim-750729177/) · [patrickmaximocordeiro9@gmail.com](mailto:patrickmaximocordeiro9@gmail.com)
