"""Builds the function dictionary (`functions.csv`, `structs.csv`) from the mapping project's research tables.

    python dictionary/export.py <My_NDS_GAME/4_docs> [--signatures signatures.csv] [--out dictionary]

`--signatures`: the generator's argument / return analysis (`mkds_gen ... --signatures FILE`, run on your ROM);
it fills `args` / `returns` and sets `sig` to `auto`. `returns` there means "what callers use" (`void`: nobody
reads a result; empty: no direct caller), and `u64` means callers read r1 too.

The dictionary holds only our own work: addresses, sizes, names, signatures and prose. Nothing from the ROM:
- the research table's `strings` column (text found in the ROM) is never read into the output, and any of those
  strings that our prose happens to quote is redacted;
- links into the hand port (`our_code`) and evidence paths are dropped.
`check()` re-verifies the written files and fails the export if a ROM string slipped through.

Rows are keyed by `(segment, address)` from `4_docs/FUNCTION_BOUNDARIES.csv` (the builder's own boundary list), so the
dictionary covers exactly the functions the builder lifts. Hand-maintained files next to this one
(`sdk_functions.csv`, later `game_*.csv`) override rows by address when the builder merges them.
"""
import argparse
import csv
import os
import re
import sys

COLUMNS = ["address", "segment", "size", "name", "kind", "area", "args", "returns", "sig", "status", "confidence", "notes"]
STRUCT_COLUMNS = ["name", "aliases", "parent", "root", "size", "recognize", "description"]

# research-table status -> how sure the prose is
CONFIDENCE = {"known": "likely", "described": "guess", "inferred": "guess", "sdk": "likely", "unknown": "", "out of scope": ""}

HERE = os.path.dirname(os.path.abspath(__file__))
BOUNDARIES = os.path.join(HERE, "..", "4_docs", "FUNCTION_BOUNDARIES.csv")


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def rom_strings(table):
    """Every string the research table found in the ROM (4+ characters), to keep out of the output."""
    found = set()
    for row in table:
        for s in (row.get("strings") or "").split(" | "):
            s = s.strip()
            if len(s) >= 4:
                found.add(s)
    return found


def standalone(s):
    """`s` as a whole token: not part of a longer word (so `-inf` stays inside `game-info`)."""
    return re.compile(r"(?<![\w-])" + re.escape(s) + r"(?![\w])")


def redact(text, strings):
    for s in strings:
        if s in text:
            text = standalone(s).sub("<rom string>", text)
    return text


def clean(text):
    """One line, without links into the hand port (a separate, unpublished project)."""
    text = re.sub(r"(vm_model|3_hand_port)/[\w/.\-]+", "the hand port", text or "")
    return re.sub(r"\s+", " ", text).strip()


def export(docs, out, signatures=None):
    table = read_csv(os.path.join(docs, "FUNCTION_TABLE.csv"))
    strings = rom_strings(table)
    by_key = {(r["segment"], int(r["ea"], 16)): r for r in table}
    sdk = {int(r["address"], 16) for r in read_csv(os.path.join(docs, "SDK_FUNCTIONS.csv"))}
    sigs = {(r["segment"], int(r["address"], 16)): r for r in read_csv(signatures)} if signatures else {}

    rows = []
    for b in read_csv(BOUNDARIES):
        address = int(b["entry"], 16)
        r = by_key.get((b["segment"], address), {})
        status = r.get("status", "unknown")
        name = r.get("name") or ""
        named = bool(name) and not name.startswith("sub_")
        notes = redact(clean(r.get("meaning")), strings)
        sig = sigs.get((b["segment"], address), {})
        rows.append({
            "address": f"0x{address:08X}",
            "segment": b["segment"],
            "size": b["size"],
            "name": name if named else "",
            "kind": "sdk" if address in sdk or status == "sdk" else "game",
            "area": redact(clean(r.get("area")), strings),
            "args": sig.get("args", ""),
            "returns": sig.get("returns", ""),
            "sig": "auto" if sig else "",
            "status": "named" if named else ("described" if notes else "unknown"),
            "confidence": CONFIDENCE.get(status, ""),
            "notes": notes,
        })

    structs = []
    for s in read_csv(os.path.join(docs, "STRUCTS.csv")):
        structs.append({k: redact(clean(s.get(k)), strings) for k in STRUCT_COLUMNS})

    os.makedirs(out, exist_ok=True)
    for name, columns, data in (("functions.csv", COLUMNS, rows), ("structs.csv", STRUCT_COLUMNS, structs)):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, columns, lineterminator="\n")
            w.writeheader()
            w.writerows(data)
    check(out, strings)
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"{len(rows)} functions {counts}, {len(structs)} structs, {len(strings)} ROM strings kept out")


def check(out, strings):
    """Fails if any ROM string or a hand-port path ended up in the dictionary."""
    for name in ("functions.csv", "structs.csv"):
        text = open(os.path.join(out, name), encoding="utf-8").read()
        leaked = [s for s in strings if s in text and standalone(s).search(text)]
        if leaked:
            sys.exit(f"{name}: ROM strings in the output: {leaked[:5]}")
        if "vm_model/" in text or "3_hand_port" in text:
            sys.exit(f"{name}: hand-port paths in the output")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("docs", help="the mapping project's 4_docs folder")
    p.add_argument("--signatures", help="mkds_gen --signatures output")
    p.add_argument("--out", default=HERE)
    a = p.parse_args()
    export(a.docs, a.out, a.signatures)
