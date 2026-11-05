"""Offline end-to-end benchmark diagnostic test, never live requests."""
import json
from pathlib import Path
import tempfile
import unittest
from secure_groq_session import Session
from providers import TransportResponse
from structured_session_fixture import StructuredSessionFixture
from test_secure_groq_session import Clock

class BenchmarkDiagnosticTests(unittest.TestCase):
    def test_untrusted_diagnostic_fields_are_not_copied_into_reports(self):
        from context_quality_benchmark import run_benchmark
        secret='SYNTHETIC_PRIVATE_DIAGNOSTIC_VALUE'
        report=run_benchmark(lambda _: {'status':503,'text':'','error_code':secret,
            'diagnostic':{'api_key':secret,'reasoning':secret,'finish_reason':secret,
                          'http_status':200,'has_content':False}},
            'openai/gpt-oss-20b',test_only=True)
        self.assertNotIn(secret,json.dumps(report))
        self.assertEqual(report['failed_case']['diagnostic'],{'http_status':200,'has_content':False})

    def test_truncation_without_answer_is_not_reported_as_an_unexplained_provider_error(self):
        body=json.dumps({'choices':[{'message':{'role':'assistant','content':None,'reasoning':'PRIVATE_SYNTHETIC_REASONING'},'finish_reason':'length'}]}).encode()
        transport=StructuredSessionFixture(200, body)
        session=Session('SYNTHETIC_DIAGNOSTIC_TOKEN',transport=transport,clock=Clock(),test_only=True)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.json'
            session.start_benchmark(confirmed=True,output=path,wait=lambda _:False)
            session._benchmark_thread.join(5)
            report=json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(len(transport.requests),1)
            self.assertEqual(report['stop_reason'],'response_truncated')
            self.assertEqual(report['failed_case']['diagnostic']['http_status'],200)
            self.assertEqual(report['failed_case']['diagnostic']['finish_reason'],'length')
            self.assertNotIn('PRIVATE_SYNTHETIC_REASONING',json.dumps(report))
            self.assertNotIn('SYNTHETIC_DIAGNOSTIC_TOKEN',json.dumps(report))
        session.close()
