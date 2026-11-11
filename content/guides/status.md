# Project status
<!-- Start here -->

Reviewed **2026-11-11**, MKDSrust **main** at **119a5dd**, launcher **v0.5.3**. This page is the current summary; source reports keep their dated measurements and may describe earlier stages.

MKDSrust's goal: **play Mario Kart DS natively on Windows, and mod it.** The launcher builds the game from your own dump, and mods are compiled straight into it.

| Part | Status |
|---|---|
| **Recompilation** | ✅ Complete and frozen. All 12,736 functions (ARM9 and ARM7) are translated to Rust; no interpreter in the game path. Native hardware services (file system, ARM7, time, sound) and budget-free timing are the player default. |
| **Decompilation** | ✅ Complete in scope: 9,446 of 9,496 in-scope functions (99.5%) are named and every pointer argument is typed. ARM7 code (replaced by native services) and the online code are out of scope. The 50 holdouts are listed in the repo's `dictionary/HOLDOUTS.md`. |
| **Launcher** | ✅ Released (v0.5.3): portable Windows app, private toolchain, ROM check, build, play, view source, mods. |
| **Mods** | ✅ Widescreen 1.2 (16:10, 16:9, 21:9, map overlay with picture and track styles). Mods live in the repo's `Mods/` folder; official ones are reviewed, community ones arrive through pull requests. |
| **Readable Rust** | 🟡 In progress. The readable layer is on by default: 39% of functions take real parameters, 20% no longer use the simulated CPU and 2% are also free of simulated memory. |
| **Verification** | Every pushed change keeps the exact race bit-identical to the DS and the default native race identical to its baseline; 253 tests pass. |
| **Toolbox** | ⏸ Paused (the visual editor for characters, karts and tracks). |
| **Mod hub** (uploads, accounts) | ⏸ Parked; [mkdsrust.com/mods](https://mkdsrust.com/mods) lists the curated `Mods/` folder instead. |

## In progress and next
1. **Readable Rust without the simulated DS.** The tylzars/mkds matching C decompilation converts automatically to Rust with c2rust (98.5% of its files). We are testing a 32-bit build that keeps the game's memory at the real DS addresses, so converted functions run directly on that memory with no simulated CPU or memory bus, while untranslated code keeps running beside them. Each converted function is checked against the original machine code before it is used. Translated code is produced on the user's machine and never committed.
2. **Single Screen**, a new layout for the Widescreen mod: the whole game (menus, race, results) in one widescreen frame, with no bottom screen. Widescreen will offer Classic, Widescreen with map overlay, and Single Screen.
3. More mods after that: graphics enhancements, then larger changes such as more racers.

These are **planned or in progress, not finished**.

## Platform limits
Windows is the primary tested platform. Linux builds and passed a short WSLg smoke test but has no validated full race or broad desktop/input/audio testing. macOS has a build path but no validation run.

## Keep this page current
Update the date and source revision, then the table and next-work list. Read newer evidence before repeating older plan status. Keep each measurement's route, mode and limits. Sync reviewed reports, build and run tests before publishing.

Evidence: [README](https://github.com/CameronStorer/MKDSrust/blob/main/README.md), [commit history](https://github.com/CameronStorer/MKDSrust/commits/main/), [Block 4 plan](../sources/BLOCK4_SOURCE_PLAN.md), [Block 5 plan](../sources/BLOCK5_PLAN.md), [defaults report](../sources/BLOCK5_DEFAULTS.md).
