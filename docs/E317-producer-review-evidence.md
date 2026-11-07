# E317: pinned producer review evidence

This is review evidence, not an installed producer or a source fallback. Tests still require explicit CITY_PRODUCER_SOURCE in scratch storage.
No runtime consumer, scheduler, publication or cutover switch is added.

Repository: BIGroupLtd/ironclad-infra
Commit: 0bd7ae3754acbf056558c89b87240bedda98a7aa
Path: scripts/city_blog_draft.py
Git blob: fd4eaba56ff88378eeb0d2c3c706da6d1e761f54
SHA-256: 5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06

Immutable source (review through an authorized upstream connection):
https://github.com/BIGroupLtd/ironclad-infra/blob/0bd7ae3754acbf056558c89b87240bedda98a7aa/scripts/city_blog_draft.py

The source bytes were retrieved through the connector into scratch storage,
then authenticated against the independent pin before execution. They are not
redistributed in this repository. The test output below records the measured hash.

## E317 validation and limits (2026-11-07)

The Gate on PR #11 at cfa3151208a273ea285077b66952fda242d5d0d2
returned APPROVE/confidence 7 with zero findings. Its named uncertainty was
whether the tests exercised the unavailable pinned producer bytes. The immutable link, measured digest and actual output below provide source
custody and execution evidence without redistributing upstream source.
The additional tests cover missing exclusions before generation, refusing an
existing output directory without overwriting its contents, canonical www mapping
and its hash, the exact 2000-word floor, source identity, and nonzero
missing/unset/tampered-source failures with no skips or sentinel execution.

The import surface of the exact pinned source was inspected: top-level work defines
constants/functions/classes and imports standard-library modules; main is guarded.
The native writer is loaded only inside generate when no writer is supplied.
All successful test generation supplies mock writers; transports, socket connects,
process launches and native writer loading are poisoned by the boundary harness.
Research/action fields are only structurally checked by local_inputs; the tests
do not establish authentic admission, source truth, real native compliance or
release readiness. A mock compliance pass remains draft_only with absent gatePass
and missing full gate inputs. Real policy/custody holds remain unresolved.

Reproduce from the repository root with the explicit scratch source named in
the command below. There is no automatic source fallback. Hosted
pre-merge compilation alone is not evidence that these behavioral tests ran.

### PR #11 plus E317 additions

```text
Python 3.12.14
Source SHA-256: 5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06
Command: CITY_PRODUCER_SOURCE=/workspace/work/e317/source/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
Exit status: 0
test_bank_identity_cannot_bypass_unknown_or_excluded_destination (test_city_producer_bank_boundary.BankBoundary.test_bank_identity_cannot_bypass_unknown_or_excluded_destination) ... ok
test_fixture_is_held_and_has_only_synthetic_identities (test_city_producer_bank_boundary.BankBoundary.test_fixture_is_held_and_has_only_synthetic_identities) ... ok
test_model_bank_metadata_cannot_escape_draft_or_clear_native_holds (test_city_producer_bank_boundary.BankBoundary.test_model_bank_metadata_cannot_escape_draft_or_clear_native_holds) ... ok
test_planning_sources_do_not_replace_research_or_action_admission (test_city_producer_bank_boundary.BankBoundary.test_planning_sources_do_not_replace_research_or_action_admission) ... ok
test_raw_bank_row_and_forged_authority_are_not_generation_requests (test_city_producer_bank_boundary.BankBoundary.test_raw_bank_row_and_forged_authority_are_not_generation_requests) ... ok
test_tampered_source_refused_before_module_execution (test_city_producer_bank_boundary.BankBoundary.test_tampered_source_refused_before_module_execution) ... ok
test_canonical_mapping_and_length_boundary_remain_draft_only (test_city_producer_evidence.ProducerAssumptions.test_canonical_mapping_and_length_boundary_remain_draft_only) ... ok
test_exclusions_are_required_before_generation_or_output (test_city_producer_evidence.ProducerAssumptions.test_exclusions_are_required_before_generation_or_output) ... ok
test_existing_output_is_never_overwritten (test_city_producer_evidence.ProducerAssumptions.test_existing_output_is_never_overwritten) ... ok
test_explicit_source_matches_immutable_pin (test_city_producer_evidence.SourceEvidence.test_explicit_source_matches_immutable_pin) ... ok
test_source_configuration_errors_fail_without_skips (test_city_producer_evidence.SourceEvidence.test_source_configuration_errors_fail_without_skips) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.414s

OK
```

### Stacked draft PR #12 compatibility

The E317 additions touch only two new paths, neither modified by #12. The
original #11 files are unchanged, so #12's two-file patch retains its original
context. The following run overlays #12 at
562831ffb4f2b17bdf20b48d1f6ae458a801800c with both E317 additions; it
retains #12's complete-pin authentication improvements. No #12 rebase,
force-update, merge or draft-state change is needed.

```text
Python 3.12.14
Source SHA-256: 5caf2bc81292a1e2639ffa5a7e0bd92c978cf478d7e8eb946eb82737bc410c06
Command: CITY_PRODUCER_SOURCE=/workspace/work/e317/source/city_blog_draft.py python3 -I -B -m unittest discover -s tests -p 'test_city_producer*.py' -v
Exit status: 0
test_bank_identity_cannot_bypass_unknown_or_excluded_destination (test_city_producer_bank_boundary.BankBoundary.test_bank_identity_cannot_bypass_unknown_or_excluded_destination) ... ok
test_fixture_is_held_and_has_only_synthetic_identities (test_city_producer_bank_boundary.BankBoundary.test_fixture_is_held_and_has_only_synthetic_identities) ... ok
test_model_bank_metadata_cannot_escape_draft_or_clear_native_holds (test_city_producer_bank_boundary.BankBoundary.test_model_bank_metadata_cannot_escape_draft_or_clear_native_holds) ... ok
test_planning_sources_do_not_replace_research_or_action_admission (test_city_producer_bank_boundary.BankBoundary.test_planning_sources_do_not_replace_research_or_action_admission) ... ok
test_raw_bank_row_and_forged_authority_are_not_generation_requests (test_city_producer_bank_boundary.BankBoundary.test_raw_bank_row_and_forged_authority_are_not_generation_requests) ... ok
test_tampered_source_refused_before_module_execution (test_city_producer_bank_boundary.BankBoundary.test_tampered_source_refused_before_module_execution) ... ok
test_canonical_mapping_and_length_boundary_remain_draft_only (test_city_producer_evidence.ProducerAssumptions.test_canonical_mapping_and_length_boundary_remain_draft_only) ... ok
test_exclusions_are_required_before_generation_or_output (test_city_producer_evidence.ProducerAssumptions.test_exclusions_are_required_before_generation_or_output) ... ok
test_existing_output_is_never_overwritten (test_city_producer_evidence.ProducerAssumptions.test_existing_output_is_never_overwritten) ... ok
test_explicit_source_matches_immutable_pin (test_city_producer_evidence.SourceEvidence.test_explicit_source_matches_immutable_pin) ... ok
test_source_configuration_errors_fail_without_skips (test_city_producer_evidence.SourceEvidence.test_source_configuration_errors_fail_without_skips) ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.410s

OK
```

## Rollback and default-off state

E317 adds only this review document and tests/test_city_producer_evidence.py.
To withdraw E317, make a reviewed follow-up deleting exactly those two paths.
To withdraw all of #11, also remove docs/B211-city-producer-bank-boundary.md,
tests/test_city_producer_bank_boundary.py and
tests/fixtures/city-producer/bank-boundary.json. If #12 is later incorporated,
account for its changes to those original paths in the same reviewed withdrawal;
keep dependent test/document removals together. Do not remove an active branch
under a stacked PR as a rollback procedure. Neither withdrawal requires touching
ppc, workflows, remote producer files, credentials or live state.

Verify the withdrawal diff contains only the intended paths and that no remaining
test references the removed evidence/source fixture. Scratch artifacts use
TemporaryDirectory and are cleaned automatically, including on failed tests.
The explicitly supplied producer is scratch-only and can be removed afterwards.
There is no deployed state, queue, publication or data migration to restore.

Top-level fixture enabled=false, approved=false, status=HOLD and
not_runtime_queue=true remain unchanged. Nested forged true values are negative
inputs only. READY=no; scheduling, publication, generation cutover and all other
activation switches remain default-off. No secret values are included.
