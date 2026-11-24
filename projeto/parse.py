import pdfplumber, re, json, sys
CID = False

SKIP = re.compile(r'(CEBRASPE|UnB/CESPE|CESPE \| CEBRASPE|Caderno AZUL|Cargo 18|^\d{3}[A-Z0-9_]+N\d+|^\|\|.*\|\||Espaço livre|RASCUNHO|PROVAS? OBJETIVAS?|^-- |www\.jcconcursos|Wilson Bento|Typewritten|^– \d+ –$|^\s*–\s*\d+\s*–\s*$)', re.I)

def col_lines(page, x0, x1):
    crop = page.crop((x0, page.bbox[1], x1, page.bbox[3]))
    words = crop.extract_words(keep_blank_chars=False, use_text_flow=False, x_tolerance=1.5)
    lines = []
    for w in sorted(words, key=lambda w: (round(w['top']), w['x0'])):
        if lines and abs(lines[-1]['top'] - w['top']) < 3:
            lines[-1]['words'].append(w)
        else:
            lines.append({'top': w['top'], 'words': [w]})
    out = []
    for l in lines:
        ws = sorted(l['words'], key=lambda w: w['x0'])
        out.append({'x0': ws[0]['x0'], 'first': ws[0]['text'], 'text': ' '.join(w['text'] for w in ws), 'top': l['top']})
    return out

def parse(pdfpath, first_item, last_item, margin_tol=14):
    pdf = pdfplumber.open(pdfpath)
    seq = []  # (page, line)
    for pi, p in enumerate(pdf.pages):
        ws = p.extract_words(x_tolerance=1.5)
        best = None
        for sx in range(240, 360, 2):
            c = sum(1 for w in ws if w['x0'] < sx < w['x1'])
            if best is None or c < best[0] or (c == best[0] and abs(sx-p.width/2) < abs(best[1]-p.width/2)): best = (c, sx)
        mid = best[1]
        fl = []
        for w in sorted(ws, key=lambda w: (round(w['top']), w['x0'])):
            if fl and abs(fl[-1][0] - w['top']) < 3: fl[-1][1].append(w)
            else: fl.append((w['top'], [w]))
        cut, bx = 0, None
        for top, lw in fl:
            txt = ' '.join(w['text'] for w in lw)
            if SKIP.search(txt) and len(txt) < 90: continue
            x0 = min(w['x0'] for w in lw)
            if txt.startswith('•'): bx = x0; cut = max(w['bottom'] for w in lw)
            elif bx is not None and x0 > bx + 5: cut = max(w['bottom'] for w in lw)
            else: break
        single = best[0] > 15
        cols = ((0, p.width),) if single else ((0, mid), (mid, p.width))
        for (a, b) in cols:
            ls = [l for l in col_lines(p, a, b) if l['top'] >= cut]
            if not ls: continue
            left = min(l['x0'] for l in ls if re.match(r'^\d', l['text']) or True)
            for l in ls:
                l['page'] = pi + 1
                l['isleft'] = l['x0'] - left < margin_tol
                seq.append(l)
    items, blocks = [], []
    expected = first_item
    cur = None
    buf = []
    texto, comando = '', ''
    state = {'passage': '', 'ctx': ''}
    def clean(txt):
        txt = re.sub(r'\(cid:\d+\)', '', txt)
        lines = [ln.strip() for ln in txt.split('\n')]
        k = next((i for i, ln in enumerate(lines) if re.fullmatch(r'CONHECIMENTOS (BÁSICOS|ESPECÍFICOS)', ln)), None)
        if k is not None: lines = lines[k+1:]
        if any(ln.startswith('•') for ln in lines):
            k = next((i for i, ln in enumerate(lines) if re.match(r'^(Texto|CONHECIMENTOS)', ln)), None)
            lines = lines[k:] if k is not None else [ln for ln in lines if not ln.startswith('•')]
        lines = [ln for ln in lines if ln and not re.fullmatch(r'[\W\d]{0,3}', ln) and not re.fullmatch(r'(CONHECIMENTOS)?( ?BÁSICOS| ?ESPECÍFICOS| ?COMPLEMENTARES|LEMENTARES)?', ln)]
        return '\n'.join(lines).strip()
    def flush_ctx():
        nonlocal buf, cur
        txt = clean('\n'.join(buf)); buf = []
        if not txt: return
        if cur is not None and len(txt) < 300 and not re.search(r'julg|assinale|item|itens|texto', txt, re.I):
            cur['enunciado'] += '\n' + txt; return
        if len(txt) > 450:
            state['passage'] = txt; state['ctx'] = txt
        elif state['passage'] and re.search(r'\btexto|tabela|acima|figura|quadro|gr[áa]fico|janela|imagem', txt, re.I) and not re.search(r'situa[çc][ãa]o hipot[ée]tica', txt[:60], re.I):
            state['ctx'] = state['passage'] + '\n\n' + txt
        else:
            state['ctx'] = txt
            if not re.search(r'\btexto', txt, re.I): state['passage'] = ''
    for l in seq:
        t = l['text'].strip()
        if SKIP.search(t) and len(t) < 90:
            continue
        m = re.match(r'^(\d{1,3})(?:\s+(.*))?$', t)
        mc = re.match(r'^((?:\(cid:\d+\))+)\s+(\S.*)$', t) if CID else None
        if CID:
            ok = bool(mc and l['isleft'] and mc.group(1).count('(cid') <= 3 and '(cid' not in mc.group(2)[:8])
            if ok: m = mc
            t = re.sub(r'^(?:\(cid:\d+\)\S*)+\s*', '', t) if not ok else t
            if not ok and not t: continue
        else:
            ok = bool(m and l['isleft'] and int(m.group(1)) == expected)
        if ok:
            if cur is None or buf:
                pass
            if cur is not None and buf and cur.get('_closed') is None:
                pass
            # new item
            if buf and cur is not None:
                # buffer since last item: may be item continuation or new context; decide by blank/ref
                pass
            if buf:
                flush_ctx()
            cur = {'n': expected, 'page': l['page'], 'contexto': state['ctx'], 'enunciado': (m.group(2) or ''), '_x': l['x0'], '_p': l['page']}
            items.append(cur)
            expected += 1
            if expected > last_item: expected = 10**6
            continue
        if cur is not None and not buf and (cur['_x'] + 6 < l['x0'] < cur['_x'] + 30 or l['page'] != cur['_p'] and l['x0'] > cur['_x'] - 3 and not looks_ctx_start(t, cur)):
            cur['enunciado'] += ('\n' if cur['enunciado'] else '') + t
        else:
            if cur is not None and not buf:
                el = cur['enunciado'].split('\n')
                if len(el) >= 2 and re.search(r'[.?)]$', el[-2]) and re.match(r'^[A-ZÀ-Ú“"]', el[-1]) and not re.search(r'[.?]$', el[-1]):
                    buf.append(el.pop()); cur['enunciado'] = '\n'.join(el)
            buf.append(t)
    for it in items:
        it['enunciado'] = it['enunciado'].strip(); it.pop('_x'); it.pop('_p')
    return items

def looks_ctx_start(t, cur):
    # heuristic: a new context block begins with these
    return bool(re.match(r'^(Texto|Julgue|Considerando|Com base|Com rela|Acerca|A respeito|No que se refere|Tendo em vista|Em rela|Quanto|A partir|Considere|Nos itens|Uma |Um |Determinad|Situação hipotética: .*\bjulgue)', t)) and len(cur['enunciado']) > 40 and re.search(r'[.?]$', cur['enunciado'].strip())

if __name__ == '__main__':
    f, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    CID = len(sys.argv) > 5
    its = parse(f, a, b)
    json.dump(its, open(out, 'w'), ensure_ascii=False, indent=1)
    print(len(its), 'items; missing:', sorted(set(range(a, b + 1)) - {i['n'] for i in its}))
