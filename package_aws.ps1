$ErrorActionPreference = "Stop"

$buildDir = "build"
$packageDir = Join-Path $buildDir "lambda"
$zipPath = Join-Path $buildDir "asistente-personal-lambda.zip"

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Path $packageDir | Out-Null

.\.venv\Scripts\python.exe -m pip install -r requirements.txt -t $packageDir

Copy-Item -LiteralPath "lambda_handler.py" -Destination $packageDir
Copy-Item -LiteralPath "app" -Destination $packageDir -Recurse
Copy-Item -LiteralPath "faqs.json" -Destination $packageDir

Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath -Force

Write-Host "Package created at $zipPath"
