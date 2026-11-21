#!/usr/bin/env bash
# Equivalente Unix de start_lab.ps1
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "No existe .venv. Ejecuta primero scripts/setup.sh" >&2
  exit 1
fi
source .venv/bin/activate

docker compose up -d
echo "Esperando a Ollama ..."
until docker exec ollama-rag-lab ollama list >/dev/null 2>&1; do sleep 3; done
docker exec ollama-rag-lab ollama pull qwen2.5:1.5b-instruct
python scripts/bootstrap_openwebui.py --base-model qwen2.5:1.5b-instruct

echo "Open WebUI: http://localhost:3000"
echo "Prueba de API: python test_openwebui_api.py"
