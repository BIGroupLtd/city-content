"""Test-only decoded draft receipt field namespace; no runtime or I/O wiring."""

FIELDS = frozenset((
    'builderRunId', 'native_violations', 'requested_model', 'reported_model',
    'artifactSHA256', 'gatePass', 'status', 'canonical_host', 'public_origin',
    'canonical_host_map_sha256', 'missing_full_gate_inputs'))


def qualify(receipt=None, *, offline=False):
    """Check field names only. Values, identities and wire bytes remain opaque."""
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'receipt_namespace': 'DISABLED',
              'reason': 'offline_not_requested'}
    if offline is not True:
        return result
    result.update(receipt_namespace='REFUSED', reason='invalid_receipt_shape')
    if type(receipt) is not dict:
        return result
    fields = set(receipt)
    if fields - FIELDS:
        result['reason'] = 'foreign_receipt_field'
        return result
    if FIELDS - fields:
        result['reason'] = 'missing_receipt_field'
        return result
    result.update(receipt_namespace='MATCH', reason='native_receipt_fields_match_still_held')
    return result
