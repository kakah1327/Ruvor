# D-76 — Alteração no motor em lista fechada para os retratos; restringe a D-21

**Status:** aceita · 2026-09-27

## Contexto

A [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) proíbe trocar backend ou biblioteca de ML
antes da Etapa 6, e o projeto a vinha lendo como congelamento do código de ML do motor. O M1.5b
não troca biblioteca nenhuma, mas precisa mexer em código que ela congelou: guardar e restaurar
o estado treinado das redes e do `caviar` em cada ponto de retreino, e semear cada retreino
([D-75](D-75-as-redes-semeiam-em-cada-retreino-estende-a-d-63.md)). A alteração foi autorizada
pelo humano em 2026-09-25.

## Decisão

**Só estes arquivos de `engine/src/engine/` podem mudar**, e só para isso:

| Arquivo | Para quê |
|---|---|
| `seeding.py` | a semente derivada por ponto de retreino |
| `snapshots.py` (novo) | o formato do retrato — só `numpy` e `json`, **verificado pelo mypy** |
| `models/ml/_quantile_nn.py` | semear em cada retreino; expor e aceitar retratos |
| `models/ml/caviar.py` | expor e aceitar o `beta` de cada ponto |
| `experiments/runner.py` | levar retratos para dentro do experimento e trazê-los para fora, também com erro |
| `models/base.py` | só se a interface precisasse de declaração comum — **não precisou** |

Mais o `pyproject.toml` do motor, só pela versão `0.3.0`. **Nenhuma linha de cálculo** dos seis
não neurais, **nenhum hiperparâmetro**, **nenhuma arquitetura**.

A lógica do retrato mora em `snapshots.py`, fora da isenção de tipos que
`engine.models.ml._quantile_nn` carrega; o que muda em `_quantile_nn.py` é o mínimo que chama
esse módulo. O TensorFlow continua importado dentro das funções que o usam: importar
`engine.snapshots` e `engine.experiments.runner` com `tensorflow` e `keras` bloqueados funciona
(V-18).

## Consequências

- A lista foi conferida no fecho por `git diff` sobre `engine/src/` desde o primeiro commit do
  bloco (V-12): cinco arquivos, todos da lista; `base.py` intocado.
- A D-21 continua valendo para o que ela protege — biblioteca e backend de ML. Qualquer outra
  alteração no motor antes da Etapa 6 precisa de lista própria, autorizada.
- A isenção de tipos de `_quantile_nn` não foi removida: removê-la exigiria tipar código
  congelado que não mudou aqui.

Origem: [spec M1.5b — Treino separado da previsão](../specs/M1.5b-treino-separado-da-previsao.md)
(RF-11).
