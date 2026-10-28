# Block 5 census (stage 5.0)

How the exact model's ARM9 waits, polls and is interrupted, per **logical frame**, measured with the 5.0 oracle
recorder. It decides how much of 5.3 (OS time/IRQ scheduler) and 5.4 (budget removal) is mechanical.

## How it was measured
- Build: branch `b5-harness` (Block 4 head + the 5.0 probe), fiber mode, exact hardware model.
- Run: `acceptance rom.nds route.csv OUT 15000 --record REC`, the reference route: boot, menus (frames 0–2279),
  one 3-lap race (finish at frame 11,462 in 1st), results. **Menus beyond the route, battle and mission are not
  covered yet**; rerun the same command with other input scripts (`--replay inputs.csv`) to extend it.
- Logical frame = the SDK V-blank count (`OS_GetVBlankCount`, `0x027FFC3C`, incremented by the ARM7's OS
  V-blank handler `0x037F86AC`). One sample per logical frame when the ARM9 takes the V-blank IRQ.
- Counters come from `ds_mem::Probe` (off by default): IRQs taken (IE & IF bits at entry; one IRQ can count for
  several sources), ARM9 reads of polled registers, ARM9 wait entries (`Machine::wait_hook`), and runs of
  consecutive slices ending within 64 bytes of one pc ("tight loops", > 1,000 instructions).
- Summary script: `python census.py REC dictionary` (scratch; reads `census.csv` / `spins.csv`).

## Results (12,343 logical frames, V-blank count 0..12,361)

| per logical frame | total | mean | max | notes |
|---|---:|---:|---:|---|
| lag (V-blanks skipped) | 19 | 0.00 | 1 | all during loading (frames 10–1,979, 2,824, 7,258); no lag in the race loop |
| VBlankIntrWait (SWI 5) | 1 | 0.00 | 1 | the main loop does **not** use SWI 5 |
| IntrWait / Halt (SWI 4/6) | 0 | 0 | 0 | |
| CP15 wait-for-interrupt | 597,551 | 48.4 | 121 | the OS idle thread: `OS_WaitIrq` sleeps the main thread, idle halts until the next IRQ |
| IRQ V-blank | 12,361 | 1.00 | 2 | |
| IRQ H-blank / V-count | 0 | 0 | 0 | no raster effects: **no H-blank work to schedule** |
| IRQ timer 0 | 1,650 | 0.13 | 1 | `OS_GetTick` overflow (tick timer) |
| IRQ timer 1 | 97,323 | 7.9 | 17 | OS alarm timer (`OS_SetAlarm`) |
| IRQ timer 2/3 | 0 | 0 | 0 | |
| IRQ IPC receive | 62,928 | 5.1 | 27 | PXI replies from the ARM7 (sound, touch, RTC ...) |
| IRQ IPC sync / send-empty | 0 | 0 | 0 | |
| IRQ DMA (0–3) | 398,710 | 32.3 | 106 | DMA-end IRQs (GX FIFO / async copies), the largest source |
| IRQ GX FIFO | 12,766 | 1.0 | 45 | bursts of 43–45 in 295 frames (loading), otherwise 0 |
| IRQ card / keypad | 0 | 0 | 0 | card transfers complete by polling, not IRQ |
| reads VCOUNT | 0 | 0 | 0 | never polled |
| reads DISPSTAT | 2 | 0 | 2 | boot only |
| reads TM0CNT_L | 341,234 | 27.6 | 61 | `OS_GetTick` (about 28 calls per frame) |
| reads TM1–3CNT_L | 0 | 0 | 0 | |
| reads IPCSYNC | 151,726 | — | 151,726 | all in frame 0: the `PXI_Init` handshake |
| reads IPCFIFOCNT | 270,518 | 21.9 | 286 | PXI send/receive status (not spin waits: ≤ 286 per frame) |
| reads GXSTAT | 92,155 | 7.5 | 51 | 7 per frame in the race (geometry busy / matrix-stack checks) |
| reads KEYINPUT | 12,262 | 0.99 | 2 | one pad read per frame |
| ARM7 SPU register writes | 180,297 | 14.6 | 105 | |
| PXI events (FIFO words + sync nibbles, both ways) | 72,836 | 5.9 | 286 | |

### Tight loops over 1,000 instructions
35,418 runs at 94 pcs (157 M instructions, 9% of the run; 13,710 runs before frame 2,280, 21,708 after). Top sites:

| pc | function (dictionary) | runs | instructions | longest | kind |
|---|---|---:|---:|---:|---|
| 0x0212F4E4 | sound_filter_sample_buffers | 13,194 | 108.1 M | 8,192 | compute (audio filter) |
| 0x0214D01C | fill loop at 0x0214D018 | 242 | 14.8 M | 1,120,352 | memory fill |
| 0x020B454C | g2d_copy_tilemap_rect | 6,165 | 8.1 M | 1,408 | copy |
| 0x020B44A4 | g2d_fill_tilemap_palette | 4,688 | 5.5 M | 6,432 | fill |
| 0x02146418 / 0C / 24 | card routine at 0x021463A4 | 7,629 | 9.8 M | 2,304 | card data-port read loop (polls the card, no IRQ) |
| 0x0214D8E4 | `PXI_Init` handshake (0x0214D830) | 1 | 1.2 M | 1,213,728 | **busy-wait** on IPCSYNC (boot) |
| 0x0214D480 / 90 / FC | copy at 0x0214D464 | 901 | 2.3 M | 14,592 | copy |
| 0x020AE64D.. | g2d_flush_clear_oam_pair | 1,842 | 2.4 M | 1,376 | fill |
| 0x0200EE60 / 80 | DC_StoreRange / DC_FlushRange | 147 | 0.9 M | 41,152 | cache ops (no-ops on the host) |
| 0x0204B2ED.. | calc_crc16 | 14 | 1.4 M | 280,736 | compute (save data) |
| 0x0200099C | MI_UncompressBackward | 135 | 0.4 M | 28,544 | decompression |
| 0x02039A88 | display_clear_vram_and_wait_maybe | 3 | 0.3 M | 146,880 | fill + wait |
| 0x020399EC | display_wait_task_maybe | 1 | 74 K | 74,148 | **wait** |

## What this means for 5.3 / 5.4
- **Time is consumed by waiting in one place.** The game never polls VCOUNT and never uses SWI 5/4/6 in its loop:
  every frame ends in `OS_WaitIrq` (thread sleep) and the idle thread's CP15 halt. 5.3 can turn "wait for the
  next V-blank" into an event jump in that one place; per-site work is not needed for frame pacing.
- **IRQ sources to schedule natively:** V-blank (1/frame), timer 1 = OS alarms (~8/frame), timer 0 = tick
  overflow (rare), IPC receive (~5/frame, from the ARM7 / `hle7`), DMA end (~32/frame) and GX FIFO (loading
  only). No H-blank, V-count, card, keypad or IPC-sync IRQs at run time. DMA-end and alarm IRQs are the ones to
  model as immediate events.
- **Tick reads:** ~28 `OS_GetTick` reads per frame. Under 5.3 these values change; expect masked differences
  in tick-derived fields only (the 5.0 tick perturbation test found them at 0x022CC610..0x022CC630,
  0x023D9700..0x023D9800 and in DTCM, then a further difference 613 frames later in 0x02170000..; see the
  test below), so each of those needs a reason in the mask.
- **Busy-waits:** only the boot `PXI_Init` handshake (IPCSYNC, 1.2 M instructions) and a few display waits
  during loading. The card driver polls the data port while reading (5.1 removes it with native FS). The other
  long loops are copies, fills and computation, not waits: removing the budget (5.4) does not need per-site
  changes for them.
- **Lag:** 19 lag frames, all during loading; the race loop is lag-free in the exact model, so logical frames
  line up 1:1 with V-blanks there.

## Oracle self-test (5.0 done-check)
- Exact vs exact open-loop replay of the reference inputs: **EQUAL**, 12,045 logical frames, every region,
  71,326 PXI events. The open-loop replay also matches the closed-loop recording in every common frame (it
  reproduces the reference race, finish at frame 11,462).
- Flat-mode recording vs fiber-mode recording: **EQUAL**.
- `MKDS_ORACLE_POKE=5000:0x0236D9AC:...` (kart 0 x position): first difference **frame 5000, regions kart0
  main_02360000**.
- `MKDS_ORACLE_TICK=3000:1` (TM0CNT_L + 1, i.e. `OS_GetTick` + 1 from frame 3000): first difference **frame
  3001** (the first sample after the change), regions dtcm main_022c0000 main_023d0000. With those three masked
  (by range or by region) the first difference moves to frame 3,614 (main_02170000).

## Wider census: battle, mission, menus (lane b5-finish, 2026-10-28)
Same recorder, exact model (`MKDS_HW_*` unset), open-loop replays of input scripts written for this purpose
(`4_docs/inputs/{battle,mission,menus}.csv`, generated by `4_docs/inputs/mkscript.py`; button rows only):
- **battle**: Single Player → Battle → Balloon Battle, Mario, default settings, stage "Nintendo DS", 7 CPU karts;
  driving (A held, weaving, items) from logical frame 3000; 6,500 frames.
- **mission**: Single Player → Missions → Level 1 → Mission 1-1 (drive through 5 gates, 35 s; the script fails it);
  driving from frame 1900; 4,800 frames.
- **menus**: title, nickname / emblem prompts, Records (+ the empty friend-roster dialog), Options (+ the
  erase-data dialog, answered No), mode select, VS character select, mission level select; 3,400 frames. (Selecting
  Nintendo WFC stalls the exact model's V-blank count — wireless is out of scope — so the walk avoids it.)

| per logical frame: total (mean / max) | battle | mission | menus |
|---|---:|---:|---:|
| logical frames | 6389 | 4783 | 2756 |
| lag | **111** (0.02 / 1) | 17 (0.00 / 1) | 25 (0.01 / 1) |
| CP15 wait-for-interrupt | 322174 (50.43 / 121) | 236727 (49.49 / 121) | 153790 (55.80 / 125) |
| IRQ V-blank | 6499 (1.02 / 2) | 4799 (1.00 / 2) | 2780 (1.01 / 2) |
| IRQ H-blank / V-count | 0 | 0 | 0 |
| IRQ timer 0 | 867 (0.14 / 1) | 640 (0.13 / 1) | 371 (0.13 / 1) |
| IRQ timer 1 | 50530 (7.91 / 17) | 37192 (7.78 / 17) | 21497 (7.80 / 18) |
| IRQ IPC receive | 33742 (5.28 / 27) | 24756 (5.18 / 27) | 14295 (5.19 / 27) |
| IRQ DMA | 83479 (13.07 / 124) | 95460 (19.96 / 33) | 0 |
| IRQ GX FIFO | 7282 (1.14 / 44) | 0 | 0 |
| IRQ card / keypad | 0 | 0 | 0 |
| reads VCOUNT | 0 | 0 | 0 |
| reads DISPSTAT | 2 (boot) | 2 (boot) | 2 (boot) |
| reads TM0CNT_L | 177381 (27.76 / 61) | 130685 (27.32 / 61) | 76080 (27.61 / 61) |
| reads TM1–3CNT_L | 0 | 0 | 0 |
| reads IPCSYNC | 151726 (frame 0) | 151726 (frame 0) | 151726 (frame 0) |
| reads GXSTAT | 45563 (7.13 / 51) | 26399 (5.52 / 34) | 0 |
| ARM7 SPU writes | 87060 (13.63 / 118) | 68946 (14.41 / 105) | 40563 (14.72 / 127) |
| PXI events | 34910 (5.46 / 286) | 27328 (5.71 / 286) | 14762 (5.36 / 286) |

Tight loops: no new waits. The new long loops are compute: battle analyses the microphone buffer every frame
(`mic_detect_blow_level` 0x0201EC30, up to 16 K instructions per run; it reads a buffer, it does not wait on the
ARM7), and loading decompression / fills / CRC as before. PXI MIC (tag 9) words: none on any route; the battle's
mic analysis works on the auto-sampling buffer.

What changes for 5.3 / 5.4: nothing new. Every mode ends its frames in the OS idle thread's CP15 halt; no mode
reads VCOUNT, TM1–3 or DISPSTAT after boot, and no mode uses H-blank / V-count IRQs. **Plan 5.4 condition 2 holds
in all four routes.** The one new fact is lag: the exact model overruns frames during balloon battle on the
"Nintendo DS" stage (111 lag frames, about one in 40 during play), so battle cannot be equal per logical frame to a
lag-free native run (see `BLOCK5_DEFAULTS.md`).
