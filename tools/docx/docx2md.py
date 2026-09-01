"""Converte o TCC .docx em Markdown preservando hierarquia de titulos e tabelas.

Opera direto sobre o XML (lxml) em vez da API de alto nivel do python-docx por dois
motivos: (1) `Document.tables` so enxerga tabelas de primeiro nivel, e este documento
tem tabelas aninhadas (a declaracao de uso de IA, Apendice B); (2) comparar celulas por
identidade de objeto e' inviavel — os proxies lxml sao coletados e o id() e' reciclado.
O merge e' lido de `w:vMerge`/`w:gridSpan`, que e' como o Word de fato o marca.
"""
import re
import sys
from pathlib import Path

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
# Em OOXML o nome do estilo built-in vem como "heading 1" (minusculo); o styleId pode
# ainda estar localizado ("Ttulo1"). Por isso o nivel e' extraido por regex dos dois,
# em vez de casar com uma tabela de nomes fixos.
HEADING_RE = re.compile(r"(?:heading|t[ií]tulo)\s*([1-6])", re.IGNORECASE)


def q(tag):
    return W + tag


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def para_text(p):
    """Texto do paragrafo, incluindo runs dentro de campos e caixas de texto."""
    parts = []
    for node in p.iter():
        if node.tag == q("t"):
            parts.append(node.text or "")
        elif node.tag in (q("tab"),):
            parts.append(" ")
        elif node.tag in (q("br"), q("cr")):
            parts.append(" ")
    return clean("".join(parts))


def starts_toc_field(p):
    """True se o paragrafo abre o campo TOC (sumario automatico do Word).

    O marcador vive em <w:instrText>, nao em <w:t>, entao nao aparece no texto visivel —
    e as entradas do sumario que vem depois sao paragrafos comuns, indistinguiveis do
    corpo. Detectar o campo aqui e' o que permite descartar o bloco inteiro.
    """
    for node in p.iter(q("instrText")):
        if "TOC" in (node.text or ""):
            return True
    for node in p.iter(q("fldSimple")):
        if "TOC" in (node.get(q("instr")) or ""):
            return True
    return False


def heading_level(p, styles):
    """Nivel do titulo (1..6), ou None se o paragrafo for corpo de texto."""
    ppr = p.find(q("pPr"))
    if ppr is None:
        return None
    ref = ppr.find(q("pStyle"))
    if ref is None:
        return None
    style_id = ref.get(q("val")) or ""
    for candidate in (styles.get(style_id, ""), style_id):
        match = HEADING_RE.search(candidate)
        if match:
            return int(match.group(1))
    return None


def cell_blocks(tc, styles):
    """Conteudo de uma celula: paragrafos e, se houver, tabelas aninhadas achatadas."""
    out = []
    for child in tc.iterchildren():
        if child.tag == q("p"):
            t = para_text(child)
            if t:
                out.append(t)
        elif child.tag == q("tbl"):
            for line in render_table(child, styles):
                out.append(line)
    return out


def render_table(tbl, styles):
    grid = []
    for tr in tbl.findall(q("tr")):
        row, pending_vmerge = [], []
        for tc in tr.findall(q("tc")):
            tcpr = tc.find(q("tcPr"))
            vmerge = tcpr.find(q("vMerge")) if tcpr is not None else None
            gridspan = tcpr.find(q("gridSpan")) if tcpr is not None else None
            span = int(gridspan.get(q("val"))) if gridspan is not None else 1

            # vMerge sem val, ou val="continue", e' continuacao de um merge vertical:
            # a celula nao repete o texto, fica vazia. val="restart" e' o topo do merge.
            is_continuation = vmerge is not None and vmerge.get(q("val")) in (None, "continue")
            text = "" if is_continuation else " ".join(cell_blocks(tc, styles))

            row.append(text)
            row.extend([""] * (span - 1))  # gridSpan: celula ocupa N colunas
        grid.append(row)

    if not grid:
        return []
    width = max(len(r) for r in grid)
    grid = [r + [""] * (width - len(r)) for r in grid]

    def fmt(row):
        return "| " + " | ".join(c.replace("|", "\\|") or " " for c in row) + " |"

    return [fmt(grid[0]), "|" + "---|" * width] + [fmt(r) for r in grid[1:]]


def iter_blocks(parent):
    """Blocos (w:p / w:tbl) em ordem, desembrulhando content controls (w:sdt).

    O Word envolve trechos em <w:sdt> — neste documento, a declaracao de uso de IA do
    Apendice B. Sem descer no <w:sdtContent>, esse conteudo some silenciosamente.
    """
    for child in parent.iterchildren():
        if child.tag in (q("p"), q("tbl")):
            yield child
        elif child.tag == q("sdt"):
            content = child.find(q("sdtContent"))
            if content is not None:
                yield from iter_blocks(content)


def load_style_names(zf):
    """Mapeia styleId -> nome legivel (ex: 'Heading1' -> 'Heading 1')."""
    from lxml import etree
    root = etree.fromstring(zf.read("word/styles.xml"))
    names = {}
    for st in root.findall(q("style")):
        name = st.find(q("name"))
        if name is not None:
            names[st.get(q("styleId"))] = name.get(q("val"))
    return names


def main(src, dst):
    import zipfile
    from lxml import etree

    with zipfile.ZipFile(src) as zf:
        styles = load_style_names(zf)
        root = etree.fromstring(zf.read("word/document.xml"))

    body = root.find(q("body"))
    lines = []
    skipping_toc = False

    for block in iter_blocks(body):
        if block.tag == q("tbl"):
            lines += [""] + render_table(block, styles) + [""]
            continue
        level = heading_level(block, styles)
        text = para_text(block)

        # Sumario: descartado — o Markdown ganha navegacao propria pelos titulos.
        # Descarta do campo TOC ate o proximo titulo real.
        if starts_toc_field(block):
            skipping_toc = True
            continue
        if skipping_toc:
            if level:
                skipping_toc = False
            else:
                continue

        if not text:
            continue
        if level:
            lines += ["", f"{'#' * level} {text}", ""]
        else:
            lines += [text, ""]

    md = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    Path(dst).write_text(md, encoding="utf-8")
    print(f"OK: {len(md.splitlines())} linhas, {len(md)} chars, "
          f"{md.count(chr(10) + '|---')} tabelas -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
