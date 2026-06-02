param(
    [switch]$CheckOnly,
    [switch]$SkipLanguageList,
    [switch]$NoRestart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-QinKeyboardPreference {
    [ordered]@{
        remapKeys = [ordered]@{
            inProcess = @(
                [ordered]@{ originalKeys = '164'; newRemapKeys = '162' }
                [ordered]@{ originalKeys = '162'; newRemapKeys = '164' }
                [ordered]@{ originalKeys = '165'; newRemapKeys = '163' }
                [ordered]@{ originalKeys = '163'; newRemapKeys = '165' }
                [ordered]@{ originalKeys = '20'; newRemapKeys = '160' }
            )
        }
        remapKeysToText = [ordered]@{
            inProcess = @()
        }
        remapShortcuts = [ordered]@{
            global = @(
                [ordered]@{ originalKeys = '91;37'; newRemapKeys = '162;37'; targetApp = '' }
                [ordered]@{ originalKeys = '91;39'; newRemapKeys = '162;39'; targetApp = '' }
                [ordered]@{ originalKeys = '92;37'; newRemapKeys = '162;37'; targetApp = '' }
                [ordered]@{ originalKeys = '92;39'; newRemapKeys = '162;39'; targetApp = '' }
                [ordered]@{ originalKeys = '164;37'; newRemapKeys = '36'; targetApp = '' }
                [ordered]@{ originalKeys = '164;39'; newRemapKeys = '35'; targetApp = '' }
                [ordered]@{ originalKeys = '165;37'; newRemapKeys = '36'; targetApp = '' }
                [ordered]@{ originalKeys = '165;39'; newRemapKeys = '35'; targetApp = '' }
                [ordered]@{ originalKeys = '162;37'; newRemapKeys = '36'; targetApp = '' }
                [ordered]@{ originalKeys = '162;39'; newRemapKeys = '35'; targetApp = '' }
                [ordered]@{ originalKeys = '163;37'; newRemapKeys = '36'; targetApp = '' }
                [ordered]@{ originalKeys = '163;39'; newRemapKeys = '35'; targetApp = '' }
            )
            appSpecific = @()
        }
        remapShortcutsToText = [ordered]@{
            global = @()
            appSpecific = @()
        }
    }
}

function ConvertTo-CompactJson {
    param([Parameter(Mandatory)]$Value)
    $Value | ConvertTo-Json -Depth 20 -Compress
}

function Write-TextFileSafely {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Content)

    $directory = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $directory | Out-Null

    $temporaryPath = Join-Path $directory ('.qin-write-' + [guid]::NewGuid().ToString('N') + '.tmp')
    $encoding = New-Object System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($temporaryPath, $Content, $encoding)
    Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
}

function Backup-File {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Stamp)
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $directory = Split-Path -Parent $Path
    $name = [System.IO.Path]::GetFileNameWithoutExtension($Path)
    $extension = [System.IO.Path]::GetExtension($Path)
    $backupPath = Join-Path $directory "$name.backup-qin-$Stamp$extension"
    Copy-Item -LiteralPath $Path -Destination $backupPath
    $backupPath
}

function Get-WinUserLanguageEntries {
    $languageList = Get-WinUserLanguageList
    for ($i = 0; $i -lt $languageList.Count; $i++) {
        $languageList[$i]
    }
}

function Enable-KeyboardManager {
    param([Parameter(Mandatory)][string]$SettingsPath, [Parameter(Mandatory)][string]$Stamp)
    if (-not (Test-Path -LiteralPath $SettingsPath)) {
        Write-Warning "PowerToys settings.json was not found: $SettingsPath"
        return
    }

    $settingsRaw = Get-Content -Raw -LiteralPath $SettingsPath
    if ([string]::IsNullOrWhiteSpace($settingsRaw)) {
        $settings = [pscustomobject]@{}
    }
    else {
        $settings = $settingsRaw | ConvertFrom-Json
    }

    $enabledProperty = $settings.PSObject.Properties['enabled']
    if ($null -eq $enabledProperty -or $null -eq $enabledProperty.Value) {
        $settings | Add-Member -NotePropertyName enabled -NotePropertyValue ([pscustomobject]@{})
    }

    $keyboardManagerProperty = $settings.enabled.PSObject.Properties['Keyboard Manager']
    if ($null -ne $keyboardManagerProperty) {
        if ($keyboardManagerProperty.Value -eq $true) {
            Write-Output 'Keyboard Manager is already enabled in settings.json'
            return
        }

        $settings.enabled.'Keyboard Manager' = $true
    }
    else {
        $settings.enabled | Add-Member -NotePropertyName 'Keyboard Manager' -NotePropertyValue $true
    }

    $backupPath = Backup-File -Path $SettingsPath -Stamp $Stamp
    Write-TextFileSafely -Path $SettingsPath -Content (ConvertTo-CompactJson -Value $settings)
    Write-Output "Enabled Keyboard Manager in settings.json"
    Write-Output "Settings backup: $backupPath"
}

function Set-EnglishDefaultChineseLanguageList {
    $current = @(Get-WinUserLanguageEntries)
    $chinese = $current | Where-Object { $_.LanguageTag -eq 'zh-Hans-CN' } | Select-Object -First 1

    $newList = New-WinUserLanguageList -Language 'en-US'
    if ($null -eq $chinese) {
        [void]$newList.Add((New-WinUserLanguageList -Language 'zh-Hans-CN')[0])
    }
    else {
        [void]$newList.Add($chinese)
    }

    Set-WinUserLanguageList -LanguageList $newList -Force
    Set-WinDefaultInputMethodOverride -InputTip '0409:00000409'

    $languageBar = Get-WinLanguageBarOption
    Set-WinLanguageBarOption -UseLegacyLanguageBar:$languageBar.IsLegacyLanguageBar

    Write-Output 'Set Windows user language list to en-US first and zh-Hans-CN second'
    Write-Output 'Set default input method override to English (United States) - US'
    Write-Output 'Disabled per-app input method memory while preserving current language bar visibility'
}

function Find-KeyboardManagerEngine {
    $running = Get-Process -Name PowerToys.KeyboardManagerEngine -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($running -and $running.Path) {
        return $running.Path
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'PowerToys\KeyboardManagerEngine\PowerToys.KeyboardManagerEngine.exe'),
        (Join-Path $env:ProgramFiles 'PowerToys\KeyboardManagerEngine\PowerToys.KeyboardManagerEngine.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'PowerToys\KeyboardManagerEngine\PowerToys.KeyboardManagerEngine.exe')
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    $null
}

function Restart-KeyboardManagerEngine {
    $enginePath = Find-KeyboardManagerEngine
    if (-not $enginePath) {
        Write-Warning 'PowerToys Keyboard Manager engine was not found. Start or install PowerToys after applying the config.'
        return
    }

    Get-Process -Name PowerToys.KeyboardManagerEngine -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Milliseconds 800
    Start-Process -FilePath $enginePath -WindowStyle Hidden
    Start-Sleep -Milliseconds 1000

    $process = Get-Process -Name PowerToys.KeyboardManagerEngine -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($process) {
        Write-Output "Restarted PowerToys Keyboard Manager engine: $($process.Id)"
    }
    else {
        Write-Warning 'PowerToys Keyboard Manager engine did not appear after restart.'
    }
}

$configDir = Join-Path $env:LOCALAPPDATA 'Microsoft\PowerToys\Keyboard Manager'
$configPath = Join-Path $configDir 'default.json'
$settingsPath = Join-Path $env:LOCALAPPDATA 'Microsoft\PowerToys\settings.json'
$desiredJson = ConvertTo-CompactJson -Value (New-QinKeyboardPreference)

if ($CheckOnly) {
    Write-Output "PowerToys config path: $configPath"
    Write-Output "PowerToys settings path: $settingsPath"
    Write-Output "Desired Keyboard Manager config:"
    Write-Output $desiredJson
    if (-not $SkipLanguageList) {
        Get-WinUserLanguageEntries | ForEach-Object {
            Write-Output "Current language: $($_.LanguageTag) tips=$($_.InputMethodTips -join ',')"
        }
    }
    return
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
$configBackup = Backup-File -Path $configPath -Stamp $stamp
Write-TextFileSafely -Path $configPath -Content $desiredJson
Write-Output "Wrote Qin Keyboard Manager config: $configPath"
if ($configBackup) {
    Write-Output "Config backup: $configBackup"
}

Enable-KeyboardManager -SettingsPath $settingsPath -Stamp $stamp

if (-not $SkipLanguageList) {
    Set-EnglishDefaultChineseLanguageList
}

if (-not $NoRestart) {
    Restart-KeyboardManagerEngine
}
