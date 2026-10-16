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
py manage.py migrate
py manage.py runserver
```

La API queda disponible en `http://127.0.0.1:8000/api/`.

## Recursos

| Recurso    | Prefijo de ruta |
| ---------- | --------------- |
| Exámenes   | `/api/examenes/` |
| Preguntas  | `/api/preguntas/` |
| Opciones   | `/api/opciones/` |

Consulta el archivo [`ENTREGABLE.md`](ENTREGABLE.md) para la tabla completa de la API,
las evidencias de las operaciones y el registro de errores.
