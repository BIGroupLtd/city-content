"""MIG-0819: isolated locale parity of pinned synthetic draft output."""
import copy
import hashlib
import io
import json
import locale
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import test_city_producer_bank_boundary as boundary

CONFIG = boundary.FIXTURE.parent / 'locale-output-config.json'
RESULT = boundary.FIXTURE.parent / 'locale-output-result.json'
RUN_ID = '0123456789abcdef0123456789abcdef'


def locale_probe():
    """Child only: real pinned generate/CLI, with synthetic callbacks."""
    boundary.BankBoundary.setUpClass()
    h = boundary.BankBoundary()
    try:
        h.setUp()
        expected_config = CONFIG.read_bytes().removesuffix(b'\n')
        expected_result = RESULT.read_bytes()
        expected = json.loads(expected_result)
        post = json.loads(expected_config)['blog_posts'][0]
        h.request['source_action_id'] = post.pop('source_action_id')
        h.request['topic'] = post.pop('source_topic')
        request_file = h.directory / 'request.json'
        # Native Path.read_text is locale dependent. ASCII escaped input keeps
        # this test on OUTPUT parity, without claiming raw UTF-8 input parity.
        request_file.write_bytes(json.dumps(h.request, ensure_ascii=True).encode('ascii'))
        assertion = unittest.TestCase()
        callback_holds = expected['native_violations']
        writer = h.writer(post, violations=callback_holds)
        snapshots = {}
        original_transport = h.draft.urllib.request.urlopen
        with patch.dict(os.environ, {}, clear=True), \
                patch.object(socket, 'getaddrinfo', side_effect=AssertionError('DNS')), \
                patch.object(socket, 'create_connection', side_effect=AssertionError('network')), \
                patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network')), \
                patch.object(h.draft.uuid, 'uuid4', return_value=Mock(hex=RUN_ID)):
            direct = h.directory / 'direct'
            result = h.draft.generate(copy.deepcopy(h.request), direct, writer=writer)
            assertion.assertEqual(result, expected)
            for name, raw in (('site-config.json', expected_config),
                              ('draft-result.json', expected_result)):
                assertion.assertEqual((direct / name).read_bytes(), raw)
                meta = (direct / name).stat()
                snapshots[name] = (raw, meta.st_ino, meta.st_mode, meta.st_size, meta.st_mtime_ns)
            cli = h.directory / 'cli'
            out, err = io.StringIO(), io.StringIO()
            with patch.object(h.draft, 'load_writer', return_value=writer), \
                    patch('sys.stdout', out), patch('sys.stderr', err):
                status = h.draft.main(['--request', str(request_file),
                                       '--artifacts-dir', str(cli)])
            assertion.assertEqual((status, out.getvalue(), err.getvalue()), (0, '', ''))
            assertion.assertEqual(writer['generate_blog'].call_count, 2)
            assertion.assertEqual(writer['_final_post_violations'].call_count, 2)
            assertion.assertEqual(writer['_count_post_words'].call_count, 2)
            assertion.assertIs(h.draft.urllib.request.urlopen, original_transport)
            for name, (raw, inode, mode, size, mtime) in snapshots.items():
                assertion.assertEqual((cli / name).read_bytes(), raw)
                meta = (direct / name).stat()
                assertion.assertEqual(((direct / name).read_bytes(), meta.st_ino,
                                       meta.st_mode, meta.st_size, meta.st_mtime_ns),
                                      (raw, inode, mode, size, mtime))
            assertion.assertEqual(json.loads((cli / 'draft-result.json').read_bytes()), expected)
            assertion.assertTrue(expected_result.isascii())
            assertion.assertFalse(expected_config.isascii())
            assertion.assertEqual(hashlib.sha256(expected_config).hexdigest(), expected['artifactSHA256'])
            assertion.assertEqual(expected['gatePass'], 'absent')
            assertion.assertEqual(expected['status'], 'draft_only')
        return {'config_sha256': hashlib.sha256(expected_config).hexdigest(),
                'result_sha256': hashlib.sha256(expected_result).hexdigest(),
                'encoding': locale.getpreferredencoding(False),
                'utf8_mode': sys.flags.utf8_mode, 'writer_calls': 2}
    finally:
        h.doCleanups()


class OutputLocale(unittest.TestCase):
    def test_actual_output_and_cli_match_frozen_bytes_across_isolated_locales(self):
        source = os.environ.get('CITY_PRODUCER_SOURCE')
        if not source:
            self.fail('CITY_PRODUCER_SOURCE must name the pinned offline source file')
        code = (
            "import json, sys; sys.path.insert(0, " + repr(str(boundary.ROOT / 'tests')) + "); "
            "from test_city_producer_output_locale import locale_probe; "
            "print(json.dumps(locale_probe(), sort_keys=True))"
        )
        results = []
        # -I ignores PYTHON* env settings. Explicit -X makes the intended
        # encoding mode authoritative; LC_ALL=C disables locale coercion.
        for language, utf8_mode in (('C', 0), ('C', 1), ('C.utf8', 0)):
            with self.subTest(locale=language, utf8_mode=utf8_mode), tempfile.TemporaryDirectory() as scratch:
                env = {'CITY_PRODUCER_SOURCE': str(Path(source).resolve()),
                       'LC_ALL': language, 'LANG': language, 'TMPDIR': scratch}
                process = subprocess.run(
                    [sys.executable, '-I', '-B', '-X', 'utf8=' + str(utf8_mode), '-c', code],
                    env=env, capture_output=True, timeout=30)
                self.assertEqual(process.returncode, 0, process.stderr.decode('ascii', errors='backslashreplace'))
                self.assertEqual(process.stderr, b'')
                value = json.loads(process.stdout.decode('ascii'))
                self.assertEqual(value['utf8_mode'], utf8_mode)
                if language == 'C' and utf8_mode == 0:
                    self.assertIn(value['encoding'].lower(), ('ascii', 'ansi_x3.4-1968'))
                else:
                    self.assertEqual(value['encoding'].lower().replace('-', ''), 'utf8')
                self.assertEqual(value['writer_calls'], 2)
                results.append((value['config_sha256'], value['result_sha256']))
        self.assertEqual(len(results), 3)
        self.assertEqual(len(set(results)), 1)
        self.assertEqual(results[0][0], '2aebc1db8a8dc87b612eabdbcbe6b7235d0bcc61770b7e93fd747b4746aabc1e')


if __name__ == '__main__':
    unittest.main()
