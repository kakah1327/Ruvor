# D-65 — A plataforma lista os modelos aprovados e não elege nenhum

**Status:** aceita · 2026-09-24

## Contexto

Dezoito resultados por ativo, cada um com veredito. A pergunta seguinte é natural: qual
deles a plataforma recomenda?

## Decisão

Nenhum. A plataforma **lista os aprovados** e para aí.

Os backtests atestam **adequação, não superioridade**: passar em Kupiec e Christoffersen diz
que o modelo não foi rejeitado, não que é melhor que outro que também não foi. Eleger um
exigiria um critério de desempate — menor perda pinball? VaR mais conservador? mais recente?
— que nenhuma literatura fixa, e escolher um por conta própria seria vender como ciência o
que seria preferência.

## Consequências

- Nenhuma coluna de "vencedor", nenhum ranking, nenhuma ordenação com significado normativo
  em `gold.risk_result`.
- **Nenhum modelo aprovado é um resultado possível e legítimo.** Se nenhum dos nove passar
  para um ativo, a tela não terá o que recomendar — e isso é informação, não falha:
  significa que nenhum método testado descreve bem aquele ativo, que é o tipo de honestidade
  que o produto promete ([PRODUTO.md](../PRODUTO.md)). O M1.6 precisa saber desenhar esse
  caso; este bloco garante que ele seja **distinguível de erro**, pelo `adequate` falso
  contra o `adequate` nulo.
- O diferencial do produto continua sendo **a comparação com validação estatística**, não a
  recomendação. Trocar uma pela outra é o caminho mais curto para parecer com o que já
  existe.

Origem: [spec M1.4 — Motor de risco](../specs/M1.4-motor-de-risco.md) (RF-15).
