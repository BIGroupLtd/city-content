"""Pinned POSIX output-mode parity; unprivileged, synthetic and offline only."""
from contextlib import contextmanager
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import stat
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary


@contextmanager
def masked(value):
    previous = os.umask(value)
    try:
        yield
    finally:
        os.umask(previous)


def snapshot(directory):
    return {p.name: (p.read_bytes(), p.stat().st_ino, p.stat().st_mode,
                     p.stat().st_size, p.stat().st_mtime_ns)
            for p in directory.iterdir()}


class OutputPermissions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Root bypasses ordinary DAC write denial; never count that as parity.
        if os.name != 'posix' or os.geteuid() == 0:
            raise RuntimeError('unprivileged POSIX executor required; no permission-test skip fallback')
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

    def test_saved_umask_matrix_preserves_private_reservation_and_native_file_modes(self):
        h = self.h
        fixture = json.loads((boundary.FIXTURE.parent / 'output-permissions.json').read_text())
        self.assertEqual({k: fixture[k] for k in ('synthetic_only', 'enabled', 'approved',
                                                'not_runtime_queue', 'status')},
                         dict(synthetic_only=True, enabled=False, approved=False,
                              not_runtime_queue=True, status='HOLD'))
        self.assertEqual(fixture['cases'], [
            dict(umask='000', directory='700', file='666'),
            dict(umask='002', directory='700', file='664'),
            dict(umask='007', directory='700', file='660'),
            dict(umask='022', directory='700', file='644'),
            dict(umask='027', directory='700', file='640'),
            dict(umask='077', directory='700', file='600')])
        for case in fixture['cases']:
            with self.subTest(umask=case['umask']):
                target = h.directory / ('mask-' + case['umask'])
                writer = h.writer()

                def observe(*args, **kwargs):
                    self.assertTrue(target.is_dir())
                    self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o700)
                    self.assertEqual(list(target.iterdir()), [])
                    return dict(h.post)

                writer['generate_blog'].side_effect = observe
                with masked(int(case['umask'], 8)):
                    result = h.draft.generate(h.request, target, writer=writer)
                self.assertEqual(stat.S_IMODE(target.stat().st_mode), int(case['directory'], 8))
                self.assertEqual(target.stat().st_uid, os.geteuid())
                self.assertEqual(sorted(p.name for p in target.iterdir()),
                                 ['draft-result.json', 'site-config.json'])
                for path in target.iterdir():
                    metadata = path.stat()
                    self.assertTrue(stat.S_ISREG(metadata.st_mode))
                    self.assertEqual(stat.S_IMODE(metadata.st_mode), int(case['file'], 8))
                    self.assertEqual(metadata.st_uid, os.geteuid())
                    self.assertEqual(metadata.st_nlink, 1)
                raw = (target / 'site-config.json').read_bytes()
                self.assertEqual(result['artifactSHA256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(json.loads((target / 'draft-result.json').read_bytes()), result)
                self.assertEqual(result['status'], 'draft_only')
                self.assertEqual(result['gatePass'], 'absent')
                writer['generate_blog'].assert_called_once()
                self.assertEqual(snapshot(self.accepted), self.retained)

    def test_owner_restricting_umasks_refuse_first_artifact_without_chmod_repair(self):
        h = self.h
        # Native target.mkdir(0700) honors umask. Losing owner write or execute
        # must not be mistaken for a complete pair or repaired by this test.
        for mask, expected in ((0o200, 0o500), (0o100, 0o600), (0o700, 0o000)):
            with self.subTest(umask=oct(mask)):
                target = h.directory / ('owner-' + str(mask))
                writer = h.writer()
                original = h.draft.urllib.request.urlopen
                try:
                    with masked(mask), self.assertRaises(PermissionError):
                        h.draft.generate(h.request, target, writer=writer)
                    self.assertEqual(stat.S_IMODE(target.stat().st_mode), expected)
                    writer['generate_blog'].assert_called_once()
                    writer['_final_post_violations'].assert_called_once()
                    writer['_count_post_words'].assert_called_once()
                    self.assertIs(h.draft.urllib.request.urlopen, original)
                    # Access restored ONLY for test evidence inspection/cleanup,
                    # after native refusal and original mode assertions above.
                finally:
                    if target.exists():
                        target.chmod(0o700)
                self.assertEqual(list(target.iterdir()), [])
                self.assertEqual(snapshot(self.accepted), self.retained)

    def test_destination_creation_errors_refuse_before_writer_or_native_loader(self):
        h = self.h
        parent_file = h.directory / 'file-parent'
        parent_file.write_bytes(b'SYNTHETIC retained parent')
        denied = h.directory / 'denied-parent'
        denied.mkdir(mode=0o500)
        self.addCleanup(denied.chmod, 0o700)
        before = parent_file.read_bytes(), parent_file.stat()
        cases = ((h.directory / 'missing-parent' / 'output', FileNotFoundError),
                 (parent_file / 'output', NotADirectoryError),
                 (denied / 'output', PermissionError))
        for target, error in cases:
            with self.subTest(error=error.__name__):
                writer = h.writer()
                with patch.object(h.draft, 'load_writer', side_effect=AssertionError('native loader')) as loader:
                    with self.assertRaises(error):
                        h.draft.generate(h.request, target, writer=writer)
                    loader.assert_not_called()
                for callback in writer.values():
                    callback.assert_not_called()
                self.assertFalse(target.exists())
                self.assertEqual(snapshot(self.accepted), self.retained)
        self.assertEqual(parent_file.read_bytes(), before[0])
        after = parent_file.stat()
        self.assertEqual((after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns),
                         (before[1].st_ino, before[1].st_mode, before[1].st_size, before[1].st_mtime_ns))
        self.assertEqual(list(denied.iterdir()), [])

    def test_actual_cli_permission_denial_is_redacted_without_writer_dispatch(self):
        h = self.h
        parent = h.directory / 'SYNTHETIC_PRIVATE_CANARY'
        parent.mkdir(mode=0o500)
        self.addCleanup(parent.chmod, 0o700)
        request_file = h.directory / 'request.json'
        request_file.write_text(json.dumps(h.request))
        out, err = io.StringIO(), io.StringIO()
        with patch.object(h.draft, 'load_writer', side_effect=AssertionError('native loader')) as loader, \
                patch('sys.stdout', out), patch('sys.stderr', err):
            result = h.draft.main(['--request', str(request_file),
                                   '--artifacts-dir', str(parent / 'output')])
        loader.assert_not_called()
        self.assertEqual(result, 1)
        self.assertEqual(out.getvalue(), '')
        self.assertEqual(err.getvalue(), 'Draft generation stopped: PermissionError\n')
        self.assertEqual(list(parent.iterdir()), [])
        self.assertEqual(snapshot(self.accepted), self.retained)


if __name__ == '__main__':
    unittest.main()
