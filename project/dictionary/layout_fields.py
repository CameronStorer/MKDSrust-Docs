"""Adds struct fields that typed code accesses but the dictionary doesn't name yet, from the facts
mkds_gen records (`MKDS_TYPE_DUMP=<file>`, `miss` rows: a value whose struct is known accessed at
an offset with no field).

    python dictionary/layout_fields.py <dump.csv> [--min-fns 2] [--apply]

A field is added when at least `--min-fns` functions access it. Its type is the access width when
every access agrees (`u8`/`s8`/`u16`/`s16`/`u32`), else empty. Its name comes from a getter or
setter that touches only that field (`mission_get_selected_row` -> `selected_row`; with `_maybe`
when only one function, or a `_maybe` function, gives it), else it is the placeholder `f_<offset>`. Each accessing function gets a `field_uses.csv` row.
Without `--apply` it prints the rows it would add.

Note: `export_layout.py` rewrites `fields.csv`/`field_uses.csv` from the mapping research; after
rerunning it, run this again (with a fresh dump) to restore these rows.
"""
import collections, csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from layout_mine import names  # noqa: E402

ACCESSOR = re.compile(r'(?:^|_)(get|set|is|has|clear|inc|dec|increment|decrement|reset)_(?P<noun>[a-z0-9_]+?)(?P<maybe>_maybe)?(?:_[0-9a-f]{6})?$')
VAGUE = re.compile(r'(^|_)(value|word|halfword|byte|field|fields|global|pointer|ptr|data|entry|record|state|flag|flags|counter|index|slot|bit|bits|mode|status|result|target|it|one|two|three|indexed|signed|unsigned|masked|scaled|struct)(_|$)')
WIDTH = {'u8': 'u8', 's8': 's8', 'st8': 'u8', 'u16': 'u16', 's16': 's16', 'st16': 'u16', 'u32': 'u32', 'w32': 'u32', 'st32': 'u32'}


def canon_map():
    m = {}
    for r in csv.DictReader(open(os.path.join(HERE, 'structs.csv'), encoding='utf-8')):
        m.setdefault(r['name'], r['name'])
        for a in (r.get('aliases') or '').split(';'):
            if a.strip():
                m.setdefault(a.strip(), r['name'])
    return m


def field_type(kinds):
    ws = {WIDTH[k] for k in kinds}
    sizes = {w[1:] for w in ws}
    if len(sizes) != 1:
        return ''
    if len(ws) == 1:
        return ws.pop()
    return 'u' + sizes.pop()  # signed and unsigned loads of one width


def main():
    dump = sys.argv[1]
    min_fns = int(sys.argv[sys.argv.index('--min-fns') + 1]) if '--min-fns' in sys.argv else 2
    apply = '--apply' in sys.argv
    nm, canon = names(), canon_map()
    known = set()
    taken = collections.defaultdict(set)
    for r in csv.DictReader(open(os.path.join(HERE, 'fields.csv'), encoding='utf-8')):
        st = canon.get(r['struct'], r['struct'])
        known.add((st, int(r['offset'], 16)))
        taken[st].add(r['name'])
    users = collections.defaultdict(set)
    kinds = collections.defaultdict(set)
    per_fn = collections.defaultdict(set)  # (function, struct) -> offsets missed
    for line in open(dump, encoding='utf-8'):
        p = line.strip().split(',')
        if p[0] != 'miss':
            continue
        f, st, off, k = int(p[1], 16) & ~1, p[2], int(p[3], 16), p[4]
        if (st, off) in known or off >= 0x10000:
            continue
        users[(st, off)].add(f)
        kinds[(st, off)].add(k)
        per_fn[(f, st)].add(off)
    fields, uses = [], []
    for (st, off) in sorted(users):
        fs = users[(st, off)]
        if len(fs) < min_fns:
            continue
        # a getter/setter touching only this field names it
        cands = collections.Counter()
        for f in fs:
            n = nm.get(f, '')
            m = ACCESSOR.search(n)
            if m and per_fn[(f, st)] == {off} and not VAGUE.search(m.group('noun')):
                cands[m.group('noun') + (m.group('maybe') or '')] += 1
        name = f'f_{off:03x}'
        if len(cands) == 1:
            c, k = next(iter(cands.items()))
            # one accessor alone is a weaker hint
            if k < 2 and not c.endswith('_maybe'):
                c += '_maybe'
            if c not in taken[st] and c.removesuffix('_maybe') not in taken[st]:
                name = c
        if name in taken[st]:
            name = f'f_{off:03x}'
            if name in taken[st]:
                continue
        taken[st].add(name)
        fields.append([st, f'0x{off:X}', name, field_type(kinds[(st, off)])])
        uses.extend([f'0x{f:08X}', st, f'0x{off:X}'] for f in sorted(fs))
    named = sum(1 for r in fields if not r[2].startswith('f_'))
    print(f'{len(fields)} fields ({named} named by an accessor), {len(uses)} field uses', file=sys.stderr)
    if not apply:
        for r in fields:
            print(','.join(r))
        return
    for name, rows in (('fields.csv', fields), ('field_uses.csv', uses)):
        p = os.path.join(HERE, name)
        old = open(p, encoding='utf-8').read()
        nl = '\r\n' if '\r\n' in old else '\n'
        with open(p, 'a', encoding='utf-8', newline='') as fh:
            if not old.endswith(('\n',)):
                fh.write(nl)
            csv.writer(fh, lineterminator=nl).writerows(rows)


if __name__ == '__main__':
    main()
