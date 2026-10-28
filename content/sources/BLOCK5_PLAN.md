# Block 5: from emulated DS hardware to a native game

## Status (2026-10-28)

| Stage | State and evidence |
|---|---|
| 5.0 Oracle harness and census | **Done, merged** (`b11c7fd`, `fcc3647`, `77cb9c1`). [Census](BLOCK5_CENSUS.md): exact/exact replay equal over 12,045 logical frames; flat/fiber equal; deliberate perturbations detected. Battle, missions and more menus remain to be covered |
| 5.1 Native FS | **Done, merged**, behind `MKDS_HW_FS=native` (`b457b54`, `4cc57a8`) |
| 5.2a ARM7 PXI services | **Done, merged**, behind `MKDS_HW_ARM7=native` (`c9d8876`, `0b88736`) |
| 5.2b Event-driven sound driver | **Done, merged**, behind `MKDS_HW_SND=native` (`2751159`, `55cf172`); IRQ scheduling refined in `db4c388`, `9776f2e`. Runs the translated driver on events; a complete native sound rewrite remains future work |
| 5.3 OS time and IRQs | **Done, merged**, behind `MKDS_HW_TIME=native` (`76efc25`, `3e99cb5`) |
| 5.4 Remove budgets | **Working opt-in build; finish work in progress** (`16b1476`, `d2d4bff`, `fb7f97a`, merged by `4286f4b`). Build with `MKDS_TIMING=native` / generator `--timing native`: 122,736 ARM9 budget sites empty, 4,164 poll sites retained. Closed-loop races finish 1st at frame 11,698 (fiber) / 11,711 (flat); 1.84/1.78 ms per frame versus exact 2.31/2.22, about **20% less CPU per frame** |
| 5.5 Remove spill/reload | **In progress**; the no-spill calling convention and per-thread register requirements below remain completion criteria |
| 5.6 Presentation extras | **Planned, optional** |

The [seed-equalized proof](masks/native_seed_equalized.md) (`fb7f97a`) reports equality in every unmasked region for all compared race frames: TIME **10,079/10,079**, ARM7 **10,082/10,082**, FS **10,077/10,077**, all three **10,081/10,081**, budget-free **10,078/10,078**. It uses test-only `MKDS_TICK_PIN`, a documented mask, re-keyed inputs and loading leads of 4 frames (FS/all three) or 18 (budget-free). Open-loop finishes are 11,462 (TIME/ARM7), 11,458 (FS/all three), and 11,444 (budget-free), all 1st. Without seed pinning the all-three control has 0/10,081 equal frames and does not finish. This proof covers FS/ARM7/TIME, not the separately merged SND switch.

5.4 finish work remains: the proof build retains ARM7 sound CPU execution and cycle-driven hardware advancement in waits; overlay residency uses `code_epoch` dispatch/slice checks rather than the planned `FS_AfterLoadOverlay` hook. Broader corpus validation, frame-event-only advancement and default promotion remain. Native modes stay opt-in. The inventory, stage designs and effort estimates below describe the original exact baseline and plan; this status records what has landed.

## Goal
Today the translated game runs inside a cycle-counted model of the DS: `Session::step` (`2_native_game/src/session.rs`)
runs ≤32-instruction slices, charges them through `budget!(pc, n)` in every raised block, then `Machine::tick`
(`machine.rs`) advances `ds_mem::Bus::advance` (scanlines, timers, DMA, IRQ flags), feeds the GX command log to
`gx::Gx` (`sync_gx`) and runs the ARM7 (`Arm7::run`, lifted ARM7 code plus `spu.rs`). A "frame" is
`hw.cycles / FRAME_CYCLES`. Raised code keeps its locals in sync with `c.r` (`spill!/reload!`) because IRQs, thread
switches and T0 code can observe the register file at any block.

Block 5 replaces that model with native services at the **library boundary** (NitroSDK / NitroSystem functions the
dictionary already names), so the generated source can drop `budget!`/`spill!`/`reload!` and run as an ordinary
program: a frame loop driven by the game's own V-blank wait, OS services on the host, sound driven by events instead
of a second CPU, files read from the user's ROM.

Rules (unchanged from Blocks 2–4): no Nintendo material in the repo; every replacement is switchable and verified
against the exact model before it becomes the default; nothing is pushed without the owner's go-ahead.

## What exists (inventory, 2026-10-27)
| Unit | Where | Model today | Block 5 fate |
|---|---|---|---|
| ARM9 run loop | `session.rs` `step`/`step_fibered`, `fibered.rs` (`run_slice`, `Guest::end_slice`, `irq_taken`) | 32-instr slices; IRQ taken at any slice end; one fiber per SDK thread (`CURRENT_THREAD_PTR` 0x0216FF34) | Frame scheduler; IRQs at safe points; fibers stay |
| Time | `ds_mem.rs` `Bus::advance`, `BUS_HZ`, `CYCLES_PER_LINE`, `LINES`; `session::FRAME_CYCLES` | Instruction count → bus cycles → scanlines | Virtual time = logical frame + fixed intra-frame events |
| IRQ controller | `ds_mem.rs` `raise`, `irq_pending`; `rt::take_irq`, `rt::ARM9_IRQ_STUB` | Exact IME/IE/IF | Kept as data; delivery only at safe points |
| Timers / DMA | `ds_mem.rs` `Timer`, `Dma`, `run_dma`, `trigger_dma` | Cycle-exact; GX-FIFO and immediate DMA run straight through | Timers virtualised behind OS_Tick/OS_Alarm HLE; DMA stays immediate |
| BIOS | `bios.rs` `swi` (Wait → `Machine::wait_for_interrupt`), wrapper `swi_vblank_intr_wait` 0x02000142 | HLE already | V-blank wait becomes the frame boundary |
| 3D | `gx.rs` (`Gx::write`, `matrix_result`), `raster.rs`, `native/src/gpu/three_d.rs` | Port-write log → polygons → wgpu renderer | Already native at the G3 command level; add direct list submit and an NNS_G3d hook later |
| 2D | `gfx2d.rs`, `native/src/gpu/two_d.rs`, `compose.rs` | Register/VRAM snapshot per frame, GPU compute | Stays register-level (it is already native-speed); snapshot taken at the V-blank wait |
| ARM7 | `arm7.rs` (`Arm7::run`, `run_cpu`, `State7::poll`, `tick_timers`), lifted ARM7 table | Second CPU, 64-cycle bursts interleaved with every ARM9 slice | Replaced by PXI service HLE (`hle7/`) |
| Sound | `spu.rs` (16 channels, device-rate mixer), ARM7 SND driver (lifted) | SPU registers written by lifted ARM7 code | Driver runs event-driven, later native |
| IPC/PXI | `ds_mem.rs` `ipc_out`, `fifo_in`, `arm7_send`, `arm7_set_sync`, `arm7_announce_ready`, `arm7_lle`; `Machine::arm7_hle_boot` | FIFO + sync nibble; an older stand-in seam still exists | The HLE seam is revived as the PXI router |
| Peripherals | `peripherals.rs` (`Spi` touch/PM/firmware, `Rtc`, `Backup`) | Byte-level SPI | Reused as backends of native TP/RTC/PM/NVRAM/backup services |
| Card | `card.rs` (`0xB7` reads, card IRQ `IRQ_CARD_DONE`) | Register-level, from the user's ROM | Native FS read at the SDK boundary |
| Natives | `src/native/mod.rs` (`Native`, `enter`, `ret`, `VERIFIED`), `Dispatcher::set_natives`, `Machine::hook` | 10 verified leaves | The mechanism for all SDK HLE |
| Proof | `native/src/bin/race_check.rs` (→ `acceptance.exe`), `shadow.rs`, `MKDS_SLICE_TRACE`, `render_compare` | Bit-identical race vs `main` (1,707,950,080 instr, 581,521 IRQs, finish frame 11,462, 1st) | Kept as the oracle; new logical-frame comparison |

Dictionary entry points used below (`dictionary/sdk_functions.csv`, `game_names.csv`; confidence mostly `likely`):
- OS: `OS_WaitIrq` 0x0200C894, `OS_SetIrqFunction` 0x0200CB50, `OS_Rescheduler` 0x0200DE50, `OS_WakeupThread`
  0x0200DF9C, `OS_SleepThread` 0x0200E01C, `OS_SaveContext` 0x0200E6EC, `OS_LoadContext` 0x0200E738, `OS_GetTick`
  0x0200F5AC, `OS_InitTick` 0x0200F6F4, `OS_SetAlarm` 0x0200F950, `OS_CancelAlarm` 0x0200F8B8, `OS_InitAlarm`
  0x0200FB28, V-count alarms `os_initvalarm_0200fc1c`, IRQ dispatcher `itcm_os_irq_dispatcher_…_01ff8000`, reschedule at
  IRQ exit `itcm_os_thread_reschedule_at_irq_exit_01ff8058`, game V-blank hooks `os_install_vblank_handler` 0x021D2DBD.
- FS: `FS_OpenFile` 0x02004A30, `FS_SeekFile` 0x02004840, `FS_ReadFile` 0x020048AC, `FS_ReadFileAsync` 0x020048BC,
  `FS_WaitAsync` 0x02004918, `FS_LoadOverlay` 0x02005144, `FS_AfterLoadOverlay` 0x020051F4, `fs_get_file_rom_offset`
  0x020182C0. **Gap:** the ROM-archive read callback / CARD ROM read entry is not yet named.
- Sound, ARM9 side: `sound_send_command` 0x020207EC (+ `sound_set_*`, `sound_send_command2x_maybe`),
  `sound_init_pxi_callback` 0x02020F84, `sound_receive_pxi_alarm` 0x02020FF0, `sound_check_arm7_fifo_ready` 0x02020EB0.
- ARM7: `pxi_fifo_recv_irq_handler` 0x037FB4D4, `pxi_set_fifo_recv_callback` 0x037FB6C0, `os_pxi_command_callback`
  0x037FB098, `snd_thread_main` 0x037FC1C8, `snd_seq_main` 0x037FEEB4, `snd_pxi_send_reply` 0x037FF3D0, plus
  125 `snd_*`, 9 `tp_*`, 36 `rtc_*`, 17 `pm_*`, 23 `nvram_*`, 24 `card_*`, 8 `mic_*`, 133 `wm_*` / 352 `wl_*`.
- 3D: `NNS_G3dDraw` 0x01FF8CF0, `NNS_G3dFuncSbc_{NODE,MTX,MAT,…}` 0x01FF8xxx (ITCM), GX DMA
  `mi_start_geometry_dma_restore_irq_maybe` 0x01FFFEF4; ~50 `nitrosdk_gx_*_unnamed` rows still need real names.

## References (public, ideas only)
- **GBATEK**: IPC sync/FIFO, SPU channel registers, V-count/V-blank timing, 3D command semantics. Already the basis of
  `ds_mem.rs`, `spu.rs`, `gx.rs`.
- **melonDS / DeSmuME**: both emulate the ARM7 at instruction level and spend much of their cost on keeping the two CPUs
  in lock-step; melonDS separates the geometry engine from interchangeable renderers (software / OpenGL / compute),
  the same split we already have (`gx.rs` → `three_d.rs`). Lesson: our renderer is not the problem; CPU lock-step is.
- **N64Recomp + N64ModernRuntime ("ultramodern")**: static recompilation plus a host re-implementation of the console
  OS (threads, message queues, timers, VI retrace) at the libultra boundary; the recompiled game never sees cycle
  timing. **RT64** consumes the game's display lists (HLE at the graphics-microcode boundary) and adds widescreen,
  high frame rate (matrix interpolation) and HD replacement on top. Our analogue: OS_* HLE = ultramodern; the GX command
  stream + `NNS_G3dDraw` = display lists.
- **NitroSDK architecture (publicly documented behaviour)**: the ARM9 SND library queues commands in main memory and
  sends them to the ARM7 over PXI; the ARM7 driver runs the sequencer on a fixed tick (~5.2 ms, ≈3.2 per frame) and
  publishes player/channel status in a shared work area the ARM9 polls. The ARM9 does not depend on *when* inside a
  frame that happens, only on order. This is what makes an event-driven ARM7 viable.

## Key decision: give up cycle identity, keep logical-frame identity
Every stage below changes instruction interleaving, so the Block 4 proof (bit-identical instruction and IRQ counts)
cannot survive Block 5. The new invariant is **logical-frame equivalence**: with the same open-loop input script keyed
by the game's own V-blank counter, the game state and the render input at the start of every logical frame are equal
to the exact model's, outside a recorded, justified mask (tick counters, driver work areas). The exact model stays in
the tree as the oracle (`--hw exact`), forever, the way `--renderer software` stayed after Block 2.

## Stages (ordered for fastest visible progress)
Each stage has a runtime switch `MKDS_HW_<UNIT>=exact|native` (default `exact` until its acceptance passes, then
flipped). Effort is in agent-weeks of one lane, assuming the harness (5.0) exists.

### 5.0 Oracle harness and census (1.5 wk, starts first, never blocks other lanes for long)
- **Logical frame**: `Session::logical_frame()` = the SDK's V-blank count (the counter the OS V-blank handler
  increments; locate it via `OS_WaitIrq`/V-blank handler xrefs) instead of `hw.cycles / FRAME_CYCLES`.
- **Recorder** (`race_check.rs` gains `--record DIR`): per logical frame write (a) input applied, (b) a hash of
  game RAM split by region (`dictionary/globals.csv` + `structs.csv` roots: kart array via 0x0217ACF8, race manager via
  0x021755FC, item/effect pools, RNG state), (c) the render input: hash of `frame_polys` + `RenderSnapshot::encode()`
  2D part, (d) the PXI traffic (`ipc_out`, `fifo_in`, sync nibble) and SPU register writes, each tagged with the frame.
- **Replayer** `native/src/bin/frame_compare.rs`: runs a build open-loop from `inputs.csv` (no route steering, so
  divergence cannot self-correct) and reports the first differing frame and region; `--mask FILE` lists allowed
  addresses with a reason. Reuses `render_compare` for pixels.
- **Census** (exact model, full race + menus + battle + mission): histogram per logical frame of IRQ sources taken
  (IF bits in `fibered.rs::irq_taken`), MMIO reads of VCOUNT/DISPSTAT/TMxCNT_L/IPC/GXSTAT (polling), H-blank DMA,
  mid-frame 2D register writes, lag frames (V-blank wait not reached within one frame of cycles), card IRQs, and the
  pc of every busy-wait loop longer than 1,000 instructions. Output `4_docs/BLOCK5_CENSUS.md`. **This decides how much
  of 5.3/5.4 is mechanical and how much needs per-site work.**
- Done when: exact vs exact replays are 100% equal; a deliberately perturbed build (e.g. `OS_GetTick` +1) is caught at
  the right frame and region.

### 5.1 Files from the user's ROM (1 wk) — visible: no loading stalls
- Replace: the FS ROM-archive read path. Boundary: the archive read callback that `FS_ReadFile`/`FS_ReadFileAsync`
  end in (name it in the dictionary first; fallback boundary is `FS_ReadFile` itself with the `FSFile` position fields
  from `structs.csv`). Native: copy from the in-memory ROM (already loaded for `card.rs`) synchronously, complete the
  async request immediately (`FS_WaitAsync` returns at once). Overlay loads: after `FS_AfterLoadOverlay`, call
  `Session::update_residency` explicitly instead of relying on the "code written" slice end.
- Files: new `src/native/fs.rs`, registered in `native::NATIVE`; `card.rs` stays for the exact model.
- Verify: shadow checker is not enough (DMA/IRQ side effects), so use 5.0 replay: equal game state per frame with a mask
  only for card-driver internals; plus a unit test that every FAT entry read natively equals `assets/files/…`.

### 5.2 ARM7 → PXI service HLE (4 wk, two sub-lanes) — visible: ~0.2–0.4 core less, no ARM7 errors
The ARM9 only talks to the ARM7 through PXI (`IPCFIFOSEND` → `ds_mem::Bus::ipc_out`, replies via `arm7_send`,
`arm7_set_sync`) and shared main memory. Replace the CPU with a **PXI router** in a new module `src/hle7/`
(`mod.rs` router keyed by PXI tag; services below), installed when `Bus::arm7_lle == false` (the old seam).
- **5.2a Small services, native** (1.5 wk): touch (`tp_*` → `Machine::set_input` touch, calibration from
  `peripherals::CAL_*`), RTC (`rtc_*` → host clock, or fixed for replays), power (`pm_*`: backlight, LED, sound amp =
  no-ops with correct replies), NVRAM/firmware user settings (`nvram_*` → `peripherals::synthetic_firmware`), backup
  memory (`card_*` save commands → `peripherals::Backup`, `.sav` on disk), mic (`mic_*` → silence), OS/system tag
  (boot handshake `arm7_announce_ready`, `Machine::arm7_hle_boot`). WiFi/WM (`wm_*`, `wl_*`): "wireless not
  available" replies; local multiplayer is out of scope for Block 5.
- **5.2b Sound, event-driven** (2.5 wk): keep the *lifted* ARM7 SND driver code but stop running it as a CPU. The
  router delivers each SND PXI command by calling the driver's receive callback (`os_pxi_command_callback` /
  the SND callback it registers) to completion, and runs one driver tick (`snd_thread_main` body / `snd_seq_main`)
  every 5.2 ms of virtual time from a fractional accumulator (3–4 per frame). The ARM7 code runs as plain function
  calls on a private `rt::Cpu` with no budget (it is already T1-raised; `budget!` there becomes a no-op under
  `MKDS_HW_ARM7=native`). SPU writes go to `spu.rs`; audio is rendered per tick, not per ARM7 burst.
  A fully native sequencer (SSEQ/SBNK/SWAR interpreter in Rust) is **not** needed for Block 5; it is a later option.
- Replace in `arm7.rs`: `Arm7::run`/`run_cpu` and `State7::poll` are bypassed; `Machine::run_arm7` calls
  `hle7::Router::advance(frame_time)` instead.
- Verify: (1) message-level oracle: the 5.0 recording of PXI words in the exact model is replayed into `hle7` alone;
  replies and shared-memory writes must match in order (timestamps ignored). (2) SPU oracle: the sequence of SPU
  register writes per driver tick must equal the exact model's, given the same command stream. (3) Full replay: game
  state equal per logical frame, mask = ARM7 WRAM and the SND shared work area's timing fields. (4) Audio: RMS
  difference vs exact-model capture under a threshold, plus listening check.

### 5.3 OS time and interrupts on the host (3 wk) — visible: frame pacing locked to display/audio, lower latency
- **Frame boundary**: `swi_vblank_intr_wait` (0x02000142, BIOS `Swi::Wait` in `bios.rs`) and `OS_WaitIrq(VBLANK)`
  become the frame end: present the render snapshot, run the frame's scheduled events, raise V-blank, then deliver the
  IRQ (dispatcher at 0x01FF8000 as a nested call, as `fibered.rs::irq_taken` already does). Host pacing: display vsync
  with ±0.5% dynamic audio resampling (`native/src/audio.rs`), or audio-clock pacing when vsync is off.
- **Timers**: `OS_GetTick` → virtual ticks = frame start tick + a deterministic per-call increment (keeps replays
  exact; host time only in a "free-running" option). `OS_SetAlarm`/`OS_CancelAlarm` → host alarm queue fired at the
  next safe point whose virtual time has passed. V-count alarms (`os_initvalarm`) → fired at their line's position in
  the frame's fixed event list (only if the census finds users).
- **Other IRQ sources**: GX FIFO (already immediate, never pending), card (gone after 5.1), IPC (synchronous after
  5.2), keypad (input applied at frame start), H-blank/V-count (census; if only used for effects, emulate the effect
  in the 2D snapshot instead).
- **Safe points**: IRQs are delivered only at (a) wait calls (`Swi::Wait`, `OS_WaitIrq`, `OS_SleepThread` idle,
  CP15 wait-for-interrupt in `Machine::mcr`), (b) `OS_RestoreInterrupts`/`OS_EnableIrq` when they re-enable with IF
  pending, (c) busy-wait loops listed in `dictionary/safe_points.csv` (from the census), where the generator emits
  `m.poll()` on the loop's back edge. A watchdog (`MKDS_WATCHDOG`, N million instructions without a safe point)
  reports new loops instead of hanging.
- Threads: the SDK scheduler (`OS_Rescheduler`, `OS_SaveContext`/`OS_LoadContext`) keeps running as game code;
  `fibered.rs` already maps SDK threads to fibers. Switches now happen only at safe points.
- Files: `session.rs` (new `step_frame`), `fibered.rs` (`irq_taken` gated by safe point), `machine.rs`
  (`wait_for_interrupt` → frame end; `tick` no longer called per slice), `ds_mem.rs` (`advance` called once per frame
  with the event list), new `src/os_hle.rs` + `src/native/os.rs`.
- Verify: 5.0 replay, equal per logical frame; expected diffs only in tick-derived values (masked, each justified).
  Lag frames in the census are the main risk: where the exact model overran a frame, native timing will not; record
  those frames as known differences and check the game recovers to equal state.

### 5.4 Remove `budget!` (2 wk, after 5.1–5.3 are default)
Condition (all must hold, checked by the census and a build-time report):
1. No hardware unit derives time from instruction counts: 5.1, 5.2, 5.3 are on; `Bus::advance` is only called at
   frame events.
2. No code observes cycle timing: no reads of TMxCNT_L counters, VCOUNT or DISPSTAT outside the safe-point list and
   the OS HLE; no H-blank DMA.
3. IRQs and thread switches are delivered only at safe points (5.3), so nothing needs a preemption point inside a block.
4. Overlay residency is re-checked at `FS_AfterLoadOverlay`, not at "code written" slice ends.
Then: `raise_emit.rs` emits `budget!` as nothing under a new `--timing native` generator flag (macro definition at the
`macro_rules! budget` line); `native::enter` stops charging; `Session::step` becomes `step_frame` (run until the
frame-end safe point). The flat loop (`MKDS_FLAT`) and the exact model stay for `--hw exact` builds.
Verify: 5.0 replay equal to 5.3's result frame-for-frame (removing budget must change nothing once 1–4 hold); race to
results; CPU per frame measured.

### 5.5 Remove `spill!/reload!` (2–3 wk, depends on Block 4 T1 coverage)
`c.r` then remains only as the calling convention between raised and T0 code. Condition:
1. 5.4 done (no IRQ or switch can observe a raised function's registers mid-block).
2. IRQ handlers entered only at safe points, which are calls: the interrupted function's live values sit in Rust
   locals; callee-saved registers are preserved by the handler (checked by the T1 calling-convention check).
3. Each fiber owns its `rt::Cpu` (today one `Session::cpu`), so `OS_SaveContext`/`OS_LoadContext` save and restore a
   per-thread register file, not the raised code's locals; or those two become natives that only switch fibers.
4. The callee is raised with a known signature (`recomp::signature`); calls to T0 holdouts keep a spill limited to
   r0–r3/sp/lr at that call site.
Then the emitter passes arguments as Rust parameters and returns values (`f(g, a, b) -> r`), the T2 shape Block 4
aims for. Verify: same as 5.4, plus `tests/t1_differential.rs` extended to "no-spill" mode.

### 5.6 Native presentation extras (optional, 4+ wk, parallel after 5.3)
- Direct GX submission: hook GX DMA (`mi_start_geometry_dma_restore_irq_maybe`) and the G3 immediate setters to hand
  whole command lists to `gx::Gx::feed_log` without the per-word `Bus::gx` log.
- Scene graph: hook `NNS_G3dDraw` and the `NNS_G3dFuncSbc_*` handlers to tag polygons with model/node/material ids
  (render input unchanged, so `render_compare` still proves it), enabling HD model/texture replacement, widescreen
  (projection from `G3_Perspective`-style setup plus 2D/HUD layout), and 120/144 Hz output by interpolating matrices
  between logical frames (RT64's approach).

## Verification summary
| Level | Tool | Used by |
|---|---|---|
| Exact (cycle) | `acceptance.exe` race vs `main`, `MKDS_SLICE_TRACE` | Unchanged for `--hw exact`; regression guard for the oracle itself |
| Function | `shadow.rs` (leaf natives) | 5.1 helpers, OS leaf natives (`OS_GetTick` with masked return) |
| Message | PXI/SPU stream replay into `hle7` | 5.2 |
| Logical frame | `frame_compare` replay (state hashes + render input + mask) | 5.1–5.5 acceptance |
| Pixels | `render_compare` on corpus | 5.6 |
| Live | windowed race to results, `--stats` cores/frame | Every stage before flipping its default |

## Parallel work packages
| WP | Lane | Entry points | Depends on | Effort |
|---|---|---|---|---|
| WP-A | ARM7 → `hle7` PXI router; 5.2a small services | `arm7.rs` `Arm7::run`/`State7::poll`; `ds_mem.rs` `ipc_out`/`arm7_send`/`arm7_set_sync`/`arm7_lle`; `peripherals.rs`; ARM7 rows in `game_names.csv` (`pxi_*`, `tp_*`, `rtc_*`, `pm_*`, `nvram_*`, `card_*`) | 5.0 PXI recording (can start with a stub recorder) | 1.5 wk |
| WP-B | Event-driven SND driver (5.2b) | `snd_thread_main` 0x037FC1C8, `snd_seq_main` 0x037FEEB4, `os_pxi_command_callback` 0x037FB098, `spu.rs`, `Machine::run_arm7` | WP-A router | 2.5 wk |
| WP-C | OS time/IRQ scheduler (5.3) | `session.rs` `step`/`step_fibered`, `fibered.rs` `irq_taken`/`end_slice`, `machine.rs` `wait_for_interrupt`/`tick`, `bios.rs` `Swi::Wait`, `OS_GetTick`/`OS_SetAlarm`/`OS_WaitIrq` | 5.0 census | 3 wk |
| WP-D | Oracle harness + census (5.0) | `race_check.rs`, new `bin/frame_compare.rs`, `fibered.rs::irq_taken` counters, `ds_mem.rs` MMIO read hooks | none | 1.5 wk |
| WP-E | Native FS (5.1) + dictionary gap (ROM archive read callback, `nitrosdk_gx_*_unnamed` names) | `src/native/fs.rs`, `card.rs`, `FS_ReadFile` 0x020048AC, `FS_AfterLoadOverlay` 0x020051F4 | 5.0 replay | 1 wk |
| WP-F | Emitter: `budget!` then `spill!` removal (5.4, 5.5) | `raise_emit.rs` macro block (`macro_rules! spill/reload/budget`), `native/mod.rs` `enter`, `tests/t1_differential.rs` | A–E default on; Block 4 T1 | 4–5 wk |
| WP-G | Presentation extras (5.6) | `gx.rs`, `native/src/gpu/three_d.rs`, `NNS_G3dDraw` 0x01FF8CF0 | 5.3 | 4+ wk |

File ownership keeps lanes from colliding: WP-A/B own `arm7.rs` + `src/hle7/`; WP-C owns `session.rs`, `fibered.rs`,
`machine.rs`; WP-D owns `bin/` tools; WP-E owns `src/native/fs.rs` and dictionary rows; WP-F owns `raise_emit.rs`.
Shared touch points (`ds_mem.rs` hooks, `native::NATIVE`) are merged by the integrating lane (agent-lift).

## Schedule (3–4 lanes)
| Week | Lane 1 | Lane 2 | Lane 3 |
|---|---|---|---|
| 1–2 | WP-D harness + census | WP-A router + small services | WP-E native FS |
| 3–5 | WP-C scheduler | WP-B SND event-driven | dictionary gaps; WP-G prep |
| 6–7 | flip defaults (5.1–5.3), acceptance | WP-F `budget!` removal | WP-G (optional) |
| 8–10 | WP-F `spill!` removal (needs Block 4 T1 ≥ 95%) | | |
Total: ~8 weeks to a budget-free native game with 3 lanes; `spill!` removal tracks Block 4.

## Risks
- **Lag frames / timing-dependent logic.** If the census shows frames where the exact model overran, native timing
  will differ there by design; treat as accepted differences, prove recovery.
- **Hidden polling loops.** Mitigated by the census, `safe_points.csv` and the watchdog.
- **RNG or logic seeded from ticks.** Deterministic virtual ticks keep replays exact; free-running ticks only as an option.
- **Overlays rewriting code mid-frame.** Residency check moves to `FS_AfterLoadOverlay`; keep the content-hash verify.
- **WiFi.** Stubbed; any future local multiplayer needs a WM HLE over UDP (separate block).

## Block 5 is done when
- `--hw native` is the default; the shipped game has no ARM7 CPU, no per-slice `Machine::tick`, no `budget!`.
- An open-loop replay of the acceptance race, battle, a mission and the menus is equal to the exact model per logical
  frame outside the documented mask, and the closed-loop race finishes 1st.
- `spill!/reload!` remain only at calls into listed T0 holdouts.
- `--hw exact` still reproduces the Block 4 baseline bit for bit.
- The repo still contains no Nintendo material.
