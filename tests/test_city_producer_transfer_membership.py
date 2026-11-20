"""Offline bundle membership: static synthetic bytes, no writer invocation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import offline_output_transfer as transfer


class TransferMembership(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.bundle = self.root / 'bundle'
        self.bundle.mkdir()
        body = json.dumps({'blog_posts': [{'source_action_id': 'synthetic-action'}]}).encode()
        receipt = json.dumps({'builderRunId': 'synthetic-run', 'gatePass': 'absent',
                              'status': 'draft_only',
                              'artifactSHA256': hashlib.sha256(body).hexdigest()}).encode()
        (self.bundle / 'site-config.json').write_bytes(body)
        (self.bundle / 'draft-result.json').write_bytes(receipt)
        self.custody = dict(offline=True, expected_run_id='synthetic-run',
                            expected_action_id='synthetic-action',
                            expected_receipt_sha256=hashlib.sha256(receipt).hexdigest())

    def inspect(self, label):
        evidence = self.root / (label + '.json')
        result = transfer.inspect_transfer(self.bundle, evidence, **self.custody)
        self.assertEqual(result, json.loads(evidence.read_bytes()))
        self.assertEqual(result['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(result[key], False)
        return result

    def test_exact_pair_stays_held_and_off_does_not_inspect_members(self):
        self.assertEqual(self.inspect('pair')['reason'], 'complete_draft_still_held')
        with patch.object(transfer, '_bundle_members', side_effect=AssertionError('read')):
            self.assertEqual(transfer.inspect_transfer()['reason'], 'offline_not_requested')

    def test_extra_files_and_directories_refused_without_reading_or_deleting_them(self):
        for name in ('draft-result.json.part', 'site-config.json.bak',
                     '.hidden-canary', 'publish-ready.json', 'nested'):
            with self.subTest(name=name):
                extra = self.bundle / name
                if name == 'nested':
                    extra.mkdir()
                else:
                    extra.write_bytes(b'SYNTHETIC_PRIVATE_CANARY')
                before = extra.lstat()
                with patch.object(Path, 'read_bytes', side_effect=AssertionError('payload read')):
                    result = transfer.inspect_transfer(
                        self.bundle, self.root / (name + '.evidence'), **self.custody)
                self.assertEqual(result['reason'], 'unexpected_bundle_members')
                self.assertEqual(result['observed'], {})
                self.assertIs(result['publish_allowed'], False)
                saved = (self.root / (name + '.evidence')).read_text()
                self.assertNotIn(name, saved)
                self.assertNotIn('SYNTHETIC_PRIVATE_CANARY', saved)
                after = extra.lstat()
                self.assertEqual((before.st_ino, before.st_size, before.st_mtime_ns),
                                 (after.st_ino, after.st_size, after.st_mtime_ns))
                extra.rmdir() if name == 'nested' else extra.unlink()

    def test_new_sidecar_during_read_is_refused_and_retained(self):
        original = Path.read_bytes

        def read(path):
            data = original(path)
            if path == self.bundle / 'site-config.json':
                (self.bundle / 'late-sidecar').write_bytes(b'synthetic')
            return data

        with patch.object(Path, 'read_bytes', read):
            result = self.inspect('drift')
        self.assertEqual(result['reason'], 'bundle_members_changed')
        self.assertEqual((self.bundle / 'late-sidecar').read_bytes(), b'synthetic')

    def test_retry_preserves_refused_inventory_and_prior_evidence(self):
        extra = self.bundle / 'sidecar'
        extra.write_bytes(b'synthetic')
        first = self.inspect('first')
        self.assertEqual(first['reason'], 'unexpected_bundle_members')
        evidence = self.root / 'first.json'
        saved = evidence.read_bytes()
        with self.assertRaises(FileExistsError):
            transfer.inspect_transfer(self.bundle, evidence, **self.custody)
        self.assertEqual(saved, evidence.read_bytes())
        self.assertEqual(self.inspect('new-attempt')['reason'], 'unexpected_bundle_members')
        self.assertEqual(extra.read_bytes(), b'synthetic')
