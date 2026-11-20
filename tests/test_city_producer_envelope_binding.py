"""Synthetic saved artifact envelope integrity against the pinned native projection."""
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


def load_tool(name):
    spec = importlib.util.spec_from_file_location(
        'envelope_test_' + name, boundary.ROOT / 'tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


parity = load_tool('blog_output_envelope_parity')
request_parity = load_tool('blog_output_request_parity')


def snapshot(path):
    value = path.stat()
    return (path.read_bytes(), value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


class EnvelopeBinding(unittest.TestCase):
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
        self.target = self.h.directory / 'retained'
        self.h.draft.generate(self.h.request, self.target, writer=self.h.writer())
        self.artifact = self.target / 'site-config.json'
        self.retained = {p.name: snapshot(p) for p in self.target.iterdir()}

    def check(self, path=None):
        path = path or self.artifact
        before = snapshot(path)
        value = parity.qualify(offline=True, artifact=path)
        self.assertEqual(snapshot(path), before)
        self.assertEqual(value['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(value[key], False)
        self.assertEqual({p.name: snapshot(p) for p in self.target.iterdir()}, self.retained)
        return value

    def test_actual_native_full_minimal_and_held_projections_remain_envelope_matches(self):
        self.assertEqual(self.check()['envelope_binding'], 'MATCH')
        for label, post, violations in (
                ('full', dict(self.h.post, **self.h.fixture['untrusted_fields']), []),
                ('minimal', {}, []),
                ('held', self.h.post, ['SYNTHETIC native hold'])):
            with self.subTest(label=label):
                writer = self.h.writer(violations=violations)
                writer['generate_blog'].return_value = copy.deepcopy(post)
                target = self.h.directory / label
                result = self.h.draft.generate(self.h.request, target, writer=writer)
                writer['generate_blog'].assert_called_once()
                self.assertEqual(result['status'], 'draft_only')
                self.assertEqual(self.check(target / 'site-config.json')['envelope_binding'], 'MATCH')
                saved = json.loads((target / 'site-config.json').read_bytes())['blog_posts'][0]
                if label == 'minimal':
                    self.assertEqual(set(saved), {'source_action_id', 'source_topic'})

    def test_foreign_root_and_post_fields_refuse_even_if_identity_stays_correct(self):
        original = json.loads(self.artifact.read_bytes())
        fields = [key for key in self.h.fixture['untrusted_fields']
                  if key not in ('source_action_id', 'source_topic')]
        fields += ['meta_title', 'meta_description', 'excerpt', 'unknown_field', 'SYNTHETIC_PRIVATE_CANARY']
        for position in ('root', 'post'):
            for index, field in enumerate(fields):
                with self.subTest(position=position, field=field):
                    output = copy.deepcopy(original)
                    node = output if position == 'root' else output['blog_posts'][0]
                    node[field] = {'pass': True, 'SYNTHETIC_PRIVATE_CANARY': True}
                    path = self.h.directory / (position + str(index))
                    path.write_bytes(json.dumps(output).encode('ascii'))
                    value = self.check(path)
                    self.assertEqual(value['reason'], 'foreign_output_field')
                    self.assertEqual(value['envelope_binding'], 'REFUSED')
                    self.assertNotIn('CANARY', json.dumps(value))
        # Even real post field names cannot appear at the artifact root.
        for field in ('title', 'slug', 'intro', 'sections', 'citations', 'source_action_id', 'source_topic'):
            with self.subTest(root_field=field):
                output = dict(original, **{field: 'SYNTHETIC'})
                path = self.h.directory / ('root-' + field)
                path.write_bytes(json.dumps(output).encode('ascii'))
                self.assertEqual(self.check(path)['reason'], 'foreign_output_field')
        for index, field in enumerate(('approved\u200b', '\ufeffapproved', 'APPROVED', 'gate\u202ePass')):
            with self.subTest(hidden_field=field):
                output = copy.deepcopy(original)
                output['blog_posts'][0][field] = True
                path = self.h.directory / ('hidden-' + str(index))
                path.write_bytes(json.dumps(output).encode('ascii'))
                self.assertEqual(self.check(path)['reason'], 'foreign_output_field')

    def test_root_cohort_and_provenance_key_presence_refuse_malformed_shapes(self):
        original = json.loads(self.artifact.read_bytes())
        post = original['blog_posts'][0]
        for index, value in enumerate((None, [], {}, {'blog_posts': {}}, {'blog_posts': None},
                                       {'blog_posts': []}, {'blog_posts': [post, post]},
                                       {'blog_posts': [None]}, {'blog_posts': [True]})):
            with self.subTest(shape=index):
                path = self.h.directory / ('shape-' + str(index))
                path.write_bytes(json.dumps(value).encode('ascii'))
                self.assertEqual(self.check(path)['envelope_binding'], 'REFUSED')
        for field in ('source_action_id', 'source_topic'):
            output = copy.deepcopy(original)
            output['blog_posts'][0].pop(field)
            path = self.h.directory / ('missing-' + field)
            path.write_bytes(json.dumps(output).encode('ascii'))
            self.assertEqual(self.check(path)['reason'], 'missing_provenance_field')

    def test_identity_match_alone_does_not_qualify_a_foreign_outer_field(self):
        request = self.h.directory / 'request.json'
        request.write_bytes(json.dumps(self.h.request).encode('ascii'))
        output = json.loads(self.artifact.read_bytes())
        output['blog_posts'][0]['approved'] = True
        path = self.h.directory / 'identity-preserved'
        path.write_bytes(json.dumps(output).encode('ascii'))
        identity = request_parity.qualify(
            offline=True, artifact=path, request_snapshot=request,
            expected_request_sha256=hashlib.sha256(request.read_bytes()).hexdigest())
        self.assertEqual(identity['request_binding'], 'MATCH')
        self.assertIs(identity['publish_allowed'], False)
        self.assertEqual(self.check(path)['envelope_binding'], 'REFUSED')

    def test_field_order_and_nested_values_are_not_editorial_or_authenticity_approval(self):
        output = json.loads(self.artifact.read_bytes())
        post = dict(reversed(list(output['blog_posts'][0].items())))
        post['intro'] = 'SYNTHETIC altered body; separate digest/content custody required'
        post['sections'] = [{'heading': 'SYNTHETIC', 'approved': True,
                             'items': [{'content': 'SYNTHETIC', 'gatePass': True}]}]
        output['blog_posts'] = [post]
        path = self.h.directory / 'limits'
        raw = json.dumps(output).encode('ascii')
        path.write_bytes(raw)
        self.assertEqual(self.check(path)['envelope_binding'], 'MATCH')
        self.assertEqual(path.read_bytes(), raw)

    def test_strict_readers_caps_and_last_observation_are_shared(self):
        raw = self.artifact.read_bytes().rstrip()
        for index, wire in enumerate((
                raw[:-1] + b', "extra":1e309}',
                raw[:-1] + b', "extra":"\\ud800"}',
                b'{"blog_posts":[],"blog_posts":[]}')):
            path = self.h.directory / ('strict-' + str(index))
            path.write_bytes(wire)
            self.assertEqual(self.check(path)['envelope_binding'], 'REFUSED')
        cap = self.h.directory / 'cap'
        cap.write_bytes(raw + b' ' * (parity.core.ARTIFACT_LIMIT - len(raw)))
        self.assertEqual(self.check(cap)['envelope_binding'], 'MATCH')
        cap.write_bytes(cap.read_bytes() + b' ')
        self.assertEqual(self.check(cap)['reason'], 'input_too_large')
        changed = self.h.directory / 'changed'
        changed.write_bytes(raw)
        reader = parity.core._regular_bytes
        saved = []

        def mutate(path, limit):
            result = reader(path, limit)
            path.write_bytes(path.read_bytes() + b' ')
            saved.append(snapshot(path))
            return result

        with patch.object(parity.core, '_regular_bytes', mutate):
            result = parity.qualify(offline=True, artifact=changed)
        self.assertEqual(result['reason'], 'input_set_changed')
        self.assertEqual(snapshot(changed), saved[0])

    def test_default_off_and_cli_private_reports_never_grant_authority(self):
        with patch.object(parity.core, '_input_signature', side_effect=AssertionError('OFF stat')), \
                patch.object(parity.core, '_regular_bytes', side_effect=AssertionError('OFF read')):
            out = io.StringIO()
            with patch('sys.stdout', out):
                self.assertEqual(parity.main(['--artifact', 'SYNTHETIC_PRIVATE_CANARY']), 0)
            self.assertEqual(json.loads(out.getvalue())['envelope_binding'], 'DISABLED')
            self.assertNotIn('CANARY', out.getvalue())
        wrong = self.h.directory / 'SYNTHETIC_PRIVATE_CANARY'
        output = json.loads(self.artifact.read_bytes())
        output['approved'] = True
        wrong.write_bytes(json.dumps(output).encode('ascii'))
        for path, status, binding in ((self.artifact, 0, 'MATCH'), (wrong, 1, 'REFUSED')):
            out, err = io.StringIO(), io.StringIO()
            with patch('sys.stdout', out), patch('sys.stderr', err):
                self.assertEqual(parity.main(['--offline', '--artifact', str(path)]), status)
            self.assertEqual(err.getvalue(), '')
            self.assertNotIn('CANARY', out.getvalue())
            value = json.loads(out.getvalue())
            self.assertEqual(value['envelope_binding'], binding)
            self.assertEqual(value['status'], 'HOLD')
            self.assertIs(value['publish_allowed'], False)


if __name__ == '__main__':
    unittest.main()
