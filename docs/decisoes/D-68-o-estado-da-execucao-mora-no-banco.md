# D-68 — O estado da execução mora no banco, não no Redis

**Status:** aceita · 2026-09-25

## Contexto

Com a transação por (ativo, modelo) da [D-67](D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md),
uma `risk_run` pode existir com parte dos resultados. Quem a lê precisa saber se ela ainda
roda, se terminou inteira, ou se terminou com falhas. A ARQUITETURA prevê um **canal de
progresso no Redis** ("modelo 4 de 9 terminou") — e o Redis é volátil: reiniciá-lo apaga o
que se escreveu lá.

## Decisão

**O estado da execução é coluna de `gold.risk_run`**, no molde do `bronze.collection_run` do
M1.1:

```python
class Status(models.TextChoices):
    RUNNING = "running"
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"
```

Mais `requested_models`, a lista dos modelos pedidos, na ordem do pedido. É contra ela que o
estado é decidido, e é ela que torna `--model garch_1_1` uma execução legítima em vez de uma
execução incompleta. **Nenhuma das duas colunas tem `default`**: com `default=running`, o
caminho que esquecesse de escrever o estado deixaria a linha `running` para sempre, em
silêncio.

O canal de progresso no Redis **não é construído**. A tela do M1.6 consulta o banco
periodicamente, como a ARQUITETURA já decidiu.

## Consequências

- `partial` é o acréscimo em relação ao `collection_run`, e existe porque o modo A produz um
  estado que a coleta não tem: **houve resultado, e nem todos**.
- O caminho síncrono também escreve o estado — sabe o desfecho antes de escrever e cria a
  linha já com ele, sem `update`. Os dois caminhos gravam o mesmo conteúdo, `status`
  incluído.
- Tirar o `default` **não basta para o `status`**, e isso foi medido: `CharField` sem padrão
  grava string vazia, sem erro. Quem guarda o estado é teste. O `requested_models`
  (`JSONField`) estoura no `NOT NULL`.
- As oito execuções do M1.4 receberam o estado pela migration `0002`, **derivado do dado**
  — os `model_name` distintos de cada uma e a regra do fecho —, não carimbado: saíram `ok`,
  com os nove.
- A auditoria lê o estado onde lê o resto do manifesto. O "modelo 4 de 9" que o canal de
  progresso daria se lê contando as linhas já gravadas da execução — o que falta é só o
  modelo que está rodando agora, e nada hoje precisa dele.

Origem: [spec M1.5 — Execução assíncrona](../specs/M1.5-execucao-assincrona.md) (RF-05, RF-08,
"O estado da `risk_run`").
