# MIG-0819: offline final-gate ordering parity

This adds four explicitly invoked tests to the existing City producer harness.
Default OFF/uninvoked; no runtime, source producer, workflow or flag changes.
The tests run the complete independently hash-authenticated `generate`, cleaner
and CLI from the existing pinned producer. Generation, final policy and word
count are explicit in-memory doubles. No content is generated or published.

```sh
CITY_PRODUCER_SOURCE=/path/to/pinned/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
```

Source custody is unchanged: ironclad-infra
`0bd7ae3754acbf056558c89b87240bedda98a7aa`, `scripts/city_blog_draft.py`,
SHA256 `5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06`.
Supply those bytes explicitly in scratch storage; they are not vendored here.
Missing or altered source fails before execution, with no skip fallback.

## Scope and evidence

On 10 November 2026 Richard's verified richardwaters-ui GitHub connection was
used to inspect open Blog PR scopes and active issue claims. city-content main
was `fc27ea98f51eecfb46884b207b56866d2d66a765`. Its only open PR, #14,
owns interrupted transfer/receipt custody; its actual patch and three-file
inventory were read and remain untouched. No open city-content issue claim or
exact MIG-0819 result was returned. This is bounded connected-GitHub inspection,
not exhaustive external claim-registry clearance.

Adjacent ironclad scopes #6042 (reply encoding), #6013 (scheduler malformed-reply
isolation) and #5581 (draft producer implementation) were inspected, including
changed-file lists and #6042/#6013 patches. This claims only final callback
ordering and failure parity in the pre-existing pinned city-content harness;
no dependency on or duplication of those unmerged implementations.

- An independent expected object requires editorial cleanup before BOTH final
  callbacks, including fields later dropped by the output projection. URL and
  identity values remain exact. Saved output binds request action/topic and its
  SHA256; native holds plus below-floor hold remain ordered and draft-only.
- Five hidden-character source URL cases refuse before either final callback
  or artifact write. Reserved failed directories remain empty.
- Six final/count callback exceptions propagate, restore the transport, emit no
  artifact and preserve accepted sibling bytes, inode, mode, size and ns-mtime.
  Reuse of the failed directory refuses before another mock writer invocation.
- Actual CLI exceptions at either callback return 1, empty stdout and only the
  exception class on stderr. A later independent sibling remains draft-only.

Validation: all 16 tests PASS, zero skips (12 existing, four new). A scratch-only
negative control replacing cleanup with identity yields one expected assertion
failure and zero execution errors. No mutant is retained. Existing HTTP/process
poison guards are reused, DNS/connection guards added and inherited environment
cleared. All artifacts are synthetic and temporary. No real native policy,
word count, bridge, scheduler, importer or live consumer is qualified. This
does not establish content approval, current upstream parity, durable storage,
multi-file atomicity, deployed readiness or migration completion.

Keep PR open/unmerged, auto-merge OFF; require the genuine exact-head AI Review
Gate APPROVE >=8 with zero blockers and every applicable check. These tests do
not replace the review gate. Rollback is reviewed removal of these two inert
files, preserving all prior evidence and original-owner holds.

No merge, deployment, live flip, paid service, SSH/restart, GA4_FEED_ENABLED,
stock/Ads changes, Kubernetes, content generation/publication or Commerce82 replay.
