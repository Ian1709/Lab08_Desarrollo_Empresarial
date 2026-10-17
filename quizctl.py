#!/usr/bin/env python
"""quizctl: un cliente sin pantalla para la API de cuestionarios. Sin navegador, sin clics.

Un programa que otro programa puede llamar debe decir qué pasó de forma que una
máquina pueda leerlo: el CÓDIGO DE SALIDA (¿funcionó? ¿por qué no?) y, con
--json, una salida estable.

    python quizctl.py examenes list
    python quizctl.py preguntas list --examen 1 --search python --json
    python quizctl.py preguntas create --examen 1 --text "¿Qué es REST?" --choice "Un estilo:ok" --choice "Un lenguaje"
    python quizctl.py preguntas create --examen 1 --text "..." --choice "a:ok" --choice "b" --dry-run
    python quizctl.py preguntas delete 7
    python quizctl.py ops                      # las operaciones que declara el contrato de la API

Entorno:  QUIZ_URL (por defecto http://127.0.0.1:8000)  y  QUIZ_TOKEN (el token a usar).

Códigos de salida:
    0 ok   1 otro / mal uso   2 validación (400)   3 no permitido (401, 403)
    4 no existe (404)   5 error del servidor (5xx)   6 no hay conexión

Las dos funciones marcadas con TODO(equipo) eran las de la Parte 2 del lab.
"""
import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any

import requests

EXIT_OK, EXIT_OTHER, EXIT_VALIDATION, EXIT_FORBIDDEN, EXIT_NOT_FOUND, EXIT_SERVER, EXIT_NETWORK = range(7)


@dataclass
class Result:
    status: int | None  # HTTP status; None = nothing sent (dry-run); 0 = no connection; -1 = usage error
    data: Any = None
    request: dict = field(default_factory=dict)
    error: str = ""


# --- la Parte 2 del lab: las dos funciones ---------------------------------------------------


def exit_code_for(status: int) -> int:
    """Mapea un código HTTP al código de salida de la tabla de arriba.

    2xx -> 0 · 400 -> 2 · 401 y 403 -> 3 · 404 -> 4 · 5xx -> 5 · cualquier
    otro estado -> 1.
    """
    if 200 <= status < 300:
        return EXIT_OK
    if status == 400:
        return EXIT_VALIDATION
    if status in (401, 403):
        return EXIT_FORBIDDEN
    if status == 404:
        return EXIT_NOT_FOUND
    if 500 <= status < 600:
        return EXIT_SERVER
    return EXIT_OTHER


def build_question_payload(examen: int, texto: str, choices: list[str]) -> dict:
    """Construye el cuerpo del POST /api/preguntas/ desde la línea de comandos.

    `choices` son cadenas; una que termina en ':ok' es la correcta:
        ["Un estilo:ok", "Un lenguaje"]  ->
        {"examen": examen, "enunciado": texto,
         "opciones": [{"texto": "Un estilo", "es_correcta": True},
                      {"texto": "Un lenguaje", "es_correcta": False}]}
    NO se valida aquí (cuántas opciones, cuántas correctas): eso es trabajo del
    servidor, y el servidor responde 400 con el motivo.
    """
    opciones = []
    for choice in choices:
        if choice.endswith(":ok"):
            opciones.append({"texto": choice[:-len(":ok")], "es_correcta": True})
        else:
            opciones.append({"texto": choice, "es_correcta": False})
    return {"examen": examen, "enunciado": texto, "opciones": opciones}


# --- el resto del cliente (ya escrito) --------------------------------------------------------


def call(method: str, path: str, env, *, params=None, body=None, dry_run=False) -> Result:
    base = env.get("QUIZ_URL", "http://127.0.0.1:8000").rstrip("/")
    token = env.get("QUIZ_TOKEN")
    if not token:  # un error de uso, no de red: no se intentó nada
        return Result(status=-1, error="Falta QUIZ_TOKEN (el token con el que se llama a la API).")
    request = {"method": method, "url": base + path, "params": params or None, "json": body}
    if dry_run and method != "GET":
        return Result(status=None, request=request)  # las escrituras se describen, no se envían
    try:
        response = requests.request(
            method, base + path, params=params, json=body, timeout=10,
            headers={"Authorization": f"Token {token}", "Accept": "application/json"},
        )
    except requests.RequestException as exc:
        return Result(status=0, request=request, error=str(exc))
    try:
        data = response.json() if response.content else None
    except ValueError:
        data = response.text
    return Result(status=response.status_code, data=data, request=request)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quizctl", description="Cliente de consola de la API de cuestionarios")
    parser.add_argument("--json", action="store_true", help="salida JSON estable, para otros programas")
    parser.add_argument("--dry-run", action="store_true", help="en escrituras, muestra la petición sin enviarla")
    sub = parser.add_subparsers(dest="resource", required=True)

    examenes = sub.add_parser("examenes").add_subparsers(dest="action", required=True)
    examenes.add_parser("list")
    examenes.add_parser("get").add_argument("id", type=int)

    preguntas = sub.add_parser("preguntas").add_subparsers(dest="action", required=True)
    listing = preguntas.add_parser("list")
    listing.add_argument("--examen", type=int)
    listing.add_argument("--search")
    listing.add_argument("--page", type=int)
    preguntas.add_parser("get").add_argument("id", type=int)
    create = preguntas.add_parser("create")
    create.add_argument("--examen", type=int, required=True)
    create.add_argument("--text", required=True)
    create.add_argument("--choice", action="append", default=[], help="texto de la opción; «:ok» marca la correcta")
    preguntas.add_parser("delete").add_argument("id", type=int)

    sub.add_parser("ops")
    return parser


def dispatch(args, env) -> Result:
    dry = args.dry_run
    if args.resource == "examenes":
        if args.action == "list":
            return call("GET", "/api/examenes/", env)
        return call("GET", f"/api/examenes/{args.id}/", env)
    if args.resource == "preguntas":
        if args.action == "list":
            params = {k: v for k, v in (("examen", args.examen), ("search", args.search), ("page", args.page)) if v}
            return call("GET", "/api/preguntas/", env, params=params)
        if args.action == "get":
            return call("GET", f"/api/preguntas/{args.id}/", env)
        if args.action == "create":
            body = build_question_payload(args.examen, args.text, args.choice)
            return call("POST", "/api/preguntas/", env, body=body, dry_run=dry)
        return call("DELETE", f"/api/preguntas/{args.id}/", env, dry_run=dry)
    # ops: el contrato, leído de la propia API
    result = call("GET", "/api/schema/", env, params={"format": "json"})
    if result.status == 200:
        result.data = [
            {"operation": op.get("operationId"), "method": method.upper(), "path": path}
            for path, methods in result.data["paths"].items()
            for method, op in methods.items()
            if method in ("get", "post", "put", "patch", "delete")
        ]
    return result


def render(result: Result, as_json: bool, out) -> None:
    if as_json:
        out.write(json.dumps({"status": result.status, "data": result.data, "error": result.error or None,
                              "request": result.request if result.status is None else None},
                             ensure_ascii=False) + "\n")
        return
    if result.status is None:
        out.write(f"[dry-run] {result.request['method']} {result.request['url']}\n")
        if result.request["json"] is not None:
            out.write(json.dumps(result.request["json"], ensure_ascii=False, indent=2) + "\n")
    elif result.error:
        out.write(f"ERROR: {result.error}\n")
    elif result.status >= 400:
        out.write(f"HTTP {result.status}: {json.dumps(result.data, ensure_ascii=False)}\n")
    elif isinstance(result.data, list):
        for row in result.data:
            out.write("  ".join(str(v) for v in row.values()) + "\n")
    elif isinstance(result.data, dict) and "results" in result.data:
        out.write(f"{result.data['count']} en total (página con {len(result.data['results'])})\n")
        for row in result.data["results"]:
            out.write(f"  #{row['id']}  {row.get('titulo') or row.get('enunciado')}\n")
    else:
        out.write(json.dumps(result.data, ensure_ascii=False, indent=2) + "\n" if result.data is not None
                  else f"HTTP {result.status} (sin contenido)\n")


def main(argv=None, env=None, out=None) -> int:
    env = os.environ if env is None else env
    out = out or sys.stdout
    args = build_parser().parse_args(argv)
    result = dispatch(args, env)
    render(result, args.json, out)
    if result.status is None:
        return EXIT_OK  # un dry-run que se describió correctamente
    if result.status == -1:
        return EXIT_OTHER
    if result.status == 0:
        return EXIT_NETWORK
    return exit_code_for(result.status)


if __name__ == "__main__":
    sys.exit(main())
