#!/usr/bin/env bash
# Equivalente Unix de setup.ps1
set -euo pipefail
cd "$(dirname "$0")/.."

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

[ -f .env ] || cp .env.example .env
echo "Listo. Siguiente paso: docker compose up -d && python scripts/bootstrap_openwebui.py"
