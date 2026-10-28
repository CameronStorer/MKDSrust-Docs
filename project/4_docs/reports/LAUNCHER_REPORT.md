# Launcher completion report

Implemented a standalone Rust eframe/egui binary crate in `launcher/`, producing `launcher/target/release/mkds_launcher.exe`.

## Implemented

- Original dark interface with sidebar navigation and a prominent Play button; no copied WheelWizard code, wording, images, icons or other assets. Consulted its README and view organization only for broad workflow ideas.
- First-run ROM selection via rfd; asynchronous inspection displays header title, region, revision, compatibility and supported-dump status. ROM/output paths persist in user preferences.
- Strict native compilation on a worker thread, streamed scrolling logs, activity spinner, actionable errors and persistent last-build log. Closing is deferred during work or gameplay. Rebuild preserves previous output and selects the new output after success.
- Home shows built/not-built/outdated status, Play, Rebuild, Refresh status and Open game folder. Outdated uses the selected ROM hash and local source timestamp at startup/refresh; it is a heuristic, not an online update service.
- Every shared Settings field is editable, including renderer, Auto/1-8 scale, filtering, layout, fullscreen, replacement-texture folder and texture-dump folder. Existing load/save functions retain interoperability.
- All keyboard and pad bindings are editable, with keyboard capture, multi-binding menus, clearing, defaults and explicit saving through Controls. Modifier-side/numpad choices and controller bindings use menus rather than physical capture.
- Experimental filesystem/ARM7/timing modes default off, persist locally and apply only to the child game's environment. Off removes inherited native overrides.
- A launcher copied into a built bundle recognizes the manifest beside itself and opens that bundle. README covers prerequisites, build/run, persistence, rebuild behavior and checks.

## Builder changes (small and additive)

`1_build_tool/src/lib.rs` exports the existing build module and adds a self-crate alias so that module compiles unchanged as a library module. `build.rs` adds `launch_with_env`; the existing `launch` delegates with no overrides, retaining terminal behavior and verification. No game files were modified.

The task described `build::build` as the native pipeline. In this checkout that function targets the missing legacy `3_hand_port` folder. The GUI uses the existing `build::recompile` pipeline for the current `2_native_game` checkout. Strict supported-ROM and complete-generation requirements remain enabled; no diagnostic bypasses were introduced.

## Verification

- `cd launcher; cargo build --release`: passed, no warnings from our code.
- `cd launcher; cargo test --release`: 5 tests passed. Includes all four egui pages rendering, press-key capture and shared persistence, key mapping, experimental defaults, and an actual verified child launch that checks environment overrides/removal without changing the parent environment.
- `cd 1_build_tool; cargo test --offline`: 53 tests passed (34 library, 19 binary), plus doc tests. ROM-optional tests retain their existing skip behavior when a ROM is absent.
- Release executable `--smoke-test`: passed, exit 0. Opens a native eframe window, renders all four pages and closes automatically. Used an isolated APPDATA profile under ignored `launcher/target`.
- `git diff --check`: passed.

The sandbox's Windows Schannel could not obtain TLS credentials for Cargo. Dependencies were fetched from official crates.io endpoints through a temporary localhost Node TLS relay, then cached under ignored `launcher/target/cargo-home`. The final ordinary build/test commands used CARGO_HOME pointing there and CARGO_NET_OFFLINE=true, without a registry replacement. No relay/configuration is required by or committed with the launcher. Rustup emits an environmental home canonicalization message; there are no Rust code warnings.

## Remaining verification limits

No supported user ROM was supplied, so an end-to-end real ROM build, real gameplay and physical controller behavior have not been exercised here. Native generation failures will appear in the GUI log. The desktop automation helper reported `native pipe is unavailable`, preventing screenshot inspection and file-dialog interaction testing; native rendering and headless page/input checks passed. No ROM bytes, extracted files, game imagery, sounds or game asset names were added to the repository.

## Commit status

The requested commit could not be created: `git add` failed to create `C:/Users/cam/dev/mkds-native-builder/.git/worktrees/launcher/index.lock` with Permission denied. The shared Git metadata is outside this sandbox's writable roots. Changes remain in the `launcher` branch worktree, unstaged; nothing was pushed. The pre-existing untracked LAUNCHER_TASK.md was left untouched.

When Git metadata is writable, stage only `launcher/`, the two builder source files and this report, then commit with the required trailers:

```
Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DpzvJhtEQtjeuHM8NFtVfX
```
