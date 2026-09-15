# D-46 — O ajuste GARCH/EGARCH tenta de novo quando não converge

**Status:** aceita · 2026-09-15

## Contexto

A [D-22](D-22-treino-centralizado-em-container.md) manda a Etapa 6 do TCC rodar em contêiner
— ou seja, em Linux. A [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) congela o motor até a
Etapa 6, e o `pyproject.toml` do motor lê isso como "não se edita `_conditional.py`".

Medido em 2026-09-15, no serviço `worker` desta máquina, com as **mesmas versões** de
`numpy`, `scipy`, `arch`, `pandas` e OpenBLAS do `.venv/` do Windows: o reajuste do EGARCH
sobre 504 pontos da série da linha de base **não converge em Linux**. O SLSQP devolve
`convergence_flag: 4` ("Inequality constraints incompatible"), log-verossimilhança
**−26.328 contra −692** no Windows, `alpha[1] = 10,96` e volatilidade condicional até 1383.
A série de VaR resultante chega a **2032%** em 12 dos 300 pontos.

Não é "outro ótimo": é otimização que falhou, e um resultado não convergido não é uma
estimativa de máxima verossimilhança. A causa é o **ponto de partida padrão do `arch`**, que
vem de uma busca em grade cujo resultado muda com a ordem de redução do BLAS. A partir de
valores iniciais explícitos e razoáveis (`alpha = 0,05`, `beta = 0,95`, `omega` derivado da
variância amostral), **as duas plataformas convergem** para ótimos sãos.

As duas decisões não podem ser satisfeitas ao mesmo tempo sem tocar no ajuste: a Etapa 6
rodaria em Linux com um EGARCH quebrado, e o ranking mostraria o ambiente, não o método —
exatamente o que a D-22 existe para impedir.

## Decisão

`ConditionalVolatilityVaR._fit_arch` **verifica `convergence_flag`**. Se o ajuste a partir do
ponto padrão do `arch` não converge, tenta de novo a partir de uma lista curta de valores
iniciais que cada modelo declara (`_fallback_starting_values`), na ordem, e devolve o
primeiro que converge — emitindo um aviso que diz de onde partiu. Se nenhum converge, levanta
`RuntimeError`. Um ajuste com `convergence_flag != 0` nunca mais é devolvido.

Isto **restringe a D-21**, e só nisto: a regra "nenhuma mudança de backend ou biblioteca de
ML" continua valendo por inteiro. Nada muda de biblioteca; o que muda é recusar um resultado
que o próprio otimizador declarou inválido.

## Consequências

- **A linha de base do Windows não muda.** Nenhum ajuste dela tem `convergence_flag != 0`,
  então o caminho novo não dispara; os 58 testes originais seguem passando, byte a byte.
- **A linha de base continua não portátil**, e agora se sabe por quê: a série dela é ruído
  i.i.d. de 1%, sem estrutura EGARCH para identificar. A superfície de verossimilhança é
  quase plana — 5 unidades separam `beta = 0` de `beta = 0,996` — e cada plataforma cai num
  ótimo local diferente. No próprio Windows o VaR do EGARCH sobe monotonicamente de 8% a
  **113%** no primeiro bloco. A linha de base provou o que tinha de provar no F2a (a migração
  não mudou lógica); não é referência de comportamento do EGARCH.
- **A Etapa 6 corre com esta configuração**, nas duas plataformas, sem ajuste não convergido.
  A ordem da D-21 continua: semente → Tabela 1 → Etapa 6, tudo com este código.
- O aviso emitido no fallback entra no manifesto de execução quando ele existir (M1.4) — é
  parte da rastreabilidade da [D-15](D-15-manifesto-de-execucao.md).
- Os valores de fallback são dois por modelo, escolhidos por serem os pontos "GARCH-típicos"
  (`alpha` pequeno, `beta` alto). Não há busca; se um caso real exigir mais, é decisão nova.

Origem: medição de 2026-09-15 sobre a dívida registrada no F5, em
[ESTADO.md](../ESTADO.md#dívida-registrada).
