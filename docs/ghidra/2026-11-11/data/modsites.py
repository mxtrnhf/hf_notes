#!/usr/bin/env python3
"""Resolve every hard-coded game address used by hf_ally / hf_ai to its
1.163 function and check whether that function already has a verified
1.151 pair in matched*.tsv."""
import re, sys

MOD_DIRS = [
    "/home/maksim/Development_Highfleet/hf_ally/src",
    "/home/maksim/Development_Highfleet/hf_ai/src",
]
IMG_BASE = 0x140000000

def load_funcs(path):
    funcs = []
    with open(path) as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            parts = line.rstrip("\n").split("\t")
            d = dict(zip(header, parts))
            funcs.append((int(d["addr"], 16), d["name"], d["namesrc"],
                          int(d["size"]), int(d["ninsn"])))
    funcs.sort()
    return funcs

def load_matches():
    m = {}
    for path in ["/tmp/port163_151/matched.tsv", "/tmp/port163_151/matched2.tsv",
                 "/tmp/port163_151/matched3.tsv"]:
        with open(path) as f:
            f.readline()
            for line in f:
                a163, a151, tier, ev = line.rstrip("\n").split("\t")
                m.setdefault(int(a163, 16), []).append((int(a151, 16), tier))
    return m

# ---- extract constants from mod sources ----
site_re = re.compile(r"const ([A-Z_0-9]+)\s*:\s*usize = (0x[0-9a-fA-F_]+)")
sites = []  # (file, line, name, value_abs, doc)
for d in MOD_DIRS:
    import os
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".rs"):
            continue
        path = os.path.join(d, fn)
        lines = open(path).read().splitlines()
        for i, line in enumerate(lines):
            mm = site_re.search(line)
            if not mm:
                continue
            raw = int(mm.group(2).replace("_", ""), 16)
            # struct offsets are < 0x10000; module RVAs used by mods are >= 0x20000
            if IMG_BASE <= raw < 0x148100000:
                val = raw
            elif 0x20000 <= raw < 0x400000:
                val = IMG_BASE + raw
            else:
                continue
            doc = line.split("//", 1)[1].strip() if "//" in line else ""
            if i > 0 and "///" in lines[i-1]:
                doc = lines[i-1].strip("/ ").strip()
            sites.append((fn, i+1, mm.group(1), val, doc))

# also addresses mentioned only in doc comments (hook-site documentation)
doc_addr_re = re.compile(r"0x14([0-9a-fA-F]{8})\b")
for d in MOD_DIRS:
    import os
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".rs"):
            continue
        path = os.path.join(d, fn)
        for i, line in enumerate(open(path).read().splitlines()):
            if "const" in line:
                continue
            for mm in doc_addr_re.finditer(line):
                val = IMG_BASE + int(mm.group(1), 16)
                sites.append((fn, i+1, "(doc)", val, line.strip()))

# dedupe
seen = set()
uniq = []
for s in sites:
    key = (s[2], s[3])
    if key in seen:
        continue
    seen.add(key)
    uniq.append(s)

funcs = load_funcs("/tmp/port163_151/funcs_163.tsv")
import bisect
entries = [f[0] for f in funcs]

def containing(addr):
    idx = bisect.bisect_right(entries, addr) - 1
    if idx >= 0:
        e, name, src, size, ninsn = funcs[idx]
        if e <= addr < e + size:
            return funcs[idx]
    return None

matches = load_matches()

print(f"{'const':22s} {'addr163':10s} {'163 function':40s} {'151 match':10s} status")
print("-" * 110)
rows = []
for fn, ln, name, val, doc in sorted(uniq, key=lambda s: (0 if s[2] != "(doc)" else 1, s[3])):
    f = containing(val)
    if f is None:
        # try exact function entry (funcs list contains entries; addr == entry covered)
        rows.append((fn, ln, name, val, doc, "NO-FUNC (data/label?)", ""))
        continue
    entry, fname, fsrc, size, ninsn = f
    m = matches.get(entry)
    status = "MATCHED" if m else "unmatched"
    if m and len(m) > 1:
        status = "MULTI"
    m151 = f"{m[0][0]:x} [{m[0][1]}]" if m else ""
    rows.append((fn, ln, name, val, doc, f"{entry:x} {fname} ({fsrc}, {ninsn}i)", m151))

for r in rows:
    print(f"{r[0]}:{r[1]:<4d} {r[2][:20]:22s} {r[3]:#x} {r[5][:52]:52s} {r[6]}")
