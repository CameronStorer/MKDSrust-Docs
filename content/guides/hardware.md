# Research: replacing DS hardware services
<!-- Researchers -->

Block 1 compiles instructions ahead of time. Block 5 tackles a different cost: maintaining a cycle-counted console hardware model around that code. Native services are merged but opt-in; the exact model remains the oracle.

## Files and PXI services
Native FS reads the ROM archive directly from the user's in-memory ROM rather than polling card hardware. ARM9 communicates with the secondary ARM7 processor using PXI messages. A high-level replacement router answers touch, clock, power, firmware/NVRAM, backup and other services at that boundary. Wireless is stubbed; multiplayer is separate future work. Native FS is not a claim that persistent save-file work is finished.

## The ARM7 CPU is gone in the latest native sound mode
With MKDS_HW_SND=native, the latest defaults report measures **zero lifted CPU cycles and zero interpreted instructions** on the ARM7. Boot still runs once as translated plain code (861,345 plain instructions), then the sound driver and interrupt work run as event-driven plain calls. Translated ARM7 code has not disappeared: the sound driver remains a substantial cost, about 54,000 plain instructions per frame in one race measurement. A fully native sequencer is a future optimization.

This supersedes the older Block 5 status/proof build, which retained ARM7 sound CPU execution. MKDS_SND_BOOT=cpu preserves the older takeover path.

## OS time and budget-free timing
Native OS time virtualizes timers and delivers interrupts at safe points such as waits. The native-timing build removes 122,736 ARM9 budget sites while retaining 4,164 poll sites in the earlier generator measurement. Budget bookkeeping previously charged instruction costs to advance hardware.

The latest implementation advances hardware time in waits and listed busy-waits; ordinary slice ends exchange graphics and PXI work with tick(0). A guard after 65,536 slices without a wait still advances time: it fired 15 times per measured route in loading computation/fill loops. Thus frame-event scheduling has a documented guard exception.

Overlay residency is rechecked at the SDK overlay hook and the game's own archive-loader code-ready step, with code-epoch checks as a safety net. This matters because overlays replace code at shared addresses.

## Performance evidence
The latest paired acceptance runs report exact fiber **2.21 ms/frame** versus budget-free all-native fiber **1.59 ms/frame**, about **28% less CPU per frame**. The machine was shared; this is a route-specific relative measurement including captures, not a universal speed guarantee. Earlier budget-free builds with the ARM7 CPU measured about 20% less. After merging the spill work, native budget-free fiber/flat races still finish first with ARM7 CPU zero.

## What the census tells us
The initial route has 19 skipped V-blanks during loading and none in the race loop. The wider census adds battle, mission and menu routes. None reads VCOUNT or TM1–3, none reads DISPSTAT after boot, none uses H-blank/V-count IRQs, and no new busy-waits appear. That supports removing instruction timing on those routes.

Battle has 111 lag frames in the exact model's 6,500-frame run. Native avoids that lag, so equality breaks after the first in-play lag frame. Mission has 17 loading lag frames, menus 25. These findings explain why the stronger [race/mission proofs](verify.md) do not imply all-mode equality.

## Next conditions
Default promotion remains planned: use a host clock for player RTC, retain exact defaults in acceptance, and do a listening check before shipping CPU-less sound. Save-file support, graphics fixes and broader validation remain active work. Spill/reload reduction and direct tail calls have landed (71b614e, 1512f01); complete ordinary calling conventions and readability remain goals.

Sources: [latest defaults report](../sources/BLOCK5_DEFAULTS.md), [census](../sources/BLOCK5_CENSUS.md), [dated plan](../sources/BLOCK5_PLAN.md). Code: [native FS](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/native/fs.rs), [PXI router](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/hle7/), [OS time](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/os_hle.rs), [ARM7](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/arm7.rs).
