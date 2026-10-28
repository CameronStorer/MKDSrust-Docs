# The journey, block by block
<!-- For everyone -->

The first aim was to run the original game's behavior on a modern computer using a cartridge owner's own copy. The next aim is to make that behavior understandable and easier to change.

## Timeline
The blocks are milestones, not a promise that every later goal is complete. Blocks overlap; dates below identify the reviewed evidence rather than inventing development dates.

| Milestone | What changed | State at 2026-10-28 |
|---|---|---|
| Block 1 | Translate machine instructions before play, then compile them for the PC | Working; the reference race uses no interpreted ARM9 instructions |
| Block 2 | Give the game a modern window, graphics, audio and controls | Working; higher-resolution 3D and texture replacement available |
| Block 3 | Build a dictionary of researched function meanings and structure layouts | Working and being refined; ten verified native helper replacements |
| Block 4 (Oct 27–28 reports) | Raise register-like code into locals, conditions, loops and inferred fields | All 12,736 functions have raised output; readability still improving |
| Block 5 (Oct 27–28 reports) | Replace simulated console services with native files, time and event-driven sound | Merged as experiments; zero ARM7 CPU cycles in latest native sound mode |
| Next | Save support, graphics/stutter fixes, native defaults, then clearer source | In progress / planned |

A key change in Block 5 is how correctness is measured. Earlier transformations could keep exactly the same instruction counts. Replacing simulated hardware intentionally changes timing, so researchers instead compare the game at equivalent frames, with fixed randomness and documented exclusions. [Verification](verify.md) explains the evidence and its boundaries.

## What success still means
A complete translation is not automatically a finished decompilation. Some names remain guesses, types cover only part of the program, and ordinary function signatures and directly callable loops still need polish. Faster loading can also move screen transitions; tests must distinguish a timing difference from a gameplay error.

Read [current status](status.md), [the FAQ](faq.md), or [get a build running](modders.md). Sources: [project README](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/README.md), [Block 4](../sources/BLOCK4_SOURCE_PLAN.md), [Block 5 defaults](../sources/BLOCK5_DEFAULTS.md).
