# MKDSrust documentation

Public documentation for MKDSrust, Cameron Storer's MKDS static recompilation and native-game research. The site provides three routes from its home page:

- **Modders:** build with the graphical launcher or scripts, find generated functions and structures, use the dictionary, replace textures, choose experimental modes and verify changes.
- **Researchers:** lifting/IR/raising, flags, type inference, hardware replacement, census findings and scoped regression proofs, with links to code on branch `block4`.
- **General readers:** an introduction, the block-by-block journey and timeline, distribution boundaries and what comes next.

[Site](https://docs.cameronstorer.com/mkds-decomp-docs/) · [Current status](content/guides/status.md) · [FAQ](content/guides/faq.md) · [Glossary](content/guides/glossary.md)

## Content structure

`content/guides/` contains the maintained audience guides. The first line is the Markdown title; the second line is an HTML comment naming the sidebar group (`Start here`, `Modders`, `Researchers`, or `For everyone`). Keep these two lines when editing. Sync discovers these guides without overwriting their prose; their modified dates come from the guide files.

`content/sources/` contains seven allowlisted technical reports copied from the main project. These are dated evidence, including earlier results and uncompleted plan sections. The status guide explains when newer evidence supersedes an older report. GitHub code links target `CameronStorer/MKDS-Native-Builder`, branch `block4`.

`content/docs/`, `content/analysis/` and `content/PROGRESS.md` retain historical research at its existing URLs. Historical pages link readers to current status. The searchable function explorer uses `content/functions.csv`: its **11,175 mapping records are distinct from the 12,736-function whole-program raised-code count**. Mapping labels are research classifications, not game completion or universal verification.

`content/manifest.json` controls page titles, groups and snapshot dates. `build.py` renders Markdown using pinned markdown-it-py with tables, fenced code, heading anchors and contents lists. It writes flat HTML URLs using the original slug convention, plus CSS, JavaScript and function metadata in `_site/`.

## Build and test locally

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe build.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
node tests/explorer.cjs
python -m http.server 8000 --directory _site
```

Open http://localhost:8000. The Python tests check rendered audience navigation, local links/anchors, Markdown features and sync preservation/read-only behavior. The Node tests check explorer sorting, filters, 200-row loading and details against the complete generated inventory. GitHub Actions builds, tests and publishes pushes to `main`.

## Update from the main project

Read the main project's README, the Block 4/5 status and newest defaults evidence, and recent commits before updating the authored guides. Update `content/guides/status.md` with the review date and source revision; retain each measurement's route, mode, mask/seed conditions and limits. Owner priorities may precede the technical reports; identify those separately from measured results.

```powershell
python sync.py --source "C:\Users\cam\dev\mkds-native-builder"
git diff -- content
python build.py
python -m unittest discover -s tests -v
node tests/explorer.cjs
```

`sync.py` only reads the project. It copies explicitly allowlisted Markdown and, when present, the mapping CSV. It normalizes local user paths and does not import new images. The native-only checkout no longer contains many legacy research documents or the old mapping export: existing site snapshots and their original dates are retained with an explicit console notice. Required current source reports must exist; missing current reports fail sync. Guides survive sync and are included in the new manifest.

The older mapping workspace can refresh the inventory with `tools/function_map.py` and `tools/function_table.py` before sync. Do not confuse that inventory with the native generator's current counts.

Review changes before publishing. `publish.ps1` is an existing convenience script that syncs, builds, commits and pushes; use the separate commands above for a local review without publishing. This task does not require a commit or push.

## Repository scope

No ROM data, game assets, screenshots or game text should be added. This update adds original documentation and reviewed technical prose only. The repo already contains two small legacy theme graphics documented in [assets/ATTRIBUTION.md](assets/ATTRIBUTION.md); the current site shell no longer uses them. Historical research includes an existing simulation figure.

MKDSrust requires the player's own lawful dump. ROM-derived generated source, extracted assets and built bundles must remain private. The reviewed main-project checkout has no top-level license declaration; do not infer redistribution rights for its tools or third-party material. This independent project is not affiliated with Nintendo.
