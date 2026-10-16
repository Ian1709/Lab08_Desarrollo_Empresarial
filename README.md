# Lab08_proyecto

Laboratorio 08 — API REST de cuestionarios con Django REST Framework.

Proyecto Django con la estructura del curso:

- `config/` — paquete de configuración del proyecto.
- `quiz/` — aplicación de cuestionarios (Examen, Pregunta, Opcion).

## Requisitos

```
pip install -r requirements.txt
```

## Puesta en marcha

```
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py seed_quiz --reset
py manage.py runserver
```

La API queda disponible en `http://127.0.0.1:8000/api/`.

## Recursos

| Recurso    | Prefijo de ruta |
| ---------- | --------------- |
| Exámenes   | `/api/examenes/` |
| Preguntas  | `/api/preguntas/` |
| Opciones   | `/api/opciones/` |

## Comprobaciones

```
py manage.py test quiz          # pruebas unitarias y de API
py scripts/demo_api.py          # cliente HTTP externo (con el servidor levantado)
```

Consulta el archivo [`ENTREGABLE.md`](ENTREGABLE.md) para la tabla completa de la API,
las decisiones sobre las relaciones, las evidencias de las operaciones y el
registro de errores.
