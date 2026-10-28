# Developer and research material

This folder contains developer tools, research plans and verification material moved out of `CameronStorer/MKDSrust` when that repository was reduced to the code needed to build and run the game. Original relative paths are preserved. [REMOVED_FROM_MAIN.txt](REMOVED_FROM_MAIN.txt) is the complete migration inventory. The main checkout supplies the builder, runtime, verification binaries and dictionary CSVs; this folder supplies the supporting scripts, masks and input sequences.

## Folder origins

| Folder | Original location and purpose |
|---|---|
| `2_native_game/examples/` | Main repo examples: dual boot, ROM-segment lifting and boot probes; historical examples may require their original code revision. |
| `2_native_game/native/diagnostics/` | Native audio comparisons, hardware census and sound scheduling/replay diagnostics, plus menu-confirmation inputs. |
| `4_docs/` | Block 2–5 plans, asset layout and dated evidence. `inputs/` contains open-loop menu, mission and battle sequences and alignment helpers; `masks/` contains justified exclusions and region comparison; `reports/` contains implementation handoffs. |
| `assets/branding/` | Branding generation script, previously under the main repo's assets tree. |
| `dictionary/` | Dictionary export, naming, field/layout inference and evidence scripts, plus SDK review notes. CSV data and the maintained dictionary README remain in the main checkout. Some exporters also need historical research tables not included in this move; read each script's usage before running it. |
| `launcher/` | Launcher reference README moved from the main repo. Launcher code remains there. |
| `tests/` | Original shell-wrapper regression script. It expects `build.sh` and `play.sh` next to the original tests directory; run against a compatible checkout or a temporary fixture with that layout. |

## Build an exact oracle and run a race

The following PowerShell examples run from a main-repo checkout, with Rust/Cargo, Python and the platform's native build prerequisites installed. Replace paths with your own. Keep ROMs, generated code, captures, tick logs and recordings outside this docs repository. Use matching source revisions and your own lawful supported ROM. Output directories must be fresh.

```powershell
$main = (Get-Location).Path
$docs = 'C:/work/mkds-docs'
$rom = 'C:/private/rom.nds'
$work = 'C:/private/verification'
New-Item -ItemType Directory -Force $work | Out-Null
cargo build --release --locked --manifest-path 1_build_tool/Cargo.toml --target-dir "$work/builder"
& "$work/builder/release/mkds_builder.exe" $rom --build --source $main --out "$work/exact" --timing exact --with-acceptance
cargo build --release --locked --manifest-path 2_native_game/native/Cargo.toml --bin frame_compare --target-dir "$work/tools"
$fc = "$work/tools/release/frame_compare.exe"
$ex = "$work/exact/acceptance.exe"
$env:MKDS_RTC = 'fixed'
'FS','ARM7','TIME','SND' | ForEach-Object { Set-Item "Env:MKDS_HW_$_" 'exact' }
$route = 'C:/private/figure8-route.csv'
& $ex $rom $route "$work/race-a" 15000 --record "$work/race-a/rec"
# After building your modified exact candidate into $work/candidate:
& "$work/candidate/acceptance.exe" $rom $route "$work/race-b" 15000 --record "$work/race-b/rec"
```

`--timing exact` is essential: acceptance shares the generated build's timing. Runtime switches cannot restore instruction budgets removed by a native build. The closed-loop route is a private course-specific CSV of `x,z` points (header plus at least three points), not one of the button-input CSVs in this folder. The original Figure-8 route is not included. Use the same route and ROM for both runs.

The historical acceptance procedure compares race telemetry and captures with `race_diff`:

```text
race_diff OUT_A OUT_B
```

Here `OUT_A` and `OUT_B` are the acceptance output directories (`race-a` and `race-b` above). Obtain the matching historical `race_diff` tool and check its usage before invoking it: neither the moved files nor the current local main checkout contains it. Do not interpret a missing comparator as an IDENTICAL result. The maintained alternative below compares recorded logical-frame state and events; it does not replace the historical image/telemetry proof. Closed-loop steering can compensate for divergence, so also use fixed-input replay.

## Open-loop frame comparison with the moved inputs

This runnable mission example uses the main checkout's `frame_compare` and this folder's masks and inputs. Both sides must record with the same mask: byte-range exclusions are applied when hashing, and cannot be applied retroactively to an unmasked recording.

```powershell
$mask = "$docs/project/4_docs/masks/native_mission.txt"
$inputs = "$docs/project/4_docs/inputs/mission.csv"
& $fc check $ex $ex $rom $inputs "$work/self-check" 4800 --mask $mask
& $fc replay $ex $rom $inputs "$work/mission-ex" 4800 --mask $mask --env MKDS_RTC=fixed --env MKDS_TICK_PIN=log
Select-String -Path "$work/mission-ex/replay.log" -Pattern 'MKDS_TICK_PIN' | ForEach-Object { $_.Line } | Set-Content -Encoding ascii "$work/ticks.txt"
# First probe: same exact-timing binary, all four native services, fixed seed values.
$native = @('--env','MKDS_HW_FS=native','--env','MKDS_HW_ARM7=native','--env','MKDS_HW_TIME=native','--env','MKDS_HW_SND=native','--env','MKDS_RTC=fixed','--env',"MKDS_TICK_PIN=$work/ticks.txt")
& $fc replay $ex $rom $inputs "$work/mission-probe" 4800 --mask $mask @native
python "$docs/project/4_docs/inputs/lead.py" "$work/mission-ex/rec" "$work/mission-probe/rec" 1700 4700
# Historical exact-timing native lead was 4. Use the measured lead for your revision.
python "$docs/project/4_docs/inputs/shift.py" $inputs "$work/mission-shifted.csv" 1650 4
& $fc replay $ex $rom "$work/mission-shifted.csv" "$work/mission-native" 4800 --mask $mask @native
python "$docs/project/4_docs/masks/region_cmp.py" "$work/mission-ex/rec" "$work/mission-native/rec" --mask $mask --from 1700 --to 4799 --offset 4
& $fc compare "$work/self-check/a/rec" "$work/self-check/b/rec" --mask $mask
```

`frame_compare check` writes `a/rec` and `b/rec` beneath its output directory; `compare A_REC B_REC --mask FILE` takes recording directories containing `regions.csv`, `frames.bin`, `inputs.csv` and `events.bin`. The self-check already performs a comparison. `region_cmp.py` prints counts for aligned hashes; inspect them, since it is a research helper rather than a pass/fail gate.

To test budget-free code, build a separate bundle with `--timing native --with-acceptance`, use its `acceptance.exe` for native replays and remeasure the lead (the dated mission result used 28). For a race, use the exact race recorder's `rec/inputs.csv` with `native_race.txt`; the dated race leads were 4 / 27. `native_all.txt` holds shared exclusions; the per-mode masks include the applicable exclusions. `native_seed_equalized.txt` and its adjacent report document the earlier three-switch proof. Read the mask comments before selecting exclusions.

For menus or battle, substitute `menus.csv` / `battle.csv` and `native_menus.txt` / `native_battle.txt`, and select a sufficient frame budget (the battle evidence used 6500). `inputs/rekey.py A_REC B_REC INPUTS OUTPUT` aligns input frames by sample index; `region_cmp.py --by-index` compares that alignment. Menus still differ around transitions; battle diverges after exact-model lag frames. Seed pinning and masked equality establish only the documented routes and unmasked regions, not universal fidelity. See [latest defaults evidence](4_docs/BLOCK5_DEFAULTS.md#reproduce) and [earlier seed proof](4_docs/masks/native_seed_equalized.md#reproduce).

Run diagnostics by their module docstrings/usage against private run outputs. Most scripts are research utilities with specific expected formats, not standalone game executables. When finished, clear the test environment (or close this shell):

```powershell
'FS','ARM7','TIME','SND' | ForEach-Object { Remove-Item "Env:MKDS_HW_$_" -ErrorAction SilentlyContinue }
Remove-Item Env:MKDS_RTC, Env:MKDS_TICK_PIN -ErrorAction SilentlyContinue
```

## Site synchronization

From the docs repository, run `python sync.py --source C:/work/MKDSrust`, then `python build.py` and `python -m unittest discover -s tests`. Sync reads this folder's allowlisted reports and launcher reference; only the dictionary README comes from the main checkout. Historical site snapshots whose source was not moved remain available. Do not edit `content/sources/` copies directly; edit their corresponding source and sync.
