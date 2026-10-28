# Defaults implementation report

Implemented the Block 5 default promotion. No commit or push was made.

## Changes

- Normal builder builds now generate budget-free ARM9 code. `--timing exact` overrides the environment; `MKDS_TIMING=exact` also selects the original instruction budgets. Interactive builds use the same builder default.
- Native build startup enables FS, ARM7, TIME and SND unless each switch was explicitly set. Both the bundle launcher and native player entry point default all four switches to native, including players built with exact instruction timing.
- Acceptance generation does not inject player hardware defaults. Its driver retains exact hardware defaults and defaults `MKDS_RTC` to `fixed`.
- The native ARM7 RTC reads `std::time::SystemTime`, converts the civil date, and uses the host OS timezone conversion (including daylight saving time) to return local BCD date/time. Windows and Unix implementations add no dependencies. `MKDS_RTC=fixed` returns the existing fixed peripheral clock. Unit tests and PXI replay routers use fixed time; recording environment paths default to fixed unless explicitly overridden. Civil-date tests cover the epoch, leap day, and midnight rollover.
- Launcher Advanced now offers one **Accuracy mode (exact hardware)** preference, off by default. It sets all four hardware switches to exact in the child process. Off preserves inherited overrides. Older native-toggle preferences are ignored during deserialization.
- Updated the MKDSrust README, launcher README, Block 5 proposal reproduction instructions and plan status. Acceptance proofs explicitly require `--timing exact --with-acceptance`.

## Restore exact behavior

Build with `--timing exact` (or `MKDS_TIMING=exact`), then set:

```text
MKDS_HW_FS=exact
MKDS_HW_ARM7=exact
MKDS_HW_TIME=exact
MKDS_HW_SND=exact
MKDS_RTC=fixed
```

The launcher Accuracy option sets the four hardware switches; use an exact-timing build for the original instruction timing as well. For acceptance, build with `--timing exact --with-acceptance`; the executable defaults to exact hardware and fixed RTC without extra overrides.

## Proof results

Final commands were run from their respective directories with the requested environment settings:

| Proof | Result | Log |
| --- | --- | --- |
| `2_native_game`: `CARGO_NET_OFFLINE=true CARGO_TARGET_DIR=../target_codex cargo test --release --locked --features gen` | PASS, exit 0 | `proof_native.log` |
| `1_build_tool`: `CARGO_NET_OFFLINE=true CARGO_TARGET_DIR=../target_codex_b cargo test --release` | PASS, exit 0 | `proof_builder.log` |
| `launcher`: `CARGO_NET_OFFLINE=true cargo build --release` | BLOCKED, exit 101 | `proof_launcher.log` |

The launcher fails before compilation because the offline Cargo cache has no `eframe` package. An online `cargo fetch` was attempted as a recovery step, but this environment cannot connect to index.crates.io:443 (see `fetch_launcher.log`). No dependency versions or lockfiles were changed to bypass this failure. The complete three-command proof therefore has **not** passed; launcher compilation still requires its existing dependencies to be made available. Launcher source was reviewed, including the four-switch child environment probe, but its build/tests could not be verified here.

`git diff --check` passes. Builder CLI help exposes `--timing`; its parser test accepts native/exact and rejects unsupported values. The native suite uses a library-only build because no ROM was supplied. No full ROM race or audio listening pass was performed; the proposal's existing listening and broader corpus limitations remain.
