# Modders: build and explore
<!-- Modders -->

Start with the established baseline, then make one change at a time. [Current status](status.md) distinguishes working features from experiments.

## Build with the graphical launcher
Use Windows 10/11 64-bit, stable Rust's MSVC toolchain and Visual Studio C++ Build Tools. Have a clean, self-dumped USA AMCE revision 0 ROM, about 2 GB free disk and preferably 8 GB RAM. Initial compilation needs internet and can consume substantial memory.

From the project checkout:
~~~powershell
cargo build --release --locked --manifest-path launcher/Cargo.toml
.\launcher\target\release\mkds_launcher.exe
~~~
On Home, select your ROM, inspect compatibility, choose an output directory and select Build game. Keep the launcher open. Play verifies the bundle before launching. Rebuilding into a nonempty destination creates a sibling directory and preserves the old bundle. Keep the checkout available for future builds.

Settings and Controls require Save and apply next launch. Controller bindings use menus rather than physical capture. Advanced has three experimental FS/ARM7/time toggles, initially off. Logs stream during building; the completed log is in %APPDATA%\MKDS Native Builder\launcher-build.log. Outdated is a local timestamp/hash heuristic, not an online updater.

## Script alternative
From the project root:
~~~powershell
.\build.bat "C:\Games\my-copy.nds"
.\play.bat --stats
~~~
Or double-click build.bat and paste your ROM path. Linux/macOS use sh build.sh and sh play.sh with their documented dependencies; Linux has limited validation and macOS remains untested. See the [upstream setup](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/README.md#requirements).

## What was generated?
In builds/mkds, play.exe verifies the package, game.exe is the program, assets/ holds your extracted files, source/ holds generated Rust, and manifest.json records fingerprints. Never distribute those ROM-derived outputs. Editing packaged files can fail verification.

Read source/README.txt first and use source/tiers.csv to find an address, tier, Rust name and crate. T0 is the exact register translation; T1 raises it into locals and structured control flow. T2 adds inferred types and fields; T3 denotes native replacements. T1 output exists for every function, while some transfers still require T0 dispatch. The proposed clean game/sdk/arm7 module organization and plain signatures are not all established.

## Find a function or structure
Search the site's Function explorer by address, meaning or area; it is a research inventory, not the current whole-program T1 count. In your generated tiers.csv look up the matching address and Rust symbol. In the checkout, search dictionary/functions.csv by address; hand-refined sdk_functions.csv and game_*.csv override filled fields in filename order. Do not edit the exported functions.csv by hand.

Find structures in dictionary/structs.csv, fields in fields.csv, access sites in field_uses.csv and roots in globals.csv. Follow address and field-offset evidence rather than assuming a name is correct. A name ending in _maybe is uncertain. Dictionary status and confidence describe research evidence, not universal behavioral proof.

Next: [replace textures](textures.md), [choose native switches or Accuracy mode](modes.md), and [verify a change](verify.md).

Sources: [README](https://github.com/CameronStorer/MKDS-Native-Builder/blob/block4/README.md), [launcher reference](../sources/launcher.md), [dictionary reference](../sources/dictionary.md), [Block 4](../sources/BLOCK4_SOURCE_PLAN.md).
