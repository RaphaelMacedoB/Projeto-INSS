import re, json, subprocess
def gab(pdf, section=None):
    t = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    if section:
        i = t.index(section); j = t.find('INSS_CARGO', i + len(section)); t = t[i: j if j > 0 else None]
    lines = t.split('\n'); res = {}
    for k, ln in enumerate(lines):
        if re.match(r'^\s*Item\b', ln):
            nums = re.findall(r'\d+', ln)
            g = next(l for l in lines[k+1:k+4] if 'Gabarito' in l)
            vals = re.findall(r'\b[CEX]\b', g.split('Gabarito', 1)[1])
            for n, v in zip(nums, vals): res[int(n)] = v
    return res
U = '/mnt/user-data/uploads/INSSzada/'
G = {'cb22': gab(U+'Gabarito-Basicos-2022.pdf'), 'ce22': gab(U+'Gabarito-Especificos-2022.pdf'),
     'p16': gab(U+'Gabarito-Definitivo-Alga-2016.pdf'), 'p08': gab(U+'Gabarito-Prova-2008.pdf', 'INSS_CARGO_NM_18_CADERNO_AZUL')}
for k, v in G.items(): print(k, len(v), min(v), max(v), sum(1 for x in v.values() if x == 'X'), 'anuladas')
json.dump(G, open('gab.json', 'w'))
