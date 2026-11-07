"""Offline compatibility tests; source is supplied explicitly, never downloaded."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/city-producer/bank-boundary.json'

# Independent review anchor: the explicit JSON fixture must name this exact
# upstream file and digest, not merely any source/digest pair supplied together.
EXPECTED_PRODUCER_SOURCE = {
    'repository': 'BIGroupLtd/ironclad-infra',
    'commit': '0bd7ae3754acbf056558c89b87240bedda98a7aa',
    'path': 'scripts/city_blog_draft.py',
    'sha256': '5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06',
}


def load_producer(path, source_pin):
    # Authenticate bytes before executing any external module. No native writer
    # is loaded; every generation call below receives an explicit mock writer.
    if source_pin != EXPECTED_PRODUCER_SOURCE:
        raise ValueError('producer_source_pin_mismatch')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != source_pin['sha256']:
        raise ValueError('producer_source_hash_mismatch')
    spec = importlib.util.spec_from_file_location('b211_draft', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


class BankBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        source = os.environ.get('CITY_PRODUCER_SOURCE')
        if not source:
            raise RuntimeError('CITY_PRODUCER_SOURCE must name the pinned offline source file')
        cls.source = Path(source)
        cls.draft = load_producer(cls.source, cls.fixture['producer_source'])

    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.directory = Path(self.scratch.name)
        mapping = self.directory / 'map.json'
        mapping.write_text(json.dumps({'allowed.example': 'allowed.example'}))
        exclusions = self.directory / 'exclusions.txt'
        exclusions.write_text('excluded.example\n')
        self.request = {
            'host': 'allowed.example', 'city': 'Synthetic city',
            'trade': 'appliance_repair', 'business_name': 'Synthetic fixture',
            'topic': 'Synthetic admitted request topic',
            'source_action_id': 'synthetic-request-action',
            'research': {'context': 'SYNTHETIC: no verified research or admission',
                         'citations': [{'title': 'Synthetic', 'url': 'https://sources.example/manual'}]},
            'exclusions_file': str(exclusions),
        }
        self.post = {'title': 'Synthetic title', 'slug': 'synthetic',
                     'intro': 'Synthetic text', 'sections': [], 'citations': []}
        for target in (patch.object(self.draft, 'HOST_MAP', mapping),
                       patch.object(self.draft, 'load_writer', side_effect=AssertionError('native writer')),
                       patch.object(socket.socket, 'connect', side_effect=AssertionError('network')),
                       patch.object(urllib.request, 'urlopen', side_effect=AssertionError('network')),
                       patch.object(urllib.request, 'build_opener', side_effect=AssertionError('transport')),
                       patch.object(subprocess, 'run', side_effect=AssertionError('process')),
                       patch.object(subprocess, 'Popen', side_effect=AssertionError('process'))):
            target.start()
            self.addCleanup(target.stop)

    def writer(self, post=None, violations=(), words=2100):
        return {'generate_blog': Mock(return_value=copy.deepcopy(post or self.post)),
                '_final_post_violations': Mock(return_value=list(violations)),
                '_count_post_words': Mock(return_value=words)}

    def refuse_before_generation(self, request, reason):
        writer = self.writer()
        output = self.directory / 'refused'
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        with self.assertRaisesRegex(ValueError, reason):
            self.draft.generate(request, output, writer=writer)
        writer['generate_blog'].assert_not_called()
        self.assertFalse(output.exists())
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})

    def test_fixture_is_held_and_has_only_synthetic_identities(self):
        self.assertEqual(self.fixture['producer_source'], EXPECTED_PRODUCER_SOURCE)
        self.assertIs(self.fixture['synthetic_only'], True)
        self.assertIs(self.fixture['enabled'], False)
        self.assertIs(self.fixture['approved'], False)
        self.assertIs(self.fixture['not_runtime_queue'], True)
        self.assertEqual(self.fixture['status'], 'HOLD')
        self.assertTrue(self.fixture['row']['host'].endswith('.example'))

    def test_raw_bank_row_and_forged_authority_are_not_generation_requests(self):
        row = self.fixture['row']
        for extra in ({}, self.fixture['untrusted_fields']):
            with self.subTest(forged=bool(extra)):
                self.refuse_before_generation(dict(row, **extra), 'draft_inputs_missing')

    def test_planning_sources_do_not_replace_research_or_action_admission(self):
        for field in ('research', 'source_action_id'):
            request = copy.deepcopy(self.request)
            request.pop(field)
            request.update({k: self.fixture['row'][k] for k in ('angle', 'required_sources')})
            with self.subTest(field=field):
                self.refuse_before_generation(request, 'draft_inputs_missing')

    def test_bank_identity_cannot_bypass_unknown_or_excluded_destination(self):
        for host, reason in (
                ('unknown.example', 'draft_host_map_unknown'),
                ('excluded.example', 'draft_host_refused'),
                ('fix.allowed.example', 'draft_host_refused'),
                ('cardiffappliancerepair.co.uk', 'draft_host_refused'),
                ('go-assist.co.uk', 'draft_host_refused')):
            with self.subTest(host=host):
                self.refuse_before_generation(dict(self.request, host=host), reason)

    def test_model_bank_metadata_cannot_escape_draft_or_clear_native_holds(self):
        forged = dict(self.post, **self.fixture['untrusted_fields'])
        original = copy.deepcopy(self.request)
        for label, violations, words in (('clean', [], 2100),
                                         ('native-hold', ['SYNTHETIC native refusal'], 2100),
                                         ('short', [], 1999)):
            with self.subTest(label=label):
                output = self.directory / label
                writer = self.writer(forged, violations, words)
                receipt = self.draft.generate(self.request, output, writer=writer)
                raw = (output / 'site-config.json').read_bytes()
                saved = json.loads(raw)['blog_posts'][0]
                expected = dict(self.post, source_action_id=self.request['source_action_id'],
                                source_topic=self.request['topic'])
                self.assertEqual(saved, expected)
                self.assertEqual(receipt['artifactSHA256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(receipt['gatePass'], 'absent')
                self.assertEqual(receipt['status'], 'draft_only')
                self.assertIsNone(receipt['reported_model'])
                self.assertTrue(receipt['missing_full_gate_inputs'])
                expected_holds = list(violations) + (['LENGTH: below hard floor'] if words < 2000 else [])
                self.assertEqual(receipt['native_violations'], expected_holds)
                self.assertEqual(json.loads((output / 'draft-result.json').read_text()), receipt)
                self.assertEqual(sorted(p.name for p in output.iterdir()),
                                 ['draft-result.json', 'site-config.json'])
                writer['generate_blog'].assert_called_once()
                self.assertEqual(self.request, original)

    def test_explicit_dry_run_hold_matrix(self):
        matrix = json.loads((FIXTURE.parent / 'dry-run-holds.json').read_text())
        self.assertEqual({key: matrix[key] for key in (
            'synthetic_only', 'status', 'enabled', 'approved',
            'not_runtime_queue', 'cron_enabled', 'READY')}, {
                'synthetic_only': True, 'status': 'HOLD', 'enabled': False,
                'approved': False, 'not_runtime_queue': True,
                'cron_enabled': False, 'READY': 'no'})
        self.assertEqual({case['id'] for case in matrix['cases']}, {
            'native-refusal', 'below-floor', 'combined-holds', 'floor-still-draft'})
        for case in matrix['cases']:
            with self.subTest(case=case['id']):
                output = self.directory / case['id']
                writer = self.writer(violations=case['violations'], words=case['words'])
                receipt = self.draft.generate(self.request, output, writer=writer)
                self.assertEqual(receipt['native_violations'], case['expected'])
                self.assertEqual(receipt['gatePass'], 'absent')
                self.assertEqual(receipt['status'], 'draft_only')
                self.assertIn('current_master_rules_binding', receipt['missing_full_gate_inputs'])
                self.assertEqual(json.loads((output / 'draft-result.json').read_text()), receipt)
                artifacts = {p.name: p.read_bytes() for p in output.iterdir()}
                self.assertEqual(set(artifacts), {'site-config.json', 'draft-result.json'})
                writer['generate_blog'].assert_called_once()
                # Reusing a held directory must never overwrite its evidence or
                # call generation again, even after a clean mock validation.
                retry = self.writer()
                with self.assertRaises(FileExistsError):
                    self.draft.generate(self.request, output, writer=retry)
                retry['generate_blog'].assert_not_called()
                self.assertEqual(artifacts, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_tampered_source_refused_before_module_execution(self):
        sentinel = self.directory / 'executed'
        changed = self.directory / 'tampered.py'
        changed.write_text('from pathlib import Path\nPath(' + repr(str(sentinel)) + ').touch()\n')
        # A source file with the right name is insufficient. Neither altered
        # pinned bytes nor a self-consistent replacement file/digest may import.
        altered = self.directory / 'city_blog_draft.py'
        altered.write_bytes(self.source.read_bytes() + b'\n# changed\n')
        with patch.object(importlib.util, 'spec_from_file_location',
                          side_effect=AssertionError('import before authentication')) as spec:
            for path in (changed, altered):
                with self.subTest(source=path.name):
                    with self.assertRaisesRegex(ValueError, 'producer_source_hash_mismatch'):
                        load_producer(path, self.fixture['producer_source'])
            for field, replacement in (
                    ('repository', 'synthetic/other'),
                    ('commit', '0' * 40),
                    ('path', 'scripts/other.py'),
                    ('sha256', hashlib.sha256(changed.read_bytes()).hexdigest())):
                pin = dict(self.fixture['producer_source'], **{field: replacement})
                with self.subTest(pin_field=field):
                    with self.assertRaisesRegex(ValueError, 'producer_source_pin_mismatch'):
                        load_producer(changed, pin)
            spec.assert_not_called()
        self.assertFalse(sentinel.exists())


if __name__ == '__main__':
    unittest.main()
