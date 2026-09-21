# D-47 — A fonte do catálogo são os endpoints internos do site da B3

**Status:** aceita · 2026-09-15

## Contexto

O `yfinance` não enumera papéis — só responde por ticker. Três fontes foram consideradas na
abertura da spec do M1.1: **brapi.dev** (documentado, com token e plano gratuito de limites
não verificados), **o site da B3** (`sistemaswebb3-listados.b3.com.br`, dois JSONs internos
que a página "Empresas Listadas" consome, sem documentação nem promessa) e **CSV curado** no
repositório.

## Decisão

O catálogo vem dos dois endpoints do site da B3 — listagem (`GetInitialCompanies`) e detalhe
(`GetDetail`). São a fonte oficial: trazem a classificação setorial da própria B3, os códigos
de negociação com ISIN e o segmento de listagem, sem intermediário.

## Consequências

- **Podem quebrar sem aviso.** Três coisas contêm o dano: a `bronze` guarda toda resposta
  crua com data de coleta; só `apps/assets/b3.py` conhece URL e formato; e as fixtures
  versionadas fazem mudança de formato aparecer como teste reprovando antes da coleta real.
- Companhia cancelada não aparece na listagem — a situação do papel é **derivada por
  presença** entre coletas, não lida.
- A B3 troca vírgula por ponto nos nomes de setor; guarda-se como veio.
- Segunda fonte (brapi, CVM) é outro bloco; a `bronze` deixa a troca possível.

Origem: [spec M1.1 — Catálogo de ativos](../specs/M1.1-catalogo-de-ativos.md).
