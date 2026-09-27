# D-134 — As tarefas Celery são tipadas por `celery-types`

**Status:** aceita · 2026-09-27

## Contexto

O Celery não publica tipos. O backend levava um `[[tool.mypy.overrides]]` com
`ignore_missing_imports` para `celery` e `celery.*`, e as tarefas eram `Any` sob o `mypy`
estrito. O comentário das tarefas justificava a forma de registro — a função com sublinhado e
`app.task(name=...)(funcao)` — pelo erro `untyped-decorator`. O ESTADO registrou isso como dívida,
a pagar no próximo bloco que criasse tarefa Celery; o M3.2 cria uma.

Medido em 2026-09-27 num ambiente descartável no `worker`: com `celery-types==0.26.0` e sem o
override, 1 erro em 124 arquivos (`tests/risk/test_beat.py:83`); um módulo com `@app.task` e
`chain(a.s(), a.si())` sai limpo.

## Decisão

**`celery-types==0.26.0` entra no extra `dev` do `backend/pyproject.toml`, e o override de
`celery`/`celery.*` sai.** O `mypy` estrito segue limpo sobre o backend inteiro.

**A forma de registro fica.** Ela já não é necessária para o `mypy`, mas a função com sublinhado
é o ponto que os testes das duas frentes chamam e substituem; trocá-la por decorador
reescreveria esses testes sem ganho de tipo. Muda só o comentário, que deixa de citar o
`untyped-decorator`.

## Consequências

- `project.dependencies` não muda: os tipos são só de desenvolvimento, e chegam à imagem do
  `worker` pelo `./backend[dev]` da construção.
- Devolver o override é detectado (V-10 do M3.2; mutação 25).
- A dívida de tipos do Celery está quitada.

Origem: [spec M3.2 — Contexto](../specs/M3.2-contexto.md) (RF-20).
