# Offline retained-evidence completion

Separate scope stacked on PR16 at71a25caec817ce26b043fe6c72d91fccc7a2ca29.
PR14 f15cf3f5 and PR16 remain unchanged. Their genuine Gate execution failures
remain external blockers; neither head was re-requested. This implementation
is an authorised new evidence-integrity gap, not a retry or approval substitute.
Director owns normal dependency merges and subsequent retarget/rechecks.

## Gap and behavior

The oracle previously ignored the retained stream's write count and could
return an in-memory result without explicitly flushing and syncing evidence.
It now requires the full serialized character count, flushes the stream, and
calls fsync before returning. Evidence failures propagate as errors, including
on input-refusal paths. Input read errors still produce retainable HOLD results.
Exclusive creation is unchanged: empty/partial/fully written evidence left by
an error is preserved and cannot be overwritten by a repeated attempt.

Default OFF performs no input/evidence I/O. Every returned result remains HOLD
with enabled/approved/publish_allowed false. No retry, repair, publication,
generation, runtime caller, dependency or workflow is introduced.

## Scope inspection

Richard's connected GitHub returned only project PR14/15/16 and no standalone
active issue claim. PR15 current620856d6's17-file inventory owns envelope,
request/map provenance, strict JSON, source-file identity, permissions and locale
qualification. Its qualifiers are read-only and do not retain evidence streams.
PR16 owns member names and membership drift. Targeted org Blog/evidence/fsync
and transfer/short-write searches returned no competing code PR. Broad umbrella
migration issues do not authorize their live scopes. No exhaustive external
registry clearance is asserted. No sibling path is edited.

## Tests and after-merge smoke

Three new standalone tests use static synthetic bytes only, with no producer,
writer, network or content generation. They exercise successful flush-before-sync
visibility, OFF/no sync, write exception, zero/short count, flush failure, sync
failure on complete/missing/extra/missing-custody inputs, input preservation,
and reservation of failed evidence against overwrite. Failures do not return
results. Removing sync in disposable scratch gives5 assertion failures/zero
errors; removing the short-count guard gives2. Neither mutant is retained.

```sh
python3 -I -B -m unittest discover -s tests -p 'test_city_producer_evidence_completion.py' -v
python3 -I -B -c "import runpy; r=runpy.run_path('tests/offline_output_transfer.py')['inspect_transfer'](); assert r['reason']=='offline_not_requested' and r['publish_allowed'] is False; print(r)"
```

Python3.12.14: new3 tests PASS; combined25 PASS/zero skips, using the existing
independently authenticated explicit scratch producer and synthetic callbacks:

```sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
```

Unchanged pin: ironclad-infra0bd7ae3754acbf056558c89b87240bedda98a7aa,
scripts/city_blog_draft.py, SHA256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.

## Limits and rollback

Successful fsync is not a crash-durability or atomic directory-entry guarantee:
the parent directory is not synced, and storage hardware/volume semantics remain
unqualified. A killed process or I/O error may leave incomplete evidence. Preserve
it as UNKNOWN/incomplete, never remove or replay it to obtain a clean result.
No authentication, file-permission policy, hostile filesystem snapshot, native
admission, exactly-once publication or migration completion is established.

Rollback reverts this follow-up only, restoring the prior oracle and removing
this document/new test module. Dependencies and live state are untouched. All
runtime controls remain OFF/READY=no. No deploy/live flip, paid service, stock,
Ads, GA4, secret, SSH/restart, Kubernetes or Commerce82 replay operation occurs.
Require genuine exact-head APPROVE>=8/zero blockers and applicable passing checks;
execution failures remain blockers, never artificial source retriggers.
