# D-122 — Conta se localiza pela descrição sob mãe fixa definida, não pelo código; a companhia tem plano de contas

**Status:** aceita · 2026-09-27

## Contexto

Nos dados abertos da CVM, o código de uma conta não diz o que ela é. O patrimônio líquido é
`2.03` numa companhia do plano geral, `2.07` num banco de uma forma e `2.08` no de outra; o
lucro é `3.11`, `3.09` ou `3.13`. A parte da controladora ora é conta fixa, ora não
(`ST_CONTA_FIXA`), conforme o tipo de companhia e o ano.

E a mesma descrição aparece em **dois níveis**: no BPP da Petrobras (DFP 2024),
`2.01.04` "Empréstimos e Financiamentos" (R$ 68,8 bi, com o arrendamento) e a filha
`2.01.04.01`, de mesma descrição (R$ 15,9 bi, sem ele).

## Decisão

**Cada campo conformado se localiza pela descrição**, sob uma **mãe de nível 1 fixa**, também
localizada por descrição, e "filha" é **só a direta** — o código da mãe mais um segmento. Por
código, só a raiz do BPA (`1`) e a receita (`3.01`). A descrição se compara depois de
`strip()`, por igualdade ou por prefixo, declarado campo a campo na tabela de Contas da spec.
Parcela que a regra não acha, ou acha duas vezes, torna o campo **nulo** — contado, não
adivinhado.

**Cada documento tem um plano** — `general`, `bank`, `insurance` ou `unknown` —, lido da
descrição da `3.01` daquele documento. Indicador que não se aplica ao plano (receita, EBIT,
margens, caixa e dívida fora do `general`) é **nulo**, e o plano gravado na linha diz por quê.
`silver.company.account_plan` é o do documento mais recente.

**A dívida bruta inclui o arrendamento** (decisão do dono da frente): é a soma das filhas
diretas "Empréstimos e Financiamentos" do passivo circulante e do não circulante, que desde o
IFRS 16 contêm o arrendamento.

## Consequências

- Bancos entram: lucro, PL, ROE e múltiplos valem; receita, margens e dívida saem nulas. O Itaú
  sai com dívida bruta nula na V-13, pelo plano `bank`, e não por lacuna.
- A dívida líquida e a dívida/PL daqui saem maiores que as de quem exclui o arrendamento; a tela
  precisa dizer o que entra. Na V-13, a dívida bruta da PETR4 no 2T26 é R$ 366.533 mi: 133.734
  de dívida financeira e 232.799 de arrendamentos, como na divulgação da companhia.
- A regra foi medida em três arquivos (ITR 2016, ITR 2025, DFP 2024) e roda sobre os 22.
  Variante nova de descrição é achado da spec, que volta a ela e se aplica por `--reconform` —
  não se acrescenta em silêncio. A revisão final achou uma: a grafia "Atribuído aos Sócios não
  Controladores" dos bancos forma A ([D-129](D-129-lucro-so-na-mae-vale-a-mae.md)).

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) (RF-08, RF-12; "Contas").
