# Levanta Ollama + Open WebUI, descarga el modelo base y crea por API la base de
# conocimiento, el modelo personalizado y la API Key.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/start_lab.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    throw "No existe .venv. Ejecuta primero: powershell -File scripts/setup.ps1"
}

Write-Host "== 1. Levantando contenedores ==" -ForegroundColor Cyan
docker compose up -d

Write-Host "== 2. Esperando a Ollama ==" -ForegroundColor Cyan
for ($i = 0; $i -lt 60; $i++) {
    $ok = docker exec ollama-rag-lab ollama list 2>$null
    if ($LASTEXITCODE -eq 0) { break }
    Start-Sleep -Seconds 3
}

Write-Host "== 3. Modelo base ==" -ForegroundColor Cyan
docker exec ollama-rag-lab ollama pull qwen2.5:1.5b-instruct

Write-Host "== 4. Bootstrap de Open WebUI (cuenta, API key, knowledge, modelo) ==" -ForegroundColor Cyan
& $python scripts/bootstrap_openwebui.py --base-model qwen2.5:1.5b-instruct

Write-Host "`nOpen WebUI: http://localhost:3000" -ForegroundColor Green
Write-Host "Prueba de API: `$env:PYTHONUTF8=1; .\.venv\Scripts\python.exe test_openwebui_api.py"
