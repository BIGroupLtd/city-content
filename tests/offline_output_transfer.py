"""Synthetic receiving-boundary oracle. Never a publisher or runtime importer."""
import hashlib
import json
from pathlib import Path


def inspect_transfer(directory, evidence, *, expected_receipt_sha256):
    """Retain a new metadata-only HOLD; retry must use a new evidence path.

    The expected digest comes from separately retained sender custody, never
    from the received bundle. Completeness cannot grant publication authority.
    """
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'retry': 'new_offline_attempt',
              'reason': 'incomplete_transfer', 'observed': {}}
    # Reserve before inspecting: repeated delivery cannot replace prior evidence.
    with Path(evidence).open('x', encoding='utf-8') as retained:
        try:
            raw = {}
            for name in ('draft-result.json', 'site-config.json'):
                raw[name] = (Path(directory) / name).read_bytes()
                result['observed'][name] = {
                    'bytes': len(raw[name]),
                    'sha256': hashlib.sha256(raw[name]).hexdigest()}
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
                result['reason'] = 'complete_draft_still_held'
        except (OSError, ValueError, UnicodeError):
            # Never retain content, paths, source identifiers or exception text.
            pass
        retained.write(json.dumps(result, sort_keys=True) + '\n')
    return result
