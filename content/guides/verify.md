# Verify a change: races and frame comparison
<!-- Researchers -->

A successful build is the beginning of verification. Keep an unchanged exact build and fixed inputs, make one change, then compare its output. The acceptance tools need your local ROM; no game-derived recordings belong on this site.

## The bit-identical race
Block 4 compares against the project's exact model, not directly against every physical-hardware state. The Figure-8 acceptance race finishes first at frame **11,462** with **1,707,950,080 ARM9 instructions** and **581,521 IRQs**. Fiber and flat runs have byte-identical telemetry across **12,362 frames**, identical inputs and all 40 captured images. Raised-code/type passes preserve the reported race. Images are evidence in the private run, not published here.

Build the relevant acceptance binaries and use the project's local ROM and route file:
~~~text
acceptance rom.nds route.csv OUT 15000
~~~
Run the same route in the exact reference and modified builds; use the upstream race_diff tool to compare outputs. For native function replacements, MKDS_SHADOW=1 compares calls with translations; zero mismatches on the tested corpus supports that replacement. A closed-loop driver steers using observed state, so finishing first alone can hide divergence.

## Logical-frame oracle
Block 5 changes timing, so instruction identity no longer applies. The exact model remains the **oracle**, the reference against which a change is checked. A logical frame is the SDK's V-blank counter, sampled when ARM9 takes its V-blank interrupt. Open-loop replay supplies fixed inputs without steering corrections. Record hashes of game-memory regions and render inputs plus PXI and sound events.

~~~text
acceptance rom.nds route.csv OUT_EX 15000 --record OUT_EX/rec
frame_compare replay EXE rom.nds inputs.csv OUT_N 12100 --mask MASK
~~~
Use the exact recorder's inputs.csv and a justified upstream mask, with both sides recorded under the same mask. Resolve EXE and MASK to your built binary and the relevant file in 4_docs/masks. Replay native switches with --env MKDS_HW_FS=native (and other selected switches). Consult [the proof reproduction commands](../sources/native_seed_equalized.md#reproduce) and [latest route procedure](../sources/BLOCK5_DEFAULTS.md#reproduce) before choosing frame offsets. Do not reuse offsets from another mode or build.

The oracle self-test compares exact/exact over **12,045 logical frames** and flat/fiber equally. Deliberate position corruption is detected at frame 5000; a tick perturbation from frame 3000 is detected at the next sampled frame. This tests the comparator itself.

## Seed pinning, masks and loading offsets
Race randomness derives from OS_GetTick. Test-only MKDS_TICK_PIN=log records seed-producing tick calls; replaying that log returns identical values at those sites. This does not force every timer value or prove unpinned equality. A mask excludes explicitly justified ranges such as timing/driver work areas; report equality as **every unmasked region**, never every byte.

The earlier FS/ARM7/TIME proof (without the separate SND switch) reports TIME 10,079/10,079, ARM7 10,082/10,082, FS 10,077/10,077, all three 10,081/10,081 and budget-free 10,078/10,078 equal race frames. FS/all-three need a four-frame loading offset; that budget-free build needs eighteen. Without pinning, the all-three control has zero equal frames and does not finish.

The newer all-four-switch report compares **10,082/10,082 race frames** equally for both exact-timing native and budget-free native, with loading leads of 4 and 27. Mission 1-1 compares **3,100/3,100** equally (leads 4 and 28). Menus remain only partly equal around loading/screen transitions; battle diverges after an exact-model lag frame. Keep those limits in any result you publish.

Sources: [Block 4](../sources/BLOCK4_SOURCE_PLAN.md), [census and oracle tests](../sources/BLOCK5_CENSUS.md), [earlier seed proof](../sources/native_seed_equalized.md), [latest defaults evidence](../sources/BLOCK5_DEFAULTS.md). Code: [race_check](https://github.com/CameronStorer/MKDSrust/blob/main/2_native_game/native/src/bin/race_check.rs), [frame_compare](https://github.com/CameronStorer/MKDSrust/blob/main/2_native_game/native/src/bin/frame_compare.rs).
