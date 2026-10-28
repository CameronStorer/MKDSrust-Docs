# Block 4: from translated code to readable source (the full decompilation)

Owner direction (2026-10-27): finish the NDS ROM -> source pipeline. The hand port is out of scope.

## Where we are
| Block | State |
|---|---|
| 1. Translate the ROM's code to Rust, with no interpreter | Done. 11,297 ARM9 functions plus the ARM7 program. A race runs to the results screen with 0 interpreted instructions |
| 2. Native window, GPU 3D, audio, controllers | Done |
| 3. Function dictionary, shadow checker, first natives | Running. 11,297 rows (8,246 with notes), 129 structs, 10 verified natives |

**The gap:** the generated `source/` runs, but it isn't readable source. Every function is a register machine:
`c.r[3] = R::subs(c, c.r[1], 0x10u32); ... bus.write32(ea, c.r[0])`. A full decompilation means that every
function comes out like this instead:

```rust
/// Kart_UpdateSpeed(kart: Ptr<Kart>, input: u32)
pub fn kart_update_speed(g: &mut Game, kart: Ptr<Kart>, input: u32) {
    let mut speed = kart.speed(g);
    if input & KEY_A != 0 {
        speed = fx_mul(speed, kart.accel(g));
    }
    while speed > MAX_SPEED { ... }
    kart.set_speed(g, speed);
}
```

The code is still generated on the user's machine from their own ROM, and it still behaves exactly like the game.

## Status (2026-10-28)
| Package | State |
|---|---|
| 4A IR | Done. Prints today's code identically for all 12,736 functions |
| 4A.2 Fibers | Done, **default** (`MKDS_FLAT=1` turns it off). Race identical to `main`; 401,332 SDK thread switches served |
| 4B pass 1, dead flags | Done, **default** (`MKDS_EXACT=1` turns it off). Race identical |
| 4B T1 raised functions | Done for **all 12,736 ARM9 and ARM7 functions** (0 rejected; the ARM7 uses its cycle-cost budget). Compiled switches print as `match` over their cases (563). Locals, folded temporaries, structured `if`/`loop`/`break`, folded compares (`if r6 == 0`), memory helpers (`R::st32`, `R::ld16s`), push/pop notes. Race identical (fibers and flat). `tests/t1_differential.rs` compares T1 with T0 on synthetic cases and on 300 ROM functions from 48 random states each. `MKDS_T1=off/all/<file>` for bisecting |
| Names | All ARM9 and all 1,105 ARM7 functions named; latest review changed 109 names and leaves 1,445 names ending exactly in `_maybe`. See the completed-work evidence below |
| Comments | Calls carry the callee's name; constants carry global names. Layout tables: `dictionary/fields.csv`, `field_uses.csv`, `globals.csv` (`export_layout.py`) |
| 4E source package | `source/README.txt` explains both versions; `tiers.csv` indexes every function (address, tier, Rust name, crate) |
| 4C types (T2) | **Accessors, struct inference and type propagation implemented.** Reaching definitions, alias/parent layouts, pointer fields, global roots, interior pointers and constant-global bases seed types; caller facts propagate to callees. Current measured coverage (`0a4351f`): **26,370 accessor sites, 810 typed-argument functions, 1,003 renamed-register functions, 11,770 named-global notes**. Fiber and flat races identical. Broader type coverage, SDK value types and source organization remain; see evidence below |

### Completed since the initial status

- **T1:** all **12,736 ARM9 and ARM7 functions** have raised output, with no rejected functions (`daf1a38`, `9c3b700`). T0 remains available for transfers that require exact dispatch behavior.
- **Flags as locals:** `6b267ef` makes **81,372 of 107,472 compares** into `fa`/`fb`/`fz` locals folded into conditions. Observable boundaries still synchronize CPU flags. Fiber and flat races remain identical.
- **Type coverage:** interior pointers, constant-global bases and additional global/field seeds (`0a4351f`) increased accessor sites **8,258 -> 26,370**, typed-argument functions **435 -> 810**, renamed-register functions **437 -> 1,003**, and named-global notes **4,086 -> 11,770**. Fiber and flat races remain identical. These are coverage counts, not proof that the 60% T2 goal is met.
- **Names:** the last ARM9 functions and all **1,105 ARM7 functions** were named (`6a12b0a`, `94f2f24`); **491 SDK placeholders** were named (`67f804a`). The latest [name review](../NAMES_REPORT.md) examined **1,532** rows ending exactly in `_maybe`: **109** changes (**87** confirmations, **22** rewordings retaining uncertainty). **1,445** such names remain uncertain (1,327 game, 118 SDK); names containing `_maybe_...` were outside that review.
- **Fields:** after **664** field names landed (`6383f63`), the [field review](../FIELDS_REPORT.md) examined the remaining **595** placeholders: **204** renamed (**58** confident, **146** `_maybe`), **391** kept.

**Remaining:** resolve uncertain names and fields, broaden inferred types, separate pointers from integers, add SDK value types and improve source organization. Direct typed call signatures and spill/reload removal remain linked to Block 5.5. The work-package lists below retain the original design; T1 coverage is complete, but full source readability and the Block 4 completion criteria are not all established.

How exactness holds:
- T1 pays the same budget at every original block start, and spills its locals before anything that reads `c.r`.
- Any transfer that isn't to a fixed block of its own (a computed jump, a call that came back somewhere else, an
  exception return) continues in the function's T0 translation. T0 stays registered for every block.
- Dead flags may differ in saved thread contexts. They're never read, and the races are identical.

## Decision: stay with Rust
C would be simpler in one way: C has `goto`, so any control flow can be written without first turning it into
loops and `if`s. That isn't worth switching for:
- The whole working pipeline is Rust: lifter, runtime, shadow checker, GPU host and builder.
- The structuring problem is solved for Rust too: labeled blocks and `loop`, with a small state machine for the rare
  graphs that can't be structured.
- The one thing C would buy is reusing the community's matching C decomps. We can't ship that code, and it covers
  only about 30% of functions.

## Decision: raise the translation, don't do a matching decomp
A *matching* decomp writes C by hand until Nintendo's compiler produces the exact same bytes. It needs the
proprietary `mwccarm` compiler. After a lot of work, the USA project is at about 30% of functions. A port would
also still need a PC platform layer on top.

A *raising* decompiler starts from what we already have: correct, complete, verified code. It improves that code
automatically, and the shadow checker proves each step. This covers 100% of functions from day one, and readability
gets better over time.

## Tiers (each function is in exactly one; the report counts them)
| Tier | What the function looks like | How it gets there |
|---|---|---|
| T0 exact | Today's register machine | Generator (done) |
| T1 raised | Local variables instead of registers, no dead flag math, `if`/`while`/`match` instead of jumps, stack slots as locals, typed calls `f(g, a, b) -> r` | Automatic decompiler passes (4A, 4B) |
| T2 typed | Real name, typed arguments, struct fields (`kart.speed(g)`), `Fx32`/`VecFx32`, named globals and constants | Dictionary plus type propagation (4C), filled in by agent batches (4D) |
| T3 native | Hand-tuned Rust that talks to native services (files, GX, sound) instead of hardware registers | Block 3 natives and Block 5 |

**Rule:** a function moves up a tier only after its new version passes the shadow checker with 0 mismatches over the
recorded corpus (races, battle, mission, menus). If it fails, the build automatically keeps the previous tier for
that function. Behaviour never changes.

## Work packages

### 4A. An IR inside the lifter (foundation)
`lift.rs` currently formats Rust strings straight from each decoded instruction. Put a small IR in between:
decode -> CFG of IR operations (explicit reads and writes of registers, flags and memory) -> emit.
- The first emitter prints T0 from the IR. Its output must match today's generator exactly (text diff, or the
  shadow corpus where the text changes).
- ARM7 goes through the same IR.
- **Done when:** a fresh build from the IR emitter passes the race acceptance with 0 interpreted instructions, and
  `race_check` under `MKDS_SHADOW=1` shows 0 mismatches.

**Status (2026-10-27):** done. `src/ir.rs` lowers each instruction to statements with explicit register, flag and
memory effects, and prints T0. `tests/ir_t0.rs` compares it with the old string emitter on 400k random ARM words,
every Thumb halfword and 835k ROM encodings, with no differences. A whole-ROM generation gives all 12,736 functions
identical to `main`, up to whitespace.

### 4A.2. Fiber runtime (needed before T1; owner-approved 2026-10-27)
Today a call doesn't run the callee. The lifted function returns to the session's run loop at every call, return
and slice end (at most 32 instructions), and is later re-entered at any block. That's why T0 must be a
`loop { match pc }` over global registers. Raised code needs real calls. Same idea as WiiCompiled (a host fiber per
guest thread), adapted so runs stay identical:
- **Calls nest:** `Bus::call` runs a nested dispatch loop until the callee returns to `ret` with the call's `sp`.
- **Slices end in place:** a block that can't pay its budget calls `Bus::slice_end`. The fiber suspends, the host
  ticks the hardware and the ARM7, and on resume a pending IRQ runs as a nested call of the vector, until the
  exception return comes back to that block. Slice boundaries are exactly the flat loop's: budget used up, code
  written, a dispatch miss.
- **One fiber per SDK thread:** each dispatch-loop step reads the SDK's current thread (`*(*0x0216FF34)` on AMCE).
  If another thread is current, the host resumes that thread's fiber, or starts a new one. The first thread adopts
  the boot fiber.
- **Non-local exits** (context loads, a `SaveContext` resume) go to the innermost loop. A pc that matches an outer
  loop's `(ret, sp)` unwinds to that loop, through T0 frames, which pass it on. Functions that do this have to stay
  T0; a raised function is only ever left normally.
- Code: `src/fibered.rs`, enabled with `MKDS_FIBERS=1` or `Session::enable_fibers`. Fibers are now the default (`74b34b3`); `MKDS_FLAT=1` selects flat dispatch.
- **Status (2026-10-27): proven identical over a full race.** On the Figure-8 acceptance race, `race_check` with
  fibers and on `main` produce:
  - the same 1,707,950,080 ARM9 instructions and 581,521 IRQs;
  - a finish at frame 11,462 in 1st place;
  - byte-identical telemetry for all 12,362 frames, identical inputs and all 40 screenshots.

  Three details were needed for exactness:
  - every slice start runs the residency-checking resolver at the resume point;
  - a return into an unmapped (invalidated) overlay block ends the slice, as the flat loop's miss does;
  - after a suspension, the CPU is read through the session pointer, never through a `&mut` held across it.

  Diagnostics: `MKDS_SLICE_TRACE=<file>` (per-frame hash of every slice end), plus `MKDS_TRACE_FRAME=<n>`.
  Not yet: `overlay_instructions` isn't counted in fiber mode, and thread switches are counted but not yet
  exercised in a test of their own.
- **Equivalence check:** `race_check` with and without fibers must give the same instruction and IRQ counts, the
  same per-frame telemetry and the same screenshots. T1 code keeps charging the same per-block budget at the same
  points, so the same check also proves raised functions, and can be bisected to single functions.

### 4B. Decompiler passes (T1), whole program
The original pass design follows. All functions now have T1 output; proposed stack-local and direct typed-call forms remain readability goals where not yet emitted. Each pass is separately switchable, so a failing function can be traced to the pass that broke it.
1. **Flag liveness.** Drop every N/Z/C/V calculation that nothing reads. This is most of today's noise.
   *Implemented, default and race-proven (`74b34b3`, `6b267ef`); `MKDS_EXACT=1` disables dead-flag elimination.* On the whole ROM it
   removes 65% of `R::set_nz`, 76% of carry writes, and turns a third of `R::subs`/`R::adds` into plain
   arithmetic.
2. **SSA and register promotion.** Registers become `let` locals. Arguments and returns come from
   `recomp::signature` (already whole-program). The callee-saved discipline is checked per function. The original design kept calling-convention exceptions at T0; all functions now have T1 output, with exact dispatch fallback where needed.
3. **Stack frames.** `sp`-relative slots become locals. A slot whose address escapes stays in a small frame array
   in DS memory.
4. **Constants.** Literal-pool loads fold into constants. Addresses inside known sections become symbols
   (`G_0217ACF8`, named once the dictionary knows them).
5. **Calls.** `BL`/`BLX`/tail calls become direct typed calls. Calls through function tables become
   `call_indirect(g, addr, args)`, using the existing overlay-safe dispatcher.
6. **Structuring.** Turn the CFG into `if`/`else`, `loop`/`while`, `break`/`continue` and `match` (the switch
   tables are already found). Rust's labeled blocks handle early exits. Irreducible graphs fall back to a local
   `loop { match state { ... } }`.
7. **Simplifier.** Turn `wrapping_add` and casts into plain expressions where values can't overflow. Fold
   comparisons into conditions.
- **Done when:** at least 95% of ARM9 functions are T1 and shadow-clean, every T0 holdout has a recorded reason,
  and a race still finishes 1st at full speed.

### 4C. Types (T2 machinery)
- Generate typed views over DS memory from `structs.csv`: `Ptr<Kart>` with accessor methods
  (`speed()`/`set_speed()`) that compile to the same `Bus` reads and writes. Semantics stay exact while the code
  reads like source.
- Propagate types both ways along calls: a typed argument types the caller's value, and vice versa.
- Separate pointers from integers with relocation analysis. `ds-decomp`'s `relocs` (MIT, Rust crate) or our own
  pass both work.
- Add NitroSDK value types: `Fx32`, `Fx16`, `VecFx32`, `MtxFx43`. Use the SDK rows the dictionary already has.
- Sort the output into modules by the dictionary's `area` column (`kart/`, `item/`, `course/`, `sdk/gx/`, ...),
  not one giant file.

### 4D. Dictionary batches (the repetitive part, handed to Codex)
Batches of about 50 functions per area, hottest and most-called first. Each batch fills in name, `args`/`returns`,
struct fields and notes for its functions. Every batch is checked automatically before it merges:
`export.py` IP check (no ROM strings), the build type-checks, and a shadow race shows 0 mismatches.
- Inputs agents can use, all private and local: IDA databases (`5_tools/idb/mkds_plan*.i64`), the reference C in
  `6_data/export`, `function_notes/`, `STRUCTS.csv`, `mapping_leads.csv`. REA (installed at
  `C:\AI\reverse-engineering\rea`) gives agents MCP access to IDA/Ghidra for xrefs and pseudocode.
- Only our own facts and prose go into the repo: names, types, offsets, notes.
- Codex runs as `codex exec` in its own worktree per batch. Claude reviews and merges. Batches stay small because
  both have usage limits.

### 4E. Source package
The builder writes `source/` as a normal cargo workspace: `game/` (raised code by area), `sdk/`, `arm7/`, plus the
runtime as a dependency, and a `TIERS.md` report (counts per tier and area, each holdout and why).
`--keep-generated` stays the default. Two fresh builds must still produce identical source.

## External helpers
| Project | Use | Caution |
|---|---|---|
| [tylzars/mkds](https://github.com/tylzars/mkds) (USA matching decomp, 3,465 / 11,501 functions matched) | Cross-check our boundaries (11,297 vs 11,501). Source of names and struct layouts | No license stated, and they don't accept outside code. Ask the maintainer before importing names. Never copy C |
| [RonyxDumb/mkds](https://github.com/RonyxDumb/mkds), [ai-tdd-labs/mkds-decomp](https://github.com/ai-tdd-labs/mkds-decomp) (EUR) | Same, via EUR -> USA function matching | Check each license |
| [ds-decomp / dsd](https://github.com/AetiasHax/ds-decomp) (MIT, Rust) | `sig apply` for SDK identification, relocation analysis to tell pointers from integers, delink info | Can be used as a crate |
| [mstan/ndsrecomp](https://github.com/mstan/ndsrecomp) (C, early) | Design comparison only (two-CPU scheduling, oracle testing) | PolyForm Noncommercial + GPL: read, don't copy |
| WiiCompiled / aurora (local copy) | Reference for the Block 5 platform layer | GPLv3: ideas only |
| [REA](https://github.com/morluto/rea) | Agent access to IDA/Ghidra during 4D | Analysis only; it doesn't produce source |

## Order and checkpoints
1. **4A** (agent-lift, 1 lane). Nothing else changes in `lift.rs` until it lands.
2. **4B** passes 1-3 -> checkpoint: % T1 on the corpus.
3. **4B** passes 4-7, in parallel with **4C** typed views and **4D** batches (4D can start right away: it only
   touches the dictionary).
4. **4E** packaging, then a fresh build and acceptance.

**Block 4 is done when:**
- One command builds from the ROM only.
- 100% of functions are at T1 or above, except listed holdouts (under 5%, each with a reason).
- At least 60% are T2: named and typed (the dictionary already has notes for 73%).
- A full race finishes to results under shadow with 0 mismatches.
- Repeat builds produce identical source.
- The repo has no Nintendo material.

## Block 5 (under way)
Native FS, ARM7 services, event-driven sound and OS time have merged behind switches; an opt-in budget-free build finishes first. See the [Block 5 status](BLOCK5_PLAN.md#status-2026-10-28). Real PC pointers, broader native graphics services, HD and modding hooks remain planned.
