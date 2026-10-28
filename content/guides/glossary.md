# Glossary
<!-- Start here -->

| Term | Plain meaning |
|---|---|
| ARM9 / ARM7 | The DS's main and secondary processors; Driftlift translates their programs ahead of play |
| ROM dump | A local copy of a cartridge's contents, supplied by its owner |
| Static recompilation | Translate instructions before launch and compile the result for the host |
| Decompilation / raising | Recover more understandable source expressions and control flow from machine-like code |
| IR | Intermediate representation: operations between instruction decoding and source emission |
| T0 / T1 / T2 / T3 | Exact translation / raised control flow / inferred types and fields / native replacements |
| Flags / liveness | Arithmetic condition bits, and the analysis of whether later code reads them |
| Accessor | A named field read/write that preserves underlying memory operations |
| Dictionary | Original research metadata about addresses, names, types and confidence |
| _maybe | A research name whose meaning remains uncertain |
| Native / HLE | Host-side implementation of a service boundary rather than its hardware protocol details |
| PXI | The message channel between the game processors |
| Oracle | The retained exact model used as a regression reference |
| Logical frame / V-blank | A frame indexed by the game's vertical-blank counter; V-blank is the display update interval |
| Open-loop replay | Fixed recorded input, without a driver correcting steering in response to state |
| Seed pinning | Test-only replay of tick values used to initialize randomness |
| Mask | Justified exclusions from a comparison; equality is claimed only outside them |
| Budget / safe point | Instruction-cost bookkeeping / a place where the runtime can service events |
| Spill / reload | Copy local values to/from the CPU register model at observable boundaries |
| Overlay | Code loaded into an address range reused by other code |
| Fiber | A resumable host execution context used for a game thread |
| Accuracy mode | This site's label for the established exact hardware baseline, not a documented launcher button |

See [pipeline](pipeline.md), [hardware](hardware.md) and [verification](verify.md) for sourced explanations.
