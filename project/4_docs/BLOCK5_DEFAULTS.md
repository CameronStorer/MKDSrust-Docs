# Block 5: can native become the default? (lane b5-finish, 2026-10-28)

**Recommendation: yes for the hardware switches in the player builds (`play.exe` / `game.exe`), after two small
fixes listed under "Blockers"; keep `exact` as the default of `acceptance.exe` (it is the oracle). Budget-free
timing (`MKDS_TIMING=native`) is ready to become the build default right after, with one listening check.**
Implemented in the defaults follow-up: player hardware and builder timing default to native. Acceptance follows the build's generated timing; build the exact oracle with `--timing exact --with-acceptance`. Native RTC uses host local time, with MKDS_RTC=fixed for deterministic runs.

## What "native" means now
| switch | native behaviour | state |
|---|---|---|
| `MKDS_HW_FS` | ROM-archive reads from the in-memory ROM (`native/fs.rs`) | proven (b5-native) |
| `MKDS_HW_ARM7` | NVRAM, RTC, touch, PM, WM, backup, WVR, CTRDG answered by `hle7::Router` | proven (b5-hle7, b5-native) |
| `MKDS_HW_TIME` | TM0/TM1 on virtual OS time, IRQs at safe points (`os_hle.rs`) | proven (b5-ostime, b5-native) |
| `MKDS_HW_SND` | **no ARM7 CPU at all** (this lane): the ARM7 boot runs once as plain code, the sound driver and the ARM7's interrupt work run event-driven as plain calls | proven here |
| `MKDS_TIMING=native` (build) | no `budget!`, natives free, hardware time only at frame events | proven here |

### ARM7 CPU removed (`MKDS_HW_SND=native`)
- `Arm7::plain_boot` runs the ARM7 from its entry (crt0, autoloads, `arm7_main`: OS, PXI, SND, FS, RTC, WVR, SPI
  init, and each service thread up to its first blocking receive — OS thread switches happen inside the run)
  until the main loop's first halt. 861,345 plain instructions, once, before the ARM9's first frame.
- The boot's four waits on the ARM9 are answered in place (`arm7::boot`): the `PXI_Init` sync-nibble countdown
  (the ARM9's half is answered by `Bus::sync_responder`, 8 → 0 on echo), the CTRDG word wait (skipped; the router
  answers the word later), `os_init_lock`'s wait for the ARM9's lock owner 0x7F (tables written at once, the
  final extension 0xBF deferred until the ARM9 has finished its own lock init — writing it early deadlocks the
  ARM9), and `card_init`'s wait for the ARM9's CARD callback.
- After the boot every tag is claimed by the router. OS (12), CARD (14), MIC (9) and any command without a native
  handler reach the ARM7's own lifted callbacks as plain calls; the SPI service thread's queue is drained as plain
  calls (MIC, and PM/touch/NVRAM commands that reach it); an OS reset request (command 0x10) is acknowledged as
  `os_reset_system` would (sound shut down, 0x10 sent back). `MKDS_SND_BOOT=cpu` keeps the old take-over.
- Result on every route: **ARM7 CPU cycles 0** (`ARM7 lifted cycles 0 interpreted instructions 0`).

### Budget-free timing
- `native::enter` charges nothing when the machine is budget-free (`native::BUDGET_FREE`).
- Frame-event time (`Machine::event_time`, on when budget-free and the ARM7 has no CPU): `Bus::advance`
  (scanlines, V-blank, timers, the ARM7's ticks) runs only in waits (`wait_for_interrupt`, 1000-cycle steps to
  the V-blank or the next OS event) and at listed busy-waits (`os_hle::SAFE_LOOPS`, one `SPIN_QUANTUM` per spin).
  At other slice ends `tick(0)` only exchanges GX commands and PXI words. A guard advances time after 65,536
  slices without a wait (an unlisted spin); it fired 15 times per run, all in load-time decompression / fill
  loops (`MI_ReadUncompLZ8`, `MI_CpuFill32`, `MI_UncompressBackward`), which are compute, not waits.
- Plan 5.4 condition 1 (no time from instruction counts) therefore holds, except for those 15 guard steps.

### Overlay residency (plan 5.4 condition 4)
The session forces a residency re-check at the next slice start after `FS_AfterLoadOverlay` (0x020051F4) is
entered, and the flat loop ends the slice there. Measured with `MKDS_GATE_WATCH`: this game never calls
`FS_LoadOverlay`/`FS_AfterLoadOverlay`; it loads its overlay through its own archive loader
(`fs_request_overlay_archive_load` 0x02059EA4 → `FS_LoadOverlayInfo` 0x020055F0 → …), so the re-check is also
armed at that loader's code-ready step (0x0200583C: data-cache flush, instruction-cache invalidate, BSS clear),
entered once per route. The epoch-based check (watched code writes) stays as the safety net.

## Evidence
Exact build and budget-free build of branch `b5-finish`; races run one at a time.

### Proof races (closed loop, `acceptance rom.nds route.csv OUT 15000`)
Branch `b5-finish` at b061f40 (before merging `block4`'s 5.5 work). "ARM7 CPU" = cycles the ARM7 CPU ran (lifted +
interpreted); "plain" = ARM7 code run as plain calls (boot, sound driver, ARM7 interrupt work).

| build / mode | finish | frames run | IRQs | ARM7 CPU | plain | race_diff vs main |
|---|---|---:|---:|---:|---:|---|
| exact build, default, fiber | 11,462, 1st | 12,362 | 581,521 | 923,441,005 | 0 | **IDENTICAL** |
| exact build, default, flat | 11,462, 1st | 12,362 | 581,521 | 923,441,005 | 0 | **IDENTICAL** |
| exact build, all four `MKDS_HW_*=native` | 11,930, 1st | 12,830 | 602,899 | **0** | 734,309,526 | (different by design) |
| budget-free build, 3 switches (ARM7 CPU still there) | 11,717, 1st | 12,617 | 577,699 | 739,831,720 | 0 | |
| budget-free build, all native, fiber | 11,336, 1st | 12,236 | 580,267 | **0** | 663,070,005 | |
| budget-free build, all native, flat | 11,951, 1st | 12,851 | 604,897 | **0** | 726,651,830 | |

ms per frame (whole acceptance run incl. its captures, back-to-back pairs on a machine shared with other lanes):
exact fiber 27.26 s / 12,362 = **2.21 ms** (31.24 s = 2.53 ms in the other pair); budget-free all native fiber
19.41 s / 12,236 = **1.59 ms** (19.63 s = 1.60 ms). About 28% less CPU per frame than exact (b5-native's
budget-free build with the ARM7 CPU: 1.84 ms). The CPU-less ARM7 still runs the lifted sound driver (663 M plain
instructions per race, about 54 K per frame); that is the next cost to remove.

After merging `block4` (with b5-spill's 5.5 emitter work), same races on the merged tree (machine busy, so only
the relative numbers matter): exact fiber and flat **IDENTICAL** (1,707,950,080 instructions, 581,521 IRQs,
finish 11,462 1st); all four switches finish 11,930 1st with ARM7 CPU 0; budget-free all native finishes
11,260 (fiber) / 11,533 (flat), 1st, ARM7 CPU 0, 96 / 94 busy-wait time steps and 15 guard steps each.

### Open-loop equality with the exact model (seed-pinned, `MKDS_TICK_PIN`)
Masks in `masks/` (`native_all.txt` plus per-mode files; kart entries are now kart-relative,
`kart +0xC-+0x18`, so one file serves every course). n4 = exact-timing build with all four `MKDS_HW_*=native`;
bf = budget-free build, all native.

| route | frames compared | n4 equal | bf equal | lead (n4 / bf) | notes |
|---|---:|---:|---:|---|---|
| GP race (reference inputs) | 10,082 (race) | **10,082** | **10,082** | 4 / 27 | finish 11,457 / 11,433 (= 11,462 − lead), 1st |
| Mission 1-1 | 3,100 (from 1700) | **3,100** | **3,100** | 4 / 28 | |
| Menus walk | 1,769 game frames (from 1000) | 1,340 | 1,595 | by game frame | rest: screen transitions (load speed, exact lag frames) |
| Balloon battle | — | diverges | diverges | — | exact model lags (111 lag frames), see below |

- **Battle** is not comparable per frame, by design (plan 5.3, "Lag frames"): the exact model overruns frames on
  the "Nintendo DS" stage with 7 CPU karts (111 lag frames in 6,500, about one in 40 during play); native timing
  never lags. The runs are equal until the first in-play lag frame (logical 2341) and differ afterwards. Native
  battle runs finish their 6,500 frames without errors, with PM commands served through the SPI-queue path.
- **Menus**: comparing by game frame (inputs re-keyed with `inputs/rekey.py`), the differences are the frames
  around screen changes (native loads and saves faster; the exact model has 25 lag frames in menus) and a menu
  sprite animation phase that counts V-blanks (masked in `native_menus.txt`).
- Without the seed pin the race RNG seeds come from `OS_GetTick` and differ (expected, see
  `masks/native_seed_equalized.md`); every closed-loop native race still finishes 1st.

### Census (`BLOCK5_CENSUS.md`, new section)
Battle, mission and menus show no VCOUNT/TM1–3 reads, no DISPSTAT reads after boot, no H-blank/V-count IRQs and
no new busy-waits: plan 5.4 condition 2 holds on all four routes.

## Blockers before flipping the player default
1. **RTC is a fixed clock** in `hle7` (replays must be deterministic). A player build should read the host clock
   (keep the fixed clock under `acceptance`/replays). Small change in `hle7::Router::rtc`.
2. **Acceptance must stay exact.** The `race_diff ... IDENTICAL` proof and the oracle need the exact model; flip
   the default only in `play.exe`/`game.exe` (or have `acceptance` set `MKDS_HW_*=exact` unless told otherwise).

## Not blockers, but known
- Audio of the CPU-less ARM7 was not re-listened in this lane (the driver code and tick model are b5-sound's,
  which passed its message/SPU oracle and RMS check); do one listening pass before shipping.
- Wireless (Nintendo WFC, multiplayer) is not available natively; the exact model stalls at the WFC menu too.
- The microphone: MIC commands go to the lifted ARM7 code (plain calls, SPI queue); no route sends one, so the
  native MIC path is exercised only by unit-level reasoning, not by a run.
- CPU per frame: see the table above. The ARM7 sound driver still runs as lifted code (plain calls) and is now
  the largest cost after the ARM9 itself; a native sequencer (plan 5.2b, "later option") is the next big win.
- `spill!/reload!` (5.5) are untouched.

## Reproduce

Build the acceptance oracle with the builder's --timing exact --with-acceptance options (or set MKDS_TIMING=exact). Keep MKDS_RTC=fixed for proofs, recordings and replays. Set all four hardware switches explicitly for native comparisons.
```
# exact, logging the seed ticks; then native with the log; inputs re-keyed by the load lead
acceptance rom.nds - OUT_EX N --record OUT_EX/rec --replay inputs/mission.csv --mask masks/native_all.txt   # env MKDS_TICK_PIN=log
grep MKDS_TICK_PIN OUT_EX.log > ticks.txt
python inputs/lead.py OUT_EX/rec OUT_N/rec 1700 4700          # lead after a first native run
python inputs/shift.py inputs/mission.csv mission_m4.csv 1650 4
acceptance rom.nds - OUT_N N --record OUT_N/rec --replay mission_m4.csv --mask masks/native_all.txt   # env MKDS_TICK_PIN=ticks.txt MKDS_HW_SND=native ...
python masks/region_cmp.py OUT_EX/rec OUT_N/rec --mask masks/native_mission.txt --from 1700 --offset 4
# menus / battle: python inputs/rekey.py OUT_EX/rec OUT_N/rec inputs/menus.csv menus_n.csv; compare with --by-index
# screenshots for writing scripts: MKDS_SHOT_FRAMES=a,b,.. (PNG files in the --record directory)
```
