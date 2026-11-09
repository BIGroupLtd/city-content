# B219 — City producer dry-run holds, offline only

This three-file delta is stacked on city-content #12 at
562831ffb4f2b17bdf20b48d1f6ae458a801800c, which fixes #11. It extends that
existing authenticated producer harness; it does not copy a producer, add a
scheduler, or supersede the upstream implementation. Review/land dependencies
through their existing PRs before retargeting this PR to main.

`tests/fixtures/city-producer/dry-run-holds.json` is synthetic test data only,
HOLD, disabled, unapproved, not a runtime queue, with cron disabled and READY=no.
The matrix covers native refusal, 1999 words, their combined holds and the 2000
word boundary. Even clean mock native validation leaves gatePass absent and
status draft_only with missing full-gate inputs. Each case verifies the saved
receipt, exact two-artifact set, and refusal to overwrite a previous run before
calling a retry writer. Tests use inherited mock writers and poisoned network,
process and native-writer entrypoints; output lives only in temporary directories.
These checks do not validate real research, native writer, CMS, runtime or replay.

## Reproduce

Use #12's explicit connector-supplied scratch source and authentication procedure:
ironclad-infra scripts/city_blog_draft.py at
0bd7ae3754acbf056558c89b87240bedda98a7aa, SHA-256
5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06.
Set CITY_PRODUCER_SOURCE to that offline file, then run:

```sh
python3 -I -B -m unittest discover -s tests -p 'test_city_producer_bank_boundary.py' -v
```

Cloud Python 3.12.14 on 2026-11-07: 7 tests PASS, including four new matrix
subcases and retry evidence checks. Missing source configuration and modified
source both fail nonzero without skips. JSON/Python syntax and whitespace pass.
No packages installed or source downloaded by the tests; no git fetch/push.

## Holds and next job

Factory MASTER-RULES.md and contamination-markers.json are still missing
original-custodian inputs. Gates remain fail-closed, READY=no. Offline test
success cannot admit generation or publication. Bank/research/action custody,
immutable release, sole-writer/drain, queue/checkpoint/restore custody and
UNKNOWN/no-replay reconciliation remain separate holds under the existing lanes.

Reuse #11/#12 and the upstream B71 bank ownership recorded there. Do not recreate
Wave9 or other supplied merged infrastructure work. No production code, workflow,
cron, environment, deployment, credential, analytics flag, protected Engineer
path or Shopify stock changes. Shopify blog writer remains PARKED.

Next job: resolve #11/#12 review dependencies, then continue the existing B71
first-batch review and same-owner second-batch sequence. Original custodians must
supply missing policy and state evidence before any separately admitted
nonpublishing preflight. Scheduling and publication stay disabled.

Exact-head required reviews/checks remain outstanding; no merge or activation.
Rollback is removal of this additive fixture/document and test method; no live
state changes exist to restore.
