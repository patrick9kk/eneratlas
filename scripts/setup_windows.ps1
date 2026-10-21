# Bootstrap Windows 5.1+: binario com dependencias, acervo publicado e atalhos.
[CmdletBinding()]
param(
    [switch]$AppOnly,
    [switch]$NoLaunch,
    [switch]$CheckOnly,
    [switch]$NoShortcuts,
    [string]$InstallRoot = (Join-Path $env:LOCALAPPDATA 'Programs\EnerAtlas'),
    [string]$DataRoot = (Join-Path $env:LOCALAPPDATA 'EnerAtlas\data'),
    [string]$CacheRoot = (Join-Path $env:LOCALAPPDATA 'EnerAtlas\downloads')
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

function Get-SafeChild([string]$Root, [string]$Child) {
    $base = [IO.Path]::GetFullPath($Root).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
    $path = [IO.Path]::GetFullPath((Join-Path $Root $Child))
    if (-not $path.StartsWith($base, [StringComparison]::OrdinalIgnoreCase)) { throw 'Caminho fora da pasta esperada.' }
    return $path
}

function Get-ReleaseMetadata([string]$Tag) {
    $suffix = if ($Tag -eq 'latest') { 'latest' } else { 'tags/' + $Tag }
    return Invoke-RestMethod -Uri ('https://api.github.com/repos/patrick9kk/eneratlas/releases/' + $suffix) -Headers @{ 'User-Agent'='EnerAtlas-Installer'; 'Accept'='application/vnd.github+json' } -TimeoutSec 60
}

function Test-ExpectedHash([string]$Path, [string]$Hash) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $stream = [IO.File]::OpenRead($Path)
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','') -eq $Hash) }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Get-VerifiedAsset($Asset, [string]$Directory) {
    $name = [string]$Asset.name
    if ([IO.Path]::GetFileName($name) -ne $name -or $name.IndexOfAny([IO.Path]::GetInvalidFileNameChars()) -ge 0) { throw 'Nome de arquivo invalido na release.' }
    if ([string]$Asset.digest -notmatch '^sha256:([a-fA-F0-9]{64})$') { throw ('Release sem SHA-256 para ' + $name) }
    $hash = $Matches[1]
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $target = Get-SafeChild $Directory $name
    if (Test-ExpectedHash $target $hash) { Write-Host ('Reutilizando ' + $name); return $target }
    if (-not ([string]$Asset.browser_download_url).StartsWith('https://github.com/patrick9kk/eneratlas/releases/download/')) { throw 'Endereco de download inesperado.' }
    $partial = $target + '.partial'
    Write-Host ('Baixando ' + $name + ' ...')
    Invoke-WebRequest -UseBasicParsing -Uri $Asset.browser_download_url -OutFile $partial -Headers @{ 'User-Agent'='EnerAtlas-Installer' } -TimeoutSec 3600
    if (-not (Test-ExpectedHash $partial $hash)) { throw ('SHA-256 nao confere: ' + $name + '. A instalacao anterior foi preservada.') }
    Move-Item -LiteralPath $partial -Destination $target -Force
    return $target
}

function Join-VerifiedParts([string[]]$Parts, [string]$Destination, [string]$Hash) {
    if (Test-ExpectedHash $Destination $Hash) { return $Destination }
    $out = [IO.File]::Open($Destination, [IO.FileMode]::Create, [IO.FileAccess]::Write)
    try {
        foreach ($part in $Parts) {
            $inputStream = [IO.File]::OpenRead($part)
            try { $inputStream.CopyTo($out, 8MB) } finally { $inputStream.Dispose() }
        }
    } finally { $out.Dispose() }
    if (-not (Test-ExpectedHash $Destination $Hash)) { throw 'SHA-256 do pacote reunido nao confere.' }
    return $Destination
}

function Expand-VerifiedZip([string]$Archive, [string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($entry in $zip.Entries) {
            if (-not $entry.FullName) { continue }
            $target = Get-SafeChild $Destination ($entry.FullName.Replace('/', [IO.Path]::DirectorySeparatorChar))
            if ($entry.FullName.EndsWith('/')) { New-Item -ItemType Directory -Path $target -Force | Out-Null; continue }
            New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force | Out-Null
            $inputStream = $entry.Open()
            $out = [IO.File]::Open($target, [IO.FileMode]::Create, [IO.FileAccess]::Write)
            try { $inputStream.CopyTo($out, 8MB) } finally { $out.Dispose(); $inputStream.Dispose() }
        }
    } finally { $zip.Dispose() }
}

function Test-SqliteFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    try {
        $header = New-Object byte[] 16
        $read = $stream.Read($header,0,16)
        return $read -eq 16 -and [Text.Encoding]::ASCII.GetString($header) -eq "SQLite format 3`0"
    } finally { $stream.Dispose() }
}

function Get-AvailableBytes([string]$Path) {
    return (New-Object IO.DriveInfo([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($Path)))).AvailableFreeSpace
}

function Install-EnerAtlas {
    foreach ($path in @($InstallRoot,$DataRoot,$CacheRoot)) {
        if ([IO.Path]::GetFullPath($path).TrimEnd('\') -eq [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($path)).TrimEnd('\')) { throw 'Nao instale na raiz de um volume.' }
    }
    if (-not [Environment]::Is64BitOperatingSystem) { throw 'Esta distribuicao requer Windows x64.' }
    $latest = Get-ReleaseMetadata 'latest'
    $exeAsset = @($latest.assets | Where-Object { $_.name -eq 'EnerAtlas.exe' })
    if ($exeAsset.Count -ne 1) { throw 'Executavel nao encontrado na release atual.' }
    if ([string]$latest.tag_name -notmatch '^[a-zA-Z0-9._-]+$') { throw 'Versao invalida.' }
    $db = Get-SafeChild $DataRoot 'eneratlas.db'
    $existing = Test-SqliteFile $db
    if ((Test-Path -LiteralPath $db) -and -not $existing) { throw 'Banco local invalido; preserve-o e revise a pasta de dados.' }
    $needsData = -not $existing -and -not $AppOnly
    $plan = [pscustomobject]@{ version=$latest.tag_name; executable=(Get-SafeChild $InstallRoot 'EnerAtlas.exe'); data=$DataRoot; existing_data=$existing; download_full_data=$needsData; minimum_free_gb=20 }
    if ($CheckOnly) { return $plan }
    if ($needsData -and (Get-AvailableBytes $CacheRoot) -lt 20GB) { throw 'A primeira instalacao completa precisa de pelo menos 20 GB livres para download, reuniao e extracao.' }
    $cachedExe = Get-VerifiedAsset $exeAsset[0] (Get-SafeChild $CacheRoot $latest.tag_name)
    $exeTarget = $plan.executable
    $exeHash = ([string]$exeAsset[0].digest).Substring(7)
    $replaceExe = -not (Test-ExpectedHash $exeTarget $exeHash)
    if ($replaceExe) {
        $active = @([Diagnostics.Process]::GetProcessesByName('EnerAtlas') | Where-Object {
            try { $_.MainModule.FileName -eq $exeTarget } catch { $false }
        })
        if ($active) { throw 'Feche o EnerAtlas pelo botao de energia e execute o instalador novamente para atualizar.' }
    }
    if ($needsData) {
        Write-Host 'Primeira instalacao: baixando o acervo publicado (aproximadamente 3,57 GB).'
        $base = Get-ReleaseMetadata 'v1.0.0'
        $cache = Get-SafeChild $CacheRoot 'acervo-v1.0.0'
        $manifestAsset = @($base.assets | Where-Object { $_.name -eq 'EnerAtlas-SHA256SUMS.txt' })
        if ($manifestAsset.Count -ne 1) { throw 'Manifesto do acervo nao encontrado.' }
        $manifest = Get-VerifiedAsset $manifestAsset[0] $cache
        $archiveHash = $null
        foreach ($line in (Get-Content -LiteralPath $manifest)) {
            if ($line -match '^([a-fA-F0-9]{64})\s+EnerAtlas-Windows-portatil\.zip$') { $archiveHash=$Matches[1] }
        }
        if (-not $archiveHash) { throw 'SHA-256 do acervo ausente no manifesto.' }
        $partAssets = @($base.assets | Where-Object { $_.name -match '^EnerAtlas-Windows-portatil\.zip\.part\d{3}$' } | Sort-Object name)
        if ($partAssets.Count -ne 4) { throw 'O acervo inicial requer quatro partes.' }
        $parts = @()
        for ($i=0;$i -lt 4;$i++) {
            if ($partAssets[$i].name -ne ('EnerAtlas-Windows-portatil.zip.part' + ($i+1).ToString('000'))) { throw 'Sequencia de partes incompleta.' }
            $parts += Get-VerifiedAsset $partAssets[$i] $cache
        }
        $archive = Join-VerifiedParts $parts (Get-SafeChild $cache 'EnerAtlas-Windows-portatil.zip') $archiveHash
        Write-Host 'Extraindo o acervo. Aguarde...'
        $staging = Get-SafeChild $cache 'extraido'
        Expand-VerifiedZip $archive $staging
        $stagedData = Get-SafeChild $staging 'EnerAtlas\data'
        if (-not (Test-SqliteFile (Get-SafeChild $stagedData 'eneratlas.db'))) { throw 'O pacote nao contem um banco SQLite valido.' }
        New-Item -ItemType Directory -Path $DataRoot -Force | Out-Null
        $stagedItems = @(Get-ChildItem -LiteralPath $stagedData -Force | Sort-Object { $_.Name -eq 'eneratlas.db' })
        foreach ($item in $stagedItems) {
            $destination = Get-SafeChild $DataRoot $item.Name
            if (Test-Path -LiteralPath $destination) { throw 'Dados existentes nao serao substituidos.' }
        }
        foreach ($item in $stagedItems) {
            $destination = Get-SafeChild $DataRoot $item.Name
            Move-Item -LiteralPath $item.FullName -Destination $destination
        }
    }
    New-Item -ItemType Directory -Path $InstallRoot,$DataRoot -Force | Out-Null
    if ($replaceExe) { Copy-Item -LiteralPath $cachedExe -Destination $exeTarget -Force }
    if (-not (Test-ExpectedHash $exeTarget $exeHash)) { throw 'O executavel instalado nao confere.' }
    if (-not $NoShortcuts) {
        $menu = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\EnerAtlas'
        New-Item -ItemType Directory -Path $menu -Force | Out-Null
        $shell = New-Object -ComObject WScript.Shell
        foreach ($link in @((Join-Path ([Environment]::GetFolderPath('Desktop')) 'EnerAtlas.lnk'), (Join-Path $menu 'EnerAtlas.lnk'))) {
            $shortcut=$shell.CreateShortcut($link);$shortcut.TargetPath=$exeTarget
            $shortcut.Arguments='--data-dir "'+$DataRoot+'"';$shortcut.WorkingDirectory=$InstallRoot
            $shortcut.IconLocation=$exeTarget+',0';$shortcut.Description='EnerAtlas - mapa de infraestrutura energetica';$shortcut.Save()
        }
    }
    $utf8 = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Get-SafeChild $InstallRoot 'INSTALACAO.json'), ($plan | ConvertTo-Json), $utf8)
    Write-Host ('EnerAtlas instalado em ' + $InstallRoot)
    if ($existing) { Write-Host 'Sua base existente foi preservada. Nenhum acervo antigo foi colocado sobre ela.' }
    if (-not $NoLaunch) { Start-Process -FilePath $exeTarget -ArgumentList @('--data-dir', ('"'+$DataRoot+'"')) -WindowStyle Hidden }
    return $plan
}

if ($MyInvocation.InvocationName -ne '.') {
    try { $result=Install-EnerAtlas; if ($CheckOnly) { $result | ConvertTo-Json } }
    catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
}
