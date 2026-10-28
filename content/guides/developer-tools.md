# Developer tools
<!-- Researchers -->

The docs repository now holds the developer and research material moved out of the main MKDSrust game checkout. Browse [project/ and its usage guide](https://github.com/CameronStorer/MKDSrust-Docs/tree/main/project) for build and verification commands, tool prerequisites and folder origins. The [migration inventory](https://github.com/CameronStorer/MKDSrust-Docs/blob/main/project/REMOVED_FROM_MAIN.txt) lists every original path.

## What is available

- [Plans, evidence, inputs and masks](https://github.com/CameronStorer/MKDSrust-Docs/tree/main/project/4_docs): dated Block 2–5 research, open-loop mission/menu/battle inputs, seed-pinning proofs and region comparison helpers.
- [Native diagnostics](https://github.com/CameronStorer/MKDSrust-Docs/tree/main/project/2_native_game/native/diagnostics): audio comparison, census and sound scheduling utilities.
- [Examples](https://github.com/CameronStorer/MKDSrust-Docs/tree/main/project/2_native_game/examples): historical boot and lifting probes.
- [Dictionary scripts](https://github.com/CameronStorer/MKDSrust-Docs/tree/main/project/dictionary): naming, field/layout inference, exports and evidence analysis. The maintained CSVs remain in the main game checkout.
- [Launcher reference](../sources/launcher.md), plus branding generation and shell-wrapper checks in `project/`.

## Use with a game checkout

Follow the project folder's README to build acceptance with `--timing exact --with-acceptance`, run a fixed reference race, and replay these inputs with `frame_compare`. It also explains the historical `race_diff` prerequisite, matching masks on both recordings, fixed RTC, seed logging and replay, loading-lead measurement and per-mode limits. Keep ROMs and game-derived outputs private and outside this repository.

Read [Verify a change](verify.md) for what each proof establishes and [Project status](status.md) for current results. Historical helpers may require their original revision or additional research tables; consult their usage before running them.
