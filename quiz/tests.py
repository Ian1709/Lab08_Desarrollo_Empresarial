from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Examen, Opcion, Pregunta
from .serializers import PreguntaSerializer


class PreguntaSerializerTests(APITestCase):
    def setUp(self):
        self.examen = Examen.objects.create(titulo='Examen de prueba')

    def test_valida_con_exactamente_una_opcion_correcta(self):
        data = {
            'examen': self.examen.id,
            'enunciado': '¿2 + 2?',
            'opciones': [
                {'texto': '4', 'es_correcta': True},
                {'texto': '5', 'es_correcta': False},
            ],
        }
        serializer = PreguntaSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        pregunta = serializer.save()
        self.assertEqual(pregunta.opciones.count(), 2)
        self.assertEqual(pregunta.opciones.filter(es_correcta=True).count(), 1)

    def test_rechaza_pregunta_sin_opcion_correcta(self):
        data = {
            'examen': self.examen.id,
            'enunciado': '¿2 + 2?',
            'opciones': [
                {'texto': '4', 'es_correcta': False},
                {'texto': '5', 'es_correcta': False},
            ],
        }
        serializer = PreguntaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('opciones', serializer.errors)

    def test_rechaza_pregunta_con_dos_opciones_correctas(self):
        data = {
            'examen': self.examen.id,
            'enunciado': '¿2 + 2?',
            'opciones': [
                {'texto': '4', 'es_correcta': True},
                {'texto': '4', 'es_correcta': True},
            ],
        }
        serializer = PreguntaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('opciones', serializer.errors)


class ApiCrudTests(APITestCase):
    def setUp(self):
        self.examen = Examen.objects.create(titulo='Examen API')
        self.pregunta = Pregunta.objects.create(
            examen=self.examen, enunciado='Pregunta base', orden=1,
        )
        Opcion.objects.create(pregunta=self.pregunta, texto='A', es_correcta=True)
        Opcion.objects.create(pregunta=self.pregunta, texto='B', es_correcta=False)

    def test_listar_examenes(self):
        respuesta = self.client.get('/api/examenes/')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_crear_pregunta_anidada(self):
        respuesta = self.client.post('/api/preguntas/', {
            'examen': self.examen.id,
            'enunciado': 'Nueva',
            'opciones': [{'texto': 'X', 'es_correcta': True}],
        }, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)

    def test_patch_parcial_sin_opciones(self):
        respuesta = self.client.patch(
            f'/api/preguntas/{self.pregunta.id}/', {'orden': 3}, format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)

    def test_eliminar_pregunta(self):
        respuesta = self.client.delete(f'/api/preguntas/{self.pregunta.id}/')
        self.assertEqual(respuesta.status_code, status.HTTP_204_NO_CONTENT)

    def test_filtrado_por_examen(self):
        respuesta = self.client.get(f'/api/preguntas/?examen={self.examen.id}')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
