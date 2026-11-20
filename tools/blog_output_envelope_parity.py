"""Default-OFF native draft projection-envelope check; never publication authority."""
import argparse
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'blog_output_envelope_core', Path(__file__).with_name('blog_output_map_parity.py'))
core = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(core)

# Exact outer post projection in the independently pinned City draft adapter.
# Nested editorial data and field values are intentionally outside this check.
POST_FIELDS = frozenset(('title', 'slug', 'intro', 'sections', 'citations',
                         'source_action_id', 'source_topic'))
PROVENANCE_FIELDS = frozenset(('source_action_id', 'source_topic'))


def qualify(*, offline=False, artifact=None):
    result = {'status': 'HOLD', 'enabled': False, 'approved': False,
              'publish_allowed': False, 'envelope_binding': 'DISABLED',
              'reason': 'offline_not_requested'}
    if offline is not True:
        return result
    result.update(envelope_binding='REFUSED', reason='unreadable_or_invalid_input')
    try:
        inputs = (artifact,)
        original = core._input_signature(inputs)
        output = core._object(core._regular_bytes(artifact, core.ARTIFACT_LIMIT))
        post = core._single_post(output)
        if set(output) != {'blog_posts'} or set(post) - POST_FIELDS:
            raise core.Refused('foreign_output_field')
        if not PROVENANCE_FIELDS.issubset(post):
            raise core.Refused('missing_provenance_field')
        core._require_signature(inputs, original)
        result.update(envelope_binding='MATCH', reason='native_envelope_matches_still_held')
    except core.Refused as exc:
        result['reason'] = str(exc)
    except (OSError, TypeError, ValueError, UnicodeError, RecursionError):
        result['reason'] = 'unreadable_or_invalid_input'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--artifact')
    args = parser.parse_args(argv)
    result = qualify(offline=args.offline, artifact=args.artifact)
    print(json.dumps(result, sort_keys=True))
    return 0 if result['envelope_binding'] in ('DISABLED', 'MATCH') else 1


if __name__ == '__main__':
    raise SystemExit(main())
