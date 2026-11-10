"""MIG-0804: real pinned draft artifacts, synthetic failures, no publication."""
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary
from offline_output_transfer import inspect_transfer


class OutputTransfer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        boundary.BankBoundary.setUpClass()

    def setUp(self):
        self.h = boundary.BankBoundary()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        self.sender = self.h.directory / 'sender'
        self.h.draft.generate(self.h.request, self.sender, writer=self.h.writer())
        self.receipt_hash = hashlib.sha256(
            (self.sender / 'draft-result.json').read_bytes()).hexdigest()

    def inspect(self, directory, name):
        evidence = self.h.directory / (name + '.json')
        before = {p.name: p.read_bytes() for p in directory.iterdir()}
        result = inspect_transfer(directory, evidence,
                                  expected_receipt_sha256=self.receipt_hash)
        self.assertEqual(result, json.loads(evidence.read_text()))
        self.assertEqual(result['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(result[key], False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in directory.iterdir()})
        saved = evidence.read_bytes()
        with self.assertRaises(FileExistsError):
            inspect_transfer(directory, evidence,
                             expected_receipt_sha256=self.receipt_hash)
        self.assertEqual(saved, evidence.read_bytes())
        self.assertNotIn('Synthetic title', evidence.read_text())
        return result

    def test_missing_and_truncated_delivery_then_complete_retry_remain_held(self):
        for name in ('site-config.json', 'draft-result.json'):
            original = (self.sender / name).read_bytes()
            for length in (None, 0, 1, len(original) // 2, len(original) - 1):
                with self.subTest(file=name, length=length):
                    target = self.h.directory / 'delivery'
                    shutil.copytree(self.sender, target)
                    if length is None:
                        (target / name).unlink()
                    else:
                        (target / name).write_bytes(original[:length])
                    result = self.inspect(target, name + str(length))
                    self.assertNotEqual(result['reason'], 'complete_draft_still_held')
                    shutil.rmtree(target)
        self.assertEqual(self.inspect(self.sender, 'retry')['reason'],
                         'complete_draft_still_held')

    def test_valid_json_substitution_and_forged_receipt_are_refused(self):
        target = self.h.directory / 'substituted'
        shutil.copytree(self.sender, target)
        (target / 'site-config.json').write_text('{"blog_posts": []}')
        self.assertEqual(self.inspect(target, 'changed-body')['reason'], 'artifact_mismatch')
        receipt = json.loads((target / 'draft-result.json').read_text())
        receipt['artifactSHA256'] = hashlib.sha256(
            (target / 'site-config.json').read_bytes()).hexdigest()
        receipt['gatePass'] = True
        (target / 'draft-result.json').write_text(json.dumps(receipt))
        self.assertEqual(self.inspect(target, 'forged')['reason'], 'receipt_custody_mismatch')

    def test_interrupted_producer_write_preserves_partial_output_and_blocks_replay(self):
        for filename in ('site-config.json', 'draft-result.json'):
            with self.subTest(filename=filename):
                output = self.h.directory / filename
                original_bytes, original_text = Path.write_bytes, Path.write_text

                def interrupt_bytes(path, data):
                    if path.parent == output and path.name == filename:
                        original_bytes(path, data[:len(data) // 2])
                        raise OSError('synthetic interruption')
                    return original_bytes(path, data)

                def interrupt_text(path, data, *args, **kwargs):
                    if path.parent == output and path.name == filename:
                        original_text(path, data[:len(data) // 2], *args, **kwargs)
                        raise OSError('synthetic interruption')
                    return original_text(path, data, *args, **kwargs)

                writer = self.h.writer()
                with patch.object(Path, 'write_bytes', interrupt_bytes), \
                        patch.object(Path, 'write_text', interrupt_text):
                    with self.assertRaises(OSError):
                        self.h.draft.generate(self.h.request, output, writer=writer)
                writer['generate_blog'].assert_called_once()
                self.assertEqual(self.inspect(output, 'interrupted-' + filename)['reason'],
                                 'incomplete_transfer')
                before = {p.name: p.read_bytes() for p in output.iterdir()}
                retry = self.h.writer()
                with self.assertRaises(FileExistsError):
                    self.h.draft.generate(self.h.request, output, writer=retry)
                retry['generate_blog'].assert_not_called()
                self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})
