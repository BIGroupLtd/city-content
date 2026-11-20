"""Synthetic retained-evidence readback; no producer, writer or network."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import offline_output_transfer as transfer


class EvidenceReadback(unittest.TestCase):
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
        (self.bundle / 'draft-result.json').write_bytes(receipt)
        self.custody = dict(offline=True, expected_run_id='synthetic-run',
                            expected_action_id='synthetic-action',
                            expected_receipt_sha256=hashlib.sha256(receipt).hexdigest())

    def test_matching_saved_evidence_returns_held_and_off_does_not_verify(self):
        evidence = self.root / 'saved.json'
        result = transfer.inspect_transfer(self.bundle, evidence, **self.custody)
        self.assertEqual(result, json.loads(evidence.read_bytes()))
        self.assertIs(result['publish_allowed'], False)
        with patch.object(transfer, '_verify_evidence', side_effect=AssertionError('verification')):
            self.assertEqual(transfer.inspect_transfer()['reason'], 'offline_not_requested')

    def test_changed_truncated_and_appended_saved_bytes_refuse_and_remain_reserved(self):
        before = {p.name: p.read_bytes() for p in self.bundle.iterdir()}
        for kind in ('changed', 'truncated', 'appended'):
            with self.subTest(kind=kind):
                evidence = self.root / (kind + '.json')

                def corrupt(descriptor):
                    raw = evidence.read_bytes()
                    if kind == 'changed':
                        raw = raw.replace(b'"HOLD"', b'"FAIL"')
                    elif kind == 'truncated':
                        raw = raw[:-1]
                    else:
                        raw += b'X'
                    evidence.write_bytes(raw)

                with patch.object(transfer.os, 'fsync', side_effect=corrupt):
                    with self.assertRaisesRegex(OSError, 'evidence_readback_mismatch'):
                        transfer.inspect_transfer(self.bundle, evidence, **self.custody)
                saved = evidence.read_bytes()
                with self.assertRaises(FileExistsError):
                    transfer.inspect_transfer(self.bundle, evidence, **self.custody)
                self.assertEqual(saved, evidence.read_bytes())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.bundle.iterdir()})

    def test_same_bytes_replacement_path_and_symlink_are_refused_without_repair(self):
        for kind in ('replacement', 'symlink'):
            with self.subTest(kind=kind):
                evidence = self.root / (kind + '.json')
                displaced = self.root / (kind + '.displaced')

                def replace(descriptor):
                    evidence.rename(displaced)
                    if kind == 'replacement':
                        evidence.write_bytes(displaced.read_bytes())
                    else:
                        evidence.symlink_to(displaced)

                with patch.object(transfer.os, 'fsync', side_effect=replace):
                    with self.assertRaisesRegex(OSError, 'evidence_identity_changed'):
                        transfer.inspect_transfer(self.bundle, evidence, **self.custody)
                saved = displaced.read_bytes()
                with self.assertRaises(FileExistsError):
                    transfer.inspect_transfer(self.bundle, evidence, **self.custody)
                self.assertEqual(saved, displaced.read_bytes())
                self.assertEqual(evidence.is_symlink(), kind == 'symlink')

    def test_readback_io_failure_propagates_and_saved_evidence_is_not_overwritten(self):
        evidence = self.root / 'read-error.json'
        with patch.object(transfer.os, 'pread', side_effect=OSError('synthetic read')):
            with self.assertRaisesRegex(OSError, 'synthetic read'):
                transfer.inspect_transfer(self.bundle, evidence, **self.custody)
        saved = evidence.read_bytes()
        self.assertEqual(json.loads(saved)['status'], 'HOLD')
        with self.assertRaises(FileExistsError):
            transfer.inspect_transfer(self.bundle, evidence, **self.custody)
        self.assertEqual(saved, evidence.read_bytes())
