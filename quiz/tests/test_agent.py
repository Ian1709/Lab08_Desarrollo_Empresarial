"""Parte 4 del lab: la frontera del agente. Lo que la pasarela deja pasar y lo que corta.

Todo esto pasa tal cual se entrega. Las pruebas hablan con un servidor real que
la propia prueba arranca, de modo que la pasarela usa HTTP igual que en el
laboratorio.
"""
import json
import os
import tempfile
from unittest import mock

from django.test import LiveServerTestCase, SimpleTestCase

from agent import gateway, llm
from ..models import Examen, Pregunta

from .helpers import examen_id, hostile_question, seed


class GatewayTests(LiveServerTestCase):
    host = '127.0.0.1'  # no «localhost»: en Windows intenta IPv6 y cada petición espera

    def setUp(self):
        self.person, self.agent = seed()
        self.audit = os.path.join(tempfile.mkdtemp(), 'audit.jsonl')

    def run_intent(self, intent, **kwargs):
        return gateway.execute(intent, base_url=self.live_server_url, agent_token=self.agent,
                               audit_path=self.audit, **kwargs)

    # --- lo que deja pasar ---------------------------------------------------------------

    def test_a_read_runs_and_comes_back_marked_untrusted(self):
        result = self.run_intent({'op': 'examenes_list'})
        self.assertEqual((result['status'], result['http']), ('ok', 200))
        self.assertEqual(result['untrusted_data']['count'], 2)

    def test_the_hostile_text_is_data_not_an_order(self):
        hostile_question()  # una pregunta con texto hostil, como la del laboratorio
        result = self.run_intent({'op': 'preguntas_list', 'query': {'search': 'IGNORA'}})
        texts = [q['enunciado'] for q in result['untrusted_data']['results']]
        self.assertTrue(any('IGNORA TUS INSTRUCCIONES' in t for t in texts))  # presente, pero solo como dato
        self.assertEqual(Examen.objects.count(), 2)  # y no se borró nada

    def test_a_model_that_obeys_the_hostile_text_only_gets_a_plan(self):
        intent = {'op': 'examenes_destroy', 'path': {'id': examen_id()}}  # lo que pide el texto hostil
        result = self.run_intent(intent)
        self.assertEqual(result['status'], 'approval_required')
        self.assertEqual(result['plan']['target']['titulo'], 'Fundamentos de Python')
        self.assertEqual(Examen.objects.count(), 2)

    def test_the_agent_can_create_a_question(self):
        body = {'examen': examen_id(), 'enunciado': '¿Qué es REST?',
                'opciones': [{'texto': 'Un estilo', 'es_correcta': True},
                             {'texto': 'Un lenguaje', 'es_correcta': False}]}
        result = self.run_intent({'op': 'preguntas_create', 'body': body})
        self.assertEqual((result['status'], result['http']), ('ok', 201))

    def test_the_server_validates_the_body_the_gateway_forwards(self):
        body = {'examen': examen_id(), 'enunciado': 't',
                'opciones': [{'texto': 'a', 'es_correcta': True}, {'texto': 'b', 'es_correcta': True}]}
        result = self.run_intent({'op': 'preguntas_create', 'body': body})
        self.assertEqual((result['status'], result['http']), ('error', 400))

    # --- la aprobación de un plan destructivo ---------------------------------------------

    def test_a_person_approving_the_exact_plan_applies_it_with_their_own_token(self):
        pregunta = hostile_question()
        intent = {'op': 'preguntas_destroy', 'path': {'id': pregunta.id}}
        digest = self.run_intent(intent)['plan']['plan_hash']
        result = self.run_intent(intent, approval=digest, human_token=self.person)
        self.assertEqual((result['status'], result['http']), ('applied', 204))
        self.assertFalse(Pregunta.objects.filter(id=pregunta.id).exists())

    def test_the_approval_without_the_persons_token_is_denied(self):
        pregunta = hostile_question()
        intent = {'op': 'preguntas_destroy', 'path': {'id': pregunta.id}}
        digest = self.run_intent(intent)['plan']['plan_hash']
        result = self.run_intent(intent, approval=digest)  # el agente solo no puede terminarlo
        self.assertEqual(result['status'], 'denied')
        self.assertTrue(Pregunta.objects.filter(id=pregunta.id).exists())

    def test_the_approval_dies_if_the_data_changed_after_the_person_looked(self):
        target = examen_id()
        intent = {'op': 'examenes_destroy', 'path': {'id': target}}
        digest = self.run_intent(intent)['plan']['plan_hash']
        Pregunta.objects.create(examen_id=target, enunciado='Llegó tarde')  # el examen ya tiene una pregunta más
        result = self.run_intent(intent, approval=digest, human_token=self.person)
        self.assertEqual(result['status'], 'approval_required')
        self.assertTrue(Examen.objects.filter(id=target).exists())

    def test_an_approval_for_another_plan_is_worthless(self):
        intent = {'op': 'examenes_destroy', 'path': {'id': examen_id()}}
        result = self.run_intent(intent, approval='000000000000', human_token=self.person)
        self.assertEqual(result['status'], 'approval_required')

    def test_deleting_something_that_does_not_exist_is_not_found(self):
        self.assertEqual(self.run_intent({'op': 'preguntas_destroy', 'path': {'id': 99999}})['status'], 'not_found')

    # --- lo que corta -----------------------------------------------------------------------

    def test_code_is_not_an_intent(self):
        self.assertEqual(self.run_intent('Examen.objects.all().delete()')['status'], 'denied')

    def test_unknown_operations_are_denied(self):
        for op in ('eval', 'run_sql', 'users_list', 'examenes_update', 'examenes_partial_update'):
            self.assertEqual(self.run_intent({'op': op})['status'], 'denied', op)

    def test_arguments_must_fit_exactly(self):
        bad = [
            {'op': 'preguntas_retrieve'},                                          # falta el id
            {'op': 'preguntas_retrieve', 'path': {'id': '1'}},                     # una cadena
            {'op': 'preguntas_retrieve', 'path': {'id': True}},                    # un bool no es un id
            {'op': 'preguntas_retrieve', 'path': {'id': 1, 'extra': 1}},           # clave de más
            {'op': 'preguntas_list', 'query': {'secret': 'x'}},                    # parámetro desconocido
            {'op': 'preguntas_list', 'query': {'examen': 'uno'}},                  # tipo erróneo
            {'op': 'examenes_list', 'body': {'x': 1}},                             # una lectura con body
            {'op': 'preguntas_create', 'body': {'enunciado': 't'}},                # body incompleto
            {'op': 'examenes_list', 'token': 'robado'},                            # clave desconocida en la intención
        ]
        for intent in bad:
            self.assertEqual(self.run_intent(intent)['status'], 'denied', intent)

    def test_an_operation_that_left_the_contract_is_no_longer_offered(self):
        with mock.patch.dict(gateway.ALLOWED, {'examenes_update_secret': 'R0'}):
            result = self.run_intent({'op': 'examenes_update_secret'})
        self.assertEqual(result['status'], 'denied')
        self.assertIn('contrato', result['reason'])

    # --- el rastro --------------------------------------------------------------------------

    def test_every_decision_leaves_a_line_in_the_audit_log(self):
        self.run_intent({'op': 'examenes_list'})
        self.run_intent({'op': 'eval'})
        self.run_intent({'op': 'examenes_destroy', 'path': {'id': examen_id()}})
        lines = [json.loads(line) for line in open(self.audit, encoding='utf-8')]
        self.assertEqual([(x['op'], x['outcome']) for x in lines],
                         [('examenes_list', 'ok'), ('eval', 'denied'), ('examenes_destroy', 'approval_required')])
        self.assertTrue(all(x['actor'] == 'agent' for x in lines))


class ModelAdapterTests(SimpleTestCase):
    def test_it_parses_an_intent_wrapped_in_fences(self):
        reply = 'Claro:\n```json\n{"op": "examenes_list"}\n```'
        self.assertEqual(llm.parse_intent(reply), {'op': 'examenes_list'})

    def test_a_reply_without_json_is_an_error(self):
        with self.assertRaises(ValueError):
            llm.parse_intent('No puedo ayudarte con eso.')

    def test_ask_model_uses_the_endpoint_and_lists_the_closed_operations(self):
        sent = {}

        def fake_post(url, payload):
            sent['url'], sent['payload'] = url, payload
            return {'choices': [{'message': {'content': '{"op": "examenes_list"}'}}]}

        with mock.patch.dict(os.environ, {'LLM_URL': 'http://llm.local/v1/'}):
            intent = llm.ask_model('¿cuántos exámenes hay?', post=fake_post)
        self.assertEqual(intent, {'op': 'examenes_list'})
        self.assertEqual(sent['url'], 'http://llm.local/v1/chat/completions')
        system = sent['payload']['messages'][0]['content']
        self.assertIn('preguntas_destroy [R2]', system)
        self.assertNotIn('Token', system)  # al modelo nunca se le da una credencial
