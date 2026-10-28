"""Types untyped arguments by function family: functions whose names share a prefix (`mission_enemy_*`)
usually take the same object in the same register. For each family listed in `FAMILIES`, a function
whose argument is accessed at 3+ distinct offsets, 75%+ of them known fields of the family's
struct (and unlikely to match by chance: density^matches < 5%), gets `field_uses.csv` rows for those fields (struct inference then types the argument).

    python dictionary/layout_prefix.py <dump.csv> [--apply]

Input: the `arg` rows mkds_gen records with `MKDS_TYPE_DUMP=<file>`.
"""
import collections, csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from layout_mine import names  # noqa: E402
from layout_fields import canon_map  # noqa: E402

# (name prefix, argument register, struct)
FAMILIES = [
    ('mission_enemy_', 0, 'MissionTarget'),
    ('item_', 0, 'Item'),
    ('obj_', 0, 'MapObj'),
    ('cpu_', 0, 'CpuDriver'),
    ('kart_', 0, 'Kart'),
    ('effect_', 0, 'Effect'),
    ('sound_', 0, 'SoundEmitter'),
    ('camera_', 0, 'Camera'),
]
MIN_OFFS, MIN_SHARE = 3, 0.75


def main():
    dump = sys.argv[1]
    apply = '--apply' in sys.argv
    nm, canon = names(), canon_map()
    parent = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'structs.csv'), encoding='utf-8')):
        if r.get('parent'):
            parent[r['name']] = canon.get(r['parent'], r['parent'])
    fields = collections.defaultdict(set)
    for r in csv.DictReader(open(os.path.join(HERE, 'fields.csv'), encoding='utf-8')):
        fields[canon.get(r['struct'], r['struct'])].add(int(r['offset'], 16))
    have = set()
    for r in csv.DictReader(open(os.path.join(HERE, 'field_uses.csv'), encoding='utf-8')):
        have.add((int(r['function'], 16) & ~1, canon.get(r['struct'], r['struct']), int(r['offset'], 16)))

    def owner(st, off):
        """The struct (st or an ancestor) with a field at off."""
        for _ in range(8):
            if off in fields.get(st, ()):
                return st
            st = parent.get(st)
            if st is None:
                return None
        return None

    def density(st):
        """Share of the word slots up to its last field that hold a field (with its ancestors)."""
        ks, s = set(), st
        for _ in range(8):
            ks |= fields.get(s, set())
            s = parent.get(s)
            if s is None:
                break
        slots = {k // 4 for k in ks}
        return len(slots) / (max(slots) + 1) if slots else 1.0

    offs = collections.defaultdict(set)  # (function, register) -> offsets
    for line in open(dump, encoding='utf-8'):
        p = line.strip().split(',')
        if p[0] == 'arg':
            offs[(int(p[1], 16) & ~1, int(p[2]))].add(int(p[3], 16))
    rows, typed = [], collections.Counter()
    for (f, reg), ks in sorted(offs.items()):
        n = nm.get(f, '')
        for pre, r, st in FAMILIES:
            st = canon.get(st, st)
            if reg != r or not n.startswith(pre) or st not in fields:
                continue
            hit = {k: owner(st, k) for k in ks}
            hit = {k: o for k, o in hit.items() if o}
            # and unlikely by chance: dense layouts match any offsets
            if len(ks) >= MIN_OFFS and len(hit) >= MIN_SHARE * len(ks) and density(st) ** len(hit) < 0.05:
                typed[st] += 1
                rows.extend([f'0x{f:08X}', o, f'0x{k:X}'] for k, o in sorted(hit.items()) if (f, o, k) not in have)
            break
    print(f'{sum(typed.values())} functions typed {dict(typed)}, {len(rows)} field uses', file=sys.stderr)
    if not apply:
        for r in rows:
            print(','.join(r))
        return
    p = os.path.join(HERE, 'field_uses.csv')
    old = open(p, encoding='utf-8').read()
    nl = '\r\n' if '\r\n' in old else '\n'
    with open(p, 'a', encoding='utf-8', newline='') as fh:
        csv.writer(fh, lineterminator=nl).writerows(rows)


if __name__ == '__main__':
    main()
