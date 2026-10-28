"""Collect local-only ROM evidence and apply reviewed placeholder names.

Evidence JSON contains generated code: keep --output outside the repository.
Run collect SOURCE --output PATH, then apply, verify, and report PATH.
"""
import argparse
import csv
import io
import json
import re
import subprocess
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r'f_[0-9a-fA-F]+$')


def rows(name):
    return list(csv.DictReader((ROOT / 'dictionary' / name).open(encoding='utf-8-sig', newline='')))


def canonical_map():
    result = {}
    for row in rows('structs.csv'):
        for alias in [row['name']] + row['aliases'].split(';'):
            if alias:
                result[alias.lower()] = row['name']
                result[re.sub(r'(?<!^)(?=[A-Z])', '_', alias).lower()] = row['name']
    return result


def collect(source, output):
    if output.resolve().is_relative_to(ROOT):
        raise ValueError('Evidence with ROM snippets must stay outside the repository')
    aliases = canonical_map()
    canon = lambda s: aliases.get(s.lower(), aliases.get(s.replace('_', '').lower(), s))
    fields = rows('fields.csv')
    accessors = defaultdict(set)
    for row in fields:
        accessors[(canon(row['struct']), row['name'])].add(int(row['offset'], 0))
    wanted = defaultdict(list)
    original_fields = list(csv.DictReader(io.StringIO(baseline().decode('utf-8-sig'))))
    for row in original_fields:
        if PLACEHOLDER.fullmatch(row['name']):
            wanted[(canon(row['struct']), int(row['offset'], 0))].append(row)
    names = {}
    for filename in ['functions.csv', 'sdk_functions.csv', 'game_names.csv']:
        for row in rows(filename):
            if row.get('name'):
                names[int(row['address'], 0) & ~1] = row['name']
    uses = defaultdict(set)
    by_function = defaultdict(set)
    for row in rows('field_uses.csv'):
        key = (canon(row['struct']), int(row['offset'], 0))
        if key in wanted:
            addr = int(row['function'], 0) & ~1
            uses[key].add(addr)
            by_function[addr].add(key)
    evidence = {k: [] for k in wanted}
    fn_re = re.compile(r'^pub fn f_\w+_([0-9A-Fa-f]{8})\(')
    access_re = re.compile(r'\b(\w+)::(\w+)\(m,')
    raw_re = re.compile(r'wrapping_add\(0x([0-9a-fA-F]+)u32\)')
    call_re = re.compile(r'\b(?:crate::)?(?:\w+::)*([A-Za-z_]\w*)\(c, m,')
    paths = sorted(source.glob('part_*/src/lib.rs'))
    if not paths:
        raise ValueError('No generated source found')
    for path in paths:
        lines = path.read_text(encoding='utf-8').splitlines()
        addr = None
        for i, line in enumerate(lines):
            match = fn_re.match(line)
            if match:
                addr = int(match[1], 16) & ~1
            # Named wrappers follow their raw function and offer typed accesses.
            if addr is None:
                continue
            hits = set()
            for access in access_re.finditer(line):
                struct = canon(access[1])
                accessor = access[2].removeprefix('set_')
                offsets = accessors.get((struct, accessor), set())
                if not offsets and re.fullmatch(r'f_[0-9a-fA-F]+', accessor):
                    offsets = {int(accessor[2:], 16)}
                for offset in offsets:
                    key = (struct, offset)
                    if key in wanted:
                        hits.add((key, 'typed' if len(offsets) == 1 else 'typed_alias_candidate'))
            for access in raw_re.finditer(line):
                for key in by_function.get(addr, ()):
                    if key[1] == int(access[1], 16):
                        hits.add((key, 'raw_candidate'))
            for key, kind in hits:
                lo, hi = max(0, i - 3), min(len(lines), i + 5)
                snippet = lines[lo:hi]
                evidence[key].append(dict(function=names.get(addr, f'unnamed_{addr:08x}'),
                    address=f'0x{addr:08X}', source=str(path), line=i + 1,
                    kind=kind, snippet=snippet,
                    callees=sorted(set(call_re.findall('\n'.join(snippet))) |
                        {names.get(int(a, 16) & ~1, f'unnamed_{a}') for a in re.findall(r'm.call\(c, 0x([0-9a-fA-F]+)', '\n'.join(snippet))})))
    result = []
    for key, group in wanted.items():
        result.append(dict(struct=key[0], offset=hex(key[1]), rows=group,
            functions=[dict(address=f'0x{a:08X}', name=names.get(a, 'unnamed')) for a in sorted(uses[key])],
            accesses=evidence[key]))
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'{sum(map(len, wanted.values()))} placeholder rows, {len(result)} alias-normalized fields; '
          f'{sum(bool(r["accesses"]) for r in result)} with source accesses')


# Reviewed decisions keyed by canonical structure and offset. Values are a name
# and a concise interpretation; source snippets remain in the local evidence.
DECISIONS = {}


def decisions(struct, text):
    for line in text.strip().splitlines():
        offset, name, reason = line.strip().split('|', 2)
        DECISIONS[(struct, int(offset, 16))] = (name, reason)


decisions('Kart', '''
44|motion_state_flags|Motion integration and mini-turbo handling test individual masks in the movement-state word.
48|terrain_state_flags_maybe|Terrain dispatch and ground-facing code test this auxiliary state word; not all bits are understood.
4c|active_effect_flags|Mini-turbo and damage handlers test and modify masks in this effect-state word.
54|facing_axis_y_maybe|Ground-facing projection multiplies this component alongside the adjacent facing axis components.
58|facing_axis_z_maybe|Ground-facing projection uses this as the third component of the vector beginning at the up axis.
60|reverse_axis_y_maybe|Ground-facing update stores the negation of the facing vector's middle component here.
64|reverse_axis_z_maybe|Ground-facing update stores the negation of the facing vector's third component here.
74|player_slot_id|Used to index the per-racer item record table with stride 528 in terrain contact handling.
7c|racer_state_bits|Mini-turbo and other kart routines test masks in this bitfield.
80|world_position_x|Ghost recording serializes this vector's first component; start pose and remote snapshots set it.
84|world_position_y|Contact orientation copies this into ground height; launch damage saves it as the initial height.
88|world_position_z|Ghost recording shifts this third position component right by ten and stores it after the other coordinates.
9c|owner_position_y_maybe|Start-pose setup copies this into the smoothed Y position; layout views disagree on the owner type.
a0|owner_position_z_maybe|Start-pose setup copies this into smoothed Z immediately after copying owner Y.
ac|motion_vector_z_maybe|Motion integration scales it with the two preceding motion-vector components.
b0|velocity_axis_x_maybe|Motion integration multiplies the vector beginning here by a common fixed-point factor.
b8|velocity_axis_z_maybe|Motion integration scales this third component alongside the preceding velocity components.
bc|render_scale_x|Controls/physics multiplies auxiliary scale and body scale into this render scale component.
c0|render_scale_y|Controls/physics writes the Y render scale after fixed-point multiplication of scale factors.
c4|render_scale_z|Collision-radius calculation multiplies this scale by the stats contact offset.
c8|bounce_velocity|Added to bounce height during motion integration.
cc|speed_limit_primary_maybe|Speed-limit update compares this cap with the adjacent alternate speed cap.
d0|speed_limit_secondary_maybe|Speed-limit update compares the two cap candidates; exact source of each cap remains uncertain.
d4|slope_speed_factor_maybe|Ground-facing calculation writes this slope-related value before speed calculation uses it.
d8|boost_speed_factor_maybe|Slipstream and item activation modify this speed factor; ground-facing also resets it.
dc|surface_speed_factor_maybe|Surface dispatch reads this together with the surface-specific speed table in kart stats.
174|visual_position_x|Flipped-body tick copies the first coordinate from the selected position pointer here.
178|visual_position_y|Flipped-body tick copies the middle coordinate from the selected position pointer here.
17c|visual_position_z|Flipped-body tick copies the third coordinate from the selected position pointer here.
180|damage_mode|Terrain contact compares this state with six; ram and blast handlers dispatch on the same state.
1b4|body_basis_ptr_maybe|Flipped-body tick selects an internal basis pointer and stores it here.
1d0|contact_radius|Terrain collision passes this radius with contact vectors; radius getter reads it.
1d8|contact_center_x|Kart contact subtracts the first contact-center coordinates of two karts before overlap tests.
1dc|contact_center_y|Kart contact subtracts the middle contact-center coordinates and compares against the overlap distance.
1e0|contact_center_z|Kart contact subtracts the third contact-center coordinates and compares against the overlap distance.
1fc|wall_push_x_maybe|Tilt-target update tests this and the next two components for zero; wall-reaction code updates the vector.
200|wall_push_y_maybe|Tilt-target update tests the middle component of the wall-reaction vector for zero.
204|wall_push_z_maybe|Tilt-target update tests the third component of the wall-reaction vector for zero.
208|contact_state_ptr_maybe|Tilt-target and effect cleanup dereference this pointer then test the first word for zero.
20c|pose_override_ptr_maybe|Object initialization tests this optional pointer while selecting pose data.
210|checkpoint_state_ptr_maybe|Object initialization tests this pointer; respawn-checkpoint restoration and reset use it.
214|pose_update_callback_maybe|Object initialization stores a code pointer here when choosing a pose update path.
218|body_update_callback_maybe|Object initialization writes the same code pointer here and in the next callback slot.
21c|body_finish_callback_maybe|Initialized to the same code pointer as the preceding callback; precise invocation phase is unclear.
224|respawn_callback|Respawn-hook code reads this field and calls it indirectly.
230|collision_update_callback|Collision update reads this pointer and invokes it with the kart as its first argument.
240|surface_grip_factor_maybe|Surface dispatch writes this factor from the current terrain data.
244|ground_normal_x|Ground-facing projection reads this and the next two words as the terrain normal vector.
248|ground_normal_y|Ground-facing tests the middle normal component against zero before slope handling.
250|contact_normal_x_maybe|Kart contact projects displacement onto the vector beginning here.
254|contact_normal_y_maybe|Kart contact multiplies the middle component of the contact projection vector.
258|contact_normal_z_maybe|Kart contact multiplies the third component of the contact projection vector.
260|vertical_velocity|Terrain contact compares this signed velocity with zero; jump-pad and flight code also use it.
274|object_push_decay_maybe|Terrain contact multiplies this object-push value by a fixed-point decay factor.
278|initial_heading_x_maybe|Start-pose initialization copies three consecutive heading values here from the spawn record.
27c|initial_heading_y_maybe|Start-pose initialization copies the second heading value from the spawn record here.
280|initial_heading_z_maybe|Start-pose initialization copies the third heading value from the spawn record here.
28c|hop_axis_y_maybe|Grounded-drift activation multiplies this vector component while calculating the hop direction.
290|hop_axis_z_maybe|Grounded-drift activation uses this forward component alongside the preceding hop-vector component.
29c|item_effect_mode_maybe|Bullet, ghost and star activation and fall handling write this item-effect mode.
2a0|normalized_speed_maybe|Tilt-target update multiplies this speed ratio into the tilt response.
2a8|forward_velocity_maybe|Terrain contact passes this speed to response calculations; steering and engine sound also read it.
2ac|ground_contact_height|Contact-orientation update copies the kart's world Y position into this height.
2bc|hop_height|Motion integration adds bounce velocity to this bounce-height accumulator.
2c4|steering_direction_maybe|Steering update negates this signed direction when computing turn response.
2cc|physics_stats_ptr|Surface dispatch reads this pointer and then accesses kart-stats surface parameters.
2d0|push_weight_state_ptr_maybe|Kart push-weight calculation dereferences this pointer at the second word before combining kart weights.
2d4|lean_response_maybe|Motion integration and steering use this signed lean value and compare it with zero.
2d8|contact_impulse_x_maybe|Terrain contact subtracts projected collision response from this three-component impulse vector.
2dc|contact_impulse_y_maybe|Terrain contact subtracts the middle projected collision-response component here.
2e0|contact_impulse_z_maybe|Terrain contact subtracts the third projected collision-response component here.
2e4|wall_impulse_x_maybe|Terrain contact passes this vector to VEC_DotProduct; wall-reaction code also writes it.
2e8|wall_impulse_y_maybe|Terrain contact subtracts the middle component of the second collision-response vector here.
2ec|wall_impulse_z_maybe|Terrain contact subtracts the third component of the second collision-response vector here.
2fc|mini_turbo_charge_stage|Charge update increments this stage and compares against two and three before changing wheel flares.
300|drift_left_press_count_maybe|Charge update increments the first halfword counter for one steering button and compares it with its neighbor.
302|drift_right_press_count_maybe|Charge update increments the second halfword counter for the opposite steering button; exact left/right assignment is tentative.
304|drift_press_source_a_maybe|Charge update compares this pointer with the first steering counter's location.
308|drift_press_source_b_maybe|Charge update compares this pointer with the second steering counter's location.
30c|drift_input_cooldown|Charge update decrements this timer and reloads ten after an accepted steering press.
310|cpu_control_ptr|Passed to CPU recovery and fallback-reset callbacks together with the racer index.
318|damage_roll_phase_maybe|Ram-damage tick accumulates roll rate into this roll-progress field.
334|launch_sine_sample_maybe|Launch-damage tick stores a signed trigonometric table sample here after shifting an angular phase.
33c|launch_rotation_phase_maybe|Launch-damage tick adds 1000 to this signed angular accumulator.
340|launch_origin_height|Launch-damage initialization saves world Y here; its tick compares current world Y against it.
348|launch_elapsed_ticks|Launch-damage tick compares this counter with two and initialization resets it.
360|damage_roll_increment_maybe|Ram-damage tick adds this roll rate to the roll-progress accumulator.
368|spin_rotation_phase_maybe|Terrain handling adds the adjacent spin increment to this spin-progress accumulator.
380|airborne_frame_count|Contact-orientation update compares this airborne counter with five before changing orientation behavior.
38c|speed_cap_multiplier_maybe|Speed update multiplies this cap factor by the current scale.
394|size_speed_multiplier_maybe|Speed update multiplies this scale with the cap factor; flatten and shrink handlers update it.
398|flatten_scale_multiplier_maybe|Visual-scale reset and flatten tick restore this factor to fixed-point one.
39c|object_speed_factor_maybe|Speed update combines this value with cap and size multipliers; object contact sets it.
3a0|object_speed_floor_maybe|Speed update clamps forward speed upward to this value when the object-contact override is active.
3cc|driver_voice_animation_maybe|Control dispatch passes this voice-animation value to a driver request routine.
3e0|ground_surface_kind|Surface dispatch stores the decoded surface type and uses it to index a surface table.
3e4|ground_surface_variant|Surface dispatch stores the upper halfword of the terrain result as its surface variant.
3ec|steering_target_rate_maybe|Steering update writes the target turn value here before rate adjustment.
3f0|steering_current_rate_maybe|Steering update reads this signed turn rate and takes its magnitude.
3f4|water_probe_height_maybe|Water-depth update multiplies this height offset by render scale before querying water height.
3f8|airborne_scale_factor_maybe|Contact-orientation update sets this factor immediately before testing airborne-frame count.
404|squash_phase_a_maybe|Squash/stretch tick loads this value from an animation-indexed table.
408|squash_phase_b_maybe|Squash/stretch tick loads this second value from an animation-indexed table.
40c|landing_effect_stamp_maybe|Hard-landing code stores a getter result here; mini-turbo tick compares it with zero.
410|boost_effect_stamp_maybe|Mini-turbo tick conditionally captures a getter result here after testing the boost flag.
414|squash_factor_a_maybe|Squash/stretch tick writes this table-selected factor together with the adjacent factor.
418|squash_factor_b_maybe|Squash/stretch tick writes the second table-selected factor here and can copy it into its neighbor.
41c|body_scale_factor_x_maybe|Controls/physics multiplies this body factor by the auxiliary X scale to obtain render X scale.
420|body_scale_factor_y_maybe|Controls/physics multiplies this body factor by the auxiliary Y scale to obtain render Y scale.
424|body_scale_factor_z_maybe|Controls/physics multiplies this body factor by the auxiliary Z scale to obtain render Z scale.
428|auxiliary_scale_x|Controls/physics multiplies this by the body X factor to form render X scale.
42c|auxiliary_scale_y|Controls/physics multiplies this by the body Y factor to form render Y scale.
430|auxiliary_scale_z|Controls/physics multiplies this by the body Z factor to form render Z scale.
434|auxiliary_scale_w_maybe|Controls/physics multiplies this fourth scale factor by render Y scale.
44c|last_contact_object_maybe|Object-contact handling caches a candidate pointer for kind eleven and later compares it against the current candidate.
4bc|fall_scale_snapshot_maybe|Fall handling copies the airborne scale here before setting a fall effect flag.
4c0|cached_effect_flag_maybe|A setter masks the input to a single effect bit and updates this cached value only when it differs.
4c8|collision_body_scale_maybe|Collision-radius getter combines this body scale with render scale and stats contact offset.
4cc|flipped_body_state_maybe|Flipped-body tick writes this state and base-state reset clears it.
4d0|elapsed_race_ticks|Tilt-target update compares this race counter with one hundred; physics and collision routines use it.
4d4|start_charge_amount_maybe|Start-boost and body-wobble routines use this charge; ground-facing tests it against zero.
4e8|start_charge_snapshot_maybe|Start-boost handling stores current charge plus fixed-point one here.
500|water_depth_value|Water-depth update writes the measured depth here; rolling and engine sound consume it.
508|visual_position_ptr|Flipped-body tick loads three coordinates through this pointer into visual position.
50c|orientation_quat_ptr|Passed as quaternion input to kart_quat_to_matrix; initialization points it to the internal quaternion.
510|contact_position_ptr|Initialization points it at world position; ground-facing passes it with contact offset to compute the contact center.
514|remote_motion_state_ptr|Ghost recording and snapshot application dereference this network/interpolation state pointer.
534|initial_position_ptr_maybe|Object initialization snapshots the selected position pointer here before initializing the start pose.
55c|remote_state_changed_maybe|Remote snapshot application sets this flag to one when a received state differs.
590|driver_model_state_ptr|Queried by driver animation, engine sound and body transform routines.
594|shake_amplitude_maybe|Shake tick damps this positive value then subtracts one hundred.
59c|shake_smoothed_value_maybe|Shake tick eases this value toward a scaled shake target using fixed-point interpolation.
''')

decisions('KartP508', '''
0|position_x|Flipped-body tick copies this coordinate into visual X position.
4|position_y|Flipped-body tick copies this coordinate into visual Y position.
8|position_z|Flipped-body tick copies this coordinate into visual Z position.
''')
decisions('KartP514', '''
e|received_yaw|Orientation update subtracts this halfword from local yaw to calculate the remote rotation difference.
c|previous_received_yaw_maybe|Network-buffer initialization copies the received yaw halfword into this preceding halfword.
20|sync_progress_maybe|Remote-sync tick compares this value with the current interpolation step.
24|sync_step_count_maybe|Remote-sync tick writes the interpolation step here; collision and race-start code also read it.
2c|replicated_racer_flags|Ghost recording serializes this word; item and damage routines set replicated state flags in it.
30|received_racer_flags|Snapshot application tests multiple masks in this received flags word.
44|interpolation_flags|Orientation update and snapshot application test individual bits in this control word.
48|received_motion_flags_maybe|Snapshot application tests bit two here before modifying local movement flags.
5c|interpolated_yaw_maybe|Snapshot application interpolates this value and stores its low halfword into the remote yaw output.
60|remote_bounce_height_maybe|Controls/physics adds the adjacent remote bounce velocity to this value.
64|remote_bounce_velocity_maybe|Controls/physics adds local bounce velocity to this value then uses it to advance remote bounce height.
a4|damage_event_kind_maybe|Bullet-ram and directional-blast application store five here in the replicated motion state.
''')
decisions('KartP12C', '''
48|motion_flag_bits_maybe|Physics tests a single high bit in this word before allowing a movement path.
4c|effect_flag_bits_maybe|Physics tests a combined mask in this word to gate movement.
7c|racer_flag_bits_maybe|Sound and physics routines test individual bits in this racer-state word.
''')
decisions('KartP168', '''
0|path_point_x_maybe|Chain update subtracts the object's first position coordinate from this coordinate.
8|path_point_z_maybe|Chain update subtracts the object's third position coordinate from this coordinate.
18|path_segment_ptr_maybe|Route steering passes this value to item_advance_path_segment.
''')
decisions('KartP590', '''
0|kart_model_id_maybe|Engine sound dispatches on this model identifier with a bounded case table.
4|driver_profile_id_maybe|Start-boost and voice setup use this identifier to index driver-specific tables.
8|driver_animation_ptr|Driver animation request and player flags dereference this animation state pointer.
18|material_animation_ptr_maybe|Material-attribute blending and flipped-body update use this optional animation pointer.
20|model_joint_positions_ptr_maybe|Wheel-contact update indexes this pointer in twelve-byte coordinate strides.
24|body_transform_factor_maybe|Flipped-body tick multiplies this value by a fixed-point body transform coefficient.
58|driver_action_state_maybe|Spin and damage handlers test this driver-model state against zero.
''')
decisions('MenuDialog', '''
10|update_frame_count|Dialog update increments this counter by one and initialization clears it.
''')
decisions('MapObj', '''
8|world_position_y_maybe|Spawn code stores source Y plus a height offset here and source Z in the following word; many object routines share this field.
74|racer_slot_index_maybe|Hatch collision uses this halfword as the shift count for a per-racer bitmask.
''')
decisions('Item', '''
60|path_segment_index|Path advancement multiplies this index by twelve before indexing the inline path-coordinate table.
1a0|bomb_active_flag_maybe|Bomb initialization sets one and bomb reset clears this field.
''')
decisions('MainMenuScreen', '''
2c|frame_heap_ptr|Screen teardown passes this pointer to memory destruction; screen creation stores its heap here.
80|primary_draw_state_maybe|Screen dispatch passes this value as the fourth argument with the primary cell resources to the draw routine.
84|secondary_draw_state_maybe|Screen dispatch passes this value with the secondary cell resources to the same draw routine.
88|grid_input_mode_maybe|Grid update compares this field with two when selecting how to process tile input.
''')
decisions('CourseSelectScreen', '''
4|cell_resource_ptr_maybe|Creation reads its resource metadata and passes it into cell allocation and drawing.
c|cell_bank_ptr_maybe|Creation passes this resource pointer with the cell-resource pointer to cell allocation and drawing.
18|resource_priority_maybe|Creation stores the result of fs_lookup_resource_priority here.
1c|message_resource_ptr|Creation stores fs_lookup_flagged_resource here then passes it into text_get_message.
28|frame_heap_ptr|Creation stores the new frame heap here and passes it into cell allocation.
64|grid_column_count_maybe|Creation initializes this layout count to four; refresh and screen updates use it.
84|selection_enabled_maybe|Creation initializes this selection-control field to one and input handling tests it.
''')
decisions('RecordSelectScreen', '''
b4|primary_draw_state_maybe|Screen update passes this value with the primary cell resources to the draw routine.
b8|secondary_draw_state_maybe|Screen update passes this value with the secondary cell resources to the same draw routine.
''')
decisions('ResultsRankScreen', '''
64|primary_draw_state_maybe|Ranking screen dispatch passes this value with primary cell resources into the draw routine.
68|secondary_draw_state_maybe|Ranking screen dispatch passes this value with secondary cell resources into the same draw routine.
''')
decisions('ChoiceMessageScreen', '''
38|prompt_message_id_maybe|Prompt selection saves its requested message value here before looking up the message resource.
3c|message_resource_ptr_maybe|Prompt selection stores the flagged-resource lookup result here before selected-message rendering.
64|primary_draw_state_maybe|Choice update passes this value with primary cell resources into the draw routine.
68|secondary_draw_state_maybe|Choice update passes this value with secondary cell resources into the same draw routine.
''')

decisions('FriendCodeState', '''
8|session_state_maybe|Lowest-latency slot selection writes three here; network dispatch routines use it as session state.
18|session_record_buffer_maybe|Session-record construction loads this pointer as the destination of a sixty-four-byte memory operation.
24|wireless_setup_buffer_maybe|Session-header setup copies configuration through this pointer and passes it to WM_SetWEPKey.
7c|session_packet_buffer_maybe|Session-record construction dereferences this buffer and passes it with a packet length.
85|pending_peer_index_maybe|Session-phase handling sign-extends this byte as an index into eight-byte peer records then resets it to minus one.
87|active_peer_mask_maybe|Wireless menu flow and network send routines use this byte as a peer mask.
88|lowest_latency_peer_maybe|Lowest-latency selection stores its winning peer index here or minus one if none qualifies.
8a|pending_peer_mask_maybe|Wireless menu flow checks this mask for zero and forwards it as a request mask.
43d|player_info_valid_mask_maybe|Player-info query tests this byte against one shifted by the requested player index.
456|pending_action_flags_maybe|Pending-action drain clears the low bit of this byte before returning.
''')

decisions('CharacterSelectScreen', '''
54|primary_draw_state_maybe|Select-screen update passes this value as the fourth argument with cell resources into the draw routine.
58|secondary_draw_state_maybe|Select-screen update passes this value with the second group of cell resources into its draw routine.
78|selected_record_index_maybe|Select-screen update multiplies this index by twenty-four before storing into the selected record.
''')
decisions('InfoMessageScreen', '''
70|graphics_resource_block_maybe|Ranking-resource loading passes this field's location to g2d_get_resource_block and later passes the resulting pointer to palette-manager setup.
7c|input_handler_ptr_maybe|Phase-two input handling reads this pointer before passing controller button states to its handler.
80|primary_draw_state_maybe|Staff-roll update passes this value with the primary row resources into the cell draw routine.
84|secondary_draw_state_maybe|Staff-roll update passes this value with the secondary row resources into the same draw routine.
''')
decisions('CourseSelectScreen', '''
7c|current_selection_maybe|Screen update copies this value into the following saved-selection slot; cursor and input routines use it.
80|previous_selection_maybe|Screen update copies the preceding current-selection value here before refreshing the option panel.
b4|cell_draw_state_maybe|Screen update passes this value as the fourth argument with its cell resources into the draw routine.
''')


def baseline():
    return subprocess.check_output(['git', '-c', f'safe.directory={ROOT.as_posix()}',
        'cat-file', '--filters', 'HEAD:dictionary/fields.csv'], cwd=ROOT)


def verify():
    old = baseline().splitlines(keepends=True)
    new = (ROOT / 'dictionary/fields.csv').read_bytes().splitlines(keepends=True)
    assert len(old) == len(new), 'Row count changed'
    changed = []
    for before, after in zip(old, new):
        if before == after:
            continue
        a, b = [next(csv.reader([v.decode('utf-8-sig')])) for v in (before, after)]
        assert PLACEHOLDER.fullmatch(a[2]), ('Non-placeholder edited', a)
        assert a[:2] == b[:2] and a[3:] == b[3:], ('Other cell edited', a, b)
        assert before.replace((',' + a[2] + ',').encode(), (',' + b[2] + ',').encode(), 1) == after
        assert re.fullmatch(r'[a-z][a-z0-9_]{0,31}', b[2]), b
        assert not re.search(r'(?:0x|[0-9a-f]{6,}|f_\d)', b[2]), b
        changed.append(b)
    aliases = canonical_map()
    canon = lambda s: aliases.get(s.lower(), s)
    current = rows('fields.csv')
    for row in changed:
        assert sum(canon(r['struct']) == canon(row[0]) and r['name'] == row[2] for r in current) == 1
        assert DECISIONS[(canon(row[0]), int(row[1], 0))][0] == row[2]
    assert len(changed) == len(DECISIONS)
    print(f'Verified {len(changed)} name-only edits; row order, other cells, and exact line endings preserved; '
          'all new names satisfy syntax, length and alias-aware uniqueness checks.')
    return changed


def report(evidence_path):
    changed = verify()
    evidence = json.loads(evidence_path.read_text(encoding='utf-8'))
    assert len(evidence) == 595
    indexed = {(r['struct'], int(r['offset'], 0)): r for r in evidence}
    assert set(DECISIONS) <= set(indexed)
    confident = sum(not r[2].endswith('_maybe') for r in changed)
    maybe = len(changed) - confident
    kept = len(evidence) - len(changed)
    out = ['# Field naming report', '',
        f'Reviewed **595** original placeholder rows: **{confident} confident**, **{maybe} `_maybe`**, '
        f'**{kept} kept**. Renamed **{len(changed)}** fields.', '',
        'Only placeholder name cells in `dictionary/fields.csv` changed. Existing names, types, offsets, '
        'row order and byte-for-byte line endings were preserved. Names are snake_case, at most 32 characters, '
        'and unique across each canonical struct and all its aliases. Existing duplicate legacy names were left untouched.', '',
        'The collector resolves aliases from `structs.csv`, normalizes the Thumb address bit, and joins '
        '`field_uses.csv` to function names with game names overriding SDK names and the base function table. '
        'It scans both lifted functions and named wrappers, collecting short access windows, comparisons, arithmetic, '
        'neighboring stores and resolved direct callees. Repeated accessor names across alias views are marked '
        '`typed_alias_candidate`; raw offset matches are marked `raw_candidate` because they do not prove the base pointer type. '
        'Generated type inference sometimes labels item, map-object, camera or sound objects as Kart. Such accesses '
        'alone do not establish a Kart field meaning.', '',
        f'{sum(bool(r["accesses"]) for r in evidence)} fields have collected source windows; '
        f'{sum(not r["accesses"] for r in evidence)} have no direct matching source window. '
        'A matching window can still be an unrelated pointer, stack offset, initialization-only store, '
        'or ambiguous arithmetic. These are evidence limitations, not proof that a field is unused.', '',
        'The generated ROM source was read only. Snippets are stored only in the external evidence JSON, '
        'never in this repository. This report contains original semantic summaries.', '',
        'Reproduce (use an output path outside this repository):', '', '```powershell',
        'python dictionary/field_evidence.py collect <generated-source-root> --output <external-evidence.json>',
        'python dictionary/field_evidence.py apply',
        'python dictionary/field_evidence.py verify',
        'python dictionary/field_evidence.py report <external-evidence.json>', '```', '',
        '`collect` also includes already-applied reviewed decisions, so it can be rerun after naming. '
        '`apply` is idempotent. `verify` compares against the Git HEAD baseline without modifying Git configuration.', '',
        '## Twenty examples with evidence', '',
        '| Canonical struct / offset | Name | Code evidence (paraphrased) |', '|---|---|---|']
    examples = [('Kart', x) for x in [0x74, 0x84, 0x88, 0xbc, 0xc8, 0x174, 0x1dc, 0x224, 0x230,
        0x260, 0x2ac, 0x2fc, 0x300, 0x30c, 0x310, 0x340, 0x50c]] + [('KartP508', 4), ('KartP514', 0xe), ('FriendCodeState', 0x85)]
    for key in examples:
        name, reason = DECISIONS[key]
        r = indexed[key]
        functions = list(dict.fromkeys(a['function'] for a in r['accesses']))
        if key[0] == 'Kart':
            functions = [f for f in functions if f.startswith('kart_')] or functions
        out.append(f'| {key[0]} +{key[1]:#x} | `{name}` | {reason} Functions: ' +
            ', '.join(f'`{f}`' for f in functions[:3]) + '. |')
    out += ['', '## Complete decision inventory', '',
        '| Struct / offset | New name | Rationale |', '|---|---|---|']
    for key, (name, reason) in sorted(DECISIONS.items()):
        assert indexed[key]['accesses'] or indexed[key]['functions'], key
        out.append(f'| {key[0]} +{key[1]:#x} | `{name}` | {reason} |')
    out += ['', '## Retained placeholders', '',
        'Each row below was assessed. A broad function association or a generated accessor is insufficient '
        'to invent a semantic identity. Fields with a tentative but useful identity received `_maybe`; '
        'the following fields lack a defensible identity from the inspected evidence.', '',
        '| Canonical struct / offset | Evidence available / reason retained |', '|---|---|']
    for key, r in sorted(indexed.items()):
        if key in DECISIONS:
            continue
        functions = list(dict.fromkeys(f['name'] for f in r['functions'] if f['name'] != 'unnamed'))
        functions += [a['function'] for a in r['accesses'] if a['function'] not in functions]
        if not r['accesses']:
            reason = 'No direct matching source window; ' + ('function association alone is inconclusive.' if functions else 'no useful function association.')
        elif not functions or all(f.startswith('unnamed') for f in functions):
            reason = 'Unidentified users and ambiguous access context.'
        else:
            reason = 'Access context does not resolve a unique semantic role or reliable owner type.'
        if functions:
            reason += ' Users include ' + ', '.join(f'`{f}`' for f in functions[:3]) + '.'
        out.append(f'| {key[0]} +{key[1]:#x} | {reason} |')
    out += ['', '## Validation', '',
        'The verification command checks every changed CSV line against HEAD: only original placeholder '
        'names may differ, all other bytes must match, and every replacement must satisfy length, syntax '
        'and alias-aware uniqueness constraints. All reviewed decisions must correspond to an actual changed row. '
        'No commit or push was performed.', '']
    (ROOT / 'FIELDS_REPORT.md').write_text('\n'.join(out), encoding='utf-8')
    print(f'Report: {confident} confident / {maybe} maybe / {kept} kept')


def apply():
    path = ROOT / 'dictionary/fields.csv'
    original = path.read_bytes()
    aliases = canonical_map()
    lines = original.decode('utf-8-sig').splitlines(keepends=True)
    changed = 0
    for i, line in enumerate(lines[1:], 1):
        row = next(csv.reader([line]))
        if len(row) != 4 or not PLACEHOLDER.fullmatch(row[2]):
            continue
        key = (aliases.get(row[0].lower(), row[0]), int(row[1], 0))
        if key in DECISIONS:
            name = DECISIONS[key][0]
            assert re.fullmatch(r'[a-z][a-z0-9_]{0,31}', name), name
            # Replace only this cell, preserving every other byte including EOL.
            lines[i] = line.replace(',' + row[2] + ',', ',' + name + ',', 1)
            changed += 1
    updated = ''.join(lines).encode('utf-8')
    if original.startswith(b'\xef\xbb\xbf'):
        updated = b'\xef\xbb\xbf' + updated
    # Existing names can repeat in legacy alias views; new names may not collide.
    all_rows = list(csv.DictReader(io.StringIO(updated.decode('utf-8-sig'))))
    for key, (name, _) in DECISIONS.items():
        matches = [r for r in all_rows if aliases.get(r['struct'].lower(), r['struct']) == key[0] and r['name'] == name]
        assert len(matches) == 1, (key, name, matches)
    path.write_bytes(updated)
    print(f'Changed {changed} placeholder names')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    c = sub.add_parser('collect')
    c.add_argument('source', type=Path)
    c.add_argument('--output', required=True, type=Path)
    sub.add_parser('apply')
    sub.add_parser('verify')
    r = sub.add_parser('report')
    r.add_argument('evidence', type=Path)
    args = parser.parse_args()
    if args.command == 'collect':
        collect(args.source, args.output)
    elif args.command == 'apply':
        apply()
    elif args.command == 'verify':
        verify()
    else:
        report(args.evidence)
