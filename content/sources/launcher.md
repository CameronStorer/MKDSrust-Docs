# MKDSrust launcher

A graphical Windows launcher built with Rust, eframe/egui and the shared builder library. All interface text, shapes and styling are original. WheelWizard was consulted only for broad workflow ideas (setup, sidebar navigation, a prominent launch action and progress feedback); none of its implementation or assets is included.

## Build and run

Install the Rust MSVC toolchain and Visual Studio C++ build tools. From this directory:

```powershell
cargo build --release
.\target\release\mkds_launcher.exe
```

Keep the source checkout available for building games. The launcher searches upward from the working directory and executable, then checks its original checkout location. Internet access is needed on the first Cargo build. Native game compilation can take substantial time and memory.

Choose your own supported `.nds` ROM on Home. Inspection shows its header title, region, revision and supported-dump result. Unsupported dumps cannot be built. Choose an output directory and Build game. Compilation runs in the background; its log streams below the setup controls and is also available on Advanced. Play verifies and launches the bundle through the builder. Keep the window open while building or playing.

Rebuild preserves the existing bundle: a nonempty destination produces a new sibling directory, which becomes the active output only after success. Old builds can be managed manually. Open game folder opens the active output in Explorer. Refresh status rechecks the selected ROM and source timestamps. Outdated means the recorded source timestamp or selected ROM hash differs; it is a local heuristic, not an online update check. ROM changes are also checked by the builder before compilation.

Settings and Controls have explicit Save buttons and use the same `settings.txt` and `controls.txt` as the terminal launcher/game. Click a keyboard binding and press a key to replace it. Edit menus support multiple keys, clearing bindings, and keys egui cannot distinguish (modifier sides and numpad keys). Controller menus support every shared pad binding, including stick directions; physical controller capture is not provided. Display settings take effect on the next game launch.

Advanced offers Accuracy mode (exact hardware), off by default. It sets MKDS_HW_FS, MKDS_HW_ARM7, MKDS_HW_TIME and MKDS_HW_SND to exact in the child process. With the option off, inherited environment overrides are preserved and player defaults are native. For the original instruction timing, build with --timing exact as well.

## Local data and checks

On Windows, preferences and logs are under `%APPDATA%\MKDS Native Builder`: `launcher.json` stores ROM/output paths, accuracy preference and a source timestamp; `launcher-build.log` stores the last completed build attempt. These stay outside the repository. The header title is only displayed in memory. No ROM or extracted assets are distributed with the launcher.

```powershell
cargo test --release
.\target\release\mkds_launcher.exe --smoke-test
```

Smoke mode renders all four native pages and closes automatically. It does not choose a ROM or build a game. Tests exercise page rendering, key capture/shared persistence, default toggles and verified child launching with environment overrides. The builder's existing tests should also pass (`cd ..\1_build_tool; cargo test`).

This checkout uses `build::recompile`, the current native build pipeline. The older `build::build` requires the absent legacy reference-port directory. Native generation remains strict: incomplete generation is reported as a build failure, not silently accepted.
