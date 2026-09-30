# D-146 — O estresse histórico vira bloco: só do ativo, só com preço

**Status:** aceita · 2026-09-29 · estende a
[D-96](D-96-discordancia-e-aprovados-entram-no-marco-1.md), item 3 ("5.3 e o resto continuam candidatos"): promove o
requisito candidato 5.3 da [PRODUTO](../PRODUTO.md#53-estresse-histórico)

## Contexto

A PRODUTO §5.3 descreve o estresse histórico como "esta carteira teria perdido 38% em março de 2020" e o chama de
"custo quase zero, altíssimo poder de comunicação". A [D-96](D-96-discordancia-e-aprovados-entram-no-marco-1.md)
promoveu o 5.1 e o 5.2 ao Marco 1 e deixou o 5.3 candidato. O texto de origem fala em **carteira**, que é o Marco 2
(M2.2), e cita a recessão de 2015–16, que a série — iniciada em 2016-09-22 — não cobre.

## Decisão

1. **O 5.3 vira o bloco M3.3**, da frente `marco1`, no Marco 3 ("tudo sobre a ação").
2. **É do ativo**, não da carteira. O estresse de uma carteira vem com o M2.2, sobre o que este bloco deixar.
3. **É só preço** — a queda, o retorno e a recuperação do preço ajustado em cada episódio —, na **camada 2**
   (comportamento), ao lado da maior queda do M1.3. **Não usa os modelos de VaR**: comparar o previsto com o
   ocorrido traria a D-15, a D-98 e a D-65 e fica para outra decisão.

## Consequências

- O cálculo segue as regras da camada 2: backend, biblioteca padrão, linha imutável, sem manifesto (D-58, D-59,
  D-55, D-60).
- O horizonte de um dia da D-98 não se aplica: o estresse descreve o passado, não estima perda.
- A PRODUTO (§5.3 e a tabela de pendências) e o ROADMAP (o parágrafo do Marco 1 que diz o 5.3 candidato) passam a
  dizer que o requisito entrou, restrito ao ativo; os outros candidatos da D-96, item 3, seguem candidatos.

Origem: [spec M3.3 — Estresse histórico](../specs/M3.3-estresse-historico.md).
