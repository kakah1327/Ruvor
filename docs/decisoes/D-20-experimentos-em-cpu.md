# D-20 — Experimentos do TCC em CPU, com paralelizacao por ativo

**Status:** aceita · 2026-08-29

## Contexto

O time tem RTX 3060 Ti e RTX 5060, ambas em Windows. O TensorFlow nao usa GPU no Windows nativo desde a versao 2.11. Existem saidas (Keras 3 sobre PyTorch, WSL2), mas as redes do projeto sao minusculas.

## Decisão

Os experimentos rodam em **CPU, com os ativos paralelizados em processos separados**.

## Consequências

- GPU brilha com matriz e lote grandes; com redes de 16-32 unidades e janela de 20 dias, o custo de mover dado para a placa pode comer o ganho.
- O que provavelmente domina o tempo e a quantidade de chamadas pequenas em sequencia, nao conta pesada — e isso se resolve paralelizando, de graca.
- 4 processos exigem ~8 GB de RAM livre e limite de threads por processo, senao brigam pelos mesmos nucleos.
- **Tarefa pendente:** medir onde o tempo esta indo antes de investir em mudanca de ambiente.
