"""Conformacao de um documento da CVM: das linhas cruas as contas, em reais.

Puro — sem ORM e sem `zipfile`: recebe `DocumentRows` ja montados por
`documents.documents_from_zip`. Esta parte cobre as contas; os periodos (trimestre
isolado, 4o trimestre) e as acoes sao da conformacao por ano.

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
    capital = latest_version(_unique(doc.capital))
    # 3. escopo
    scope: Scope = (
        "consolidated"
        if any(rows for (s, _), rows in statements.items() if s == "consolidated")
        else "individual"
    )
    scoped: dict[StatementName, list[Row]] = {
        name: rows for (s, name), rows in statements.items() if s == scope
    }
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
