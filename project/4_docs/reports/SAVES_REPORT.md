# Save persistence report

Implemented disk-backed cartridge saves in the shared `peripherals::Backup`, whose `data` vector is the 256 KiB flat flash image. Native PXI tag 11 services and the exact ARM7 SPI path both mutate this image and mark it dirty. The session polls pending writes with a one-second debounce; SPI write-disable and normal destruction flush pending changes. Writes sync a sibling temporary file and atomically replace the destination (Windows `MoveFileExW` with replacement/write-through; rename on other platforms). Failed writes retain the dirty state and report the error.

Player startup loads the image before guest execution. The default location is the platform directory selected by the existing controls/settings helper, followed by `MKDSrust/saves/<original ROM sha1>.sav`. The builder now records SHA-1 from the original ROM in the asset manifest, avoiding an incorrect hash of the sparse virtual cartridge. Windows independently verified the test ROM hash as `691e00d9a5dd80b04f80cc7559503e8b06848785`.

If the destination is missing, a flat `save.sav` beside the executable is imported and atomically persisted. Existing user saves take priority. Wrong-size files fail startup without overwriting the source. Images have no emulator-specific headers or footers; same-size raw emulator saves can be copied in directly.

`MKDS_SAVE=off` disables persistence, and `MKDS_SAVE=<path>` overrides the destination. Acceptance defaults to blank memory and only enables persistence with an explicit path. Recording/replay, including player input scripts/logs and PXI/sound recording, always remains blank and does not open save files, even with an override. The launcher settings page has **Open save folder**, and the README documents the location, imports, and override.

## Proof

Proof logs are retained in `saves_proof/` in this checkout.

All scratch artifacts below live under:

`C:/Users/cam/AppData/Local/Temp/claude/--192-168-1-11-Shared-Coding-My-NDS-GAME/d2702baf-4324-41bc-919f-6df583f54ea0/scratchpad`

| Check | Result / evidence |
| --- | --- |
| `2_native_game`: `CARGO_NET_OFFLINE=true CARGO_TARGET_DIR=../target_codex cargo test --release --locked --features gen` | PASS, exit 0. 219 tests total: 168 library tests plus enabled integration tests; two existing ignored tests. `saves_tests.log`. |
| New backup-service test | PASS. PXI write, drop/exit flush, reload, PXI read of identical bytes; exact SPI write-disable then atomically replaces the same image. |
| New save-image test | PASS. One-time import, existing-file priority, debounce, atomic replacement, wrong-size rejection without corruption. |
| `1_build_tool`: offline release build and tests | PASS, exit 0. SHA-1 known vectors also pass. `saves_builder.log`, `saves_builder_tests.log`. |
| Requested player bundle build | PASS. `saves_bundle/`, including `play.exe` and `acceptance.exe`; 11,297 generated functions, complete coverage. `saves_bundle.log`. |
| First race, `MKDS_SAVE=<scratch>/test.sav` | PASS, exit 0. Finished 1st at frame 11,260; stopped at 12,160. Created 262,144 bytes, 21,912 bytes differing from erased `0xff`. `saves_race_first.log`, `saves_race_first/`. |
| Second race, same save path | PASS, exit 0. Startup explicitly logged loading 262,144 bytes. Finished 1st at frame 11,414; stopped at 12,314. `saves_race_second.log`, `saves_race_second/`. |
| Default acceptance, `MKDS_SAVE` absent | PASS, exit 0. Finished 1st at frame 11,260; stopped at 12,160. All 40 emitted files match the existing `stall_fixed_native/` reference byte-for-byte, including inputs, telemetry, and PPM captures. The reference's extra manually converted PNG is not an acceptance output. `saves_race_default.log`, `saves_reference_compare.log`. |
| Recording/replay disk isolation | PASS. An intentionally invalid three-byte override file remained exactly `1,2,3`; neither path tried to load it. One-frame recording completed its recording then returned the expected race-not-finished result; one-frame replay exited 0. `saves_record.log`, `saves_replay.log`. |
| Default player save path | PASS, exit 0. With `APPDATA=<scratch>/saves_userdata`, headless player created a save in the product save directory (now `MKDSrust/saves/691e00d9a5dd80b04f80cc7559503e8b06848785.sav`), 262,144 bytes. `saves_default_path.log`. |
| Bundle import | PASS, exit 0. With isolated `APPDATA`, a temporary bundle `save.sav` was imported before guest execution and the destination hash matched the fixture. Temporary bundle fixture removed afterward. `saves_import_path.log`. |
| Explicit off and acceptance blank policy | PASS. With isolated `APPDATA` and a bundle import present, player `MKDS_SAVE=off` and default acceptance created no save directory. `saves_off.log`, `saves_blank_policy.log`. |

The first and second race save-image SHA-256 is `5c1e01f042c8e9ba8913b51bc8214f0a6ed5cdfcff080aa8e582156560e3d1e2`. The second race is allowed to differ because it loads initialized progress/options. The blank default race remains identical: 335,036,416 ARM9 instructions, 567,039 IRQs, 654,021,434 ARM7 plain-call instructions, and 455,018 fiber switches.

Race command: `saves_bundle/acceptance.exe <scratch>/rom.nds <scratch>/route.csv <scratch>/saves_race_{first|second|default} 15000`, with the save override set for the first two runs and absent for the third. No hardware overrides were needed: the default native-timing bundle supplies its normal runtime defaults.

## Exact mode

Built a second complete bundle at `saves_bundle_exact/` using the same builder command plus `--timing exact` (exit 0; `saves_bundle_exact.log`). Its acceptance executable used its default exact hardware, with no hardware overrides:

- First race with `MKDS_SAVE=<scratch>/saves_exact_test.sav`: exit 0, finished 1st at frame 11,462 and stopped at 12,362. Created a 262,144-byte flat image via the ARM7 SPI path. `saves_exact_first.log`, `saves_exact_first/`.
- Second race with the same path: exit 0, explicitly loaded the image, finished 1st at frame 11,640 and stopped at 12,540. `saves_exact_second.log`, `saves_exact_second/`.
- Blank default race with `MKDS_SAVE` absent: exit 0; all 40 emitted files match `stall_fixed_exact/` byte-for-byte. Stats match the established baseline: 1,707,950,080 ARM9 instructions, 581,521 IRQs, 923,441,005 ARM7 lifted cycles, zero interpreted instructions, and 401,332 fiber switches. `saves_exact_default.log`, `saves_exact_reference_compare.log`.
- The exact-timing player itself, with all four `MKDS_HW_*` switches set to `exact`, created `saves_player_exact_correct.sav` during a headless 200,000,000-instruction run and loaded it on a second startup. Both exits were 0. `saves_player_exact_correct.log`, `saves_player_exact_correct_reload.log`.

The exact race image SHA-256 is `2e857f4ac7b69d2d0d39b2e7d4959b8f1f8f4b19a925d2a1008f52be0059ff03`. Native and exact mode therefore both have end-to-end save/reload evidence, and both blank acceptance baselines remain unchanged.

## Additional check limitation

Launcher compilation could not run because the offline Cargo cache lacks the existing `eframe` dependency (`cargo check --release --manifest-path launcher/Cargo.toml`, exit 101; `saves_launcher.log`). The button uses the same folder helper as the player. This does not affect the passing required runtime proof or bundle build.

No commits or pushes were made.

Final `git diff --check` passes.
