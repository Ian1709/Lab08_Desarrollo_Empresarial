# ENTREGABLE — Laboratorio 08
## API REST de cuestionarios con Django REST Framework

- **Proyecto:** `Lab08_proyecto`
- **Repositorio:** https://github.com/Ian1709/Lab08_Desarrollo_Empresarial
- **Entorno:** Python 3.13.5 · Django 6.1.2 · djangorestframework 3.18.3 · django-filter 26.2
- **Evidencias:** carpeta [`evidencias/`](evidencias/)

---

## 1. Estructura del proyecto (estructura del curso)

```
Lab08_proyecto/
├── config/                     # paquete de configuración
│   ├── settings.py             # INSTALLED_APPS + bloque REST_FRAMEWORK
│   └── urls.py                 # router de la API bajo /api/
├── quiz/                       # aplicación del cuestionario
│   ├── models.py               # Examen, Pregunta, Opcion
│   ├── serializers.py          # ModelSerializer de los tres recursos
│   ├── filters.py              # filtro por examen
│   ├── views.py                # ModelViewSet de los tres recursos
│   ├── admin.py
│   ├── tests.py                # 8 pruebas
│   ├── management/commands/seed_quiz.py
│   └── migrations/0001_initial.py
├── scripts/demo_api.py         # cliente HTTP externo (pasos 7-10)
├── evidencias/
│   ├── api_navegable.txt       # recorrido de la API navegable (paso 7)
│   └── api_demo.txt            # salida del cliente HTTP externo (pasos 8-10)
├── requirements.txt
└── manage.py
```

---

## 2. Paso 1 — djangorestframework declarado en INSTALLED_APPS

Se instaló `djangorestframework` (y `django-filter`) y se declaró en
`config/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'django_filters',
    'quiz',
]
```

`requirements.txt`:

```
Django==6.1.2
djangorestframework==3.18.3
django-filter==26.2
```

---

## 3. Paso 2 — Bloque REST_FRAMEWORK

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

- **Paginación por defecto:** `PageNumberPagination` con **5** elementos por
  página.
- **Permisos de partida:** `AllowAny` (acceso abierto para poder recorrer toda
  la API en la práctica; en producción se endurecería, por ejemplo, a
  `IsAuthenticatedOrReadOnly`).

---

## 4. Paso 3 — Serializadores (ModelSerializer)

| Serializador | Modelo | Campos expuestos | Campos de solo lectura |
| ------------ | ------ | ---------------- | ---------------------- |
| `ExamenSerializer` | `Examen` | `id`, `titulo`, `descripcion`, `activo`, `fecha_creacion` | `id`, `fecha_creacion` |
| `PreguntaSerializer` | `Pregunta` | `id`, `examen`, `enunciado`, `orden`, `opciones` | `id` |
| `OpcionSerializer` | `Opcion` | `id`, `pregunta`, `texto`, `es_correcta` | `id` |
| `OpcionAnidadaSerializer` | `Opcion` | `id`, `texto`, `es_correcta` | `id` |

---

## 5. Paso 4 — Cómo viajan las relaciones (decisión y justificación)

| Relación | Cómo viaja | Por qué |
| -------- | ---------- | ------- |
| `Examen` → `Pregunta` | La pregunta referencia al examen **por identificador**: `PreguntaSerializer` expone `examen` como `PrimaryKeyRelatedField` (`"examen": 7`). | Evita anidar listas grandes y permite consultar las preguntas de un examen con su propio recurso y filtro (`/api/preguntas/?examen=7`). |
| `Pregunta` → `Opcion` | Las opciones viajan **anidadas** dentro de la pregunta: `"opciones": [ {...}, {...} ]`, y son escribibles. | Una opción no tiene sentido sin su pregunta; al crear o editar una pregunta se crean/editan sus opciones en la misma operación. Al anidarlas, la opción **no** expone `pregunta` (`OpcionAnidadaSerializer`). |
| `Opcion` (recurso propio) | El recurso `/api/opciones/` sí expone `pregunta` **por identificador**, porque una opción suelta debe poder indicar a qué pregunta pertenece. | Permite el CRUD independiente de opciones. |

En resumen: **las opciones se anidan dentro de la pregunta y el examen se
refiere por identificador.**

---

## 6. Paso 5 — Validación propia del serializador de pregunta

En `PreguntaSerializer.validate` **no se acepta una pregunta sin exactamente una
opción correcta** (ni 0 ni 2+ correctas). Si el `PATCH` no envía opciones, se
cuentan las que ya están guardadas.

```python
def validate(self, attrs):
    if 'opciones' in attrs:
        correctas = sum(1 for o in attrs['opciones'] if o.get('es_correcta'))
    elif self.instance is not None:
        correctas = self.instance.opciones.filter(es_correcta=True).count()
    else:
        correctas = 0
    if correctas != 1:
        raise serializers.ValidationError({'opciones': (
            'La pregunta debe tener exactamente una opción correcta '
            f'(se recibieron {correctas}).')})
    return attrs
```

---

## 7. Paso 6 — Conjuntos de vistas y enrutador

`quiz/views.py`:

```python
class ExamenViewSet(viewsets.ModelViewSet): ...
class PreguntaViewSet(viewsets.ModelViewSet):
    filterset_class = PreguntaFilter
    search_fields = ['enunciado']
class OpcionViewSet(viewsets.ModelViewSet): ...
```

`config/urls.py`:

```python
router = DefaultRouter()
router.register(r'examenes', ExamenViewSet, basename='examen')
router.register(r'preguntas', PreguntaViewSet, basename='pregunta')
router.register(r'opciones', OpcionViewSet, basename='opcion')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
```

---

## 8. Paso 7 — API navegable (códigos de estado)

Evidencia completa en [`evidencias/api_navegable.txt`](evidencias/api_navegable.txt).

| Operación | Petición | Código |
| --------- | -------- | ------ |
| Listar | `GET /api/examenes/` | **200 OK** |
| Ver detalle | `GET /api/examenes/11/` | **200 OK** |
| Crear (formulario HTML) | `POST /api/examenes/` | **201 Created** |
| Modificar parcialmente (Raw data) | `PATCH /api/examenes/11/` | **200 OK** |
| Eliminar | `DELETE /api/examenes/11/` | **204 No Content** |

En la creación (POST) la API navegable devolvió el objeto creado con su `id`
generado; en el `PATCH` se conservó el `titulo` y solo cambió `descripcion`.

---

## 9. Paso 8 — Cliente HTTP externo (mismo resultado)

Cliente: [`scripts/demo_api.py`](scripts/demo_api.py) (usa `urllib` de la
biblioteca estándar). Se ejecuta con `py scripts/demo_api.py` con el servidor
levantado. Evidencia completa en [`evidencias/api_demo.txt`](evidencias/api_demo.txt).

| Operación | Método y ruta | Código |
| --------- | ------------- | ------ |
| Listar exámenes | `GET /api/examenes/` | **200** |
| Crear examen | `POST /api/examenes/` | **201** |
| Detalle de examen | `GET /api/examenes/{id}/` | **200** |
| Reemplazar examen | `PUT /api/examenes/{id}/` | **200** |
| Modificar parcial examen | `PATCH /api/examenes/{id}/` | **200** |
| Crear pregunta (opciones anidadas) | `POST /api/preguntas/` | **201** |
| Detalle de pregunta | `GET /api/preguntas/{id}/` | **200** |
| Modificar parcial pregunta | `PATCH /api/preguntas/{id}/` | **200** |
| Reemplazar pregunta | `PUT /api/preguntas/{id}/` | **200** |
| Crear opción | `POST /api/opciones/` | **201** |
| Modificar parcial opción | `PATCH /api/opciones/{id}/` | **200** |
| Eliminar opción | `DELETE /api/opciones/{id}/` | **204** |
| Eliminar pregunta | `DELETE /api/preguntas/{id}/` | **204** |
| Eliminar examen | `DELETE /api/examenes/{id}/` | **204** |

Los códigos y los cuerpos coinciden con los de la API navegable.

---

## 10. Paso 9 — Errores provocados a propósito

| # | Error | Petición | Código | Mensaje de la API |
| - | ----- | -------- | ------ | ----------------- |
| 1 | Campo obligatorio ausente (falta `enunciado`) | `POST /api/preguntas/` | **400 Bad Request** | `{"enunciado":["This field is required."]}` |
| 2 | Tipo incorrecto (`examen` texto, `orden` texto) | `POST /api/preguntas/` | **400 Bad Request** | `{"examen":["Incorrect type. Expected pk value, received str."],"orden":["A valid integer is required."]}` |
| 3a | Validación de opción correcta: **ninguna** correcta | `POST /api/preguntas/` | **400 Bad Request** | `{"opciones":["La pregunta debe tener exactamente una opción correcta (se recibieron 0)."]}` |
| 3b | Validación de opción correcta: **dos** correctas | `POST /api/preguntas/` | **400 Bad Request** | `{"opciones":["La pregunta debe tener exactamente una opción correcta (se recibieron 2)."]}` |

---

## 11. Paso 10 — Filtrado, búsqueda y paginación

- **Filtrado por examen:** `GET /api/preguntas/?examen=7` → **200**, `count=7`.
- **Búsqueda por texto del enunciado:** `GET /api/preguntas/?search=Python` →
  **200**, `count=1`.
- **Paginación (tamaño 5):**
  - `GET /api/preguntas/` → **200**, `count=10`, `results=5`,
    `next=.../?page=2`.
  - `GET /api/preguntas/?page=2` → **200**, `results=5`, `previous=.../`.
  - `GET /api/preguntas/?examen=7&page=2` → **200**, `count=7`, `results=2`
    (filtrado y paginación combinados).

Cuando hay más de una página, la respuesta incluye los enlaces `next` y
`previous`, y `count` refleja el total de elementos del conjunto **filtrado**.

---

## 12. Paso 11 — Tabla de la API

Base: `http://127.0.0.1:8000`  ·  `Content-Type: application/json`

### Exámenes

| Recurso | Dirección | Método | Cuerpo de ejemplo | Respuesta esperada |
| ------- | --------- | ------ | ----------------- | ------------------ |
| Exámenes | `/api/examenes/` | GET | — | `200` `{"count":2,"next":null,"previous":null,"results":[...]}` |
| Exámenes | `/api/examenes/` | POST | `{"titulo":"Cuestionario de prueba","descripcion":"...","activo":true}` | `201` objeto con `id` y `fecha_creacion` |
| Examen | `/api/examenes/{id}/` | GET | — | `200` `{"id":7,"titulo":"...","descripcion":"...","activo":true,"fecha_creacion":"..."}` |
| Examen | `/api/examenes/{id}/` | PUT | `{"titulo":"Nuevo","descripcion":"...","activo":false}` | `200` objeto actualizado |
| Examen | `/api/examenes/{id}/` | PATCH | `{"activo":true}` | `200` objeto con solo el campo cambiado |
| Examen | `/api/examenes/{id}/` | DELETE | — | `204` sin cuerpo |

### Preguntas

| Recurso | Dirección | Método | Cuerpo de ejemplo | Respuesta esperada |
| ------- | --------- | ------ | ----------------- | ------------------ |
| Preguntas | `/api/preguntas/` | GET | — | `200` paginado, cada pregunta con `examen` (id) y `opciones` anidadas |
| Preguntas (filtro) | `/api/preguntas/?examen={id}` | GET | — | `200` solo las preguntas del examen |
| Preguntas (búsqueda) | `/api/preguntas/?search={texto}` | GET | — | `200` coincidencias por enunciado |
| Preguntas | `/api/preguntas/` | POST | `{"examen":7,"enunciado":"¿Capital de Francia?","orden":1,"opciones":[{"texto":"París","es_correcta":true},{"texto":"Roma","es_correcta":false}]}` | `201` pregunta con opciones creadas |
| Pregunta | `/api/preguntas/{id}/` | GET | — | `200` pregunta con opciones |
| Pregunta | `/api/preguntas/{id}/` | PUT | cuerpo anterior completo | `200` pregunta reemplazada (opciones reemplazadas) |
| Pregunta | `/api/preguntas/{id}/` | PATCH | `{"orden":2}` | `200` solo cambia el orden |
| Pregunta | `/api/preguntas/{id}/` | DELETE | — | `204` (borra en cascada sus opciones) |

### Opciones

| Recurso | Dirección | Método | Cuerpo de ejemplo | Respuesta esperada |
| ------- | --------- | ------ | ----------------- | ------------------ |
| Opciones | `/api/opciones/` | GET | — | `200` paginado |
| Opciones | `/api/opciones/` | POST | `{"pregunta":22,"texto":"Marsella","es_correcta":false}` | `201` `{"id":91,"pregunta":22,"texto":"Marsella","es_correcta":false}` |
| Opción | `/api/opciones/{id}/` | GET | — | `200` opción |
| Opción | `/api/opciones/{id}/` | PUT | `{"pregunta":22,"texto":"Niza","es_correcta":false}` | `200` opción actualizada |
| Opción | `/api/opciones/{id}/` | PATCH | `{"texto":"Niza"}` | `200` opción con el texto cambiado |
| Opción | `/api/opciones/{id}/` | DELETE | — | `204` sin cuerpo |

### Errores esperados

| Dirección | Método | Cuerpo de ejemplo | Respuesta esperada |
| --------- | ------ | ----------------- | ------------------ |
| `/api/preguntas/` | POST | `{"examen":7,"opciones":[{"texto":"Única","es_correcta":true}]}` (sin `enunciado`) | `400` `{"enunciado":["This field is required."]}` |
| `/api/preguntas/` | POST | `{"examen":"no-es-id","enunciado":"x","orden":"primero","opciones":[...]}` | `400` error de tipo en `examen` y `orden` |
| `/api/preguntas/` | POST | pregunta con 0 o 2 opciones `es_correcta:true` | `400` `{"opciones":["La pregunta debe tener exactamente una opción correcta (se recibieron 0)."]}` |

---

## 13. Paso 12 — Entrega

- **Repositorio del equipo:** https://github.com/Ian1709/Lab08_Desarrollo_Empresarial
  (rama `main`; historial con un commit por paso).
- **Campus virtual:** subir este `ENTREGABLE.md` (y opcionalmente
  `evidencias/`).

### Cómo reproducir

```bash
py -m pip install -r requirements.txt
py manage.py migrate
py manage.py seed_quiz --reset          # datos de ejemplo
py manage.py runserver                  # http://127.0.0.1:8000/api/
py scripts/demo_api.py                  # cliente HTTP externo (en otra consola)
py manage.py test quiz                  # 8 pruebas
```
