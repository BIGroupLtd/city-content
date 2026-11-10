"""Pinned producer receipt field projection, canned callbacks, no content generation."""
import copy
import json
import os
import socket
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary
from offline_draft_receipt_namespace import qualify


class NativeReceiptNamespace(unittest.TestCase):
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

    def test_actual_returned_and_saved_receipt_names_match_for_all_existing_hold_cases(self):
        matrix = json.loads((boundary.FIXTURE.parent / 'dry-run-holds.json').read_text())
        for case in matrix['cases']:
            with self.subTest(case=case['id']):
                target = self.h.directory / case['id']
                writer = self.h.writer(violations=case['violations'], words=case['words'])
                returned = self.h.draft.generate(self.h.request, target, writer=writer)
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                saved = json.loads(before['draft-result.json'])
                self.assertEqual(returned, saved)
                self.assertEqual(saved['native_violations'], case['expected'])
                for receipt in (returned, saved):
                    original = copy.deepcopy(receipt)
                    result = qualify(receipt, offline=True)
                    self.assertEqual(result['receipt_namespace'], 'MATCH')
                    self.assertEqual(result['status'], 'HOLD')
                    self.assertIs(result['publish_allowed'], False)
                    self.assertEqual(receipt, original)
                self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})
                writer['generate_blog'].assert_called_once()

    def test_saved_receipt_copy_cannot_acquire_foreign_control_fields(self):
        target = self.h.directory / 'clean'
        returned = self.h.draft.generate(self.h.request, target, writer=self.h.writer())
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        for field in ('approved', 'enabled', 'publish_allowed', 'READY', 'new_metadata'):
            with self.subTest(field=field):
                changed = dict(returned, **{field: True})
                result = qualify(changed, offline=True)
                self.assertEqual(result['receipt_namespace'], 'REFUSED')
                self.assertIs(result['approved'], False)
                self.assertIs(result['publish_allowed'], False)
        self.assertEqual(before, {p.name: p.read_bytes() for p in target.iterdir()})


if __name__ == '__main__':
    unittest.main()
