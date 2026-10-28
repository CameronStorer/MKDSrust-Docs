# MKDSrust rename report

Updated the launcher window title, navigation header and desktop description; builder terminal title and CLI help; native game window title; generated controls/settings file headings; batch/shell script messages; launcher README; main README compatibility wording and suggested checkout directory; and descriptive references in prior reports/tasks. Updated the native host package description. Removed the obsolete brand from temporary test-directory prefixes without moving any existing folders.

Crate/binary names, Rust identifiers, environment variables, output/cache/settings/save paths, repository URLs and layout remain compatible. The save report now describes the current product directory while identifying its previous proof as historical. The dictionary README and 4_docs headers contain no obsolete product title, so needed no edits. Generated bundle manifests have no product-name field to rename. No custom Windows ProductName/FileDescription resources or executable metadata configuration were found.

## Verification

All requested commands passed (exit 0), using PowerShell environment assignments equivalent to the task's shell syntax:

| Directory | Environment | Command | Log |
| --- | --- | --- | --- |
| 1_build_tool | CARGO_NET_OFFLINE=true, CARGO_TARGET_DIR=../target_codex_b | cargo build --release | rename_builder.log |
| launcher | CARGO_NET_OFFLINE=true, CARGO_TARGET_DIR unset | cargo build --release | rename_launcher.log |
| 2_native_game | CARGO_NET_OFFLINE=true, CARGO_TARGET_DIR=../target_codex | cargo build --release --features gen | rename_native.log |

Additional direct native host build passed (exit 0): from repository root, CARGO_NET_OFFLINE=true CARGO_TARGET_DIR=target_codex cargo build --release --manifest-path 2_native_game/native/Cargo.toml (rename_window.log). This compiles the changed game window title, which the requested generator build does not cover. Builder --help displays MKDSrust and retains the existing executable invocation. git diff --check passed. No ROM was supplied: the native proof reports a library-only build with zero lifted functions; no gameplay or visual UI smoke test was performed.

## Remaining search matches

Recursive case-insensitive text search equivalent to the task's grep expression, excluding every target-prefixed directory and Git internals, found the following 12 matching lines. PowerShell Select-String was used because rg/grep are unavailable. This report uses locations rather than repeating obsolete strings, so it adds no search matches.

| Location | Why it stays |
| --- | --- |
| README.md:49 | Actual existing Windows launcher preferences path; changing it would misdirect existing installs. |
| README.md:173 | Actual existing Windows controls path. |
| README.md:174 | Actual existing macOS controls path. |
| launcher/README.md:26 | Actual existing Windows preferences/logs path. |
| 1_build_tool/src/controls.rs:178 | Documentation of the existing settings path. The macOS path continues on line 179. |
| 1_build_tool/src/controls.rs:183 | Windows settings directory implementation; deliberately preserved. |
| 1_build_tool/src/controls.rs:185 | macOS settings directory implementation; deliberately preserved. |
| RENAME_TASK.md:3 | Original task specifies prior names for the rename; task instructions preserved. |
| RENAME_TASK.md:16 | Original instruction naming the obsolete brand to remove. |
| RENAME_TASK.md:21 | Original required search expression. |
| STALL_TASK.md:20 | Existing external playtest folder location in historical reproduction instructions; no folder renamed. |
| STALL_TASK.md:22 | Command referring to that same existing external playtest executable. |

Hyphenated repository/configuration path references also remain where they identify real URLs, existing directories or historical evidence. These are compatibility references, not product titles. No obsolete product branding remains in application UI or generated user-facing headings.

No commit or push was made.
