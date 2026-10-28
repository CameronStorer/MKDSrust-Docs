# SDK dictionary review (lane B2)

`sdk_functions.csv` covers all 1,257 addresses in the supplied SDK research table.
Segments come from the repository's function boundaries. It contains names,
signatures and review notes only; neither ROM text nor the research evidence
column is copied. Addresses are segment-relative identities, not portable SDK
version identifiers.

`named` rows with empty signatures are intentionally unresolved. In particular,
an area label such as `nitrosdk_mi_related_unnamed_*` does not identify a public
API. Descriptive names include the entry address to avoid collisions. `typed`
means a proposed API signature, not proof that the address implements it.
Public API types are symbolic C types; `fx32` is signed 20.12 fixed point.
`u32` sizes describe the guest's 32-bit ABI, not the host's `usize`.

Internal memory entry points take different arguments from public convenience
macros: `MIi_CpuClear16` and `MIi_CpuClearFast` take the fill value first, followed
by destination and byte count. Copy entries take source before destination.
The MSL multiply helper uses little-endian register pairs for its two `u64`
arguments; its descriptive name does not assert GCC symbol identity.

The fixed-point names (`FX_DivAsync`, `FX_GetDivResult`, ...) follow the SDK's published API names.
Names and API signatures inform the dictionary; native acceptance depends on
the user's ROM and the differential checks, including scratch-register state.

Native functions start as `native` (on trial). Ten were then verified by whole-race shadow checks and are
`native-verified` (installed by default); see `4_docs/BLOCK3_PLAN.md`.
