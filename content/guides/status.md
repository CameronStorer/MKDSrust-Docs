# Project status
<!-- Start here -->

Reviewed **2026-10-28**, main-project branch **block4**, head **602e770**. This page is the current summary; source reports preserve dated measurements and may describe earlier stages. Native hardware and budget-free timing remain **opt-in**. Existing executable/configuration names still use mkds / MKDS Native Builder.

| Area | Current evidence / remaining work |
|---|---|
| Block 1: static recompilation | Working: compiled ARM9/ARM7 translations, no instruction interpreter in the normal game path |
| Block 2: presentation | Working: native window, GPU rendering, audio, keyboard/controller input and texture replacement |
| Block 3: dictionary | Working: original names/types metadata, shadow checker and ten verified native helpers |
| Block 4: readable source | All 12,736 functions raised; 81,372/107,472 compares use local flags; 26,370 accessor sites, 810 typed-argument functions, 1,003 renamed-register functions; full readability unfinished |
| Block 5: native services | Oracle, native FS/ARM7/time/sound merged behind switches; latest SND mode has zero ARM7 CPU cycles |
| Budget-free timing | Working opt-in: about 28% less CPU/frame in the latest paired acceptance measurement; guard exceptions remain |
| Verification | Exact race bit-identical; pinned-seed all-four native race 10,082/10,082 unmasked frames equal; mission 3,100/3,100; menus partial, battle diverges with lag |
| Graphical launcher | Working Windows build/inspect/play/settings/controls; three experimental FS/ARM7/time toggles |

## In progress and next
Owner-requested priorities are save files; course-select preview screen swap, Yoshi Falls waterfall rendering and small stutters; making native the player default; then readability polish: plain Rust signatures, loops callable directly and remaining uncertain names. These are **planned or in progress, not completed fixes**. This priority list comes from the owner's DOCS_SITE_TASK.md; the technical sources establish the underlying native/readability work but do not establish completion of those specific graphics fixes.

Before promoting native defaults, the defaults report calls for a host-clock RTC in player builds, retaining exact defaults in the acceptance oracle and a listening check. Native sound still uses the translated driver. Spill/reload reduction and direct veneer tail calls have landed, but the complete plain-call source goal remains open. There are 1,445 names ending exactly in _maybe and 391 retained field placeholders in the latest reviews.

Optional future work: direct graphics submission, HD model hooks, widescreen camera/HUD and high-refresh interpolation. Wireless/multiplayer is separate future work.

## Platform limits
Windows is the primary tested platform. Linux has a full build and 600-frame WSLg smoke test, but no validated full race or broad desktop/input/audio testing. macOS has instructions and a build path, not a Mac validation run. GPU/controller support on Linux/macOS has not been tested in the cited README.

## Keep this page current
Update the date and source revision, then the table and next-work list. Read newer evidence before repeating older plan status. Keep each measurement's route, mode, seed/mask conditions and limits. Sync reviewed reports, build and run tests before publishing.

Evidence: [Block 4](../sources/BLOCK4_SOURCE_PLAN.md), [Block 5 plan](../sources/BLOCK5_PLAN.md), [latest defaults report](../sources/BLOCK5_DEFAULTS.md), [census](../sources/BLOCK5_CENSUS.md), [README](https://github.com/CameronStorer/MKDSrust/blob/main/README.md), [commit history](https://github.com/CameronStorer/MKDSrust/commits/block4/).
