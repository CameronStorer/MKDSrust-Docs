# GPU 2D (block 3, lane A)

`native/src/gpu/two_d.rs` uploads raw registers, standard palettes, OAM and the nine VRAM banks. A compute pass resolves the bank mappings, including overlapping banks (bytewise OR) and extended palettes. A second pass builds the compositor's base/other/info buffers using the integer rules in `Engine2d::render_split`. The existing compositor applies the 3D pixel and master brightness at the selected output scale.

The game thread still takes an owned `RenderSnapshot`. The render worker transfers that snapshot without building CPU splits. Software rendering and the no-compute fallback use the original CPU renderer. No changes were made to `gfx2d.rs`.

Uploads compare 256-byte pages against the last **submitted** snapshot, coalesce adjacent dirty pages, and upload only those ranges. Skipped frames therefore cannot lose updates. Bank mapping descriptors are small (144 bytes) and rebuilt each frame; remapping and disabling banks also clears obsolete mapped memory on the GPU. Resizing creates a fresh uploader and sends its initial full state.

Exactness is against the existing implementation, including its limitations: it ignores mosaic, returns white for display-off/forced-blank, and black for the unsupported VRAM/main-memory display modes. This change does not add hardware behavior absent from the CPU reference.

## Reproduce

```powershell
cargo build --release --manifest-path 2_native_game/native/Cargo.toml --bin render_compare
$corpus = 'C:/Users/camer/Desktop/mkds-native-builder/builds/corpus'
foreach ($folder in 'snap_gp','snap_battle','snap_user') {
    & 2_native_game/native/target/release/render_compare.exe "$corpus/$folder" --gpu-2d
    if ($LASTEXITCODE -ne 0) { throw "Comparison failed: $folder" }
}
cargo test --manifest-path 1_build_tool/Cargo.toml
cargo test --manifest-path 2_native_game/Cargo.toml
cargo test --manifest-path 2_native_game/native/Cargo.toml
```

`--gpu-2d` always requires 100% equality. It compares every split record (including records hidden by the current 3D layer), split composition with the software 3D layer, and the original software screens. It does not use the approximate GPU 3D renderer in this check. It prints CPU elapsed time around parallel reference splits and around raw upload/compute/compositor submission, excluding readback and shader creation. These are elapsed costs of CPU work, not GPU timestamps or OS thread CPU counters.

The synthetic native test covers both engines, modes 0–5, affine references, randomized OAM and blending/windows/brightness, overlapping/disabled/remapped banks, extended palettes, mixed transparent/translucent/opaque 3D samples, repeated identical frames, and single-byte VRAM mutations. It checks all split records and verifies zero raw uploads for repeated frames and one 256-byte upload for a changed byte.

Use `play.exe --renderer gpu --scale 1 --stats` on a separately rebuilt game. The new `GPU 2D upload + compose submission CPU` line measures the window thread's CPU submission cost; `snapshot` continues to measure the game thread's raw snapshot copy. The worker's old 2D-A cost becomes zero. The upload count covers raw bytes; the small mapping and compositor uniforms are additional.

## Validation results

Pending final timing and mutation results.
