import json
m = json.load(open('/tmp/port163_151/matched.json'))
with open('/tmp/port163_151/matched.tsv', 'w') as f:
    f.write('addr163\taddr151\ttier\tev\n')
    for k, v in sorted(m.items()):
        f.write(f"{k}\t{v['addr151']}\t{v['tier']}\t{v['ev']}\n")
print('rows', len(m))
