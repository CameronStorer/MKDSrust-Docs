"""Block 5 oracle helper (scratch tool kept for 4_docs/masks/native_seed_equalized.md). Per-region comparison of two oracle recordings (frames.bin), aligned by logical frame (default) or by
sample index ("game frames": V-blank IRQs taken; --by-index), optionally after skipping until a frame.
usage: python region_cmp.py RECA RECB [--by-index] [--from F] [--to F] [--offset D] [--regions a,b,..] [--mask maskfile]
--offset D compares A frame f with B frame f - D (B runs D logical frames ahead, e.g. after a faster load)."""
import struct, sys, os

def load(d):
    names = [l.split(',')[1] for l in open(os.path.join(d, 'regions.csv')).read().splitlines()[1:]]
    b = open(os.path.join(d, 'frames.bin'), 'rb').read()
    n = struct.unpack_from('<I', b, 8)[0]
    size = 16 + 8 * n
    fr = []
    for o in range(12, len(b) - size + 1, size):
        lf, hf, cyc = struct.unpack_from('<IIQ', b, o)
        fr.append((lf, struct.unpack_from('<%dQ' % n, b, o + 16)))
    return names, fr

args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
by_index = '--by-index' in args
if by_index: args.remove('--by-index')
lo = int(opt('--from', '0')); hi = int(opt('--to', '99999999'))
focus = opt('--regions')
maskf = opt('--mask')
offset = int(opt('--offset', '0'))  # compare A frame f with B frame f - offset
masked = set()
if maskf:
    for l in open(maskf):
        l = l.split('#')[0].strip()
        if l.startswith('region '):
            masked.add(l.split()[1])
na, A = load(args[0]); nb, B = load(args[1])
assert na == nb
if by_index:
    pairs = [(a, b) for a, b in zip(A, B)]
else:
    db = dict(B)
    pairs = [((f, h), (f - offset, db[f - offset])) for f, h in A if f - offset in db]
pairs = [p for p in pairs if lo <= p[0][0] <= hi]
names = focus.split(',') if focus else na
print(f"compared samples: {len(pairs)} ({'by index' if by_index else 'by logical frame'}, A frames {pairs[0][0][0]}..{pairs[-1][0][0]})")
alleq = 0
for p in pairs:
    if all(p[0][1][k] == p[1][1][k] for k in range(len(na)) if na[k] not in masked):
        alleq += 1
rows = []
for name in names:
    k = na.index(name)
    diff = [(a[0], b[0]) for a, b in pairs if a[1][k] != b[1][k]]
    if diff or focus:
        rows.append((diff[0] if diff else None, len(diff), name, diff))
for first, cnt, name, diff in sorted(rows, key=lambda r: (r[0] is None, r[0])):
    m = ' (masked)' if name in masked else ''
    if first is None:
        print(f"{name:16s} EQUAL in every compared frame")
    else:
        # runs of differing frames (A numbering)
        runs = []
        for f, _ in diff:
            if runs and f <= runs[-1][1] + 1: runs[-1][1] = f
            else: runs.append([f, f])
        rs = ' '.join(f"{a}-{b}" if a != b else f"{a}" for a, b in runs[:6]) + (' ...' if len(runs) > 6 else '')
        print(f"{name:16s} first A{first[0]}/B{first[1]} differing {cnt:6d}{m}  runs: {rs}")
print(f"samples equal in every unmasked region: {alleq} / {len(pairs)}")
