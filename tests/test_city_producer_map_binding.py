"""Real pinned producer epoch drift, offline map qualifier, synthetic only."""
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import os
import socket
import unittest
from unittest.mock import patch

import test_city_producer_bank_boundary as boundary

SPEC = importlib.util.spec_from_file_location(
    'offline_map_parity', boundary.ROOT / 'tools/blog_output_map_parity.py')
parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parity)


def snapshot(path):
    value = path.stat()
    return path.read_bytes(), value.st_ino, value.st_mode, value.st_size, value.st_mtime_ns


class MapBinding(unittest.TestCase):
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
        self.baseline = self.h.directory / 'map-snapshot.json'
        self.original_map = self.h.draft.HOST_MAP.read_bytes()
        self.baseline.write_bytes(self.original_map)
        self.digest = hashlib.sha256(self.original_map).hexdigest()
        self.target = self.h.directory / 'retained'
        self.h.draft.generate(self.h.request, self.target, writer=self.h.writer())
        self.receipt = self.target / 'draft-result.json'
        self.retained = {p.name: snapshot(p) for p in self.target.iterdir()}

    def qualify(self, receipt=None, baseline=None, digest=None, host=None):
        receipt = receipt or self.receipt
        baseline = baseline or self.baseline
        before = snapshot(receipt), snapshot(baseline)
        value = parity.qualify(offline=True, receipt=receipt, map_snapshot=baseline,
                               expected_map_sha256=digest or self.digest,
                               request_host=host or self.h.request['host'])
        self.assertEqual((snapshot(receipt), snapshot(baseline)), before)
        self.assertEqual(value['status'], 'HOLD')
        for key in ('enabled', 'approved', 'publish_allowed'):
            self.assertIs(value[key], False)
        self.assertEqual({p.name: snapshot(p) for p in self.target.iterdir()}, self.retained)
        return value

    def test_actual_apex_and_www_receipts_match_original_snapshot_but_stay_held(self):
        for destination in ('allowed.example', 'www.allowed.example'):
            mapping = json.dumps({'allowed.example': destination}).encode('ascii')
            self.h.draft.HOST_MAP.write_bytes(mapping)
            self.baseline.write_bytes(mapping)
            digest = hashlib.sha256(mapping).hexdigest()
            for host in ('allowed.example', 'www.allowed.example'):
                with self.subTest(destination=destination, host=host):
                    output = self.h.directory / (destination + '-' + host)
                    request = dict(self.h.request, host=host)
                    self.h.draft.generate(request, output, writer=self.h.writer())
                    value = self.qualify(output / 'draft-result.json', digest=digest, host=host)
                    self.assertEqual((value['map_binding'], value['reason']),
                                     ('MATCH', 'map_binding_matches_still_held'))

    def test_native_mid_writer_map_drift_is_not_coherent_baseline_evidence(self):
        variants = (
            b'{"allowed.example": "www.allowed.example"}',
            b'{"other.example": "other.example"}',
            b'{"allowed.example":"allowed.example"}',
            b'{"allowed.example": "allowed.example", "other.example": "other.example"}')
        for index, changed in enumerate(variants):
            with self.subTest(index=index):
                self.h.draft.HOST_MAP.write_bytes(self.original_map)
                output = self.h.directory / ('drift-' + str(index))
                writer = self.h.writer()

                def mutate(*args, **kwargs):
                    self.h.draft.HOST_MAP.write_bytes(changed)
                    return copy.deepcopy(self.h.post)

                writer['generate_blog'].side_effect = mutate
                receipt = self.h.draft.generate(self.h.request, output, writer=writer)
                writer['generate_blog'].assert_called_once()
                # Actual source chose the old destination, then hashed new bytes.
                self.assertEqual(receipt['canonical_host'], 'allowed.example')
                self.assertEqual(receipt['canonical_host_map_sha256'],
                                 hashlib.sha256(changed).hexdigest())
                value = self.qualify(output / 'draft-result.json')
                self.assertEqual(value['reason'], 'receipt_map_mismatch')
                # Even an agreeing substituted map/receipt cannot replace the
                # independently retained baseline digest.
                substituted = self.h.directory / ('substituted-' + str(index))
                substituted.write_bytes(changed)
                self.assertEqual(self.qualify(output / 'draft-result.json', baseline=substituted)['reason'],
                                 'baseline_digest_mismatch')

    def test_each_reported_binding_and_draft_marker_refuses_corruption(self):
        original = json.loads(self.receipt.read_bytes())
        mutations = {
            'canonical_host_map_sha256': ('0' * 64, None, 0, True),
            'canonical_host': ('www.allowed.example', 'other.example', None, ['allowed.example']),
            'public_origin': ('http://allowed.example', 'https://allowed.example/',
                              'https://other.example', None),
            'status': ('published', True, None),
            'gatePass': (True, {'pass': True}, 'APPROVE', None)}
        for field, values in mutations.items():
            for index, bad in enumerate(values):
                with self.subTest(field=field, bad=bad):
                    record = dict(original, **{field: bad})
                    path = self.h.directory / (field + str(index) + '.json')
                    path.write_text(json.dumps(record), encoding='utf-8')
                    self.assertEqual(self.qualify(path)['map_binding'], 'REFUSED')
            record = dict(original)
            record.pop(field)
            path = self.h.directory / ('missing-' + field)
            path.write_text(json.dumps(record), encoding='utf-8')
            self.assertEqual(self.qualify(path)['map_binding'], 'REFUSED')

    def test_self_consistent_replacement_cannot_supply_its_own_baseline(self):
        changed = b'{"allowed.example": "www.allowed.example"}'
        changed_digest = hashlib.sha256(changed).hexdigest()
        mapping = self.h.directory / 'forged-map.json'
        mapping.write_bytes(changed)
        record = json.loads(self.receipt.read_bytes())
        record.update(canonical_host_map_sha256=changed_digest,
                      canonical_host='www.allowed.example',
                      public_origin='https://www.allowed.example')
        receipt = self.h.directory / 'forged-receipt.json'
        receipt.write_text(json.dumps(record), encoding='utf-8')
        self.assertEqual(self.qualify(receipt, baseline=mapping)['reason'],
                         'baseline_digest_mismatch')
        # Changing trusted baseline custody is outside this qualifier's power.
        # Even if a caller supplies that digest, MATCH grants no authority.
        self.assertEqual(self.qualify(receipt, baseline=mapping, digest=changed_digest)[
            'map_binding'], 'MATCH')

    def test_strict_snapshot_and_receipt_wire_refuse_ambiguous_or_invalid_json(self):
        raw_receipt = self.receipt.read_bytes()
        wires = (b'[]', b'null', b'{} trailing', b'\xff',
                 b'{"canonical_host": "allowed.example", "canonical_host": "other.example"}',
                 b'{"canonical_host":NaN}', b'{"nested":{"x":1,"x":2}}',
                 b'{"nested":' + b'[' * 1500 + b'0' + b']' * 1500 + b'}')
        for index, wire in enumerate(wires):
            with self.subTest(index=index):
                path = self.h.directory / ('wire-' + str(index))
                path.write_bytes(wire)
                self.assertEqual(self.qualify(path)['map_binding'], 'REFUSED')
        for index, wire in enumerate((b'[]', b'{}', b'{"allowed.example":"other.example"}',
                                      b'{"allowed.example":"allowed.example","allowed.example":"www.allowed.example"}',
                                      b'{"allowed.example":NaN}', b'\xff')):
            with self.subTest(map=index):
                path = self.h.directory / ('map-' + str(index))
                path.write_bytes(wire)
                self.assertEqual(self.qualify(baseline=path, digest=hashlib.sha256(wire).hexdigest())[
                    'map_binding'], 'REFUSED')
        self.assertEqual(self.receipt.read_bytes(), raw_receipt)

    def test_invalid_custody_arguments_refuse_without_reading_inputs(self):
        cases = [(value, 'allowed.example') for value in
                 (None, '', '0' * 63, self.digest.upper(), 1, True)]
        cases += [(self.digest, host) for host in
                  (None, '', 'https://allowed.example', 'ALLOWED.example',
                   'fix.allowed.example', ['allowed.example'])]
        with patch.object(parity.os, 'open', side_effect=AssertionError('invalid baseline read')):
            for digest, host in cases:
                with self.subTest(digest=digest, host=host):
                    value = parity.qualify(offline=True, receipt=self.receipt,
                                           map_snapshot=self.baseline,
                                           expected_map_sha256=digest, request_host=host)
                    self.assertEqual(value['reason'], 'invalid_baseline')
                    self.assertEqual(value['map_binding'], 'REFUSED')

    def test_unsafe_or_oversized_leaves_refuse_without_blocking_or_mutation(self):
        paths = []
        directory = self.h.directory / 'directory'
        directory.mkdir()
        paths.append(directory)
        link = self.h.directory / 'symlink'
        link.symlink_to(self.receipt)
        paths.append(link)
        fifo = self.h.directory / 'fifo'
        os.mkfifo(fifo)
        paths.append(fifo)
        large = self.h.directory / 'large'
        large.write_bytes(b' ' * (parity.RECEIPT_LIMIT + 1))
        paths.append(large)
        for path in paths:
            with self.subTest(kind=path.name):
                result = parity.qualify(offline=True, receipt=path, map_snapshot=self.baseline,
                                        expected_map_sha256=self.digest, request_host='allowed.example')
                self.assertEqual(result['map_binding'], 'REFUSED')
        hardlink = self.h.directory / 'hardlink'
        os.link(self.receipt, hardlink)
        try:
            self.assertEqual(parity.qualify(offline=True, receipt=hardlink,
                                           map_snapshot=self.baseline,
                                           expected_map_sha256=self.digest,
                                           request_host='allowed.example')['reason'], 'unsafe_input')
        finally:
            hardlink.unlink()
        self.assertEqual({p.name: snapshot(p) for p in self.target.iterdir()}, self.retained)

    def test_exact_byte_caps_and_overflow_are_enforced_on_both_input_kinds(self):
        for limit in (parity.MAP_LIMIT, parity.RECEIPT_LIMIT):
            with self.subTest(limit=limit):
                path = self.h.directory / ('cap-' + str(limit))
                path.write_bytes(b' ' * limit)
                self.assertEqual(len(parity._regular_bytes(path, limit)), limit)
                path.write_bytes(b' ' * (limit + 1))
                with self.assertRaisesRegex(parity.Refused, '^input_too_large$'):
                    parity._regular_bytes(path, limit)

    def test_short_reads_are_valid_but_same_inode_rewrite_refuses_and_closes_descriptor(self):
        read = parity.os.read
        opened = []
        original_open = parity.os.open

        def tracked_open(*args, **kwargs):
            descriptor = original_open(*args, **kwargs)
            opened.append(descriptor)
            return descriptor

        with patch.object(parity.os, 'read', side_effect=lambda fd, size: read(fd, min(size, 3))):
            self.assertEqual(self.qualify()['map_binding'], 'MATCH')
        changed = self.h.directory / 'changing'
        changed.write_bytes(b'{"synthetic": "before"}')
        replaced = False

        def rewrite(fd, size):
            nonlocal replaced
            value = read(fd, size)
            if not replaced:
                replaced = True
                changed.write_bytes(b'{"synthetic": "after!"}')
            return value

        with patch.object(parity.os, 'open', tracked_open), patch.object(parity.os, 'read', rewrite):
            with self.assertRaisesRegex(parity.Refused, '^input_changed$'):
                parity._regular_bytes(changed, parity.RECEIPT_LIMIT)
        self.assertEqual(len(opened), 1)
        with self.assertRaises(OSError):
            os.fstat(opened[0])
        opened.clear()
        with patch.object(parity.os, 'open', tracked_open), \
                patch.object(parity.os, 'read', side_effect=OSError('SYNTHETIC_PRIVATE_CANARY')):
            result = parity.qualify(offline=True, receipt=self.receipt, map_snapshot=self.baseline,
                                    expected_map_sha256=self.digest, request_host='allowed.example')
        self.assertEqual(result['reason'], 'unreadable_or_invalid_input')
        self.assertEqual(len(opened), 1)
        with self.assertRaises(OSError):
            os.fstat(opened[0])

    def test_default_off_and_cli_refusal_never_echo_inputs_or_enable_publication(self):
        with patch.object(parity.os, 'open', side_effect=AssertionError('OFF read')):
            self.assertEqual(parity.qualify(receipt='private')['map_binding'], 'DISABLED')
            out = io.StringIO()
            with patch('sys.stdout', out):
                self.assertEqual(parity.main(['--receipt', 'SYNTHETIC_PRIVATE_CANARY']), 0)
            self.assertEqual(json.loads(out.getvalue())['map_binding'], 'DISABLED')
            self.assertNotIn('CANARY', out.getvalue())
        args = ['--offline', '--receipt', str(self.receipt), '--map-snapshot', str(self.baseline),
                '--expected-map-sha256', self.digest, '--request-host', 'allowed.example']
        for host, expected_status in (('allowed.example', 0), ('SYNTHETIC_PRIVATE_CANARY', 1)):
            out, err = io.StringIO(), io.StringIO()
            with patch('sys.stdout', out), patch('sys.stderr', err):
                status = parity.main(args[:-1] + [host])
            self.assertEqual(status, expected_status)
            self.assertEqual(err.getvalue(), '')
            self.assertNotIn('CANARY', out.getvalue())
            value = json.loads(out.getvalue())
            self.assertEqual(value['status'], 'HOLD')
            self.assertIs(value['publish_allowed'], False)


if __name__ == '__main__':
    unittest.main()
