# D-185 — O experimento mora em `gold.lab_run`, `gold.lab_result` e `gold.lab_year`, nasce fechado e é imutável no Django e no banco; um experimento bom por identidade, e motor novo é experimento novo

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do
[M2.4](../specs/M2.4-regime-de-laboratorio.md) aprovada pelo dono (no portão: a opção (a) do `partial`)

## Contexto

O experimento é resultado ([D-16](D-16-resultado-e-imutavel.md)) com manifesto
([D-15](D-15-manifesto-de-execucao.md)). Ao contrário da `risk_run`, que nasce `running` e recebe o fecho,
o cálculo inteiro do experimento acontece antes da escrita.

## Decisão

1. **Três tabelas em `gold`**, da app `apps/risk`, migration `0004`: `lab_run` (o manifesto, uma linha por
   tentativa), `lab_result` (uma por modelo e nível, sem `var_latest`, `var_mean` e `basel_zone`, mais a
   contagem do teste) e `lab_year` (uma por resultado e trecho; os testes e o veredito nulos a 99% e no
   trecho não julgado). Chaves estrangeiras `PROTECT`.
2. **Nasce fechado e é imutável nas duas camadas**: no Django, o molde de `core.report` (`save` de linha
   existente, `delete` e as escritas em massa levantam `lab so cresce`); no banco, o gatilho da
   [D-114](D-114-tabela-que-so-cresce-e-guardada-tambem-no-banco-por-gatilho.md) nas três. O `TRUNCATE`
   passa.
3. **A identidade** é (`asset`, `engine_version`, `seed`, `train_window_days`, `first_price_date`,
   `decade_end`, `library_versions_hash`), com restrição única parcial **só sobre `ok`**
   (`lab_run_identity_ok`): o `partial` se refaz no fecho seguinte (a opção (a), decidida pelo dono no
   portão; a (b), o `partial` definitivo, foi preterida). A impressão digital dos preços é gravada e fica
   fora da identidade.

## Consequências

- Com motor, semente, janela ou biblioteca novos, o experimento antigo fica e o novo se soma; a rota
  mostra o mais recente.
- Provento depois do experimento não o refaz; a série que muda **durante** o cálculo grava `failed`
  ("série mudou durante o cálculo"), e o próximo fecho refaz.
- A tabela cresce uma linha por ativo por versão do motor, mais um `partial` por dia útil enquanto um
  modelo falhar — sem problema de volume.
