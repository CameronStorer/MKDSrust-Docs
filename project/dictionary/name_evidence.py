"""Collect local ROM evidence; never write generated source into the repository.

Usage: python dictionary/name_evidence.py SOURCE --output EXTERNAL_DIRECTORY
Direct calls and constant tail transfers are resolved. Global access directions are conservative:
references are always recorded, but indirect/aliased memory can remain unresolved.
Sizes describe covered instruction addresses, not inferred gaps between functions.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def collect(source, output, baseline_dir=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Evidence must be stored outside the repository')
    tiers = read_rows(source / 'tiers.csv')
    baseline_dir = Path(baseline_dir) if baseline_dir else ROOT / 'dictionary'
    coverage = {(r['segment'], int(r['entry'], 0) & ~1): r for r in read_rows(source / 'coverage.csv')} if (source / 'coverage.csv').exists() else {}
    global_names = {int(r['address'], 0): r['name'] for r in read_rows(ROOT / 'dictionary/globals.csv')}
    names = {(r['segment'], int(r['entry'], 0) & ~1): r['name'] for r in tiers}
    by_addr = defaultdict(list)
    for key in names:
        by_addr[key[1]].append(key)
    wanted = []
    for filename in ('game_names.csv', 'sdk_functions.csv'):
        for row in read_rows(baseline_dir / filename):
            if row['name'].endswith('_maybe'):
                wanted.append((filename, row, (row['segment'], int(row['address'], 0) & ~1)))
    paths = sorted(source.glob('part_*/src/lib.rs'))
    if not paths:
        raise ValueError('No generated part_*/src/lib.rs source found')
    functions = {}
    calls = defaultdict(set)
    incoming = defaultdict(set)
    for path in paths:
        text = path.read_text(encoding='utf-8')
        starts = list(re.finditer(r'^pub fn f_(\w+)_([0-9A-Fa-f]{8})\(', text, re.M))
        for i, match in enumerate(starts):
            key = (match[1], int(match[2], 16) & ~1)
            chunk = text[match.start():starts[i + 1].start() if i + 1 < len(starts) else len(text)]
            wrapper = re.search(r'^pub fn (?!f_)(\w+)\(', chunk, re.M)
            body = chunk[wrapper.start():] if wrapper else chunk
            inst = re.search(r'pub static INSTS_\w+: &\[u32\] = &\[([^]]*)\]', chunk)
            addresses = sorted(set(int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]+)', inst[1]))) if inst else []
            widths = [min(b - a, 4) for a, b in zip(addresses, addresses[1:])]
            # Odd direct call entries indicate Thumb. Otherwise infer from instruction spacing.
            thumb = bool(int(match[2], 16) & 1) or any(w == 2 for w in widths)
            size = sum(widths) + (2 if thumb else 4) if addresses else None
            fields = {'reads': set(), 'writes': set()}
            memory = {'reads': set(), 'writes': set()}
            globals_ = {'references': set(), 'reads': set(), 'writes': set(), 'unresolved': set()}
            provenance = {}
            literals = {}
            targets = set()
            call_comments = set()
            commented_targets = {}
            ambiguous_targets = []
            for line in body.splitlines():
                if 'macro_rules!' in line or 'if pc !=' in line:
                    continue
                for struct, accessor in re.findall(r'\b(\w+)::(\w+)\(m,', line):
                    if struct in {'R', 'rt', 'recomp'}:
                        continue
                    fields['writes' if accessor.startswith('set_') else 'reads'].add(struct + '::' + accessor.removeprefix('set_'))
                ref = re.search(r'// &(\w+)', line)
                ref_name = ref[1] if ref else None
                assignment = re.search(r'^\s*(?:let (?:mut )?)?(\w+) = (.*?);', line)
                # Resolve addresses through simple assignments and pointer offsets only.
                if assignment:
                    register, expr = assignment.groups()
                    literal = re.fullmatch(r'0x([0-9a-fA-F]+)(?:u32)?', expr)
                    if literal:
                        literals[register] = int(literal[1], 16)
                        if not ref_name:
                            ref_name = global_names.get(int(literal[1], 16))
                    elif expr in literals:
                        literals[register] = literals[expr]
                    else:
                        literals.pop(register, None)
                    if ref_name:
                        provenance[register] = ref_name
                    elif re.fullmatch(r'\w+(?:\.wrapping_(?:add|sub)\(.*\))?', expr):
                        base = re.match(r'\w+', expr)[0]
                        provenance[register] = provenance.get(base)
                    else:
                        # Memory read below is processed before clearing its destination.
                        pass
                for direction, pattern in [('reads', r'(?:R::(?:ldr\w*|ld8s?|ld16s?)\(m,\s*|m\.r(?:8|16|32)\()(\w+)'), ('writes', r'(?:R::st\w*\(m,\s*|m\.w(?:8|16|32)\()(\w+)')]:
                    for base in re.findall(pattern, line):
                        memory[direction].add(line.strip())
                        if provenance.get(base):
                            globals_[direction].add(provenance[base])
                if assignment and not ref_name and not re.fullmatch(r'\w+(?:\.wrapping_(?:add|sub)\(.*\))?', assignment[2]):
                    provenance.pop(assignment[1], None)
                if ref_name:
                    globals_['references'].add(ref_name)
                targets.update(int(a, 16) & ~1 for a in re.findall(r'm\.call\(c, 0x([0-9A-Fa-f]+)', line))
                targets.update(int(a, 16) & ~1 for a in re.findall(r'exit!\(0x([0-9A-Fa-f]+)', line))
                for register in re.findall(r'exit!\(iw\((\w+)\)\)', line):
                    if register in literals:
                        targets.add(literals[register] & ~1)
                if 'm.call(' in line:
                    comment = re.search(r'//\s*(\w+)\s*$', line)
                    if comment:
                        call_comments.add(comment[1])
                        direct = re.search(r'm\.call\(c, 0x([0-9a-fA-F]+)', line)
                        if direct:
                            commented_targets[int(direct[1], 16) & ~1] = comment[1]
                    literals.clear()
                    provenance.clear()  # Call clobbers are not followed.
            for target in targets:
                if target != key[1]:
                    candidates = by_addr.get(target, [])
                    local = [k for k in candidates if k[0] == key[0]]
                    commented = [k for k in candidates if names[k] == commented_targets.get(target)]
                    resolved = commented or local or (candidates if len(candidates) == 1 else [])
                    if not resolved:
                        ambiguous_targets.append(dict(address=f'0x{target:08X}', candidates=[names[k] for k in candidates]))
                    if resolved:
                        for dest in resolved:
                            calls[key].add(dest)
                            incoming[dest].add(key)
            globals_['unresolved'] = globals_['references'] - globals_['reads'] - globals_['writes']
            metadata = coverage.get(key, {})
            if metadata.get('size'):
                size = int(metadata['size'], 0)
                thumb = metadata.get('mode') == 'thumb'
            operational = '\n'.join(l.split('//')[0] for l in body.splitlines()
                if 'budget!' not in l and not re.match(r'\s*(?:lr|pc)\s*=', l) and not any(s in l for s in ('macro_rules!', 'if pc !=', 'm.call(', 'exit!(', 'leave!(')))
            constants = sorted(set(re.findall(r'\b(?:0x[0-9A-Fa-f]+|[0-9]+)(?:[ui](?:8|16|32|64))?\b', operational)))
            functions[key] = dict(source=str(path), line=text.count('\n', 0, match.start()) + 1,
                wrapper_line=text.count('\n', 0, match.start() + wrapper.start()) + 1 if wrapper else None,
                size_bytes=size, size_source='coverage.csv' if metadata.get('size') else 'instruction_address_estimate', mode=metadata.get('mode', 'inferred_thumb' if thumb else 'inferred_arm'), instruction_count=len(addresses), instruction_span_bytes=(addresses[-1] - addresses[0] + (2 if thumb else 4)) if addresses else None,
                fields={k: sorted(v) for k, v in fields.items()}, globals={k: sorted(v) for k, v in globals_.items()},
                memory_accesses={k: sorted(v) for k, v in memory.items()},
                constants=constants, callee_comments=sorted(call_comments), unresolved_direct_targets=ambiguous_targets,
                unresolved_indirect_calls=len(re.findall(r'm\.call\(c, (?!0x)[^,]+,', body)),
                unresolved_indirect_exits=len(re.findall(r'exit!\(iw\((?!lr\b)\w+\)\)', body)), body=body)
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for filename, row, key in wanted:
        record = dict(file=filename, address=row['address'], segment=row['segment'], name=row['name'], found=key in functions)
        record.update(functions.get(key, {}))
        record['callers'] = sorted(names.get(k, str(k)) for k in incoming[key])
        record['callees'] = sorted(names.get(k, str(k)) for k in calls[key])
        record['decision'] = 'unreviewed'
        record['proposed_name'] = row['name']
        record['reason'] = 'Evidence collected; this collector does not make naming decisions.'
        records.append(record)
    (output / 'name_evidence.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    summary = {f: sum(r['file'] == f for r in records) for f in ('game_names.csv', 'sdk_functions.csv')}
    summary['limitations'] = ['Direct calls and constant tail transfers only; ambiguous overlays and indirect dispatch remain unresolved.', 'Typed field names can be incorrect propagated hypotheses; raw accesses are retained separately.', 'Global directions follow simple register copies and offsets, not complete alias/control-flow analysis; unresolved references remain explicit.', 'Constants exclude budget macros, return addresses and direct-call scaffolding.', 'Sizes use generation coverage when available; instruction span and instruction count are also retained.']
    summary.update(found=sum(r['found'] for r in records), total=len(records), indexed_functions=len(functions))
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--baseline-dir', type=Path, help='Optional original dictionary CSVs, for reproducing a completed review')
    args = parser.parse_args()
    collect(args.source, args.output, args.baseline_dir)
