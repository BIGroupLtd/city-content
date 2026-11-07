"""E317 evidence and assumptions; no source download or production invocation."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import test_city_producer_bank_boundary as boundary

PIN = {
    'repository': 'BIGroupLtd/ironclad-infra',
    'commit': '0bd7ae3754acbf056558c89b87240bedda98a7aa',
    'path': 'scripts/city_blog_draft.py',
    'sha256': '5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06',
}


class SourceEvidence(unittest.TestCase):
    def test_explicit_source_matches_immutable_pin(self):
        fixture = json.loads(boundary.FIXTURE.read_text())
        self.assertEqual(fixture['producer_source'], PIN)
        source = Path(os.environ['CITY_PRODUCER_SOURCE']).read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), PIN['sha256'])

    def test_source_configuration_errors_fail_without_skips(self):
        # Exercise the actual suite entrypoint in isolated interpreters. Do not
        # substitute a fake producer or let unittest turn missing custody green.
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'wrong.py'
            sentinel = Path(directory) / 'executed'
            wrong.write_text('from pathlib import Path\nPath(' + repr(str(sentinel)) + ').touch()\n')
            for source, error in ((None, 'CITY_PRODUCER_SOURCE must name'),
                                  (str(Path(directory) / 'missing.py'), 'FileNotFoundError'),
                                  (str(wrong), 'producer_source_hash_mismatch')):
                env = dict(os.environ)
                env.pop('CITY_PRODUCER_SOURCE', None)
                if source is not None:
                    env['CITY_PRODUCER_SOURCE'] = source
                with self.subTest(source=source):
                    result = subprocess.run(
                        [sys.executable, '-I', '-B', '-m', 'unittest', 'discover',
                         '-s', str(boundary.ROOT / 'tests'),
                         '-p', 'test_city_producer_bank_boundary.py', '-v'],
                        env=env, capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(error, result.stderr)
                    self.assertNotIn('skipped=', result.stderr)
            self.assertFalse(sentinel.exists())


class ProducerAssumptions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        boundary.BankBoundary.setUpClass()

    def setUp(self):
        self.harness = boundary.BankBoundary()
        self.addCleanup(self.harness.doCleanups)
        self.harness.setUp()

    def test_exclusions_are_required_before_generation_or_output(self):
        request = dict(self.harness.request)
        request.pop('exclusions_file')
        self.harness.refuse_before_generation(request, 'draft_exclusions_required')

    def test_existing_output_is_never_overwritten(self):
        h = self.harness
        output = h.directory / 'existing'
        output.mkdir()
        sentinel = output / 'prior-draft'
        sentinel.write_bytes(b'synthetic prior artifact')
        writer = h.writer()
        with self.assertRaises(FileExistsError):
            h.draft.generate(h.request, output, writer=writer)
        writer['generate_blog'].assert_not_called()
        self.assertEqual(list(output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'synthetic prior artifact')

    def test_canonical_mapping_and_length_boundary_remain_draft_only(self):
        h = self.harness
        mapping = h.draft.HOST_MAP
        mapping.write_text(json.dumps({'allowed.example': 'www.allowed.example'}))
        writer = h.writer(words=2000)
        result = h.draft.generate(h.request, h.directory / 'boundary', writer=writer)
        research = writer['generate_blog'].call_args.kwargs['research_context']
        self.assertIn('https://www.allowed.example', research['context'])
        self.assertEqual(result['canonical_host'], 'www.allowed.example')
        self.assertEqual(result['public_origin'], 'https://www.allowed.example')
        self.assertEqual(result['canonical_host_map_sha256'],
                         hashlib.sha256(mapping.read_bytes()).hexdigest())
        self.assertEqual(result['native_violations'], [])
        self.assertEqual(result['status'], 'draft_only')
        self.assertEqual(result['gatePass'], 'absent')
        self.assertIsNone(result['reported_model'])
        self.assertTrue(result['missing_full_gate_inputs'])


if __name__ == '__main__':
    unittest.main()
