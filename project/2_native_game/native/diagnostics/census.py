"""Summarise an oracle recording's census.csv / spins.csv (Block 5.0) as Markdown."""
import csv, sys, os, collections, bisect

rec, dic = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(os.path.join(rec, "census.csv"))))
spins = list(csv.DictReader(open(os.path.join(rec, "spins.csv"))))

# function ranges for naming pcs
funcs = []
names = {}
for f in ("sdk_functions.csv", "game_names.csv"):
    for r in csv.reader(open(os.path.join(dic, f), encoding="utf-8")):
        if r and r[0].startswith("0x"):
            names.setdefault(int(r[0], 16) & ~1, r[2])
for r in csv.reader(open(os.path.join(dic, "functions.csv"), encoding="utf-8")):
    if r and r[0].startswith("0x") and r[2].isdigit():
        funcs.append((int(r[0], 16) & ~1, int(r[2]), r[-1][:70]))
funcs.sort()
starts = [f[0] for f in funcs]
def name(pc):
    i = bisect.bisect_right(starts, pc) - 1
    if i >= 0 and pc < funcs[i][0] + max(funcs[i][1], 4):
        a = funcs[i][0]
        return f"{names.get(a, 'sub_%X' % a)} (+{pc - a:#x})"
    return "?"

cols = [c for c in rows[0] if c not in ("frame",)]
n = len(rows)
tot = {c: sum(int(r[c]) for r in rows) for c in cols}
def hist(c):
    h = collections.Counter(int(r[c]) for r in rows)
    return ", ".join(f"{k}: {v}" for k, v in sorted(h.items())[:8]) + (" ..." if len(h) > 8 else "")

print(f"Logical frames sampled: {n} (V-blank count {rows[0]['frame']}..{rows[-1]['frame']})")
print(f"Lag frames (V-blank count advanced by more than 1 between samples): {sum(1 for r in rows if int(r['lag']) > 0)} "
      f"samples, {tot['lag']} V-blanks skipped in total")
print()
print("| counter | total | per frame (mean) | max | histogram (value: frames) |")
print("|---|---:|---:|---:|---|")
for c in cols:
    if c in ("cycles",):
        continue
    mx = max(int(r[c]) for r in rows)
    print(f"| {c} | {tot[c]} | {tot[c]/n:.2f} | {mx} | {hist(c)} |")
print()
by = collections.defaultdict(lambda: [0, 0, 0])
for s in spins:
    pc = int(s["pc"], 16); k = by[pc]; k[0] += 1; k[1] += int(s["instructions"]); k[2] = max(k[2], int(s["instructions"]))
print(f"Tight loops over 1,000 instructions: {len(spins)} runs at {len(by)} pcs")
print()
print("| pc | function | runs | instructions | longest |")
print("|---|---|---:|---:|---:|")
for pc, (c, t, m) in sorted(by.items(), key=lambda kv: -kv[1][1])[:30]:
    print(f"| {pc:#010x} | {name(pc)} | {c} | {t} | {m} |")
