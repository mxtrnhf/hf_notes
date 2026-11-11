import csv, json
base='/tmp/port163_151/'
d163=list(csv.DictReader(open(base+'dtypes_163.tsv'),delimiter='\t',quoting=csv.QUOTE_NONE))
d151=list(csv.DictReader(open(base+'types_151.tsv'),delimiter='\t',quoting=csv.QUOTE_NONE))
def leaf(p): return p.rsplit('/',1)[-1]
l151={leaf(r['path']) for r in d151}
missing=[r for r in d163 if leaf(r['path']) not in l151]
print('missing rows (struct/union/enum):', len(missing),
      'kinds', {k: sum(1 for r in missing if r['kind']==k) for k in ('S','U','E')})
with open(base+'toimport.tsv','w',newline='\n') as f:
    w=csv.writer(f,delimiter='\t',quoting=csv.QUOTE_NONE)
    for r in missing:
        f.write('\t'.join([r['kind'],r['path'],r['size'],r['descr'],r['fields']])+'\n')
print('wrote toimport.tsv')

# closure check: referenced component types resolve in 151 or are in the import set
imp_paths={r['path'] for r in missing}
def elempath(tp, extra):
    # array path like /cat/X[8] -> element /cat/X
    if '[' in tp:
        base=tp[:tp.index('[')]
        return base
    return tp
bad=collections.Counter() if False else {}
import collections
unres=collections.defaultdict(set)
for r in missing:
    for f in (r['fields'] or '').split(';'):
        if not f: continue
        p=f.split('&')
        if len(p)<5: continue
        tk,tp,extra=p[2],p[3],p[4]
        need = tp
        if tk=='ptr':
            need=tp[:-2].strip()
        elif tk=='arr':
            need=elempath(tp,extra)
            if need[0:1]!='/': need=need  # unusual
        if need in imp_paths: continue
        if leaf(need) in l151: continue
        if need.startswith('/undefined') or need in ('/void','/char','/uchar','/float','/double','/byte','/word','/dword','/qword','/uint','/int','/long','/ulong','/short','/ulonglong','/longlong','/bool','/wstring','/string','/string16','/code'):
            continue
        unres[r['path']].add(need)
print('structs with unresolved external deps:',len(unres))
alldep=set()
for k,v in unres.items(): alldep|=v
print('unresolved dep types:',sorted(alldep)[:40])
