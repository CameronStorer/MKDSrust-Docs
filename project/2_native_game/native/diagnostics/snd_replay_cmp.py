"""Compare an exact-model MKDS_SND_LOG (from its take-over point Z) with the log of an MKDS_SND_REPLAY run.
Per context: every driver loop body (B..b) and every interrupt handler (I..E) with the replies (R), main-RAM
writes (M) and SPU writes (S) it made, in order. Reads (L) and command markers (C) are not compared.
usage: snd_replay_cmp.py exact.log replay.log
"""
import sys


def groups(path, after_z):
    bodies, irqs = [], []
    body = irq = None
    seen_z = not after_z
    with open(path) as f:
        for line in f:
            p = line.split()
            if not p:
                continue
            k = p[0]
            if k == 'Z':
                seen_z = True
                bodies, irqs = [], []
                body = irq = None
                continue
            if not seen_z:
                continue
            if k == 'B':
                body = [p[1], []]
                bodies.append(body)
            elif k == 'b':
                body = None
            elif k == 'I':
                irq = [p[1], []]
                irqs.append(irq)
            elif k == 'E':
                irq = None
            elif k in 'RMS':
                g = irq if irq is not None else body
                if g is not None:
                    g[1].append(tuple(p))
    return bodies, irqs


def cmp(name, a, b):
    n = min(len(a), len(b))
    diff = [i for i in range(n) if a[i] != b[i]]
    kinds = {}
    for g in a:
        for e in g[1]:
            kinds[e[0]] = kinds.get(e[0], 0) + 1
    print(f"{name}: {len(a)} vs {len(b)} groups; {len(diff)} differ; items {kinds}")
    if diff:
        i = diff[0]
        print(f"  first differing group #{i}: {a[i][0]} vs {b[i][0]}")
        ea, eb = a[i][1], b[i][1]
        for j in range(max(len(ea), len(eb))):
            x = ea[j] if j < len(ea) else '-'
            y = eb[j] if j < len(eb) else '-'
            if x != y:
                print(f"    item {j}: {x} | {y}")
                break
    return diff


ba, ia = groups(sys.argv[1], True)
bb, ib = groups(sys.argv[2], True)
d1 = cmp("loop bodies", ba, bb)
d2 = cmp("interrupts", ia, ib)
ra = [e for g in ba + ia for e in g[1] if e[0] == 'R']
print("replies:", len(ra), "exact")
print("RESULT:", "IDENTICAL" if not d1 and not d2 and len(ba) == len(bb) and len(ia) == len(ib) else "DIFFERENT")
