# D-114 — Tabela que só cresce é guardada também no banco, por gatilho

**Status:** aceita · 2026-09-29 · frente `identidade`

## Contexto

O "só cresce" do repositório vivia só no Django: `core.access_event`
([D-104](D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md)) recusa `save()` de
linha existente, `delete()` e a escrita em massa do queryset. Nada segura um `UPDATE` feito pelo
`psql`, por SQL cru ou por um caminho sem o gerente. Um relatório ([D-113](D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md))
que se pudesse alterar pelo banco não provaria nada.

## Decisão

`core.report` é imutável em duas camadas. **No Django**, o molde do `AccessEvent`: `save()` de
linha existente, `delete()` da instância e `update()` e `delete()` do queryset — pelo gerente padrão
e pelo gerente base — levantam `TypeError("report so cresce")`. **No banco**, a função
`core.report_so_cresce()` e o gatilho `report_so_cresce`, `BEFORE UPDATE OR DELETE ... FOR EACH
ROW`, criados por `RunSQL` na migration `accounts.0006_report`, com a reversa que os apaga, levantam
`report so cresce`. É o **primeiro gatilho do repositório**.

O `TRUNCATE` **continua passando**: gatilho por linha não dispara nele, e é assim que a suíte limpa
o banco. A proteção é contra a alteração de uma linha, não contra quem administra o banco.

## Consequências

- `core.report` é a primeira tabela assim; `core.access_event` pode receber o mesmo gatilho por
  decisão futura.
- Teste que prova o gatilho envolve cada `UPDATE` e `DELETE` cru em `transaction.atomic()`: o erro
  do banco envenena a transação do teste.
- Medido na execução real (2026-09-30): `UPDATE core.report SET size_bytes = 0` pelo `psql` →
  `ERROR:  report so cresce`.

Origem: [spec M4.1 — Relatórios](../specs/M4.1-relatorios.md).
