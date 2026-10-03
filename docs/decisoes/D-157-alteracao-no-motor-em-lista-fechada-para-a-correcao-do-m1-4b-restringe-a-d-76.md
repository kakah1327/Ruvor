# D-157 — Alteração no motor em lista fechada para a correção do M1.4b; restringe a D-76, a D-21 e a D-46

**Status:** aceita · 2026-10-02 · com a aprovação da [spec do M1.4b](../specs/M1.4b-correcao-do-motor.md)

## Contexto

A conferência técnica do M2.3 (2026-10-02) achou dois defeitos no motor, os dois vindos do motor original: o GARCH e o
EGARCH testavam cada dia com uma previsão que já conhecia o retorno daquele dia (`_sigma_path`, em
`engine/src/engine/models/garch/_conditional.py`), e os três tradicionais ficavam presos ao quantil dos 252 primeiros
retornos no teste inteiro. Corrigir é mexer em código que a [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) congela
até a Etapa 6 e que a [D-76](D-76-alteracao-no-motor-em-lista-fechada-restringe-a-d-21.md) só abriu, em lista
fechada, para os retratos do M1.5b. A [D-46](D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md) diz que "a Etapa
6 corre com esta configuração".

## Decisão

**Só podem mudar, e só para a correção:**

| Arquivo | Para quê |
|---|---|
| `engine/src/engine/models/garch/_conditional.py` | o alinhamento de `_sigma_path` e a docstring |
| `engine/src/engine/models/traditional/historical.py`, `parametric.py`, `monte_carlo.py` | a janela expansiva e os hiperparâmetros |
| `engine/src/engine/models/traditional/_expanding.py` (novo) | o laço comum, se o plano o quiser |
| `engine/src/engine/models/base.py` | **só as duas docstrings** que ficam falsas (o `{}` legítimo para os tradicionais; os modelos "estáticos") |
| `engine/pyproject.toml` | a versão |
| `engine/tests/` | os testes do motor, inclusive `baseline/valores.json`, o script de captura novo e a fixture do trecho 0 |

**Nenhuma linha** de `models/ml/`, de `backtesting/`, de `runner.py`, de `seeding.py` ou de `snapshots.py`, nem
código de `base.py`. A D-46 ("a Etapa 6 corre com esta configuração") passa a valer para a configuração corrigida.

## Consequências

- A lista foi conferida no fecho por `git diff --stat origin/main -- engine/src/` (V-07): seis arquivos, todos da lista
  — `base.py` só nas duas docstrings, e o `_expanding.py` criado pelo plano.
- A D-21 continua valendo para o que ela protege — biblioteca, arquitetura e hiperparâmetro de ML. Outra alteração no
  motor antes da Etapa 6 precisa de lista própria.
- A Etapa 6 do TCC, que ainda não rodou, roda sobre o motor `0.4.0`.

Origem: [spec M1.4b — Correção do motor](../specs/M1.4b-correcao-do-motor.md).
