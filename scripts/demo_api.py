"""Cliente HTTP externo para recorrer la API de cuestionarios.

Realiza las mismas operaciones que la API navegable (listar, ver detalle,
crear, modificar parcialmente, modificar y eliminar) y provoca tres errores
a propósito, anotando el código de estado de cada respuesta.

Uso:
    py scripts/demo_api.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8000/api'
SALIDA = []
TIMEOUT = 10


def log(texto: str = '') -> None:
    SALIDA.append(texto)
    print(texto)


def peticion(metodo: str, ruta: str, cuerpo=None):
    """Devuelve (codigo, texto_cuerpo). Envía y recibe JSON."""
    datos = None
    cabeceras = {'Accept': 'application/json'}
    if cuerpo is not None:
        datos = json.dumps(cuerpo).encode('utf-8')
        cabeceras['Content-Type'] = 'application/json'

    req = urllib.request.Request(
        BASE + ruta,
        data=datos,
        headers=cabeceras,
        method=metodo,
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode('utf-8')
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode('utf-8')


def muestra(titulo: str, metodo: str, ruta: str, codigo: int, cuerpo: str) -> None:
    log('=' * 78)
    log(f'{titulo}')
    log(f'{metodo} {BASE}{ruta}')
    log(f'-> HTTP {codigo}')
    cuerpo_legible = cuerpo.strip()
    if cuerpo_legible:
        log(cuerpo_legible[:900])
    log()


def main() -> int:
    # ---------------------------------------------------------------- listar
    codigo, cuerpo = peticion('GET', '/examenes/')
    muestra('PASO 7/8.1  Listar exámenes', 'GET', '/examenes/', codigo, cuerpo)
    examenes = json.loads(cuerpo)['results']
    examen_base = examenes[0]['id'] if examenes else None

    # ---------------------------------------------------------------- crear
    nuevo_examen = {
        'titulo': 'Cuestionario de prueba',
        'descripcion': 'Creado desde el cliente HTTP externo.',
        'activo': True,
    }
    codigo, cuerpo = peticion('POST', '/examenes/', nuevo_examen)
    muestra('PASO 7/8.2  Crear examen', 'POST', '/examenes/', codigo, cuerpo)
    examen_id = json.loads(cuerpo)['id'] if codigo == 201 else None

    # -------------------------------------------------------------- detalle
    codigo, cuerpo = peticion('GET', f'/examenes/{examen_id}/')
    muestra('PASO 7/8.3  Detalle del examen', 'GET', f'/examenes/{examen_id}/', codigo, cuerpo)

    # ------------------------------------------------------- modificar (PUT)
    completo = {
        'titulo': 'Cuestionario de prueba (PUT)',
        'descripcion': 'Reemplazo completo vía PUT.',
        'activo': False,
    }
    codigo, cuerpo = peticion('PUT', f'/examenes/{examen_id}/', completo)
    muestra('PASO 7/8.4  Modificar examen (PUT)', 'PUT', f'/examenes/{examen_id}/', codigo, cuerpo)

    # ------------------------------------------- modificar parcial (PATCH)
    codigo, cuerpo = peticion('PATCH', f'/examenes/{examen_id}/', {'activo': True})
    muestra('PASO 7/8.5  Modificar parcialmente el examen (PATCH)', 'PATCH',
            f'/examenes/{examen_id}/', codigo, cuerpo)

    # ------------------------------------------------ crear pregunta anidada
    nueva_pregunta = {
        'examen': examen_id,
        'enunciado': '¿Cuál es la capital de Francia?',
        'orden': 1,
        'opciones': [
            {'texto': 'París', 'es_correcta': True},
            {'texto': 'Madrid', 'es_correcta': False},
            {'texto': 'Roma', 'es_correcta': False},
        ],
    }
    codigo, cuerpo = peticion('POST', '/preguntas/', nueva_pregunta)
    muestra('PASO 7/8.6  Crear pregunta con opciones anidadas', 'POST',
            '/preguntas/', codigo, cuerpo)
    pregunta_id = json.loads(cuerpo)['id'] if codigo == 201 else None

    # ------------------------------------------------- detalle de pregunta
    codigo, cuerpo = peticion('GET', f'/preguntas/{pregunta_id}/')
    muestra('PASO 7/8.7  Detalle de la pregunta', 'GET',
            f'/preguntas/{pregunta_id}/', codigo, cuerpo)

    # ---------------------------------------- modificar parcial la pregunta
    codigo, cuerpo = peticion('PATCH', f'/preguntas/{pregunta_id}/', {'orden': 2})
    muestra('PASO 7/8.8  Modificar parcialmente la pregunta (PATCH)', 'PATCH',
            f'/preguntas/{pregunta_id}/', codigo, cuerpo)

    # ------------------------------------------- modificar pregunta (PUT)
    codigo, cuerpo = peticion('PUT', f'/preguntas/{pregunta_id}/', {
        'examen': examen_id,
        'enunciado': '¿Cuál es la capital de Francia? (actualizado)',
        'orden': 2,
        'opciones': [
            {'texto': 'París', 'es_correcta': True},
            {'texto': 'Lyon', 'es_correcta': False},
        ],
    })
    muestra('PASO 7/8.9  Modificar la pregunta (PUT)', 'PUT',
            f'/preguntas/{pregunta_id}/', codigo, cuerpo)

    # -------------------------------------------------- crear una opción
    codigo, cuerpo = peticion('POST', '/opciones/', {
        'pregunta': pregunta_id,
        'texto': 'Marsella',
        'es_correcta': False,
    })
    muestra('PASO 7/8.10  Crear opción', 'POST', '/opciones/', codigo, cuerpo)
    opcion_id = json.loads(cuerpo)['id'] if codigo == 201 else None

    # --------------------------------------------- modificar parcial opción
    codigo, cuerpo = peticion('PATCH', f'/opciones/{opcion_id}/', {'texto': 'Niza'})
    muestra('PASO 7/8.11  Modificar parcialmente la opción (PATCH)', 'PATCH',
            f'/opciones/{opcion_id}/', codigo, cuerpo)

    # ---------------------------------------------------- eliminar opción
    codigo, cuerpo = peticion('DELETE', f'/opciones/{opcion_id}/')
    muestra('PASO 7/8.12  Eliminar opción', 'DELETE',
            f'/opciones/{opcion_id}/', codigo, cuerpo)

    # -------------------------------------------------- eliminar pregunta
    codigo, cuerpo = peticion('DELETE', f'/preguntas/{pregunta_id}/')
    muestra('PASO 7/8.13  Eliminar pregunta', 'DELETE',
            f'/preguntas/{pregunta_id}/', codigo, cuerpo)

    # -------------------------------------------------- eliminar examen
    codigo, cuerpo = peticion('DELETE', f'/examenes/{examen_id}/')
    muestra('PASO 7/8.14  Eliminar examen', 'DELETE',
            f'/examenes/{examen_id}/', codigo, cuerpo)

    # ============================================================= ERRORES
    log('#' * 78)
    log('PASO 9.  ERRORES PROVOCADOS A PROPÓSITO')
    log('#' * 78)

    # Error 1: campo obligatorio ausente (falta el enunciado).
    codigo, cuerpo = peticion('POST', '/preguntas/', {
        'examen': examen_base,
        'opciones': [{'texto': 'Única', 'es_correcta': True}],
    })
    muestra('ERROR 1  Campo obligatorio ausente (falta "enunciado")', 'POST',
            '/preguntas/', codigo, cuerpo)

    # Error 2: tipo incorrecto (examen como texto, orden como texto).
    codigo, cuerpo = peticion('POST', '/preguntas/', {
        'examen': 'esto-no-es-un-id',
        'enunciado': 'Pregunta con tipos incorrectos',
        'orden': 'primero',
        'opciones': [{'texto': 'A', 'es_correcta': True}],
    })
    muestra('ERROR 2  Tipo incorrecto ("examen" y "orden")', 'POST',
            '/preguntas/', codigo, cuerpo)

    # Error 3: la validación de la opción correcta (ninguna correcta).
    codigo, cuerpo = peticion('POST', '/preguntas/', {
        'examen': examen_base,
        'enunciado': 'Pregunta sin opción correcta',
        'opciones': [
            {'texto': 'A', 'es_correcta': False},
            {'texto': 'B', 'es_correcta': False},
        ],
    })
    muestra('ERROR 3a  Ninguna opción correcta', 'POST', '/preguntas/', codigo, cuerpo)

    # Error 3b: dos opciones correctas.
    codigo, cuerpo = peticion('POST', '/preguntas/', {
        'examen': examen_base,
        'enunciado': 'Pregunta con dos opciones correctas',
        'opciones': [
            {'texto': 'A', 'es_correcta': True},
            {'texto': 'B', 'es_correcta': True},
        ],
    })
    muestra('ERROR 3b  Dos opciones correctas', 'POST', '/preguntas/', codigo, cuerpo)

    # ================================================ FILTRADO Y PAGINACIÓN
    log('#' * 78)
    log('PASO 10.  FILTRADO, BÚSQUEDA Y PAGINACIÓN')
    log('#' * 78)

    codigo, cuerpo = peticion('GET', f'/preguntas/?examen={examen_base}')
    datos = json.loads(cuerpo)
    muestra(f'Filtrado por examen (?examen={examen_base}) — count={datos.get("count")}',
            'GET', f'/preguntas/?examen={examen_base}', codigo, cuerpo)

    codigo, cuerpo = peticion('GET', '/preguntas/?search=Python')
    datos = json.loads(cuerpo)
    muestra(f'Búsqueda por enunciado (?search=Python) — count={datos.get("count")}',
            'GET', '/preguntas/?search=Python', codigo, cuerpo)

    codigo, cuerpo = peticion('GET', '/preguntas/')
    datos = json.loads(cuerpo)
    muestra(
        f'Paginación página 1 — count={datos.get("count")} '
        f'results={len(datos.get("results", []))} next={datos.get("next")}',
        'GET', '/preguntas/', codigo, cuerpo)

    codigo, cuerpo = peticion('GET', '/preguntas/?page=2')
    datos = json.loads(cuerpo)
    muestra(
        f'Paginación página 2 — count={datos.get("count")} '
        f'results={len(datos.get("results", []))} previous={datos.get("previous")}',
        'GET', '/preguntas/?page=2', codigo, cuerpo)

    codigo, cuerpo = peticion('GET', f'/preguntas/?examen={examen_base}&page=2')
    datos = json.loads(cuerpo)
    muestra(
        f'Filtrado + paginación (?examen={examen_base}&page=2) — count={datos.get("count")} '
        f'results={len(datos.get("results", []))}',
        'GET', f'/preguntas/?examen={examen_base}&page=2', codigo, cuerpo)

    with open('evidencias/api_demo.txt', 'w', encoding='utf-8') as archivo:
        archivo.write('\n'.join(SALIDA))
    log('Evidencia escrita en evidencias/api_demo.txt')
    return 0


if __name__ == '__main__':
    sys.exit(main())
