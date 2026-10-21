# Instala por usuario, sem administrador, preservando as bases existentes.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Executable,
    [Parameter(Mandatory=$true)][string]$ExistingData,
    [string]$SourcesRoot,
    [switch]$MoveData
)
$ErrorActionPreference = 'Stop'
$exeSource = (Resolve-Path -LiteralPath $Executable).Path
$dataSource = (Resolve-Path -LiteralPath $ExistingData).Path
$localRoot = [Environment]::GetFolderPath('LocalApplicationData')
$programRoot = [IO.Path]::GetFullPath((Join-Path $localRoot 'Programs\EnerAtlas'))
$storageRoot = [IO.Path]::GetFullPath((Join-Path $localRoot 'EnerAtlas'))
$dataTarget = [IO.Path]::GetFullPath((Join-Path $storageRoot 'data'))
if (-not $dataTarget.StartsWith($storageRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Destino de dados fora da pasta de instalacao.'
}
if (-not (Test-Path -LiteralPath (Join-Path $dataSource 'eneratlas.db'))) { throw 'Banco de dados nao encontrado.' }
if ([IO.Path]::GetFileName($exeSource) -ne 'EnerAtlas.exe') { throw 'Executavel inesperado.' }
$sourceItem = Get-Item -LiteralPath $dataSource
if ($MoveData -and $sourceItem.Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)) {
    $dataSource = $sourceItem.ResolveLinkTarget($true).FullName
}
New-Item -ItemType Directory -Path $programRoot,$storageRoot -Force | Out-Null
if (-not $dataSource.Equals($dataTarget, [StringComparison]::OrdinalIgnoreCase)) {
    if (Test-Path -LiteralPath $dataTarget) { throw 'O destino ja existe; nenhuma base sera substituida.' }
    if ($MoveData) {
        # Somente a pasta literal fornecida e movida, com destino absoluto validado.
        # Mesmo volume: a realocacao nao precisa de outra copia integral do banco.
        if ([IO.Path]::GetPathRoot($dataSource) -ne [IO.Path]::GetPathRoot($dataTarget)) {
            throw 'Use MoveData apenas no mesmo volume.'
        }
        Move-Item -LiteralPath $dataSource -Destination $dataTarget
        # Mantem os caminhos anteriores funcionais para projetos e coletores.
        New-Item -ItemType Junction -Path $dataSource -Target $dataTarget | Out-Null
    } else {
        throw 'Forneca a base ja instalada ou autorize sua realocacao com MoveData; nenhuma copia automatica sera feita.'
    }
}
$exeTarget = Join-Path $programRoot 'EnerAtlas.exe'
Copy-Item -LiteralPath $exeSource -Destination $exeTarget -Force
if ((Get-FileHash -LiteralPath $exeSource -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $exeTarget -Algorithm SHA256).Hash) {
    throw 'O executavel copiado nao confere.'
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
$settings = Join-Path $dataTarget 'sources.local.json'
$sourceRoots = @()
if (Test-Path -LiteralPath $settings) { $sourceRoots += @(Get-Content -LiteralPath $settings -Raw | ConvertFrom-Json) }
if ($SourcesRoot) { $sourceRoots += (Resolve-Path -LiteralPath $SourcesRoot).Path }
$sourceRoots = @($sourceRoots | Select-Object -Unique)
[IO.File]::WriteAllText($settings, (ConvertTo-Json -InputObject $sourceRoots), $utf8)
$desktop = [Environment]::GetFolderPath('Desktop')
$menuFolder = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\EnerAtlas'
New-Item -ItemType Directory -Path $menuFolder -Force | Out-Null
$shell = New-Object -ComObject WScript.Shell
$links = @((Join-Path $desktop 'EnerAtlas.lnk'), (Join-Path $menuFolder 'EnerAtlas.lnk'))
foreach ($linkPath in $links) {
    $shortcut = $shell.CreateShortcut($linkPath)
    $shortcut.TargetPath = $exeTarget
    $shortcut.Arguments = '--data-dir "' + $dataTarget + '"'
    $shortcut.WorkingDirectory = $programRoot
    $shortcut.IconLocation = $exeTarget + ',0'
    $shortcut.Description = 'EnerAtlas - mapa local de infraestrutura energetica'
    $shortcut.Save()
}
$record = [ordered]@{
    installed_at = (Get-Date).ToString('o')
    executable = $exeTarget
    data = $dataTarget
    original_data_access = $dataSource
    shortcuts = $links
    executable_sha256 = (Get-FileHash -LiteralPath $exeTarget -Algorithm SHA256).Hash
}
[IO.File]::WriteAllText((Join-Path $programRoot 'INSTALACAO.json'), ($record | ConvertTo-Json -Depth 4), $utf8)
$record | ConvertTo-Json -Depth 4
