"""Mines the struct-inference facts mkds_gen records (`MKDS_TYPE_DUMP=<file>`) for dictionary work.
It prints candidates; names are chosen by a person and added to `globals.csv` / `fields.csv` /
`field_uses.csv` (see `layout_apply.py`).

    python dictionary/layout_mine.py <dump.csv> globals [--top N]   # most-used main-RAM globals
    python dictionary/layout_mine.py <dump.csv> fields  [--top N]   # typed accesses with no field
    python dictionary/layout_mine.py <dump.csv> args    [--top N]   # untyped argument clusters by name prefix

The dump holds only addresses, offsets, access widths and struct names from our own tables.
"""
import collections, csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def names():
    """Function entry (no Thumb bit) -> name, from the dictionary (later files override)."""
    out = {}
    for f in ('functions.csv', 'game_names.csv', 'sdk_functions.csv'):
        p = os.path.join(HERE, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding='utf-8')):
            try:
                a = int(r['address'], 16) & ~1
            except (KeyError, ValueError):
                continue
            if r.get('name'):
                out[a] = r['name']
    return out


def known_globals():
    return {int(r['address'], 16): r for r in csv.DictReader(open(os.path.join(HERE, 'globals.csv'), encoding='utf-8'))}


def load(dump):
    rows = []
    for line in open(dump, encoding='utf-8'):
        p = line.strip().split(',')
        if len(p) >= 4:
            rows.append(p)
    return rows


def short(n):
    return n if len(n) < 48 else n[:45] + '...'


def cmd_globals(rows, top):
    nm, kg = names(), known_globals()
    users = collections.defaultdict(set)      # address -> functions
    kinds = collections.defaultdict(collections.Counter)
    pointee = collections.defaultdict(lambda: collections.defaultdict(set))  # global -> off -> funcs
    pstruct = collections.defaultdict(collections.Counter)
    for p in rows:
        if p[0] == 'gacc':
            a = int(p[2], 16)
            if 0x02000000 <= a < 0x02400000:
                users[a].add(int(p[1], 16))
                kinds[a][p[3]] += 1
        elif p[0] == 'gptr':
            g = int(p[2], 16)
            pointee[g][int(p[3], 16)].add(int(p[1], 16))
            if len(p) > 5 and p[5]:
                pstruct[g][p[5]] += 1
    order = sorted(users, key=lambda a: -len(users[a]))
    shown = 0
    for a in order:
        if a in kg:
            continue
        fs = users[a]
        pt = pointee.get(a, {})
        offs = ' '.join(f'{o:X}' for o in sorted(pt, key=lambda o: -len(pt[o]))[:10])
        print(f'{a:#010X} fns={len(fs):3} kinds={dict(kinds[a])} ptr_offs=[{offs}] typed={dict(pstruct.get(a, {}))}')
        ex = collections.Counter(short(nm.get(f & ~1, f"sub_{f:X}")) for f in fs)
        print('    ' + '; '.join(n for n, _ in ex.most_common(8)))
        shown += 1
        if shown >= top:
            break


def cmd_fields(rows, top):
    nm = names()
    miss = collections.defaultdict(lambda: collections.defaultdict(set))
    kinds = collections.defaultdict(collections.Counter)
    for p in rows:
        if p[0] == 'miss':
            k = (p[2], int(p[3], 16))
            miss[k][p[4]].add(int(p[1], 16))
            kinds[k][p[4]] += 1
    order = sorted(miss, key=lambda k: -len(set().union(*miss[k].values())))
    for k in order[:top]:
        fs = set().union(*miss[k].values())
        print(f'{k[0]} {k[1]:#X} fns={len(fs)} kinds={dict(kinds[k])}')
        print('    ' + '; '.join(short(nm.get(f & ~1, f"sub_{f:X}")) for f in sorted(fs)[:8]))


def cmd_args(rows, top):
    nm = names()
    by = collections.defaultdict(lambda: collections.defaultdict(set))  # prefix -> off -> funcs
    for p in rows:
        if p[0] != 'arg':
            continue
        f = int(p[1], 16)
        n = nm.get(f & ~1)
        if not n or n.startswith('sub_'):
            continue
        pre = n.split('_')[0]
        by[(pre, p[2])][int(p[3], 16)].add(f)
    order = sorted(by, key=lambda k: -len(set().union(*by[k].values())))
    for k in order[:top]:
        offs = by[k]
        fs = set().union(*offs.values())
        common = sorted((o for o in offs if len(offs[o]) >= 3), key=lambda o: -len(offs[o]))
        print(f'{k[0]} r{k[1]}: fns={len(fs)} offsets(>=3 fns)=' + ' '.join(f'{o:X}:{len(offs[o])}' for o in common[:20]))


if __name__ == '__main__':
    dump, cmd = sys.argv[1], sys.argv[2]
    top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 60
    {'globals': cmd_globals, 'fields': cmd_fields, 'args': cmd_args}[cmd](load(dump), top)
