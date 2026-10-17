# Lab08_proyecto

Laboratorio 08 — API REST de cuestionarios con Django REST Framework, más el **lab extra headless**: contrato OpenAPI, cliente de consola y frontera del agente de IA.

Proyecto Django con la estructura del curso:

- `config/` — paquete de configuración del proyecto (incluye el contrato OpenAPI).
- `quiz/` — aplicación de cuestionarios (Examen, Pregunta, Opcion) y la regla de permisos por rol.
- `agent/` — pasarela cerrada entre un modelo de lenguaje y la API (Parte 4 del lab extra).
- `quizctl.py` — cliente de consola sin pantalla (Parte 2 del lab extra).
- `scripts/demo_api.py` — cliente HTTP externo con urllib (pasos 7-10 del Lab 8).
- `evidencias/` — salidas reales de la API navegable y del cliente externo.

## Requisitos

```
pip install -r requirements.txt
```

## Puesta en marcha

```
python manage.py migrate
python manage.py seed_quiz          # datos de ejemplo + usuarios «profe» y «agente», con su token
python manage.py runserver
```

La API queda disponible en `http://127.0.0.1:8000/api/` y su contrato en `http://127.0.0.1:8000/api/docs/`.

**La API exige identidad** (Parte 3 del lab extra): sin token responde `401`. `seed_quiz` imprime los tokens de la persona (`profe`, que puede todo) y del agente (`agente`, que no puede borrar). Para usar la API navegable desde el navegador, entra con `profe` / `profe12345` en `/api-auth/login/`.

## Recursos

| Recurso | Prefijo de ruta |
| ------- | --------------- |
| Exámenes | `/api/examenes/` |
| Preguntas | `/api/preguntas/` |
| Opciones | `/api/opciones/` |
| Contrato OpenAPI | `/api/schema/` (y `/api/docs/` para verlo) |

## Comprobaciones

```
python manage.py test                # pruebas: Lab 8 + cliente de consola + permisos + agente
python scripts/demo_api.py           # cliente HTTP externo (con el servidor levantado y QUIZ_TOKEN)
python quizctl.py examenes list      # cliente de consola (con QUIZ_TOKEN)
python -m agent --intent '{"op": "examenes_list"}'   # pasarela del agente (con QUIZ_TOKEN_AGENTE)
```

Consulta [`ENTREGABLE.md`](ENTREGABLE.md) para la tabla completa de la API del Lab 8 y [`HEADLESS.md`](HEADLESS.md) para las cuatro partes del lab extra (contrato, cliente de consola, permisos y frontera del agente).
