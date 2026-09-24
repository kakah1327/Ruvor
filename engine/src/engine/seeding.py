"""Semente da execucao, para que os modelos neurais sejam reproduziveis.

A D-21 congela o motor de ML ate a Etapa 6 e nomeia a semente como a excecao necessaria:
sem ela, `garchnet`, `lstm` e `gru` dao numeros diferentes a cada execucao e nao ha
manifesto possivel.

A divisao e deliberada e tem duas metades:

- `configure(seed)` so GUARDA o valor, e e chamado uma vez por experimento pelo runner;
- `apply()` SEMEIA, e e chamado no inicio de cada treino (`_fit_for_alpha`).

Semear no runner semearia antes de nada acontecer — o `fit()` dos neurais e preguicoso e
nao consome aleatoriedade nenhuma —, e a reprodutibilidade passaria a depender de toda a
sequencia posterior ser identica. Aplicando por treino, cada (modelo, alpha) e reprodutivel
isoladamente, independente da ordem em que os alphas foram pedidos ou de quem chamou.

`apply()` NUNCA e inerte: sem `configure()` previo, semeia com `DEFAULT_SEED`. Quem chama o
modelo direto, sem runner, tambem roda semeado.

O TensorFlow e importado DENTRO de `apply()`, nunca no topo: o runner importa este modulo, e
um import de modulo tornaria o TensorFlow obrigatorio para o motor inteiro — uma instalacao
`engine[traditional,garch]` deixaria de conseguir importar o runner.
"""

from __future__ import annotations

#: o padrao do motor; o do backend (apps.risk.config.DEFAULT_SEED) pode divergir
DEFAULT_SEED = 42

_seed: int = DEFAULT_SEED


def configure(seed: int) -> None:
    """Guarda a semente da execucao. NAO semeia — quem semeia e `apply()`."""
    global _seed
    _seed = seed


def apply() -> None:
    """Semeia `random`, o gerador global legado do NumPy e o TensorFlow de uma vez.

    Os seis modelos nao neurais usam `np.random.default_rng(...)`, que nao le o estado
    global do NumPy — por isso a semeadura nao muda nenhum numero deles.
    """
    from tensorflow import keras

    keras.utils.set_random_seed(_seed)
