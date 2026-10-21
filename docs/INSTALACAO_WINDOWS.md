# Instalação por usuário no Windows

## Instalação automática recomendada

Após instalar, abra pelo atalho **EnerAtlas** da área de trabalho ou do menu Iniciar. O programa carrega a base instalada automaticamente e inicia com camadas existentes de geração, transmissão e subestações selecionadas. As outras camadas ficam disponíveis na lista. Não é necessário importar ou selecionar a pasta das bases a cada abertura.

A partir da versão 1.1.4, abrir novamente o atalho reutiliza a sessão da mesma base. O endereço local preferencial é `http://127.0.0.1:8769`; caso a porta esteja ocupada por outro programa, o navegador abre o endereço disponível automaticamente. O executável instalado também lê o caminho dos dados em `INSTALACAO.json` ao ser aberto diretamente, sem argumentos. A opção explícita `--data-dir` continua disponível.

Baixe e abra [Instalar-EnerAtlas.exe](https://github.com/patrick9kk/eneratlas/releases/download/v1.1.2/Instalar-EnerAtlas.exe). Ele inclui seu próprio ambiente de execução; não exige Python ou Git. O instalador consulta a release mais recente para obter o aplicativo, mesmo que seu próprio link esteja na release v1.1.2.

Para baixar todo o código, use [Download ZIP](https://github.com/patrick9kk/eneratlas/archive/refs/heads/main.zip), extraia e abra `Instalar-EnerAtlas.cmd`. Com Git instalado, uma linha no **CMD** faz tudo:

```bat
git clone https://github.com/patrick9kk/eneratlas.git && cd eneratlas && Instalar-EnerAtlas.cmd
```

O instalador usa o Windows PowerShell 5.1 incluído no Windows, sem alterar permanentemente sua política de execução. Não exige administrador. Baixa arquivos somente das releases deste repositório e verifica os hashes SHA-256 informados pelo GitHub. As quatro partes do acervo são reunidas e o ZIP completo também é conferido pelo manifesto publicado. Em caso de falha de rede, execute novamente: arquivos completos cujo hash confere são reaproveitados; a parte interrompida é reiniciada.

A primeira instalação completa baixa aproximadamente 3,57 GB de dados, além do aplicativo. Precisa de pelo menos 20 GB livres. Usa o acervo histórico v1.0.0 (144 camadas, 1.324.499 registros), não uma coleta nova dos portais. Consulte [onde atualizar cada base](ONDE_ATUALIZAR_AS_BASES.md) para dados atuais. Se já existir um banco SQLite na pasta de destino, ele será preservado e o pacote antigo não será baixado.

Destinos padrão:

| Conteúdo | Pasta |
|---|---|
| Programa | `%LOCALAPPDATA%\Programs\EnerAtlas` |
| Base e configurações | `%LOCALAPPDATA%\EnerAtlas\data` |
| Downloads e arquivos de instalação | `%LOCALAPPDATA%\EnerAtlas\downloads` |
| Atalhos | Área de trabalho e menu Iniciar do usuário |

Os arquivos de instalação ficam no cache para reaproveitamento. Depois de confirmar o funcionamento do mapa, você pode remover **somente a pasta `downloads`** para recuperar esse espaço; preserve a pasta `data`.

Opções, executadas na pasta extraída do repositório:

```powershell
# Instalar somente o aplicativo, sem acervo inicial
.\Instalar-EnerAtlas.cmd -AppOnly

# Consultar versão e plano de instalação sem modificar arquivos
.\Instalar-EnerAtlas.cmd -CheckOnly

# Instalar sem abrir o mapa ao concluir
.\Instalar-EnerAtlas.cmd -NoLaunch

# Usar outra unidade para os dados e os arquivos de instalação
.\Instalar-EnerAtlas.cmd -DataRoot D:\EnerAtlas\data -CacheRoot D:\EnerAtlas\downloads
```

As mesmas opções funcionam com `Instalar-EnerAtlas.exe`. Para atualizar o aplicativo, encerre-o pelo botão de energia e execute o instalador novamente. A pasta de dados permanece no computador. O download do acervo inicial não atualiza automaticamente as fontes oficiais.

Para gerar o instalador a partir do código, em um ambiente de desenvolvimento com `requirements-dev.txt` instalado:

```powershell
python scripts\build_installer.py
```

O resultado fica em `dist/Instalar-EnerAtlas.exe`. O fluxo é testado em Windows PowerShell 5.1 com um pacote pequeno: extração, reunião, hashes, preservação de banco existente e rejeição de caminhos fora da pasta de extração. Não é necessário baixar vários GB para executar esses testes.

Referências técnicas: [API de assets do GitHub](https://docs.github.com/en/rest/releases/assets) e [Invoke-WebRequest no PowerShell 5.1](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest?view=powershell-5.1).

## Instalar arquivos que você já possui

O aplicativo pode ser instalado sem administrador usando `scripts/install_windows.ps1`. O executável já deve ter sido extraído de uma release, e a pasta de dados deve conter `eneratlas.db`.

Feche o aplicativo pelo botão de energia e confirme que a indexação terminou antes de realocar os dados. Em PowerShell 7, a partir do repositório:

```powershell
./scripts/install_windows.ps1 `
  -Executable 'C:\EnerAtlas\EnerAtlas.exe' `
  -ExistingData 'C:\EnerAtlas\data' `
  -SourcesRoot 'C:\BasesEnergia' `
  -MoveData
```

O script instala o executável em `%LOCALAPPDATA%\Programs\EnerAtlas` e realoca os dados para `%LOCALAPPDATA%\EnerAtlas\data`. Ele cria atalhos na área de trabalho e no menu Iniciar do usuário. O manifesto local `INSTALACAO.json` registra os caminhos e o SHA-256 do executável.

`MoveData` é permitido apenas no mesmo volume. A realocação evita uma segunda cópia integral do banco; uma junção de diretório no caminho anterior mantém o acesso dos projetos existentes. Nenhum diretório de dados de destino já existente é substituído. Para usar dados já instalados, informe o próprio caminho de destino.

`SourcesRoot` é opcional e registra a pasta das bases originais para sincronização futura. Essa configuração e os caminhos pessoais ficam exclusivamente no computador, fora do Git. O script não habilita inicialização automática, não altera antivírus ou firewall e não instala Python.

Para abrir, use o atalho **EnerAtlas**. O navegador é a interface e o processamento continua local. Para encerrar, use o botão de energia no cabeçalho do mapa; fechar somente a aba não encerra o servidor.

Para atualizar o programa, encerre o aplicativo e substitua o executável na pasta instalada, preservando os dados. A distribuição portátil também permanece disponível nas releases.
