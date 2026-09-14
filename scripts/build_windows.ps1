[CmdletBinding()]
param(
    [string]$Version = "1.0.0",
    [string]$PythonPath = "",
    [string]$InnoSetupPath = "",
    [switch]$SkipBundle
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$artifactsDir = Join-Path $projectRoot "artifacts"
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$installerScript = Join-Path $projectRoot "installer\MdfCutting.iss"

if (-not $PythonPath) {
    $PythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Не найден Python сборки: $PythonPath. Создайте .venv и установите requirements.txt."
}

$isccCandidates = @(
    @(
        $InnoSetupPath
        $env:INNO_SETUP_PATH
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe")
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe")
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
)
if (-not $isccCandidates) {
    throw "Не найден ISCC.exe из Inno Setup. Установите Inno Setup или передайте -InnoSetupPath."
}
$isccPath = $isccCandidates[0]

$bundleDir = Join-Path $distDir "MDF Cutting"
if (-not $SkipBundle) {
    Remove-Item -LiteralPath $artifactsDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $artifactsDir -Force | Out-Null

    & $PythonPath -m PyInstaller --noconfirm --clean --windowed --onedir `
        --name "MDF Cutting" `
        --distpath $distDir `
        --workpath $buildDir `
        --add-data "$projectRoot\web;web" `
        --add-data "$projectRoot\config.py;packer" `
        --add-data "$projectRoot\constants.py;packer" `
        --add-data "$projectRoot\utils.py;packer" `
        --add-data "$projectRoot\patterns.py;packer" `
        --add-data "$projectRoot\remnants.py;packer" `
        --add-data "$projectRoot\dxf_generator.py;packer" `
        --add-data "$projectRoot\layout_review.py;packer" `
        --add-data "$projectRoot\operator_review.py;packer" `
        --add-data "$projectRoot\packing.py;packer" `
        --add-data "$projectRoot\review_candidate.py;packer" `
        --paths $projectRoot `
        --hidden-import packer `
        --hidden-import packer.config `
        --hidden-import packer.constants `
        --hidden-import packer.utils `
        --hidden-import packer.patterns `
        --hidden-import packer.remnants `
        --hidden-import packer.dxf_generator `
        --hidden-import packer.layout_review `
        --hidden-import packer.operator_review `
        --hidden-import packer.packing `
        --hidden-import packer.review_candidate `
        --collect-all rectpack `
        --hidden-import pandas `
        --collect-data pandas `
        --collect-binaries pandas `
        --collect-all ezdxf `
        (Join-Path $projectRoot "main.py")
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller завершился с кодом $LASTEXITCODE" }
} elseif (-not (Test-Path -LiteralPath $bundleDir)) {
    throw "Нельзя пропустить PyInstaller: не найдена готовая папка $bundleDir"
}

& $isccPath "/DAppVersion=$Version" "/DSourceDir=$bundleDir" "/DOutputDir=$artifactsDir" $installerScript
if ($LASTEXITCODE -ne 0) { throw "Inno Setup завершился с кодом $LASTEXITCODE" }

$installerPath = Join-Path $artifactsDir "MDF Cutting Setup $Version.exe"
if (-not (Test-Path -LiteralPath $installerPath)) {
    throw "Не создан ожидаемый установщик: $installerPath"
}
Get-Item -LiteralPath $installerPath
