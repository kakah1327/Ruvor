# D-72 — O fecho escreve metadado de execução; restringe a D-16

**Status:** aceita · 2026-09-25

## Contexto

A [D-16](D-16-resultado-e-imutavel.md) manda que nunca se atualize um resultado, e o M1.4 a
levou ao pé da letra: o RF-11 da spec dele e dois docstrings (`apps/risk/models.py` e
`apps/risk/compute.py`) afirmavam que "nenhum caminho do código faz `update` ou `delete`".

No caminho assíncrono, a `risk_run` nasce `running` na abertura
([D-71](D-71-a-risk-run-nasce-no-worker.md)) e só o fecho sabe o desfecho
([D-70](D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md)). Escrever o estado exige mexer
numa linha que já existe.

## Decisão

**O fecho faz `UPDATE` na `risk_run`, e só nela**: `close_run` escreve `status` e
`finished_at`, com `save(update_fields=["status", "finished_at"])`. É o único `update` sobre
`gold`.

A distinção que sustenta a restrição: **o que é imutável é o resultado**, e nenhum
`risk_result` é alterado nem apagado. O que muda é **metadado de execução** — o mesmo que o
`bronze.collection_run` faz desde o M1.1, passando de `running` a `ok` ou `failed` sem que
ninguém chamasse aquilo de violação.

## Consequências

- A D-16 continua valendo para o que ela protege: recalcular insere execução nova, com
  manifesto novo, e os números de uma execução nunca mudam. Nenhum caminho do código faz
  `delete`.
- **`finished_at` passa a ser escrito quando o grupo fecha.** A descrição "nulo enquanto
  roda", que o M1.4 carregava e que com escrita atômica nunca foi verdadeira — a linha
  nascia pronta —, passa a ser fato no caminho assíncrono.
- O caminho síncrono **não** faz `update`: sabe o desfecho antes de escrever e cria a linha
  já com o estado final.
- A spec do M1.4 é histórica e não é reescrita: o RF-11 dela ganhou uma nota apontando para
  esta decisão. Os dois docstrings foram corrigidos no M1.5.

Origem: [spec M1.5 — Execução assíncrona](../specs/M1.5-execucao-assincrona.md) ("O estado da
`risk_run`").
