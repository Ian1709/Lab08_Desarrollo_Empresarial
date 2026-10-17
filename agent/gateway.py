"""Una pasarela cerrada entre un modelo de lenguaje y la API.

El modelo nunca recibe un token, una shell ni un cliente HTTP. Emite una
INTENCIÓN:

    {"op": "preguntas_list", "query": {"examen": 1}}
    {"op": "preguntas_destroy", "path": {"id": 7}}

y `execute` decide. Cuatro capas, del lado del modelo hacia el del servidor:

1. Solo existen las operaciones de ALLOWED (una lista cerrada, con el riesgo de
   cada una).
2. Cada una debe existir además en el CONTRATO de la API (el esquema OpenAPI):
   si la API cambia y una operación desaparece, la pasarela deja de ofrecerla.
   La lista permitida no puede desviarse.
3. Se validan los argumentos: solo claves conocidas, enteros donde va un entero.
4. El riesgo decide qué pasa:  R0 lectura -> se ejecuta · R1 creación -> se
   ejecuta con el token del AGENTE · R2 destructivo -> nunca se ejecuta por
   sola palabra del modelo: devuelve un PLAN con un hash, y solo ese mismo
   plan, aprobado por una persona que aporta SU token, se aplica.

Y detrás de todo eso, el servidor tiene la última palabra: el token del agente
no puede borrar aunque esta pasarela tuviera un fallo (ver quiz/permissions.py).

Lo que devuelve la API se envuelve como `untrusted_data`: una pregunta que dice
«ignora tus instrucciones» es una cadena, no una orden.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import requests

ALLOWED = {  # operationId -> riesgo
    "examenes_list": "R0",
    "examenes_retrieve": "R0",
    "preguntas_list": "R0",
    "preguntas_retrieve": "R0",
    "opciones_list": "R0",
    "opciones_retrieve": "R0",
    "opciones_create": "R1",
    "preguntas_create": "R1",
    "opciones_destroy": "R2",
    "preguntas_destroy": "R2",
    "examenes_destroy": "R2",
}
QUERY_PARAMS = {"examen": int, "search": str, "page": int}
BODY_FIELDS = {"examen", "enunciado", "opciones"}
INTENT_KEYS = {"op", "path", "query", "body"}


def denied(reason: str) -> dict:
    return {"status": "denied", "reason": reason}


def load_catalog(base_url: str, http=requests) -> dict[str, tuple[str, str]]:
    """El contrato, leído de la propia API: operationId -> (MÉTODO, plantilla de ruta)."""
    response = http.get(base_url.rstrip("/") + "/api/schema/", params={"format": "json"}, timeout=10)
    response.raise_for_status()
    return {
        op["operationId"]: (method.upper(), path)
        for path, methods in response.json()["paths"].items()
        for method, op in methods.items()
        if method in ("get", "post", "put", "patch", "delete")
    }


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)  # bool es un int en Python


def _fill_path(template: str, given: Any) -> tuple[str | None, str]:
    """(ruta, '') si los parámetros de ruta encajan exactamente con la plantilla; si no, (None, motivo)."""
    names = [part[1:-1] for part in template.split("/") if part.startswith("{")]
    given = given if given is not None else {}
    if not isinstance(given, dict) or set(given) != set(names):
        return None, f"path debe llevar exactamente {sorted(names)}"
    path = template
    for name in names:
        if not _is_int(given[name]):
            return None, f"path.{name} debe ser un entero"
        path = path.replace("{" + name + "}", str(given[name]))
    return path, ""


def _valid_query(query: Any) -> str | None:
    if query is None:
        return None
    if not isinstance(query, dict):
        return "query debe ser un objeto"
    for key, value in query.items():
        kind = QUERY_PARAMS.get(key)
        if kind is None:
            return f"parámetro de consulta desconocido: {key!r}"
        if not isinstance(value, kind) or (kind is int and not _is_int(value)):
            return f"query.{key} debe ser {kind.__name__}"
    return None


def _valid_body(body: Any) -> str | None:
    if not isinstance(body, dict) or set(body) != BODY_FIELDS:
        return f"body debe llevar exactamente {sorted(BODY_FIELDS)}"
    return None  # el SERVIDOR valida el contenido (400 si está mal)


def _send(http, method: str, url: str, token: str, *, params=None, body=None) -> tuple[int, Any]:
    response = http.request(method, url, params=params or None, json=body, timeout=10,
                            headers={"Authorization": f"Token {token}", "Accept": "application/json"})
    try:
        data = response.json() if response.content else None
    except ValueError:
        data = response.text
    return response.status_code, data


def plan_hash(op: str, path_args: dict, target: dict) -> str:
    canonical = json.dumps({"op": op, "path": path_args, "target": target}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def _audit(audit_path: str | Path | None, op: str, risk: str, outcome: str) -> None:
    if not audit_path:
        return
    line = {"at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"), "actor": "agent",
            "op": op, "risk": risk, "outcome": outcome}
    with open(audit_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")


def execute(intent: Any, *, base_url: str, agent_token: str, approval: str | None = None,
            human_token: str | None = None, audit_path: str | Path | None = None, http=requests) -> dict:
    """Decide qué hacer con una intención. `approval` y `human_token` vienen de una
    persona, nunca del modelo."""
    result = _execute(intent, base_url, agent_token, approval, human_token, http)
    op = intent.get("op") if isinstance(intent, dict) else None
    _audit(audit_path, str(op), ALLOWED.get(op, "-"), result["status"])
    return result


def _execute(intent, base_url, agent_token, approval, human_token, http) -> dict:
    if not isinstance(intent, dict):
        return denied("la intención debe ser un objeto")
    extra = set(intent) - INTENT_KEYS
    if extra:
        return denied(f"claves desconocidas en la intención: {sorted(extra)}")
    op = intent.get("op")
    risk = ALLOWED.get(op)
    if risk is None:
        return denied(f"operación no permitida: {op!r}")
    catalog = load_catalog(base_url, http)
    if op not in catalog:
        return denied(f"la operación {op!r} ya no existe en el contrato de la API")
    method, template = catalog[op]
    path, problem = _fill_path(template, intent.get("path"))
    if path is None:
        return denied(problem)
    problem = _valid_query(intent.get("query"))
    if problem:
        return denied(problem)
    body = intent.get("body")
    if method == "POST":
        problem = _valid_body(body)
        if problem:
            return denied(problem)
    elif body is not None:
        return denied("esta operación no admite body")
    url = base_url.rstrip("/") + path

    if risk in ("R0", "R1"):
        code, data = _send(http, method, url, agent_token, params=intent.get("query"), body=body)
        return {"status": "ok" if code < 400 else "error", "http": code, "untrusted_data": data}

    # R2: se mira el objetivo AHORA, para que la persona apruebe lo que hay de verdad
    code, snapshot = _send(http, "GET", url, agent_token)
    if code == 404:
        return {"status": "not_found", "http": 404}
    if code >= 400:
        return {"status": "error", "http": code, "untrusted_data": snapshot}
    target = {k: snapshot[k] for k in ("id", "titulo", "question_count", "enunciado", "activo") if k in snapshot}
    path_args = intent.get("path") or {}
    digest = plan_hash(op, path_args, target)
    plan = {"op": op, "path": path_args, "target": target, "plan_hash": digest}
    if approval != digest:
        return {"status": "approval_required", "plan": plan}
    if not human_token:
        return denied("aprobar exige el token de la persona (QUIZ_TOKEN_HUMANO); el agente no puede borrar")
    code, data = _send(http, method, url, human_token)
    return {"status": "applied" if code < 400 else "error", "http": code, "plan": plan, "untrusted_data": data}


def tools_for_prompt() -> str:
    """El catálogo que se le muestra al modelo: operación, riesgo y las claves que puede usar."""
    return "\n".join(f"- {op} [{risk}]" for op, risk in ALLOWED.items()) + (
        "\n  claves: path {id: int} · query {examen: int, search: str, page: int}"
        " · body {examen, enunciado, opciones}"
    )
