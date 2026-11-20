"""MIG-0819: pinned draft gate ordering, synthetic callbacks, no writer loading."""
import copy
import hashlib
import io
import json
import os
import socket
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary


def snapshot(directory):
    return {p.name: (p.read_bytes(), p.stat().st_ino, p.stat().st_mode,
                     p.stat().st_size, p.stat().st_mtime_ns)
            for p in directory.iterdir()}


class FinalGateParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        boundary.BankBoundary.setUpClass()

    def setUp(self):
        self.h = boundary.BankBoundary()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        for target in (patch.dict(os.environ, {}, clear=True),
                       patch.object(socket, 'getaddrinfo', side_effect=AssertionError('DNS')),
                       patch.object(socket, 'create_connection', side_effect=AssertionError('network')),
                       patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network'))):
            target.start()
            self.addCleanup(target.stop)
        self.accepted = self.h.directory / 'retained'
        self.h.draft.generate(self.h.request, self.accepted, writer=self.h.writer())
        self.retained = snapshot(self.accepted)

    def assert_retained(self):
        self.assertEqual(snapshot(self.accepted), self.retained)

    def test_cleanup_precedes_both_gates_then_projection_and_hash(self):
        h = self.h
        post = dict(h.post, title='A\u200bB\u00a0C', intro='e\u0301\u2060X',
                    meta_title='M\ufeffN', meta_description='D\u202fE', excerpt='F\u00adG',
                    sections=[{'heading': 'H\u202eI', 'items': [
                        {'subtitle': 'S\u034fT', 'content': 'C\u200dD'}]}],
                    citations=[{'title': 'R\u2066S', 'url': 'https://sources.example/a%20b'}],
                    gatePass=True, source_action_id='forged', source_topic='forged')
        cleaned = copy.deepcopy(post)
        cleaned.update(title='AB C', intro='e\u0301X', meta_title='MN',
                       meta_description='D E', excerpt='FG')
        cleaned['sections'][0]['heading'] = 'HI'
        cleaned['sections'][0]['items'][0] = {'subtitle': 'ST', 'content': 'CD'}
        cleaned['citations'][0]['title'] = 'RS'
        events = []
        writer = h.writer(post)

        def final(value, trade):
            events.append('final')
            self.assertEqual(value, cleaned)
            self.assertEqual(trade, h.request['trade'])
            return ['SYNTHETIC hold']

        def count(value):
            events.append('count')
            self.assertEqual(events, ['final', 'count'])
            self.assertEqual(value, cleaned)
            return 1999

        writer['_final_post_violations'].side_effect = final
        writer['_count_post_words'].side_effect = count
        target = h.directory / 'ordered'
        result = h.draft.generate(h.request, target, writer=writer)
        expected = {k: cleaned[k] for k in ('title', 'slug', 'intro', 'sections', 'citations')}
        expected.update(source_action_id=h.request['source_action_id'], source_topic=h.request['topic'])
        raw = (target / 'site-config.json').read_bytes()
        # Independent literal projection, not the production cleaner/serializer.
        self.assertEqual(json.loads(raw), {'blog_posts': [expected]})
        self.assertEqual(result['artifactSHA256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(result['native_violations'], ['SYNTHETIC hold', 'LENGTH: below hard floor'])
        self.assertEqual(result['gatePass'], 'absent')
        self.assertEqual(result['status'], 'draft_only')
        writer['generate_blog'].assert_called_once()
        writer['_final_post_violations'].assert_called_once()
        writer['_count_post_words'].assert_called_once()
        self.assert_retained()

    def test_hidden_source_url_refuses_before_gates_and_output(self):
        h = self.h
        for index, hidden in enumerate(('\u200b', '\ufeff', '\u202e', '\u00a0', '\u202f')):
            with self.subTest(hidden=repr(hidden)):
                post = dict(h.post, citations=[{'title': 'SYNTHETIC',
                            'url': 'https://sources.example/' + hidden + 'manual'}])
                writer = h.writer(post)
                target = h.directory / ('source-' + str(index))
                with self.assertRaisesRegex(ValueError, '^hidden_unicode_in_source_url$'):
                    h.draft.generate(h.request, target, writer=writer)
                writer['generate_blog'].assert_called_once()
                writer['_final_post_violations'].assert_not_called()
                writer['_count_post_words'].assert_not_called()
                self.assertEqual(list(target.iterdir()), [])
                self.assert_retained()

    def test_gate_exceptions_preserve_reserved_output_and_transport(self):
        h = self.h
        for stage in ('_final_post_violations', '_count_post_words'):
            for error in (ValueError, RuntimeError, OSError):
                with self.subTest(stage=stage, error=error.__name__):
                    writer = h.writer()
                    writer[stage].side_effect = error('SYNTHETIC_PRIVATE_CANARY')
                    target = h.directory / (stage + error.__name__)
                    original = h.draft.urllib.request.urlopen
                    with self.assertRaises(error):
                        h.draft.generate(h.request, target, writer=writer)
                    self.assertIs(h.draft.urllib.request.urlopen, original)
                    writer['generate_blog'].assert_called_once()
                    writer['_final_post_violations'].assert_called_once()
                    self.assertEqual(writer['_count_post_words'].call_count,
                                     0 if stage == '_final_post_violations' else 1)
                    self.assertEqual(list(target.iterdir()), [])
                    retry = h.writer()
                    with self.assertRaises(FileExistsError):
                        h.draft.generate(h.request, target, writer=retry)
                    retry['generate_blog'].assert_not_called()
                    self.assert_retained()

    def test_cli_gate_failure_is_redacted_and_following_sibling_is_independent(self):
        h = self.h
        request_file = h.directory / 'request.json'
        request_file.write_text(json.dumps(h.request))
        for stage in ('_final_post_violations', '_count_post_words'):
            with self.subTest(stage=stage):
                writer = h.writer()
                writer[stage].side_effect = RuntimeError('SYNTHETIC_PRIVATE_CANARY')
                target = h.directory / ('cli-' + stage)
                out, err = io.StringIO(), io.StringIO()
                with patch.object(h.draft, 'load_writer', return_value=writer), \
                        patch('sys.stdout', out), patch('sys.stderr', err):
                    status = h.draft.main(['--request', str(request_file), '--artifacts-dir', str(target)])
                self.assertEqual(status, 1)
                self.assertEqual(out.getvalue(), '')
                self.assertEqual(err.getvalue(), 'Draft generation stopped: RuntimeError\n')
                self.assertEqual(list(target.iterdir()), [])
                next_path = h.directory / ('next-' + stage)
                result = h.draft.generate(h.request, next_path, writer=h.writer())
                self.assertEqual(result['native_violations'], [])
                self.assertEqual(result['status'], 'draft_only')
                self.assertEqual(result['gatePass'], 'absent')
                self.assert_retained()


if __name__ == '__main__':
    unittest.main()
