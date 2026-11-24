import json, re, urllib.parse

G = json.load(open('gab.json'))
EXAMS = [
    ('2022', 'Cebraspe 2022 – Técnico do Seguro Social', [('cb22', 'Conhecimentos-Basicos-2022.pdf'), ('ce22', 'Conhecimentos-Especificos-2022.pdf')]),
    ('2016', 'Cespe/Cebraspe 2016 – Técnico do Seguro Social (Caderno ALGA)', [('p16', 'Caderno-Alga-2016.pdf')]),
    ('2008', 'Cespe/UnB 2008 – Técnico do Seguro Social (Caderno AZUL)', [('p08', 'Prova-2008.pdf')]),
]
R = lambda a, b: range(a, b + 1)
DISC = {
    '2022': [(R(1, 14), 'Língua Portuguesa'), (R(15, 20), 'Ética no Serviço Público'), (R(21, 26), 'Direito Constitucional'),
             (R(27, 40), 'Direito Administrativo'), (R(41, 45), 'Noções de Informática'), (R(46, 50), 'Raciocínio Lógico-Matemático'),
             (R(51, 120), 'Seguridade Social')],
    '2016': [(R(1, 15), 'Língua Portuguesa'), (R(16, 21), 'Ética no Serviço Público'), (R(22, 31), 'Direito Administrativo'),
             (R(32, 34), 'Direito Constitucional'), (R(35, 39), 'Direito Administrativo'), (R(40, 44), 'Noções de Informática'),
             (R(45, 50), 'Raciocínio Lógico-Matemático'), (R(51, 120), 'Seguridade Social')],
    '2008': [(R(1, 4), 'Língua Portuguesa'), (R(5, 10), 'Atualidades / Interpretação'), (R(11, 17), 'Seguridade Social'),
             (R(18, 22), 'Raciocínio Lógico-Matemático'), (R(23, 26), 'Língua Portuguesa'), (R(27, 33), 'Ética no Serviço Público'),
             (R(34, 34), 'Língua Portuguesa'), (R(35, 37), 'Noções de Informática'), (R(38, 42), 'Direito Administrativo'),
             (R(43, 44), 'Noções de Informática'), (R(45, 47), 'Seguridade Social'), (R(48, 49), 'Raciocínio Lógico-Matemático'),
             (R(50, 50), 'Noções de Informática'), (R(51, 55), 'Atendimento ao Público'), (R(56, 58), 'Ética no Serviço Público'),
             (R(59, 62), 'Direito Administrativo'), (R(63, 66), 'Atendimento ao Público'), (R(67, 70), 'Administração Pública'),
             (R(71, 72), 'Comunicação Institucional'), (R(73, 76), 'Responsabilidade Socioambiental'), (R(77, 78), 'Atendimento ao Público'),
             (R(79, 80), 'Saúde e Segurança no Trabalho'), (R(81, 150), 'Seguridade Social')],
}
P = 'https://www.planalto.gov.br/ccivil_03/'
LAWS = [
    (r'103/2019|EC\)? n\.?º? ?103|reforma da previd', 'EC 103/2019', P + 'constituicao/emendas/emc/emc103.htm'),
    (r'3\.048', 'Decreto 3.048/1999 (RPS)', P + 'decreto/d3048.htm'),
    (r'8\.212|custeio|contribui[çc]', 'Lei 8.212/1991 (Custeio)', P + 'leis/l8212cons.htm'),
    (r'6\.214|BPC|benef[íi]cio de presta[çc][ãa]o continuada', 'Decreto 6.214/2007 (BPC)', P + '_ato2007-2010/2007/decreto/d6214.htm'),
    (r'8\.742|assist[êe]ncia social|SUAS|CNAS|CRAS|CREAS|LOAS', 'Lei 8.742/1993 (LOAS)', P + 'leis/l8742.htm'),
    (r'CNIS', 'Lei 8.213/1991 – CNIS (art. 29-A)', P + 'leis/l8213cons.htm'),
    (r'RPPS|regime pr[óo]prio|contagem rec[íi]proca', 'Lei 9.717/1998 (RPPS)', P + 'leis/l9717.htm'),
    (r'8\.213|benef[íi]cio|segurad|aposentadoria|aux[íi]lio|pens[ãa]o|car[êe]ncia|sal[áa]rio-(fam[íi]lia|maternidade)|reabilita', 'Lei 8.213/1991 (Benefícios)', P + 'leis/l8213cons.htm'),
    (r'seguridade', 'CF/88 – arts. 194 a 204 (Seguridade Social)', P + 'constituicao/constituicao.htm#art194'),
    (r'8\.112|servidor', 'Lei 8.112/1990', P + 'leis/l8112cons.htm'),
    (r'1\.171|C[óo]digo de [ÉE]tica|CEPSPC', 'Decreto 1.171/1994 (Código de Ética)', P + 'decreto/d1171.htm'),
    (r'6\.029|Comiss[ãa]o de [ÉE]tica|Gest[ãa]o da [ÉE]tica', 'Decreto 6.029/2007 (Sistema de Gestão da Ética)', P + '_ato2007-2010/2007/decreto/d6029.htm'),
    (r'8\.429|improbidade', 'Lei 8.429/1992 (Improbidade)', P + 'leis/l8429.htm'),
    (r'9\.784|processo administrativo', 'Lei 9.784/1999 (Processo Administrativo)', P + 'leis/l9784.htm'),
    (r'concess[ãa]o de servi[çc]o|encampa', 'Lei 8.987/1995 (Concessões)', P + 'leis/l8987cons.htm'),
    (r'Defesa do Consumidor', 'Lei 8.078/1990 (CDC)', P + 'leis/l8078compilado.htm'),
    (r'usu[áa]rios? de servi[çc]os? p[úu]blicos?', 'Lei 13.460/2017 (Usuários de serviços públicos)', P + '_ato2015-2018/2017/lei/l13460.htm'),
    (r'Manual de Reda[çc][ãa]o|reda[çc][ãa]o oficial|memorando|of[íi]cio', 'Manual de Redação da Presidência da República', 'https://www4.planalto.gov.br/centrodeestudos/assuntos/manual-de-redacao-da-presidencia-da-republica'),
    (r'direitos? (e garantias )?fundamenta|nacionalidade|direitos pol[íi]ticos|Constitui', 'CF/88 – Direitos e Garantias Fundamentais (arts. 5º a 17)', P + 'constituicao/constituicao.htm#art5'),
    (r'administra[çc][ãa]o p[úu]blica|princ[íi]pio da (legalidade|moralidade|impessoalidade|publicidade|efici)', 'CF/88 – art. 37 (Administração Pública)', P + 'constituicao/constituicao.htm#art37'),
]
DISC_LAW = {
    'Ética no Serviço Público': ('Decreto 1.171/1994 (Código de Ética)', P + 'decreto/d1171.htm'),
    'Direito Administrativo': ('CF/88 – art. 37 (Administração Pública)', P + 'constituicao/constituicao.htm#art37'),
    'Direito Constitucional': ('CF/88 – Direitos e Garantias Fundamentais', P + 'constituicao/constituicao.htm#art5'),
    'Seguridade Social': ('Lei 8.213/1991 (Benefícios)', P + 'leis/l8213cons.htm'),
}
NOLAW = {'Língua Portuguesa', 'Noções de Informática', 'Raciocínio Lógico-Matemático', 'Atualidades / Interpretação'}

def assunto(ctx):
    sents = re.split(r'(?<=[.!?])\s+', ctx.replace('\n', ' '))
    cmd = next((s for s in reversed(sents) if re.search(r'julg|assinale|itens?\b', s, re.I)), sents[-1] if sents else '')
    m = re.search(r'(?:acerca d[aoe]s?|a respeito d[aoe]s?|com rela[çc][ãa]o (?:a|à|ao|aos|às)|em rela[çc][ãa]o (?:a|à|ao|aos|às)|relativos? (?:a|à|ao|aos|às)|referentes? (?:a|à|ao|aos|às)|no que (?:se refere|diz respeito) (?:a|à|ao|aos|às)|com refer[êe]ncia a|que versam sobre|com base n[ao]s?|à luz d[ao]s?|conforme o disposto n[ao]s?|quanto (?:a|à|ao|aos|às))\s+((?:[^,;.]|\.(?=\S))+)', cmd, re.I)
    a = (m.group(1) if m else '').strip()
    a = re.sub(r'\s*(julgue.*|\bd?[oa]s? textos?\b.*|apresentad[ao]s? em cada.*|seguida de uma.*|que se seguem.*)$', '', a, flags=re.I)
    return a[:110]

def links(disc, ass, text):
    q = 'INSS técnico ' + disc + (' ' + ass if ass and disc not in ('Língua Portuguesa',) else '') + ' aula'
    video = 'https://www.youtube.com/results?search_query=' + urllib.parse.quote(q)
    law = None
    if disc not in NOLAW:
        for rx, name, url in LAWS:
            if re.search(rx, ass, re.I) or re.search(rx, text, re.I):
                law = (name, url); break
        law = law or DISC_LAW.get(disc)
    if law:
        estudo = {'nome': law[0], 'url': law[1]}
    else:
        qs = disc + (' ' + ass if ass else '') + ' resumo teoria'
        estudo = {'nome': 'Resumo: ' + disc + (' – ' + ass if ass else ''), 'url': 'https://www.google.com/search?q=' + urllib.parse.quote(qs)}
    return {'video': video, 'estudo': estudo}

def fix(t, ano):
    t = t.replace('(cid:126)', '∀').replace('(cid:6)', '≤').replace('(cid:53)', 'ℓ').replace('da forma xP(x)', 'da forma ∀xP(x)')
    t = re.sub(r'\(cid:\d+\)', '', t)
    t = re.sub(r'\s*(-- )?(CONHECIMENTOS )?(OS )?(BÁSICOS|ESPECÍFICOS)? ?(--)?\s*$', '', t) if re.search(r'(OS|BÁSICOS|ESPECÍFICOS|--)\s*$', t) else t
    if ano == '2016': t = re.sub(r'\bR\.\s?(?=\d)', 'ℓ.', t)
    return t

def joinlines(t, keep_par):
    ls = t.split('\n')
    if len(ls) < 2: return t
    L = sorted(len(x) for x in ls)[int(len(ls) * .8)]
    out = ls[0]
    for prev, ln in zip(ls, ls[1:]):
        brk = re.match(r'^(Assertiva:|[A-E]\)|•|—|–|Texto [IVX0-9A-Z]+$|\(com adapta)', ln) or (keep_par and re.search(r'[.:?!»”)]$', prev) and len(prev) < .85 * L) or re.match(r'^Texto ', prev)
        out += ('\n' if brk else ' ') + ln
    return out

def fix(t, ano):
    t = t.replace('(cid:126)', '∀').replace('(cid:6)', '≤').replace('(cid:53)', 'ℓ').replace('da forma xP(x)', 'da forma ∀xP(x)')
    t = re.sub(r'\(cid:\d+\)', '', t)
    t = re.sub(r'\s*(-- )?(CONHECIMENTOS )?(OS )?(BÁSICOS|ESPECÍFICOS)? ?(--)?\s*$', '', t) if re.search(r'(OS|BÁSICOS|ESPECÍFICOS|--)\s*$', t) else t
    if ano == '2016': t = re.sub(r'\bR\.\s?(?=\d)', 'ℓ.', t)
    return t

def joinlines(t, keep_par):
    ls = t.split('\n')
    if len(ls) < 2: return t
    L = sorted(len(x) for x in ls)[int(len(ls) * .8)]
    out = ls[0]
    for prev, ln in zip(ls, ls[1:]):
        brk = re.match(r'^(Assertiva:|[A-E]\)|•|—|–|Texto [IVX0-9A-Z]+$|\(com adapta)', ln) or (keep_par and re.search(r'[.:?!»”)]$', prev) and len(prev) < .85 * L) or re.match(r'^Texto ', prev)
        out += ('\n' if brk else ' ') + ln
    return out

out = []
for ano, titulo, parts in EXAMS:
    qs = []
    for key, pdf in parts:
        for it in json.load(open(key + '.json')):
            n = it['n']; g = G[key][str(n)]
            disc = next(d for r, d in DISC[ano] if n in r)
            ctx = it['contexto']
            if ano == '2008' and n == 50:
                it['enunciado'] += '\nB4; digitar =B2*1,02^2 e, em seguida, teclar [Enter].'
            if ano == '2008' and n >= 51 and ctx.startswith('B4; digitar'):
                ctx = ctx.split('\n', 1)[1]
            ass = assunto(ctx) if ctx else ''
            cmdtxt = ctx[-400:] + ' ' + it['enunciado']
            fig = bool(re.search(r'figura|imagem|imagens|janela|planilha mostrada|gr[áa]fico|ilustra|tabela (acima|abaixo|a seguir|anterior)|na tabela|ícone|bot[ãa]o', cmdtxt, re.I))
            qs.append({'n': n, 'disc': disc, 'assunto': ass, 'ctx': fix(joinlines(ctx, True), ano), 'enun': fix(joinlines(it['enunciado'], False), ano), 'gab': g,
                       'pdf': pdf, 'page': it['page'], 'fig': fig, **links(disc, ass, ctx + ' ' + it['enunciado'])})
    # dedupe contexts into table
    out.append({'id': ano, 'titulo': titulo, 'q': qs})

ctxs, idx = [], {}
for e in out:
    for q in e['q']:
        c = q.pop('ctx')
        if c not in idx: idx[c] = len(ctxs); ctxs.append(c)
        q['c'] = idx[c]
data = {'exams': out, 'ctx': ctxs}
json.dump(data, open('data.json', 'w'), ensure_ascii=False)
for e in out:
    from collections import Counter
    print(e['id'], len(e['q']), Counter(q['gab'] for q in e['q']), Counter(q['disc'] for q in e['q']).most_common(3))
print(len(json.dumps(data, ensure_ascii=False)) // 1024, 'KB')
import random, sys; sys.exit()
for q in random.sample(out[0]['q'], 4) + random.sample(out[2]['q'], 3): print(q['n'], q['disc'], '|', q['assunto'], '|', q['estudo']['nome'])
