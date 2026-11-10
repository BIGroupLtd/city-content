"""Synthetic receiving-boundary oracle. Never a publisher or runtime importer."""
import hashlib
import json
import os
from pathlib import Path

EXPECTED_MEMBERS = frozenset({'draft-result.json', 'site-config.json'})


def _bundle_members(directory):
    return frozenset(path.name for path in Path(directory).iterdir())


class _Held(Exception):
    """Stop input inspection, then persist the fixed refusal outside its try."""


def _verify_evidence(retained, evidence, payload):
    descriptor = retained.fileno()
    opened = os.fstat(descriptor)
    named = os.stat(evidence, follow_symlinks=False)
    if (opened.st_nlink != 1
            or (opened.st_dev, opened.st_ino, opened.st_mode)
            != (named.st_dev, named.st_ino, named.st_mode)):
        raise OSError('evidence_identity_changed')
    expected = payload.encode('utf-8')
    if os.pread(descriptor, len(expected) + 1, 0) != expected:
        raise OSError('evidence_readback_mismatch')


def _persist_evidence(retained, result, evidence):
    payload = json.dumps(result, sort_keys=True) + '\n'
    if retained.write(payload) != len(payload):
        raise OSError('incomplete_evidence_write')
    retained.flush()
    os.fsync(retained.fileno())
    _verify_evidence(retained, evidence, payload)


def inspect_transfer(directory=None, evidence=None, *, offline=False,
                     expected_receipt_sha256=None, expected_run_id=None,
                     expected_action_id=None):
    """Retain a new metadata-only HOLD; retry must use a new evidence path.

    The expected digest comes from separately retained sender custody, never
    from the received bundle. Completeness cannot grant publication authority.
    """
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'retry': 'new_offline_attempt',
              'reason': 'incomplete_transfer', 'observed': {}}
    if offline is not True:
        result['reason'] = 'offline_not_requested'
        return result
    # Reserve before inspecting: repeated delivery cannot replace prior evidence.
    with Path(evidence).open('x+', encoding='utf-8') as retained:
        try:
            if (not isinstance(expected_run_id, str) or not expected_run_id
                    or not isinstance(expected_action_id, str) or not expected_action_id):
                result['reason'] = 'missing_attempt_custody'
                raise _Held
            members = _bundle_members(directory)
            if members - EXPECTED_MEMBERS:
                result['reason'] = 'unexpected_bundle_members'
                raise _Held
            raw = {}
            for name in ('draft-result.json', 'site-config.json'):
                raw[name] = (Path(directory) / name).read_bytes()
                result['observed'][name] = {
                    'bytes': len(raw[name]),
                    'sha256': hashlib.sha256(raw[name]).hexdigest()}
            if _bundle_members(directory) != members:
                result['reason'] = 'bundle_members_changed'
                raise _Held
            receipt = json.loads(raw['draft-result.json'])
            artifact = json.loads(raw['site-config.json'])
            if (hashlib.sha256(raw['draft-result.json']).hexdigest()
                    != expected_receipt_sha256):
                result['reason'] = 'receipt_custody_mismatch'
            elif (not isinstance(receipt, dict)
                  or receipt.get('artifactSHA256')
                  != hashlib.sha256(raw['site-config.json']).hexdigest()):
                result['reason'] = 'artifact_mismatch'
            elif (receipt.get('status') != 'draft_only'
                  or receipt.get('gatePass') != 'absent'
                  or not isinstance(artifact, dict)
                  or not isinstance(artifact.get('blog_posts'), list)
                  or len(artifact['blog_posts']) != 1):
                result['reason'] = 'draft_contract_refused'
            else:
                post = artifact['blog_posts'][0]
                if receipt.get('builderRunId') != expected_run_id:
                    result['reason'] = 'run_identity_mismatch'
                elif (not isinstance(post, dict)
                      or post.get('source_action_id') != expected_action_id):
                    result['reason'] = 'action_identity_mismatch'
                else:
                    result['reason'] = 'complete_draft_still_held'
        except _Held:
            pass
        except (OSError, ValueError, UnicodeError):
            # Never retain content, paths, source identifiers or exception text.
            pass
        # Input refusal is retainable; evidence I/O failure must propagate.
        # Never return an in-memory result as if its retry evidence was saved.
        _persist_evidence(retained, result, evidence)
    return result
