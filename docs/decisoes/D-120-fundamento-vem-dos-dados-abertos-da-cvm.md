# D-120 — Fundamento vem dos dados abertos da CVM (DFP e ITR), por HTTP direto

**Status:** aceita · 2026-09-27

## Contexto

A camada 4 — lucro, patrimônio, dívida, margens, múltiplos — precisa de balanço, e o
repositório não tinha fonte para isso. O Yahoo, fonte do preço
([D-50](D-50-preco-vem-do-chart-v8-do-yahoo-por-http-direto.md)), não serve para a B3, como o
ROADMAP já registrava; e a capitalização de mercado ficou fora do M1.3 pelo mesmo motivo.

O produto promete transparência sobre o método. Um número sem origem verificável contradiz
isso na primeira pergunta do usuário.

## Decisão

**A fonte são os dados abertos da CVM**: os zips anuais de ITR e DFP em
`https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/{ITR,DFP}/DADOS/{itr,dfp}_cia_aberta_<ano>.zip`,
de 2016 até o ano corrente, baixados **por HTTP direto** (`urllib`), pelo cliente
`apps/fundamentals/cvm.py` — o único lugar onde a URL existe, no molde do `yahoo.py`.

Alternativas descartadas:

- **raspar Fundamentus ou Status Invest** — frágil, sujeito aos termos de uso, e o número vem
  sem método: é exatamente o que o produto promete não fazer;
- **API comercial** — custo e dependência de fornecedor, para um dado que o regulador publica
  de graça.

## Consequências

- O dado é oficial, gratuito e tem trilha de auditoria: cada linha da `silver` aponta para o
  documento, a versão e a data de recebimento na CVM.
- Quem conforma lida com o formato da CVM, e ele é irregular: Latin-1, contas localizadas por
  descrição ([D-122](D-122-conta-se-localiza-pela-descricao-sob-mae-fixa.md)), quantidade de
  ações sem escala ([D-124](D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md)),
  registros mal formados nos CSVs e documentos com a mesma data em ITR e DFP
  ([D-128](D-128-itr-e-dfp-na-mesma-data-vale-o-dfp.md)).
- A primeira carga real (2026-09-27) baixou 22 arquivos, ~404 MiB, em 4 min 43 s.
- A V-13 conferiu lucro de 12 meses, PL e dívida bruta de PETR4, VALE3 e ITUB4 (2T26) contra a
  divulgação de cada companhia, e os três bateram.
- EBITDA fica de fora: depreciação e amortização estão na DFC em linhas abertas, sem regra que
  não erre calada.

Origem: [spec M3.1 — Fundamentos](../specs/M3.1-fundamentos.md) ("A fonte, medida"; RF-03).
