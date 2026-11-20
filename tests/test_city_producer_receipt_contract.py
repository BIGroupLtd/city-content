"""Actual pinned draft receipts, synthetic callbacks, no model/content generation."""
import copy
import json
import os
import socket
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary
from offline_draft_receipt_contract import qualify


class NativeReceiptContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        boundary.BankBoundary.setUpClass()

    def setUp(self):
        self.h = boundary.BankBoundary()
        self.addCleanup(self.h.doCleanups)
        self.h.setUp()
        for guard in (patch.dict(os.environ, {}, clear=True),
                      patch.object(socket, 'getaddrinfo', side_effect=AssertionError('DNS')),
                      patch.object(socket, 'create_connection', side_effect=AssertionError('network')),
                      patch.object(socket.socket, 'connect_ex', side_effect=AssertionError('network'))):
            guard.start()
            self.addCleanup(guard.stop)

    def test_native_clean_floor_and_combined_holds_preserve_mandatory_receipt_contract(self):
        matrix = json.loads((boundary.FIXTURE.parent / 'dry-run-holds.json').read_text())
        for case in matrix['cases']:
            with self.subTest(case=case['id']):
                target = self.h.directory / case['id']
                writer = self.h.writer(violations=case['violations'], words=case['words'])
                returned = self.h.draft.generate(self.h.request, target, writer=writer)
                raw = {p.name: p.read_bytes() for p in target.iterdir()}
                saved = json.loads(raw['draft-result.json'])
                self.assertEqual(saved, returned)
                self.assertEqual(saved['native_violations'], case['expected'])
                for receipt in (returned, saved):
                    original = copy.deepcopy(receipt)
                    result = qualify(receipt, offline=True)
                    self.assertEqual(result['receipt_contract'], 'MATCH')
                    self.assertEqual(result['status'], 'HOLD')
                    self.assertIs(result['publish_allowed'], False)
                    self.assertEqual(receipt, original)
                self.assertEqual(raw, {p.name: p.read_bytes() for p in target.iterdir()})
                writer['generate_blog'].assert_called_once()

    def test_saved_receipt_metadata_cannot_clear_full_gate_holds_even_with_empty_native_holds(self):
        target = self.h.directory / 'clean'
        returned = self.h.draft.generate(self.h.request, target, writer=self.h.writer())
        original = {p.name: p.read_bytes() for p in target.iterdir()}
        self.assertEqual(returned['native_violations'], [])
        for index in range(len(returned['missing_full_gate_inputs'])):
            with self.subTest(index=index):
                forged = copy.deepcopy(returned)
                forged['missing_full_gate_inputs'].pop(index)
                self.assertEqual(qualify(forged, offline=True)['receipt_contract'], 'REFUSED')
        for forged in (dict(returned, missing_full_gate_inputs=[]),
                       dict(returned, gatePass=True),
                       dict(returned, status='published'),
                       dict(returned, reported_model='SYNTHETIC other model')):
            self.assertEqual(qualify(forged, offline=True)['receipt_contract'], 'REFUSED')
        self.assertEqual(original, {p.name: p.read_bytes() for p in target.iterdir()})


if __name__ == '__main__':
    unittest.main()
