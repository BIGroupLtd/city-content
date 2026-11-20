"""Source-free adversarial namespace fixtures, no writer or external effect."""
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from offline_draft_receipt_namespace import qualify

FIXTURE = Path(__file__).parent / 'fixtures/city-producer/receipt-namespace.json'


class ReceiptNamespace(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.receipt = self.fixture['receipt']

    def check(self, receipt):
        before = copy.deepcopy(receipt)
        out, err = io.StringIO(), io.StringIO()
        with patch('sys.stdout', out), patch('sys.stderr', err):
            result = qualify(receipt, offline=True)
        self.assertEqual(receipt, before)
        self.assertEqual((out.getvalue(), err.getvalue()), ('', ''))
        self.assertEqual(result['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(result[key], False)
        return result

    def test_synthetic_fixture_reordered_fields_and_opaque_values_remain_held(self):
        self.assertEqual({key: self.fixture[key] for key in
                          ('synthetic_only', 'enabled', 'approved', 'not_runtime_queue', 'status')},
                         dict(synthetic_only=True, enabled=False, approved=False,
                              not_runtime_queue=True, status='HOLD'))
        self.assertEqual(self.check(self.receipt)['receipt_namespace'], 'MATCH')
        reordered = dict(reversed(list(self.receipt.items())))
        self.assertEqual(self.check(reordered)['receipt_namespace'], 'MATCH')

    def test_default_off_never_inspects_poison_inputs(self):
        class Poison:
            def __getattribute__(self, key):
                raise AssertionError('OFF inspected input')
            def __iter__(self):
                raise AssertionError('OFF iterated input')
        for active in (False, None, 0, 1, 'true'):
            result = qualify(Poison(), offline=active)
            self.assertEqual(result['receipt_namespace'], 'DISABLED')
            self.assertIs(result['publish_allowed'], False)

    def test_every_removed_native_field_refuses(self):
        for field in self.receipt:
            with self.subTest(field=field):
                changed = dict(self.receipt)
                changed.pop(field)
                result = self.check(changed)
                self.assertEqual(result['receipt_namespace'], 'REFUSED')
                self.assertEqual(result['reason'], 'missing_receipt_field')

    def test_foreign_operational_and_unknown_fields_never_enter_report(self):
        fields = ('approved', 'enabled', 'publish_allowed', 'publication_enabled',
                  'generation_enabled', 'READY', 'ready', 'noindex', 'isPublished',
                  'blog_posts', '__proto__', 'constructor', 'prototype',
                  'new_metadata', 'errors', 'data', 'SYNTHETIC_PRIVATE_CANARY')
        for field in fields:
            for value in (True, {'pass': True}, None):
                with self.subTest(field=field, value=value):
                    changed = dict(self.receipt, **{field: value})
                    result = self.check(changed)
                    self.assertEqual(result['receipt_namespace'], 'REFUSED')
                    self.assertEqual(result['reason'], 'foreign_receipt_field')
                    self.assertNotIn('CANARY', json.dumps(result))

    def test_field_aliases_and_unicode_spellings_refuse_without_normalization(self):
        for field in self.receipt:
            for alias in (field.upper(), field + '\u200b', '\ufeff' + field):
                with self.subTest(field=field, alias=alias):
                    changed = dict(self.receipt)
                    changed[alias] = changed.pop(field)
                    self.assertEqual(self.check(changed)['receipt_namespace'], 'REFUSED')

    def test_wrong_document_shapes_and_nonstring_extra_keys_refuse(self):
        for value in (None, False, 0, [], [self.receipt], 'draft_only'):
            self.assertEqual(qualify(value, offline=True)['receipt_namespace'], 'REFUSED')
        for key in (1, None, False, ('synthetic',)):
            with self.subTest(key=key):
                changed = dict(self.receipt)
                changed[key] = True
                self.assertEqual(self.check(changed)['reason'], 'foreign_receipt_field')

    def test_namespace_match_does_not_validate_values_or_clear_external_holds(self):
        changed = dict(self.receipt, status='published', gatePass=True,
                       missing_full_gate_inputs=[], native_violations=False,
                       requested_model='SYNTHETIC untrusted model',
                       builderRunId='SYNTHETIC opaque value',
                       artifactSHA256='SYNTHETIC not a digest')
        result = self.check(changed)
        self.assertEqual(result['receipt_namespace'], 'MATCH')
        self.assertEqual(result['status'], 'HOLD')
        self.assertIs(result['approved'], False)
        self.assertIs(result['publish_allowed'], False)

    def test_missing_and_foreign_fields_cannot_cancel_each_other(self):
        for field in self.receipt:
            with self.subTest(field=field):
                changed = dict(self.receipt)
                changed.pop(field)
                changed['SYNTHETIC_PRIVATE_CANARY'] = 'SYNTHETIC'
                self.assertEqual(len(changed), len(self.receipt))
                result = self.check(changed)
                self.assertEqual(result['receipt_namespace'], 'REFUSED')
                self.assertNotIn('CANARY', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
