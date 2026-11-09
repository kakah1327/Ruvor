# TCC — material acadêmico

> ## ⚠️ ESCOPO ACADÊMICO, NÃO ESPECIFICAÇÃO DE PRODUTO
>
> Esta pasta contém o Trabalho de Conclusão de Curso apresentado à Faculdade Impacta
> Tecnologia. É **pesquisa acadêmica**, com referencial teórico, justificativa e normas
> ABNT.
>
> **Não é especificação da plataforma** e não deve ser usado como referência de arquitetura,
> escopo de produto ou padrão de documentação. Para isso, ver
> [`docs/PRODUTO.md`](../PRODUTO.md) e [`docs/ARQUITETURA.md`](../ARQUITETURA.md).

## Arquivos

| Arquivo | Papel |
|---|---|
| `TCC_II_VaR_ML_v4.docx` e `.pdf` | **A versão entregue** do TCC II (2026-10-05), gerada por [`tools/tcc/`](../../tools/tcc/README.md) |
| `TCC_II_VaR_ML_v3_cap1.docx` | A base do v4: o `montar.py` aplica o texto novo sobre ela |
| `TCC_II_VaR_ML_v3.md` | Conversão em Markdown do v3, para leitura e diff. **Gerada** — não editar |

Para regenerar o Markdown após alterar o `.docx`:

```bash
python tools/docx/docx2md.py docs/tcc/TCC_II_VaR_ML_v3_cap1.docx docs/tcc/TCC_II_VaR_ML_v3.md
```

## Relação com a plataforma

O TCC e o Ruvor compartilham o **motor numérico** (`engine/`) e divergem no resto.

- O TCC valida cientificamente os modelos de risco e publica o experimento comparativo.
- O Ruvor é a plataforma construída sobre esse motor.

O modelo núcleo-aberto sustenta as duas afirmações ao mesmo tempo — ver
[`docs/ARQUITETURA.md`](../ARQUITETURA.md), seção de estrutura do repositório.

## Divergências entre o texto e o código

As do v3 (Flask, Jinja2, `statsmodels.QuantReg`, ausência de banco), levantadas em
[`docs/prototipo/07-backlog-specs.md`](../prototipo/07-backlog-specs.md), foram corrigidas no v4. O v4 cita as telas de
carteira como trabalho futuro; elas entraram depois, no M2.2b.

## Pendências do trabalho acadêmico

Nenhuma: a Etapa 6, o Capítulo 5, a semente e a Tabela 1, e o nome Ruvor estão no v4
([ROADMAP](../ROADMAP.md#trilha-paralela--tcc)).
