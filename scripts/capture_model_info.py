"""Verifica y documenta el modelo personalizado y su recuperacion vectorial.

Imprime la lista de modelos expuestos por Open WebUI, la configuracion del
modelo personalizado (modelo base, temperatura, knowledge vinculada) y una
consulta de prueba al indice vectorial. Se usa para generar la evidencia
evidence/terminal/04-modelos-openwebui.txt.

Uso:
    python scripts/capture_model_info.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BASE_URL = os.getenv("OPENWEBUI_BASE_URL", "http://localhost:3000/api")
API_KEY = (os.getenv("OPENWEBUI_API_KEY") or "").strip()
MODEL_ID = (os.getenv("TARGET_MODEL") or "modelo-innovatech-2027").strip()


def main() -> int:
    if not API_KEY:
        print("Falta OPENWEBUI_API_KEY en el archivo .env", file=sys.stderr)
        return 1

    headers = {"Authorization": f"Bearer {API_KEY}"}

    models = requests.get(f"{BASE_URL}/models", headers=headers, timeout=60).json()
    print("Modelos expuestos por Open WebUI:")
    for item in sorted(models.get("data", []), key=lambda m: m["id"]):
        print(f"  - {item['id']}")

    model = requests.get(
        f"{BASE_URL}/v1/models/model",
        params={"id": MODEL_ID},
        headers=headers,
        timeout=60,
    ).json()
    print("\nModelo personalizado:")
    print(f"  id          : {model['id']}")
    print(f"  nombre      : {model.get('name')}")
    print(f"  modelo base : {model.get('base_model_id')}")
    print(f"  temperatura : {(model.get('params') or {}).get('temperature')}")

    knowledge = (model.get("meta") or {}).get("knowledge") or []
    print(
        "  knowledge   : "
        + str([(k.get("name"), k.get("id"), k.get("type")) for k in knowledge])
    )

    if knowledge:
        knowledge_id = knowledge[0]["id"]
        result = requests.post(
            f"{BASE_URL}/v1/retrieval/query/collection",
            headers=headers,
            json={
                "collection_names": [knowledge_id],
                "query": "monto del auxilio de conectividad y codigo interno",
                "k": 2,
            },
            timeout=180,
        ).json()
        print("\nRecuperacion vectorial (consulta de prueba):")
        chunks = result.get("documents", [[]])[0]
        if not chunks:
            print("  (sin resultados)")
        for index, chunk in enumerate(chunks, 1):
            preview = " ".join(chunk.split())[:220]
            print(f"  chunk {index}: {preview}...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
