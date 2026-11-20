"""Static synthetic transfer evidence, no producer or writer invocation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import offline_output_transfer as transfer


class EvidenceCompletion(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.bundle = self.root / 'bundle'
        self.bundle.mkdir()
        body = b'{"blog_posts":[{"source_action_id":"synthetic-action"}]}'
        receipt = json.dumps({'builderRunId': 'synthetic-run', 'status': 'draft_only',
                              'gatePass': 'absent',
                              'artifactSHA256': hashlib.sha256(body).hexdigest()}).encode()
        (self.bundle / 'site-config.json').write_bytes(body)
        self.body = body
        (self.bundle / 'draft-result.json').write_bytes(receipt)
        self.custody = dict(offline=True, expected_run_id='synthetic-run',
                            expected_action_id='synthetic-action',
                            expected_receipt_sha256=hashlib.sha256(receipt).hexdigest())

    def test_success_flushes_then_syncs_before_return_and_default_off_does_neither(self):
        evidence = self.root / 'saved.json'
        # At fsync the buffered bytes must already be visible through a new read.
        def sync(descriptor):
            self.assertGreaterEqual(descriptor, 0)
            self.assertEqual(json.loads(evidence.read_bytes())['status'], 'HOLD')

        with patch.object(transfer.os, 'fsync', side_effect=sync) as synced:
            result = transfer.inspect_transfer(self.bundle, evidence, **self.custody)
            synced.assert_called_once()
            synced.reset_mock()
            transfer.inspect_transfer()
            synced.assert_not_called()
        self.assertEqual(json.loads(evidence.read_bytes()), result)
        self.assertIs(result['publish_allowed'], False)

    def test_sync_failures_propagate_on_complete_and_refused_input_without_overwrite(self):
        for label in ('complete', 'missing', 'extra', 'custody'):
            with self.subTest(label=label):
                (self.bundle / 'site-config.json').write_bytes(self.body)
                (self.bundle / 'extra').unlink(missing_ok=True)
                custody = dict(self.custody)
                if label == 'missing':
                    (self.bundle / 'site-config.json').unlink()
                elif label == 'extra':
                    (self.bundle / 'extra').touch()
                elif label == 'custody':
                    custody['expected_run_id'] = None
                evidence = self.root / (label + '.json')
                before = {p.name: p.read_bytes() for p in self.bundle.iterdir()}
                with patch.object(transfer.os, 'fsync', side_effect=OSError('synthetic sync')):
                    with self.assertRaisesRegex(OSError, 'synthetic sync'):
                        transfer.inspect_transfer(self.bundle, evidence, **custody)
                saved = evidence.read_bytes()
                self.assertEqual(json.loads(saved)['status'], 'HOLD')
                with self.assertRaises(FileExistsError):
                    transfer.inspect_transfer(self.bundle, evidence, **custody)
                self.assertEqual(saved, evidence.read_bytes())
                self.assertEqual(before, {p.name: p.read_bytes() for p in self.bundle.iterdir()})

    def test_short_write_and_flush_failure_never_return_a_result(self):
        original = Path.open
        for failure in ('write', 'zero', 'short', 'flush'):
            with self.subTest(failure=failure):
                evidence = self.root / (failure + '.json')

                class Faulted:
                    def __init__(self, real):
                        self.real = real

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        return self.real.__exit__(*args)

                    def write(self, payload):
                        if failure == 'write':
                            raise OSError('synthetic write')
                        if failure == 'zero':
                            return 0
                        if failure == 'short':
                            return self.real.write(payload[:7])
                        return self.real.write(payload)

                    def flush(self):
                        if failure == 'flush':
                            raise OSError('synthetic flush')
                        self.real.flush()

                    def fileno(self):
                        return self.real.fileno()

                def opened(path, *args, **kwargs):
                    real = original(path, *args, **kwargs)
                    return Faulted(real) if path == evidence else real

                with patch.object(Path, 'open', opened), \
                        patch.object(transfer.os, 'fsync') as synced:
                    with self.assertRaises(OSError):
                        transfer.inspect_transfer(self.bundle, evidence, **self.custody)
                    synced.assert_not_called()
                saved = evidence.read_bytes()
                self.assertEqual(bool(saved), failure not in ('write', 'zero'))
                with self.assertRaises(FileExistsError):
                    transfer.inspect_transfer(self.bundle, evidence, **self.custody)
                self.assertEqual(saved, evidence.read_bytes())
