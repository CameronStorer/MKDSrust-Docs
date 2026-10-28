# Driftlift documentation update report

Completed 2026-10-28 against the read-only main-project checkout at `C:/Users/cam/dev/mkds-native-builder`, branch `block4`, head `602e770`. Read the site README, all task requirements including Restructure, the requested main-project reports/READMEs and the latest 80 commit subjects. The seed proof lives at `4_docs/masks/native_seed_equalized.md` in this checkout.

## New site structure

The home page provides three explicit audience entry points:

- **Modders:** launcher/script quick start, generated-source navigation, function/structure lookup, dictionary files, texture replacement, exact/Accuracy and native switches, and verification procedures.
- **Researchers:** lift → IR → T0/T1 raising → inferred types; flag liveness and local flags; hardware replacement, census and performance evidence; exact race and logical-frame verification. Code links target the main project's `block4` branch.
- **General readers:** plain-language introduction, purpose and distribution boundaries, a block-by-block journey/timeline, and next work.

Shared navigation includes current project status, glossary and FAQ. Current guides live in `content/guides/`; dated technical evidence lives in `content/sources/`. Existing research pages retain stable URLs and remain accessible under Research archive / Function maps. They explicitly direct readers to current status; dated technical reports warn that they include plans and earlier measurements.

The current-status page is the single maintained summary, with a review date, source revision and update instructions. It distinguishes completed work from owner-requested in-progress priorities (save files, course-select screen swap, Yoshi Falls waterfall, stutters, native defaults, then signature/loop/name polish). Those specific priorities are attributed to the owner's task rather than presented as verified fixes.

## Evidence and scope

Documented all 12,736 raised functions, local flags (81,372/107,472 compares), type/accessor/name counts, the oracle, launcher, native FS/ARM7/time/sound and CPU-less ARM7 execution. The latest defaults report supports about 28% less CPU/frame, superseding the earlier roughly 20% experiment. Native promotion remains planned with RTC/oracle/listening conditions.

The verification guide separates Block 4 bit-identical race results from both generations of seed-pinned native proof. It preserves masks, input re-keying, loading offsets and route limits. The latest all-four native race and mission equality does not imply equal menus/battle or universal real-hardware agreement. The legacy explorer's 11,175 mapping records are explicitly distinguished from the 12,736-function raised-code check.

No ROM data, game assets, screenshots or game text were added. The site shell now uses original CSS instead of the existing game-derived theme graphics; those old repository files remain unchanged. No main-project files were changed. No commit, push or publish script was run.

## Files changed

- `README.md`: Driftlift identity, audience structure, maintenance/source conventions, build/test/sync instructions and scope.
- `build.py`: Driftlift shell and home page, audience navigation, historical/source notices, stable heading anchors and page contents using markdown-it-py.
- `requirements.txt`: pinned `markdown-it-py==4.2.0` renderer. Markdown tables, fenced code, contents and existing URL conventions remain supported. The old Markdown dependency was unavailable locally and network installation was blocked; the installed markdown-it-py enabled running the real build with a reproducible declared dependency.
- `sync.py`: seven current report imports, UTF-8 BOM handling, authored-guide discovery, retained legacy snapshots/dates when absent upstream, retained mapping inventory, no new figure copying. Reads only from the source checkout.
- `assets/theme.css`: original gradient hero, Driftlift theme comment and repaired sidebar disclosure glyph.
- `.github/workflows/pages.yml`: run Python and explorer tests after build, before deployment.
- `.gitignore`: ignore local dependency/runtime caches used while locating a usable Python environment.
- `content/manifest.json`: 45 documentation entries with audience/source/archive groups and dates.
- New `content/guides/start.md`, `modders.md`, `textures.md`, `modes.md`, `pipeline.md`, `verify.md`, `hardware.md`, `status.md`, `journey.md`, `glossary.md`, `faq.md`.
- New `content/sources/BLOCK4_SOURCE_PLAN.md`, `BLOCK5_PLAN.md`, `BLOCK5_CENSUS.md`, `BLOCK5_DEFAULTS.md`, `native_seed_equalized.md`, `launcher.md`, `dictionary.md`: synced technical prose with existing path/public-name normalization.
- New `tests/test_site.py`: renderer/anchor checks, generated audience-link/fragment checks, manifest uniqueness, historical notices and isolated sync preservation/source-read-only checks.
- `DOCS_SITE_REPORT.md`: this report.

The 26 missing legacy Markdown source files and missing old function CSV were retained from the existing site, with explicit sync notices. Their dates and inventory were not falsely refreshed. The existing asset-layout snapshot was read successfully and remained byte-identical. `DOCS_SITE_TASK.md` was already present and was not edited.

## Build and test results

Python was not on PATH. Used the installed interpreter `C:/AI/ComfyUI/python_embeded/python.exe` with markdown-it-py 4.2.0; no system packages were installed or changed.

| Check | Result |
|---|---|
| `python sync.py --source C:/Users/cam/dev/mkds-native-builder` | PASS: current reports imported, legacy history retained, 45 total documentation entries |
| `python build.py` | PASS: 45 documentation pages plus home/explorer, 11,175 function records |
| `python -m unittest discover -s tests -v` | PASS: 3 tests; all authored-page/home local links and fragments resolve; sync preserves history and source bytes |
| `node tests/explorer.cjs` | PASS: all five sorts both ways, filters, 200-row batches, exhaustion, stable details over 11,175 records |
| `git diff --check` | PASS after whitespace cleanup |

Generated `_site/` output remains ignored. Validation covers generated HTML/link structure and explorer behavior; no interactive browser visual review was performed.
