param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }),
    [switch]$Check,
    [switch]$Install
)
$ErrorActionPreference = 'Stop'
$sourceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../skills'))
if ([string]::IsNullOrWhiteSpace($CodexHome)) { throw 'CodexHome must not be empty.' }
if (-not [IO.Path]::IsPathFullyQualified($CodexHome)) { throw 'CodexHome must be an absolute path.' }
$destinationHome = [IO.Path]::GetFullPath($CodexHome)
$names = @('github-sync', 'ch584-ui-tuning', 'embedded-link-debug')

function Assert-PlainPath([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse path refused: $current" }
            if (-not $item.PSIsContainer -and $current -ne $Path) { throw "Parent is not a directory: $current" }
        }
        $current = [IO.Path]::GetDirectoryName($current)
    }
}

function Get-Manifest([string]$Directory) {
    Assert-PlainPath $Directory
    if (-not (Get-Item -LiteralPath $Directory -Force).PSIsContainer) { throw "Not a skill directory: $Directory" }
    $manifest = @{}
    $queue = [Collections.Generic.Queue[string]]::new()
    $queue.Enqueue($Directory)
    while ($queue.Count) {
        foreach ($item in Get-ChildItem -LiteralPath $queue.Dequeue() -Force) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse entry refused: $($item.FullName)" }
            if ($item.PSIsContainer) { $queue.Enqueue($item.FullName); continue }
            $relative = [IO.Path]::GetRelativePath($Directory, $item.FullName).Replace('\', '/')
            $manifest[$relative] = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
        }
    }
    return $manifest
}

Assert-PlainPath $destinationHome
if ((Test-Path -LiteralPath $destinationHome) -and -not (Get-Item -LiteralPath $destinationHome).PSIsContainer) { throw 'CodexHome must be a directory.' }
$skillsDirectory = Join-Path $destinationHome 'skills'
$sourceBoundary = $sourceRoot.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
$targetBoundary = $skillsDirectory.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
if ($sourceBoundary.StartsWith($targetBoundary, [StringComparison]::OrdinalIgnoreCase) -or $targetBoundary.StartsWith($sourceBoundary, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Source and destination skills directories must not overlap.'
}
Assert-PlainPath $skillsDirectory
if ((Test-Path -LiteralPath $skillsDirectory) -and -not (Get-Item -LiteralPath $skillsDirectory).PSIsContainer) { throw 'skills must be a directory.' }
$states = @()
foreach ($name in $names) {
    $source = Join-Path $sourceRoot $name
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) { throw "Missing source skill: $name" }
    $sourceManifest = Get-Manifest $source
    $destination = Join-Path $skillsDirectory $name
    Assert-PlainPath $destination
    $state = 'missing'
    if (Test-Path -LiteralPath $destination) {
        $targetManifest = Get-Manifest $destination
        $identical = $sourceManifest.Count -eq $targetManifest.Count
        foreach ($key in $sourceManifest.Keys) {
            if (-not $targetManifest.ContainsKey($key) -or $sourceManifest[$key] -cne $targetManifest[$key]) { $identical = $false }
        }
        if (-not $identical) { throw "Existing skill differs; review and preserve local changes before replacing: $destination" }
        $state = 'identical'
    }
    $states += [pscustomobject]@{ Name = $name; Source = $source; Destination = $destination; State = $state }
}
Write-Output "Source: $sourceRoot"
Write-Output "Codex Home: $destinationHome"
foreach ($entry in $states) { Write-Output "$($entry.Name): $($entry.State)" }
if (-not $Install) {
    Write-Output 'Read-only preflight complete. Use -Install to copy missing skills.'
    return
}
# Every source and destination has passed preflight before the first write.
New-Item -ItemType Directory -Path $skillsDirectory -Force | Out-Null
foreach ($entry in $states) {
    if ($entry.State -eq 'identical') { Write-Output "Unchanged: $($entry.Name)"; continue }
    Copy-Item -LiteralPath $entry.Source -Destination $skillsDirectory -Recurse
    Write-Output "Installed: $($entry.Name)"
}
