# Field naming report

Reviewed **595** original placeholder rows: **58 confident**, **146 `_maybe`**, **391 kept**. Renamed **204** fields.

Only placeholder name cells in `dictionary/fields.csv` changed. Existing names, types, offsets, row order and byte-for-byte line endings were preserved. Names are snake_case, at most 32 characters, and unique across each canonical struct and all its aliases. Existing duplicate legacy names were left untouched.

The collector resolves aliases from `structs.csv`, normalizes the Thumb address bit, and joins `field_uses.csv` to function names with game names overriding SDK names and the base function table. It scans both lifted functions and named wrappers, collecting short access windows, comparisons, arithmetic, neighboring stores and resolved direct callees. Repeated accessor names across alias views are marked `typed_alias_candidate`; raw offset matches are marked `raw_candidate` because they do not prove the base pointer type. Generated type inference sometimes labels item, map-object, camera or sound objects as Kart. Such accesses alone do not establish a Kart field meaning.

458 fields have collected source windows; 137 have no direct matching source window. A matching window can still be an unrelated pointer, stack offset, initialization-only store, or ambiguous arithmetic. These are evidence limitations, not proof that a field is unused.

The generated ROM source was read only. Snippets are stored only in the external evidence JSON, never in this repository. This report contains original semantic summaries.

Reproduce (use an output path outside this repository):

```powershell
python dictionary/field_evidence.py collect <generated-source-root> --output <external-evidence.json>
python dictionary/field_evidence.py apply
python dictionary/field_evidence.py verify
python dictionary/field_evidence.py report <external-evidence.json>
```

`collect` also includes already-applied reviewed decisions, so it can be rerun after naming. `apply` is idempotent. `verify` compares against the Git HEAD baseline without modifying Git configuration.

## Twenty examples with evidence

| Canonical struct / offset | Name | Code evidence (paraphrased) |
|---|---|---|
| Kart +0x74 | `player_slot_id` | Used to index the per-racer item record table with stride 528 in terrain contact handling. Functions: `kart_query_terrain_contact`, `kart_compute_ground_facing`, `kart_update_collision`. |
| Kart +0x84 | `world_position_y` | Contact orientation copies this into ground height; launch damage saves it as the initial height. Functions: `kart_update_contact_orientation_ffa0c4`, `kart_compute_ground_facing`, `kart_record_ghost_frame`. |
| Kart +0x88 | `world_position_z` | Ghost recording shifts this third position component right by ten and stores it after the other coordinates. Functions: `kart_record_ghost_frame`, `kart_init_start_pose`, `kart_apply_remote_snapshot`. |
| Kart +0xbc | `render_scale_x` | Controls/physics multiplies auxiliary scale and body scale into this render scale component. Functions: `kart_tick_controls_physics`, `kart_finish_respawn`, `kart_tick_finish_sequence`. |
| Kart +0xc8 | `bounce_velocity` | Added to bounce height during motion integration. Functions: `kart_integrate_motion_maybe_ff9c40`, `kart_integrate_motion_maybe_ffb9cc`, `kart_tick_controls_physics`. |
| Kart +0x174 | `visual_position_x` | Flipped-body tick copies the first coordinate from the selected position pointer here. Functions: `kart_tick_flipped_body`, `kart_init_start_pose`, `kart_init_object`. |
| Kart +0x1dc | `contact_center_y` | Kart contact subtracts the middle contact-center coordinates and compares against the overlap distance. Functions: `kart_resolve_kart_contact`. |
| Kart +0x224 | `respawn_callback` | Respawn-hook code reads this field and calls it indirectly. Functions: `kart_call_respawn_hook`. |
| Kart +0x230 | `collision_update_callback` | Collision update reads this pointer and invokes it with the kart as its first argument. Functions: `kart_update_collision`, `kart_tick_physics_collision`, `kart_tick_controls_physics`. |
| Kart +0x260 | `vertical_velocity` | Terrain contact compares this signed velocity with zero; jump-pad and flight code also use it. Functions: `kart_query_terrain_contact`, `kart_compute_ground_facing`, `kart_integrate_motion_maybe_ffb9cc`. |
| Kart +0x2ac | `ground_contact_height` | Contact-orientation update copies the kart's world Y position into this height. Functions: `kart_update_contact_orientation_ffa0c4`, `kart_handle_hard_landing`, `kart_reset_base_state`. |
| Kart +0x2fc | `mini_turbo_charge_stage` | Charge update increments this stage and compares against two and three before changing wheel flares. Functions: `kart_update_mini_turbo_charge`, `kart_reset_damage_drift`, `kart_activate_grounded_drift`. |
| Kart +0x300 | `drift_left_press_count_maybe` | Charge update increments the first halfword counter for one steering button and compares it with its neighbor. Functions: `kart_update_mini_turbo_charge`, `kart_reset_damage_drift`, `kart_activate_grounded_drift`. |
| Kart +0x30c | `drift_input_cooldown` | Charge update decrements this timer and reloads ten after an accepted steering press. Functions: `kart_update_mini_turbo_charge`, `kart_reset_damage_drift`, `kart_activate_grounded_drift`. |
| Kart +0x310 | `cpu_control_ptr` | Passed to CPU recovery and fallback-reset callbacks together with the racer index. Functions: `kart_query_terrain_contact`, `kart_init_object`, `kart_init_race_start`. |
| Kart +0x340 | `launch_origin_height` | Launch-damage initialization saves world Y here; its tick compares current world Y against it. Functions: `kart_tick_launch_damage`, `kart_init_launch_damage`, `kart_reset_base_state`. |
| Kart +0x50c | `orientation_quat_ptr` | Passed as quaternion input to kart_quat_to_matrix; initialization points it to the internal quaternion. Functions: `kart_tick_flipped_body`, `kart_init_object`. |
| KartP508 +0x4 | `position_y` | Flipped-body tick copies this coordinate into visual Y position. Functions: `kart_tick_flipped_body`, `effect_compute_world_position`, `effect_update_kart_speed_offset`. |
| KartP514 +0xe | `received_yaw` | Orientation update subtracts this halfword from local yaw to calculate the remote rotation difference. Functions: `kart_update_orientation`, `kart_init_network_buffer`. |
| FriendCodeState +0x85 | `pending_peer_index_maybe` | Session-phase handling sign-extends this byte as an index into eight-byte peer records then resets it to minus one. Functions: `net_handle_session_phase_maybe`, `net_handle_slot_phase_maybe`, `net_reset_session`. |

## Complete decision inventory

| Struct / offset | New name | Rationale |
|---|---|---|
| CharacterSelectScreen +0x54 | `primary_draw_state_maybe` | Select-screen update passes this value as the fourth argument with cell resources into the draw routine. |
| CharacterSelectScreen +0x58 | `secondary_draw_state_maybe` | Select-screen update passes this value with the second group of cell resources into its draw routine. |
| CharacterSelectScreen +0x78 | `selected_record_index_maybe` | Select-screen update multiplies this index by twenty-four before storing into the selected record. |
| ChoiceMessageScreen +0x38 | `prompt_message_id_maybe` | Prompt selection saves its requested message value here before looking up the message resource. |
| ChoiceMessageScreen +0x3c | `message_resource_ptr_maybe` | Prompt selection stores the flagged-resource lookup result here before selected-message rendering. |
| ChoiceMessageScreen +0x64 | `primary_draw_state_maybe` | Choice update passes this value with primary cell resources into the draw routine. |
| ChoiceMessageScreen +0x68 | `secondary_draw_state_maybe` | Choice update passes this value with secondary cell resources into the same draw routine. |
| CourseSelectScreen +0x4 | `cell_resource_ptr_maybe` | Creation reads its resource metadata and passes it into cell allocation and drawing. |
| CourseSelectScreen +0xc | `cell_bank_ptr_maybe` | Creation passes this resource pointer with the cell-resource pointer to cell allocation and drawing. |
| CourseSelectScreen +0x18 | `resource_priority_maybe` | Creation stores the result of fs_lookup_resource_priority here. |
| CourseSelectScreen +0x1c | `message_resource_ptr` | Creation stores fs_lookup_flagged_resource here then passes it into text_get_message. |
| CourseSelectScreen +0x28 | `frame_heap_ptr` | Creation stores the new frame heap here and passes it into cell allocation. |
| CourseSelectScreen +0x64 | `grid_column_count_maybe` | Creation initializes this layout count to four; refresh and screen updates use it. |
| CourseSelectScreen +0x7c | `current_selection_maybe` | Screen update copies this value into the following saved-selection slot; cursor and input routines use it. |
| CourseSelectScreen +0x80 | `previous_selection_maybe` | Screen update copies the preceding current-selection value here before refreshing the option panel. |
| CourseSelectScreen +0x84 | `selection_enabled_maybe` | Creation initializes this selection-control field to one and input handling tests it. |
| CourseSelectScreen +0xb4 | `cell_draw_state_maybe` | Screen update passes this value as the fourth argument with its cell resources into the draw routine. |
| FriendCodeState +0x8 | `session_state_maybe` | Lowest-latency slot selection writes three here; network dispatch routines use it as session state. |
| FriendCodeState +0x18 | `session_record_buffer_maybe` | Session-record construction loads this pointer as the destination of a sixty-four-byte memory operation. |
| FriendCodeState +0x24 | `wireless_setup_buffer_maybe` | Session-header setup copies configuration through this pointer and passes it to WM_SetWEPKey. |
| FriendCodeState +0x7c | `session_packet_buffer_maybe` | Session-record construction dereferences this buffer and passes it with a packet length. |
| FriendCodeState +0x85 | `pending_peer_index_maybe` | Session-phase handling sign-extends this byte as an index into eight-byte peer records then resets it to minus one. |
| FriendCodeState +0x87 | `active_peer_mask_maybe` | Wireless menu flow and network send routines use this byte as a peer mask. |
| FriendCodeState +0x88 | `lowest_latency_peer_maybe` | Lowest-latency selection stores its winning peer index here or minus one if none qualifies. |
| FriendCodeState +0x8a | `pending_peer_mask_maybe` | Wireless menu flow checks this mask for zero and forwards it as a request mask. |
| FriendCodeState +0x43d | `player_info_valid_mask_maybe` | Player-info query tests this byte against one shifted by the requested player index. |
| FriendCodeState +0x456 | `pending_action_flags_maybe` | Pending-action drain clears the low bit of this byte before returning. |
| InfoMessageScreen +0x70 | `graphics_resource_block_maybe` | Ranking-resource loading passes this field's location to g2d_get_resource_block and later passes the resulting pointer to palette-manager setup. |
| InfoMessageScreen +0x7c | `input_handler_ptr_maybe` | Phase-two input handling reads this pointer before passing controller button states to its handler. |
| InfoMessageScreen +0x80 | `primary_draw_state_maybe` | Staff-roll update passes this value with the primary row resources into the cell draw routine. |
| InfoMessageScreen +0x84 | `secondary_draw_state_maybe` | Staff-roll update passes this value with the secondary row resources into the same draw routine. |
| Item +0x60 | `path_segment_index` | Path advancement multiplies this index by twelve before indexing the inline path-coordinate table. |
| Item +0x1a0 | `bomb_active_flag_maybe` | Bomb initialization sets one and bomb reset clears this field. |
| Kart +0x44 | `motion_state_flags` | Motion integration and mini-turbo handling test individual masks in the movement-state word. |
| Kart +0x48 | `terrain_state_flags_maybe` | Terrain dispatch and ground-facing code test this auxiliary state word; not all bits are understood. |
| Kart +0x4c | `active_effect_flags` | Mini-turbo and damage handlers test and modify masks in this effect-state word. |
| Kart +0x54 | `facing_axis_y_maybe` | Ground-facing projection multiplies this component alongside the adjacent facing axis components. |
| Kart +0x58 | `facing_axis_z_maybe` | Ground-facing projection uses this as the third component of the vector beginning at the up axis. |
| Kart +0x60 | `reverse_axis_y_maybe` | Ground-facing update stores the negation of the facing vector's middle component here. |
| Kart +0x64 | `reverse_axis_z_maybe` | Ground-facing update stores the negation of the facing vector's third component here. |
| Kart +0x74 | `player_slot_id` | Used to index the per-racer item record table with stride 528 in terrain contact handling. |
| Kart +0x7c | `racer_state_bits` | Mini-turbo and other kart routines test masks in this bitfield. |
| Kart +0x80 | `world_position_x` | Ghost recording serializes this vector's first component; start pose and remote snapshots set it. |
| Kart +0x84 | `world_position_y` | Contact orientation copies this into ground height; launch damage saves it as the initial height. |
| Kart +0x88 | `world_position_z` | Ghost recording shifts this third position component right by ten and stores it after the other coordinates. |
| Kart +0x9c | `owner_position_y_maybe` | Start-pose setup copies this into the smoothed Y position; layout views disagree on the owner type. |
| Kart +0xa0 | `owner_position_z_maybe` | Start-pose setup copies this into smoothed Z immediately after copying owner Y. |
| Kart +0xac | `motion_vector_z_maybe` | Motion integration scales it with the two preceding motion-vector components. |
| Kart +0xb0 | `velocity_axis_x_maybe` | Motion integration multiplies the vector beginning here by a common fixed-point factor. |
| Kart +0xb8 | `velocity_axis_z_maybe` | Motion integration scales this third component alongside the preceding velocity components. |
| Kart +0xbc | `render_scale_x` | Controls/physics multiplies auxiliary scale and body scale into this render scale component. |
| Kart +0xc0 | `render_scale_y` | Controls/physics writes the Y render scale after fixed-point multiplication of scale factors. |
| Kart +0xc4 | `render_scale_z` | Collision-radius calculation multiplies this scale by the stats contact offset. |
| Kart +0xc8 | `bounce_velocity` | Added to bounce height during motion integration. |
| Kart +0xcc | `speed_limit_primary_maybe` | Speed-limit update compares this cap with the adjacent alternate speed cap. |
| Kart +0xd0 | `speed_limit_secondary_maybe` | Speed-limit update compares the two cap candidates; exact source of each cap remains uncertain. |
| Kart +0xd4 | `slope_speed_factor_maybe` | Ground-facing calculation writes this slope-related value before speed calculation uses it. |
| Kart +0xd8 | `boost_speed_factor_maybe` | Slipstream and item activation modify this speed factor; ground-facing also resets it. |
| Kart +0xdc | `surface_speed_factor_maybe` | Surface dispatch reads this together with the surface-specific speed table in kart stats. |
| Kart +0x174 | `visual_position_x` | Flipped-body tick copies the first coordinate from the selected position pointer here. |
| Kart +0x178 | `visual_position_y` | Flipped-body tick copies the middle coordinate from the selected position pointer here. |
| Kart +0x17c | `visual_position_z` | Flipped-body tick copies the third coordinate from the selected position pointer here. |
| Kart +0x180 | `damage_mode` | Terrain contact compares this state with six; ram and blast handlers dispatch on the same state. |
| Kart +0x1b4 | `body_basis_ptr_maybe` | Flipped-body tick selects an internal basis pointer and stores it here. |
| Kart +0x1d0 | `contact_radius` | Terrain collision passes this radius with contact vectors; radius getter reads it. |
| Kart +0x1d8 | `contact_center_x` | Kart contact subtracts the first contact-center coordinates of two karts before overlap tests. |
| Kart +0x1dc | `contact_center_y` | Kart contact subtracts the middle contact-center coordinates and compares against the overlap distance. |
| Kart +0x1e0 | `contact_center_z` | Kart contact subtracts the third contact-center coordinates and compares against the overlap distance. |
| Kart +0x1fc | `wall_push_x_maybe` | Tilt-target update tests this and the next two components for zero; wall-reaction code updates the vector. |
| Kart +0x200 | `wall_push_y_maybe` | Tilt-target update tests the middle component of the wall-reaction vector for zero. |
| Kart +0x204 | `wall_push_z_maybe` | Tilt-target update tests the third component of the wall-reaction vector for zero. |
| Kart +0x208 | `contact_state_ptr_maybe` | Tilt-target and effect cleanup dereference this pointer then test the first word for zero. |
| Kart +0x20c | `pose_override_ptr_maybe` | Object initialization tests this optional pointer while selecting pose data. |
| Kart +0x210 | `checkpoint_state_ptr_maybe` | Object initialization tests this pointer; respawn-checkpoint restoration and reset use it. |
| Kart +0x214 | `pose_update_callback_maybe` | Object initialization stores a code pointer here when choosing a pose update path. |
| Kart +0x218 | `body_update_callback_maybe` | Object initialization writes the same code pointer here and in the next callback slot. |
| Kart +0x21c | `body_finish_callback_maybe` | Initialized to the same code pointer as the preceding callback; precise invocation phase is unclear. |
| Kart +0x224 | `respawn_callback` | Respawn-hook code reads this field and calls it indirectly. |
| Kart +0x230 | `collision_update_callback` | Collision update reads this pointer and invokes it with the kart as its first argument. |
| Kart +0x240 | `surface_grip_factor_maybe` | Surface dispatch writes this factor from the current terrain data. |
| Kart +0x244 | `ground_normal_x` | Ground-facing projection reads this and the next two words as the terrain normal vector. |
| Kart +0x248 | `ground_normal_y` | Ground-facing tests the middle normal component against zero before slope handling. |
| Kart +0x250 | `contact_normal_x_maybe` | Kart contact projects displacement onto the vector beginning here. |
| Kart +0x254 | `contact_normal_y_maybe` | Kart contact multiplies the middle component of the contact projection vector. |
| Kart +0x258 | `contact_normal_z_maybe` | Kart contact multiplies the third component of the contact projection vector. |
| Kart +0x260 | `vertical_velocity` | Terrain contact compares this signed velocity with zero; jump-pad and flight code also use it. |
| Kart +0x274 | `object_push_decay_maybe` | Terrain contact multiplies this object-push value by a fixed-point decay factor. |
| Kart +0x278 | `initial_heading_x_maybe` | Start-pose initialization copies three consecutive heading values here from the spawn record. |
| Kart +0x27c | `initial_heading_y_maybe` | Start-pose initialization copies the second heading value from the spawn record here. |
| Kart +0x280 | `initial_heading_z_maybe` | Start-pose initialization copies the third heading value from the spawn record here. |
| Kart +0x28c | `hop_axis_y_maybe` | Grounded-drift activation multiplies this vector component while calculating the hop direction. |
| Kart +0x290 | `hop_axis_z_maybe` | Grounded-drift activation uses this forward component alongside the preceding hop-vector component. |
| Kart +0x29c | `item_effect_mode_maybe` | Bullet, ghost and star activation and fall handling write this item-effect mode. |
| Kart +0x2a0 | `normalized_speed_maybe` | Tilt-target update multiplies this speed ratio into the tilt response. |
| Kart +0x2a8 | `forward_velocity_maybe` | Terrain contact passes this speed to response calculations; steering and engine sound also read it. |
| Kart +0x2ac | `ground_contact_height` | Contact-orientation update copies the kart's world Y position into this height. |
| Kart +0x2bc | `hop_height` | Motion integration adds bounce velocity to this bounce-height accumulator. |
| Kart +0x2c4 | `steering_direction_maybe` | Steering update negates this signed direction when computing turn response. |
| Kart +0x2cc | `physics_stats_ptr` | Surface dispatch reads this pointer and then accesses kart-stats surface parameters. |
| Kart +0x2d0 | `push_weight_state_ptr_maybe` | Kart push-weight calculation dereferences this pointer at the second word before combining kart weights. |
| Kart +0x2d4 | `lean_response_maybe` | Motion integration and steering use this signed lean value and compare it with zero. |
| Kart +0x2d8 | `contact_impulse_x_maybe` | Terrain contact subtracts projected collision response from this three-component impulse vector. |
| Kart +0x2dc | `contact_impulse_y_maybe` | Terrain contact subtracts the middle projected collision-response component here. |
| Kart +0x2e0 | `contact_impulse_z_maybe` | Terrain contact subtracts the third projected collision-response component here. |
| Kart +0x2e4 | `wall_impulse_x_maybe` | Terrain contact passes this vector to VEC_DotProduct; wall-reaction code also writes it. |
| Kart +0x2e8 | `wall_impulse_y_maybe` | Terrain contact subtracts the middle component of the second collision-response vector here. |
| Kart +0x2ec | `wall_impulse_z_maybe` | Terrain contact subtracts the third component of the second collision-response vector here. |
| Kart +0x2fc | `mini_turbo_charge_stage` | Charge update increments this stage and compares against two and three before changing wheel flares. |
| Kart +0x300 | `drift_left_press_count_maybe` | Charge update increments the first halfword counter for one steering button and compares it with its neighbor. |
| Kart +0x302 | `drift_right_press_count_maybe` | Charge update increments the second halfword counter for the opposite steering button; exact left/right assignment is tentative. |
| Kart +0x304 | `drift_press_source_a_maybe` | Charge update compares this pointer with the first steering counter's location. |
| Kart +0x308 | `drift_press_source_b_maybe` | Charge update compares this pointer with the second steering counter's location. |
| Kart +0x30c | `drift_input_cooldown` | Charge update decrements this timer and reloads ten after an accepted steering press. |
| Kart +0x310 | `cpu_control_ptr` | Passed to CPU recovery and fallback-reset callbacks together with the racer index. |
| Kart +0x318 | `damage_roll_phase_maybe` | Ram-damage tick accumulates roll rate into this roll-progress field. |
| Kart +0x334 | `launch_sine_sample_maybe` | Launch-damage tick stores a signed trigonometric table sample here after shifting an angular phase. |
| Kart +0x33c | `launch_rotation_phase_maybe` | Launch-damage tick adds 1000 to this signed angular accumulator. |
| Kart +0x340 | `launch_origin_height` | Launch-damage initialization saves world Y here; its tick compares current world Y against it. |
| Kart +0x348 | `launch_elapsed_ticks` | Launch-damage tick compares this counter with two and initialization resets it. |
| Kart +0x360 | `damage_roll_increment_maybe` | Ram-damage tick adds this roll rate to the roll-progress accumulator. |
| Kart +0x368 | `spin_rotation_phase_maybe` | Terrain handling adds the adjacent spin increment to this spin-progress accumulator. |
| Kart +0x380 | `airborne_frame_count` | Contact-orientation update compares this airborne counter with five before changing orientation behavior. |
| Kart +0x38c | `speed_cap_multiplier_maybe` | Speed update multiplies this cap factor by the current scale. |
| Kart +0x394 | `size_speed_multiplier_maybe` | Speed update multiplies this scale with the cap factor; flatten and shrink handlers update it. |
| Kart +0x398 | `flatten_scale_multiplier_maybe` | Visual-scale reset and flatten tick restore this factor to fixed-point one. |
| Kart +0x39c | `object_speed_factor_maybe` | Speed update combines this value with cap and size multipliers; object contact sets it. |
| Kart +0x3a0 | `object_speed_floor_maybe` | Speed update clamps forward speed upward to this value when the object-contact override is active. |
| Kart +0x3cc | `driver_voice_animation_maybe` | Control dispatch passes this voice-animation value to a driver request routine. |
| Kart +0x3e0 | `ground_surface_kind` | Surface dispatch stores the decoded surface type and uses it to index a surface table. |
| Kart +0x3e4 | `ground_surface_variant` | Surface dispatch stores the upper halfword of the terrain result as its surface variant. |
| Kart +0x3ec | `steering_target_rate_maybe` | Steering update writes the target turn value here before rate adjustment. |
| Kart +0x3f0 | `steering_current_rate_maybe` | Steering update reads this signed turn rate and takes its magnitude. |
| Kart +0x3f4 | `water_probe_height_maybe` | Water-depth update multiplies this height offset by render scale before querying water height. |
| Kart +0x3f8 | `airborne_scale_factor_maybe` | Contact-orientation update sets this factor immediately before testing airborne-frame count. |
| Kart +0x404 | `squash_phase_a_maybe` | Squash/stretch tick loads this value from an animation-indexed table. |
| Kart +0x408 | `squash_phase_b_maybe` | Squash/stretch tick loads this second value from an animation-indexed table. |
| Kart +0x40c | `landing_effect_stamp_maybe` | Hard-landing code stores a getter result here; mini-turbo tick compares it with zero. |
| Kart +0x410 | `boost_effect_stamp_maybe` | Mini-turbo tick conditionally captures a getter result here after testing the boost flag. |
| Kart +0x414 | `squash_factor_a_maybe` | Squash/stretch tick writes this table-selected factor together with the adjacent factor. |
| Kart +0x418 | `squash_factor_b_maybe` | Squash/stretch tick writes the second table-selected factor here and can copy it into its neighbor. |
| Kart +0x41c | `body_scale_factor_x_maybe` | Controls/physics multiplies this body factor by the auxiliary X scale to obtain render X scale. |
| Kart +0x420 | `body_scale_factor_y_maybe` | Controls/physics multiplies this body factor by the auxiliary Y scale to obtain render Y scale. |
| Kart +0x424 | `body_scale_factor_z_maybe` | Controls/physics multiplies this body factor by the auxiliary Z scale to obtain render Z scale. |
| Kart +0x428 | `auxiliary_scale_x` | Controls/physics multiplies this by the body X factor to form render X scale. |
| Kart +0x42c | `auxiliary_scale_y` | Controls/physics multiplies this by the body Y factor to form render Y scale. |
| Kart +0x430 | `auxiliary_scale_z` | Controls/physics multiplies this by the body Z factor to form render Z scale. |
| Kart +0x434 | `auxiliary_scale_w_maybe` | Controls/physics multiplies this fourth scale factor by render Y scale. |
| Kart +0x44c | `last_contact_object_maybe` | Object-contact handling caches a candidate pointer for kind eleven and later compares it against the current candidate. |
| Kart +0x4bc | `fall_scale_snapshot_maybe` | Fall handling copies the airborne scale here before setting a fall effect flag. |
| Kart +0x4c0 | `cached_effect_flag_maybe` | A setter masks the input to a single effect bit and updates this cached value only when it differs. |
| Kart +0x4c8 | `collision_body_scale_maybe` | Collision-radius getter combines this body scale with render scale and stats contact offset. |
| Kart +0x4cc | `flipped_body_state_maybe` | Flipped-body tick writes this state and base-state reset clears it. |
| Kart +0x4d0 | `elapsed_race_ticks` | Tilt-target update compares this race counter with one hundred; physics and collision routines use it. |
| Kart +0x4d4 | `start_charge_amount_maybe` | Start-boost and body-wobble routines use this charge; ground-facing tests it against zero. |
| Kart +0x4e8 | `start_charge_snapshot_maybe` | Start-boost handling stores current charge plus fixed-point one here. |
| Kart +0x500 | `water_depth_value` | Water-depth update writes the measured depth here; rolling and engine sound consume it. |
| Kart +0x508 | `visual_position_ptr` | Flipped-body tick loads three coordinates through this pointer into visual position. |
| Kart +0x50c | `orientation_quat_ptr` | Passed as quaternion input to kart_quat_to_matrix; initialization points it to the internal quaternion. |
| Kart +0x510 | `contact_position_ptr` | Initialization points it at world position; ground-facing passes it with contact offset to compute the contact center. |
| Kart +0x514 | `remote_motion_state_ptr` | Ghost recording and snapshot application dereference this network/interpolation state pointer. |
| Kart +0x534 | `initial_position_ptr_maybe` | Object initialization snapshots the selected position pointer here before initializing the start pose. |
| Kart +0x55c | `remote_state_changed_maybe` | Remote snapshot application sets this flag to one when a received state differs. |
| Kart +0x590 | `driver_model_state_ptr` | Queried by driver animation, engine sound and body transform routines. |
| Kart +0x594 | `shake_amplitude_maybe` | Shake tick damps this positive value then subtracts one hundred. |
| Kart +0x59c | `shake_smoothed_value_maybe` | Shake tick eases this value toward a scaled shake target using fixed-point interpolation. |
| KartP12C +0x48 | `motion_flag_bits_maybe` | Physics tests a single high bit in this word before allowing a movement path. |
| KartP12C +0x4c | `effect_flag_bits_maybe` | Physics tests a combined mask in this word to gate movement. |
| KartP12C +0x7c | `racer_flag_bits_maybe` | Sound and physics routines test individual bits in this racer-state word. |
| KartP168 +0x0 | `path_point_x_maybe` | Chain update subtracts the object's first position coordinate from this coordinate. |
| KartP168 +0x8 | `path_point_z_maybe` | Chain update subtracts the object's third position coordinate from this coordinate. |
| KartP168 +0x18 | `path_segment_ptr_maybe` | Route steering passes this value to item_advance_path_segment. |
| KartP508 +0x0 | `position_x` | Flipped-body tick copies this coordinate into visual X position. |
| KartP508 +0x4 | `position_y` | Flipped-body tick copies this coordinate into visual Y position. |
| KartP508 +0x8 | `position_z` | Flipped-body tick copies this coordinate into visual Z position. |
| KartP514 +0xc | `previous_received_yaw_maybe` | Network-buffer initialization copies the received yaw halfword into this preceding halfword. |
| KartP514 +0xe | `received_yaw` | Orientation update subtracts this halfword from local yaw to calculate the remote rotation difference. |
| KartP514 +0x20 | `sync_progress_maybe` | Remote-sync tick compares this value with the current interpolation step. |
| KartP514 +0x24 | `sync_step_count_maybe` | Remote-sync tick writes the interpolation step here; collision and race-start code also read it. |
| KartP514 +0x2c | `replicated_racer_flags` | Ghost recording serializes this word; item and damage routines set replicated state flags in it. |
| KartP514 +0x30 | `received_racer_flags` | Snapshot application tests multiple masks in this received flags word. |
| KartP514 +0x44 | `interpolation_flags` | Orientation update and snapshot application test individual bits in this control word. |
| KartP514 +0x48 | `received_motion_flags_maybe` | Snapshot application tests bit two here before modifying local movement flags. |
| KartP514 +0x5c | `interpolated_yaw_maybe` | Snapshot application interpolates this value and stores its low halfword into the remote yaw output. |
| KartP514 +0x60 | `remote_bounce_height_maybe` | Controls/physics adds the adjacent remote bounce velocity to this value. |
| KartP514 +0x64 | `remote_bounce_velocity_maybe` | Controls/physics adds local bounce velocity to this value then uses it to advance remote bounce height. |
| KartP514 +0xa4 | `damage_event_kind_maybe` | Bullet-ram and directional-blast application store five here in the replicated motion state. |
| KartP590 +0x0 | `kart_model_id_maybe` | Engine sound dispatches on this model identifier with a bounded case table. |
| KartP590 +0x4 | `driver_profile_id_maybe` | Start-boost and voice setup use this identifier to index driver-specific tables. |
| KartP590 +0x8 | `driver_animation_ptr` | Driver animation request and player flags dereference this animation state pointer. |
| KartP590 +0x18 | `material_animation_ptr_maybe` | Material-attribute blending and flipped-body update use this optional animation pointer. |
| KartP590 +0x20 | `model_joint_positions_ptr_maybe` | Wheel-contact update indexes this pointer in twelve-byte coordinate strides. |
| KartP590 +0x24 | `body_transform_factor_maybe` | Flipped-body tick multiplies this value by a fixed-point body transform coefficient. |
| KartP590 +0x58 | `driver_action_state_maybe` | Spin and damage handlers test this driver-model state against zero. |
| MainMenuScreen +0x2c | `frame_heap_ptr` | Screen teardown passes this pointer to memory destruction; screen creation stores its heap here. |
| MainMenuScreen +0x80 | `primary_draw_state_maybe` | Screen dispatch passes this value as the fourth argument with the primary cell resources to the draw routine. |
| MainMenuScreen +0x84 | `secondary_draw_state_maybe` | Screen dispatch passes this value with the secondary cell resources to the same draw routine. |
| MainMenuScreen +0x88 | `grid_input_mode_maybe` | Grid update compares this field with two when selecting how to process tile input. |
| MapObj +0x8 | `world_position_y_maybe` | Spawn code stores source Y plus a height offset here and source Z in the following word; many object routines share this field. |
| MapObj +0x74 | `racer_slot_index_maybe` | Hatch collision uses this halfword as the shift count for a per-racer bitmask. |
| MenuDialog +0x10 | `update_frame_count` | Dialog update increments this counter by one and initialization clears it. |
| RecordSelectScreen +0xb4 | `primary_draw_state_maybe` | Screen update passes this value with the primary cell resources to the draw routine. |
| RecordSelectScreen +0xb8 | `secondary_draw_state_maybe` | Screen update passes this value with the secondary cell resources to the same draw routine. |
| ResultsRankScreen +0x64 | `primary_draw_state_maybe` | Ranking screen dispatch passes this value with primary cell resources into the draw routine. |
| ResultsRankScreen +0x68 | `secondary_draw_state_maybe` | Ranking screen dispatch passes this value with secondary cell resources into the same draw routine. |

## Retained placeholders

Each row below was assessed. A broad function association or a generated accessor is insufficient to invent a semantic identity. Fields with a tentative but useful identity received `_maybe`; the following fields lack a defensible identity from the inspected evidence.

| Canonical struct / offset | Evidence available / reason retained |
|---|---|
| CameraView +0x64 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_074828`, `camera_074854`, `camera_074874`. |
| CameraView +0x88 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_place_eye`, `camera_init_for_kart`. |
| CameraView +0xf0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_place_eye`, `camera_init_for_kart`. |
| CameraView +0x248 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_place_eye`, `camera_0747f4`, `camera_init_for_kart`. |
| CharacterSelectScreen +0xf0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_select_screen`, `menu_create_select_screen`, `menu_apply_select_layout`. |
| ChoiceMessageScreen +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_choice_update`, `menu_draw_manager_rows`, `results_draw_ranking_rows`. |
| ChoiceMessageScreen +0x4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_choice_update`, `menu_choice_update_slide_in`, `menu_get_mode_value_maybe`. |
| ChoiceMessageScreen +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_choice_update`, `menu_get_mode_value_maybe`, `menu_draw_manager_rows`. |
| ChoiceMessageScreen +0xc | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_choice_update`, `results_draw_ranking_rows`, `menu_message_manager_destroy`. |
| ChoiceMessageScreen +0x10 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_choice_update`, `menu_choice_update_slide_in`, `menu_choice_update_slide`. |
| ChoiceMessageScreen +0x14 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_handle_button_input`, `menu_choice_load_resources`. |
| ChoiceMessageScreen +0x18 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_choice_update`, `menu_get_mode_value_maybe`, `results_draw_ranking_rows`. |
| ChoiceMessageScreen +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_setup_name_input`, `menu_choice_load_resources`. |
| ChoiceMessageScreen +0x20 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_message_manager_destroy`, `menu_choice_load_resources`. |
| ChoiceMessageScreen +0x24 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_message_manager_destroy`, `menu_create_message_manager`, `menu_choice_load_resources`. |
| ChoiceMessageScreen +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_create_message_manager`, `menu_choice_load_resources`. |
| ChoiceMessageScreen +0x2c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_create_message_manager`, `menu_choice_load_resources`. |
| CourseData +0x9c | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_init_checkpoint_progress`, `mission_load_course_data`. |
| CourseData +0x108 | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_scale_racer_value`, `cpu_setup_race_maybe`. |
| CourseMapView +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `per_frame_map_scroll_zoom_update`, `unnamed_020b58f8`, `unnamed_020b58f8`. |
| CourseMapView +0xc | Access context does not resolve a unique semantic role or reliable owner type. Users include `per_frame_map_scroll_zoom_update`, `unnamed_020b58f8`, `unnamed_020b58f8`. |
| CourseMapView +0x20 | Access context does not resolve a unique semantic role or reliable owner type. Users include `per_frame_map_scroll_zoom_update`, `minimap_kart_pixel`, `allocates_156_byte_map_state_block`. |
| CourseMapView +0x24 | Access context does not resolve a unique semantic role or reliable owner type. Users include `per_frame_map_scroll_zoom_update`, `minimap_kart_pixel`, `allocates_156_byte_map_state_block`. |
| CourseMapView +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `per_frame_map_scroll_zoom_update`, `allocates_156_byte_map_state_block`. |
| CourseMapView +0x2c | Access context does not resolve a unique semantic role or reliable owner type. Users include `allocates_156_byte_map_state_block`, `unnamed_020b6078`, `unnamed_020b6078`. |
| CourseMapView +0x30 | Access context does not resolve a unique semantic role or reliable owner type. Users include `allocates_156_byte_map_state_block`, `unnamed_020b6078`, `unnamed_020b6078`. |
| CourseMapView +0x3c | Access context does not resolve a unique semantic role or reliable owner type. Users include `allocates_156_byte_map_state_block`, `unnamed_020b6078`, `unnamed_020b6078`. |
| CourseMapView +0x40 | Access context does not resolve a unique semantic role or reliable owner type. Users include `allocates_156_byte_map_state_block`, `unnamed_020b6078`, `unnamed_020b6078`. |
| CourseMapView +0x44 | Access context does not resolve a unique semantic role or reliable owner type. Users include `allocates_156_byte_map_state_block`, `unnamed_020b6078`, `unnamed_020b6078`. |
| CourseMapView +0x48 | Access context does not resolve a unique semantic role or reliable owner type. Users include `allocates_156_byte_map_state_block`, `unnamed_020b6078`, `unnamed_020b6078`. |
| CourseSelectScreen +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_course_screen`, `menu_highlight_map_cell`, `menu_create_course_select`. |
| CourseSelectScreen +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_handle_course_select_input`, `menu_test_entry_cells`, `menu_build_hud_resources`. |
| CourseSelectScreen +0x10 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_create_course_select`, `menu_build_hud_resources`. |
| CourseSelectScreen +0x20 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_refresh_option_panel`, `menu_build_hud_resources`. |
| CourseSelectScreen +0x68 | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_update_result_menu`, `menu_refresh_entry_icons`, `menu_can_advance_substate_maybe`. |
| CourseSelectScreen +0x70 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_course_screen`, `menu_tick_selection_state_11ac88`, `menu_destroy_course_select`. |
| CourseSelectScreen +0x74 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_handle_course_select_input`, `menu_create_course_select`, `race_update_result_menu`. |
| FriendCodeEntryScreen +0x4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_update`, `menu_friend_input_update_slots`, `menu_friend_input_select_key`. |
| FriendCodeEntryScreen +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_highlight_tab`, `menu_friend_input_slide_answer`, `menu_friend_input_handle_keypad`. |
| FriendCodeEntryScreen +0xc | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_update`, `menu_keyboard_init`. |
| FriendCodeEntryScreen +0x14 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_update_flags`, `menu_keyboard_update_completion`. |
| FriendCodeEntryScreen +0x18 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_update_flags`, `menu_keyboard_update_completion`. |
| FriendCodeEntryScreen +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_handle_keypad`, `menu_friend_input_update_flags`, `menu_keyboard_handle_input`. |
| FriendCodeEntryScreen +0x20 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_handle_keypad`, `menu_keyboard_init`. |
| FriendCodeEntryScreen +0x24 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_update`, `menu_friend_input_handle_keypad`, `menu_friend_input_slide_in`. |
| FriendCodeEntryScreen +0x6c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_register_friend`, `menu_friend_input_slide_answer`, `menu_friend_input_handle_keypad`. |
| FriendCodeEntryScreen +0x8a | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_friend_input_register_friend`, `menu_friend_input_slide_confirm`. |
| FriendCodeState +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_create_select_screen`, `menu_get_mode_entry_index_maybe`, `race_classify_result_maybe`. |
| FriendCodeState +0x2 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_dispatch_session_event`, `net_handle_slot_packet_event`, `net_handle_slot_status_packet`. |
| FriendCodeState +0x5 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_send_session_status`, `menu_reset_record_state`. |
| FriendCodeState +0x6 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_start_channel_send_maybe`, `net_send_session_status`, `net_reinitialize_session`. |
| FriendCodeState +0x9 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_start_channel_send_maybe`, `menu_reset_record_state`, `WM_StartScan`. |
| FriendCodeState +0xa | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_session_message`, `net_dispatch_session_event`, `net_handle_slot_packet_event`. |
| FriendCodeState +0xb | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `net_start_channel_send_maybe`, `WM_StartScan`. |
| FriendCodeState +0xd | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `net_start_channel_send_maybe`, `WM_StartScan`. |
| FriendCodeState +0xe | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_race_setup_record_maybe`, `net_handle_slot_packet_event`. |
| FriendCodeState +0xf | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `WM_StartScan`. |
| FriendCodeState +0x12 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_session_message`, `net_handle_slot_packet_event`, `net_reinitialize_session`. |
| FriendCodeState +0x14 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_send_session_start`, `net_alloc_session_buffers`. |
| FriendCodeState +0x15 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_session_record`, `net_build_race_setup_record_maybe`. |
| FriendCodeState +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_start_channel_send_maybe`, `net_reinitialize_session`, `net_alloc_session_buffers`. |
| FriendCodeState +0x20 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_reinitialize_session`, `net_alloc_session_buffers`. |
| FriendCodeState +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `net_reinitialize_session`, `net_alloc_session_buffers`. |
| FriendCodeState +0x2c | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_reinitialize_session`, `net_alloc_session_buffers`. |
| FriendCodeState +0x32 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_session_record`, `net_build_race_setup_record_maybe`. |
| FriendCodeState +0x36 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_session_record`, `net_handle_slot_phase_maybe`. |
| FriendCodeState +0x44 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_randomize_karts`, `net_append_slot_record`. |
| FriendCodeState +0x48 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_append_slot_record`, `net_dispatch_session_event`, `net_handle_slot_status_packet`. |
| FriendCodeState +0x84 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_screen_state`, `net_pop_pending_message_maybe`, `net_append_slot_record`. |
| FriendCodeState +0x86 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_reset_session`, `net_send_transfer_end_step_maybe`. |
| FriendCodeState +0x432 | No direct matching source window; function association alone is inconclusive. Users include `net_send_payload`, `net_dispatch_session_event`, `net_refresh_player_records`. |
| FriendCodeState +0x436 | No direct matching source window; function association alone is inconclusive. Users include `net_update_slot_connection_maybe`, `net_handle_session_phase_maybe`, `net_send_command_9`. |
| FriendCodeState +0x438 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_update_slot_connection_maybe`, `net_handle_slot_packet_event`, `net_match_received_slot_maybe`. |
| FriendCodeState +0x439 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `net_start_channel_send_maybe`, `net_reset_session`. |
| FriendCodeState +0x43a | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_dispatch_session_event`, `net_reset_session`. |
| FriendCodeState +0x43b | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_update_slot_connection_maybe`, `net_handle_slot_packet_event`, `net_start_channel_send_maybe`. |
| FriendCodeState +0x43c | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_update_slot_connection_maybe`, `net_reset_session`. |
| FriendCodeState +0x440 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `net_start_channel_send_maybe`. |
| FriendCodeState +0x444 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_handle_slot_packet_event`, `net_start_channel_send_maybe`. |
| FriendCodeState +0x448 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_dispatch_session_event`, `net_send_session_header_maybe`. |
| FriendCodeState +0x44c | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_dispatch_session_event`, `net_send_session_header_maybe`. |
| FriendCodeState +0x450 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_dispatch_session_event`, `net_send_session_header_maybe`. |
| FriendCodeState +0xeac | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_refresh_player_records`, `net_send_session_status`. |
| FriendCodeState +0x15bc | No direct matching source window; function association alone is inconclusive. Users include `net_send_session_field`, `net_request_session_reset`, `net_refresh_player_records`. |
| FriendCodeState +0x15c0 | No direct matching source window; function association alone is inconclusive. Users include `net_refresh_player_records`, `net_send_session_status`, `net_alloc_session_buffers`. |
| FriendCodeState +0x15c4 | No direct matching source window; function association alone is inconclusive. Users include `net_clear_session_buffers`, `net_alloc_session_buffers`. |
| FriendCodeState +0x15c8 | No direct matching source window; function association alone is inconclusive. Users include `input_poll_controllers`, `net_alloc_session_buffers`, `net_is_ready_maybe`. |
| FriendCodeState +0x15ec | No direct matching source window; function association alone is inconclusive. Users include `net_send_session_status`, `net_enter_mode_7`, `net_poll_slot_readiness_maybe`. |
| FriendCodeState +0x1d00 | No direct matching source window; function association alone is inconclusive. Users include `net_write_slot_packet`, `net_finish_session_shutdown`. |
| FriendCodeState +0x1d54 | No direct matching source window; function association alone is inconclusive. Users include `net_handle_session_message`, `handle_state_event_maybe`. |
| FriendCodeState +0x1eac | No direct matching source window; function association alone is inconclusive. Users include `net_merge_pending_slot_mask`, `net_handle_slot_status_packet`. |
| FriendCodeState +0x1ee8 | No direct matching source window; function association alone is inconclusive. Users include `net_dispatch_session_event`, `net_handle_slot_status_packet`. |
| GamePart +0x24 | Access context does not resolve a unique semantic role or reliable owner type. Users include `invoke_callback_maybe_04ad24`, `scene_alloc_state_buffer`, `race_init_lighting`. |
| GamePart +0x3e | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_init_player_record_maybe`, `flow_reset_record_state`. |
| GamePart +0x40 | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_init_player_record_maybe`, `net_init_download_child`, `net_init_download_parent`. |
| GamePart +0x44 | Access context does not resolve a unique semantic role or reliable owner type. Users include `game_set_state_field_maybe_03a8e0`, `race_init_player_record_maybe`. |
| GamePart +0x54 | Access context does not resolve a unique semantic role or reliable owner type. Users include `scene_run_until_idle`, `race_init_player_record_maybe`. |
| InfoMessageScreen +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_staff_roll`, `results_create_screen`. |
| InfoMessageScreen +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_row_cell_flags`, `menu_refresh_display_rows`, `menu_handle_phase2_input`. |
| InfoMessageScreen +0x10 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_handle_phase2_input`, `results_create_screen`. |
| InfoMessageScreen +0x14 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_handle_phase2_input`, `results_create_screen`. |
| InfoMessageScreen +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_animate_exit_offset`, `menu_handle_phase2_input`, `results_create_screen`. |
| InfoMessageScreen +0x54 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_staff_roll`, `menu_set_info_cell_attributes`, `results_update_rows`. |
| InfoMessageScreen +0x5c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_staff_roll`, `results_update_rows`. |
| InfoMessageScreen +0x74 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_staff_roll`, `menu_set_info_cell_attributes`, `results_load_ranking_resources_199444`. |
| InfoMessageScreen +0x78 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_staff_roll`, `menu_refresh_display_rows`, `menu_set_info_cell_attributes`. |
| InfoMessageScreen +0x88 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_animate_exit_offset`, `results_create_screen`, `results_update_rows`. |
| InfoMessageScreen +0x8c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_animate_exit_offset`, `results_create_screen`, `results_update_rows`. |
| Item +0x54 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_calc_path_progress`, `item_update_collision_and_motion`, `item_collide_course_object`. |
| Item +0x58 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_calc_path_progress`, `item_check_target_range`, `item_update_collision_and_motion`. |
| Item +0x13a | No direct matching source window; function association alone is inconclusive. Users include `race_motion_update_speed`, `kart_update_physics_damping`. |
| Item +0x198 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_bob_omb_init`, `kart_update_physics_damping`. |
| Kart +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `course_rebuild_object_lists`, `course_water_update_tide`. |
| Kart +0x2 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `init_0de6a8`. |
| Kart +0x4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `course_rebuild_object_lists`, `obj_chain_chomp_reset_to_stake`. |
| Kart +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`, `course_rebuild_object_lists`, `course_rebuild_object_lists`. |
| Kart +0xc | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `course_rebuild_object_lists`, `course_rebuild_object_lists`. |
| Kart +0x10 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `course_rebuild_object_lists`, `course_rebuild_object_lists`. |
| Kart +0x14 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `course_rebuild_object_lists`, `course_rebuild_object_lists`. |
| Kart +0x18 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `course_rebuild_object_lists`, `obj_chain_chomp_reset_to_stake`. |
| Kart +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_init_vector_table`, `obj_init_heading`. |
| Kart +0x20 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `obj_chain_chomp_init_path`, `obj_chain_chomp_init_chained`. |
| Kart +0x24 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_update_held_chain`, `item_init_vector_table`. |
| Kart +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `course_rebuild_object_lists`, `item_init_vector_table`. |
| Kart +0x2c | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `course_rebuild_object_lists`, `item_init_vector_table`. |
| Kart +0x30 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `course_rebuild_object_lists`, `course_rebuild_object_lists`. |
| Kart +0x34 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_engine_sound`, `race_rank_by_distance_maybe`, `item_init_vector_table`. |
| Kart +0x38 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_init_vector_table`, `race_update_kart_checkpoint`, `kart_reset_base_state`. |
| Kart +0x3c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_wading`, `item_init_vector_table`, `race_update_kart_checkpoint`. |
| Kart +0x40 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_chain_chomp_init_chained`, `item_init_vector_table`, `race_update_kart_checkpoint`. |
| Kart +0x50 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_compute_ground_facing`, `kart_init_start_pose`, `kart_apply_remote_snapshot`. |
| Kart +0x5c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_compute_ground_facing`, `kart_update_wading`, `spline`. |
| Kart +0x68 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_compute_ground_facing`, `kart_respawn_at_checkpoint`, `kart_cannon_fly`. |
| Kart +0x6c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_compute_ground_facing`, `display_init_object`, `kart_respawn_at_checkpoint`. |
| Kart +0x70 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_compute_ground_facing`, `kart_respawn_at_checkpoint`, `kart_cannon_fly`. |
| Kart +0x78 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_mini_turbo`, `kart_update_steering_ffc27c`, `itcm_in_a_given_game_mode_mode_01ffc558`. |
| Kart +0x7e | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_rebuild_object_lists`, `obj_init_heading`. |
| Kart +0x8c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `sub_2070398`. |
| Kart +0x90 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `kart_update_water_depth`. |
| Kart +0x94 | Access context does not resolve a unique semantic role or reliable owner type. Users include `sub_2070398`, `effect_alloc_emitter_groups`, `effect_alloc_emitter_groups`. |
| Kart +0x98 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_flipped_body`, `kart_init_start_pose`, `kart_init_object`. |
| Kart +0xa4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `kart_integrate_motion_maybe_ffae14`, `kart_compute_ground_facing`. |
| Kart +0xa8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `kart_integrate_motion_maybe_ffae14`, `kart_compute_ground_facing`. |
| Kart +0xb4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_integrate_motion_maybe_ffae14`, `display_init_object`, `kart_reset_base_state`. |
| Kart +0xda | Access context does not resolve a unique semantic role or reliable owner type. Users include `spline`, `homing`, `item_update_shell_movement`. |
| Kart +0xe0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_shell_final_approach`, `item_resolve_track_collision`. |
| Kart +0xe4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `kart_reset_base_state`. |
| Kart +0xe8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `obj_chain_chomp_update`, `obj_chain_chomp_update`. |
| Kart +0xec | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `kart_reset_base_state`. |
| Kart +0xf0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`, `camera_init_defaults`, `obj_chain_chomp_init_path`. |
| Kart +0xf4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_chain_chomp_update`, `spline`, `item_shell_steer_route`. |
| Kart +0xf8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `spline`, `item_shell_steer_route`, `homing`. |
| Kart +0xfc | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_chain_chomp_update`, `obj_chain_chomp_update`, `obj_chain_chomp_update`. |
| Kart +0x100 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_ground_tilt`, `kart_reset_base_state`, `camera_init_defaults`. |
| Kart +0x104 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_collide_moving_box`, `course_collide_moving_box`, `course_collide_moving_box`. |
| Kart +0x108 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_collide_moving_box`, `course_collide_moving_box`, `course_collide_moving_box`. |
| Kart +0x10c | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_collide_moving_box`, `course_collide_moving_box`, `course_collide_moving_box`. |
| Kart +0x110 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `kart_reset_remote_interpolation`. |
| Kart +0x114 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `kart_reset_remote_interpolation`. |
| Kart +0x118 | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_collide_moving_box`, `course_collide_moving_box`, `course_collide_moving_box`. |
| Kart +0x11c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`, `kart_apply_remote_snapshot`, `kart_reset_remote_interpolation`. |
| Kart +0x120 | Access context does not resolve a unique semantic role or reliable owner type. Users include `getter_063b50`, `kart_tick_flipped_body`, `kart_init_start_pose`. |
| Kart +0x124 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_init_physics_basis`, `item_init_ground_orientation`, `item_init_shell_movement_0f2b94`. |
| Kart +0x128 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_effect_resources_maybe`. |
| Kart +0x12c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_get_up_vector`, `kart_tick_flipped_body`, `kart_init_start_pose`. |
| Kart +0x130 | Access context does not resolve a unique semantic role or reliable owner type. Users include `sub_20_f1_d70`, `item_init_physics_basis`, `item_init_physics_basis`. |
| Kart +0x134 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_init_physics_basis`, `item_init_physics_basis`, `item_launch_bob_omb`. |
| Kart +0x138 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_apply_remote_snapshot`, `kart_apply_remote_snapshot`, `kart_activate_grounded_drift`. |
| Kart +0x13c | Access context does not resolve a unique semantic role or reliable owner type. Users include `course_collide_moving_box`, `sub_20_f1_d70`, `sub_20_f1_d70`. |
| Kart +0x140 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `sub_20_f1_d70`, `sub_20_f1_d70`. |
| Kart +0x144 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `sub_20_f1_d70`, `sub_20_f1_d70`. |
| Kart +0x148 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_init_physics_basis`, `item_init_shell_movement_0f2b94`. |
| Kart +0x14c | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_init_physics_basis`, `item_init_shell_movement_0f2b94`. |
| Kart +0x150 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_flipped_body`, `kart_init_start_pose`, `camera_init_defaults`. |
| Kart +0x154 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_init_physics_basis`, `item_init_physics_basis`. |
| Kart +0x158 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_shell_update_route_run`, `spline`. |
| Kart +0x15c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_flipped_body`, `kart_init_start_pose`, `camera_init_defaults`. |
| Kart +0x160 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_init_physics_basis`, `item_reflect_flat_heading`, `item_reflect_heading`. |
| Kart +0x164 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_physics`, `obj_advance_track_segment`. |
| Kart +0x168 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_flipped_body`, `kart_init_start_pose`, `camera_init_defaults`. |
| Kart +0x16c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_flipped_body`, `kart_init_start_pose`, `camera_init_defaults`. |
| Kart +0x170 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_flipped_body`, `kart_init_start_pose`, `camera_init_defaults`. |
| Kart +0x184 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_physics`, `kart_update_physics`, `kart_update_physics`. |
| Kart +0x188 | No direct matching source window; no useful function association. |
| Kart +0x18c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_physics`, `obj_advance_track_segment`, `obj_advance_track_segment`. |
| Kart +0x190 | No direct matching source window; no useful function association. |
| Kart +0x194 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_physics`, `kart_update_physics`, `obj_advance_track_segment`. |
| Kart +0x198 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_bob_omb_update`, `obj_tick_attached_object`, `obj_tick_attached_object`. |
| Kart +0x19c | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_tick_attached_object`, `kart_update_physics`, `kart_update_physics`. |
| Kart +0x1b8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`, `kart_reset_and_place`. |
| Kart +0x1bc | No direct matching source window; no useful function association. |
| Kart +0x1c0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_chain_chomp_update`. |
| Kart +0x1c4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`, `kart_reset_and_place`. |
| Kart +0x1c8 | No direct matching source window; no useful function association. |
| Kart +0x1cc | No direct matching source window; no useful function association. |
| Kart +0x1e4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`. |
| Kart +0x1e8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`. |
| Kart +0x1ec | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`. |
| Kart +0x1f0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`, `obj_init_large_piranha`. |
| Kart +0x1f4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`. |
| Kart +0x1f8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`. |
| Kart +0x220 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `spline`, `item_tick_route_steering`. |
| Kart +0x228 | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `targeting`, `homing`. |
| Kart +0x22c | Access context does not resolve a unique semantic role or reliable owner type. Users include `targeting`, `item_enter_rise_state`, `item_calc_chase_offset`. |
| Kart +0x234 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_contact_orientation_ffa0c4`, `kart_update_steering_ffc27c`, `kart_handle_hard_landing`. |
| Kart +0x236 | No direct matching source window; function association alone is inconclusive. Users include `kart_update_contact_orientation_ff9f60`, `kart_decay_wall_yaw_kick`, `kart_update_steering_ffc090`. |
| Kart +0x238 | No direct matching source window; no useful function association. |
| Kart +0x23a | No direct matching source window; function association alone is inconclusive. Users include `kart_dispatch_control`, `kart_tick_ram_damage`, `kart_tick_blast_damage`. |
| Kart +0x23c | No direct matching source window; function association alone is inconclusive. Users include `kart_tick_mini_turbo`, `kart_end_damage_spin_out`, `kart_init_launch_damage`. |
| Kart +0x24c | No direct matching source window; no useful function association. |
| Kart +0x24e | No direct matching source window; function association alone is inconclusive. Users include `item_enter_kart_linked_state`, `item_shell_home_on_target`. |
| Kart +0x25c | Access context does not resolve a unique semantic role or reliable owner type. Users include `camera_init_defaults`, `item_enter_spiral_state`, `item_enter_spiral_state`. |
| Kart +0x264 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_enter_rise_state`, `item_enter_rise_state`, `item_enter_rise_state`. |
| Kart +0x268 | No direct matching source window; no useful function association. |
| Kart +0x26c | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_blue_shell_search_target`. |
| Kart +0x270 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_enter_spiral_state`, `item_blue_shell_follow_route`, `item_enter_approach_state`. |
| Kart +0x284 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_activate_grounded_drift`, `item_enter_rise_state`, `item_enter_spiral_state`. |
| Kart +0x288 | No direct matching source window; no useful function association. |
| Kart +0x294 | No direct matching source window; no useful function association. |
| Kart +0x298 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_blue_shell_find_target`. |
| Kart +0x2a4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_query_terrain_contact`, `kart_integrate_motion_maybe_ffae14`, `kart_update_heading`. |
| Kart +0x2b0 | No direct matching source window; no useful function association. |
| Kart +0x2b2 | No direct matching source window; no useful function association. |
| Kart +0x2b4 | No direct matching source window; no useful function association. |
| Kart +0x2b8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_integrate_motion_maybe_ff9c40`, `kart_update_contact_orientation_ff9f60`, `kart_update_orientation`. |
| Kart +0x2c0 | No direct matching source window; no useful function association. |
| Kart +0x2c8 | No direct matching source window; function association alone is inconclusive. Users include `kart_query_terrain_contact`, `kart_compute_ground_facing`, `kart_tick_physics_collision`. |
| Kart +0x2ca | No direct matching source window; no useful function association. |
| Kart +0x2f0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_physics`, `kart_query_terrain_contact`, `kart_query_terrain_contact`. |
| Kart +0x2f4 | No direct matching source window; no useful function association. |
| Kart +0x2f8 | No direct matching source window; no useful function association. |
| Kart +0x2fa | No direct matching source window; no useful function association. |
| Kart +0x314 | No direct matching source window; function association alone is inconclusive. Users include `kart_tick_ram_damage`, `kart_apply_bullet_ram`, `kart_tick_blast_damage`. |
| Kart +0x31c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`. |
| Kart +0x320 | No direct matching source window; no useful function association. |
| Kart +0x324 | No direct matching source window; no useful function association. |
| Kart +0x338 | No direct matching source window; no useful function association. |
| Kart +0x344 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_launch_damage`, `kart_reset_base_state`. |
| Kart +0x34c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`. |
| Kart +0x350 | No direct matching source window; no useful function association. |
| Kart +0x354 | No direct matching source window; no useful function association. |
| Kart +0x358 | No direct matching source window; no useful function association. |
| Kart +0x35c | No direct matching source window; function association alone is inconclusive. Users include `kart_tick_ram_damage`, `kart_apply_bullet_ram`, `kart_tick_blast_damage`. |
| Kart +0x364 | No direct matching source window; function association alone is inconclusive. Users include `kart_query_terrain_contact`, `kart_start_spin_out`, `kart_reset_base_state`. |
| Kart +0x366 | No direct matching source window; function association alone is inconclusive. Users include `kart_query_terrain_contact`, `kart_start_spin_out`, `kart_spin_for_turns`. |
| Kart +0x36c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_query_terrain_contact`, `kart_start_spin_out`, `kart_reset_base_state`. |
| Kart +0x370 | No direct matching source window; function association alone is inconclusive. Users include `kart_tick_ram_damage`, `kart_apply_bullet_ram`, `kart_apply_directional_blast`. |
| Kart +0x374 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_query_terrain_contact`, `kart_reset_base_state`. |
| Kart +0x378 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_query_terrain_contact`, `kart_query_terrain_contact`. |
| Kart +0x37c | No direct matching source window; no useful function association. |
| Kart +0x384 | No direct matching source window; no useful function association. |
| Kart +0x386 | No direct matching source window; function association alone is inconclusive. Users include `kart_decay_wall_yaw_kick`, `kart_react_to_wall`, `kart_reset_base_state`. |
| Kart +0x388 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_decay_wall_yaw_kick`, `kart_record_ghost_frame`, `kart_apply_remote_snapshot`. |
| Kart +0x38a | No direct matching source window; function association alone is inconclusive. Users include `kart_update_steering_ffc090`, `kart_update_steering_ffc158`, `kart_activate_grounded_drift`. |
| Kart +0x3a4 | No direct matching source window; no useful function association. |
| Kart +0x3a8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_contact_orientation_ff9f60`, `kart_update_tilt_target`, `kart_update_orientation`. |
| Kart +0x3ac | No direct matching source window; no useful function association. |
| Kart +0x3b0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `effect_update_speed_trail_maybe`. |
| Kart +0x3b4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`. |
| Kart +0x3b8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `itcm_runs_continuous_smoke_red_blue_wheel_01ff9b70`, `effect_update_speed_trail_maybe`. |
| Kart +0x3bc | No direct matching source window; no useful function association. |
| Kart +0x3be | No direct matching source window; no useful function association. |
| Kart +0x3c0 | No direct matching source window; no useful function association. |
| Kart +0x3c4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_kart_fall_into_water_out_of_01ffa1f8`, `kart_start_fall`, `kart_reset_base_state`. |
| Kart +0x3c8 | No direct matching source window; no useful function association. |
| Kart +0x3d0 | No direct matching source window; no useful function association. |
| Kart +0x3d2 | No direct matching source window; no useful function association. |
| Kart +0x3d4 | No direct matching source window; no useful function association. |
| Kart +0x3d8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `itcm_kart_rank_change_check_reads_current_01ffc92c`, `itcm_kart_rank_change_check_reads_current_01ffc92c`, `itcm_kart_rank_change_check_reads_current_01ffc92c`. |
| Kart +0x3dc | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_dispatch_surface`, `itcm_clears_given_bits_in_kart_68_01ffa350`, `kart_handle_boost_ramp`. |
| Kart +0x3e8 | No direct matching source window; no useful function association. |
| Kart +0x3fc | No direct matching source window; no useful function association. |
| Kart +0x3fe | No direct matching source window; no useful function association. |
| Kart +0x400 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_calc_collision_sphere_center`, `kart_set_drift_animation`, `kart_tick_squash_stretch`. |
| Kart +0x438 | No direct matching source window; no useful function association. |
| Kart +0x440 | No direct matching source window; no useful function association. |
| Kart +0x444 | No direct matching source window; no useful function association. |
| Kart +0x448 | No direct matching source window; no useful function association. |
| Kart +0x450 | Access context does not resolve a unique semantic role or reliable owner type. Users include `sound_update_kart_engine_maybe`, `kart_init_voice_params`. |
| Kart +0x454 | No direct matching source window; no useful function association. |
| Kart +0x458 | No direct matching source window; no useful function association. |
| Kart +0x45c | No direct matching source window; no useful function association. |
| Kart +0x460 | No direct matching source window; no useful function association. |
| Kart +0x464 | No direct matching source window; no useful function association. |
| Kart +0x468 | No direct matching source window; no useful function association. |
| Kart +0x46c | No direct matching source window; no useful function association. |
| Kart +0x470 | No direct matching source window; no useful function association. |
| Kart +0x474 | No direct matching source window; no useful function association. |
| Kart +0x478 | No direct matching source window; no useful function association. |
| Kart +0x47c | No direct matching source window; no useful function association. |
| Kart +0x480 | No direct matching source window; no useful function association. |
| Kart +0x484 | Access context does not resolve a unique semantic role or reliable owner type. Users include `sound_set_object_callback_10a644`, `sound_clear_object_pending_callback`. |
| Kart +0x488 | Access context does not resolve a unique semantic role or reliable owner type. Users include `sound_play_pending_object_sound`, `sound_play_pending_object_sound`. |
| Kart +0x490 | Access context does not resolve a unique semantic role or reliable owner type. Users include `sound_play_kart_landing`. |
| Kart +0x494 | No direct matching source window; no useful function association. |
| Kart +0x498 | No direct matching source window; no useful function association. |
| Kart +0x49c | No direct matching source window; no useful function association. |
| Kart +0x4a0 | No direct matching source window; no useful function association. |
| Kart +0x4a4 | No direct matching source window; no useful function association. |
| Kart +0x4a8 | No direct matching source window; no useful function association. |
| Kart +0x4ac | No direct matching source window; no useful function association. |
| Kart +0x4b0 | No direct matching source window; no useful function association. |
| Kart +0x4b4 | No direct matching source window; no useful function association. |
| Kart +0x4b8 | No direct matching source window; no useful function association. |
| Kart +0x4c4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_update_speed_ffbe70`, `kart_apply_jump_pad`, `kart_reset_base_state`. |
| Kart +0x4d8 | No direct matching source window; no useful function association. |
| Kart +0x4da | No direct matching source window; function association alone is inconclusive. Users include `kart_query_terrain_contact`, `kart_react_to_wall`, `kart_reset_base_state`. |
| Kart +0x4dc | No direct matching source window; no useful function association. |
| Kart +0x4de | No direct matching source window; no useful function association. |
| Kart +0x4e0 | No direct matching source window; no useful function association. |
| Kart +0x4e2 | No direct matching source window; no useful function association. |
| Kart +0x4e4 | No direct matching source window; no useful function association. |
| Kart +0x4ec | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`. |
| Kart +0x4f0 | No direct matching source window; no useful function association. |
| Kart +0x4f4 | No direct matching source window; no useful function association. |
| Kart +0x4f8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_reset_base_state`. |
| Kart +0x4fc | No direct matching source window; no useful function association. |
| Kart +0x504 | No direct matching source window; no useful function association. |
| Kart +0x506 | No direct matching source window; no useful function association. |
| Kart +0x538 | No direct matching source window; function association alone is inconclusive. Users include `kart_tick_mini_turbo`, `kart_end_damage_spin_out`, `kart_init_launch_damage`. |
| Kart +0x540 | No direct matching source window; function association alone is inconclusive. Users include `kart_check_slipstream`. |
| Kart +0x554 | No direct matching source window; function association alone is inconclusive. Users include `kart_apply_remote_snapshot`, `kart_reset_of_render_state`. |
| Kart +0x598 | No direct matching source window; no useful function association. |
| Kart +0x5a0 | No direct matching source window; no useful function association. |
| KartP12C +0x98 | No direct matching source window; no useful function association. |
| KartP12C +0x9c | No direct matching source window; no useful function association. |
| KartP12C +0xa0 | No direct matching source window; no useful function association. |
| KartP2CC +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_race_setup_record_maybe`. |
| KartP2CC +0x4 | No direct matching source window; no useful function association. |
| KartP2CC +0xc | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_race_setup_record_maybe`, `net_build_race_setup_record_maybe`. |
| KartP2CC +0xe | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_race_setup_record_maybe`. |
| KartP2CC +0x10 | No direct matching source window; no useful function association. |
| KartP2CC +0x14 | No direct matching source window; no useful function association. |
| KartP2CC +0x18 | No direct matching source window; no useful function association. |
| KartP2CC +0x1c | No direct matching source window; no useful function association. |
| KartP2CC +0x20 | No direct matching source window; no useful function association. |
| KartP2CC +0x24 | No direct matching source window; no useful function association. |
| KartP2CC +0x28 | No direct matching source window; no useful function association. |
| KartP2CC +0x30 | No direct matching source window; no useful function association. |
| KartP2CC +0x32 | Access context does not resolve a unique semantic role or reliable owner type. Users include `net_build_race_setup_record_maybe`. |
| KartP2CC +0x34 | No direct matching source window; no useful function association. |
| KartP2CC +0x38 | No direct matching source window; no useful function association. |
| KartP2CC +0x78 | No direct matching source window; no useful function association. |
| KartP514 +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_activate_grounded_drift`, `kart_activate_grounded_drift`, `VEC_Subtract`. |
| KartP514 +0x4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `VEC_Subtract`, `VEC_Add`, `VEC_Add`. |
| KartP514 +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `VEC_Subtract`, `VEC_Add`, `VEC_Add`. |
| KartP514 +0x10 | No direct matching source window; no useful function association. |
| KartP514 +0x14 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_tick_physics_collision`, `kart_tick_physics_collision`. |
| KartP514 +0x18 | No direct matching source window; no useful function association. |
| KartP514 +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_network_buffer`. |
| KartP514 +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_network_buffer`. |
| KartP514 +0x34 | No direct matching source window; no useful function association. |
| KartP514 +0x38 | No direct matching source window; no useful function association. |
| KartP514 +0x3c | No direct matching source window; no useful function association. |
| KartP514 +0x40 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_network_buffer`. |
| KartP514 +0x4c | No direct matching source window; no useful function association. |
| KartP514 +0x50 | No direct matching source window; no useful function association. |
| KartP514 +0x54 | No direct matching source window; no useful function association. |
| KartP514 +0x58 | No direct matching source window; no useful function association. |
| KartP514 +0x98 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_record_ghost_frame`. |
| KartP514 +0x9c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_record_ghost_frame`. |
| KartP514 +0xa0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_record_ghost_frame`. |
| KartP514 +0xa8 | No direct matching source window; no useful function association. |
| KartP514 +0xac | No direct matching source window; no useful function association. |
| KartP514 +0xb0 | No direct matching source window; no useful function association. |
| KartP514 +0xb4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_apply_remote_snapshot`, `kart_init_network_buffer`, `kart_reset_and_place`. |
| KartP590 +0x1c | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_rank_by_distance_maybe`, `race_rank_by_distance_maybe`, `race_rank_by_distance_maybe`. |
| KartP590 +0x2c | Access context does not resolve a unique semantic role or reliable owner type. Users include `kart_init_start_pose`. |
| KartP590 +0x30 | No direct matching source window; no useful function association. |
| KartP590 +0x5c | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_rank_by_distance_maybe`, `race_rank_by_distance_maybe`, `race_rank_by_distance_maybe`. |
| KartP590 +0x60 | Access context does not resolve a unique semantic role or reliable owner type. Users include `race_rank_by_distance_maybe`, `race_rank_by_distance_maybe`, `race_rank_by_distance_maybe`. |
| KartP590 +0xa4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `item_bullet_bill_activate`. |
| KartP9C +0x10 | Access context does not resolve a unique semantic role or reliable owner type. Users include `obj_init_large_piranha`. |
| KartP9C +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `input_get_touch_position`, `input_update_touch`. |
| KartP9C +0x2a | Access context does not resolve a unique semantic role or reliable owner type. Users include `input_get_touch_position`, `input_update_touch`. |
| KartP9C +0x2c | Access context does not resolve a unique semantic role or reliable owner type. Users include `input_get_touch_position`, `input_update_touch`. |
| KartP9C +0x2e | Access context does not resolve a unique semantic role or reliable owner type. Users include `input_get_touch_position`, `input_update_touch`. |
| KartP9C +0x30 | No direct matching source window; no useful function association. |
| KartP9C +0x32 | No direct matching source window; no useful function association. |
| KartP9C +0x34 | No direct matching source window; no useful function association. |
| KartPreviewMenu +0x0 | Unidentified users and ambiguous access context. Users include `unnamed_02078158`, `unnamed_02078158`, `unnamed_02078158`. |
| KartPreviewMenu +0x4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `getter_077a5c`, `unnamed_02078158`, `unnamed_02078158`. |
| KartPreviewMenu +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `getter_077a4c`, `unnamed_02078158`, `unnamed_02078158`. |
| KartPreviewMenu +0x2c | Unidentified users and ambiguous access context. Users include `unnamed_02078158`, `unnamed_02078158`, `unnamed_02078c58`. |
| MainMenuScreen +0x0 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_dispatch_screen_state_117418`, `menu_create_screen_117e24`, `menu_refresh_result_card`. |
| MainMenuScreen +0x4 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_dispatch_screen_state_117418`, `menu_update_tile_positions`, `menu_update_grid_layout`. |
| MainMenuScreen +0x8 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_dispatch_screen_state_117418`, `menu_create_screen_117e24`, `menu_update_four_cell_highlight`. |
| MainMenuScreen +0xc | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_dispatch_screen_state_117418`, `menu_draw_eight_items`. |
| MainMenuScreen +0x10 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_dispatch_screen_state_117418`, `menu_create_screen_117e24`, `menu_draw_eight_items`. |
| MainMenuScreen +0x28 | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_create_screen_117e24`, `menu_enter_result_message_state`. |
| MainMenuScreen +0x3c | Access context does not resolve a unique semantic role or reliable owner type. Users include `menu_update_tile_positions`, `menu_step_transition`, `menu_handle_grid_input`. |

## Validation

The verification command checks every changed CSV line against HEAD: only original placeholder names may differ, all other bytes must match, and every replacement must satisfy length, syntax and alias-aware uniqueness constraints. All reviewed decisions must correspond to an actual changed row. No commit or push was performed.
