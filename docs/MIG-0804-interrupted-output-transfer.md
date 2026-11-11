# MIG-0804: interrupted output transfer (offline only)

On 2026-11-10, Richard's GitHub connection returned no open PRs or
issue claims in BIGroupLtd/city-content. Main was
fc27ea98f51eecfb46884b207b56866d2d66a765, containing merged #11–#13.
The existing bank-boundary, source-evidence and dry-run hold suites did not
exercise interrupted artifact/receipt writes or truncated receiving bundles.
This PR claims that synthetic parity gap only.

The producer remains the independently authenticated upstream source from
`tests/fixtures/city-producer/bank-boundary.json`: ironclad-infra commit
0bd7ae3754acbf056558c89b87240bedda98a7aa, scripts/city_blog_draft.py,
SHA-256 5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
It is supplied explicitly in scratch storage, never copied into this repository.

The new test-only receiving oracle inspects the two existing producer artifacts.
It requires a sender receipt digest supplied separately from the receiving
directory, validates the artifact digest, and retains only byte counts, hashes
and fixed HOLD reason codes in an exclusively created evidence file. Missing,
empty, truncated, substituted or forged files cannot become complete drafts.
Even complete drafts remain HOLD with enabled, approved and publish_allowed
false. No network, publisher callback, scheduler, CLI or runtime wiring exists.
The oracle is not an authenticated admission gate or a production importer.

Retries use a new evidence path. Existing evidence is never replaced. A failed
producer output directory also remains reserved: the actual pinned producer
refuses a second generation before calling the mock writer and preserves the
partial bytes. A clean offline retry can use a fresh directory; a complete
retry still cannot authorize publication. There is no automatic retry or
commerce82 replay. Process death during evidence writing may leave an empty or
partial evidence file: treat it as incomplete, preserve it, and inspect again
using a fresh path. This is not crash-durable storage or live exactly-once proof.

Validation: Python 3.12, all 18 producer tests PASS (12 existing plus 6 new).
The new tests include ten missing/truncated delivery cases, valid-JSON body
substitution, a self-consistent forged receipt, interruptions after partial
artifact and partial receipt writes, preservation on repeated delivery and
blocked generation replay. Existing harness poison guards prohibit sockets,
HTTP transports, subprocesses and native writer loading. Only synthetic mock
posts and temporary directories are used; no content is authored.

Reproduce with the explicit authenticated scratch source:

```sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
```

No workflow, gate configuration, provider, flag, stock, GA4, cron, deployment,
SSH, Kubernetes or live state changes. All existing custody and full-gate holds
remain, READY=no. Rollback removes only this document and the two new test
files; there is no runtime state to restore. Exact-head hosted checks and the
genuine AI Review Gate must still pass before this work can be accepted.

## Follow-up: bind intact transfers to the expected attempt

The original head 2000c8129cc8f5ac8aa33192d883883f82f51597 passed
Pre-merge gates and genuine App4760566 AI Review Gate129727472475:
APPROVE, confidence9, zero blocking findings. No source failure was outstanding.
On the follow-up, project sibling #15's actual inventory and map qualifier
were inspected: it owns cleanup/permissions/locale/map provenance, not transfer
attempt identity. Project issues had no active claim; targeted open org
builderRunId and Blog identity/run transfer searches found no competing code
claim. This is scoped search evidence, not external-registry clearance.

The next gap is an intact old bundle accompanied by its own correct sender
digest. Hash integrity alone does not establish the expected attempt. The same
test-only oracle now requires separately supplied expected builderRunId and
source_action_id, compares both exactly, and retains no identifier values.
Missing custody, wrong run and wrong action are held. Custody supplied by the
caller is not authentication and cannot authorize a live retry or publication.
The oracle defaults OFF: without offline=True it performs no filesystem access
and returns offline_not_requested/HOLD. No runtime caller is added.

After-merge default smoke (no source file or data access):

```sh
python3 -I -B -c "import runpy; m=runpy.run_path('tests/offline_output_transfer.py'); r=m['inspect_transfer'](); assert r['reason']=='offline_not_requested' and r['publish_allowed'] is False; print(r)"
```

Run the full explicit-source command above for positive, refusal, partial-write,
duplicate-evidence and retry smoke. All writers are synthetic doubles; no model
or editorial generation occurs. The two-attempt test uses distinct producer
run IDs with the same synthetic body and verifies that stale-run custody fails
even when the delivered receipt hash is correct. A fresh matching attempt still
returns complete_draft_still_held. No duplicate publish is possible in this
oracle because it has no publisher capability; live exactly-once effects remain
unqualified. The new head requires its own genuine Gate approval.
