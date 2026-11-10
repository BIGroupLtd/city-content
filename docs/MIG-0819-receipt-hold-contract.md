# Offline native draft receipt hold contract

This separate main-based PR adds tests/offline_draft_receipt_contract.py, a
test-only, explicitly invoked pure-data qualifier. It checks mandatory hold
metadata in an already decoded synthetic native receipt. No wire parser,
filesystem, runtime caller, provider, generator or publisher is added.
Default OFF: offline=True must be supplied before inspecting the argument.
Every result remains HOLD with enabled=false, approved=false and
publish_allowed=false. MATCH is never admission or an AI review verdict.

## Boundary after saved artifact envelope integrity

The pinned adapter's artifact envelope is separate from its draft-result
receipt. An artifact/identity match cannot establish that the receipt still
retains unresolved full-gate obligations or truthful draft/model metadata.
This qualifier requires the six native control fields, draft_only/absent
markers, pinned requested-model string, a null or matching reported-model
string, a list of native hold strings, and each of the five fixed missing
full-gate inputs exactly once. Marker list order is immaterial; omissions,
duplicates, unknowns, wrong types and cleared lists refuse.

The five native obligations are current_master_rules_binding,
verified_claim_sources, native_site_enrollment, current_estate_similarity_corpus
and retained_full_builder_gate_result. Empty native_violations never removes
these obligations. A null reported model remains compatible with an injected
offline writer and proves no live model execution or model identity.

The source is the existing independently authenticated pinned City adapter:
ironclad-infra 0bd7ae3754acbf056558c89b87240bedda98a7aa,
scripts/city_blog_draft.py, SHA256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
Source is supplied explicitly in scratch; no vendor copy or new dependency.
Native source, receipt generation, policy and all original holds stay unchanged.

## Tests and after-merge smoke

Source-free contract suite, no writer/model/provider:

~~~sh
python3 -I -B -m unittest discover -s tests -p 'test_draft_receipt_contract.py' -v
~~~

Eight methods PASS, zero skips: valid empty/nonempty holds, unknown-model versus
null evidence, poison-object OFF/no inspection, every missing control, every
missing/duplicate/unknown/typed full-gate marker, forged/coerced draft markers,
model mismatch, and invalid native-hold representation. Results are value-free,
silent and input-preserving. Fixture flags are synthetic/HOLD/OFF/not a queue.

Full original-main plus native receipt integration:

~~~sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test*.py' -v
~~~

22 methods PASS, zero skips: 12 original, eight source-free and two new native
receipt methods. Reuses the existing dry-run-hold matrix and original harness.
Actual returned and saved pinned receipts agree for clean/floor/combined holds;
corrupted receipt copies cannot clear mandatory full-gate markers even when
native_violations is empty. All callbacks are canned synthetic doubles, not
content generation. Existing HTTP/process/native-loader and added DNS/connect
guards remain active; environment cleared. Producer artifacts are unchanged
by qualification, and decoded inputs are never mutated.

Scratch-only negative controls bypassing full-gate and model checks yield
26 and 12 assertion failures respectively, zero execution errors. No mutant
is retained; fresh unmodified source passes again.

Direct OFF/positive/refusal smoke:

~~~sh
python3 -I -B - <<'PY'
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path('tests').resolve()))
from offline_draft_receipt_contract import qualify
receipt = json.loads(pathlib.Path(
    'tests/fixtures/city-producer/receipt-hold-contract.json'
).read_text(encoding='utf-8'))['receipt']
for value, active, expected in (
    (object(), False, 'DISABLED'),
    (receipt, True, 'MATCH'),
    (dict(receipt, missing_full_gate_inputs=[]), True, 'REFUSED')
):
    result = qualify(value, offline=active)
    assert result['receipt_contract'] == expected and result['status'] == 'HOLD'
    assert result['publish_allowed'] is False
    print(json.dumps(result, sort_keys=True))
PY
~~~

Observed DISABLED/HOLD, MATCH/HOLD, REFUSED/HOLD, all authority booleans false.

## Limits, ownership and rollback

This checks decoded hold metadata only. It does not parse or authenticate JSON,
reject all extra receipt fields, inspect hashes/run/action IDs, validate native
hold prose, discover erased prior native holds, prove sender custody, check
artifact/body bytes, or authorize policy/full-gate/job/attempt/publication.
An empty native list replacing a real prior list can still MATCH/HOLD without
independent sender evidence: that limit is executable. Extra unexamined metadata
cannot change the report's false authority booleans. All receipt/body custody,
wire encoding, directory/durability and original-owner controls remain separate.

Fresh project PR/issue inspection preceded work: PR15 owns saved envelope/
request/map qualification; PR14 transfer and run/action identity; PR16 unexpected
members; PR17 retained evidence write/flush/fsync. Their current scopes and file
inventories were read. Targeted native_violations/missing_full_gate_inputs/
draft-receipt-contract searches found no matching producer hold-contract owner.
No peer path changes or exhaustive external claim-registry clearance asserted.

This branch starts directly at main fc27ea98f51eecfb46884b207b56866d2d66a765,
with five new paths and no unmerged dependency. PR15 branch/head remains
unchanged. Rollback is reviewed removal of these five inert files; no live state
to restore. No generation/publishing, merge/deploy/live flips, paid services,
secret exposure, Hetzner/Vault SSH/restarts, GA4_FEED_ENABLED, stock/Ads/wealth/
crypto/new-MCP/Kubernetes changes or Commerce82 replay.

Director owns merge only after genuine exact-head Gate APPROVE >=8/zero blockers
and every required check. Existing provider execution failures and uncertain
effects are preserved; no blind retries, substituted approval or bypass.
