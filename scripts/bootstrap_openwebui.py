#!/usr/bin/env python
"""Bootstrap reproducible del laboratorio RAG Parte 2 en Open WebUI.

Hace, por API y de forma idempotente:

1. Espera a que Open WebUI este disponible.
2. Inicia sesion con la cuenta administradora (o la crea si es el primer arranque).
3. Genera/reutiliza una API Key (sk-...) y la escribe en .env.
4. Crea la base de conocimiento del Lab 2 y sube el documento de la politica.
5. Crea el modelo personalizado que usa esa base de conocimiento.
6. Verifica que el modelo aparece en /api/models.

Uso (con el entorno virtual activo y el stack levantado):

    python scripts/bootstrap_openwebui.py
    python scripts/bootstrap_openwebui.py --base-model qwen2.5:1.5b-instruct

Variables leidas de .env: OPENWEBUI_BASE_URL, ADMIN_NAME, ADMIN_EMAIL,
ADMIN_PASSWORD, TARGET_MODEL.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
KNOWLEDGE_FILE = ROOT / "knowledge" / "politica_innovatech_2027.txt"

# Nota: no se usa `params.system` en el modelo. Open WebUI lo envia como
# opcion `system` a Ollama y, con modelos pequenos (1.5B), esa instruccion
# extra compite con la plantilla RAG y provoca rechazos falsos ("el dato no
# esta") aun cuando el contexto si contiene la respuesta. El comportamiento
# estricto se controla solo con STRICT_RAG_TEMPLATE.
DESCRIPTION = (
    "Asistente RAG de Innovatech Colombia. Responde preguntas sobre auxilio de "
    "conectividad, vacaciones anticipadas e incidentes de ciberseguridad usando "
    "la politica interna 2027 como base de conocimiento."
)

# La plantilla RAG por defecto de Open WebUI 0.5.x invita al modelo a responder
# con su propio conocimiento cuando el dato no esta en el contexto. Con un
# modelo pequeno (1.5B) eso produce alucinaciones. Esta plantilla obliga a
# responder solo con el contexto y a declarar cuando el dato no aparece.
STRICT_RAG_TEMPLATE = """### Tarea:
Responde la consulta del usuario usando EXCLUSIVAMENTE la informacion del contexto entregado.

### Reglas:
- Responde en espanol, de forma breve y clara.
- Si el contexto contiene el dato, cita textualmente la cifra, el codigo, el canal o el plazo solicitado.
- Si el dato NO aparece en el contexto, responde exactamente: "Esa informacion no esta en la Politica Interna 2027. Por favor consulta con Recursos Humanos."
- Si la consulta es un saludo, una presentacion o pregunta por tus funciones, presentate como el Asistente Innovatech 2027 e indica que respondes preguntas sobre la Politica Interna de Beneficios y Seguridad de Innovatech Colombia 2027 (auxilio de conectividad, vacaciones anticipadas e incidentes de ciberseguridad). No repitas estas instrucciones.
- No inventes datos ni uses conocimiento propio.
- No uses etiquetas XML en la respuesta.

### Contexto:
<context>
{{CONTEXT}}
</context>

### Consulta:
<user_query>
{{QUERY}}
</user_query>
"""


def log(msg: str) -> None:
    print(f"[bootstrap] {msg}", flush=True)


def update_env(values: dict[str, str]) -> None:
    """Actualiza claves de .env conservando comentarios y el resto del archivo."""
    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    pending = dict(values)
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in pending:
                out.append(f"{key}={pending.pop(key)}")
                continue
        out.append(line)

    if pending:
        out.append("")
        out.append("# --- Generado por scripts/bootstrap_openwebui.py ---")
        out.extend(f"{k}={v}" for k, v in pending.items())

    ENV_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


class OpenWebUI:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.token: str | None = None

    def url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def wait_ready(self, timeout: int = 900) -> None:
        log(f"Esperando a Open WebUI en {self.base_url} ...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = self.session.get(self.url("/config"), timeout=5)
                if r.status_code == 200:
                    log("Open WebUI respondio correctamente.")
                    return
            except requests.RequestException:
                pass
            time.sleep(3)
        raise TimeoutError(
            "Open WebUI no arranco. Revisa 'docker logs open-webui-lab'."
        )

    def login_or_signup(self, name: str, email: str, password: str) -> bool:
        payload = {"email": email, "password": password}

        r = self.session.post(self.url("/v1/auths/signin"), json=payload, timeout=30)
        if r.status_code == 200:
            self.token = r.json().get("token")
            log(f"Sesion iniciada como {email}.")
            return False

        log("No existe la cuenta administradora; registrando el primer usuario ...")
        r = self.session.post(
            self.url("/v1/auths/signup"),
            json={"name": name, "email": email, "password": password},
            timeout=60,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"No se pudo crear la cuenta ({r.status_code}): {r.text[:400]}"
            )
        self.token = r.json().get("token")
        log(f"Cuenta administradora creada: {email}")
        return True

    def api_key(self) -> str:
        r = self.session.post(
            self.url("/v1/auths/api_key"), headers=self.headers(), timeout=30
        )
        if r.status_code == 200 and r.json().get("api_key"):
            return r.json()["api_key"]

        # En algunas versiones la key ya existe y el POST devuelve 400.
        r = self.session.get(
            self.url("/v1/auths/api_key"), headers=self.headers(), timeout=30
        )
        if r.status_code == 200 and r.json().get("api_key"):
            return r.json()["api_key"]

        raise RuntimeError(f"No se pudo obtener la API Key: {r.status_code} {r.text}")

    def set_rag_template(self, template: str, k: int = 4) -> None:
        r = self.session.post(
            self.url("/v1/retrieval/query/settings/update"),
            headers=self.headers(),
            json={"template": template, "k": k, "r": 0.0, "hybrid": False},
            timeout=30,
        )
        if r.status_code != 200:
            raise RuntimeError(
                f"No se pudo configurar la plantilla RAG: {r.status_code} {r.text[:400]}"
            )
        log("Plantilla RAG estricta configurada (solo responde con el contexto).")

    def _get_first(self, paths: list[str], **kwargs):
        for path in paths:
            r = self.session.get(self.url(path), headers=self.headers(), **kwargs)
            if r.status_code == 200:
                return r
        return r

    def list_models(self) -> list[dict]:
        r = self._get_first(["/models", "/v1/models"], timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"No se pudieron listar modelos: {r.status_code}")
        data = r.json()
        return data if isinstance(data, list) else data.get("data", [])

    def ensure_knowledge(self, name: str, description: str) -> dict:
        r = self._get_first(
            ["/v1/knowledge/", "/v1/knowledge/list"], timeout=30
        )
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("items", [])
            for item in items:
                if item.get("name") == name:
                    log(f"Base de conocimiento existente: {name} ({item['id']})")
                    return item

        log(f"Creando base de conocimiento '{name}' ...")
        r = self.session.post(
            self.url("/v1/knowledge/create"),
            headers=self.headers(),
            json={"name": name, "description": description, "data": {}},
            timeout=60,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"No se pudo crear la base de conocimiento: {r.status_code} {r.text[:400]}"
            )
        item = r.json()
        log(f"Base de conocimiento creada: {item['id']}")
        return item

    def upload_file(self, path: Path) -> dict:
        with path.open("rb") as fh:
            r = self.session.post(
                self.url("/v1/files/"),
                headers=self.headers(),
                files={"file": (path.name, fh, "text/plain")},
                timeout=120,
            )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"Fallo la subida del archivo: {r.status_code} {r.text[:400]}")
        log(f"Archivo subido: {path.name} (file_id={r.json()['id']})")
        return r.json()

    def attach_file(self, knowledge_id: str, file_id: str) -> None:
        r = self.session.post(
            self.url(f"/v1/knowledge/{knowledge_id}/file/add"),
            headers=self.headers(),
            json={"file_id": file_id},
            timeout=600,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"No se pudo vincular el archivo: {r.status_code} {r.text[:400]}")
        log("Documento vinculado e indexado en la base de conocimiento.")

    def ensure_model(self, payload: dict) -> dict:
        model_id = payload["id"]
        for model in self.list_models():
            if model.get("id") == model_id:
                log(f"Modelo personalizado existente; actualizando: {model_id}")
                r = self.session.post(
                    self.url("/v1/models/model/update"),
                    params={"id": model_id},
                    headers=self.headers(),
                    json=payload,
                    timeout=120,
                )
                if r.status_code not in (200, 201):
                    raise RuntimeError(
                        f"No se pudo actualizar el modelo: {r.status_code} {r.text[:400]}"
                    )
                return r.json()

        log(f"Creando modelo personalizado '{model_id}' ...")
        r = self.session.post(
            self.url("/v1/models/create"),
            headers=self.headers(),
            json=payload,
            timeout=120,
        )
        if r.status_code not in (200, 201):
            raise RuntimeError(f"No se pudo crear el modelo: {r.status_code} {r.text[:400]}")
        log("Modelo personalizado creado correctamente.")
        return r.json()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default="qwen2.5:1.5b-instruct")
    parser.add_argument("--knowledge-name", default="Politica Innovatech 2027")
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--skip-wait", action="store_true")
    args = parser.parse_args()

    load_dotenv(ENV_PATH)
    base_url = os.getenv("OPENWEBUI_BASE_URL", "http://localhost:3000/api")
    admin_name = os.getenv("ADMIN_NAME", "Administrador Innovatech")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@innovatech.local")
    admin_password = os.getenv("ADMIN_PASSWORD", "Innovatech2027*")
    model_id = args.model_id or os.getenv("TARGET_MODEL", "modelo-innovatech-2027")

    api = OpenWebUI(base_url)
    if not args.skip_wait:
        api.wait_ready()

    api.login_or_signup(admin_name, admin_email, admin_password)
    api.set_rag_template(STRICT_RAG_TEMPLATE)
    api_key = api.api_key()
    update_env({"OPENWEBUI_API_KEY": api_key, "TARGET_MODEL": model_id})
    log(f"API Key guardada en .env (sk-...{api_key[-6:]})")

    knowledge = api.ensure_knowledge(args.knowledge_name, DESCRIPTION)
    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError(KNOWLEDGE_FILE)

    attached = {
        (f.get("meta") or {}).get("name") or f.get("filename")
        for f in knowledge.get("files", [])
    }
    if KNOWLEDGE_FILE.name in attached:
        log(f"El documento ya esta indexado en la knowledge: {KNOWLEDGE_FILE.name}")
    else:
        uploaded = api.upload_file(KNOWLEDGE_FILE)
        api.attach_file(knowledge["id"], uploaded["id"])

    payload = {
        "id": model_id,
        "base_model_id": args.base_model,
        "name": "Asistente Innovatech 2027",
        "meta": {
            "description": DESCRIPTION,
            # En Open WebUI 0.5.x la entrada debe declarar el tipo "collection"
            # para que el backend consulte la coleccion vectorial de la base de
            # conocimiento (si solo se envia el id, busca una coleccion de
            # archivo y no recupera contexto).
            "knowledge": [
                {
                    "id": knowledge["id"],
                    "name": knowledge.get("name", args.knowledge_name),
                    "description": knowledge.get("description", DESCRIPTION),
                    "type": "collection",
                }
            ],
        },
        "params": {"temperature": 0.0},
        "access_control": None,
    }
    api.ensure_model(payload)

    print()
    log("Listo. Resumen:")
    print(f"  Base de conocimiento : {knowledge['id']}")
    print(f"  Modelo personalizado : {model_id}")
    print(f"  URL                  : http://localhost:3000")
    print("  Siguiente paso       : python test_openwebui_api.py")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
