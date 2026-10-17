"""Parte 2 del lab: el cliente de consola.

Las dos primeras clases eran rojas en el punto de partida (las dos funciones
marcadas con TODO en quizctl.py). La clase que habla con el servidor real usa un
servidor que la propia prueba arranca, igual que lo haría una persona desde la
consola.
"""
import io
import json

from django.test import LiveServerTestCase, SimpleTestCase

import quizctl

from .helpers import examen_id, seed


class ExitCodeTests(SimpleTestCase):
    def test_success_is_zero(self):
        for status in (200, 201, 204):
            self.assertEqual(quizctl.exit_code_for(status), 0, status)

    def test_validation_is_two(self):
        self.assertEqual(quizctl.exit_code_for(400), 2)

    def test_not_allowed_is_three(self):
        self.assertEqual(quizctl.exit_code_for(401), 3)
        self.assertEqual(quizctl.exit_code_for(403), 3)

    def test_not_found_is_four(self):
        self.assertEqual(quizctl.exit_code_for(404), 4)

    def test_server_errors_are_five(self):
        self.assertEqual(quizctl.exit_code_for(500), 5)
        self.assertEqual(quizctl.exit_code_for(503), 5)

    def test_anything_else_is_one(self):
        for status in (302, 405, 409):
            self.assertEqual(quizctl.exit_code_for(status), 1, status)


class PayloadTests(SimpleTestCase):
    def test_ok_marks_the_correct_choice(self):
        body = quizctl.build_question_payload(3, '¿Qué es REST?', ['Un estilo:ok', 'Un lenguaje'])
        self.assertEqual(body, {
            'examen': 3, 'enunciado': '¿Qué es REST?',
            'opciones': [
                {'texto': 'Un estilo', 'es_correcta': True},
                {'texto': 'Un lenguaje', 'es_correcta': False},
            ],
        })

    def test_only_the_final_ok_counts(self):
        body = quizctl.build_question_payload(1, 't', ['Verdad: sí:ok', 'ok es una palabra'])
        self.assertEqual(body['opciones'][0], {'texto': 'Verdad: sí', 'es_correcta': True})
        self.assertEqual(body['opciones'][1], {'texto': 'ok es una palabra', 'es_correcta': False})

    def test_it_does_not_validate_that_is_the_servers_job(self):
        # dos correctas: el servidor responderá 400
        body = quizctl.build_question_payload(1, 't', ['a:ok', 'b:ok'])
        self.assertEqual(sum(c['es_correcta'] for c in body['opciones']), 2)


class CliLiveTests(LiveServerTestCase):
    host = '127.0.0.1'  # no «localhost»: en Windows intenta IPv6 y cada petición espera

    def setUp(self):
        self.person, self.agent = seed()
        self.env = {'QUIZ_URL': self.live_server_url, 'QUIZ_TOKEN': self.person}

    def run_cli(self, *argv, env=None):
        out = io.StringIO()
        code = quizctl.main(list(argv), env=env or self.env, out=out)
        return code, out.getvalue()

    def test_examenes_list(self):
        code, text = self.run_cli('examenes', 'list')
        self.assertEqual(code, 0)
        self.assertIn('Fundamentos de Python', text)

    def test_json_output_is_stable(self):
        code, text = self.run_cli('--json', 'preguntas', 'list', '--examen', str(examen_id()))
        payload = json.loads(text)
        self.assertEqual((code, payload['status']), (0, 200))
        self.assertEqual(payload['data']['count'], 7)

    def test_create_a_valid_question(self):
        code, text = self.run_cli('--json', 'preguntas', 'create', '--examen', str(examen_id()),
                                  '--text', '¿Qué es REST?', '--choice', 'Un estilo:ok', '--choice', 'Un lenguaje')
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)['status'], 201)

    def test_two_correct_choices_exit_two_with_the_reason(self):
        code, text = self.run_cli('preguntas', 'create', '--examen', str(examen_id()), '--text', 't',
                                  '--choice', 'a:ok', '--choice', 'b:ok')
        self.assertEqual(code, 2)
        self.assertIn('exactamente una', text)

    def test_dry_run_describes_and_creates_nothing(self):
        code, text = self.run_cli('--dry-run', 'preguntas', 'create', '--examen', str(examen_id()), '--text', 't',
                                  '--choice', 'a:ok', '--choice', 'b')
        self.assertEqual(code, 0)
        self.assertIn('[dry-run] POST', text)
        _, listing = self.run_cli('--json', 'preguntas', 'list')
        self.assertEqual(json.loads(listing)['data']['count'], 10)

    def test_a_missing_question_exits_four(self):
        self.assertEqual(self.run_cli('preguntas', 'get', '99999')[0], 4)

    def test_the_agent_token_cannot_delete_exit_three(self):
        """Necesita la Parte 3 hecha: el SERVIDOR debe responder 403 al DELETE del agente."""
        env = {**self.env, 'QUIZ_TOKEN': self.agent}
        first = json.loads(self.run_cli('--json', 'preguntas', 'list', env=env)[1])['data']['results'][0]['id']
        self.assertEqual(self.run_cli('preguntas', 'delete', str(first), env=env)[0], 3)

    def test_a_wrong_token_exits_three(self):
        env = {**self.env, 'QUIZ_TOKEN': 'nonsense'}
        self.assertEqual(self.run_cli('examenes', 'list', env=env)[0], 3)

    def test_no_token_is_a_usage_error(self):
        self.assertEqual(self.run_cli('examenes', 'list', env={'QUIZ_URL': self.live_server_url})[0], 1)

    def test_no_connection_exits_six(self):
        env = {'QUIZ_URL': 'http://127.0.0.1:9', 'QUIZ_TOKEN': 'x'}
        self.assertEqual(self.run_cli('examenes', 'list', env=env)[0], 6)

    def test_ops_lists_the_contract(self):
        code, text = self.run_cli('ops')
        self.assertEqual(code, 0)
        self.assertIn('preguntas_destroy', text)
