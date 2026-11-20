# Offline evidence bytes and pathname binding

Separate scope stacked on PR17 head682ad2140c4ad62520a201a5b7db8d7558f20995.
PR14/16/17 heads and their provider-execution blockers remain unchanged, with
no re-request, bypass or source bump solely for a retry. Director owns normal
dependency merges, then retarget/rechecks. This PR is not migration acceptance.

## Gap

PR17 checks write count, flush and fsync, but those acknowledgements alone do
not establish that retained bytes equal the returned result or that the named
evidence path still refers to the opened file. The oracle now exclusively opens
evidence for read/write, then verifies the descriptor's single link and its
device/inode/mode against a no-follow pathname observation. A bounded positional
read of exactly serialized-size-plus-one must equal the UTF-8 payload. Changed,
truncated, appended, replaced or symlinked evidence refuses return. Readback I/O
errors propagate; reserved evidence is never repaired, removed or overwritten.
All successful results remain HOLD/false authority booleans; default OFF does
no filesystem I/O. No publisher, generator, runtime caller or new CLI is added.

## Claims and sibling boundaries

Fresh Richard-connection inspection returned only PR14/15/16/17. Project had no
standalone active issue claim. PR15 current620856d6 and its17-file inventory own
read-only source envelope/provenance/identity qualification, not retained evidence
output. PR16 owns bundle membership; PR17 evidence write completion. Targeted
org evidence_readback search returned no match; broad Blog/evidence/readback
search returned umbrella issues, not competing code PRs. No peer path is edited
and no exhaustive external-registry clearance is asserted.

## Focused tests and after-merge smoke

Four new methods use static synthetic identity bytes, with no producer, writer,
network, model or editorial generation. They cover valid HOLD readback, OFF,
same-length changed bytes, truncation, appended bytes, same-byte pathname
replacement, symlink replacement, read errors and preservation against replay.
Negative controls in disposable scratch remove byte verification or identity
verification; both produce assertion failures/zero errors. No mutant retained.

```sh
python3 -I -B -m unittest discover -s tests -p 'test_city_producer_evidence_readback.py' -v
python3 -I -B -c "import runpy; r=runpy.run_path('tests/offline_output_transfer.py')['inspect_transfer'](); assert r['reason']=='offline_not_requested' and r['publish_allowed'] is False; print(r)"
```

Python3.12.14: focused4 PASS, combined29 PASS/zero skips. Full synthetic harness:

```sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
```

Existing source pin unchanged: ironclad-infra0bd7ae3754acbf056558c89b87240bedda98a7aa,
scripts/city_blog_draft.py, SHA256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
Only explicit scratch source and synthetic doubles are used by inherited tests.

## Limits and rollback

Readback is a bounded observation through the same descriptor/page cache, not
an independent disk/hardware verification or adversarial atomic snapshot.
Mutation after an observation or ancestor replacement remains outside the proof.
No parent-directory sync, crash durability, authentication, source approval,
exactly-once publication or live acceptance is claimed. Preserve failed or
UNKNOWN evidence; never delete/repair/replay it to obtain a clean result.

Rollback reverts only this follow-up, removes this document/test module and
restores PR17's prior oracle. All original custody/full-gate holds remain.
Everything stays OFF/READY=no; no merge/auto-merge, deploy/live flips, paid
services, stock/Ads/GA4/secret changes, SSH/restarts, Kubernetes or Commerce82
replay. Fresh exact-head genuine APPROVE>=8/zero blockers and passing checks
remain mandatory; execution failures cannot be substituted with local review.
