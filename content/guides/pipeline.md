# Research: from instructions to typed Rust
<!-- Researchers -->

Read the [verification method](verify.md) alongside these source transformations. Naming and coverage do not prove behavior on their own.

## Lift, IR, raise, types
The builder validates the user's ROM, extracts local files, discovers functions and decodes ARM/Thumb instructions. Lifting converts their effects into an intermediate representation (IR): explicit register, flag and memory operations grouped into a control-flow graph. The T0 emitter preserves exact dispatch behavior. T1 promotes registers to locals, folds temporaries and comparisons, and structures branches into if, loop, break and match. T0 remains available for exceptional transfers requiring exact dispatch.

All **12,736 ARM9 and ARM7 functions** have T1 output, with zero rejected functions. There are 563 compiled switches printed as match. This does not mean every function has a plain Rust signature or a directly callable structured loop yet.

## Flag liveness and local flags
ARM condition flags record properties such as zero, carry and overflow after arithmetic. Liveness asks whether any later operation actually reads each flag before it is overwritten, including across calls. Unread flag calculations can disappear. The reported pass removes 65% of set_nz operations and 76% of carry writes.

Flags as locals turns **81,372 of 107,472 compares** into fa/fb/fz locals folded into conditions. Observable boundaries still synchronize CPU flags. Fiber and flat races remain identical to the exact baseline.

## Type inference
Typed views over DS memory retain bus-read/write semantics while expressing structure fields. Reaching definitions track which assignment produced a value; aliases and parent layouts, pointer fields, global roots, interior pointers and constant-global bases seed types. Caller facts propagate to callees. This is inference, with confidence limits, not recovery of every original declaration.

| Measured coverage | Count |
|---|---:|
| Accessor sites | 26,370 |
| Functions with typed arguments | 810 |
| Functions with renamed registers | 1,003 |
| Named-global notes | 11,770 |
| Names ending exactly in _maybe | 1,445 |
| Field placeholders remaining after review | 391 |

All ARM9 and 1,105 ARM7 functions have research names. The latest name review changed 109 of 1,532 uncertain entries (87 confirmed, 22 reworded); that exact-suffix review excludes names containing _maybe_ elsewhere. The field review renamed 204 of 595 placeholders (58 confident, 146 uncertain). These are dated coverage measurements, not a 60% T2 completion claim.

## Read the implementation
Browse [IR](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/ir.rs), [raised emitter](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/raise_emit.rs), [fiber runtime](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/2_native_game/src/fibered.rs) and [dictionary](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/dictionary/). A fiber preserves a guest thread's nested calls while the host services a suspension.

Source and detailed evidence: [Block 4 report](../sources/BLOCK4_SOURCE_PLAN.md). Next: [hardware replacement](hardware.md).
