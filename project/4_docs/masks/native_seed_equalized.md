# Seed-equalized proof of the native switches (lane b5-native, 2026-10-27)

Acceptance evidence for flipping `MKDS_HW_FS`, `MKDS_HW_ARM7` and `MKDS_HW_TIME` to `native`, and the first
5.4 (budget-free) result. Mask: `native_seed_equalized.txt` (beside this file).

## Method
- **Seed pin** (`MKDS_TICK_PIN`, test only, `os_hle::TickPin`): the race seeds its RNGs from `OS_GetTick`
  (`course_init_checkpoint_progress` 0x020401AC stores tick mixes into the race manager's RNG states +0x47C
  and +0x498; race setup and the menus' random picks do the same, `os_hle::TICK_SEED_SITES`). The exact run
  logs those results (`MKDS_TICK_PIN=log`, 20 calls in the reference route), the native run returns the
  logged values at the same call sites (`MKDS_TICK_PIN=<log file>`). Nothing else is changed.
- **Open loop**: `frame_compare replay` of the reference inputs (`b5-harness` recording, 250 rows), 12,100
  frames, with `--mask native_seed_equalized.txt` on both runs.
- **Load lead**: native loads finish earlier, so the race starts earlier in V-blank count: FS native and
  all three switches by 4 logical frames, the budget-free build by 18. Inputs from the race load on are
  re-keyed by that lead (`inputs.csv` rows >= 1976 minus 4, >= 1963 minus 18), and frame f of the exact run
  is compared with frame f - lead (`region_cmp.py --offset`). ARM7 and TIME native alone have no race lead.
- Regions: the 5.0 recorder's (karts, race manager, item slots, object RNG, race config, records,
  controllers, DTCM/ITCM, main RAM per 64 KB, 2D/3D I/O, palette, OAM, VRAM, polygons, PXI, SPU).

## Results (race: logical frames 1980..12063, all unmasked regions)
| run | finish (open loop) | frames compared | equal in every unmasked region | kart0-7, race_manager, item_slots, object_rng |
|---|---|---:|---:|---|
| exact (log) | 11,462, 1st | | | |
| `MKDS_HW_TIME=native` | 11,462, 1st | 10,079 | **10,079** | equal every frame |
| `MKDS_HW_ARM7=native` | 11,462, 1st | 10,082 | **10,082** | equal every frame |
| `MKDS_HW_FS=native` (lead 4) | 11,458, 1st | 10,077 | **10,077** | equal every frame |
| all three (lead 4) | 11,458, 1st | 10,081 | **10,081** | equal every frame |
| all three, budget-free 5.4 build (lead 18) | 11,444, 1st | 10,078 | **10,078** | equal every frame |
| all three, **no** seed pin (control) | does not finish | 10,081 | 0 | race_manager/object_rng differ from frame 1980 |

The lead comparisons also mask the V-blank counter (0x027FFC3C), which differs by the lead by definition.
Hardware frames of the finish differ by the lead (11,462 - 4 = 11,458; - 18 = 11,444).

Before the race (menus and loads, frames 0..1979) the runs are equal outside the loading transitions, which
move with load speed: TIME 1,683/1,703 frames equal up to frame 1719, ARM7 1,387/1,695, FS 1,471/1,697,
all three 1,258/1,703, budget-free 1,075/1,704; the race load itself (1720..1979) is shifted.

## Remaining divergences and why (all masked, see the mask file)
- **TIME**: tick-derived values only (the 5.3 mask), plus the cartridge lock word owner at the sample.
- **ARM7**: the native RTC is a fixed clock (RTC area 0x027FFDE8 and an ID derived from RTC + tick at
  0x02180488, copies at 0x02174F78/0x02175078); lock words 0x027FFFB8..; DISPCAPCNT at the sample (ARM7
  alone only).
- **FS**: the card driver's work area (0x02180040..0x021803C8, 512-byte page buffer) is not used.
- **Sound timing (FS and ARM7)**: each kart starts with a sound emitter; its voice-handle list (+0xC/+0x10)
  and active count (+0x14) depend on when the ARM7 sound driver reports a voice done, which both switches
  move by a few ARM7 bursts (the SND command queue 0x021732B0.. and SoundState's handle pool are in the
  already-masked main_02170000). Kart positions, physics, items and the RNGs are unaffected.
- **IPC delivery (task 2)**: with `MKDS_HW_ARM7=native` + `MKDS_HW_TIME=native` the PXI/SPU streams move
  between adjacent frames (masked `pxi`/`spu`), but no game state differs, so 5.3's model does not need
  synchronous replies for correctness. The budget-free mode answers native-service PXI words synchronously
  (`Machine::pxi_sync`), which removes the polled deliveries in the PXI wait loops (47 -> 1 per race).

## 5.4: budget-free build (`MKDS_TIMING=native` when building)
Generator: `mkds_gen --timing native` emits ARM9 `budget!` as nothing; loop headers and the census busy-waits
keep it as `poll!` (4,164 poll sites; 122,736 `budget!` sites are empty). The ARM7 table keeps its cycle
budget. Runtime: waits end the slice; native PXI replies are synchronous; `Session::step_frame` runs to the
next V-blank count.

Closed-loop race (`acceptance rom.nds route.csv OUT 15000`, each run alone on the machine):

| build / mode | finish | wall s | frames run | ms per frame | charged units | IRQs |
|---|---|---:|---:|---:|---:|---:|
| default, fiber (exact; race_diff IDENTICAL) | 11,462, 1st | 28.55 | 12,362 | 2.31 | 1,707,950,080 instr | 581,521 |
| default, flat (IDENTICAL) | 11,462, 1st | 27.45 | 12,362 | 2.22 | 1,707,950,080 instr | 581,521 |
| default + all three native, fiber | 11,683, 1st | 28.30 | 12,583 | 2.25 | 1,714,814,976 instr | 573,273 |
| budget-free, fiber | 11,698, 1st | 23.16 | 12,598 | **1.84** | 370,507,776 | 593,444 |
| budget-free, flat | 11,711, 1st | 22.46 | 12,611 | **1.78** | 367,247,360 | 583,001 |

About 20% less CPU per frame than the exact build; the rest is the ARM7 CPU (sound), the hardware model
ticking in waits, and the acceptance driver's captures.

### Plan 5.4 conditions, checked against the census
1. *No hardware unit derives time from instruction counts* — **partly.** TM0/TM1 are virtual (5.3), FS and
   the small ARM7 services are native. Still cycle-driven: the ARM7 CPU running the sound driver (lane
   b5-sound) and `Bus::advance` (scanlines, V-blank). Without a budget nearly all hardware time passes in the
   frame-end wait, so this is benign, but it is not yet "advance only at frame events".
2. *No code observes cycle timing* — **holds** for the reference route: VCOUNT 0 reads, DISPSTAT 2 (boot),
   TM1-3 0 reads, TM0 only through `OS_GetTick` (virtual), no H-blank / V-count IRQs, GXSTAT reads see the
   immediate geometry engine. DISPCAPCNT's end-of-capture bit is hardware-timed but only shows in the mask.
   Menus beyond the route, battle and missions are not in the census yet.
3. *IRQs and switches only at safe points* — **holds** under `MKDS_HW_TIME=native`; the watchdog still
   fires once per race at MI_CpuFill32 (0x0214D01C, a 1.1 M-instruction fill while loading; harmless).
4. *Residency re-checked at FS_AfterLoadOverlay* — **not implemented as stated**; residency is still
   re-checked at every dispatch after code was written (`code_epoch`) and at slice starts, which also works
   without a budget (the race loads its overlays and finishes in both runtimes).

## Reproduce
```
# exact, logging the seed ticks; then each native switch with the log
frame_compare replay EXE rom.nds inputs.csv OUT_EX 12100 --mask native_seed_equalized.txt --env MKDS_TICK_PIN=log
grep MKDS_TICK_PIN OUT_EX/replay.log > ticks.txt
frame_compare replay EXE rom.nds inputs_m4.csv OUT_N 12100 --mask native_seed_equalized.txt \
    --env MKDS_TICK_PIN=ticks.txt --env MKDS_HW_FS=native --env MKDS_HW_ARM7=native --env MKDS_HW_TIME=native
python region_cmp.py OUT_EX/rec OUT_N/rec --mask native_seed_equalized.txt --from 1980 --offset 4
```
