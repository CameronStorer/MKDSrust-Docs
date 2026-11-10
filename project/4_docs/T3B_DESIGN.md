# T3b "no simulated memory": design

> **Approved by the owner, 2026-11-10, as recommended:** T3b = M2 (one byte arena, typed opaque pointers, no
> addresses in the source; M3 real structs optional and later); pilots sys_math → kart physics → items; only the
> dead-stack mask may differ in `frame_compare`; a separate "T3b-pending" tier in `t3_metric.py`; hardware traits in
> a new `platform` crate.

Status: proposal, 2026-11-09. Nothing here has been built. It follows the roadmap's parity rule
(`4_docs/ROADMAP_DECOMP_TO_PORTS.md`): game logic stays identical and fixed-point, presentation is free to change,
and `--timing exact` stays the reference.

## 1. What T3b means, and where we are

`dictionary/t3_metric.py` defines **T3b** like this: the function has a direct variant, and its body uses neither
the simulated CPU (`c`) nor the simulated bus (`m`). For porting, this design adds one more condition: **no DS
addresses in the source**.

Measured on `fleet/r7_both` (in scope = everything except `code_arm7` and `code_net`):

| | All 12,736 | In scope 9,451 |
|---|---:|---:|
| Direct variant | 4,327 | — |
| T3a (no CPU) | 2,529 | 2,264 (24.0%) |
| T3b (no CPU, no Bus) | 253 | 235 (2.5%) |

What the 4,327 direct functions still use `m` for (counted in `direct/src/lib.rs`):

| Use of `m` | Count | What it is |
|---|---:|---|
| `push {..}` / `pop {..}` blocks | 1,742 / 3,147 | Saving callee-saved registers on the DS stack |
| Named field accessors (`kart::bounce_height(m, kart)`) | 9,024 sites | Typed data access, still by DS address |
| Untyped `R::ldr/st32/ld16/...` | 12,768 sites | Data or hardware access through a register holding an address |
| Dispatcher boundary calls (`m.call(c, ..)`) | 527 | Calls into functions that aren't direct yet |
| `R::bad_return` / `lr` parameters | 3,432 | Checks that the callee returned where expected |

So T3b breaks into four jobs, and each can be proven on its own: **stack frames, data access, calls, and
hardware**. The real limit is T3a: only 24% of in-scope functions are T3a. T3b work therefore moves together with
T3a work and can't get ahead of it.

## 2. Memory model

### 2.1 Principle: one backing image, typed views, no copies

Game state stays in **one memory image**: the byte buffers `ds_mem::Bus` already holds (`main` 4 MB, `dtcm`
16 KB, `itcm`, `swram`). Converted and unconverted functions read and write **the same bytes**. Nothing is copied
or synced, so code with some functions converted and others not is safe by construction. What changes is how code
reaches those bytes.

| Stage | What code sees | Example |
|---|---|---|
| M0 (today) | `m: &mut dyn Bus`, DS address `u32` | `kart::bounce_height(m, kart)` |
| **M1** | `g: &mut Game`, typed `Ptr<T>` (a 32-bit DS address inside) | `kart.bounce_height(g)` |
| **M2 (= T3b)** | No addresses in source: globals by name, opaque pointers, generated layout table | `g.globals.kart_array()` |
| M3 (optional) | Real Rust structs in arenas per subsystem | `g.karts[i].bounce_height` |

**Recommendation: T3b = M2.** M3 is optional and decided per subsystem (2.7). A port still needs a byte arena of
about 4.1 MB. That arena is ordinary memory, not DS hardware.

### 2.2 `Game` and the data image

```rust
pub struct Game<'a> {
    mem: DataImage<'a>,        // main RAM, DTCM, ITCM, WRAM: plain bytes, no MMIO
    hw:  &'a mut dyn Platform, // section 3
    sp:  u32,                  // current thread's DS stack pointer (2.5)
}
```

`DataImage` copies the RAM part of `ds_mem::Bus::locate` and nothing else:
- **Address lookup.** DTCM is checked first (`dtcm_base` 0x027E0000; `item_slots` at 0x027E00C8 is there). After
  that come mirrored main RAM (`a & 0x3F_FFFF`), ITCM and WRAM.
- **ARM access rules**, the ones `rt.rs` already spells out:
  - `ld32` masks bits 0–1, and `ldr` rotates unaligned words.
  - `ld16` masks bit 0, and signed loads sign-extend.
  - Values are **little-endian** (`from_le_bytes`), so big-endian hosts get the same results.
- **Overlays.** Main-RAM writes keep the `note_main_write`/`code_epoch` hook, which invalidates overlays.
- **Bad addresses.** A non-RAM address in a T3b function is a **bug**. Debug builds panic. Transition builds fall
  back to the Bus and log it.

### 2.3 Typed views (`Ptr<T>`)

The `layout` crate already generates offsets and accessors for every struct (22k lines from
`structs.csv`/`fields.csv`). Only their printed form changes:

```rust
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Ptr<T>(u32, PhantomData<T>);
impl Ptr<Kart> {
    #[inline(always)] pub fn bounce_height(self, g: &Game) -> Fx32 { g.mem.ld32(self.0 + OFF) as Fx32 }
    #[inline(always)] pub fn set_bounce_height(self, g: &mut Game, v: Fx32) { g.mem.st32(self.0 + OFF, v as u32) }
}
```

- **The pointer is still a 32-bit DS address inside.**
  - Game data stores pointers: 573 `ptr` fields and 116 pointer globals, used for linked lists and object tables.
  - The game also compares pointers, sorts them, and offsets them (`base + i * 0x5A8`).
  - Keeping the real value keeps all of that identical. M2 hides the number from the source but doesn't change it.
- **Aliasing costs nothing.** Several views over the same bytes are just offsets. `Kart` has 21 aliases, and 31
  structs have a parent. Accessors hold no Rust references, so overlapping views never fight the borrow checker.
- **Odd cases keep their own accessors.** That covers unknown fields (`f_008`) and odd-width reads
  (`entries_a_u8`). Each is still a typed *data* access, exact to the byte.

### 2.4 Globals

`globals.csv` names 187 globals, and the code refers to many more. In M2, every constant address that the generator
can place in `.data`/`.bss` becomes a symbol: `KART_ARRAY: Global<Ptr<Kart>>`, or `G_0217B49C` until it has a
name. The address table is a **build output** made from the user's ROM, and so are the initial values. No
Nintendo data goes into the repo.

### 2.5 The stack

- **Saved registers** (`push {r4-r6, lr}`) are simply not written, because their values live in Rust locals.
  - The shadow checker already treats bytes below the entry `sp` as dead, and `preserved_regs` proves the restore.
  - `frame_compare` hashes DTCM and main RAM, where thread stacks live. It therefore needs a new **dead-stack
    mask**: per thread, everything below that thread's saved `sp`.
- **Locals whose address escapes** stay on the DS stack at the same address.
  - 373 direct functions access data relative to `sp`.
  - `let buf: Ptr<VecFx32> = g.frame(12);` lowers `g.sp`, and the function's exit raises it again.
  - A stack address that leaks into game data therefore still matches.
- **Stack arguments** (the 5th and later):
  - They become Rust parameters when the callee is direct.
  - Unconverted callees still get them on the stack at `[sp]`.

### 2.6 Heaps, pointers to code, overlays

- **The game's own allocators stay game code.** That covers `mem_alloc_heap_block`, the expanded and linear heaps,
  `os_alloc_from_heap` and the object pools.
  - On the same arena they return the same addresses in the same order.
  - Free lists, pointer comparisons and pool scans all depend on that.
  - They convert to T3b like any other function. Game logic must **never** switch to `Box` or `Vec`.
- **Pointers to code** stored in data (vtables, `update_callback`) stay DS code addresses, Thumb bit included,
  because the ROM's own tables contain them.
  - `g.call_indirect::<Sig>(addr, args)` looks them up in a generated table keyed by **(resident segment,
    address)**, since overlays share addresses (`residency.rs`).
  - During the transition, addresses missing from the table fall back to the dispatcher.
  - This is how the 404 computed-call functions convert. `FnPtr<Sig>` keeps those calls readable.
- **Overlays** still load into the image at their own addresses, and residency is still checked by content.

### 2.7 When real structs are allowed (M3)

A subsystem may move its objects into Rust structs only when all of these are proven:
1. The struct's size and every field are known. Today only 56 of 560 structs have a known size.
2. Every access anywhere in the program is typed and comes from the subsystem's own code. No `memcpy`, DMA,
   save/ghost serialisation or other views touch it.
3. No object or field address is stored, compared or hashed, unless an order-preserving handle can replace it.
4. A per-frame state diff (5.6) matches.

M3 is large and risky, and gains little for porting. Keep it out of T3b.

## 3. Hardware access

Game code reaches hardware **through traits at the SDK boundary**: the NitroSDK functions the dictionary already
names. It never uses register addresses. Each trait has two implementations:
- **`DsPlatform`** writes the same registers, in the same order, into `ds_mem::Bus`. This keeps native builds
  comparable with exact ones.
- **Port backends** (PC first) implement the trait natively.

| Unit | Game today | T3b interface | `DsPlatform` (reference) | Port backend |
|---|---|---|---|---|
| Math unit (DIV 0x280, SQRT 0x2B0) | Register writes, busy poll, result reads | Pure `div_s32`, `sqrt_u64` (in `native/math.rs`); `MathUnit` state only if results are read outside the SDK | Register writes, as the `math.rs` adapters do | Integer maths |
| 3D (GX ports, FIFO, GX DMA) | Port writes logged to `Bus::gx`; matrix/test results read back (`geometry_read`) | `Gx3d`: `cmd(op, &params)`, `submit(list)`, `read_clip_matrix()`, `box_test()`, `pos_test()` | Same `(offset, value, bytes)` log | `gx::Gx` + wgpu (already native at the command level) |
| 2D engines | Register writes, snapshot at V-blank | `Gfx2d` named setters (`set_dispcnt(engine, v)`) | Same register writes | Renderer reads a typed state |
| VRAM / palette / OAM | Byte writes, bank mapping (`vram_place`) | `Video`: `vram_bank_mut`, `oam_mut`, `palette_mut`, `map_bank()` | `ds_mem` VRAM, exact mapping | Same bytes, passed to the renderer |
| Sound | SND commands in shared RAM + PXI | `Sound::send_command` at `sound_send_command`; status stays in the shared work area (game-visible state) | Current PXI → `hle7`/driver path | Driver called directly; native sequencer later |
| Input | KEYINPUT 0x130, touch via ARM7 area | `Input::keys()`, `touch()` at frame start | Register/shared-RAM reads | Host controller |
| Time / IRQs | `OS_GetTick`, timers, IME/IE/IF, V-blank handlers | `Clock::tick()`; IRQ state as a Rust struct; V-blank handlers as frame-boundary callbacks | `os_hle::VirtualTime`, exact registers | Same deterministic virtual time |
| DMA | `MI_DmaCopy` etc. | `dma_copy/fill(src, dst, len)` | Channel registers, immediate | `memcpy` |
| Files | FS / card | `Files::read(file, off, buf)` | Card model | `native/fs.rs` (already native) |
| SWI / CP15 | `m.swi`, `m.mrc/mcr` | BIOS functions in Rust; cache ops do nothing; DTCM base is a constant | `bios.rs`, CP15 map | Same |

The generator gets there in two steps:
1. **Named register access.** A store to a constant I/O address prints as
   `g.hw.io_write16(Reg::DISPCNT, v)`, with names from `ds_mem::REGS`. This takes hardware out of the memory model.
2. **SDK-level traits.** These are hand-written for the bottom SDK layer (G3_*, GX_*, MI_*, OS IRQ). Game code
   above that layer only calls them.

**What stays modelled as hardware:** all of `--timing exact`. That is `rt::Cpu`, `ds_mem::Bus`, timers, DMA,
scanlines, the GX log, the ARM7 and budgets, kept for good. Direct/T3b code only runs in native builds, so
`race_diff` against `race_main` keeps proving that the oracle itself is unchanged.

**Threads:** the SDK scheduler and fibers stay. A T3b function can only be switched away from inside a call.

## 4. Incremental path

### 4.1 Steps

| Step | Change | Proof that nothing changed |
|---|---|---|
| S0 plumbing | Generator prints `g: &mut Game` instead of `m`; `Game` wraps the same `ds_mem::Bus` buffers. Renames only | `frame_compare` T3a build vs S0 build: 0 differing frames, no mask |
| S1 frames and returns | Drop push/pop of saved registers; drop `lr` and `bad_return` once all callees are direct; drop unread scratch results (the `rets` mask exists); add `g.frame(n)` | Same, plus the dead-stack mask |
| S2 data access | Send a load/store to `DataImage` when it is proven to be data (typed pointer, global root, `sp` frame, value range); unproven ones stay on the Bus | Same, plus the typed-access audit with 0 unexpected hits |
| S3 hardware | Constant I/O stores become named register calls; SDK leaf natives implement the traits | `frame_compare`, including the polys/PXI/SPU regions |
| S4 symbols | Constant addresses become globals/`Ptr` symbols; the no-address lint passes | Text-only change; race equal |

### 4.2 Pilot order

1. **`code_sys_math`** (121 functions: 85 direct, 78 T3a, 17 T3b). Proves S0–S2 and `MathUnit`. The value cores in
   `math.rs` show the target shape.
2. **Kart physics** (`code_kart`, 386 functions: 132 direct, 86 T3a).
   - It has one root, `*0x0217ACF8`: 8 karts of 0x5A8 bytes each.
   - `frame_compare` already hashes these as `kart0..kart7`, so a difference points straight at one kart and an
     offset.
   - The code is mostly logic and maths.
3. **Items** (`code_item`, 356 functions: 120 direct, 32 T3a). Covers `item_slots`, the object pools, callbacks and
   the item-box event hook.
4. Then race, course, cpu_racer and camera. Graphics-heavy areas (menus, sys_gfx, effects, HUD) come after S3.

### 4.3 How a function moves from T3a to T3b

The generator checks each condition below and writes the first one that fails to `tiers.csv`:
1. The function is T3a.
2. Every callee is T3b, or is reached through a **legacy shim**, `g.legacy_call(addr, args)`. The shim spills to a
   scratch `Cpu` and uses the dispatcher. Functions that need it count as "T3b-pending", not T3b.
3. It writes nothing to the stack except through `g.frame`.
4. Every memory access is a typed data access.
5. It reaches hardware only through traits.
6. Its body contains no DS address literal.

**Mixed code:**
- Old code calls T3b code through the existing `f_<id>_t1` wrapper pattern. The wrapper builds a `Game` over the
  same buffers.
- T3b code calls old code through the shim.
- One rule keeps this safe: **never hold game state in a Rust variable across a call; re-read it through `g`.**
  Generated code already works this way.

## 5. Verification

| Check | Exists | Role in T3b |
|---|---|---|
| Exact race vs `race_main` (`race_diff.py` IDENTICAL) | Yes | Stays IDENTICAL at every step: the reference is untouched |
| Native race (1st, frame 11260) | Yes | Smoke test for each step |
| `frame_compare check`, native T3a vs native T3b, open loop | Yes | **Main gate:** 0 differing logical frames, with only the dead-stack mask |
| Shadow checker (`MKDS_SHADOW=1`) | Leaves only, flat mode | Checks converted leaves; needs extending (below) |
| `tests/t1_differential.rs` | Yes | New "T3b mode": random states; compare writes, results and the order of trait calls |
| `t3_metric.py` | Yes | Merge gate: counts may only go up |

New checks needed:
1. **Dead-stack mask** for `frame_compare`. It is the only newly allowed difference.
2. **Typed-access audit** (debug build). Every `DataImage` access is checked against the struct and global map,
   using roots from `structs.csv` and live blocks from the game's allocator headers. It logs untyped accesses,
   accesses to the wrong struct, and accesses to non-RAM addresses.
3. **Shadow for non-leaves.** Also compare the ordered list of calls each version makes (target and arguments).
   Make it work in fiber mode, where it is bypassed today (noted in `MATH_PILOT.md`).
4. **Hardware trace equality.** `DsPlatform` and the old path must produce the same ordered I/O writes. This uses
   the Block 5.0 `Probe`.
5. **No-address lint.** Fails any T3b function that contains a DS-range hex literal.
6. **State diff (M3 only).** Each frame, serialise the Rust structs back to DS layout and compare them with a
   parallel run that keeps the data in the image.

**Known catch:** natives installed on the dispatcher moved the native finish from frame 11260 to 11262
(`MATH_PILOT.md`, because of per-entry costs). T3b doesn't go through the dispatcher. Even so, the gate must be
logical-frame equality, and any timing that depends on the shape of the code must be removed.

## 6. Costs, risks, decisions

### 6.1 Effort (one lane, rough)

| Stage | Generator does | Hand work | Estimate |
|---|---|---|---|
| S0 plumbing | All | Review | 1 wk |
| S1 frames/returns | All (`preserved_regs`, `rets` exist) | Escaping-frame edge cases | 1–2 wk |
| S2 data access | Most (26k accessor sites of type facts exist) | Telling pointers from integers in hard functions | 2–3 wk tooling, then per area |
| S3 hardware | Named-register step | Traits + SDK leaves: math 1, 3D 2–3, 2D/VRAM 3, sound/input/time/DMA 2 wk | 8–9 wk |
| S4 symbols | All | Naming (dictionary agents) | 1 wk + ongoing |
| Pilots: math, kart, items | — | Fixing what the audit finds | 1 + 2 + 2 wk |
| New checks | — | Tooling | 2–3 wk |
| M3 arenas (optional) | Little | Per subsystem | 2–4 wk each |

The biggest cost isn't in this table: **T3a and T2 coverage**. T3b can only convert functions that are already T3a
and typed.

### 6.2 Risks

- **Pointer/integer confusion.** A wrong `Ptr` type only gives a wrong name. An I/O address sent to `DataImage`
  changes behaviour; the non-RAM panic and the audit catch it.
- **Hidden byte views** (`memcpy`, checksums, save/ghost data). Harmless in M1/M2, but they block M3.
- **Stack tricks** (reads above the frame, stack addresses stored in the heap). Covered because frames keep their
  real addresses.
- **Register access inlined into game code.** S3's named-register step finds these and lists them.
- **Thread switches in the middle of a function.** Native timing rules them out. This has to be proven again if
  the scheduler changes.

### 6.3 Decisions for the owner

1. **T3b = M2:** one byte arena, typed opaque pointers, no addresses in the source. M3 is optional and comes later.
   *Recommended.*
2. **Pilot order:** sys_math, then kart physics, then items. *Recommended.*
3. **Allowed difference:** only the dead-stack mask in `frame_compare`.
4. Should "T3b-pending" (still uses shims) be reported as its own tier in `t3_metric.py`?
5. Should the hardware traits live in the runtime crate or in a new `platform` crate?

### 6.4 Open questions

- Should IRQ handlers stay game code running on a Rust IRQ state, or become host callbacks? Ports without fibers
  (such as WebAssembly) need a cooperative SDK scheduler. Is that part of T3b?
- Is the math unit read anywhere outside SDK functions? If not, `MathUnit` state goes away.
- Does any in-scope game logic read VCOUNT, DISPSTAT or timer counters? The Block 5 census found such reads only at
  safe points; this needs confirming per subsystem.
- How should the address table be versioned so that repeat builds produce identical source (the Block 4 rule)?
- Should typed views over loaded file formats (NKM/KCL course data in heaps) be part of T3b, or come later?
