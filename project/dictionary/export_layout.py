"""Export struct fields, field uses and globals from the mapping research into the dictionary.

Reads the mapping project's `MAPPING.csv` (struct_field and global rows) and `mapping_leads.csv`
(field accesses with the functions doing them). Writes, next to this script:
- `fields.csv`: `struct,offset,name,type`, one row per named field;
- `field_uses.csv`: `function,struct,offset`, the named fields each function accesses;
- `globals.csv`: `address,name,type`.
Only our own names go out: every name is checked against the ROM's strings and file names (same rule
as `merge_names.py`). The generator uses these for comments in raised code (`// Kart.speed`).
"""
import argparse
import csv
import os
import re

import merge_names as M

HERE = os.path.dirname(os.path.abspath(__file__))


def offset(s):
    s = s.strip().lstrip("+")
    if not s:
        return None
    try:
        return int(s, 16) if s.lower().startswith("0x") else int(s)
    except ValueError:
        return None


def ident(s):
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s.strip()).strip("_")
    return s if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,47}", s) else None


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--docs", required=True, help="the mapping project's 4_docs folder")
    p.add_argument("--assets", required=True, help="a ripped assets folder (file names to keep out)")
    a = p.parse_args()
    bad = M.forbidden(a.docs, a.assets)
    ok = lambda n: n and not M.leaks(n.lower(), bad)
    mapping = M.read_csv(os.path.join(a.docs, "MAPPING.csv"))
    leads = M.read_csv(os.path.join(a.docs, "mapping_leads.csv"))
    fields = {}
    for r in mapping:
        if r["kind"] != "struct_field":
            continue
        st, off, name = ident(r["address_or_struct"]), offset(r["offset"]), ident(r["name"])
        if st and off is not None and ok(name) and ok(st):
            fields.setdefault((st, off), (name, r["type"].strip()))
    for r in leads:
        st, off, name = ident(r["struct"]), offset(r["offset"]), ident(r["name"])
        if st and off is not None and ok(name) and ok(st):
            fields.setdefault((st, off), (name, ""))
    uses = set()
    for r in leads:
        st, off = ident(r["struct"]), offset(r["offset"])
        if (st, off) not in fields:
            continue
        for f in r["functions"].split():
            m = re.fullmatch(r"sub_([0-9A-Fa-f]+)", f)
            if m:
                uses.add((int(m.group(1), 16), st, off))
    globals_ = {}
    for r in mapping:
        if r["kind"] != "global":
            continue
        m = re.fullmatch(r"0x([0-9A-Fa-f]+)", r["address_or_struct"].strip())
        name = ident(r["name"])
        if m and ok(name):
            globals_.setdefault(int(m.group(1), 16), (name, r["type"].strip()))
    with open(os.path.join(HERE, "fields.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["struct", "offset", "name", "type"])
        for (st, off), (n, t) in sorted(fields.items()):
            w.writerow([st, f"0x{off:X}", n, t])
    with open(os.path.join(HERE, "field_uses.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["function", "struct", "offset"])
        for fn, st, off in sorted(uses):
            w.writerow([f"0x{fn:08X}", st, f"0x{off:X}"])
    with open(os.path.join(HERE, "globals.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["address", "name", "type"])
        for ad, (n, t) in sorted(globals_.items()):
            w.writerow([f"0x{ad:08X}", n, t])
    print(f"{len(fields)} fields, {len(uses)} field uses, {len(globals_)} globals")


if __name__ == "__main__":
    main()
