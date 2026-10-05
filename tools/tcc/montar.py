"""Monta a versão nova do TCC a partir do .docx anterior e dos dados exportados (ver README.md).

Uso: python montar.py <entrada.docx> <saida.docx> <pasta-de-dados>
"""
import copy, csv, json, re, sys
from pathlib import Path
from docx import Document
from docx.shared import Cm
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
sys.path.insert(0, str(Path(__file__).parent))
from conteudo import *
from cap45 import CAP4, CAP5

SRC, OUT, DADOS = sys.argv[1], sys.argv[2], Path(sys.argv[3])
D = Document(SRC)
body = D.element.body
W = qn
problems = []


def text(el):
    return "".join(t.text or "" for t in el.iter(W("w:t")))


def paras():
    return [p for p in body.iter(W("w:p"))]


def top():
    return [e for e in body if e.tag in (W("w:p"), W("w:tbl"))]


def find(prefix, start=0):
    for p in paras():
        if text(p).strip().startswith(prefix):
            return p
    problems.append(f"não achei: {prefix!r}")
    return None


def heading(txt):
    for p in body.findall(W("w:p")):
        st = p.find(W("w:pPr") + "/" + W("w:pStyle"))
        if st is not None and st.get(W("w:val")) == "Ttulo1" and text(p).strip() == txt:
            return p
    problems.append(f"título ausente: {txt!r}")
    return None


def strip_italic(rpr):
    if rpr is None:
        return None
    rpr = copy.deepcopy(rpr)
    for tag in ("w:i", "w:iCs"):
        for e in rpr.findall(W(tag)):
            rpr.remove(e)
    return rpr


def set_text(p, new):
    runs = p.findall(W("w:r"))
    rpr = None
    for r in runs:
        if r.find(W("w:t")) is not None:
            rpr = r.find(W("w:rPr"))
            break
    for e in list(p):
        if e.tag != W("w:pPr"):
            p.remove(e)
    r = OxmlElement("w:r")
    if rpr is not None:
        r.append(strip_italic(rpr))
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = new
    r.append(t)
    p.append(r)


def ppr(p, *, line=240, first=None, jc=None, before=None, after=None, keep=False, size=None, bold=False):
    pp = p.find(W("w:pPr"))
    if pp is None:
        pp = OxmlElement("w:pPr")
        p.insert(0, pp)
    if keep:
        pp.append(OxmlElement("w:keepNext"))
    sp = OxmlElement("w:spacing")
    if before is not None:
        sp.set(W("w:before"), str(before))
    if after is not None:
        sp.set(W("w:after"), str(after))
    sp.set(W("w:line"), str(line))
    sp.set(W("w:lineRule"), "auto")
    pp.append(sp)
    if first is not None:
        ind = OxmlElement("w:ind")
        ind.set(W("w:firstLine"), str(first))
        pp.append(ind)
    if jc:
        j = OxmlElement("w:jc")
        j.set(W("w:val"), jc)
        pp.append(j)
    return pp


def run(p, s, *, size=None, bold=False, italic=False):
    r = OxmlElement("w:r")
    rp = OxmlElement("w:rPr")
    if bold:
        rp.append(OxmlElement("w:b"))
    if italic:
        rp.append(OxmlElement("w:i"))
    if size:
        for tag in ("w:sz", "w:szCs"):
            z = OxmlElement(tag)
            z.set(W("w:val"), str(size))
            rp.append(z)
    if len(rp):
        r.append(rp)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = s
    r.append(t)
    p.append(r)
    return r


class Cursor:
    def __init__(self, el):
        self.el = el

    def add(self, el):
        self.el.addnext(el)
        self.el = el
        return el

    def p(self, s, **kw):
        p = OxmlElement("w:p")
        ppr(p, first=708, jc="both")
        run(p, s)
        return self.add(p)

    def heading(self, s, level):
        p = OxmlElement("w:p")
        pp = OxmlElement("w:pPr")
        st = OxmlElement("w:pStyle")
        st.set(W("w:val"), f"Ttulo{level}")
        pp.append(st)
        p.append(pp)
        run(p, s)
        return self.add(p)

    def caption(self, s):
        p = OxmlElement("w:p")
        ppr(p, jc="center", before=240, after=120, keep=True)
        run(p, s, size=22)
        return self.add(p)

    def source(self, s):
        p = OxmlElement("w:p")
        ppr(p, jc="center", after=240)
        run(p, s, size=20)
        return self.add(p)

    def figure(self, path, width_cm=15.5):
        p = OxmlElement("w:p")
        ppr(p, jc="center", keep=True)
        self.add(p)
        Paragraph(p, D._body).add_run().add_picture(path, width=Cm(width_cm))
        return p

    def table(self, header, rows, widths, align):
        t = D.add_table(rows=1 + len(rows), cols=len(header))
        tbl = t._tbl
        tblPr = tbl.tblPr
        b = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement(f"w:{side}")
            e.set(W("w:val"), "single")
            e.set(W("w:sz"), "4")
            e.set(W("w:space"), "0")
            e.set(W("w:color"), "auto")
            b.append(e)
        tblPr.append(b)
        jc = OxmlElement("w:jc")
        jc.set(W("w:val"), "center")
        tblPr.append(jc)
        tw = sum(widths)
        tblW = tblPr.find(W("w:tblW"))
        tblW.set(W("w:type"), "dxa")
        tblW.set(W("w:w"), str(tw))
        grid = tbl.find(W("w:tblGrid"))
        for gc, w in zip(grid.findall(W("w:gridCol")), widths):
            gc.set(W("w:w"), str(w))
        for i, row in enumerate([header] + rows):
            tr = t.rows[i]._tr
            if i == 0:
                trPr = tr.get_or_add_trPr()
                trPr.append(OxmlElement("w:tblHeader"))
            for j, val in enumerate(row):
                tc = t.rows[i].cells[j]._tc
                tcPr = tc.get_or_add_tcPr()
                tcW = OxmlElement("w:tcW")
                tcW.set(W("w:w"), str(widths[j]))
                tcW.set(W("w:type"), "dxa")
                tcPr.append(tcW)
                va = OxmlElement("w:vAlign")
                va.set(W("w:val"), "center")
                tcPr.append(va)
                if i == 0:
                    sh = OxmlElement("w:shd")
                    sh.set(W("w:val"), "clear")
                    sh.set(W("w:color"), "auto")
                    sh.set(W("w:fill"), "E7E6E6")
                    tcPr.append(sh)
                p = tc.find(W("w:p"))
                ppr(p, jc="center" if (i == 0 or align[j] == "c") else "left", before=20, after=20)
                run(p, str(val), size=18, bold=(i == 0))
        return self.add(tbl)


def apply(cur, items, tables):
    for it in items:
        kind = it[0]
        if kind == "H1":
            cur.heading(it[1], 1)
        elif kind == "H2":
            cur.heading(it[1], 2)
        elif kind == "P":
            cur.p(it[1])
        elif kind == "FIG":
            _, f, cap, src = it
            cur.caption(cap)
            cur.figure(FIGS[f])
            cur.source(src)
        elif kind == "TAB":
            _, name, cap, src = it
            cur.caption(cap)
            cur.table(*tables[name])
            cur.source(src)


# ---------------------------------------------------------------- dados
FIGS = {
    "arquitetura.png": str(DADOS / "fig/arquitetura.png"),
    "serie_petr4.png": str(DADOS / "fig/serie_petr4.png"),
    "razao_violacoes.png": str(DADOS / "fig/razao_violacoes.png"),
    "anos_adequados.png": str(DADOS / "fig/anos_adequados.png"),
    "02-visao-geral.png": str(DADOS / "telas/02-visao-geral.png"),
    "03-risco.png": str(DADOS / "telas/03-risco.png"),
    "04-laboratorio.png": str(DADOS / "telas/04-laboratorio.png"),
}
NAME = {"historical": "Histórico", "parametric": "Paramétrico", "monte_carlo": "Monte Carlo",
        "garch_1_1": "GARCH(1,1)", "egarch": "EGARCH", "lstm": "LSTM", "gru": "GRU", "garchnet": "GARCHNet",
        "caviar": "CAViaR"}
ORDER = list(NAME)
R = [r for r in csv.DictReader(open(DADOS / "lab_result.csv", encoding="utf-8"), delimiter=";")
     if r["ticker"] and not r["ticker"].startswith("(")]


def pv(v):
    f = float(v)
    return "< 0,0001" if f < 0.0001 else f"{f:.4f}".replace(".", ",")


rows = []
for a in ("0.0500", "0.0100"):
    for m in ORDER:
        r = next(x for x in R if x["ticker"] == "PETR4" and x["model_name"] == m and x["alpha"] == a)
        rows.append([NAME[m], "95%" if a == "0.0500" else "99%",
                     f"{r['violations']} × {r['ev'].replace('.', ',')}", pv(r["kpv"]), pv(r["cpv"]), pv(r["dpv"]),
                     "adequado" if r["adequate"] == "t" else "não adequado"])
TAB_PETR4 = (["Modelo", "Nível", "Violações (obs. × esp.)", "Kupiec", "Christoffersen", "DQ", "Veredito"], rows,
             [1450, 750, 1450, 1150, 1350, 1150, 1500], ["l", "c", "c", "c", "c", "c", "c"])
st = json.load(open(DADOS / "stats.json"))
rank = sorted(ORDER, key=lambda m: (-st[m]["adeq"], -st[m]["all3"], -st[m]["dq"], st[m]["dev"]))
rows = []
for i, m in enumerate(rank, 1):
    s = st[m]
    rows.append([f"{i}º", NAME[m], int(s["adeq"]), int(s["kup"]), int(s["chr"]), int(s["dq"]),
                 f"{s['dev'] * 100:.1f}%".replace(".", ","), f"{int(s['green'])} de 32"])
TAB_RANK = (["Posição", "Modelo", "Adequado (de 8)", "Kupiec (de 8)", "Christoffersen (de 8)", "DQ (de 8)",
             "Desvio médio", "Zona verde a 99%"], rows,
            [850, 1400, 1100, 1000, 1350, 900, 1100, 1100], ["c", "l", "c", "c", "c", "c", "c", "c"])
TABLES = {"petr4": TAB_PETR4, "ranking": TAB_RANK}

# ---------------------------------------------------------------- 1. trocas pontuais e reescritas
for pre, old, new in TROCAS:
    p = find(pre)
    if p is None:
        continue
    s = text(p)
    if old not in s:
        problems.append(f"trecho ausente em {pre!r}: {old[:50]!r}")
        continue
    set_text(p, s.replace(old, new))
for pre, new in REESCRITOS:
    p = find(pre)
    if p is not None:
        set_text(p, new)

# ---------------------------------------------------------------- 2. seção 3.2
first = find("A plataforma VaR Lab será desenvolvida")
last = find("Armazenamento de dados:")
cur = Cursor(first.getprevious())
el = first
while True:
    nxt = el.getnext()
    body.remove(el)
    if el is last:
        break
    el = nxt
for s in SECAO_32:
    if s.startswith("FIG:"):
        f, cap = s[4:].split("|")
        cur.caption(cap)
        cur.figure(FIGS[f])
        cur.source("Fonte: Os autores.")
    else:
        cur.p(s)

# ---------------------------------------------------------------- 3. capítulos 4 e 5
h4 = heading("4 RESULTADOS")
href = heading("REFERÊNCIAS")
cur = Cursor(h4.getprevious())
el = h4
while el is not href:
    nxt = el.getnext()
    body.remove(el)
    el = nxt
apply(cur, CAP4 + CAP5, TABLES)

# ---------------------------------------------------------------- 4. "VaR Lab" e "PETR4.SA" no texto
for p in paras():
    s = text(p)
    if "VaR Lab" in s or "PETR4.SA" in s:
        set_text(p, s.replace("VaR Lab", "Ruvor").replace("PETR4.SA", "PETR4"))

# ---------------------------------------------------------------- 5. Matriz de Validação
MATRIZ = [
    ("Coletar dados via yfinance (Yahoo Finance): IBOV (^BVSP), PETR4.SA, VALE3.SA, ITUB4.SA — período jan/2015–dez/2024.",
     "Coletar dados do Yahoo Finance (API de cotações, por HTTP): IBOV, PETR4, VALE3 e ITUB4 — dez anos, de set/2016 a set/2026."),
    ("Coletar dados via yfinance (Yahoo Finance): IBOV (^BVSP), PETR4, VALE3.SA, ITUB4.SA — período jan/2015–dez/2024.",
     "Coletar dados do Yahoo Finance (API de cotações, por HTTP): IBOV, PETR4, VALE3 e ITUB4 — dez anos, de set/2016 a set/2026."),
    ("1. Integração yfinance + tratamento de dados (Alta)", "1. Integração com o Yahoo Finance + tratamento de dados (Alta)"),
    ("Resultado obtido: a LSTM aprovou",
     "Resultado obtido: os quatro modelos foram avaliados na década de cada ativo, com semente fixa (42); o CAViaR "
     "teve o maior número de casos adequados (4 de 8), seguido do GARCH(1,1) e da LSTM (3 de 8 cada) — ver Seção 4.6."),
    ("Front-end: Single Page Application em React",
     "Front-end: Single Page Application em React com TypeScript (Vite), consumindo a API REST do Django — "
     "front-end e back-end desacoplados."),
    ("Back-end Flask como API JSON pura",
     "Back-end Django com API REST (JSON) em /api/v1, banco PostgreSQL e fila Celery para os cálculos."),
    ("Dashboards interativos com Plotly.js",
     "Gráficos com a biblioteca uPlot e tabelas comparativas dos nove modelos, com os testes de backtesting e o "
     "veredito de cada um."),
    ("2. Back-end Flask (rotas/APIs)", "2. Back-end Django (API REST)"),
    ("3. Integração front × back via fetch/CORS (React)", "3. Integração front × back (React + API REST)"),
    ("4. Dashboards Plotly.js (pendente)", "4. Gráficos e tabelas comparativas (uPlot)"),
    ("5. Testes de usabilidade com usuários-alvo", "5. Testes de usabilidade com usuários-alvo (não realizados; ver Seção 4.5)"),
    ("Selecionar ativos: IBOV (^BVSP), PETR4.SA, VALE3.SA, ITUB4.SA — jan/2015–dez/2024.",
     "Selecionar ativos: IBOV, PETR4, VALE3 e ITUB4 — set/2016 a set/2026."),
    ("Selecionar ativos: IBOV (^BVSP), PETR4, VALE3.SA, ITUB4.SA — jan/2015–dez/2024.",
     "Selecionar ativos: IBOV, PETR4, VALE3 e ITUB4 — set/2016 a set/2026."),
    ("Interface intuitiva validada por usuários-alvo.",
     "Interface verificada por testes automatizados; validação por usuários-alvo pendente."),
    ("Ranking comparativo de todos os modelos.",
     "Ranking comparativo de todos os modelos: CAViaR, GARCH(1,1) e LSTM nas três primeiras posições (Tabela 2)."),
]
for tbl in body.iter(W("w:tbl")):
    tp = tbl.find(W("w:tblPr")).find(W("w:tblpPr"))
    if tp is not None:
        tbl.find(W("w:tblPr")).remove(tp)
        matriz = tbl
for old, new in MATRIZ:
    hit = [p for p in matriz.iter(W("w:p")) if text(p).strip().startswith(old)]
    if not hit and "PETR4, VALE3.SA" not in old:
        problems.append(f"matriz: {old[:50]!r}")
    for p in hit:
        set_text(p, new)

# ---------------------------------------------------------------- 6. Apêndice B
tB = [t for t in body.iter(W("w:tbl")) if text(t).startswith("Campo")][0]
trs = tB.findall(W("w:tr"))
i1 = next(i for i, r in enumerate(trs) if text(r).startswith("Ferramenta 1"))
i2 = next(i for i, r in enumerate(trs) if text(r).startswith("Ferramenta 2"))
i3 = next(i for i, r in enumerate(trs) if text(r).startswith("Declaração dos Autores"))
block = [copy.deepcopy(r) for r in trs[i1:i2]]
NOVO = {
    "Ferramenta 1": "Ferramenta 3 — Claude Code (Anthropic)",
    "Ferramenta / Modelo": "Claude Opus 5.5 (claude-opus-5-5) — Anthropic, pelo Claude Code",
    "Período de uso": "Outubro de 2026",
    "Entradas fornecidas": "O repositório do projeto, os resultados do experimento gravados no banco de dados da "
                           "plataforma e as orientações do professor orientador para a versão final.",
    "Edição humana": "As saídas passam por revisão e validação dos autores antes da incorporação final ao trabalho.",
    "Controle e validação": "Os números das tabelas e figuras foram extraídos por consulta ao banco de dados do "
                            "experimento e conferidos contra a interface da plataforma.",
}
TAREFAS = ["— Atualização dos Capítulos 1 e 3 para refletir a arquitetura implementada.",
           "— Redação assistida dos Capítulos 4 e 5, do Resumo e do Abstract, a partir dos resultados do experimento.",
           "— Geração das figuras e tabelas a partir do banco de dados e formatação conforme as normas do TCC II."]
EXT = "Caps. 4 e 5, Resumo e Abstract — rascunho gerado com IA a partir dos resultados, sujeito à revisão integral dos autores."
for r in block:
    cells = r.findall(W("w:tc"))
    label = text(cells[0]).strip()
    if label.startswith("Ferramenta 1"):
        set_text(cells[0].find(W("w:p")), NOVO["Ferramenta 1"])
        continue
    if len(cells) < 2:
        continue
    ps = cells[1].findall(W("w:p"))
    if label in NOVO:
        set_text(ps[0], NOVO[label])
        for extra in ps[1:]:
            cells[1].remove(extra)
    elif label == "Tarefas realizadas":
        for k, p in enumerate(ps):
            if k < len(TAREFAS):
                set_text(p, TAREFAS[k])
            else:
                cells[1].remove(p)
    elif label == "Extensão do uso":
        set_text(ps[0], EXT)
        for extra in ps[1:]:
            cells[1].remove(extra)
anchor = trs[i3]
for r in block:
    anchor.addprevious(r)
for p in paras():
    s = text(p)
    if s.strip() == "São Paulo, maio de 2026.":
        set_text(p, "São Paulo, outubro de 2026.")
sig = find("Guilherme Nunes")
if sig is not None and text(sig).strip() == "Guilherme Nunes":
    nxt = sig.getnext()
    set_text(sig, "Guilherme Nunes Joanna")
    if text(nxt).strip().startswith("Joanna Kauã"):
        set_text(nxt, "Kauã Ribeiro Santos")

# ---------------------------------------------------------------- 7. Resumo, Abstract e Sumário
sumario = find("SUMÁRIO")
pb_before = sumario.getprevious()  # parágrafo com a quebra antes do sumário


def page_block(title, txt, kw, english):
    cur = Cursor(pb_before)
    t = OxmlElement("w:p")
    ppr(t, jc="center", after=360)
    run(t, title, bold=True)
    cur.add(t)
    p = OxmlElement("w:p")
    ppr(p, jc="both")
    run(p, txt, italic=english)
    cur.add(p)
    k = OxmlElement("w:p")
    ppr(k, jc="both", before=240)
    lab, rest = kw.split(":", 1)
    run(k, lab + ":", bold=True, italic=english)
    run(k, rest, italic=english)
    cur.add(k)
    brp = OxmlElement("w:p")
    r = OxmlElement("w:r")
    br = OxmlElement("w:br")
    br.set(W("w:type"), "page")
    r.append(br)
    brp.append(r)
    cur.add(brp)
    return cur.el


# a ordem: Resumo, Abstract e depois o Sumário
end_abs = page_block("ABSTRACT", ABSTRACT, KEYWORDS, True)
pb_before_abs = pb_before
page_block("RESUMO", RESUMO, PALAVRAS, False)
# o sumário manual vira campo TOC
el = sumario.getnext()
intro = heading("1 INTRODUÇÃO")
while True:
    nxt = el.getnext()
    if nxt is intro or "w:type=\"page\"" in el.xml if hasattr(el, "xml") else False:
        break
    if any(b.get(W("w:type")) == "page" for b in el.iter(W("w:br"))):
        break
    body.remove(el)
    el = nxt
toc = OxmlElement("w:p")
for kind, val in (("begin", None), ("instr", ' TOC \\o "1-3" \\h \\z \\u '), ("separate", None),
                  ("text", "Clique com o botão direito e atualize o sumário."), ("end", None)):
    r = OxmlElement("w:r")
    if kind == "instr":
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = val
        r.append(it)
    elif kind == "text":
        t = OxmlElement("w:t")
        t.text = val
        r.append(t)
    else:
        fc = OxmlElement("w:fldChar")
        fc.set(W("w:fldCharType"), kind)
        if kind == "begin":
            fc.set(W("w:dirty"), "true")
        r.append(fc)
    toc.append(r)
sumario.addnext(toc)

# ---------------------------------------------------------------- 8. texto contínuo: sem quebra de página depois do sumário
intro = heading("1 INTRODUÇÃO")
started = False
for el in list(body):
    if el is intro:
        started = True
    if not started or el.tag != W("w:p"):
        continue
    for br in list(el.iter(W("w:br"))):
        if br.get(W("w:type")) == "page":
            r = br.getparent()
            r.remove(br)
            if not len([c for c in r if c.tag != W("w:rPr")]):
                r.getparent().remove(r)
    for lr in list(el.iter(W("w:lastRenderedPageBreak"))):
        lr.getparent().remove(lr)
    for pb in el.iter(W("w:pageBreakBefore")):
        pb.getparent().remove(pb)
# parágrafos vazios no corpo do texto (inclusive títulos vazios que só levavam a quebra)
started = False
for el in list(body):
    if el is intro:
        started = True
    if not started or el.tag != W("w:p"):
        continue
    if text(el).strip() == "" and el.find(".//" + W("w:drawing")) is None and el.find(".//" + W("w:sectPr")) is None:
        body.remove(el)

# ---------------------------------------------------------------- 9. espaço simples e itálico só para inglês
for sp in body.iter(W("w:spacing")):
    if sp.get(W("w:line")):
        sp.set(W("w:line"), "240")
        sp.set(W("w:lineRule"), "auto")
for r in body.iter(W("w:r")):
    rp = r.find(W("w:rPr"))
    if rp is not None:
        for tag in ("w:i", "w:iCs"):
            for e in rp.findall(W(tag)):
                rp.remove(e)

EN = ["Generalized Autoregressive Conditional Heteroskedasticity",
      "Conditional Autoregressive Value at Risk by Regression Quantiles", "Value at Risk", "Machine Learning",
      "Deep Learning", "Long Short-Term Memory", "Gated Recurrent Unit", "Exponential GARCH",
      "Proportion of Failures", "Dynamic Quantile", "Symmetric Absolute Value", "Expected Shortfall",
      "Single Page Application", "volatility clustering", "walk-forward validation", "walk-forward", "grid search",
      "pinball loss", "backtesting", "Backtesting", "frameworks", "framework", "Front-end", "front-end", "Back-end",
      "back-end", "dashboards", "templates", "bindings", "notebooks", "overhead", "dropout", "batch size", "batch",
      "gates", "clusters", "clustering", "feature", "out-of-sample", "ranking", "Ranking", "traffic-light"]
EN_RE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(e) for e in EN) + r")(?![\w-])")

ref = heading("REFERÊNCIAS")
abs_title = find("ABSTRACT")
skip = set()
# não mexe na capa, na folha de rosto, no Abstract (já em itálico inteiro) nem nas referências
in_ref = False
for el in body:
    if el is ref:
        in_ref = True
    if el.tag == W("w:p") and text(el).startswith("Apêndice A"):
        in_ref = False
    if in_ref:
        skip.add(el)
abs_block = [abs_title.getnext(), abs_title.getnext().getnext()]
skip.update(abs_block)
for p in abs_block:  # o Abstract é texto em inglês: itálico inteiro
    for r in p.findall(W("w:r")):
        rp = r.find(W("w:rPr"))
        if rp is None:
            rp = OxmlElement("w:rPr")
            r.insert(0, rp)
        rp.append(OxmlElement("w:i"))


def italicize(p):
    for r in list(p.findall(W("w:r"))):
        t = r.find(W("w:t"))
        if t is None or not t.text or not EN_RE.search(t.text):
            continue
        parts = EN_RE.split(t.text)
        rpr = r.find(W("w:rPr"))
        for k, part in enumerate(parts):
            if not part:
                continue
            nr = OxmlElement("w:r")
            np_ = copy.deepcopy(rpr) if rpr is not None else OxmlElement("w:rPr")
            if k % 2 == 1:
                np_.append(OxmlElement("w:i"))
            if len(np_):
                nr.append(np_)
            nt = OxmlElement("w:t")
            nt.set(qn("xml:space"), "preserve")
            nt.text = part
            nr.append(nt)
            r.addprevious(nr)
        p.remove(r)


start = find("RESUMO")
started = False
for el in body:
    if el is start:
        started = True
    if not started or el in skip:
        continue
    for p in ([el] if el.tag == W("w:p") else list(el.iter(W("w:p")))):
        italicize(p)

# estilos: espaço simples por padrão e título de capítulo com espaço antes
styles = D.styles.element
for sp in styles.iter(W("w:spacing")):
    if sp.get(W("w:line")):
        sp.set(W("w:line"), "240")
for s in styles.findall(W("w:style")):
    if s.get(W("w:styleId")) == "Ttulo1":
        sp = s.find(W("w:pPr")).find(W("w:spacing"))
        sp.set(W("w:before"), "480")
        sp.set(W("w:after"), "240")
    if s.get(W("w:styleId")) == "Ttulo2":
        sp = s.find(W("w:pPr")).find(W("w:spacing"))
        sp.set(W("w:before"), "240")
        sp.set(W("w:after"), "120")
for s_ in styles.findall(W("w:style")):
    if s_.get(W("w:styleId")) in ("Ttulo1", "Ttulo2", "Ttulo3"):
        pp = s_.find(W("w:pPr"))
        pp.insert(0, OxmlElement("w:keepNext"))
# capa e folha de rosto mantêm o espaçamento original (1,5), que posiciona os blocos na página
res = find("RESUMO")
for el in body:
    if el is res:
        break
    if el.tag != W("w:p"):
        continue
    pp = el.find(W("w:pPr"))
    if pp is None:
        pp = OxmlElement("w:pPr")
        el.insert(0, pp)
    sp = pp.find(W("w:spacing"))
    if sp is None:
        sp = OxmlElement("w:spacing")
        pp.append(sp)
    sp.set(W("w:line"), "360")
    sp.set(W("w:lineRule"), "auto")
# assinatura do Apêndice B: o nome do Guilherme estava partido em duas linhas
for p in tB.iter(W("w:p")):
    if text(p).strip() == "Guilherme Nunes":
        set_text(p, "Guilherme Nunes Joanna")
    elif text(p).strip() == "Joanna Kauã Ribeiro Santos":
        set_text(p, "Kauã Ribeiro Santos")
# fonte monoespaçada perdida na matriz
for rf in list(body.iter(W("w:rFonts"))):
    if any("Gungsuh" in (v or "") for v in rf.attrib.values()):
        rf.getparent().remove(rf)
for p in body.findall(W("w:p")):
    if text(p).strip() == "Apêndice A":
        set_text(p, "APÊNDICE A")
D.save(OUT)
print("\n".join(problems) or "sem problemas")
