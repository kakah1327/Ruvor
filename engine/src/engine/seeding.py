"""Semente da execucao, para que os modelos neurais sejam reproduziveis.

A D-21 congela o motor de ML ate a Etapa 6 e nomeia a semente como a excecao necessaria:
sem ela, `garchnet`, `lstm` e `gru` dao numeros diferentes a cada execucao e nao ha
manifesto possivel.

A divisao e deliberada e tem duas metades:

- `configure(seed)` so GUARDA o valor, e e chamado uma vez por experimento pelo runner;
- `apply(position)` SEMEIA, e e chamado no inicio de cada treino (`_fit_for_alpha`, com a
  posicao 0) e no inicio de cada retreino das redes (com a posicao do ponto de retreino).

Semear no runner semearia antes de nada acontecer — o `fit()` dos neurais e preguicoso e
nao consome aleatoriedade nenhuma —, e a reprodutibilidade passaria a depender de toda a
sequencia posterior ser identica. Aplicando por treino, cada (modelo, alpha) e reprodutivel
isoladamente, independente da ordem em que os alphas foram pedidos ou de quem chamou.

Aplicando tambem por retreino (M1.5b, RF-05), cada retreino deixa de depender do estado do
gerador que os anteriores deixaram no processo: um calculo incremental, num processo novo,
reproduz o retreino da posicao k sem ter rodado os anteriores. A semente de cada posicao sai
de `derive(position)`, que combina a semente da execucao com a posicao — a posicao 0 devolve
a semente da execucao sem transformacao, e e por isso que o treino inicial sai igual ao do
motor 0.2.0.

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


#: primo (2**31 - 1); as posicoes de retreino sao multiplos de 252 e nunca chegam perto dele
_MODULUS = 2**31 - 1


def derive(position: int) -> int:
    """A semente do treino na `position` do trecho de teste.

    Posicao 0 devolve a semente configurada, EXATAMENTE — e o que mantem o treino inicial
    igual ao do motor 0.2.0. Nas demais, posicoes diferentes dao sementes diferentes, e
    sementes da execucao diferentes dao sementes diferentes na mesma posicao (RF-05).
    """
    if position == 0:
        return _seed
    return (_seed * 100_003 + position) % _MODULUS


def apply(position: int = 0) -> None:
    """Semeia `random`, o gerador global legado do NumPy e o TensorFlow de uma vez, com
    `derive(position)`. Sem argumento, semeia com a semente configurada.

    Os seis modelos nao neurais usam `np.random.default_rng(...)`, que nao le o estado
    global do NumPy — por isso a semeadura nao muda nenhum numero deles.
    """
    from tensorflow import keras

    keras.utils.set_random_seed(derive(position))
