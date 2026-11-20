"""Pinned synthetic outputs checked against original request identity snapshots."""
import copy
import hashlib
import importlib.util
import io
import json
import os
import socket
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary

SPEC = importlib.util.spec_from_file_location(
    'offline_request_parity', boundary.ROOT / 'tools/blog_output_request_parity.py')
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


def snapshot(path):
    value = path.stat()
    return (path.read_bytes(), value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class RequestBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        boundary.BankBoundary.setUpClass()

    def setUp(self):
        self.h = boundary.BankBoundary()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        for guard in (patch.dict(os.environ, {}, clear=True),
                      patch.object(socket, 'getaddrinfo', side_effect=AssertionError('DNS')),
                      patch.object(socket, 'create_connection', side_effect=AssertionError('network')),
                      patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network'))):
            guard.start()
            self.addCleanup(guard.stop)
        self.request = self.h.directory / 'original-request.json'
        self.request.write_bytes(json.dumps(self.h.request, ensure_ascii=True).encode('ascii'))
        self.digest = hashlib.sha256(self.request.read_bytes()).hexdigest()
        self.target = self.h.directory / 'retained'
        self.h.draft.generate(self.h.request, self.target, writer=self.h.writer())
        self.artifact = self.target / 'site-config.json'
        self.retained = {p.name: snapshot(p) for p in self.target.iterdir()}

    def check(self, artifact=None, request=None, digest=None):
        artifact, request = artifact or self.artifact, request or self.request
        before = snapshot(artifact), snapshot(request)
        result = parity.qualify(offline=True, artifact=artifact, request_snapshot=request,
                                expected_request_sha256=digest or self.digest)
        self.assertEqual((snapshot(artifact), snapshot(request)), before)
        self.assertEqual(result['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(result[key], False)
        self.assertEqual({p.name: snapshot(p) for p in self.target.iterdir()}, self.retained)
        return result

    def test_actual_native_projection_matches_original_request_and_overrides_forged_model_identity(self):
        self.assertEqual(self.check()['request_binding'], 'MATCH')
        request = dict(self.h.request, source_action_id='SYNTHETIC 动作',
                       topic='  SYNTHETIC Ω e\u0301  ')
        baseline = self.h.directory / 'unicode-request.json'
        baseline.write_bytes(json.dumps(request, ensure_ascii=True).encode('ascii'))
        digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
        forged = dict(self.h.post, source_action_id='SYNTHETIC wrong',
                      source_topic='SYNTHETIC wrong topic')
        writer = self.h.writer(forged)
        target = self.h.directory / 'projected'
        self.h.draft.generate(request, target, writer=writer)
        writer['generate_blog'].assert_called_once()
        self.assertEqual(self.check(target / 'site-config.json', baseline, digest)[
            'request_binding'], 'MATCH')

    def test_other_valid_native_outputs_cannot_satisfy_original_request_identity(self):
        variants = (dict(self.h.request, source_action_id='SYNTHETIC other action'),
                    dict(self.h.request, topic='SYNTHETIC other topic'),
                    dict(self.h.request, source_action_id='SYNTHETIC other action',
                         topic='SYNTHETIC other topic'))
        for index, request in enumerate(variants):
            with self.subTest(index=index):
                output = self.h.directory / ('other-' + str(index))
                self.h.draft.generate(request, output, writer=self.h.writer())
                result = self.check(output / 'site-config.json')
                self.assertEqual(result['reason'], 'request_identity_mismatch')
                self.assertEqual(result['request_binding'], 'REFUSED')

    def test_request_digest_is_independent_of_self_consistent_replacements(self):
        changed_request = dict(self.h.request, source_action_id='SYNTHETIC replacement')
        baseline = self.h.directory / 'substituted-request'
        baseline.write_bytes(json.dumps(changed_request).encode('ascii'))
        output = self.h.directory / 'substituted-output'
        self.h.draft.generate(changed_request, output, writer=self.h.writer())
        self.assertEqual(self.check(output / 'site-config.json', baseline)['reason'],
                         'request_digest_mismatch')
        changed_digest = hashlib.sha256(baseline.read_bytes()).hexdigest()
        # Supplying new trusted custody is beyond this qualifier's authority.
        self.assertEqual(self.check(output / 'site-config.json', baseline, changed_digest)[
            'request_binding'], 'MATCH')
        whitespace = self.h.directory / 'changed-request-bytes'
        whitespace.write_bytes(self.request.read_bytes() + b'\n')
        self.assertEqual(self.check(request=whitespace)['reason'], 'request_digest_mismatch')

    def test_malformed_output_shapes_and_missing_or_typed_identity_refuse(self):
        original = json.loads(self.artifact.read_bytes())
        post = original['blog_posts'][0]
        cases = (None, [], {}, {'blog_posts': None}, {'blog_posts': {}},
                 {'blog_posts': []}, {'blog_posts': [post, post]},
                 {'blog_posts': [None]}, {'blog_posts': [True]})
        for index, value in enumerate(cases):
            with self.subTest(shape=index):
                path = self.h.directory / ('shape-' + str(index))
                path.write_bytes(json.dumps(value).encode('ascii'))
                self.assertEqual(self.check(path)['request_binding'], 'REFUSED')
        for field in ('source_action_id', 'source_topic'):
            for index, bad in enumerate((None, False, 1, [], {}, '', 'SYNTHETIC wrong')):
                with self.subTest(field=field, bad=bad):
                    value = copy.deepcopy(original)
                    value['blog_posts'][0][field] = bad
                    path = self.h.directory / (field + str(index))
                    path.write_bytes(json.dumps(value).encode('ascii'))
                    self.assertEqual(self.check(path)['reason'], 'request_identity_mismatch')
            value = copy.deepcopy(original)
            value['blog_posts'][0].pop(field)
            path = self.h.directory / ('missing-' + field)
            path.write_bytes(json.dumps(value).encode('ascii'))
            self.assertEqual(self.check(path)['request_binding'], 'REFUSED')

    def test_invalid_request_identity_and_shared_strict_parser_refuse(self):
        for field in ('source_action_id', 'topic'):
            for index, bad in enumerate((None, False, 1, [], {}, '', ' \t')):
                with self.subTest(field=field, bad=bad):
                    value = dict(self.h.request, **{field: bad})
                    path = self.h.directory / ('request-' + field + str(index))
                    raw = json.dumps(value).encode('ascii')
                    path.write_bytes(raw)
                    self.assertEqual(self.check(request=path, digest=hashlib.sha256(raw).hexdigest())[
                        'reason'], 'invalid_request_identity')
        for index, addition in enumerate((b'1e309', b'"SYNTHETIC\\ud800"', b'{"x":1,"x":2}')):
            for kind in ('request', 'artifact'):
                with self.subTest(index=index, kind=kind):
                    raw = (self.request if kind == 'request' else self.artifact).read_bytes().rstrip()
                    raw = raw[:-1] + b', "extra":' + addition + b'}'
                    path = self.h.directory / ('strict-' + kind + str(index))
                    path.write_bytes(raw)
                    result = (self.check(request=path, digest=hashlib.sha256(raw).hexdigest())
                              if kind == 'request' else self.check(path))
                    self.assertEqual(result['request_binding'], 'REFUSED')

    def test_byte_caps_and_input_pair_drift_use_shared_readonly_guards(self):
        for kind, limit in (('request', parity.REQUEST_LIMIT), ('artifact', parity.ARTIFACT_LIMIT)):
            with self.subTest(kind=kind):
                raw = (self.request if kind == 'request' else self.artifact).read_bytes()
                path = self.h.directory / ('cap-' + kind)
                path.write_bytes(raw + b' ' * (limit - len(raw)))
                if kind == 'request':
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    self.assertEqual(self.check(request=path, digest=digest)['request_binding'], 'MATCH')
                else:
                    self.assertEqual(self.check(path)['request_binding'], 'MATCH')
                path.write_bytes(path.read_bytes() + b' ')
                result = (self.check(request=path) if kind == 'request' else self.check(path))
                self.assertEqual(result['reason'], 'input_too_large')
        reader = parity.core._regular_bytes
        request, artifact = self.h.directory / 'drift-request', self.h.directory / 'drift-artifact'
        request.write_bytes(self.request.read_bytes())
        artifact.write_bytes(self.artifact.read_bytes())
        changed = []

        def mutate(path, limit):
            raw = reader(path, limit)
            if path == artifact:
                request.write_bytes(request.read_bytes() + b' ')
                changed.append(snapshot(request))
            return raw

        with patch.object(parity.core, '_regular_bytes', mutate):
            result = parity.qualify(offline=True, artifact=artifact, request_snapshot=request,
                                    expected_request_sha256=self.digest)
        self.assertEqual(result['reason'], 'input_set_changed')
        self.assertEqual(snapshot(request), changed[0])

    def test_body_integrity_and_full_admission_are_explicitly_outside_projection_match(self):
        value = json.loads(self.artifact.read_bytes())
        value['blog_posts'][0]['intro'] = 'SYNTHETIC altered body; separate hash custody required'
        value['blog_posts'][0]['approved'] = True
        path = self.h.directory / 'body-only-change'
        path.write_bytes(json.dumps(value).encode('ascii'))
        result = self.check(path)
        self.assertEqual(result['request_binding'], 'MATCH')
        self.assertIs(result['approved'], False)
        self.assertIs(result['publish_allowed'], False)

    def test_default_off_cli_match_and_refusal_have_fixed_private_output(self):
        with patch.object(parity.core, '_input_signature', side_effect=AssertionError('OFF stat')), \
                patch.object(parity.core, '_regular_bytes', side_effect=AssertionError('OFF read')):
            out = io.StringIO()
            with patch('sys.stdout', out):
                self.assertEqual(parity.main(['--artifact', 'SYNTHETIC_PRIVATE_CANARY']), 0)
            self.assertEqual(json.loads(out.getvalue())['request_binding'], 'DISABLED')
            self.assertNotIn('CANARY', out.getvalue())
        args = ['--offline', '--request-snapshot', str(self.request),
                '--expected-request-sha256', self.digest, '--artifact', str(self.artifact)]
        for digest, status in ((self.digest, 0), ('0' * 64, 1)):
            out, err = io.StringIO(), io.StringIO()
            selected = list(args)
            selected[selected.index('--expected-request-sha256') + 1] = digest
            with patch('sys.stdout', out), patch('sys.stderr', err):
                self.assertEqual(parity.main(selected), status)
            self.assertEqual(err.getvalue(), '')
            result = json.loads(out.getvalue())
            self.assertEqual(result['status'], 'HOLD')
            self.assertIs(result['publish_allowed'], False)
        with patch.object(parity.core, '_input_signature', side_effect=AssertionError('bad baseline stat')):
            for bad in (None, '', '0' * 63, True, 1):
                self.assertEqual(parity.qualify(offline=True, expected_request_sha256=bad)['reason'],
                                 'invalid_baseline')


if __name__ == '__main__':
    unittest.main()
