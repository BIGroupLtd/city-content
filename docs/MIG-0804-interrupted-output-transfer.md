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

Validation: Python 3.12, all 15 producer tests PASS (12 existing plus 3 new).
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
