"""Prueba de consumo del modelo personalizado de Open WebUI via API.

Usa el endpoint compatible con OpenAI que expone Open WebUI en
http://localhost:3000/api y una API Key creada en Settings -> Account -> API Keys.

El modelo se toma de TARGET_MODEL (archivo .env), por defecto
"modelo-innovatech-2027". Ese modelo tiene vinculada la base de conocimiento
creada en el Lab 2 (politica_innovatech_2027.txt), por lo que la recuperacion
vectorial ocurre del lado del servidor: no hay que adjuntar archivos en el
mensaje.

Uso:
    python test_openwebui_api.py
    python test_openwebui_api.py "Cual es el codigo del auxilio de conectividad?"
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent / ".env")

# ==============================================================================
# 1. CONFIGURACION DE CONEXION A OPEN WEBUI
# ==============================================================================
OPENWEBUI_BASE_URL = os.getenv("OPENWEBUI_BASE_URL", "http://localhost:3000/api")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY", "").strip().strip('"').strip("'")
MODELO_A_USAR = (
    os.getenv("TARGET_MODEL", "modelo-innovatech-2027").strip().strip('"').strip("'")
)

client = OpenAI(base_url=OPENWEBUI_BASE_URL, api_key=OPENWEBUI_API_KEY)

# Preguntas de demostracion del laboratorio.
PREGUNTAS = [
    "Hola, presentate brevemente y dime que tipo de asistencia puedes brindarme.",
    "Cual es el monto del auxilio de conectividad y cual es el codigo interno "
    "para solicitarlo?",
    "Cual es el horario de la cafeteria los sabados?",
]


def consultar_modelo(prompt_usuario: str) -> bool:
    if not OPENWEBUI_API_KEY:
        print(
            "Falta OPENWEBUI_API_KEY. Ponla en el archivo .env "
            "(junto a este script) o expórtala en la terminal."
        )
        return False

    print("=" * 78)
    print(f"Pregunta: {prompt_usuario}")
    print("-" * 78)

    inicio = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=MODELO_A_USAR,
            messages=[{"role": "user", "content": prompt_usuario}],
            temperature=0.0,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error al conectar con Open WebUI: {exc}")
        return False

    latencia = time.perf_counter() - inicio
    respuesta = response.choices[0].message.content or ""
    print(respuesta.strip())
    print("-" * 78)
    print(f"Modelo: {MODELO_A_USAR} | Latencia: {latencia:.2f}s", end="")
    if response.usage:
        print(
            f" | Tokens prompt/completion: "
            f"{response.usage.prompt_tokens}/{response.usage.completion_tokens}"
        )
    else:
        print()
    print()
    return True


def main() -> int:
    if len(sys.argv) > 1:
        preguntas = [" ".join(sys.argv[1:])]
    else:
        preguntas = PREGUNTAS

    print(f"Conectando a {OPENWEBUI_BASE_URL} | Modelo: {MODELO_A_USAR}\n")
    resultados = [consultar_modelo(p) for p in preguntas]
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
