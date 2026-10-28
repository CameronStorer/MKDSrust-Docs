# Block 2: native platform layer

Owner direction (2026-10-15): complete block 2; block 3 (hand-port mod repo) is out of scope. Task T121, branch `block2`.
Block 1 (game code lifted from the user's ROM, no CPU interpreter) is done; block 2 replaces the *presentation* side of the
hardware model with native services. Game logic stays lifted ROM code: block 2 never replaces game behaviour with our own.

## What changes and what stays

| Area | Block 1 (today) | Block 2 |
|---|---|---|
| Window, input | `minifb` window, keyboard only, fixed 2x size | `winit` window (resizable, fullscreen, layout options), keyboard + gamepad (`gilrs`), same `controls.txt` |
| 3D engine | software rasterizer on the CPU at 256x192 | GPU renderer (`wgpu`: Direct3D 12 / Vulkan / Metal) at 1x-8x internal resolution |
| 2D engines | software, final pixels only | software decodes the layers at 256x192; the GPU composites them with the high-resolution 3D (priority, blending, windows, brightness) |
| Textures | decoded per frame | decoded once into a GPU cache keyed by content; optional PNG replacement pack |
| Audio | 16-channel mixer at 32,768 Hz, then resampled to the device | the same channel model mixed directly at the device rate with interpolation (one pass, less latency) |
| Fallback | | `--renderer software` keeps the block 1 path, and is the reference for every GPU test |

Audio note: the game's sound driver is ROM code (lifted ARM7) and keeps driving the sound channels; replacing it with our own
sequencer would change game behaviour. "Native audio" here means our mixer writes straight to the PC's audio device.

## Proof method
1. **Snapshot corpus** (local only, never committed: snapshots contain game data). `game --snapshots DIR --snapshot-every N`
   writes the complete renderer input (registers, palettes, OAM, VRAM, 3D polygon list) for scripted runs through menus,
   races on several courses, battle and a mission.
2. **Comparator**: `render_compare DIR` renders every snapshot with the software path and the GPU path at 1x and reports per
   frame the share of differing pixels and the largest channel difference. Acceptance thresholds per stage below.
3. **Live acceptance**: a windowed race through the results with the GPU path; `--stats` CPU/frame-time comparison with block 1.

## Stages
| Stage | Content | Done when |
|---|---|---|
| B2.0 | Snapshot file format + capture flag + comparator skeleton (software vs software) | corpus of >= 200 snapshots; comparator self-test is 0 differences |
| B2.1 | `winit` + `wgpu` host presenting the software frames; resizable/fullscreen/screen layouts; gamepad; touch mapping under scaling | same pixels as block 1 at 1x; input tests; race played windowed |
| B2.2 | GPU 3D renderer: clipping, perspective-correct attributes, all texture formats with the cache, wrap/flip, modulate/decal, depth (z/w, equal test), alpha blending, polygon ID, shadow volumes (stencil) | 1x vs software 3D layer: >= 99% identical pixels per frame, no frame below 97%, differences explained |
| B2.3 | GPU compositor: 2D layer records from the software decoder + high-resolution 3D; blending, windows, brightness, master brightness | 1x full screens vs software: >= 99.5% identical per frame |
| B2.4 | Resolution scaling 1x-8x, texture filtering option, settings file + menu entries | 4x race windowed at real time |
| B2.5 | Texture dump/replace (PNG by content hash) | a replaced texture shows in game |
| B2.6 | Device-rate audio mixing | no underruns in a race; output compared with the block 1 mixer |
| B2.7 | Acceptance, docs, Linux check, merge to `main` | fresh build, race to results on GPU path, docs updated |

## Work split
- agent-lift (Claude): B2.0, B2.1, B2.3, B2.4 integration, B2.6, B2.7.
- Codex (worktree `block2-gpu3d`): B2.2 as a standalone module with a fixed interface, verified by the comparator.

## Status (2026-10-15)
| Stage | Result |
|---|---|
| B2.0 | `MKSNAP01` snapshots (`--snapshots DIR --snapshot-every N`), `render_compare`; corpus of 549 frames (GP race, battle, menus + a second race); self-test 100% |
| B2.1 | winit 0.30 + wgpu 30 window on the main thread, game on its own thread (`HostLink`); resizable, F11 fullscreen, AZERTY-safe keys, gilrs controllers (`Pad` lines in `controls.txt`); `minifb` removed |
| B2.2 | GPU 3D renderer (Codex): compute tile rasterizer, content-hashed texture cache. Scale 1 vs software 3D layer: 99.998% / 99.994% / 99.999% average, worst frame 99.898%; GPU 0.08-0.22 ms/frame |
| B2.3 | `Engine2d::render_split` + `Split::pixel` (exact on all 549 frames and 60 random screens, mutation-checked) and the GPU compositor (exact with the software 3D layer on all 549 frames; full GPU screens 99.997-99.999%). In the game: 2D split on two threads (~5.5 ms), 3D + composition on the GPU, 60 fps presented at 100% speed |
| B2.4 | `settings.txt` (Renderer, Scale/Auto, Filter, Layout, Fullscreen, TexturePack, DumpTextures), Auto scale on resize, side-by-side layout, CPU fallback without compute shaders, "Display settings" in the `mkds.bat` menu |
| B2.5 | Texture dump/packs (Codex, finished by agent-lift): stable FNV ids, integer-factor replacements; 111 corpus textures; a 2x nearest pack renders identically to no pack on all 549 frames |
| B2.6 | Sound mixed at the device rate (Codex): exact timer stepping at any rate, passthrough output; windowed race at 48 kHz: 1 underrun (start-up) in 60 s |
| B2.7 | Fresh no-cache build (8 min): 11,297 functions, complete. Acceptance driver on it: race finished 1st (frame 11,331), 1.67 billion ARM9 instructions, 0 interpreted. `play.exe` with Scale 4, Smooth, SideBySide and a colour-inverted 111-texture pack: 4x, pack loaded, replaced textures visible, 100% speed, 60 fps, 48 kHz audio. Tests: builder 37, runtime 140, host 27, shell wrappers. Not tested: the GPU renderer and controllers on Linux/macOS; a physical controller |
