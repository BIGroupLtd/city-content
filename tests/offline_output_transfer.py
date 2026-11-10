"""Synthetic receiving-boundary oracle. Never a publisher or runtime importer."""
import hashlib
import json
from pathlib import Path

EXPECTED_MEMBERS = frozenset({'draft-result.json', 'site-config.json'})


def _bundle_members(directory):
    return frozenset(path.name for path in Path(directory).iterdir())


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
    with Path(evidence).open('x', encoding='utf-8') as retained:
        try:
            if (not isinstance(expected_run_id, str) or not expected_run_id
                    or not isinstance(expected_action_id, str) or not expected_action_id):
                result['reason'] = 'missing_attempt_custody'
                retained.write(json.dumps(result, sort_keys=True) + '\n')
                return result
            members = _bundle_members(directory)
            if members - EXPECTED_MEMBERS:
                result['reason'] = 'unexpected_bundle_members'
                retained.write(json.dumps(result, sort_keys=True) + '\n')
                return result
            raw = {}
            for name in ('draft-result.json', 'site-config.json'):
                raw[name] = (Path(directory) / name).read_bytes()
                result['observed'][name] = {
                    'bytes': len(raw[name]),
                    'sha256': hashlib.sha256(raw[name]).hexdigest()}
            if _bundle_members(directory) != members:
                result['reason'] = 'bundle_members_changed'
                retained.write(json.dumps(result, sort_keys=True) + '\n')
                return result
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
        except (OSError, ValueError, UnicodeError):
            # Never retain content, paths, source identifiers or exception text.
            pass
        retained.write(json.dumps(result, sort_keys=True) + '\n')
    return result
