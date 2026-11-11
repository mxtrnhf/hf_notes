#!/usr/bin/env python3
"""Emit mod_functions.tsv: unique 1.163 functions referenced by hf_ally/hf_ai,
their 1.151 match (if any) and the current 1.151 name."""
import re, os, bisect

f151 = {}
with open('/tmp/port163_151/funcs_151.tsv') as f:
    h = f.readline().rstrip().split('\t')
    for line in f:
        p = line.rstrip('\n').split('\t')
        d = dict(zip(h, p))
        f151[int(d['addr'],16)] = (d['name'], d['namesrc'])

# reuse the extraction+resolution logic from modsites.py as a module, but
# silence its print: run exec on the file with stdout redirected
import io, contextlib
src = open('/tmp/port163_151/modsites.py').read()
ns = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, 'modsites.py', 'exec'), ns)
rows = ns['uniq'].items() if isinstance(ns['uniq'], dict) else None
rows = ns['uniq']
containing = ns['containing']
matches = ns['matches']

out = open('/tmp/port163_151/mod_functions.tsv','w')
out.write("addr163\tname163\tninsn\taddr151\ttier151\tname151\tnamesrc151\n")
seen = set()
for fn, ln, name, val, doc in rows:
    f = containing(val)
    if not f:
        continue
    entry, fname, fsrc, size, ninsn = f
    if entry in seen:
        continue
    seen.add(entry)
    m = matches.get(entry)
    if m:
        a151, tier = m[0]
        n151, src151 = f151.get(a151, ('?','?'))
        out.write(f"{entry:x}\t{fname}\t{ninsn}\t{a151:x}\t{tier}\t{n151}\t{src151}\n")
    else:
        out.write(f"{entry:x}\t{fname}\t{ninsn}\t\t\t\t\n")
out.close()
for line in open('/tmp/port163_151/mod_functions.tsv'):
    print(line.rstrip())
