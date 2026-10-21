# Instalação por usuário no Windows

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
