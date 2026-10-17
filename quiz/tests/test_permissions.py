"""Parte 3 del lab: los roles. El servidor decide, pase lo que pase en el cliente.

`test_the_agent_cannot_delete` era roja en el punto de partida: `AgentPermission`
dejaba pasar todo. Se implementa en quiz/permissions.py hasta que pase todo.
"""
from rest_framework.test import APITestCase

from ..models import Pregunta

from .helpers import examen_id, reader_token, seed, valid_body


class RoleTests(APITestCase):
    def setUp(self):
        self.person, self.agent = seed()
        self.reader = reader_token()

    def as_(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        return self.client

    def test_the_agent_can_read(self):
        self.assertEqual(self.as_(self.agent).get('/api/preguntas/').status_code, 200)

    def test_the_agent_can_create(self):
        response = self.as_(self.agent).post('/api/preguntas/', valid_body(examen_id()), format='json')
        self.assertEqual(response.status_code, 201)

    def test_the_agent_can_modify(self):
        pregunta = Pregunta.objects.first()
        response = self.as_(self.agent).patch(f'/api/preguntas/{pregunta.id}/', {'enunciado': 'Otro'}, format='json')
        self.assertEqual(response.status_code, 200)

    def test_the_agent_cannot_delete(self):
        pregunta = Pregunta.objects.first()
        response = self.as_(self.agent).delete(f'/api/preguntas/{pregunta.id}/')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Pregunta.objects.filter(id=pregunta.id).exists())

    def test_the_agent_cannot_delete_an_exam_either(self):
        self.assertEqual(self.as_(self.agent).delete(f'/api/examenes/{examen_id()}/').status_code, 403)

    def test_a_person_can_delete(self):
        pregunta = Pregunta.objects.first()
        self.assertEqual(self.as_(self.person).delete(f'/api/preguntas/{pregunta.id}/').status_code, 204)

    def test_somebody_without_a_role_can_only_read(self):
        self.assertEqual(self.as_(self.reader).get('/api/preguntas/').status_code, 200)
        self.assertEqual(
            self.as_(self.reader).post('/api/preguntas/', valid_body(examen_id()), format='json').status_code, 403
        )

    def test_no_token_is_401_not_403(self):
        self.client.credentials()
        self.assertEqual(self.client.get('/api/preguntas/').status_code, 401)
