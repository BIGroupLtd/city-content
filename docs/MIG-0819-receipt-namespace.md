# Offline native receipt field namespace

This separate main-based PR adds a test-only pure-data namespace qualifier for
the decoded native draft-result receipt. Default OFF: offline=True must be
supplied before inspecting the argument. Every outcome is HOLD with enabled,
approved and publish_allowed all false. No parsing, file/network I/O, native
runtime caller, provider, generator or publisher is added.

The pinned adapter emits eleven receipt fields. Exact field membership refuses
foreign operational/unknown fields and missing fields. It does not inspect any
field VALUE, infer approval from status/gatePass, or authenticate the receipt.
Reordered keys are compatible; missing and extra keys cannot cancel by count.
Reports contain only fixed codes/booleans, not names, values or exception text.

This is distinct from PR15's saved ARTIFACT envelope and original-input checks,
and PR19's native hold/model metadata VALUE contract. PR14 transfer/attempt/hash
custody, PR16 membership, PR17 evidence completion and PR18 evidence readback
remain separate. Names-only MATCH may coexist with invalid values: an explicit
test returns MATCH/HOLD for a receipt whose status/model/gates/hashes are wrong.
Those value/authenticity checks remain mandatory under their original owners.

## Source and synthetic qualification

The independent source anchor is unchanged:
ironclad-infra 0bd7ae3754acbf056558c89b87240bedda98a7aa,
scripts/city_blog_draft.py, SHA256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
The existing main harness authenticates supplied scratch bytes before execution;
no source copy, dependency or pin change is included.

Source-free smoke/tests:

~~~sh
python3 -I -B -m unittest discover -s tests -p 'test_draft_receipt_namespace.py' -v
~~~

Eight methods PASS, zero skips: synthetic/OFF fixture, reordered keys, poison
object default OFF, each eleven missing field, 51 foreign-field/value cases,
33 case/hidden-Unicode aliases, malformed shapes/typed keys, same-count
missing/extra substitutions, silence/input preservation and explicit limits.
No receipt or logical article identity validation/comparison is implemented.

Full original-main plus native integration:

~~~sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test*.py' -v
~~~

22 methods PASS, zero skips: twelve original, eight source-free and two native
receipt tests. Reuses the existing dry-run matrix and pinned producer harness.
Actual returned and saved receipts retain the namespace for clean/floor/
combined native holds; forged extra fields on copies refuse. Only canned
synthetic callbacks execute, with environment cleared and HTTP/process/native
loader plus DNS/connect poison guards. Qualification never changes decoded
inputs or native artifact bytes. No model/content generation.

Scratch-memory negative controls removing foreign/missing field checks yield
51/11 assertion failures respectively, zero execution errors. No mutant remains.
Unmodified source passes again.

Direct default/positive/refusal smoke:

~~~sh
python3 -I -B - <<'PY'
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path('tests').resolve()))
from offline_draft_receipt_namespace import qualify
receipt = json.loads(pathlib.Path(
    'tests/fixtures/city-producer/receipt-namespace.json'
).read_text(encoding='utf-8'))['receipt']
for value, active, expected in (
    (object(), False, 'DISABLED'),
    (receipt, True, 'MATCH'),
    (dict(receipt, approved=True), True, 'REFUSED')
):
    result = qualify(value, offline=active)
    assert result['receipt_namespace'] == expected and result['status'] == 'HOLD'
    assert result['publish_allowed'] is False
    print(json.dumps(result, sort_keys=True))
PY
~~~

Observed DISABLED/HOLD, MATCH/HOLD and REFUSED/HOLD; all authority booleans false.
Fixture zeros/metadata are synthetic, not real run or hash custody.

## Ownership, limits and rollback

Before editing, fresh project PR/issue inspection found PR14–19 and no active
issue claim. Relevant current scopes/file inventories were inspected. Targeted
receipt namespace/foreign-field searches found no matching native draft-result
owner. #6020's actual scope/inventory is terminal-exception structured logs,
not this draft-result. MIG-1100 Blog/#6089 owns logical-article identity and
cross-article payload binding; that scope is explicitly excluded. This change
contains no identity, uniqueness, collision, deduplication or cross-article
logic; the qualifier never dereferences field values. No external registry
clearance claim.

Input is already decoded synthetic dictionaries, not wire bytes. No duplicate
JSON detection, scalar/encoding/type/value validation, receipt/body hash,
sender/run/action custody, policy/model evidence, held-content authenticity,
durability, live readiness or migration completion is claimed. Native source
and serializer stay unchanged. Independent custody and all original-owner
holds remain required; no UNKNOWN attempt replay or repair is admitted.

Five additive paths directly on main fc27ea98f51eecfb46884b207b56866d2d66a765.
No unmerged dependency and no PR15/PR19 or unrelated edits. Rollback is reviewed
removal of these five inert files. Everything default OFF. No generation/
publication, merge/deploy/live flip, paid services/secrets, Hetzner/Vault SSH/
restart, GA4_FEED_ENABLED, stock/Ads/wealth/crypto/new-MCP/Kubernetes change or
Commerce82 replay. Director owns merge after genuine exact-head Gate APPROVE
>=8/zero blockers and all required checks. Preserve external provider recovery
holds, uncertain effects and allowances; no blind retry or substitute approval.
