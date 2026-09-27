"""Conformacao de um documento da CVM: das linhas cruas as contas, em reais.

Puro — sem ORM e sem `zipfile`: recebe `DocumentRows` ja montados por
`documents.documents_from_zip`. `conform_accounts` da as contas de um documento;
`conform_year` junta os documentos de uma companhia num ano de zip e decide os periodos
(trimestre isolado, 4o trimestre) e as acoes (RF-13 a RF-15).

A ordem e a da spec, e cada passo e uma regra dela:

1. linhas identicas viram uma (RF-08);
2. a maior `VERSAO` de cada demonstracao, e o `DT_RECEB` do indice com a mesma `VERSAO`
   (RF-10) — o filtro de `ULTIMO` nao mora aqui, e so de `documents.py`;
3. o escopo: consolidado se ha linha no `_con`, senao individual (RF-09);
4. a escala: `MIL` x 1000, `UNIDADE` x 1, outra levanta `ValueError` (RF-11);
5. o plano, pela descricao da `3.01` (RF-12);
6. as contas, pela tabela `RULES` — dado, nao `if` (RF-08).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from apps.fundamentals.documents import DocumentRows

Scope = Literal["consolidated", "individual"]
StatementName = Literal["bpa", "bpp", "dre"]
Row = dict[str, str]

SCALES: dict[str, Decimal] = {"MIL": Decimal(1000), "UNIDADE": Decimal(1)}

# RF-12: a tabela da spec, literal.
PLAN_BY_REVENUE_LABEL: dict[str, str] = {
    "Receita de Venda de Bens e/ou Serviços": "general",
    "Receitas de Intermediação Financeira": "bank",
    "Receitas da Intermediação Financeira": "bank",
    "Receitas das Atividades Seguradoras/Resseguradoras": "insurance",
    "Receitas das Operações": "insurance",
}
GENERAL = "general"
UNKNOWN = "unknown"
REVENUE_CODE = "3.01"

BALANCE_FIELDS = ("total_assets", "cash", "gross_debt", "equity_parent")
RESULT_FIELDS = ("revenue", "ebit", "net_income_parent")
FIELDS = BALANCE_FIELDS + RESULT_FIELDS


@dataclass(frozen=True)
class Match:
    """Descricao comparada depois de `strip()`: **igual** a uma de `labels`, ou **comeca com**."""

    labels: tuple[str, ...]
    mode: Literal["equal", "prefix"] = "equal"

    def matches(self, description: str) -> bool:
        text = description.strip()
        if self.mode == "equal":
            return text in self.labels
        return any(text.startswith(label) for label in self.labels)


@dataclass(frozen=True)
class Parcel:
    """Uma parcela de um campo.

    `parent` e um codigo (so a raiz do BPA, `"1"`, e a `"3.01"`) ou a descricao de uma
    conta **fixa de nivel 1**. `child`, se houver, e a descricao de uma **filha direta**
    dela — o codigo da mae mais exatamente um segmento —, fixa ou nao conforme
    `child_fixed`. `sign` e +1 (soma) ou -1 (subtrai).
    """

    parent: Match | str
    child: Match | None = None
    child_fixed: bool = False
    sign: int = 1


@dataclass(frozen=True)
class Rule:
    """A regra de um campo num escopo: as parcelas somadas, na demonstracao `statement`.

    `when_child_present` e o caso (a) do `equity_parent` consolidado: se a mae dessa
    parcela tem ao menos uma filha com a descricao dela, o campo e so essa parcela; senao,
    `parcels` — o caso (b).
    """

    field: str
    scope: Scope
    statement: StatementName
    parcels: tuple[Parcel, ...]
    only_general: bool = False
    when_child_present: Parcel | None = None


# A tabela Contas da spec. As descricoes sao copiadas dela, byte a byte.
_CURRENT_ASSETS = Match(("Ativo Circulante",))
_CASH = Match(("Caixa e Equivalentes de Caixa",))
_INVESTMENTS = Match(("Aplicações Financeiras",))
_CURRENT_LIABILITIES = Match(("Passivo Circulante",))
_NONCURRENT_LIABILITIES = Match(("Passivo Não Circulante",))
_LOANS = Match(("Empréstimos e Financiamentos",))
_EQUITY = Match(("Patrimônio Líquido",), mode="prefix")
_EQUITY_CONTROLLER = Match(("Patrimônio Líquido Atribuído ao Controlador",))
_NONCONTROLLING = Match(("Participação dos Acionistas Não Controladores",))
_EBIT = Match(("Resultado Antes do Resultado Financeiro e dos Tributos",))
_PROFIT_CONSOLIDATED = Match(
    (
        "Lucro/Prejuízo Consolidado do Período",
        "Lucro ou Prejuízo Líquido Consolidado do Período",
    )
)
_PROFIT_CONTROLLER = Match(
    (
        "Atribuído a Sócios da Empresa Controladora",
        "Atribuído aos Sócios da Empresa Controladora",
    )
)
_PROFIT_INDIVIDUAL = Match(
    ("Lucro/Prejuízo do Período", "Lucro ou Prejuízo Líquido do Período")
)


def _same_in_both_scopes(
    field: str,
    statement: StatementName,
    parcels: tuple[Parcel, ...],
    only_general: bool = False,
) -> tuple[Rule, Rule]:
    return (
        Rule(field, "consolidated", statement, parcels, only_general),
        Rule(field, "individual", statement, parcels, only_general),
    )


RULES: tuple[Rule, ...] = (
    *_same_in_both_scopes("total_assets", "bpa", (Parcel("1"),)),
    *_same_in_both_scopes(
        "cash",
        "bpa",
        (
            Parcel(_CURRENT_ASSETS, _CASH, child_fixed=True),
            Parcel(_CURRENT_ASSETS, _INVESTMENTS, child_fixed=True),
        ),
        only_general=True,
    ),
    *_same_in_both_scopes(
        "gross_debt",
        "bpp",
        (
            Parcel(_CURRENT_LIABILITIES, _LOANS, child_fixed=True),
            Parcel(_NONCURRENT_LIABILITIES, _LOANS, child_fixed=True),
        ),
        only_general=True,
    ),
    Rule(
        "equity_parent",
        "consolidated",
        "bpp",
        (Parcel(_EQUITY), Parcel(_EQUITY, _NONCONTROLLING, sign=-1)),
        when_child_present=Parcel(_EQUITY, _EQUITY_CONTROLLER),
    ),
    Rule("equity_parent", "individual", "bpp", (Parcel(_EQUITY),)),
    *_same_in_both_scopes("revenue", "dre", (Parcel(REVENUE_CODE),), only_general=True),
    *_same_in_both_scopes("ebit", "dre", (Parcel(_EBIT),), only_general=True),
    Rule(
        "net_income_parent",
        "consolidated",
        "dre",
        (Parcel(_PROFIT_CONSOLIDATED, _PROFIT_CONTROLLER),),
    ),
    Rule("net_income_parent", "individual", "dre", (Parcel(_PROFIT_INDIVIDUAL),)),
)


@dataclass(frozen=True)
class Accounts:
    """As contas de um documento, em reais.

    Os campos de resultado sao `DT_INI_EXERC → valor`, um por periodo presente na DRE do
    escopo — o isolado e o acumulado; escolher entre eles e da conformacao por ano. Valor
    `None` e campo nulo. `missing` lista os campos nulos **pela regra do RF-08** (o
    `ausentes` do relatorio); nulo por plano ("so `general`") nao entra nele. `capital` e
    a `composicao_capital` do documento na maior `VERSAO` (RF-10).
    """

    scope: Scope
    version: int
    received_date: date | None
    account_plan: str
    name: str
    cnpj: str
    total_assets: Decimal | None
    cash: Decimal | None
    gross_debt: Decimal | None
    equity_parent: Decimal | None
    revenue: dict[date, Decimal | None]
    ebit: dict[date, Decimal | None]
    net_income_parent: dict[date, Decimal | None]
    missing: list[str]
    capital: list[Row]


def conform_accounts(doc: DocumentRows) -> Accounts:
    """As contas de `doc`, pelos seis passos do modulo."""
    # 1. duplicatas, 2. versao, 3. escopo
    scope, scoped = scoped_statements(doc)
    capital = latest_version(_unique(doc.capital))
    version = _document_version(scoped, doc.index_rows)
    index_row = next((r for r in doc.index_rows if int(r["VERSAO"]) == version), None)
    # 4. escala
    for rows in scoped.values():
        for row in rows:
            if row["ESCALA_MOEDA"] not in SCALES:
                raise ValueError(f"ESCALA_MOEDA {row['ESCALA_MOEDA']}")
    # 5. plano
    plan = account_plan(scoped["dre"])
    # 6. contas
    periods = sorted({row["DT_INI_EXERC"] for row in scoped["dre"]})
    balance: dict[str, Decimal | None] = {}
    results: dict[str, dict[date, Decimal | None]] = {}
    missing: list[str] = []
    for rule in RULES:
        if rule.scope != scope:
            continue
        rows = scoped[rule.statement]
        by_plan = rule.only_general and plan != GENERAL
        if rule.statement == "dre":
            values = {
                date.fromisoformat(p): None if by_plan else locate(rows, rule, p)
                for p in periods
            }
            results[rule.field] = values
            if not by_plan and (not values or None in values.values()):
                missing.append(rule.field)
        else:
            value = None if by_plan else locate(rows, rule, None)
            balance[rule.field] = value
            if not by_plan and value is None:
                missing.append(rule.field)

    name = index_row["DENOM_CIA"] if index_row else _any_name(scoped)
    return Accounts(
        scope=scope,
        version=version,
        received_date=date.fromisoformat(index_row["DT_RECEB"]) if index_row else None,
        account_plan=plan,
        name=name,
        cnpj=doc.cnpj,
        total_assets=balance["total_assets"],
        cash=balance["cash"],
        gross_debt=balance["gross_debt"],
        equity_parent=balance["equity_parent"],
        revenue=results["revenue"],
        ebit=results["ebit"],
        net_income_parent=results["net_income_parent"],
        missing=[field for field in FIELDS if field in missing],
        capital=capital,
    )


def scoped_statements(
    doc: DocumentRows,
) -> tuple[Scope, dict[StatementName, list[Row]]]:
    """Os passos 1 a 3: sem duplicatas, na maior `VERSAO`, e so as do escopo."""
    # 1. duplicatas
    statements: dict[tuple[Scope, StatementName], list[Row]] = {
        ("consolidated", "bpa"): _unique(doc.bpa_con),
        ("consolidated", "bpp"): _unique(doc.bpp_con),
        ("consolidated", "dre"): _unique(doc.dre_con),
        ("individual", "bpa"): _unique(doc.bpa_ind),
        ("individual", "bpp"): _unique(doc.bpp_ind),
        ("individual", "dre"): _unique(doc.dre_ind),
    }
    # 2. versao
    statements = {key: latest_version(rows) for key, rows in statements.items()}
    # 3. escopo
    scope: Scope = (
        "consolidated"
        if any(rows for (s, _), rows in statements.items() if s == "consolidated")
        else "individual"
    )
    scoped: dict[StatementName, list[Row]] = {
        name: rows for (s, name), rows in statements.items() if s == scope
    }
    return scope, scoped


def latest_version(rows: list[Row]) -> list[Row]:
    """So as linhas da maior `VERSAO` presente (RF-10)."""
    if not rows:
        return []
    top = max(int(row["VERSAO"]) for row in rows)
    return [row for row in rows if int(row["VERSAO"]) == top]


def account_plan(dre: list[Row]) -> str:
    """O plano pela descricao da `3.01` da DRE do documento (RF-12); fora da tabela, `unknown`."""
    labels = {row["DS_CONTA"].strip() for row in dre if row["CD_CONTA"] == REVENUE_CODE}
    if len(labels) != 1:
        return UNKNOWN
    return PLAN_BY_REVENUE_LABEL.get(labels.pop(), UNKNOWN)


def locate(rows: list[Row], rule: Rule, period_key: str | None) -> Decimal | None:
    """O valor do campo de `rule`, em reais, ou `None` (RF-08).

    `period_key` e o `DT_INI_EXERC` na DRE e `None` no balanco, que nao o tem. A busca
    conta **linhas**, nao codigos: dentro do periodo, qualquer parcela que case com zero
    ou mais de uma linha — na mae ou na filha — anula o campo inteiro.
    """
    if period_key is not None:
        rows = [row for row in rows if row["DT_INI_EXERC"] == period_key]
    parcels = rule.parcels
    preferred = rule.when_child_present
    if preferred is not None and _children(rows, preferred):
        parcels = (preferred,)
    total = Decimal(0)
    for parcel in parcels:
        value = _parcel_value(rows, parcel)
        if value is None:
            return None
        total += parcel.sign * value
    return total


def _parcel_value(rows: list[Row], parcel: Parcel) -> Decimal | None:
    if parcel.child is None:
        parents = _parents(rows, parcel)
        return _value(parents[0]) if len(parents) == 1 else None
    children = _children(rows, parcel)
    return _value(children[0]) if len(children) == 1 else None


def _parents(rows: list[Row], parcel: Parcel) -> list[Row]:
    if isinstance(parcel.parent, str):
        code = parcel.parent
        return [row for row in rows if row["CD_CONTA"] == code]
    match = parcel.parent
    return [
        row
        for row in rows
        if row["CD_CONTA"].count(".") == 1
        and row["ST_CONTA_FIXA"] == "S"
        and match.matches(row["DS_CONTA"])
    ]


def _children(rows: list[Row], parcel: Parcel) -> list[Row]:
    """As filhas diretas da mae de `parcel` que casam; mae nao unica → nenhuma."""
    parents = _parents(rows, parcel)
    if len(parents) != 1 or parcel.child is None:
        return []
    prefix = parents[0]["CD_CONTA"] + "."
    child = parcel.child
    return [
        row
        for row in rows
        if row["CD_CONTA"].startswith(prefix)
        and "." not in row["CD_CONTA"][len(prefix) :]
        and (not parcel.child_fixed or row["ST_CONTA_FIXA"] == "S")
        and child.matches(row["DS_CONTA"])
    ]


def _value(row: Row) -> Decimal:
    return Decimal(row["VL_CONTA"]) * SCALES[row["ESCALA_MOEDA"]]


def _unique(rows: list[Row]) -> list[Row]:
    """Linhas com todos os campos guardados iguais viram uma, na ordem (RF-08)."""
    seen: set[tuple[tuple[str, str], ...]] = set()
    unique: list[Row] = []
    for row in rows:
        key = tuple(sorted(row.items()))
        if key not in seen:
            seen.add(key)
            unique.append(row)
    return unique


def _document_version(
    scoped: dict[StatementName, list[Row]], index_rows: list[Row]
) -> int:
    """A `VERSAO` do documento: a das demonstracoes do escopo, ou a do indice sem elas."""
    versions = [int(row["VERSAO"]) for rows in scoped.values() for row in rows]
    if not versions:
        versions = [int(row["VERSAO"]) for row in index_rows]
    return max(versions) if versions else 0


def _any_name(scoped: dict[StatementName, list[Row]]) -> str:
    return next((row["DENOM_CIA"] for rows in scoped.values() for row in rows), "")


# Conformacao por ano: o trimestre isolado, o 4o trimestre e as acoes (RF-13 a RF-15).

FOURTH_QUARTER_DAYS = range(88, 94)  # de 88 a 93 dias entre o ITR e o DFP (RF-14)
BASIC_EPS_LABEL = "Lucro Básico por Ação"


@dataclass(frozen=True)
class ConformedStatement:
    """Uma linha de `silver.financial_statement`, sem `company`, `run` e `updated_at`.

    Mais `missing` (o `ausentes` do RF-08, do documento), e `name` e `cnpj`, para o
    `silver.company` do RF-19. Os campos de resultado sao do **trimestre isolado**.
    """

    reference_date: date
    fiscal_year_start: date | None
    source: Literal["itr", "dfp"]
    version: int
    received_date: date | None
    scope: Scope
    account_plan: str
    total_assets: Decimal | None
    cash: Decimal | None
    gross_debt: Decimal | None
    equity_parent: Decimal | None
    revenue: Decimal | None
    ebit: Decimal | None
    net_income_parent: Decimal | None
    shares_on: int | None
    shares_pn: int | None
    shares_scale: int | None
    share_composition: bool
    missing: list[str]
    name: str
    cnpj: str


@dataclass(frozen=True)
class _Conformed:
    """Um documento com as contas e a DRE do escopo (passos 1 a 3)."""

    doc: DocumentRows
    accounts: Accounts
    dre: list[Row]
    fiscal_year_start: date | None  # o menor `DT_INI_EXERC` da DRE; nulo sem DRE


def conform_year(
    itr: list[DocumentRows], dfp: list[DocumentRows], itr_prev: list[DocumentRows]
) -> list[ConformedStatement]:
    """As linhas de uma companhia num ano de zip, por `reference_date` crescente.

    `itr` e `dfp` sao os documentos do ano; `itr_prev`, os ITR do ano anterior — so
    candidatos ao 4o trimestre (RF-14), sem linha propria.
    """
    current = [_conform(doc) for doc in itr]
    candidates = current + [_conform(doc) for doc in itr_prev]
    statements = [_statement(item, _isolated(item)) for item in current]
    for doc in dfp:
        annual = _conform(doc)
        statements.append(_statement(annual, _fourth_quarter(annual, candidates)))
    return sorted(statements, key=lambda statement: statement.reference_date)


def infer_share_scale(L: Decimal, N: int, E: Decimal) -> int | None:
    if not L or N <= 0 or not E or (L / E) < 0:
        return None
    best = min((1, 1000), key=lambda k: abs(math.log(float(L / (N * k) / E))))
    return best if abs(math.log(float(L / (N * best) / E))) < math.log(2) else None


def _conform(doc: DocumentRows) -> _Conformed:
    accounts = conform_accounts(doc)
    _, scoped = scoped_statements(doc)
    dre = scoped["dre"]
    starts = [date.fromisoformat(row["DT_INI_EXERC"]) for row in dre]
    return _Conformed(doc, accounts, dre, min(starts) if starts else None)


def _isolated(item: _Conformed) -> dict[str, Decimal | None]:
    """ITR: o valor do **maior** `DT_INI_EXERC` de cada campo de resultado (RF-14)."""
    results: dict[str, Decimal | None] = {}
    for field in RESULT_FIELDS:
        values: dict[date, Decimal | None] = getattr(item.accounts, field)
        results[field] = values[max(values)] if values else None
    return results


def _accumulated(values: dict[date, Decimal | None]) -> Decimal | None:
    """O acumulado do exercicio: o valor do **menor** `DT_INI_EXERC`."""
    return values[min(values)] if values else None


def _fourth_quarter(
    annual: _Conformed, candidates: list[_Conformed]
) -> dict[str, Decimal | None]:
    """DFP: o anual menos o acumulado do ITR anterior, campo a campo (RF-14)."""
    previous = _previous_itr(annual, candidates)
    results: dict[str, Decimal | None] = {}
    for field in RESULT_FIELDS:
        total = _accumulated(getattr(annual.accounts, field))
        partial = (
            None
            if previous is None
            else _accumulated(getattr(previous.accounts, field))
        )
        results[field] = None if total is None or partial is None else total - partial
    return results


def _previous_itr(
    annual: _Conformed, candidates: list[_Conformed]
) -> _Conformed | None:
    """O ITR do mesmo exercicio com o maior `DT_REFER` anterior ao do DFP — se valer.

    Nao vale, e da nulo, fora de 88 a 93 dias do DFP ou em outro escopo. ITR sem DRE
    (`fiscal_year_start` nulo) nunca e candidato.
    """
    if annual.fiscal_year_start is None:
        return None
    reference = annual.doc.reference_date
    same_year = [
        item
        for item in candidates
        if item.fiscal_year_start == annual.fiscal_year_start
        and item.doc.reference_date < reference
    ]
    if not same_year:
        return None
    previous = max(same_year, key=lambda item: item.doc.reference_date)
    if (reference - previous.doc.reference_date).days not in FOURTH_QUARTER_DAYS:
        return None
    if previous.accounts.scope != annual.accounts.scope:
        return None
    return previous


def _statement(
    item: _Conformed, results: dict[str, Decimal | None]
) -> ConformedStatement:
    accounts = item.accounts
    shares_on, shares_pn, shares_scale = _shares(item)
    return ConformedStatement(
        reference_date=item.doc.reference_date,
        fiscal_year_start=item.fiscal_year_start,
        source=item.doc.kind,
        version=accounts.version,
        received_date=accounts.received_date,
        scope=accounts.scope,
        account_plan=accounts.account_plan,
        total_assets=accounts.total_assets,
        cash=accounts.cash,
        gross_debt=accounts.gross_debt,
        equity_parent=accounts.equity_parent,
        revenue=results["revenue"],
        ebit=results["ebit"],
        net_income_parent=results["net_income_parent"],
        shares_on=shares_on,
        shares_pn=shares_pn,
        shares_scale=shares_scale,
        share_composition=bool(accounts.capital),
        missing=accounts.missing,
        name=accounts.name,
        cnpj=accounts.cnpj,
    )


def _shares(item: _Conformed) -> tuple[int | None, int | None, int | None]:
    """`shares_on`, `shares_pn` e `shares_scale` (RF-15); os tres nulos se inconclusivo.

    `L` e o lucro acumulado, em reais; `N`, o total integralizado menos o total em
    tesouraria, como veio; `E`, o LPA basico do mesmo `DT_INI_EXERC` de `L`, sem escala.
    Mais de uma linha de `composicao_capital` na maior `VERSAO` e inconclusivo.
    """
    capital = item.accounts.capital
    profits = item.accounts.net_income_parent
    if len(capital) != 1 or not profits:
        return None, None, None
    (row,) = capital
    period = min(profits)
    profit = profits[period]
    eps = _basic_eps(item.dre, period)
    total = _difference(row, "QT_ACAO_TOTAL_CAP_INTEGR", "QT_ACAO_TOTAL_TESOURO")
    on = _difference(row, "QT_ACAO_ORDIN_CAP_INTEGR", "QT_ACAO_ORDIN_TESOURO")
    pn = _difference(row, "QT_ACAO_PREF_CAP_INTEGR", "QT_ACAO_PREF_TESOURO")
    if profit is None or eps is None or total is None or on is None or pn is None:
        return None, None, None
    scale = infer_share_scale(profit, total, eps)
    if scale is None:
        return None, None, None
    return on * scale, pn * scale, scale


def _basic_eps(dre: list[Row], period: date) -> Decimal | None:
    """A primeira filha direta, por `CD_CONTA`, de "Lucro Básico por Ação", com valor
    diferente de zero, no periodo `period` — em reais por acao, **sem** `ESCALA_MOEDA`."""
    rows = [row for row in dre if row["DT_INI_EXERC"] == period.isoformat()]
    parents = {
        row["CD_CONTA"] for row in rows if row["DS_CONTA"].strip() == BASIC_EPS_LABEL
    }
    children = sorted(
        (
            row
            for row in rows
            if "." in row["CD_CONTA"]
            and row["CD_CONTA"].rsplit(".", 1)[0] in parents
            and Decimal(row["VL_CONTA"]) != 0
        ),
        key=lambda row: row["CD_CONTA"],
    )
    return Decimal(children[0]["VL_CONTA"]) if children else None


def _difference(row: Row, integral: str, treasury: str) -> int | None:
    """`integral - treasury`, em inteiros; nulo se algum dos dois nao e numero."""
    try:
        return int(row[integral]) - int(row[treasury])
    except (KeyError, ValueError):
        return None
