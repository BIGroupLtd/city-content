"""Source-free negative fixtures for decoded native draft receipt hold metadata."""
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from offline_draft_receipt_contract import qualify

FIXTURE = Path(__file__).parent / 'fixtures/city-producer/receipt-hold-contract.json'


class ReceiptContract(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text(encoding='utf-8'))
        self.receipt = self.fixture['receipt']

    def check(self, receipt):
        original = copy.deepcopy(receipt)
        out, err = io.StringIO(), io.StringIO()
        with patch('sys.stdout', out), patch('sys.stderr', err):
            value = qualify(receipt, offline=True)
        self.assertEqual(receipt, original)
        self.assertEqual((out.getvalue(), err.getvalue()), ('', ''))
        self.assertEqual(value['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(value[key], False)
        return value

    def test_fixture_and_valid_empty_or_nonempty_native_holds_always_stay_held(self):
        self.assertEqual({key: self.fixture[key] for key in
                          ('synthetic_only', 'enabled', 'approved', 'not_runtime_queue', 'status')},
                         dict(synthetic_only=True, enabled=False, approved=False,
                              not_runtime_queue=True, status='HOLD'))
        for reported in (None, 'claude-sonnet-4-6'):
            for holds in ([], ['SYNTHETIC native hold'], ['LENGTH: below hard floor', 'SYNTHETIC Ω']):
                with self.subTest(reported=reported, holds=holds):
                    receipt = dict(self.receipt, reported_model=reported, native_violations=holds)
                    self.assertEqual(self.check(receipt)['receipt_contract'], 'MATCH')
        reordered = dict(self.receipt, missing_full_gate_inputs=list(reversed(
            self.receipt['missing_full_gate_inputs'])))
        self.assertEqual(self.check(reordered)['receipt_contract'], 'MATCH')

    def test_default_off_does_not_inspect_even_a_poison_object(self):
        class Poison:
            def __getattribute__(self, name):
                raise AssertionError('OFF inspected receipt')
            def __iter__(self):
                raise AssertionError('OFF iterated receipt')
        for flag in (False, None, 0, 1, 'true'):
            with self.subTest(flag=flag):
                value = qualify(Poison(), offline=flag)
                self.assertEqual(value['receipt_contract'], 'DISABLED')
                self.assertIs(value['publish_allowed'], False)

    def test_every_missing_control_field_refuses(self):
        for field in ('status', 'gatePass', 'requested_model', 'reported_model',
                      'native_violations', 'missing_full_gate_inputs'):
            with self.subTest(field=field):
                receipt = dict(self.receipt)
                receipt.pop(field)
                value = self.check(receipt)
                self.assertEqual(value['reason'], 'missing_hold_field')
                self.assertEqual(value['receipt_contract'], 'REFUSED')
        for malformed in (None, [], True, 1, 'draft_only'):
            self.assertEqual(qualify(malformed, offline=True)['receipt_contract'], 'REFUSED')

    def test_all_missing_gate_markers_and_duplicate_unknown_or_typed_markers_refuse(self):
        markers = self.receipt['missing_full_gate_inputs']
        for index in range(len(markers)):
            for replacement in ('missing', 'duplicate', 'unknown', 'typed'):
                with self.subTest(index=index, replacement=replacement):
                    changed = list(markers)
                    if replacement == 'missing':
                        changed.pop(index)
                    elif replacement == 'duplicate':
                        changed[index] = markers[(index + 1) % len(markers)]
                    elif replacement == 'unknown':
                        changed[index] = 'SYNTHETIC_PRIVATE_CANARY'
                    else:
                        changed[index] = {'pass': True}
                    value = self.check(dict(self.receipt, missing_full_gate_inputs=changed))
                    self.assertEqual(value['reason'], 'incomplete_full_gate_hold')
                    self.assertNotIn('CANARY', json.dumps(value))
        for cleared in (None, False, {}, '', [], tuple(markers)):
            with self.subTest(cleared=cleared):
                self.assertEqual(self.check(dict(self.receipt, missing_full_gate_inputs=cleared))[
                    'receipt_contract'], 'REFUSED')

    def test_draft_markers_cannot_be_upgraded_or_coerced(self):
        for field, invalid in (('status', ('published', 'complete', True, 0, None, {})),
                               ('gatePass', (True, False, 'APPROVE', {'pass': True}, [], None))):
            for value in invalid:
                with self.subTest(field=field, value=value):
                    result = self.check(dict(self.receipt, **{field: value}))
                    self.assertEqual(result['reason'], 'draft_marker_mismatch')
                    self.assertEqual(result['receipt_contract'], 'REFUSED')

    def test_model_evidence_is_exact_and_null_report_never_implies_approval(self):
        for field in ('requested_model', 'reported_model'):
            for invalid in ('SYNTHETIC wrong model', ['claude-sonnet-4-6'], True, 1, {}, ''):
                with self.subTest(field=field, invalid=invalid):
                    result = self.check(dict(self.receipt, **{field: invalid}))
                    self.assertEqual(result['reason'], 'model_evidence_mismatch')
        self.assertEqual(self.check(self.receipt)['receipt_contract'], 'MATCH')
        self.assertIs(self.check(self.receipt)['approved'], False)

    def test_native_hold_representation_refuses_non_lists_and_non_text_entries(self):
        for invalid in (None, False, {}, '', 'SYNTHETIC hold', ('SYNTHETIC hold',),
                        [None], [False], [1], [{}], [[]]):
            with self.subTest(invalid=invalid):
                value = self.check(dict(self.receipt, native_violations=invalid))
                self.assertEqual(value['reason'], 'invalid_native_hold_list')
                self.assertEqual(value['receipt_contract'], 'REFUSED')

    def test_contract_match_does_not_authenticate_unchanged_or_erased_hold_content(self):
        # Without independent sender custody, an empty valid list cannot prove
        # that a real prior native hold was absent. Full-gate holds still remain.
        held = dict(self.receipt, native_violations=['SYNTHETIC retained refusal'])
        erased = dict(held, native_violations=[], approved=True, builderRunId='SYNTHETIC untrusted')
        self.assertEqual(self.check(held)['receipt_contract'], 'MATCH')
        value = self.check(erased)
        self.assertEqual(value['receipt_contract'], 'MATCH')
        self.assertIs(value['approved'], False)
        self.assertIs(value['publish_allowed'], False)


if __name__ == '__main__':
    unittest.main()
