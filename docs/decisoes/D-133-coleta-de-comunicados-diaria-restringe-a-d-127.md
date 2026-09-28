# D-133 — A coleta de comunicados é diária, em entrada própria do Beat; restringe a D-127

**Status:** aceita · 2026-09-27 · restringe a
[D-127](D-127-coleta-de-fundamentos-semanal-e-encadeada-restringe-a-d-69.md)

## Contexto

A [D-127](D-127-coleta-de-fundamentos-semanal-e-encadeada-restringe-a-d-69.md) deu ao Beat a
terceira entrada, `fundamentos`, semanal, e disse que "uma quarta entrada, de qualquer frente,
reprova na mesma guarda até que outra decisão a admita". A CVM regera os zips do IPE do ano
corrente e do anterior **todo dia** (`Last-Modified` medido em 2026-09-27), e comunicado é
notícia: uma semana de atraso não serve. A coleta de comunicados não alimenta cálculo nenhum.

## Decisão

**O Beat ganha a quarta entrada**, `comunicados` → `apps.fundamentals.tasks.importar_comunicados`,
com `_cron("RUVOR_BEAT_DISCLOSURES_CRON", "0 20 * * 1-5")` — segunda a sexta, 20h, depois dos
preços. **Não encadeia nada.** A tarefa é casca sobre `import_disclosures`, captura `CommandError`
e devolve `"FALHOU: ..."`, como a `importar_fundamentos`.

A guarda de `tests/risk/test_beat.py` foi atualizada, não removida: o conjunto esperado é
`{"catalogo", "precos", "fundamentos", "comunicados"}`. As outras três entradas não mudam, e
nenhuma aponta para `apps.risk.tasks.*` — a regra da D-69 segue.

## Consequências

- A variável chega ao serviço `beat` por uma linha no `environment` do `compose.yaml` (V-09 do
  M3.2; sem a linha, reprova — mutação 24).
- Uma quinta entrada reprova na mesma guarda até que outra decisão a admita.
- Na coleta diária, em regra só os zips do ano corrente e do anterior mudam; os outros respondem
  "não modificado", sem baixar.

Origem: [spec M3.2 — Contexto](../specs/M3.2-contexto.md) (RF-16 a RF-18).
