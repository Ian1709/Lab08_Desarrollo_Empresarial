from django.core.management.base import BaseCommand

from quiz.models import Examen, Opcion, Pregunta


class Command(BaseCommand):
    help = 'Crea datos de ejemplo para probar la API de cuestionarios.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra los datos existentes antes de sembrar.',
        )

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

        self.stdout.write(self.style.SUCCESS(
            f'Listo: {Examen.objects.count()} exámenes y '
            f'{total_preguntas} preguntas sembradas.'
        ))
