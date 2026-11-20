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

## Continued offline boundary: POSIX output permissions

The first head's Pre-merge gates passed, but its genuine App4760566 suite
remained queued with zero check runs/findings on continuation. Under the user's
instruction to advance another unowned offline boundary, this same PR also
qualifies pinned-producer output modes. No second PR or runtime implementation.

Fresh open city-content PR/issue inspection returned only #14 and this #15,
with no active issue claims. Targeted all-state/open org searches for Blog
umask, output permissions and permission parity found no matching City draft
qualification. Reservation/concurrency was considered and excluded after reading
the actual ironclad #6022 patch and inventory: that PR already owns it. #6044
owns published-HTML receiver containment. #5935 owns SEO worker identity, while
#5673's source/core inventory and existing draft tests were inspected; neither
owns this pinned draft permission matrix. All those paths remain unchanged.
These are bounded GitHub claim checks, not external-registry clearance.

The synthetic saved fixture `tests/fixtures/city-producer/output-permissions.json`
is HOLD, enabled=false, approved=false and not a runtime queue. Four additional
tests execute as an ordinary POSIX user (UID 1000 in this run):

- Six umasks (000/002/007/022/027/077) all reserve a 0700 directory BEFORE
  the mock callback. Both regular files retain native 0666-and-umask modes,
  effective-user ownership and one link; their bytes/hash/result remain bound.
- Three owner-restricting masks remove directory write or search permission.
  The real filesystem refuses the first artifact after synthetic callbacks;
  the producer does not silently chmod or emit a receipt. Tests restore mode
  only after original-mode/refusal assertions, for evidence inspection/cleanup.
- Missing, regular-file and unwritable parents refuse actual mkdir before
  writer dispatch. Native loading stays prohibited, no output is created and
  pre-existing parent/sibling evidence remains exact.
- Actual CLI permission denial returns 1, no stdout and only PermissionError
  on stderr, without exposing the synthetic private path or loading a writer.

All 20 producer tests PASS / zero skips (12 original, eight in this PR).
A scratch-memory mutation widening reservation mode from 0700 to 0777 yields
five expected assertion failures and zero errors; no mutant is retained.
Root/non-POSIX execution fails qualification explicitly rather than skipping
permission checks. Umask changes are bounded by try/finally and restored.
No chmod/chown/identity change occurs outside temporary synthetic paths.

This proves ordinary POSIX DAC behavior in the tested filesystem, not ACLs,
alternate identities, group custody, hostile ancestors, symlink containment,
mount semantics, concurrent umask changes, installed volume compatibility or
durability. With a permissive umask, files themselves can have group/world bits;
privacy here comes from the new 0700 parent. Do not serve/chmod/move that
directory or infer publish permission. Source/defaults and all original holds
remain unchanged. Rollback removes this PR's inert tests/fixture/document only.

## Continued offline boundary: output locale parity

Current-head Pre-merge gates passed, while the genuine Gate again remained
queued without a verdict or findings. Following the user's next-boundary
instruction, the same PR adds an isolated-interpreter output-locale regression.
Fresh city-content open PR/issue claims still returned only #14 and this PR,
with no active issue claims. Targeted all-state/open Blog locale, PYTHONUTF8,
ASCII-locale and output-locale searches returned no matching City scope. Existing
#6042 owns reply scalar/encoding validity in one interpreter; #6054 saved HTML
packet encoding, #6048 SEO export encoding and #6022 reservation scopes stay
untouched. No existing producer/runtime/consumer implementation is duplicated.

One regression method starts three bounded (30-second) isolated Python children:
LC_ALL=C with UTF-8 mode explicitly OFF and ON, and C.utf8 with UTF-8 mode OFF.
Each asserts its actual preferred encoding and mode; unavailable locale/mode
fails instead of silently qualifying the host default. Inherited environment
is replaced by explicit locale, source path and temporary scratch settings.
Each child authenticates the original source pin before execution and reuses
the existing HTTP/process/native-loader poison guards; DNS/connect guards are
added. Only the parent launches the fixed local Python probes.

The native generate and CLI both run with synthetic callbacks and a fixed mock
UUID, preserving two frozen fixture byte strings. The config is UTF-8 with
visible Unicode/decomposed accents/emoji/control escapes; the result is ASCII
JSON with escaped Unicode native holds. Source action/topic, config SHA256,
map digest, all receipt fields, gatePass=absent, draft_only and full missing-gate
holds match the frozen expected pair. CLI and direct output are byte-identical
across all three interpreter modes, with no stdout/stderr and two mock calls
per child. A second output leaves the first pair's bytes/inode/mode/size/mtime
unchanged. Fixture files contain synthetic placeholders, not generated content.

All 21 producer tests PASS, zero skips. Two scratch-memory negative controls
make this regression fail with assertion failures and zero execution errors:
locale-dependent artifact encoding, and disabling ASCII escaping in the result
serializer. No mutant is retained. Original pinned bytes pass again.

This deliberately uses ASCII-escaped request JSON and ASCII map/exclusions:
native input read_text remains locale-dependent. No raw non-ASCII input-file,
non-ASCII filesystem-path, arbitrary OS/locale, physical durability, current
upstream, installed runtime or editorial/publishing compatibility is claimed.
The frozen result's UUID is a test double, not a live attempt identity. Separate
temporary mock invocations do not authorize a live/UNKNOWN attempt replay.
No schema, output contract, source producer, workflow, provider, flag or runtime
wiring changes; default OFF and all original holds remain. Rollback also removes
this inert test and its two expected-output fixtures through normal review.

The next same-PR implementation adds the default-OFF read-only
[original-map binding qualifier](MIG-0819-map-binding.md). It preserves all above
scopes and native source bytes, and addresses only independently retained
canonical-map snapshot/receipt consistency.
