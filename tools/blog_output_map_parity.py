"""Read-only offline canonical-map receipt qualification; never publish authority."""
import argparse
import hashlib
import json
import os
import re
import stat

MAP_LIMIT = 128 * 1024
RECEIPT_LIMIT = 64 * 1024
HOST = re.compile(r'[a-z0-9]+(?:[.-][a-z0-9]+)*', re.ASCII)


class Refused(ValueError):
    """Value-free refusal; never retain source data or operating-system text."""


def _identity(item):
    return (item.st_dev, item.st_ino, item.st_mode, item.st_nlink,
            item.st_size, item.st_mtime_ns, item.st_ctime_ns)


def _input_signature(paths):
    # Leaf metadata only: no following a replacement link or opening a FIFO.
    return tuple(_identity(os.stat(path, follow_symlinks=False)) for path in paths)


def _regular_bytes(path, limit):
    # O_NONBLOCK prevents a substituted FIFO from hanging before fstat.
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise Refused('unsafe_input')
        if before.st_size > limit:
            raise Refused('input_too_large')
        chunks = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise Refused('input_too_large')
        after = os.fstat(descriptor)
        if size != before.st_size or _identity(before) != _identity(after):
            raise Refused('input_changed')
        return b''.join(chunks)
    finally:
        os.close(descriptor)


def _object(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Refused('invalid_json')
            result[key] = value
        return result

    def constant(_):
        raise Refused('invalid_json')

    result = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    if not isinstance(result, dict):
        raise Refused('invalid_json')
    return result


def _host(value):
    return (isinstance(value, str) and HOST.fullmatch(value) is not None
            and 'fix' not in value.split('.')[:-1])


def qualify(*, offline=False, receipt=None, map_snapshot=None,
            expected_map_sha256=None, request_host=None):
    """Compare one receipt with independently retained map bytes and digest.

    The caller supplies baseline custody. A matching self-supplied file/digest
    is not authentication. Qualification never changes any artifact or state.
    """
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'map_binding': 'DISABLED',
              'reason': 'offline_not_requested'}
    if offline is not True:
        return result
    result['map_binding'] = 'REFUSED'
    result['reason'] = 'invalid_baseline'
    if (not isinstance(expected_map_sha256, str)
            or re.fullmatch(r'[0-9a-f]{64}', expected_map_sha256) is None
            or not _host(request_host)):
        return result
    try:
        inputs = (map_snapshot, receipt)
        original_signature = _input_signature(inputs)
        original = _regular_bytes(map_snapshot, MAP_LIMIT)
        if hashlib.sha256(original).hexdigest() != expected_map_sha256:
            raise Refused('baseline_digest_mismatch')
        mapping = _object(original)
        if not mapping or any(not _host(key) or key.startswith('www.')
                              or not _host(value) or value not in (key, 'www.' + key)
                              for key, value in mapping.items()):
            raise Refused('invalid_map')
        root = request_host.removeprefix('www.')
        if root not in mapping:
            raise Refused('unknown_request_host')
        record = _object(_regular_bytes(receipt, RECEIPT_LIMIT))
        if record.get('canonical_host_map_sha256') != expected_map_sha256:
            raise Refused('receipt_map_mismatch')
        if (record.get('canonical_host') != mapping[root]
                or record.get('public_origin') != 'https://' + mapping[root]):
            raise Refused('receipt_destination_mismatch')
        if record.get('status') != 'draft_only' or record.get('gatePass') != 'absent':
            raise Refused('draft_hold_mismatch')
        # A stable individual read is insufficient if the earlier map changes
        # while the receipt is read/parsed, or either leaf is then replaced.
        try:
            current_signature = _input_signature(inputs)
        except OSError:
            raise Refused('input_set_changed') from None
        if current_signature != original_signature:
            raise Refused('input_set_changed')
        result.update(map_binding='MATCH', reason='map_binding_matches_still_held')
    except Refused as exc:
        result['reason'] = str(exc)
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError):
        result['reason'] = 'unreadable_or_invalid_input'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--receipt')
    parser.add_argument('--map-snapshot')
    parser.add_argument('--expected-map-sha256')
    parser.add_argument('--request-host')
    args = parser.parse_args(argv)
    result = qualify(offline=args.offline, receipt=args.receipt,
                     map_snapshot=args.map_snapshot,
                     expected_map_sha256=args.expected_map_sha256,
                     request_host=args.request_host)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['map_binding'] in ('DISABLED', 'MATCH') else 1


if __name__ == '__main__':
    raise SystemExit(main())
