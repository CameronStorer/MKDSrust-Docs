# Default-build stall report

## Cause

Commit `cd9763c` kept the builder's native code generation but removed `with_timing(...)` from the generated acceptance entry point. The executable consequently ran budget-free ARM9 code without setting `MKDS_TIMING=native` before the runtime initialized its cached timing switches. The four hardware switches alone do not enable budget-free runtime timing.

This mismatch left `Machine::budget_free` false, native calls charging instruction budgets, and Session applying exact-mode progress checks to generated code that does not charge instruction budgets. The first overlay-related slice with zero charged instructions triggered the frame-516 error. The overlay residency recheck itself was present and working; it did not need changing.

## Fix

Restored `with_timing(...)` around the generated acceptance main in `1_build_tool/src/build.rs`. Like the player executable, acceptance built with native timing now sets `MKDS_TIMING=native` before constructing runtime state and supplies native hardware defaults for unset switches. Explicit hardware overrides remain supported. The wrapper is conditional on native generation, so `--timing exact` retains its original acceptance startup, exact hardware defaults, and fixed RTC. No runtime, emitter, residency, or exact-timing code changed.

Updated README and Block 5 documentation to distinguish native acceptance from the exact oracle (`--timing exact --with-acceptance`). No commit or push was made.

## Race verification

All artifacts below are under `C:/Users/cam/AppData/Local/Temp/claude/--192-168-1-11-Shared-Coding-My-NDS-GAME/d2702baf-4324-41bc-919f-6df583f54ea0/scratchpad`.

- Original playtest acceptance, four native hardware switches, no `MKDS_TIMING`: reproduced the exact reported stall at frame **516**, PC **0x021987cf**, thread **0x0217000c** (`stall_baseline.log`). One overlay load and one residency recheck were reported.
- Same original executable with `MKDS_TIMING=native`: finished **1st at frame 11,260**, stopped after results at **12,160** (`stall_env_native.log`, `stall_env_native/`). This isolates the startup switch mismatch without changing code.
- Rebuilt default bundle, four native hardware switches, `MKDS_TIMING` absent externally: finished **1st at frame 11,260**, stopped after results at **12,160** (`stall_fixed_native.log`, `stall_fixed_native/`). Visually inspected the results capture: Mario is 1st. All original output files (CSVs and captures) match the diagnostic run byte for byte.
- Rebuilt `--timing exact --with-acceptance` bundle, no timing/hardware/RTC overrides: finished **1st at frame 11,462**, stopped after results at **12,362**, exit **0** (`stall_fixed_exact.log`, `stall_fixed_exact/`). Compared SHA-256 hashes and file lists against the established merged-tree exact reference `b5-finish/M_ex/`: **all 40 output files identical**, including inputs, telemetry, and captures. Stats also match `b5-finish/M_ex.log`: **1,707,950,080 ARM9 instructions**, **581,521 IRQs**, **923,441,005 ARM7 lifted cycles**, zero interpreted instructions, **401,332 fiber thread switches**. The exact build is unchanged for the proof race.

The rebuilt native run reported **0 interpreted ARM9 instructions**, **567,039 IRQs**, **0 ARM7 CPU cycles**, **654,021,434 ARM7 plain-call instructions**, **96 busy-wait time steps**, **15 guard steps**, and **one overlay residency recheck**. Frame-event timing was on. The race command was `codex_bundle/acceptance.exe rom.nds route.csv stall_fixed_native 15000` with `MKDS_HW_FS`, `MKDS_HW_ARM7`, `MKDS_HW_TIME`, and `MKDS_HW_SND` each set to `native`.

## Build and checks

- Rebuilt the release builder offline (`stall_builder.log`).
- Rebuilt the complete default bundle with `--with-acceptance`, using only `cache_codex`, seeded from `cache_b5-native-t` (`stall_bundle.log`). Build status: complete, **11,297 generated functions**. PowerShell's cache copy encountered long-path errors on some cached dependency files; Cargo successfully rebuilt the required artifacts.
- Builder release tests: **20 passed**, zero failures (`stall_builder_tests.log`).
- Rebuilt the complete exact bundle with the same isolated cache (`stall_exact_bundle.log`); inspected generated acceptance startup to confirm that no native timing or hardware defaults are injected.
- `git diff --check` passes.
