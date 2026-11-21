# Evidencias de ejecución

## `terminal/`

Salidas reales capturadas con `Tee-Object` durante la ejecución del laboratorio:

| Archivo | Contenido |
|---|---|
| `01-docker-compose-ps.txt` | Estado de los servicios `ollama` y `open-webui` |
| `02-docker-ps.txt` | Contenedores activos, imagen y puertos publicados |
| `03-ollama-list.txt` | Modelos disponibles en Ollama (`qwen2.5:1.5b-instruct`) |
| `04-modelos-openwebui.txt` | Modelos expuestos, configuración del modelo y recuperación vectorial |
| `05-test-openwebui-api.txt` | Ejecución de `test_openwebui_api.py` con la API Key |
| `06-bootstrap.txt` | Salida de `scripts/bootstrap_openwebui.py` |
| `07-evaluacion.txt` | Resumen de `evaluate_rag.py` sobre las 8 preguntas |
| `08-evaluacion-detalle.jsonl` | Respuestas completas de cada caso evaluado |

## `capturas/`

| Archivo | Contenido |
|---|---|
| `01-workspace-modelos.jpeg` | *Workspace → Models* con “Asistente Innovatech 2027” |
| `02-workspace-conocimiento.jpeg` | *Workspace → Knowledge* con “Politica Innovatech 2027” |
| `03-chat-rag-auxilio.jpeg` | Respuesta con monto del auxilio, código interno y fuente citada |
| `04-chat-fuera-de-alcance.jpeg` | Rechazo de una pregunta fuera de la política |

> Las capturas se tomaron de la instancia local después de ejecutar el
> laboratorio. Ninguna imagen contiene la API Key completa.
