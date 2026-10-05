"""Estatísticas do ranking (stats.json) e as quatro figuras do TCC, a partir dos dados exportados.

Uso: python figuras.py <pasta-de-dados>

Lê lab_result.csv, lab_year.csv e serie.csv da pasta (ver exportar.sh) e grava stats.json e fig/*.png nela.
"""

import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as md
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import FancyBboxPatch

DADOS = Path(sys.argv[1])
FIG = DADOS / "fig"
FIG.mkdir(exist_ok=True)
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

NAME = {"historical": "Histórico", "parametric": "Paramétrico", "monte_carlo": "Monte Carlo",
        "garch_1_1": "GARCH(1,1)", "egarch": "EGARCH", "lstm": "LSTM", "gru": "GRU", "garchnet": "GARCHNet",
        "caviar": "CAViaR"}
ORDER = list(NAME)
ATIVOS = ["IBOV", "PETR4", "VALE3", "ITUB4"]


def ler(nome):
    with open(DADOS / nome, encoding="utf-8") as f:
        linhas = f.read().splitlines()
    # o psql e o manage.py shell deixam linhas antes do cabeçalho e o rodapé "(N rows)"
    ini = next(i for i, l in enumerate(linhas) if l.startswith("ticker;"))
    return [r for r in csv.DictReader(linhas[ini:], delimiter=";") if r["ticker"] and not r["ticker"].startswith("(")]


R = ler("lab_result.csv")
Y = ler("lab_year.csv")


def t(v):
    return v == "t"


# ------------------------------------------------------------------ estatísticas do ranking
st = defaultdict(lambda: defaultdict(float))
for r in R:
    s = st[r["model_name"]]
    s["adeq"] += t(r["adequate"])
    s["kup"] += t(r["kp"])
    s["chr"] += t(r["cp"])
    s["dq"] += t(r["dp"])
    s["all3"] += t(r["kp"]) and t(r["cp"]) and t(r["dp"])
    s["dev"] += abs(int(r["violations"]) / float(r["ev"]) - 1) / (len(ATIVOS) * 2)
for y in Y:
    s = st[y["model_name"]]
    if y["alpha"] == "0.0500":
        s["yadeq"] += t(y["adequate"])
        s["yjud"] += y["adequate"] != ""
    # Basileia a 99%: só os anos completos de 252 pregões; verde até 4 violações, vermelha a partir de 10
    if y["alpha"] == "0.0100" and int(y["test_count"]) == 252:
        v = int(y["violations"])
        s["green"] += v <= 4
        s["red"] += v >= 10
        s["ny"] += 1
json.dump({m: dict(st[m]) for m in st}, open(DADOS / "stats.json", "w"), indent=1)
rank = sorted(ORDER, key=lambda m: (-st[m]["adeq"], -st[m]["all3"], -st[m]["dq"], st[m]["dev"]))
for i, m in enumerate(rank, 1):
    print(i, NAME[m], {k: round(v, 3) for k, v in st[m].items()})

# ------------------------------------------------------------------ Figura 2: VaR a 99% e violações, PETR4
S = ler("serie.csv")


def serie(m, a):
    v = [r for r in S if r["model"] == m and r["alpha"] == a]
    return ([date.fromisoformat(r["date"]) for r in v], np.array([float(r["ret"]) for r in v]),
            np.array([float(r["var"]) for r in v]))


d, ret, vh = serie("historical", "0.01")
_, _, vg = serie("garch_1_1", "0.01")
D = np.array(d)
fig, ax = plt.subplots(figsize=(6.3, 3.0), dpi=200)
ax.vlines(D, 0, ret * 100, color="#9aa3a8", lw=0.6, label="Retorno logarítmico diário")
ax.plot(d, -vh * 100, color="#1f4e79", lw=1, label="VaR 99% – Histórico")
ax.plot(d, -vg * 100, color="#b5452b", lw=0.9, label="VaR 99% – GARCH(1,1)")
mh, mg = ret < -vh, ret < -vg
ax.scatter(D[mg], ret[mg] * 100, s=9, color="#b5452b", zorder=3, label=f"Violação GARCH(1,1) ({mg.sum()})")
ax.scatter(D[mh], ret[mh] * 100, s=16, facecolors="none", edgecolors="#1f4e79", zorder=4,
           label=f"Violação Histórico ({mh.sum()})")
ax.set_ylabel("% ao dia")
ax.xaxis.set_major_locator(md.YearLocator())
ax.xaxis.set_major_formatter(md.DateFormatter("%Y"))
ax.set_ylim(-40, 15)
ax.legend(fontsize=7, ncol=2, loc="lower right", frameon=False)
ax.grid(axis="y", color="#e5e5e5", lw=0.6)
fig.tight_layout()
fig.savefig(FIG / "serie_petr4.png")
plt.close(fig)

# ------------------------------------------------------------------ Figura 6: violações observadas ÷ esperadas
cols = [(a, n) for a in ATIVOS for n in ("0.0500", "0.0100")]
M = np.zeros((9, 8))
A = np.zeros((9, 8), bool)
for r in R:
    i, j = ORDER.index(r["model_name"]), cols.index((r["ticker"], r["alpha"]))
    M[i, j] = int(r["violations"]) / float(r["ev"])
    A[i, j] = t(r["adequate"])
fig, ax = plt.subplots(figsize=(6.3, 3.4), dpi=200)
im = ax.imshow(M, cmap="RdBu_r", norm=TwoSlopeNorm(vcenter=1, vmin=0.4, vmax=1.8), aspect="auto")
for i in range(9):
    for j in range(8):
        ax.text(j, i, f"{M[i, j]:.2f}".replace(".", ",") + ("*" if A[i, j] else ""), ha="center", va="center",
                fontsize=7.5, fontweight="bold" if A[i, j] else "normal",
                color="white" if (M[i, j] < 0.62 or M[i, j] > 1.5) else "black")
ax.set_xticks(range(8), [f"{a}\n{'95%' if n == '0.0500' else '99%'}" for a, n in cols])
ax.set_yticks(range(9), [NAME[m] for m in ORDER])
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
cb.set_label("violações observadas ÷ esperadas", fontsize=7.5)
cb.ax.tick_params(labelsize=7)
fig.tight_layout()
fig.savefig(FIG / "razao_violacoes.png")
plt.close(fig)

# ------------------------------------------------------------------ Figura 7: anos adequados a 95%
fig, ax = plt.subplots(figsize=(6.3, 2.6), dpi=200)
yy = np.arange(9)[::-1]
total = int(max(st[m]["yjud"] for m in ORDER))
ax.barh(yy, [st[m]["yadeq"] for m in rank], color="#1f4e79", height=0.6)
for y_, m in zip(yy, rank):
    ax.text(st[m]["yadeq"] + 0.4, y_, f"{int(st[m]['yadeq'])} de {total}", va="center", fontsize=7.5)
ax.set_yticks(yy, [NAME[m] for m in rank])
ax.set_xlim(0, total + 4)
ax.set_xlabel(f"anos considerados adequados a 95% ({len(ATIVOS)} ativos × 9 anos)")
fig.tight_layout()
fig.savefig(FIG / "anos_adequados.png")
plt.close(fig)

# ------------------------------------------------------------------ Figura 1: arquitetura (não depende dos dados)
plt.rcParams.update({"font.size": 8})
fig, ax = plt.subplots(figsize=(6.3, 3.3), dpi=200)
ax.set_xlim(0, 100)
ax.set_ylim(0, 52)
ax.axis("off")


def caixa(x, y, w, h, titulo, sub="", fc="#eef2f6", ec="#1f4e79"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=0.9))
    ax.text(x + w / 2, y + h / 2 + (1.6 if sub else 0), titulo, ha="center", va="center", fontweight="bold")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 2.2, sub, ha="center", va="center", fontsize=6.6, color="#333")


def seta(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", color="#555", lw=0.9))


caixa(1, 40, 20, 9, "Fontes externas", "B3 · Yahoo · CVM", fc="#f6f1ea", ec="#8a6d3b")
caixa(27, 40, 22, 9, "Coleta (Celery)", "agendada pelo Beat")
caixa(55, 40, 44, 9, "PostgreSQL", "bronze → silver → gold")
caixa(27, 22, 22, 11, "Motor (engine)", "9 modelos de VaR\n4 testes de backtesting", fc="#fbecea", ec="#b5452b")
caixa(55, 22, 29, 11, "Tarefas de cálculo", "risco diário · laboratório\nretorno · relatórios")
caixa(79, 4, 20, 10, "API REST", "Django REST /api/v1")
caixa(55, 4, 20, 10, "Interface web", "React + TypeScript")
caixa(27, 4, 22, 10, "Usuário", "navegador", fc="#f6f1ea", ec="#8a6d3b")
seta(21, 44.5, 27, 44.5)
seta(49, 44.5, 55, 44.5)
seta(69, 40, 69, 33.5)
seta(55, 27.5, 49, 27.5)
seta(93, 40, 93, 14.5)
seta(79, 9, 75, 9)
seta(55, 9, 49, 9)
ax.text(94.5, 30, "leitura", fontsize=6.3, color="#555", va="center")
fig.tight_layout()
fig.savefig(FIG / "arquitetura.png")
plt.close(fig)
print("figuras em", FIG)
