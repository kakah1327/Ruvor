# D-150 — O fecho só escreve sobre execução em `running`, e o que chega depois é descartado; estende a D-72 e restringe a D-70

**Status:** aceita · 2026-09-29 · estende a [D-72](D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md); restringe a [D-70](D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md)

## Contexto

A D-72 fez do `close_run` o único `update` sobre `gold`, chamado só pelo fecho do `chord`. Com a
varredura da [D-149](D-149-a-execucao-presa-e-fechada-pela-regra-do-fecho.md), dois caminhos passam
a fechar a mesma linha, e a execução "presa" pode estar só lenta: o fecho verdadeiro chega depois da
varredura, e as tarefas por modelo que ainda rodam gravam resultados numa execução já fechada. Hoje
`close_run` sobrescreve sempre, sem conferir o estado, e a tarefa por modelo não o confere.

E há um caminho que nasce preso sem falha nenhuma de `worker`: a abertura enfileira o `chord` no
`on_commit`; se o broker recusar nesse instante, a `risk_run` já está gravada `running` e nenhuma
tarefa sai.

## Decisão

1. **`close_run` só escreve sobre a linha ainda `running`.** A escrita é condicional ao estado
   gravado, e devolve se escreveu. Quem chega depois — o fecho atrasado, ou a varredura sobre uma
   execução que o fecho acabou de fechar — não muda `status` nem `finished_at`, e não fecha pedido
   nenhum: o primeiro que fechou já fechou os ligados.
2. **Continua sendo o único `update` sobre `gold`**: a varredura o chama no mesmo molde do fecho — a
   trava por ativo, dentro de uma transação, e a linha relida depois da trava
   ([D-92](D-92-nunca-duas-execucoes-do-mesmo-ativo-ao-mesmo-tempo.md)).
3. **A tarefa por (ativo, modelo) não grava em execução fechada.** A escrita dos dois resultados
   — e a do par de erro — acontece sob a trava por ativo, depois de reler o estado; fechada, a
   tarefa descarta o que calculou, registra no log e termina. Continua nunca levantando
   ([D-70](D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md)). Sem isso, o número de resultados
   gravados divergiria do `status` que o fecho escreveu, e a D-16 impediria consertar. **É a trava dos
   dois lados que protege a contagem**: o filtro de estado do item 1 garante um só escritor do
   `status`, não que a contagem ainda valha no instante do `UPDATE`.
4. **A abertura que não consegue enfileirar fecha a própria execução** pela regra — zero
   resultados, `failed` —, com os pedidos ligados (`failed`, "a execução falhou"), e levanta em
   seguida. **Restringe a D-70**, que dava como modo de falha da abertura "o log e a ausência de
   execução": aqui a execução existe, e fecha `failed`.

## Consequências

- A tarefa por modelo passa a disputar a trava por ativo com a abertura e o fecho. A escrita é de
  dois registros; a espera é curta.
- A execução `failed` sem resultados do item 4 vira `latest` do ativo: a tela mostra o estado de
  execução falha até a próxima rotina fechar uma execução nova, em vez da execução boa anterior.
- Um cálculo concluído depois da varredura é perdido — declarado: o preço é recalcular na rotina
  seguinte.
- A D-16 continua valendo para o que protege: nenhum `risk_result` muda, e nenhum caminho faz
  `delete`.

Origem: [spec M1.5c — Execução presa](../specs/M1.5c-execucao-presa.md).
