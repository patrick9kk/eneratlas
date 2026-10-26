/* Orientação de abertura compartilhada pelas versões local e pública. */
(() => {
  'use strict';
  const online = location.hostname.endsWith('github.io') || new URLSearchParams(location.search).has('online');
  const preference = 'eneratlas.tutorial.hidden.v1';
  const steps = [
    ['Bem-vindo ao EnerAtlas', 'Explore os dados de energia do Brasil.', 'Este guia mostra o que é cada parte da tela. Use Próximo para conhecer o mapa ou Fechar para começar a explorar.', 'Visão geral'],
    ['Camadas e busca', 'Escolha o que aparece à esquerda.', 'Camadas são grupos de dados, como usinas, linhas e subestações. Marque as caixas para mostrá-las. Use a busca para procurar projetos e os filtros para escolher fonte, UF e situação. A engrenagem muda o ícone e a cor da camada.', 'Painel esquerdo'],
    ['Mapa e satélite', 'Explore a região que interessa.', 'Arraste para mover e use + e − para aproximar. O botão de casa volta ao Brasil. No seletor acima do mapa, escolha ruas, satélite ou nenhum fundo. Passe o mouse nas linhas para ver nome e tensão; as cores indicam a tensão em kV.', 'Centro da tela'],
    ['Ficha técnica e registros', 'Clique em um componente para conhecê-lo.', 'A ficha à direita mostra os dados e a fonte do projeto. Localizar aproxima o mapa e Ficha JSON baixa a ficha. O botão Registros abre a tabela: ali você também encontra dados sem localização e pode exportar a consulta em CSV.', 'Painel direito e botão Registros'],
    ['Cruzar dados', 'Encontre relações entre as bases.', online
      ? 'Selecione um projeto e abra Cruzar dados. Em Cruzar por campo, compare identificadores de duas camadas. Análises por distância e interseção estão no aplicativo instalado. A web mostra as camadas publicadas e usa geometrias simplificadas.'
      : 'Selecione um projeto e abra Cruzar dados. Você pode buscar componentes próximos, que cruzam sua geometria ou ficam dentro dela. Em Cruzar por campo, compare identificadores de duas camadas. Confira a fonte: proximidade não comprova conexão elétrica.', 'Aba Cruzar dados']
  ];
  if (!online) steps.push(['Suas bases e atualizações', 'Os botões do topo cuidam dos dados.', 'Fontes & dados permite adicionar pastas e atualizar camadas pela internet. Importar camada recebe seus arquivos GeoJSON ou CSV. Sincronizar relê arquivos locais. Para usar sem internet, escolha Sem mapa de fundo. Para encerrar o programa, use ⏻.', 'Cabeçalho do aplicativo']);

  const dialog = document.createElement('dialog');
  dialog.id = 'welcome-dialog';
  dialog.className = 'welcome-dialog';
  dialog.setAttribute('aria-labelledby', 'welcome-title');
  dialog.setAttribute('aria-describedby', 'welcome-description');
  dialog.innerHTML = '<div class="dialog-heading"><span class="eyebrow">GUIA RÁPIDO · <span id="welcome-progress"></span></span><button id="welcome-close" aria-label="Fechar tutorial">Fechar ✕</button></div><div class="welcome-location" id="welcome-location"></div><div aria-live="polite" aria-atomic="true"><h2 id="welcome-title"></h2><p class="welcome-lead" id="welcome-lead"></p><p id="welcome-description"></p></div><label class="welcome-preference"><input type="checkbox" id="welcome-hide">Não mostrar ao abrir novamente</label><div class="welcome-actions"><button id="welcome-previous">← Voltar</button><button id="welcome-next" class="button-dark">Próximo →</button></div><p class="welcome-reminder">Você pode rever este guia no botão Tutorial, no topo da tela.</p>';
  document.body.append(dialog);
  const element = id => document.getElementById(id);
  let current = 0;
  function render() {
    const [title, lead, description, area] = steps[current];
    element('welcome-title').textContent = title;
    element('welcome-lead').textContent = lead;
    element('welcome-description').textContent = description;
    element('welcome-location').textContent = area;
    element('welcome-progress').textContent = `${current + 1} de ${steps.length}`;
    element('welcome-previous').disabled = current === 0;
    element('welcome-next').textContent = current === steps.length - 1 ? 'Começar a usar ✓' : 'Próximo →';
  }
  function remember() {
    try {
      if (element('welcome-hide').checked) localStorage.setItem(preference, '1');
      else localStorage.removeItem(preference);
    } catch { /* O guia continua utilizável sem armazenamento no navegador. */ }
  }
  function open() {
    current = 0;
    try { element('welcome-hide').checked = localStorage.getItem(preference) === '1'; } catch {}
    render();
    if (!dialog.open) dialog.showModal();
  }
  const help = document.createElement('button');
  help.id = 'open-tutorial';
  help.textContent = '? Tutorial';
  help.setAttribute('aria-haspopup', 'dialog');
  help.onclick = open;
  document.querySelector('.topbar nav').prepend(help);
  element('welcome-close').onclick = () => dialog.close();
  element('welcome-previous').onclick = () => { if (current > 0) { current--; render(); } };
  element('welcome-next').onclick = () => {
    if (current === steps.length - 1) dialog.close();
    else { current++; render(); }
  };
  dialog.addEventListener('close', remember);
  let hidden = false;
  try { hidden = localStorage.getItem(preference) === '1'; } catch {}
  if (!hidden) open();
})();
