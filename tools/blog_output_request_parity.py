"""Offline original-request/output identity qualification; no publication authority."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

# Reuse the same reviewed bounded reader, strict JSON and input-pair guards.
# Resolve only the repository sibling, independently of ambient import paths.
SPEC = importlib.util.spec_from_file_location(
    'blog_output_request_core', Path(__file__).with_name('blog_output_map_parity.py'))
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)

REQUEST_LIMIT = 128 * 1024
ARTIFACT_LIMIT = core.ARTIFACT_LIMIT


def qualify(*, offline=False, request_snapshot=None, expected_request_sha256=None,
            artifact=None):
    """Compare saved source identity to an independently retained request.

    This checks the two native provenance fields only, not receipt or body
    authenticity, job admission, model execution or editorial acceptance.
    """
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'request_binding': 'DISABLED',
              'reason': 'offline_not_requested'}
    if offline is not True:
        return result
    result.update(request_binding='REFUSED', reason='invalid_baseline')
    if (not isinstance(expected_request_sha256, str)
            or re.fullmatch(r'[0-9a-f]{64}', expected_request_sha256) is None):
        return result
    try:
        inputs = (request_snapshot, artifact)
        original_signature = core._input_signature(inputs)
        raw_request = core._regular_bytes(request_snapshot, REQUEST_LIMIT)
        if hashlib.sha256(raw_request).hexdigest() != expected_request_sha256:
            raise core.Refused('request_digest_mismatch')
        request = core._object(raw_request)
        identity = request.get('source_action_id'), request.get('topic')
        if any(not isinstance(value, str) or not value.strip() for value in identity):
            raise core.Refused('invalid_request_identity')
        output = core._object(core._regular_bytes(artifact, ARTIFACT_LIMIT))
        post = core._single_post(output)
        projected = post.get('source_action_id'), post.get('source_topic')
        if any(not isinstance(value, str) for value in projected) or projected != identity:
            raise core.Refused('request_identity_mismatch')
        core._require_signature(inputs, original_signature)
        result.update(request_binding='MATCH', reason='request_binding_matches_still_held')
    except core.Refused as exc:
        result['reason'] = str(exc)
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError):
        result['reason'] = 'unreadable_or_invalid_input'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--request-snapshot')
    parser.add_argument('--expected-request-sha256')
    parser.add_argument('--artifact')
    args = parser.parse_args(argv)
    result = qualify(offline=args.offline, request_snapshot=args.request_snapshot,
                     expected_request_sha256=args.expected_request_sha256,
                     artifact=args.artifact)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['request_binding'] in ('DISABLED', 'MATCH') else 1


if __name__ == '__main__':
    raise SystemExit(main())
