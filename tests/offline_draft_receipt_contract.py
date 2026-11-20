"""Synthetic-only decoded receipt hold contract; no runtime or filesystem wiring."""

MODEL = 'claude-sonnet-4-6'
MISSING_GATES = frozenset((
    'current_master_rules_binding', 'verified_claim_sources', 'native_site_enrollment',
    'current_estate_similarity_corpus', 'retained_full_builder_gate_result'))
CONTROL_FIELDS = frozenset((
    'status', 'gatePass', 'requested_model', 'reported_model',
    'native_violations', 'missing_full_gate_inputs'))


def qualify(receipt=None, *, offline=False):
    """Check mandatory native hold metadata, never admission or authenticity.

    Input is an already decoded synthetic dictionary. This helper neither
    parses wire bytes nor loads, reads, writes, retries or publishes anything.
    """
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'receipt_contract': 'DISABLED',
              'reason': 'offline_not_requested'}
    if offline is not True:
        return result
    result.update(receipt_contract='REFUSED', reason='invalid_receipt_shape')
    if type(receipt) is not dict:
        return result
    if not CONTROL_FIELDS.issubset(receipt):
        result['reason'] = 'missing_hold_field'
        return result
    if (type(receipt['status']) is not str or receipt['status'] != 'draft_only'
            or type(receipt['gatePass']) is not str or receipt['gatePass'] != 'absent'):
        result['reason'] = 'draft_marker_mismatch'
        return result
    requested, reported = receipt['requested_model'], receipt['reported_model']
    if (type(requested) is not str or requested != MODEL
            or (reported is not None and (type(reported) is not str or reported != MODEL))):
        result['reason'] = 'model_evidence_mismatch'
        return result
    missing = receipt['missing_full_gate_inputs']
    if (type(missing) is not list or len(missing) != len(MISSING_GATES)
            or any(type(value) is not str for value in missing)
            or set(missing) != MISSING_GATES):
        result['reason'] = 'incomplete_full_gate_hold'
        return result
    violations = receipt['native_violations']
    if type(violations) is not list or any(type(value) is not str for value in violations):
        result['reason'] = 'invalid_native_hold_list'
        return result
    result.update(receipt_contract='MATCH', reason='native_hold_contract_matches_still_held')
    return result
