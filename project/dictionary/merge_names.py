"""Merge proposed function names into `game_names.csv` after checking them.

Inputs are CSV files with `address,segment,name` (for example names written by an assistant from our
own notes). A name is kept only if:
- it is a Rust snake_case identifier of at most 40 characters (CamelCase SDK names are converted);
- it contains no string found in the ROM (the research table's `strings` column, `--docs`) and no
  game file name (`--assets`: a ripped assets folder), so the dictionary stays free of ROM text;
- the function has no name yet (`functions.csv` / `sdk_functions.csv` names are never replaced).
Names used more than once in a segment get the address appended. Writes `game_names.csv`
(`address,segment,name`), which the builder applies after `functions.csv`.
"""
import argparse
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def snake(name):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name.strip())
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()
    return re.sub(r"_+", "_", s)


def addr(s):
    return f"0x{int(s.strip(), 16):08X}"


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def forbidden(docs, assets):
    """Normalised ROM strings and file names (5+ characters) that may not appear in a name."""
    bad = set()
    if docs:
        for row in read_csv(os.path.join(docs, "FUNCTION_TABLE.csv")):
            for s in (row.get("strings") or "").split(" | "):
                n = norm(s)
                if len(n) >= 5:
                    bad.add(n)
    if assets:
        for _, _, files in os.walk(assets):
            for f in files:
                n = norm(os.path.splitext(f)[0])
                if len(n) >= 5:
                    bad.add(n)
    return bad


def leaks(name, bad):
    """True if `name` contains ROM text: a multi-word string or file name as whole words, or a
    distinctive single word (10+ characters). Plain words that are also file names (`record`,
    `result`) don't count."""
    padded = f"_{name}_"
    for b in bad:
        if "_" in b or any(ch.isdigit() for ch in b):
            if f"_{b}_" in padded:
                return True
        elif len(b) >= 10 and b in name:
            return True
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("names", nargs="+", help="CSV files with address,segment,name")
    p.add_argument("--docs", help="the mapping project's 4_docs folder (ROM strings to keep out)")
    p.add_argument("--assets", help="a ripped assets folder (file names to keep out)")
    p.add_argument("--out", default=os.path.join(HERE, "game_names.csv"))
    a = p.parse_args()
    if not a.docs or not a.assets:
        sys.exit("--docs and --assets are both required: names must be checked against ROM text")
    bad = forbidden(a.docs, a.assets)
    named = set()
    for table in ("functions.csv", "sdk_functions.csv"):
        for r in read_csv(os.path.join(HERE, table)):
            if r.get("name"):
                named.add((r["segment"], addr(r["address"])))
    rows, rejected = {}, {"identifier": 0, "rom text": 0, "already named": 0}
    for path in a.names:
        for r in read_csv(path):
            key = (r["segment"].strip(), addr(r["address"]))
            n = snake(r.get("name", ""))
            if key in named:
                rejected["already named"] += 1
                continue
            if not re.fullmatch(r"[a-z][a-z0-9_]{0,39}", n):
                rejected["identifier"] += 1
                continue
            if leaks(n, bad):
                rejected["rom text"] += 1
                continue
            rows[key] = n  # later files win
    # unique per segment
    count = {}
    for (seg, _), n in rows.items():
        count[(seg, n)] = count.get((seg, n), 0) + 1
    out = []
    for (seg, ad), n in sorted(rows.items()):
        if count[(seg, n)] > 1:
            n = f"{n}_{int(ad, 16) & 0xFFFFFF:06x}"
        out.append((ad, seg, n))
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["address", "segment", "name"])
        w.writerows(out)
    print(f"{len(out)} names written to {a.out}; rejected {rejected}; {len(bad)} ROM strings/file names checked")


if __name__ == "__main__":
    main()
