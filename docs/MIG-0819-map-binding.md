# Offline original-map binding qualifier

tools/blog_output_map_parity.py is a read-only, default-OFF migration qualifier.
It never loads a writer, calls a provider, imports a native runtime, changes a
file or admits publication. Even MATCH always returns HOLD, enabled=false,
approved=false and publish_allowed=false. It is not wired to any pipeline.

~~~sh
python3 -I -B tools/blog_output_map_parity.py
python3 -I -B tools/blog_output_map_parity.py --offline \
  --receipt /explicit/synthetic/draft-result.json \
  --map-snapshot /explicit/retained-map.json \
  --expected-map-sha256 INDEPENDENTLY_RETAINED_SHA256 \
  --request-host allowed.example
~~~

Default mode performs no file reads and exits 0 with DISABLED/HOLD. Explicit
offline MATCH exits 0; REFUSED exits 1. Output contains only fixed reason codes
and hold booleans, never paths, map/receipt contents or exception text. This is
a standalone offline CLI, not an MCP tool or added MCP argument.

## Demonstrated gap and implementation

The existing independently authenticated pinned City producer chooses its
canonical destination before the injected mock writer, but reads the map bytes
again when building the receipt afterward. Real synthetic tests change that
file inside the mock callback. The actual producer retains the old destination
and reports the changed file's digest. Byte-only formatting changes, destination
changes, key removal and unrelated-key additions all demonstrate this epoch gap.
No native source or existing runtime owner path is changed here.

The qualifier requires an original snapshot and an independently retained SHA256
baseline, then compares the receipt's map digest, canonical destination and
HTTPS origin against that snapshot's requested host binding. Apex and www
request spellings follow the snapshot's explicit apex/www destination. Missing
keys, foreign destinations, wrong digests or cleared native draft markers refuse.
Strict UTF-8 JSON objects reject duplicate fields and nonfinite extensions.
The original map schema permits only explicit apex-to-apex/www bindings.

Both agreeing substituted candidate files refuse against the original digest.
This does NOT authenticate a file/digest pair supplied together. Changing the
trusted digest can produce MATCH, as an explicit limit test demonstrates; MATCH
still never supplies authority. Independently authenticated baseline custody,
current exclusions, full policy, sole-writer and original-owner controls remain
necessary. No current operational map or private data was read.

The POSIX reader uses nonblocking, no-follow leaf opens; requires a regular
single-link file; caps snapshots at 128 KiB and receipts at 64 KiB; reads through
EOF; checks size and descriptor metadata stability; and always closes the
descriptor. Short reads remain valid. FIFO/directory/symlink/hardlink leaves,
oversize, read errors or observed rewrites refuse. These bounded reads protect
this offline qualifier only, not the native writer or receipt-transfer path.

## Qualification and limits

Run all existing and added producer regressions with the unchanged source pin:

~~~sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
~~~

38 methods PASS, zero skips, including seventeen map-binding methods. Actual
source authentication remains ironclad-infra
0bd7ae3754acbf056558c89b87240bedda98a7aa,
SHA256 5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
Only synthetic temporary maps/receipts and injected callbacks execute. Existing
network/process/native-loader poison guards and additional DNS/connect guards
remain active; inherited environment is cleared. Retained artifact bytes,
inode, mode, size and ns-mtime stay unchanged. Descriptor cleanup is tested on
rewrite and read exceptions. Exact caps, deeply nested/ambiguous/bad JSON,
missing/malformed custody inputs, every binding field, default OFF and actual
CLI main dispatch/redaction are covered. A scratch-memory mutation deleting the
receipt map-digest check yields four assertion failures and zero errors; the
unmodified qualifier passes again. No mutant is retained.

This qualifies only map/destination consistency, NOT artifact bytes/receipt
authenticity, whole-output acceptance, publication admission, current pathname
after the final observation or adversarial snapshot stability, ancestor
symlinks, mount/ACL custody, live
time freshness, physical durability, deployed/current-upstream compatibility
or migration completion. The native source's dual read is not repaired. Do not
rewrite/resubmit/replay an uncertain attempt or replace its evidence to get
MATCH. Original owner reconciliation and all prior holds remain.

## Ownership and delivery boundary

Before editing, fresh connected-GitHub project inspection returned only #14 and
this existing #15, with no active project issue claims. Targeted all-state/open
org Blog host-map provenance, map_binding and canonical_host_map_sha256 searches
returned no matching owner. #14 retains interrupted transfer, #6022 reservation,
#6042 model-reply encoding, #6054 saved HTML packet encoding and #6064 native
HTML file-identity qualification. Previous PR15 scopes remain unchanged.
Bounded GitHub searches do not establish exhaustive external-registry clearance.

Three new disjoint paths only in this continuation: qualifier, focused tests
and this runbook, plus a link in the existing runbook. No source producer,
config, workflow, scheduler, dependency or live state change. Default OFF;
rollback is normally reviewed removal of these additions, preserving all prior
evidence/scopes. No content generation or publication, merge/deploy/live flip,
paid services, Hetzner/Vault SSH/restarts, GA4_FEED_ENABLED, stock/Ads/wealth/crypto
changes, new MCP tools/arguments, Kubernetes or Commerce82 replay.

Keep the same PR open/unmerged, auto-merge OFF. Acceptance still requires the
genuine exact-head App4760566 AI Review Gate APPROVE >=8 / zero blockers,
App15368 and every applicable protection. Local qualification cannot replace
those checks or authorize any runtime action.

## Whole input-pair stability

A follow-on red/green regression demonstrated eighteen false MATCH cases in the
previous qualifier: either map or receipt could change after its own stable
read, while validation still used the earlier bytes. This was a real offline
qualifier gap, separate from the native producer's map epoch gap.

The existing qualifier now records both no-follow leaf identities before
reading either file, then rechecks the whole pair after parsing and binding
checks, immediately before MATCH. Device/inode/mode/link count/size/mtime/ctime
must remain equal. Missing or changed names refuse with input_set_changed;
the recheck never opens or follows replacement leaves. The same metadata
identity helper serves the original descriptor reader. No CLI/schema/default
change and no new module or runtime caller.

Two regression methods inject six byte/mode/time changes and twelve leaf
substitutions across both inputs after their individually successful reads.
Substitutions cover identical bytes/mode/mtime on another inode, missing names,
symlink, FIFO, directory and foreign hardlink. Prior implementation: 18 assertion
failures, zero execution errors. Corrected implementation: all 33 producer
methods PASS, zero skips. Every refused input pair remains exactly as the test's
injection left it; the qualifier never rewrites/repairs/deletes anything.
Original retained artifacts remain unchanged.

Fresh sibling scope inspection preceded editing: only other project PR14,
no active project issue claims; targeted map/cohort/input_set_changed/qualifier
searches found no competing map qualifier. #6052/#6069 actual file inventories
own Factory receipt paths/sets and do not overlap these files. #5476 owns
published-HTML handoff checking, not this original-map qualifier. No external
claim-registry clearance asserted.

This is optimistic detection of observed ordinary changes, not locking or a
transactional/cryptographically authenticated snapshot. Ancestor changes,
adversarial change-and-restore beyond observable metadata, or mutation after
the final observation remain unqualified. MATCH remains HOLD, never admission.

After-merge smoke (stdlib only, fixed synthetic receipt, no producer/model):

~~~sh
python3 -I -B tools/blog_output_map_parity.py
python3 -I -B - <<'PY'
import pathlib, subprocess, sys, tempfile
with tempfile.TemporaryDirectory(prefix='mig0819-smoke-') as directory:
    mapping = pathlib.Path(directory) / 'map.json'
    mapping.write_bytes(b'{"allowed.example": "allowed.example"}')
    subprocess.run([
        sys.executable, '-I', '-B', 'tools/blog_output_map_parity.py',
        '--offline', '--receipt', 'tests/fixtures/city-producer/locale-output-result.json',
        '--map-snapshot', str(mapping),
        '--expected-map-sha256', '37bafb6d434ca6049a799107fa5a85a82f70caf783edbeadcaa0c9c48b916d80',
        '--request-host', 'allowed.example'
    ], env={}, check=True, timeout=10)
PY
~~~

Observed outputs are DISABLED/HOLD then MATCH/HOLD, all authority booleans false.
The full source-authenticated regression command above additionally exercises
the eighteen refusal cases. No package install, live data or provider required.

## Decoded input scalar validation

The next input-validation slice remains in this same qualifier/PR. Fresh
city-content PR/issue inspection still found only other PR14 and this PR, with
no active issue claim. Targeted map-qualifier scalar, receipt-surrogate and
receipt-1e309 searches found no other owner. Actual sibling file inventories
confirm #6042 owns model-reply/output encoding, #6054 saved HTML packet
encoding and #6055 native SEO/GSC metric qualification. None edits this
qualifier or owns its decoded receipt-metadata input boundary.

Raw UTF-8 decoding alone did not catch ASCII JSON escape sequences decoding
to lone surrogate code points. parse_constant rejected NaN/Infinity spellings,
but ordinary JSON numeric tokens such as 1e309 still overflowed to Python
infinity. Both could hide in otherwise unused receipt metadata and yield MATCH.
The prior parser reproduced 36 assertion failures and zero execution errors
across the new refusal/CLI cases.

The existing JSON reader now requires each parsed float to remain finite in
binary64 and validates every decoded string/key as UTF-8-encodable Unicode
scalars, including strings nested in arrays/objects. Traversal is iterative.
Fixed invalid_json_number and invalid_json_unicode codes refuse before MATCH,
with no values or exception text in output. No field meanings, host rules,
CLI arguments, schema, output authorization, runtime or default changes.

Five new methods cover eighteen overflow tokens/placements, sixteen lone
surrogate placements (values, native holds, nested keys and arrays), CLI
redaction/OFF-no-parse and positive compatibility. Finite max/subnormal edges,
signed zero, numeric-looking text, visible/decomposed Unicode, controls/interior
BOM and valid escaped surrogate pairs retain their input bytes and map MATCH
only under HOLD. All 38 methods pass, zero skips. This is finite binary64 float
qualification, not exact decimal arithmetic, integer/count business validation,
full receipt authentication or editorial acceptance. No bytes are normalized.

Additional after-merge refusal smoke (fixed synthetic bytes; no producer/model):

~~~sh
python3 -I -B - <<'PY'
import json, pathlib, subprocess, sys, tempfile
with tempfile.TemporaryDirectory(prefix='mig0819-scalar-smoke-') as directory:
    root = pathlib.Path(directory)
    mapping, receipt = root / 'map.json', root / 'receipt.json'
    mapping.write_bytes(b'{"allowed.example": "allowed.example"}')
    raw = pathlib.Path('tests/fixtures/city-producer/locale-output-result.json').read_bytes().rstrip()
    receipt.write_bytes(raw[:-1] + b', "synthetic_extra":1e309}')
    result = subprocess.run([
        sys.executable, '-I', '-B', 'tools/blog_output_map_parity.py',
        '--offline', '--receipt', str(receipt), '--map-snapshot', str(mapping),
        '--expected-map-sha256', '37bafb6d434ca6049a799107fa5a85a82f70caf783edbeadcaa0c9c48b916d80',
        '--request-host', 'allowed.example'
    ], env={}, capture_output=True, timeout=10)
    assert result.returncode == 1 and not result.stderr
    value = json.loads(result.stdout)
    assert value['reason'] == 'invalid_json_number'
    assert value['status'] == 'HOLD' and value['publish_allowed'] is False
    print(result.stdout.decode('ascii'), end='')
PY
~~~
