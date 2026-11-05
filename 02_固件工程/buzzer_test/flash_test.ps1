param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$taskCore = 'C:\Users\lihao\Documents\Codex\2026-10-14\zhe\work\clang_analysis\pio_core'
$taskPio = 'C:\Users\lihao\Documents\Codex\2026-10-14\zhe\work\clang_analysis\pio_venv\Scripts\pio.exe'
$taskOpenOcd = Join-Path $taskCore 'packages\tool-openocd\bin\openocd.exe'
$taskScripts = Join-Path $taskCore 'packages\tool-openocd\openocd\scripts'
$taskBackup = Join-Path $PSScriptRoot 'backup\before-buzzer-flash.bin'
Push-Location -LiteralPath $PSScriptRoot
try {
    if ($Restore) {
        if (!(Test-Path -LiteralPath $taskBackup)) { throw 'Original flash backup is missing.' }
        & $taskOpenOcd -s $taskScripts -f interface/stlink.cfg -f target/stm32f4x.cfg -c 'program backup/before-buzzer-flash.bin 0x08000000 verify reset exit'
        if ($LASTEXITCODE -ne 0) { throw "Restore failed: $LASTEXITCODE" }
    } else {
        $env:PLATFORMIO_CORE_DIR = $taskCore
        if (!(Test-Path -LiteralPath $taskBackup)) {
            New-Item -ItemType Directory -Path 'backup' -Force | Out-Null
            & $taskOpenOcd -s $taskScripts -f interface/stlink.cfg -f target/stm32f4x.cfg -c 'init; reset halt; dump_image backup/before-buzzer-flash.bin 0x08000000 0x80000; reset run; shutdown'
            if ($LASTEXITCODE -ne 0) { throw "Backup failed: $LASTEXITCODE" }
        }
        if ((Get-Item -LiteralPath $taskBackup).Length -ne 524288) { throw 'Original flash backup is incomplete.' }
        & $taskPio run -d $PSScriptRoot -e nucleo_f411re_buzzer -t upload
        if ($LASTEXITCODE -ne 0) { throw "Build/upload failed: $LASTEXITCODE" }
    }
} finally {
    Pop-Location
}
