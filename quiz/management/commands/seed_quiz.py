from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from rest_framework.authtoken.models import Token

from quiz.models import Examen, Opcion, Pregunta
from quiz.permissions import AGENT_GROUP

# Contraseña de aula de la persona «profe»: solo para entrar en la API navegable
# desde el navegador. Cambiar en cualquier despliegue real.
PROFE_PASSWORD = 'profe12345'


def ensure_users():
    """La persona (staff) y el agente (grupo «agente»), cada una con su token.

    Idempotente: volver a ejecutar el seed conserva los mismos tokens, de modo
    que las variables de entorno siguen siendo válidas.

    La persona recibe además una contraseña de aula (solo para poder iniciar
    sesión en la API navegable desde el navegador; en producción sería una
    contraseña real o un token, nunca un valor fijo).
    """
    group, _ = Group.objects.get_or_create(name=AGENT_GROUP)
    person, created = User.objects.get_or_create(username='profe', defaults={'is_staff': True})
    if created:
        person.set_password(PROFE_PASSWORD)
        person.save()
    agent, created = User.objects.get_or_create(username='agente')
    if created:
        agent.set_unusable_password()
        agent.save()
    agent.groups.add(group)
    return (
        Token.objects.get_or_create(user=person)[0].key,
        Token.objects.get_or_create(user=agent)[0].key,
    )


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para probar la API de cuestionarios.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra los datos existentes antes de sembrar.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset']:
            Opcion.objects.all().delete()
            Pregunta.objects.all().delete()
            Examen.objects.all().delete()
            self.stdout.write('Datos anteriores eliminados.')

        examen_1 = Examen.objects.create(
            titulo='Fundamentos de Python',
            descripcion='Cuestionario de introducción al lenguaje Python.',
        )
        examen_2 = Examen.objects.create(
            titulo='Bases de datos',
            descripcion='Cuestionario sobre SQL y modelado relacional.',
        )

        banco = {
            examen_1: [
                ('¿Qué tipo de dato es el resultado de 3 / 2 en Python 3?', ['float', 'int', 'str', 'bool']),
                ('¿Qué palabra clave define una función?', ['def', 'func', 'lambda', 'function']),
                ('¿Qué estructura es inmutable?', ['tuple', 'list', 'dict', 'set']),
                ('¿Qué operador compara identidad?', ['is', '==', '!=', 'equals']),
                ('¿Qué módulo maneja fechas?', ['datetime', 'time64', 'calendarx', 'dateutil']),
                ('¿Qué método añade al final de una lista?', ['append', 'push', 'add', 'insert']),
                ('¿Qué símbolo inicia un comentario?', ['#', '//', '--', '/*']),
            ],
            examen_2: [
                ('¿Qué sentencia recupera filas?', ['SELECT', 'GET', 'FETCH', 'READ']),
                ('¿Qué clave identifica de forma única una fila?', ['PRIMARY KEY', 'INDEX', 'UNIQUE ROW', 'FOREIGN KEY']),
                ('¿Qué JOIN devuelve solo las coincidencias?', ['INNER JOIN', 'LEFT JOIN', 'CROSS JOIN', 'FULL JOIN']),
            ],
        }

        total_preguntas = 0
        for examen, preguntas in banco.items():
            for orden, (enunciado, textos) in enumerate(preguntas, start=1):
                pregunta = Pregunta.objects.create(
                    examen=examen,
                    enunciado=enunciado,
                    orden=orden,
                )
                for i, texto in enumerate(textos):
                    Opcion.objects.create(
                        pregunta=pregunta,
                        texto=texto,
                        es_correcta=(i == 0),
                    )
                total_preguntas += 1

        human, agent = ensure_users()

        if options['verbosity'] > 0:
            self.stdout.write(self.style.SUCCESS(
                f'Listo: {Examen.objects.count()} exámenes y '
                f'{total_preguntas} preguntas sembradas.'
            ))
            self.stdout.write('\nTokens (solo para esta máquina; el de la persona es el que puede borrar):')
            self.stdout.write('  PowerShell:')
            self.stdout.write(f'    $env:QUIZ_TOKEN_HUMANO = "{human}"')
            self.stdout.write(f'    $env:QUIZ_TOKEN_AGENTE = "{agent}"')
            self.stdout.write('  Bash:')
            self.stdout.write(f'    export QUIZ_TOKEN_HUMANO={human}')
            self.stdout.write(f'    export QUIZ_TOKEN_AGENTE={agent}')
            self.stdout.write(f'\nAPI navegable (navegador): usuario «profe», contraseña «{PROFE_PASSWORD}».')
