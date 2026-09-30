# D-149 — A execução presa é fechada pela regra do fecho, na rotina diária e por comando

**Status:** aceita · 2026-09-29 · responde à pergunta aberta da [D-70](D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md); estende a [D-91](D-91-a-rotina-diaria-e-precos-metricas-risco-estende-a-d-69.md)

## Contexto

A D-70 restringiu a `risk_run` presa em `running` à falha de infraestrutura — o `worker` morto no
meio do leque, o Redis reiniciado sem persistência, o fecho que levanta — e deixou em aberto o que
fazer com a linha: limpar por idade, reprocessar ou deixar para a operação. A
[D-92](D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md) já a trata como presa depois de
`RUVOR_ON_DEMAND_TIMEOUT_MIN` (30 min): a abertura e a API deixam de considerá-la. Mas a linha fica
`running` com `finished_at` nulo para sempre, e os `risk_result` que ela chegou a gravar nunca
aparecem em `latest`.

## Decisão

1. **A execução presa é fechada pela regra do fecho** — `status_for` sobre o que está gravado:
   todos os resultados pedidos sem erro, `ok`; parte, `partial`; nenhum, ou todos com erro, `failed`.
   **Não há status novo**: a lista fechada da [D-68](D-68-o-estado-da-execucao-mora-no-banco.md)
   continua `running`, `ok`, `partial`, `failed`.
2. **Presa é a `running` cujo `calculated_at` é mais velho que `RUVOR_RISK_STALE_AFTER_MIN`**,
   padrão **360** (6 h), que não pode ser menor que `RUVOR_ON_DEMAND_TIMEOUT_MIN`: fechar é escrever
   em `gold`, e exige mais certeza do que ignorar. Seis horas cobrem, com folga, o pior leque
   legítimo medido hoje — a invalidação de todos os retratos, ~160 s por ativo em duas vagas.
3. **Quem fecha é uma varredura**, com dois gatilhos: o **primeiro elo da `rotina_diaria`**, antes
   da coleta de preços, e o comando **`manage.py close_stale_runs`**. **Nenhuma entrada nova no
   Beat**: a D-69 continua proibindo entrada que aponte para `apps.risk.tasks.*`.
4. **O `finished_at` é o instante da varredura**, não o fim real, que ninguém conhece. **Só o log da
   varredura identifica a execução fechada por ela** — não há coluna nova, e `finished_at -
   calculated_at` não serve de marca: o prazo é configuração, o comando aceita outro, e um fecho legítimo
   também pode passar dele.
5. **Os pedidos sob demanda ligados fecham junto**, pelo mesmo `close_linked` do fecho: vencidos
   pelo relógio, `expired`; os demais, pelo status da execução.
6. **Não se reprocessa.** A execução presa não é completada; a rotina seguinte abre uma nova.

## Consequências

- Uma execução presa com resultados passa a poder ser `latest`, se for a fechada mais recente do
  ativo. É verdade sobre o que foi gravado — `partial` diz que faltou parte —, e dura até a próxima
  execução do mesmo ativo fechar, na mesma rotina.
- "Presa" continua sendo por relógio: uma execução legítima que passe de seis horas seria fechada
  com o que tiver gravado. O prazo é configuração.
- O `acks_late`, o `reject_on_worker_lost` e a persistência do Redis ficam fora: reduzem o problema
  sem eliminá-lo, e trazem o laço da tarefa que derruba o `worker` por falta de memória.
- O V-06 do M1.5 continua verdadeiro — sem fecho, a linha fica `running` —, mas só até a varredura.
- A spec do M1.5 é histórica e não é reescrita.

Origem: [spec M1.5c — Execução presa](../specs/M1.5c-execucao-presa.md).
