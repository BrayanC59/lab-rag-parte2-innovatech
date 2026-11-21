# Guía paso a paso de la actividad

Esta guía mapea cada indicación del documento `actividad rag-parte dos.txt` con
los comandos ejecutados y la evidencia generada.

> Todos los comandos se ejecutan desde la raíz del repositorio, en PowerShell,
> salvo que se indique lo contrario.

---

## Paso 1. Clonar el repositorio de ejemplo

```powershell
git clone https://github.com/FerchoRV/ejemplo-rag-openwebui.git repo-original
```

Se usó como referencia el `docker-compose.yml`, `test_openwebui_api.py`,
`evaluate_rag.py` y el `.env.example` del repositorio del curso. Los archivos del
producto final viven en la raíz de este repositorio.

## Paso 2. Crear el entorno virtual con los requirements

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

o simplemente:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

> **Corrección:** el repo de ejemplo fija `openai==3.53.0`, una versión que no
> existe en PyPI. En este repo se usa `openai>=1.60,<3`; la ejecución real quedó
> con `openai 2.54.0` y Python 3.12.

## Paso 3. Levantar el laboratorio (Ollama + Open WebUI)

```powershell
docker compose up -d
docker ps
docker logs --tail 50 open-webui-lab
```

El `docker-compose.yml` publica:

- Open WebUI en <http://localhost:3000> (contenedor `open-webui-lab`).
- Ollama en <http://localhost:11434> (contenedor `ollama-rag-lab`).

El modelo base se descarga una sola vez:

```powershell
docker exec ollama-rag-lab ollama pull qwen2.5:1.5b-instruct
```

## Paso 4. Modelo personalizado con la base de conocimiento del Lab 2

La base de conocimiento es `knowledge/politica_innovatech_2027.txt`, la misma
que se usó en el Lab 2. El script `scripts/bootstrap_openwebui.py`:

1. Espera a que Open WebUI esté listo.
2. Inicia sesión como administrador (o crea el primer usuario).
3. Crea la knowledge **“Politica Innovatech 2027”** y sube/indexa el documento.
4. Crea el modelo **`modelo-innovatech-2027`** con
   `base_model_id = qwen2.5:1.5b-instruct` y la knowledge vinculada en
   `meta.knowledge` con `type = collection`.
5. Configura una **plantilla RAG estricta** (solo responde con el contexto).
6. Genera la API Key y la escribe en `.env`.

```powershell
.\.venv\Scripts\python.exe scripts\bootstrap_openwebui.py
```

También se puede hacer a mano desde la interfaz:

1. *Workspace → Knowledge → +* y subir el `.txt`.
2. *Workspace → Models → +*: elegir `qwen2.5:1.5b-instruct`, poner ID
   `modelo-innovatech-2027`, nombre y descripción.
3. En la configuración del modelo, sección **Knowledge**, adjuntar
   “Politica Innovatech 2027”.
4. Guardar y verificar que la visibilidad sea pública.
5. En *Admin Settings → Documents*, revisar que la plantilla RAG sea la
   estricta (solo responde con el contexto).

## Paso 5. Crear la API Key

En la interfaz: *Settings → Account → API Keys → Create new key*.

En el flujo automatizado la crea el bootstrap con
`POST /api/v1/auths/api_key` y la escribe en `.env`:

```text
OPENWEBUI_API_KEY=sk-...
```

La key **no se versiona** (`.env` está en `.gitignore`).

## Paso 6. Ajustar el ID del modelo y la variable de la API Key

Archivo `.env`:

```dotenv
OPENWEBUI_BASE_URL=http://localhost:3000/api
OPENWEBUI_API_KEY=sk-...
TARGET_MODEL=modelo-innovatech-2027
JUDGE_MODEL=
```

El ID debe coincidir exactamente con el de *Workspace → Models*. Si el modelo o
la knowledge no son visibles para el dueño de la key, el RAG no recupera
contexto.

## Paso 7. Ejecutar `test_openwebui_api.py`

```powershell
$env:PYTHONUTF8=1
.\.venv\Scripts\python.exe test_openwebui_api.py
```

Se prueba el saludo, el auxilio de conectividad (dato que está en la política) y
el horario de la cafetería (dato que **no** está, para verificar que no inventa).

También se puede enviar una pregunta puntual:

```powershell
.\.venv\Scripts\python.exe test_openwebui_api.py "¿Cuál es el código del auxilio de conectividad?"
```

Salida esperada (resumida):

```text
Conectando a http://localhost:3000/api | Modelo: modelo-innovatech-2027

Pregunta: ¿Cuál es el monto del auxilio de conectividad...
El auxilio mensual de conectividad es de $245.000 COP...
Código: #INV-CON-2027
```

## Paso 8. Evidencias y repositorio

- Terminal: `evidence/terminal/`.
- Capturas de Open WebUI: `evidence/capturas/`.
- Resultados de evaluación: `runs/` y `docs/INFORME.md`.

Comandos usados para guardar la salida:

```powershell
docker ps | Tee-Object -FilePath evidence/terminal/01-docker-ps.txt
.\.venv\Scripts\python.exe test_openwebui_api.py 2>&1 |
    Tee-Object -FilePath evidence/terminal/02-test-api.txt
```

Para publicar el repositorio:

```powershell
git init
git add .
git commit -m "Laboratorio RAG parte 2: modelo personalizado y consumo por API"
git branch -M main
git remote add origin https://github.com/<usuario>/lab-rag-parte2-innovatech.git
git push -u origin main
```

## Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| `docker: daemon not running` | Abrir Docker Desktop y esperar a que el motor Linux arranque. |
| Open WebUI en `Restarting` | Revisar `docker logs open-webui-lab`; probar `docker compose pull open-webui` o la versión `main`. |
| `Model not found` en la API | El `TARGET_MODEL` no coincide con el ID de *Workspace → Models* o no es visible para la key. |
| Respuestas sin RAG | La knowledge no es pública / no está vinculada al modelo / el archivo no se indexó. |
| `401` al llamar la API | Se usó el token de sesión del navegador en vez de una API Key `sk-...`. |
| Primera respuesta lenta | El contenedor descarga el modelo de embeddings (all-MiniLM-L6-v2) y Ollama carga el LLM en memoria. |
