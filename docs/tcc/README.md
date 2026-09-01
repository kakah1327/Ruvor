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
| `TCC_II_VaR_ML_v3_cap1.docx` | **Fonte canônica** do texto acadêmico |
| `TCC_II_VaR_ML_v3.md` | Conversão em Markdown, para leitura e diff. **Gerada** — não editar |

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

## Divergências conhecidas entre o texto e o código

O TCC descreve decisões que mudaram desde a redação (Flask, Jinja2, `statsmodels.QuantReg`,
ausência de banco). O levantamento completo está em
[`docs/prototipo/07-backlog-specs.md`](../prototipo/07-backlog-specs.md), seção de
divergências.

## Pendências do trabalho acadêmico

- **Etapa 6** (ranking comparativo dos 9 modelos nos 4 ativos) não executada
- **Capítulo 5** (considerações finais) em branco
- Correção da semente aleatória e refação da Tabela 1 — pré-requisito da Etapa 6
- Renomeação de "VaR Lab" para "Ruvor" no texto
