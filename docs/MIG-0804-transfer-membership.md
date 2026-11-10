# Offline transfer bundle membership

This stacked follow-up depends on PR14 at
f15cf3f538c453152d91d9b16bf96aa914eb765a. PR14 is unchanged: its exact-head
Pre-merge check129765949264 passed, while genuine App4760566 check129766127516
failed PROVIDER/TIMEOUT/CLI_TIMEOUT without a source finding or verdict.
The user confirms no re-request occurred. This follow-up does not retry that
check, reset its allowance, or treat historical approval as current approval.
Director owns merges; merge the dependency normally and retarget/recheck this
follow-up before accepting it against main.

## Gap and claim inspection

The previous oracle inspected only two named files and ignored other directory
members. An intact pair plus a stale receipt backup, partial-transfer sidecar,
hidden file, publish marker or nested directory could be labelled complete.
The oracle now requires exactly site-config.json and draft-result.json, and
rechecks member names after reading both. Unexpected initial membership or
changed membership refuses completion, preserves every input, and retains a
fixed reason without copying untrusted member names or content into evidence.
Every outcome remains HOLD with enabled/approved/publish_allowed false.

Fresh Richard-connection inspection on 2026-11-10 found city-content PR14 and
PR15 and no other active issue claim. PR15's current head7b1ca37d and14-file
inventory own original request/topic projection, map provenance, JSON scalar
validation, pair file identity, permissions, cleanup and locale. No sibling
files are changed. Targeted org Blog/bundle/inventory, transfer/sidecar and
output/unexpected-title searches found no competing code PR. Broad migration
umbrella issues are not clearance for their live scopes. No external-registry
clearance is asserted.

## Verification and after-merge smoke

The four new tests construct only static synthetic identity bytes, without
calling any producer or writer. They cover the exact pair, five sidecar types,
no payload reads on initial refusal, redacted/preserved metadata, a sidecar
appearing during the body read, exclusive prior evidence, and repeated refused
delivery. Removing the final membership comparison in disposable scratch causes
exactly one assertion failure/zero errors. The mutant is not retained.

Run the new standalone smoke without any producer source, model or network:

```sh
python3 -I -B -m unittest discover -s tests -p 'test_city_producer_transfer_membership.py' -v
python3 -I -B -c "import runpy; r=runpy.run_path('tests/offline_output_transfer.py')['inspect_transfer'](); assert r['reason']=='offline_not_requested' and r['publish_allowed'] is False; print(r)"
```

Python3.12.14: these4 tests PASS. Combined22 tests PASS/zero skips using the
existing explicit authenticated scratch producer, synthetic callbacks only:

```sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
```

Source pin is unchanged: ironclad-infra0bd7ae3754acbf056558c89b87240bedda98a7aa,
scripts/city_blog_draft.py, SHA256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
No source copy, dependency or workflow is added.

## Limits and rollback

This qualifies observed directory member names only. It does not establish
inode/link/ancestor authenticity, stable snapshots, crash durability or absence
of mutation after observation. An attacker that adds and removes a member
between observations is outside this check. Evidence must be outside the
two-file bundle; an in-bundle evidence path is itself an unexpected member and
remains held. No deletion, quarantine, automatic retry or repair is performed.
Do not remove UNKNOWN evidence to obtain a complete result.

Default OFF remains unchanged: only explicit offline=True inspects inputs.
No publication, generation, runtime caller, deploy, live flip, paid service,
stock/Ads/GA4 change, SSH/restart, Kubernetes or Commerce82 replay. READY=no.
Rollback reverts this follow-up commit only, restoring the prior oracle and
removing this document and membership tests. It does not withdraw PR14 or
change live state. Fresh exact-head CI and genuine APPROVE>=8/zero blockers
remain required; no artificial retry or substitute approval.
