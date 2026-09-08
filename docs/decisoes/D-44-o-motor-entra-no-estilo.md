# D-44 — O motor entra no estilo, e como isso se prova

**Status:** aceita · 2026-09-06

## Contexto

A [D-21](D-21-motor-ml-congelado-ate-etapa-6.md) diz que o motor **não é alterado** antes da
Etapa 6. Estilo mexeria nele: medido com `ruff 0.16.6`, a formatação reescreve **25 dos 33**
arquivos de `engine/src`, e o lint acusa **24** violações.

Deixar o motor de fora significaria a parte com mais código do repositório sem guarda de
estilo por tempo indeterminado — a Etapa 6 não tem data.

## Decisão

**O motor entra no estilo, formatação e lint**, com provas separadas porque as operações são
diferentes.

**Formatação — prova completa, por árvore sintática.** Comparar `ast.dump()` de cada arquivo
antes e depois prova, arquivo a arquivo, que nada semântico mudou. Cobre os nove modelos, sem
amostragem. Executado: 58 arquivos `.py`, zero divergência.

**Lint — prova por enumeração.** As 24 violações do motor são conhecidas uma a uma:

| Regra | Quantas | O que muda |
|---|---|---|
| `UP006` | 8 | `typing.Type` → `type` |
| `UP037` | 8 | remove aspas de anotação |
| `I001` | 2 | ordena imports, nos dois blocos dentro de função |
| `UP035` | 2 | import depreciado |
| `RUF012` | 1 | exige `ClassVar` |
| `RUF100` | 2 | `# noqa` que não suprime nada |
| `UP042` | 1 | **não é aplicada** — ver abaixo |

**Vinte e uma das 24 são de anotação de tipo ou de ordem de import, e nenhuma toca expressão
numérica.**

## Consequências

- **A D-21 protege comportamento numérico, e é isso que continua protegido.** A linha de base
  do F2a — 12 combinações, diferença zero — segue como reforço, sobre a prova por árvore
  sintática.
- **`UP042` é ignorada em `engine/pyproject.toml`, com o motivo no próprio arquivo.** Ela
  trocaria `class ModelCategory(str, Enum)` por `StrEnum`, e **a troca não é equivalente**:
  `str()` e f-string se comportam de forma diferente entre as duas no 3.12, e `ModelCategory` é
  comparado e formatado em todo o motor. Reavaliar depois da Etapa 6.
- **As duas `RUF100` não podem ser corrigidas automaticamente.** O `--fix` apagaria
  `# noqa: BLE001 — isola falha de 1 modelo do restante`, e com ele a intenção escrita. A
  correção é converter em comentário comum.
- **Risco residual, declarado:** a linha de base cobre **seis dos nove** modelos —
  `lstm`, `gru` e `garchnet` não têm número comparado contra nada. Medido: `lstm.py` e `gru.py`
  não recebem lint nenhum, só formatação; `garchnet.py` recebe um `UP037`; `_quantile_nn.py`,
  dois. Ampliar a linha de base é trabalho da trilha do TCC, depois da Etapa 6.
- **Essa afirmação depende de `E501` estar fora do piso** ([D-43](D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)).
  Com ele ligado, os três modelos ganham linha longa e a afirmação seria falsa.

## Aprendizado de método, que produziu duas versões erradas desta decisão

**Medir com `ruff --isolated` não é medir o projeto.** O `--isolated` usa a versão-alvo padrão
de Python, não a do `requires-python`. O `UP042` fica calado ali e dispara no projeto real.
**E medir lint antes de formatar infla o número** com violações que a formatação resolve.

Origem: [spec F5 — Integração contínua](../specs/F5-integracao-continua.md).
