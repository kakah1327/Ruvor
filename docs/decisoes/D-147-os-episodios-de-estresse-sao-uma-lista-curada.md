# D-147 — Os episódios de estresse são uma lista curada, com datas de calendário

**Status:** aceita · 2026-09-29 — datas decididas pelo dono da frente no portão da spec do M3.3

## Contexto

O estresse histórico (D-146) precisa dizer **quais** momentos mostra. Há dois caminhos: detectar, em cada ativo, as
piores janelas da própria série, ou fixar uma lista de episódios, a mesma para todos. A detecção responde "quando
este ativo sofreu" — pergunta que a maior queda do M1.3 já responde para a série inteira —; a lista responde "como
este ativo passou pelo que o mercado inteiro passou", que é o que a PRODUTO §5.3 descreve e o que permite comparar
com o Ibovespa no mesmo recorte.

## Decisão

1. **A lista é curada e fechada**, a mesma para todo ativo, escrita uma vez no código do cálculo.
2. **Cada episódio é um código estável, uma data de início e uma data de fim, de calendário.** Os pregões saem das
   datas pela regra "último pregão em ou antes da data", em cada série (spec do M3.3, RF-02).
3. **A lista**, em ordem cronológica, decidida no portão:

   | Código | Episódio | Início | Fim | Por que estas datas |
   |---|---|---|---|---|
   | `jbs_2017` | A delação da JBS | 2017-05-17 | 2017-06-30 | o início é o último pregão **antes** da divulgação da gravação, na noite de 17 de maio; o fim fecha o mês seguinte — **escolha do autor** |
   | `truckers_2018` | A greve dos caminhoneiros | 2018-05-18 | 2018-06-29 | o início é a sexta-feira antes do primeiro dia da greve (21 de maio); o fim fecha junho. **O recorte é o da greve, não o da queda do ano**, que começou antes (decisão do dono) |
   | `covid_2020` | A chegada da COVID | 2020-02-21 | 2020-03-31 | o início é o último pregão antes do Carnaval; o fim fecha março, com o fundo do Ibovespa dentro |
   | `rates_2021` | A alta dos juros | 2021-06-07 | 2022-07-14 | o ciclo de alta da Selic começou em março de 2021; a janela abre no recorde de fechamento do Ibovespa em 2021 e fecha no fundo de 2022 (decisão do dono). O código leva o ano de início, como os outros |

4. **A recessão de 2015–16 fica fora**: a série começa em 2016-09-22.
5. **Mudar a lista — episódio novo, episódio tirado, data mudada — é decisão nova** que restringe esta. As linhas já
   gravadas guardam o código e as datas que usaram, e continuam válidas; os nomes dos códigos aposentados ficam no
   módulo de textos.

## Conferência no banco

Feita em 2026-09-29 no banco de desenvolvimento, só leitura, sobre o `silver.price` do IBOV (fechamento; no índice,
`adj_close = close`):

| Episódio | Início (P0) | Pregão seguinte | Fim (Pn) | Menor fechamento na janela |
|---|---|---|---|---|
| `jbs_2017` | 2017-05-17 — 67.540 | 2017-05-18 — 61.597 (−8,8%) | 2017-06-30 — 62.900 | 2017-06-21 — 60.762 |
| `truckers_2018` | 2018-05-18 — 83.082 | 2018-05-21 — 81.815 | 2018-06-29 — 72.763 | 2018-06-18 — 69.815 |
| `covid_2020` | 2020-02-21 — 113.681 | 2020-02-26 — 105.718 (sem pregão em 24 e 25, o Carnaval) | 2020-03-31 — 73.020 | 2020-03-23 — 63.570 |
| `rates_2021` | 2021-06-07 — 130.776 | 2021-06-08 — 129.787 | 2022-07-14 — 96.121 | 2022-07-14 — 96.121 |

- **As oito pontas são pregões do IBOV**, e P0 e Pn caem exatamente nas datas de calendário.
- **Os oito pregões descartados do IBOV** (datas com pregão no ITUB4 e sem linha no IBOV: 2017-06-15, 2017-09-07,
  2017-10-12, 2017-11-02, 2017-11-15, 2017-11-20, 2017-12-25, 2018-01-25) **não caem em nenhuma ponta**; um deles,
  2017-06-15, fica **dentro** da janela da JBS, e a medida do índice nesse episódio usa um pregão a menos.
- **O recorde de 2021 confere**: 2021-06-07 é o maior fechamento do IBOV no ano (130.776; depois vêm 2021-06-14 e
  2021-06-04).
- **O fundo de 2022 confere**: 2022-07-14 é pregão do IBOV (96.121) e o menor fechamento de toda a janela
  2021-06-07 a 2022-07-14; o pregão seguinte, 2022-07-15, fecha em 96.551. A janela tem **277 pregões** em cada uma
  das seis séries do banco.
- **O que a conferência mostrou, e o portão decidiu**: em 2018 o topo do ano foi 2018-02-26 (87.653), e o IBOV já
  caía desde 2018-05-16 (86.537) — a janela pega a greve, não a queda inteira, e **fica assim**; a primeira proposta
  do ciclo de juros terminava em 2021-11-30, o próprio fundo daquela janela, com o pregão seguinte (2021-12-01,
  100.775) mais baixo — cortava a queda —, e **o fim passou ao fundo de 2022**.
- **No IBOV, o ciclo de juros começa no topo e termina no fundo**: o `period_return` e o `drawdown` do índice nesse
  episódio coincidem.

## Consequências

- A ordem mostrada é cronológica; nenhuma ordem por tamanho da queda.
- O backend e o módulo de textos do frontend compartilham os códigos, e um teste de contrato os confronta; a PR que
  muda a lista muda os dois lados e os dois testes.
- Um ativo que abriu capital depois do início de um episódio fica "sem dado" nele.

Origem: [spec M3.3 — Estresse histórico](../specs/M3.3-estresse-historico.md) (RF-01 a RF-03).
