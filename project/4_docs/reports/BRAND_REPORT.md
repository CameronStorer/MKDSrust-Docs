# Branding report

Implemented the final owner-selected MKDSrust branding.

- `assets/branding/icon.png`: transparent RGBA 256 x 256, scaled from the owner's `C:/Users/cam/dev/logos/final/icon_236.png` with Pillow LANCZOS. Also generated transparent 64, 32 and 16 px PNGs and `icon.ico` containing 16/32/48/256 px images.
- `logo.svg` retains option 3 Apex Trace's 640 x 160 layout and exact italic system-font wordmark styling, with the owner's wheel embedded as PNG at the original icon position. `logo_light.svg` uses charcoal and rust orange; `logo_dark.svg` uses an ivory wordmark with a charcoal outline and rust orange. Both SVGs are self-contained.
- `logo.png` and `logo_dark.png` are transparent 1200 x 300 renders. The dark-background raster is embedded in the launcher so its wordmark appearance does not depend on runtime fonts or SVG support.
- Launcher: embedded PNG window icon through `ViewportBuilder::with_icon`, wheel in the sidebar header, and full logo in the home header. Branding textures load once at startup.
- Native game: embedded PNG decoded with the existing `png` dependency and supplied to winit's window attributes. No runtime asset files are required.
- README: centred logo at the top. Updated `.gitignore` to include `assets/branding/` while keeping other asset folders ignored.
- Neither launcher nor native executable crate has a Cargo build script or Windows resource setup. Executable-resource ICO embedding was skipped as instructed. `1_build_tool/src/build.rs` is an application module, not a Cargo resource build script. No dependencies were added.
- `assets/branding/generate.py` records asset generation using Pillow 11.1.0 and Inkscape; it references the supplied original artwork outside this checkout.

## Verification

All requested offline release builds passed with Cargo exit code 0:

```powershell
cd launcher
$env:CARGO_NET_OFFLINE='true'; cargo build --release

cd ../1_build_tool
$env:CARGO_NET_OFFLINE='true'; $env:CARGO_TARGET_DIR='../target_codex_b'; cargo build --release

cd ..
$env:CARGO_NET_OFFLINE='true'; $env:CARGO_TARGET_DIR='target_codex'; cargo build --release --manifest-path 2_native_game/native/Cargo.toml
```

Logs: `brand_launcher.log`, `brand_builder.log`, `brand_native.log`.
The environment emits a Cargo home canonicalization warning; the native build also reports the expected no-ROM/library-only warning. Neither prevents compilation.

The launcher's existing `--smoke-test` completed with process exit code 0 (waited for process completion). Inspected both rendered logo PNGs, verified PNG dimensions and transparency, and confirmed all four ICO sizes with Pillow. `git diff --check` passed. A live game session was not run; the native window integration was verified by compilation.

No commit or push was made.
