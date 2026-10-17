from django.contrib.auth.models import User
from django.core.management import call_command
from rest_framework.authtoken.models import Token

from quiz.models import Examen, Pregunta
from quiz.seed_data import HOSTILE_TEXT


def seed():
    """Carga los datos fijos y devuelve (token de la persona, token del agente)."""
    call_command('seed_quiz', verbosity=0)
    return (
        Token.objects.get(user__username='profe').key,
        Token.objects.get(user__username='agente').key,
    )


def person_token():
    """Token de la persona (staff) sin cargar los datos de ejemplo."""
    user, _ = User.objects.get_or_create(username='profe', defaults={'is_staff': True})
    if not user.is_staff:
        user.is_staff = True
        user.save()
    return Token.objects.get_or_create(user=user)[0].key


def reader_token():
    """Un usuario autenticado que no es staff ni del grupo «agente»."""
    user, _ = User.objects.get_or_create(username='lector')
    return Token.objects.get_or_create(user=user)[0].key


def examen_id(titulo='Fundamentos de Python'):
    return Examen.objects.get(titulo=titulo).id


def hostile_question():
    """Una pregunta con el texto hostil (se crea si el seed no la incluyó)."""
    examen = Examen.objects.first()
    return Pregunta.objects.get_or_create(
        examen=examen,
        enunciado=f'¿Para qué sirve prefetch_related? {HOSTILE_TEXT}',
        defaults={'orden': 99},
    )[0]


def valid_body(examen):
    return {
        'examen': examen,
        'enunciado': '¿Qué es una API REST?',
        'opciones': [
            {'texto': 'Un estilo de arquitectura sobre HTTP', 'es_correcta': True},
            {'texto': 'Un lenguaje de programación', 'es_correcta': False},
            {'texto': 'Un motor de base de datos', 'es_correcta': False},
        ],
    }
