# Constant tail jumps through veneers

## Implementation

`src/raise_emit.rs` now proves block-local constant jump targets in native no-spill mode. It follows constants through registers and temporaries, applies BX interworking alignment, and leaves arbitrary memory reads, conditional overwrites, calls, helpers and block boundaries conservative. Literal-pool constants are supplied by the existing lowering pass.

External constant tail jumps contribute dependencies to the existing segment-aware whole-program closed-function fixed point in `mkds_gen`. Veneers remain real functions: their register writes are retained, and a chain becomes closed only when every target is available and closed. Tail dependencies also participate in register liveness, result propagation and preservation checks. The current link register must still represent the entry return address.

A direct variant invokes the target's direct variant with its register arguments, assigns its results and returns its exit PC without spilling or setting a new link register. Ordinary T1 entries retain the dispatcher path. Original computed jump expressions are retained for fallback; unknown targets and unavailable overlays do not become direct calls. Exact timing and `MKDS_SPILL=keep` do not run the constant-tail pass.

Regression tests in `t1_differential.rs` execute an r3-to-r12 veneer chain ending in a Thumb leaf over 200 register seeds, comparing its direct variant against sequential T0 execution. Additional assertions cover conditional overwrite invalidation, Thumb target identity, unavailable overlay targets and original jump fallback.

The 800-function proof also exposed a pre-existing test-harness mismatch: T0's `Ram::call` randomly clobbered registers even when T1 executed a real sampled closed leaf directly. The no-spill harness now routes those same leaf targets to their actual T0 implementations, forwarding all other calls to the adversarial stub. This preserves direct-call coverage and makes the two sides execute the same program. The synthetic no-spill case includes an ordinary caller of a closed leaf to guard this behavior. The original mismatch occurred in function `0x02074E6C`, calling sampled leaf `0x0214848C`.

Generated differential cases are separate non-inlined check functions instead of one enormous `main`, avoiding excessive optimizer work at sample size 800. All samples, seeds, assertions and optimization settings are retained.

## Measurements

Baseline: repository HEAD `4ec5d1e`, including Block 5.5 commit `71b614e`. The requested `HEAD~1` stat was also inspected; on this merge history it identifies the earlier documentation commit.

Both generations used the supplied ROM, `4_docs/FUNCTION_BOUNDARIES.csv`, no name tables, `--no-game --allow-incomplete`, and `--timing native`. Both lifted all 11,297 metadata entries, with zero undecoded sites.

| Measurement | Before | After | Change |
| --- | ---: | ---: | ---: |
| Closed functions | 3,284 | 3,474 | +190 |
| `spill!(` sites in all generated `.rs` files | 61,517 | 60,577 | -940 |
| Call/tail sites reaching direct functions | 15,220 | 15,757 | +537 |
| Signature convergence rounds | 5 | 5 | 0 |

The spill count counts textual macro invocations, including invocations in generated macro bodies; it is not a dynamic execution count. The closed count comes from the generator's final fixed point, including segment rows. Recognizing a constant tail does not necessarily close its caller: many targets still reach polls, helpers or other non-closed functions.

Artifacts and logs are under `target_codex/`: `veneer_before_native/`, `veneer_after_native/`, `veneer_before_native.log`, and `veneer_after_native.log`.

## Verification

- `CARGO_NET_OFFLINE=true CARGO_TARGET_DIR=../target_codex cargo test --release --locked --features gen`: PASS on final source, 216 tests passed and two existing tests ignored. ROM-dependent tests skip when `MKDS_ROM` is unset. Log: `target_codex/veneer_tests_final.log`.
- `MKDS_ROM=C:/Users/cam/AppData/Local/Temp/claude/--192-168-1-11-Shared-Coding-My-NDS-GAME/d2702baf-4324-41bc-919f-6df583f54ea0/scratchpad/rom.nds MKDS_T1_SAMPLE=800 CARGO_NET_OFFLINE=true CARGO_TARGET_DIR=../target_codex cargo test --release --locked --features gen --test t1_differential`: PASS on final source, all 11 tests passed, including both no-spill tests, in 863.95 seconds. Log: `target_codex/veneer_rom_proof.log`.
- Generated native `direct` crate: `cargo check --offline --release --manifest-path target_codex/veneer_after_native/Cargo.toml -p direct` passes.
- `git diff --check` passes.

### Default-output comparison and provenance exception

Before editing, all 109 files from a default-timing generation were SHA-256 hashed. The final generator was run into the same output directory with the same arguments. Every file is byte-identical except `lifted/src/lib.rs` and `generation.json`. Those two differences are exclusively the generator-source fingerprint (`GENERATOR_ID` / `generator_id`), which necessarily changes because the existing `generator_id()` hashes `raise_emit.rs` itself.

Normalizing only that fingerprint yields zero differences across all 109 files. The actual translated functions, wrappers, tables, layout and manifests are unchanged. Evidence: `target_codex/veneer_before_exact.hashes`, `veneer_exact_raw_diff.txt`, and `veneer_exact_comparison.txt`.

The literal requirement that *every output byte*, including source provenance, stay identical is therefore not met. The source fingerprint was deliberately not forged or frozen to hide the implementation change. No generator provenance policy was changed.

## Limits and risks

- The proof is deliberately local to a basic block. Constants requiring cross-block reasoning, unknown register values, mutable memory or ambiguous conditions retain fallback.
- Existing overlay-residency selection, native/hook exclusions, poll exclusions and final signature checks remain authoritative.
- These are logical tail calls implemented with ordinary Rust calls followed by returns; machine-level tail-call optimization is not guaranteed.
- Differential testing samples the supplied ROM; it is not a whole-game behavioral proof.

No commits or pushes were made. This report is placed under `2_native_game/tests/` to obey the task's edit-location restriction.
