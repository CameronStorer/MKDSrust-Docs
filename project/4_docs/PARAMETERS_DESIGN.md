# Real function parameters in the readable source: design (draft for review)

Status: proposal, 2026-11-03. Builds on the Block 5.5 work already merged (`--timing native`, `direct` crate).

## Problem
Every raised function today looks like this:

```rust
pub fn kart_update_tilt_target(c: &mut Cpu, m: &mut dyn Bus, pc: u32) -> u32 {
    let (mut r0, mut r1, mut kart, mut sp, mut lr) = (c.r[0], c.r[1], c.r[4], c.r[13], c.r[14]);
    ...
    spill!(); let x = m.call(c, 0x2075A1Cu32, 0x2075AF0); ... reload!(); // vec_dot_product
```

That means:
- arguments arrive in a register file (`c.r`);
- every call writes all live registers back (`spill!`) and reads them again (`reload!`);
- calls go through the dispatcher by address.

The goal (the "T2 shape"):

```rust
pub fn kart_update_tilt_target(g: &mut Game, kart: Ptr<Kart>, target: Fx32) {
    let d = vec_dot_product(g, kart.add(0x244), target);
    ...
}
```

## Where we are
In `--timing native` builds the generator already finds **closed** functions: ones that reach no point where the
console could observe their registers (no poll point, no call into code that can). They get a direct variant with
registers as Rust parameters, and 15,757 call sites call them directly. Last build:

| Reason a function is not closed | Functions |
|---|---|
| **closed (already direct)** | **3,474** |
| calls a function that is not closed | 5,193 |
| loop with a poll point | 2,157 |
| computed call (function pointer) | 404 |
| returns elsewhere | 199 |
| falls through into the next function | 170 |
| native, hook, thread context, helpers, exception return | 29 |

Most of the blockers are **transitive**: a function is open only because something it calls is open.

## Approach (three steps, each proven separately)
**Step 1: boundary calls (unblocks most of the 5,193).** A closed function may call an open one through a narrow
boundary:
- spill only the callee's argument registers, plus `sp` and `lr`;
- call through the dispatcher;
- reload only what the callee may return or clobber (r0–r3, r12), as the ARM calling convention promises.

The callee-saved registers (r4–r11) stay in Rust locals. This is safe only if every open callee really preserves
r4–r11. That's what the existing **T1 calling-convention check** verifies per function (`preserved_regs`). Callees
that fail it keep the full spill. Expected result: most of the 5,193 become closed or boundary-closed.

**Step 2: poll points in loops (2,157).** In native timing, a loop's poll point lets interrupts run. Interrupt
handlers only save and restore the registers they use, and they run on their own stack, so the interrupted function's
locals don't need to be in `c.r`. This is Block 5.5 condition 2 ("IRQ handlers entered only at safe points"). It is
true once IRQs are delivered only at calls and polls (already the case in native timing) and the handlers are raised
functions checked to preserve r4–r11. Thread switches (`OS_SaveContext`/`OS_LoadContext`) are the exception. They
need per-fiber register files (condition 3, already done with fibers) and stay full-spill.

**Step 3: signatures and types in the printout.** With the calling convention settled:
- arguments are the registers a function reads before writing (r0–r3, and stack slots for more than 4);
- results are r0 (and r1 for 64-bit values) when a caller reads them.

Both are found by the whole-program analysis the generator already runs (`entry_reads`, `ret_seed`). The struct
types from Block 4 name and type them: `kart: Ptr<Kart>`, `Fx32` where the value comes from or goes to a fixed-point
field, `u32` otherwise. Calls print as `kart_update(g, kart, speed)`.

## What stays as it is
- `--timing exact` (the proof build) keeps today's register-file code. Parameters are a native-timing feature, as
  all of Block 5.5 is. The exact build is the reference that native builds are compared against.
- Computed calls (404) go through the dispatcher with a boundary spill. Function-pointer tables can get typed
  wrappers later.
- Functions that fall through or return elsewhere (369) stay T0-shaped. They are oddities, listed in `tiers.csv`.

## Proof
Every step is checked three ways:
1. **Differential tests** (`tests/t1_differential.rs`, extended to "no-spill" mode): every changed function against
   its exact translation on random states, for all ROM functions with boundary calls.
2. **The native race:** `acceptance` on the native build still finishes 1st, at the same frame (11260) as before
   each step.
3. **Frame compare** (`frame_compare`, Block 5.0 oracle): logical frames of the native build match the exact build,
   as they do today.

A step lands only when all three pass.

## Effort and order
Step 1: about a week. Step 2: about a week, mostly the handler-preservation check and its tests. Step 3: printing
and types, about a week. Each step ships on its own and makes the code more readable.

## Risks
- **A callee breaks the calling convention** (hand-written assembly in the SDK does this). Mitigated by the
  per-function check, so failing callees keep the full spill.
- **IRQ handlers that touch r4–r11 without saving them.** The same check covers handlers.
- **Performance changes timing in native builds.** Native timing doesn't depend on instruction counts, so it's
  unaffected by design.
