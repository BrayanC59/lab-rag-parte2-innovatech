# Captura automatica de evidencias
# Ejecuta las verificaciones y guarda la salida en evidence/terminal/.
# Uso: powershell -ExecutionPolicy Bypass -File scripts/capture_evidence.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"
$dest = Join-Path $root "evidence\terminal"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

$env:PYTHONUTF8 = "1"

Write-Host "1/5 docker compose ps ..."
docker compose ps 2>&1 | Tee-Object -FilePath "$dest\01-docker-compose-ps.txt"

Write-Host "2/5 docker ps ..."
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" 2>&1 |
    Tee-Object -FilePath "$dest\02-docker-ps.txt"

Write-Host "3/5 modelos en Ollama ..."
docker exec ollama-rag-lab ollama list 2>&1 |
    Tee-Object -FilePath "$dest\03-ollama-list.txt"

Write-Host "4/5 modelos expuestos por Open WebUI ..."
& $python -c @"
import os, requests
from dotenv import load_dotenv
load_dotenv()
base = os.getenv('OPENWEBUI_BASE_URL', 'http://localhost:3000/api')
r = requests.get(base + '/models', timeout=60)
r.raise_for_status()
for m in sorted(r.json().get('data', []), key=lambda x: x['id']):
    print(m['id'])
"@ 2>&1 | Tee-Object -FilePath "$dest\04-modelos-openwebui.txt"

Write-Host "5/5 prueba de consumo por API ..."
& $python test_openwebui_api.py 2>&1 |
    Tee-Object -FilePath "$dest\05-test-openwebui-api.txt"

Write-Host "`nEvidencias guardadas en evidence/terminal/" -ForegroundColor Green
