import csv, collections
base='/tmp/port163_151/'
def load(v):
    return list(csv.DictReader(open(base+f'funcs_{v}.tsv'),delimiter='\t',quoting=csv.QUOTE_NONE))
def cls(n):
    for p,c in (('FUN_','FUN'),('rep_','rep'),('CFUN_','CFUN')):
        if n.startswith(p): return c
    return 'named'
for v in ('163','151'):
    rows=load(v)
    cnt=collections.Counter(cls(r['name']) for r in rows)
    named=[r for r in rows if cls(r['name'])=='named']
    pl=sum(1 for r in rows if int(r['hasplate'] or 0)>30)
    namedpl=sum(1 for r in named if int(r['hasplate'] or 0)>30)
    tot=len(rows)
    print(v,'total',tot,'| named',cnt['named'],'(%.0f%%)'%(100*cnt['named']/tot),
          '| FUN',cnt['FUN'],'| rep',cnt['rep'],'| CFUN',cnt['CFUN'],
          '| plates(any fn)',pl,'| plates on named',namedpl)
# plates on 151 named vs unnamed; how many 151 named are 163-shared
a163=load('163'); a151=load('151')
n163={r['name'] for r in a163}
shared=sum(1 for r in a151 if cls(r['name'])=='named' and r['name'] in n163)
print('151 named functions whose name also exists in 163:',shared)
# struct/enum coverage
def types(v):
    rows=list(csv.DictReader(open(base+f'types_{v}.tsv'),delimiter='\t',quoting=csv.QUOTE_NONE))
    return rows
t163=types('163'); t151=types('151')
s163={r['path'] for r in t163 if r['kind']=='S'}; s151={r['path'] for r in t151 if r['kind']=='S'}
e163={r['path'] for r in t163 if r['kind']=='E'}; e151={r['path'] for r in t151 if r['kind']=='E'}
print('structs: 163',len(s163),'151',len(s151),'| shared',len(s163&s151),'| 163-only',len(s163-s151),'| 151-only',len(s151-s163))
print('enums: 163',len(e163),'151',len(e151),'| shared',len(e163&e151),'| 163-only',len(e163-e151),'| 151-only',len(e151-e163))
