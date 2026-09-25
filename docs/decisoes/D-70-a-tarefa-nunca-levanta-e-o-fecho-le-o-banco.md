# D-70 — A tarefa nunca levanta, e o fecho lê o banco

**Status:** aceita · 2026-09-25

## Contexto

As nove tarefas de um ativo formam um `chord` do Celery — grupo mais retorno —, e o retorno é
o fecho, que escreve o estado da execução ([D-68](D-68-o-estado-da-execucao-mora-no-banco.md)).
No Celery, **se uma tarefa do grupo levanta, o corpo do `chord` não roda** — vira
`ChordError`. A tarefa que levantasse para sinalizar falha impediria o fecho de escrever
`failed`, e o estado viraria o "preso em `running`": o modo de falha raro passaria a ser o
comportamento normal do mecanismo.

E "gravou sem erro" tem duas leituras: no M1.4, **modelo que falha grava linha**, com `error`
preenchido e números nulos.

## Decisão

**A tarefa por (ativo, modelo) nunca levanta.** Qualquer exceção depois de achar a execução
— a série que mudou, o `run_experiment` que estoura, a escrita que falha — vira o **par de
erro** do modelo pelo `write_failed`, uma linha por nível, números nulos e `error`
preenchido, e a tarefa termina normalmente. Se nem o erro puder ser gravado, loga e devolve.

**O fecho lê o banco**, não os resultados das tarefas. A regra é literal, relativa ao que
foi **pedido**:

```
esperado = len(requested_models) * len(config.ALPHAS)
gravados = risk_result da execucao
com_erro = gravados com error != ""

failed   se gravados == 0  ou  com_erro == gravados
ok       se gravados == esperado  e  com_erro == 0
partial  nos demais casos
```

Uma função pura, `status_for`, usada pelo fecho assíncrono, pelo caminho síncrono e — por
cópia, porque migration não importa código que importa o motor — pelo `backfill` da
migration `0002`. Um teste confere as duas contra a mesma tabela de casos.

## Consequências

- O "preso em `running`" fica restrito ao que ele deve ser: o `worker` morrer, o Redis
  reiniciar — falha de infraestrutura, não de modelo. **O que fazer com a linha presa** —
  limpar por idade, reprocessar, deixar para operação — segue pergunta aberta: não há dado de
  produção para decidir.
- A distinção "falhou × reprovado" do M1.4 se mantém: modelo que falha é linha com `error`,
  não ausência de linha. O `status` final sai igual nas duas escolhas, então só o conteúdo
  das linhas a denuncia — e é o conteúdo que o teste confere.
- A abertura (`abrir_execucao`) é a exceção, e **pode** levantar: antes dela não há linha
  onde gravar `error`. O modo de falha dela é o log e a ausência de execução.
- A spec escreveu o esperado como `len(modelos_pedidos) * 2`; o código usa
  `len(config.ALPHAS)`, que é o mesmo número hoje e não envelhece se os níveis mudarem. A
  migration `0002` mantém o `* 2`, porque descreve as execuções do M1.4, que tinham dois.

Origem: [spec M1.5 — Execução assíncrona](../specs/M1.5-execucao-assincrona.md) (RF-05, RF-06).
