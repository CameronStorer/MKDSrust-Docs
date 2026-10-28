# Block 3: function dictionary (toward native code) + GPU 2D

Owner direction (2026-10-16): prioritise the big hitters, not the cheap wins.

**Block 3 builds on blocks 1 and 2:**
- **Block 1:** the game's code is translated from the user's ROM; no CPU interpreter runs.
- **Block 2:** native window, GPU 3D, compositor, controllers, settings and audio.

**Block 3 attacks the two ways the game still imitates the DS:**
1. **The function dictionary.** For every game function it records the name, arguments, return value, types and meaning. Readable native Rust versions of functions are written from it, and each one is checked automatically against the exact translation before it is switched on. This is the foundation for:
   - truly native code;
   - readable source generated from the player's own ROM;
   - the HD / modern mod.
2. **GPU 2D.** The graphics card draws the background and sprite layers. Today the CPU does this, at ~5.5 ms per frame (~0.5 of the ~1.45 cores the GPU path uses).

**Rules:**
- **No Nintendo material in the repo:** no ROM bytes, no strings taken from the ROM, no assets, no snapshots.
- **Behaviour stays identical:** a native function replaces the translation only after it has passed the shadow checker over a whole recorded race.
- **Nothing is pushed to GitHub without the owner's go-ahead.**

## Why a dictionary, and why it can't be fully automatic
Compiling the game threw away the meaning of the code: names, types, which numbers are pointers, what each structure holds. A tool can guess these, but it can't tell a right guess from a wrong one, and one wrong guess means bugs that may only show up hours into play.

The dictionary stores that meaning, one confirmed fact at a time. Guesses become safe because each native function is checked against the exact translation.

Native functions keep using "DS memory" (an array) through `Bus`. Turning DS addresses into real PC pointers needs the types of everything, so it comes last, and only where the dictionary already knows them.

## Starting point (in `My_NDS_GAME/4_docs`)
| File | Contents |
|---|---|
| `FUNCTION_TABLE.csv` | 11,175 functions. 8,174 have a written meaning (6,246 described, 1,872 known, 56 inferred); 506 sdk; 2,472 out of scope. Its `strings` column holds ROM text and is **never exported** |
| `SDK_FUNCTIONS.csv` | 1,257 Nintendo library functions with a guessed SDK name, confidence (guess / likely / verified) and `hle_needed` |
| `STRUCTS.csv`, `mapping_leads.csv` | 129 structures (e.g. `Kart`, 0x5A8 bytes) and ~16k field accesses |
| `FUNCTION_BOUNDARIES.csv`, `FUNCTION_MODES.csv`, `function_notes/` | Boundaries, ARM/Thumb modes, notes |

Existing code to reuse:
- **`2_native_game/src/machine.rs`:** `Hook::Func(fn(&mut Cpu, &mut ds_mem::Bus))` and `Machine::hook(entry, h)` replace a function by address. Native functions plug in here.
- **`2_native_game/src/bin/mkds_gen.rs`:** the generator, which already has `--names`.
- **`1_build_tool/src/build.rs`:** the builder.
- **`2_native_game/src/gfx2d.rs`:** `Engine2d::render_split`, `scan`/`fold`, `Split::pixel`.
- **`2_native_game/native/src/gpu/compose.rs` + `compose.wgsl`:** the GPU compositor.
- **Proof tools:** `render_compare`, plus `Machine::profile_time` / `prof_ns`.
- **Snapshot corpus (local only, git-ignored):** `builds/corpus/snap_{gp,battle,user}`, 549 frames.

## Work split
| Lane | Who | Branch / worktree |
|---|---|---|
| A. GPU 2D | Codex | `block3-gpu2d` |
| B1. Dictionary format, exporter, builder/generator hook-up, argument/return analysis | agent-lift (Claude) | `block3` |
| B2. SDK pass: names and signatures for the library functions; native versions of pure, hot ones with differential tests | Codex | `block3-sdk` |
| B4. Shadow checker: write journal on `Bus`, `--shadow` driver mode | Codex, when usage allows (otherwise agent-lift) | `block3-shadow` |
| B3. Game-function batches: dictionary rows, native versions, shadow race | Codex batches, reviewed by agent-lift | per batch |

## Lane A: GPU 2D
- **What moves to the GPU:** everything `Engine2d::render_split` produces, computed from the same inputs (2D registers, palettes, OAM, VRAM). That covers:
  - text, affine, extended and bitmap backgrounds;
  - sprites (normal, affine, bitmap);
  - windows and mosaic;
  - the priority and blend stack;
  - the 3D-layer slot;
  - brightness.

  The compositor then consumes the GPU results instead of the CPU `Split`.
- **Uploads:** only changed VRAM, palette and OAM regions are uploaded each frame.
- **Fallback:** the CPU path stays as the reference and the fallback (`Renderer = Software`, GPUs without compute support).
- **Done when:**
  - `render_compare` shows GPU 2D identical to the software 2D on all 549 frames at 1x (2D is integer work: exact, not ~99%);
  - mutation checks fail;
  - a windowed race runs at 100% speed;
  - 2D CPU time per frame and total CPU are measured before and after.

## Lane B: the dictionary
**Format (B1):** `dictionary/functions.csv`, one row per function:

| Column | Contents |
|---|---|
| `address` | Entry address |
| `segment` | Code segment |
| `name` | Function name |
| `kind` | `sdk` / `game` / `libc` |
| `args` | Typed arguments, e.g. `kart:*Kart, n:u32` |
| `returns` | Return type |
| `status` | `named` / `typed` / `native` / `native-verified` |
| `confidence` | How sure we are of the entry |
| `notes` | Our own prose |

Alongside it:
- **`dictionary/structs.csv`:** structure layouts.
- **Native versions:** readable, typed Rust in `2_native_game/src/native/`, registered as `Hook::Func` by address.

**Pipeline:**
1. **Exporter.** Converts the `My_NDS_GAME` mapping files into this format, without ROM strings or bytes, and runs an IP check.
2. **Builder.** Reads the dictionary. `mkds_gen` uses its names; `native-verified` functions are hooked; everything else stays the exact translation.
3. **Argument/return analysis.** The generator finds which of `r0`–`r3` each function reads before writing, and whether `r0`/`r1` are used after the return. This fills `args`/`returns` as a starting point.
4. **Shadow checker.** On each call to a function with a native version:
   - run the exact version with a write journal on `Bus`;
   - roll back;
   - run the native version;
   - compare the returned registers, `sp`, and memory and hardware writes.

   A recorded race with 0 mismatches promotes a function from `native` to `native-verified`.
5. **Batches.** The systems the mod needs come first (kart physics, camera, race logic, rendering calls), and the hottest functions first within them.

## After block 3 (roadmap)
1. **Profile the emulation thread** (~0.6 core): game code vs the ARM7 sound driver vs waiting loops vs synchronisation.
2. **Native sound driver** replacing the imitated ARM7 sound processor, if the profile says so.
3. **3D-model interception** at Nintendo's library calls: native rendering, HD models, widescreen. The base of the HD mod.
4. **Real PC pointers and types** where the dictionary knows them. Readable source from the player's own ROM.

## Status
| Item | State |
|---|---|
| Plan, branch `block3`, corpus at `builds/corpus` | Done 2026-10-16 |
| Native-function contract | Done. `2_native_game/src/native`: lifted-block shape, pay budget, whole leaf, return to lr. `Dispatcher::set_natives` installs natives over the entry block, per segment (calls in the game do not go through `Machine` hooks) |
| B1. Dictionary export | Done. `dictionary/export.py` produces `functions.csv` (11,297 functions, 8,246 with notes) and `structs.csv` (129), with ROM strings redacted and checked |
| B1. Builder / generator hook-up | Done. Every `dictionary/*.csv` goes to `mkds_gen --names`: signature + notes as comments. Games and `race_check` install `native::selected()` (VERIFIED by default; `MKDS_NATIVES=off`/`all`) |
| B1. Argument/return analysis | Done. `recomp::signature`, `mkds_gen --signatures`: whole-program register liveness through calls and tail calls; merged into `functions.csv` (`sig=auto`). Argument counts agree with public SDK signatures on 81 of 100 |
| B2. SDK pass (Codex) | Partial, merged; Codex stopped by its usage limit. `sdk_functions.csv`: 1,257 rows (1,157 named, 87 typed, 13 native). 13 native leaves (copy/fill, strlen, clz, 64-bit multiply, divider/sqrt helpers), differential-tested against the ROM (`tests/native_sdk.rs`) |
| B4. Shadow checker | Done (agent-lift). `recomp::shadow`, `Session::enable_shadow`, `acceptance`/`race_check` with `MKDS_SHADOW=1` writes `shadow.txt`. Memory-like hardware registers (2D registers, 3D tables) are compared in order; FIFOs/command ports are refused |
| First verified natives | 10 of 13 SDK natives verified by two GP races under the shadow checker (0 mismatches; e.g. 852,381 `FX_GetDivResult` calls, 74,473 `MIi_CpuClearFast`) and installed by default. A race with them on finishes 1st with 0 interpreted instructions. Still on trial: `MIi_CpuCopy32` (3 calls), `FX_Mod`, `FX_DivS32` (not called in a race). These natives cover ~1-2% of executed instructions: the pipeline is proven, the speed gain comes from game functions |
| A. GPU 2D (Codex) | Done. `gpu/two_d.rs` + `two_d.wgsl`, dirty-page uploads, `render_compare --gpu-2d`: exact on all 549 corpus frames (records and screens); a sprite-priority mutation drops snap_gp to 39/301. In the game window: 102% speed, 60 fps, 0 underruns, 2D submission ~0.5 ms/frame. Whole game process: **0.87 cores** with the GPU renderer (block 2: ~1.45; block 1: ~1.0), 1.49 with the software renderer |
| Display capture | Fixed (owner report: course intros flickered between screens). The game shows 3D on both screens by capturing engine A into VRAM C/D and showing it on engine B the next frame; presenters now carry the captured image (at HD scale on the GPU) for up to 3 frames (`CaptureCarry`) |
| Toon shading | Fixed (owner report: karts black with the star and after a blue shell). Toon/highlight polygons now take their colour from the toon table (`gx::resolve_toon`); highlight shading is still not modelled |
| Default scale | `Auto` (owner: "default ... more than the native resolution"); `Scale = 1` is the original look |
| B3. Game-function batches | Paused 2026-10-16: the owner moved the focus to the hand port (private plans in `My_NDS_GAME/4_docs`) |
