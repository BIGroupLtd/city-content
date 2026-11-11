# Offline original-request/output identity qualifier

tools/blog_output_request_parity.py is explicitly invoked, read-only and OFF
by default. It checks only the native saved post's source_action_id/source_topic
against an independently retained original request snapshot and SHA256.
Every result remains HOLD, enabled=false, approved=false, publish_allowed=false.
No generator, provider, model, importer, scheduler or publisher is loaded.

This is coherent with the same PR's original-map output provenance checks but
is a separate CLI. It reuses their bounded regular-file reader, strict decoded
JSON scalar parser and whole-input-pair metadata check. The map CLI's arguments
and output remain unchanged; no MCP tool or argument is introduced.

~~~sh
python3 -I -B tools/blog_output_request_parity.py
python3 -I -B tools/blog_output_request_parity.py --offline \
  --request-snapshot /explicit/retained-original-request.json \
  --expected-request-sha256 INDEPENDENTLY_RETAINED_SHA256 \
  --artifact /explicit/synthetic/site-config.json
~~~

Default mode exits 0 with DISABLED and performs no input reads. Explicit offline
MATCH exits 0; REFUSED exits 1. Both are always HOLD, with no authority to run,
retry, import or publish. Paths, identities, topics, post content and exception
text never enter the fixed-code report.

## Integrity boundary and limits

A transfer-consistent pair may still belong to another request. This qualifier
requires an original request byte snapshot and independent lowercase SHA256
baseline, nonblank string source_action_id/topic, exactly one dictionary post,
and exact string equality to its projected source_action_id/source_topic.
Identity strings are opaque: no trimming, Unicode normalization, topic
similarity, numeric coercion or invented request-ID format. Requests cap at
128 KiB and artifacts at 2 MiB. Shared no-follow/single-link/stable-read guards
and final pair identity checks apply to both.

It does not authenticate a self-supplied file/digest pair. Supplying a new
trusted baseline can match a substituted request/output; an explicit limit
test preserves that distinction. It checks no other native input-admission
fields and no artifact/receipt digest, body authenticity, map, exclusion,
editorial review, full gate, current job or live state. Altering body text while
retaining these two fields can still MATCH/HOLD, as another limit test shows.
Original independent sender custody/PR14 transfer checks, native admission,
policy and original-owner controls remain separate and necessary.

The saved output-request-identity.json fixture contains only synthetic identity
fields and HOLD metadata. It is not a full native generation request or queue.
No deployment, content generation, publication or UNKNOWN attempt replay is
authorized by any example or MATCH. Existing optimistic-reader limits remain:
no ancestor/mount/ACL or adversarial snapshot guarantee and no protection after
the final observation. Native producer source/defaults remain unchanged.

## Tests and after-merge smoke

~~~sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
python3 -I -B tools/blog_output_request_parity.py
~~~

All 53 current producer methods PASS, zero skips, including the eight preserved
request-binding tests and seven separate envelope tests.
Actual pinned native generate runs only with synthetic callbacks and authentic
source pin 0bd7ae3754acbf056558c89b87240bedda98a7aa / SHA256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
The snapshot is retained before the callback. Correct projection, forged-model
identity override, swapped valid outputs, each typed/missing identity, malformed
post shape, changed/self-consistent replacement snapshots, strict-parser
integration, exact caps, pair drift and default OFF/CLI redaction are covered.
Environment is cleared; HTTP/process/native-loader and DNS/connect guards
remain active. Inputs and retained sibling artifacts preserve bytes, inode,
mode, links, size, ns-mtime and ns-ctime. A scratch-memory identity-check bypass
yields three assertion failures and zero errors. No mutant is retained.

This smoke launches only the offline qualifier on fixed synthetic fixtures:

~~~sh
python3 -I -B - <<'PY'
import hashlib, json, pathlib, subprocess, sys, tempfile
request = pathlib.Path('tests/fixtures/city-producer/output-request-identity.json')
artifact = pathlib.Path('tests/fixtures/city-producer/locale-output-config.json')
base = [
    sys.executable, '-I', '-B', 'tools/blog_output_request_parity.py',
    '--offline', '--request-snapshot', str(request),
    '--expected-request-sha256', hashlib.sha256(request.read_bytes()).hexdigest(),
    '--artifact'
]
with tempfile.TemporaryDirectory(prefix='mig0819-request-smoke-') as directory:
    changed = json.loads(artifact.read_bytes())
    changed['blog_posts'][0]['source_topic'] = 'SYNTHETIC different request'
    wrong = pathlib.Path(directory) / 'wrong.json'
    wrong.write_text(json.dumps(changed), encoding='utf-8')
    for candidate, code, binding in ((artifact, 0, 'MATCH'), (wrong, 1, 'REFUSED')):
        result = subprocess.run(base + [str(candidate)], env={}, capture_output=True, timeout=10)
        assert result.returncode == code and not result.stderr
        value = json.loads(result.stdout)
        assert value['request_binding'] == binding and value['status'] == 'HOLD'
        assert value['publish_allowed'] is False
        print(result.stdout.decode('ascii'), end='')
PY
~~~

Observed: default DISABLED/HOLD, original identity MATCH/HOLD, wrong topic
REFUSED/HOLD; authority booleans false. Synthetic digest calculation in this
smoke demonstrates the interface, not live authenticated custody.

## Ownership, rollback and review

Fresh connected-GitHub project inspection returned only other PR14 and this
PR15, no active issue claims. Targeted request/output identity, source_action_id
and original-request-snapshot searches found no matching saved-output
projection owner. PR14's current patch and inventory were read: it owns receipt
custody/transfer, not original request field projection. #5986 actual inventory
and scope owns researcher admission BEFORE generation. #5994 owns ROW request
deduplication and #6064 native HTML file/storage identity. Their paths and
policies remain untouched. No external registry clearance is asserted.

Same existing PR only. Rollback removes this qualifier, its focused test, fixed
identity fixture and this runbook, plus the small shared-helper extraction
through normal review. All earlier PR scopes remain. No merge/deploy/live flip,
paid service, secret, Hetzner/Vault SSH/restart, GA4_FEED_ENABLED, stock/Ads/
wealth/crypto change, new MCP tool/argument, Kubernetes or Commerce82 replay.
Director owns merge after genuine exact-head AI Review Gate APPROVE >=8 with
zero blockers, App15368 and all mandatory checks. Provider failure is never
source approval, and this offline report cannot replace that Gate.
