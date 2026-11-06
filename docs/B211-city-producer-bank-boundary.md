# B211 — offline City producer bank boundary

This content repository carries a synthetic compatibility fixture, not a topic
bank, importer, scheduler or release candidate. Nothing consumes it at runtime.
The existing producer is reused from `BIGroupLtd/ironclad-infra`, at immutable
commit `0bd7ae3754acbf056558c89b87240bedda98a7aa`. The fixture pins the SHA-256
of `scripts/city_blog_draft.py`; the test authenticates and executes those exact
bytes. It never loads the native writer, downloads source or installs packages.

## Reproduce offline

Materialise that single source file through the GitHub connector at the named
commit into a scratch directory. Do not point at a live installation. From this
repository, set `CITY_PRODUCER_SOURCE` to the scratch file and run:

```sh
python3 -I -B -m unittest discover -s tests -p 'test_city_producer_bank_boundary.py' -v
git diff --check
```

Missing source configuration fails explicitly; missing or changed source cannot
produce a skipped/pass result. Source pins are test custody only and do not
change any runtime/release pin. Review source changes before updating the pin.

Six standard-library tests cover raw bank-row refusal, forged authority refusal,
missing research/action refusal despite planning-source text, unknown/excluded
destinations before writer/output, draft metadata stripping, preserved synthetic
native violations or length holds, artifact hash binding, and tampered-source refusal
before execution. Network transports, socket connections, subprocesses and the
native writer loader are poisoned. Mock generation writes only temporary draft
artifacts. No real research, full builder gate, importer/CMS, current runtime,
natural run or publication is qualified. A mock's clean native result is still
`draft_only`, with absent gatePass and outstanding full-gate inputs.

The fixture's `untrusted_fields` deliberately contains forged activation,
publication and READY values. These are negative test inputs, never acceptance
or environment configuration. Its top-level controls remain HOLD, disabled,
unapproved and not a runtime queue. No real topic rows are copied.

## Existing ownership and holds

At inspection, ironclad-infra B71/#5564 remains open at
`17a882e254e734495d386bac0107db5ac22c8269`: B71 owns its 300-topic first batch
and sequential second batch. This fixture does not duplicate its bank/count/hash
or absent/failed/forged gatePass suite. Merged #5885 holds the separate 98-host
preparation cohort; #5889 covers gas fixtures, and B196/#5890 covers final
revision holds. Merged #5882 and city-build-infra #669 retain the disabled cron
handoff. Those remain the authoritative lanes, with no cron enable here.

The supplied city-build-infra #662/#665/#669/#677/#679/#680/#681/#683,
ironclad-infra #5840/#5842/#5845/#5878/#5879/#5880/#5882–#5885/#5887/#5889/
#5891–#5895 and cbi-voltrade #165 were inspected as merged; their implementations
are not recreated. No review-gate, protected Engineer path, quote/contact file,
Shopify stock, analytics flag, Hetzner/Vault or service setting changes.
Shopify blog writer stays PARKED.

Factory MASTER-RULES.md and contamination-markers.json remain missing original
custodian inputs. READY=no; successful offline tests cannot satisfy those gates.
Bank custody/review, authentic destination/research/action admission, immutable
producer/publisher release, queue/checkpoint/restore custody, sole-writer/drain,
UNKNOWN/no-replay reconciliation and rollback remain blocked separately.

Next job: continue B71's existing first-batch review and same-owner second-batch
sequence. Once the reviewed complete bank lands, extend its existing tests there;
do not populate active city config from this fixture. Any later nonpublishing
preflight requires separate admission. All scheduling/publication stays disabled.
This PR must pass genuine exact-head reviews and applicable checks; no merge is
authorised by this delivery. Rollback is a reviewed removal of these three files;
there is no live state to restore.
