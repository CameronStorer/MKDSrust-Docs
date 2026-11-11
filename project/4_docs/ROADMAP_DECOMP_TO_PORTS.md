# Roadmap: from decomp to portable source

Owner decision, 2026-11-10. This replaces earlier priorities for code work; the PC port stays frozen.

## Where we stand (2026-11-10)
| Goal | Status |
|---|---|
| Recomp (the game runs natively on PC) | **Complete.** All 12,736 functions translated; the exact build matches the DS frame for frame |
| Decomp (every function named and typed, "T2") | **81.3%** (10,360 / 12,736), measured 2026-11-03 |
| Readable Rust (no simulated DS, "T3") | **Barely started.** 3,474 functions have a direct form; none is free of the simulated CPU and memory |

## Scope (owner decision, 2026-11-10)
- **ARM7 code (1,109 functions) is out of scope for readable source.** Native builds already replace it with
  native services (sound driver, ARM7 HLE). Converting it would be wasted work. Names stay as they are.
- **The online area (`code_net`, 2,185 functions) is parked.** Nintendo's servers closed in 2014; online play needs a
  new service anyway. Names stay best guesses; no conversion.
- Both metrics print an "in scope" figure over the remaining 9,451 functions.

## Reference: the tylzars/mkds matching decompilation (owner decision, 2026-11-10)
[tylzars/mkds](https://github.com/tylzars/mkds) (MIT, Tyler Zars and RonyxDumb) is a matching C decompilation of the
USA version: 11,498 / 11,498 functions matched. The owner has the creator's permission to use its findings.
- **We use its facts:** function names, struct layouts and field names, and function signatures, merged into our
  dictionary with credit. They finish naming and typing (stage 1) and give stage 2 exact types and signatures.
- **We don't copy its code:** no C function bodies are translated into our repo. Our repo stays "generated on the
  user's machine from their ROM, plus our own dictionary". Conversion agents may read its C to understand intent.

## Decision: park full T3b (owner, 2026-11-10)
Readable source for ports now exists as the tylzars/mkds C decompilation, and consoles are out of scope, so the full
T3b conversion (about 5-8 weeks) is parked. Plan instead:
1. Finish the decomp (names and types).
2. The cheap readable layer: typed signatures, flags as locals, boundary calls and loop polls, turned on together and
   verified. It still runs on the simulated DS, but reads far better for modders.
3. Then T3b only per subsystem, when a concrete mod needs it (e.g. graphics interfaces for HD/widescreen, kart and item
   code for AI or more karts). The approved [T3b design](T3B_DESIGN.md) stays the plan for that work.

## Direction update (owner, 2026-11-11)
- **Positioning:** MKDSrust is about playing MKDS natively on Windows and modding it. The tylzars/mkds C decompilation already
  serves people porting the game to other hardware, so ports are not our goal.
- **Readable Rust continues only through the flat-memory route:** a 32-bit build with the DS memory at its real addresses,
  so c2rust output of the tylzars C runs natively on that memory (no simulated CPU or memory bus), with our generated code as
  the fallback. It replaces the earlier plan of routing converted code through the `Bus`. A feasibility test (32-bit build
  with an identical race, then one converted file swapped in) decides whether it goes ahead.
- **Next mod:** Single Screen, as a layout option of the Widescreen mod.
- **Paused:** the Toolbox and the mod hub.

## The four stages
1. **Finish the decomp (T2).** Name and type every function. Dictionary batches, done by agents, merged and
   checked by a build and the race.
2. **Readable source (T3).** Rewrite functions as plain Rust and replace the simulated DS with native services:
   - **T3a, no CPU:** no `Cpu` argument, no flag maths, real parameters and results
     ([PARAMETERS_DESIGN](PARAMETERS_DESIGN.md) steps 1-3, plus flags as locals).
   - **T3b, no simulated memory:** no `Bus`; typed structs and real pointers; renderer, sound and file interfaces
     instead of DS hardware registers. Needs its own design, reviewed by the owner before work starts.
3. **Optimise.** Whole-program optimisation (LTO), Thumb/size options for weak targets, fixes to obvious waste in
   the readable code.
4. **Improve over time.** Apply new findings and better methods without changing how the game plays.

Stage 1 and stage 2 run side by side: each area is named and typed first, then converted.

## Parity rule
| Part | Rule |
|---|---|
| **Game logic** (physics, items, AI, timing, randomness) | **Must stay identical.** Same inputs give the same race, frame by frame |
| **Presentation** (graphics, sound output, UI layout) | **Free to improve** (resolution, widescreen, rendering) |

- The game's maths is fixed-point. Game logic must stay fixed-point: switching to floating point changes results
  slightly, so ghosts and physics drift. Presentation code may use floating point.
- `--timing exact` stays the reference build. Every change is checked against it.

## How every change is checked
- **Decomp rounds:** build, `dictionary/t2_metric.py` goes up, exact race `race_diff.py` prints IDENTICAL.
- **T3 changes:** differential tests against the exact translation (`tests/t1_differential.rs`), the native race
  finishes 1st at the same frame, and `frame_compare` matches the exact build.
- **Hand-written natives:** a shadow race (`MKDS_SHADOW=1`) with 0 mismatches, plus random tests.

## Order
1. T2 in the weakest areas first: sys_math, input, save, net, sys_mem; then the largest backlogs (menu, net, obj, misc).
2. T3a generator work: boundary calls, flags as locals, poll points in loops, typed signatures.
3. T3 pilot: hand-written `sys_math` in plain Rust, measured for size and speed against the lifted code.
4. T3b design, then area by area.

## Later (needs stage 2 first)
- **Ports to other hardware:** with T3b done, a port is the game plus a renderer, sound and input for that device.
  The two-screen layout and touch input need a design per device.
- **DSi-native build:** compile the readable source back to an ARM ROM for DSi mode (16 MB RAM, 133 MHz).
  Homebrew loaders only; built from the user's own ROM like everything else. Consoles were left to forks on
  2026-11-09, so this needs the owner's go-ahead.
- Every port still ships the builder, never the generated source. Each user supplies their own ROM.
