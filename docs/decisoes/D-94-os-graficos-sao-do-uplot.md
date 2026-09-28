# D-94 — Os gráficos são do uPlot; a comparação dos modelos é tabela

**Status:** aceita · 2026-09-28

## Contexto

A tela do ativo do M1.6b precisa de gráficos — o preço de dez anos (~2.500 pregões) e a
distribuição dos retornos (42 baldes) — e da comparação dos nove modelos de VaR nos dois níveis. O
frontend não tinha biblioteca de gráfico, e os gráficos dos mockups de referência são SVG escritos à
mão, com cor literal.

Três bibliotecas foram comparadas lado a lado, sobre o mesmo dado real da API, nos dois temas
([`docs/mockups/M1.6b/graficos-comparativo.html`](../mockups/M1.6b/graficos-comparativo.html)):
Recharts (SVG, componentes React, ~159 KB gz sem o React, segue o tema sozinho pelo `var()`), uPlot
(canvas, ~22 KB gz, o mais rápido) e lightweight-charts (canvas, ~61 KB gz, o melhor gráfico de
preço, fraco fora de série temporal). O comparativo recomendou o Recharts; o dono da frente escolheu
o uPlot.

## Decisão

1. **Os gráficos do produto são do [uPlot](https://github.com/leeoniya/uPlot)** (licença MIT),
   dependência do `frontend/` numa versão fixa, com um invólucro React próprio.
2. **A cor vem dos tokens**, lida por `getComputedStyle` pelo nome do token (`--ruvor-*`), nunca
   escrita: a varredura de cor de `frontend/src/` continua valendo sem exceção. Como o canvas não
   resolve `var()`, **o gráfico redesenha na troca de tema** — pela chave e pela mudança de
   `prefers-color-scheme`.
3. **A comparação dos nove modelos é tabela, não gráfico** — com a barra do kit (`.ruvor-bar`) e o
   veredito em tag. O eixo por categoria e a cor por barra são o ponto fraco do uPlot, e a tabela é
   o vocabulário dos mockups `02` e `04`, segue o tema pelo CSS e é legível por leitor de tela.

## Consequências

- Cada gráfico tem alternativa em texto, porque o canvas não é lido por leitor de tela.
- O jsdom não implementa canvas: os testes do frontend substituem o uPlot por duplo e provam cor,
  tema e alternativa em texto; o desenho é provado pelas capturas da execução real e pela revisão
  contra o mockup.
- Gráfico novo (o M1.6c, o laboratório do M2.4) usa o mesmo invólucro.

Origem: [spec M1.6b — As telas](../specs/M1.6b-as-telas.md) (RF-22).
