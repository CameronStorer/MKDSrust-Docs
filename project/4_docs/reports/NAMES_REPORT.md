# Function name evidence review

Reviewed all **1,532 rows ending exactly in `_maybe`** (109 name cells changed: 87 confirmed, 22 reworded with uncertainty retained): 1,403 game names and 129 SDK-dictionary names. Every row resolves to generated source. Names containing `_maybe_...` rather than ending in `_maybe` are outside this task; non-target rows are unchanged.

| Dictionary | Reviewed | Confirmed (suffix removed) | Reworded, still uncertain | Unchanged, still uncertain | Remaining `_maybe` |
|---|---:|---:|---:|---:|---:|
| game_names.csv | 1403 | 76 | 18 | 1309 | 1327 |
| sdk_functions.csv | 129 | 11 | 4 | 114 | 118 |

## Evidence and decisions

`dictionary/name_evidence.py` indexes all 12,733 generated function bodies and collects callers, direct callees, resolved constant tail calls, typed field reads/writes, global references and simple direct access directions, operational constants, coverage metadata sizes and instruction count. ROM-derived bodies and memory-access lines remain outside this repository. Address matching includes the segment and normalizes the Thumb bit; ambiguous cross-segment destinations are not guessed.

Each of the 1,532 target rows has an explicit keep/confirm decision and rationale in the external ledger. All rows received conservative evidence triage; selected candidates received detailed code review. Retention is deliberate where an operation, object identity, protocol constant or function boundary remains unproved. This is not a claim that all retained names are correct. Generated field types and existing callee names can be wrong: an entry labeled `OS_ExitThread`, for example, actually sets an alarm and sleeps until a marker is cleared. Such labels were not treated as independent confirmation.

Only reviewed, clear operations lost `_maybe`. Rewording also corrects misleading operations while preserving uncertainty where needed. New descriptive names use Rust snake_case and at most 40 characters. Public SDK names `OS_ReadMessage` and `CARD_WaitRomAsync` use their conventional spelling; descriptive wrapper names do not assert a newly identified public SDK symbol. No game text, resource filenames or entry addresses were used in new names.

Static limitations: indirect runtime call targets are unresolved; global direction inference follows simple assignments and pointer offsets, not general control flow or heap aliasing. Pointer-root reads do not imply pointee writes. Empty field/global lists mean no resolved annotation, not absence of memory access; raw memory operations are recorded separately. Sizes use `coverage.csv` metadata when present, with instruction-address estimates as a fallback; they do not use distance to the next function. Constants include offsets, masks and literal addresses, whose roles require review.

## Twenty examples

Each size below is the generated coverage size in bytes. Source file and raw/wrapper line locations are recorded in the external evidence JSON.

| Address / segment | Original ? decision | Evidence |
|---|---|---|
| 0x037F8AE4 / arm7_auto_037F8000 | `os_spin_wait_4096_maybe` ? `os_spin_wait_4096` | 12 bytes; callers: os_init_lock, os_lock_common; no resolved typed fields. Passes 0x1000 to os_spin_wait by a resolved constant tail jump; lock initialization and lock acquisition call it. |
| 0x037FAC14 / arm7_auto_037F8000 | `os_valarm_set_tag_maybe` ? `os_valarm_set_tag` | 44 bytes; callers: tp_init_valarms; no resolved typed fields. Touch-panel VAlarm initialization calls it; rejects zero tags through os_terminate and writes the tag to alarm +8. |
| 0x037FB808 / arm7_auto_037F8000 | `os_set_rcnt_mode_maybe` ? `os_set_rcnt_mode` | 24 bytes; callers: pad_update_xy_hinge_buttons, pm_go_sleep, rtc_init; no resolved typed fields. Supplies mask 0xC000 and the low halfword of the argument to os_set_rcnt_bits; RTC, pad and touch input callers corroborate register mode selection. |
| 0x037FCC54 / arm7_auto_037F8000 | `snd_ex_channel_set_sustain_rate_maybe` ? `snd_channel_set_converted_rate_maybe` | 28 bytes; callers: snd_ex_channel_init, snd_ex_channel_note_on, snd_track_note_on; no resolved typed fields. Calls snd_calc_release_rate and stores its halfword result at channel +0x1E. This proves a converted envelope-rate store, but not which ADSR stage consumes it; another entry already owns the release-rate name. |
| 0x0238015C / arm7_main | `crt0_detect_main_memory_size_maybe` ? `crt0_detect_main_memory_size` | 56 bytes; callers: crt0_start; no resolved typed fields. Writes two probe values and checks whether addresses separated by 4 MiB alias, then records size code 1 or 2. |
| 0x01FFC064 / arm9_autoload1_itcm | `kart_transform_matrix_maybe` ? `kart_add_radius_scaled_vector` | 44 bytes; callers: kart_apply_remote_snapshot, kart_check_slipstream, kart_compute_ground_facing; kart::collision_radius. Reads kart::collision_radius, adds the input distance, and calls VEC_MultAdd with the vector at kart +0x12C and the input origin. The new wording describes the geometric operation without asserting an axis identity. |
| 0x0200C914 / arm9_main | `os_set_irq_callback_7_maybe` ? `os_dispatch_irq_callback_seven` | 12 bytes; callers: no resolved direct callers; no resolved typed fields. Passes index 7 to the common IRQ callback dispatcher. Target reads and clears the indexed callback, invokes it and updates IRQ flags; it does not install callbacks. |
| 0x0202811C / arm9_main | `menu_get_object_state_maybe` ? `menu_read_game_part_state` | 16 bytes; callers: menu_exit_select_screen, sub_arm9_main_02028865; game_part::state_observed. Loads g_game_part and returns its state_observed field; menu-exit callers use the result. |
| 0x02029A24 / arm9_main | `race_get_config_field_maybe` ? `race_read_game_part_state` | 16 bytes; callers: race_reset_racer_entries; game_part::state_observed. Loads g_game_part and returns state_observed, exactly like the menu accessor; the old config-field wording names the wrong object. |
| 0x0203BFC4 / arm9_main | `os_clear_check_result_maybe` ? `rtc_read_calendar_or_zero` | 40 bytes; callers: net_build_race_setup_record_maybe, net_build_session_record, net_generate_session_id; no resolved typed fields. Calls the synchronous calendar reader and, on nonzero status, zeroes three output words. Target returns asynchronous RTC status after waiting. |
| 0x0203BFEC / arm9_main | `os_set_check_result_maybe` ? `rtc_read_time_or_default` | 44 bytes; callers: large_056750, net_friend_upsert, save_tally_match_results; no resolved typed fields. Calls the synchronous time reader and, on nonzero status, writes fallback words {5,1,1}. Target returns asynchronous RTC status after waiting. |
| 0x0207A84C / arm9_main | `kart_query_record_hook_maybe` ? `kart_get_finish_flags_by_index` | 24 bytes; callers: hud_draw_ranking_default_icons, hud_draw_ranking_frame, hud_draw_ranking_icons; no resolved typed fields. Indexes g_kart_array with stride 0x5A8 and tail-calls kart_get_finish_flags. |
| 0x02085354 / arm9_main | `obj_invoke_resource_hook_maybe` ? `obj_g3d_draw_thunk` | 12 bytes; callers: no resolved direct callers; no resolved typed fields. Forwards arguments unchanged by a resolved tail jump to NNS_G3dDraw. |
| 0x020A126C / arm9_main | `battle_is_manager_active_maybe` ? `battle_has_first_finisher_maybe` | 28 bytes; callers: battle_update_kart_counter, boolean_0b29c4, mission_enemy_begin_dying; racer_manager::first_finisher. Tests racer_manager::first_finisher >= 0 through score_manager. This is more precise than manager active, but the inferred layout identity still needs corroboration. |
| 0x021213F4 / arm9_main | `net_has_sample_entries_maybe` ? `net_has_type_four_entries` | 32 bytes; callers: menu_build_status_entries_maybe, menu_check_record_status_maybe; net_session::type4_count. Returns whether net_session::type4_count is nonzero through g_net_session; the sample-entry interpretation is unnecessary. |
| 0x0218E889 / ov9_000 | `os_wrapper_maybe` ? `os_thread_alarm_wait_thunk_maybe` | 8 bytes; callers: net_browser_start_query_maybe, net_connect_blocking, net_connect_remote_address; no resolved typed fields. Tail target is labeled OS_ExitThread but its body creates an alarm, sleeps a thread until the callback clears a marker and restores interrupts. Keep uncertainty rather than endorsing the incorrect public label. |
| 0x021ACEBD / ov9_000 | `memory_compare_wrapper_maybe` ? `dgt_md5_reset_thunk` | 8 bytes; callers: hash_md5_to_hex; no resolved typed fields. Tail target writes MD5 IV words 67452301, EFCDAB89, 98BADCFE, 10325476 and clears length words; no comparison occurs. |
| 0x021CDBBD / ov9_003 | `sound_play_sequence_maybe` ? `menu_set_secondary_volume_maybe` | 12 bytes; callers: menu_update_scroll_sound_maybe, menu_update_scrollbar; no resolved typed fields. Loads the menu sound handle and calls sound_set_secondary_volume_layer; retained uncertainty in the concurrently chosen wording is preserved. Concurrent edit preserved. |
| 0x0214FB24 / arm9_main | `pm_set_led_pattern_three_maybe` ? `pm_write_register_three` | 20 bytes; callers: sound_init_microphone_capture; no resolved typed fields. Truncates the input to 16 bits and writes power-management register index 3 through the inspected synchronous register writer; LED-pattern wording is unsupported. |
| 0x021525E0 / arm9_main | `os_id_is_flag0_set_maybe` ? `os_id_is_flag0_set` | 14 bytes; callers: race_request_stage_transition_maybe; no resolved typed fields. Loads word +0x20, masks bit 0 and returns a normalized boolean. |

## Local evidence and reproduction

External evidence directory: `C:\Users\cam\AppData\Local\Temp\claude\--192-168-1-11-Shared-Coding-My-NDS-GAME\d2702baf-4324-41bc-919f-6df583f54ea0\scratchpad\g_f2\name_review`.

- `name_evidence.json`: collected evidence for every original target, including local-only generated bodies.
- `reviewed_decisions.json` and `decisions.csv`: all final decisions with row identities and reasons.
- `review_summary.json`: per-dictionary counts.
- `*.csv.before`: exact working-tree bytes before this pass applied its changes (including preserved concurrent edits).
- `*.csv.initial` and `original_dictionaries/`: original Git dictionary contents, used to reproduce the original target set; Git normalizes these to LF while the working CSVs use CRLF.
- `review_names.py`: explicit reviewed choices and byte-preserving application used for this pass.

Collector command (use the saved original dictionaries to reproduce all 1,532 targets):

```powershell
$source = "C:/Users/cam/AppData/Local/Temp/claude/--192-168-1-11-Shared-Coding-My-NDS-GAME/d2702baf-4324-41bc-919f-6df583f54ea0/scratchpad/g_f2"
$review = Join-Path $source "root_name_review"
& "C:/Program Files/Blender Foundation/Blender 4.5/4.5/python/bin/python.exe" dictionary/name_evidence.py $source --output (Join-Path $review "recollected") --baseline-dir (Join-Path $review "baseline")
```

## Validation

Passed independent checks for all 1,532 ledger decisions against the final CSVs; unchanged row order, column values and non-target names; exact byte preservation outside edited name cells against the working-tree snapshots; preserved CRLF and final-newline status; valid naming lengths/spelling; and no newly introduced name collisions within a segment.

Synthetic collector checks passed for typed reads/writes, raw byte/halfword accesses, global direction inference, direct and constant-tail calls, Thumb normalization, ambiguous overlays, decimal and hexadecimal constants, coverage sizes, missing functions, missing source and rejection of evidence output inside the repository. The full collector rerun found all 1,532 original targets. `git diff --check` passed. The external `validate_review.py` and `validation_results.json` record the checks.

No commit or push was performed.

## Reconciled final artifacts

The additional review in the shared workspace was preserved. The final CSVs contain 109 name changes: 87 confirmations and 22 rewordings retaining `_maybe`. 1445 names remain uncertain.

Canonical reconciled evidence and decisions: `C:\Users\cam\AppData\Local\Temp\claude\--192-168-1-11-Shared-Coding-My-NDS-GAME\d2702baf-4324-41bc-919f-6df583f54ea0\scratchpad\g_f2\root_name_review`. `final_decisions.json` and `final_decisions.tsv` cover every original target; `final_checks.json` records the final counts, checks and CSV hashes. `name_evidence.json` supplies refreshed observations, and `baseline/` holds byte-exact original CSVs. The collector requires only Python standard-library modules.
