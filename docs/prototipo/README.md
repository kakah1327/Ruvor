# Protótipo VaR Lab — documentação de referência histórica

> ## ⚠️ NÃO É REFERÊNCIA
>
> Estes documentos descrevem o **protótipo VaR Lab**, construído em cerca de 3 horas como
> teste e **substituído** pela plataforma Ruvor.
>
> **Não use como modelo** de como escrever spec, de como estruturar código, nem de como o
> sistema deve ser. O padrão atual está em [`docs/PROCESSO.md`](../PROCESSO.md),
> [`docs/ARQUITETURA.md`](../ARQUITETURA.md) e [`docs/PRODUTO.md`](../PRODUTO.md).
>
> **Por que continua aqui:** é a linha de base da revisão (decisão
> [D-10](../decisoes/D-10-spec-do-existente-e-linha-de-base.md)). Cada spec nova é cruzada
> contra estes documentos para decidir o que se aproveita, o que se melhora e o que se
> descarta.

## O que estes documentos são

Especificação retroativa e honesta do protótipo: o que ele faz, o que não faz, e onde o
texto do TCC diverge do código.

| Documento | Conteúdo |
|---|---|
| [01 — Visão geral e requisitos](01-visao-geral.md) | Escopo, requisitos rastreáveis, status de cada um |
| [02 — Arquitetura](02-arquitetura.md) | Camadas, contratos, registries do protótipo |
| [03 — Modelos de VaR](03-modelos.md) | Os 9 modelos, fórmulas e parâmetros |
| [04 — Backtesting](04-backtesting.md) | Os 4 testes estatísticos |
| [05 — Dados e protocolo](05-dados-e-protocolo.md) | Fonte, limpeza, janelas, reprodutibilidade |
| [06 — API e frontend](06-api.md) | Contrato JSON atual |
| [07 — Backlog](07-backlog-specs.md) | Lacunas do protótipo e divergências com o TCC |

## O que tem valor real aqui

Nem tudo no protótipo é descartável. O que é caro de refazer e foi validado:

- **Os 9 modelos de VaR** (03) — inclusive a correção da instabilidade numérica do EGARCH
- **Os 4 testes de backtesting** (04) — validados contra séries sintéticas de violação conhecida
- **A verificação cruzada com o pacote rugarch em R** (05)

Estes são a matéria-prima do `engine/` da plataforma nova. O resto — API, frontend,
persistência — é reconstruído.

## O que aqui está desatualizado por definição

- O nome: o produto é **Ruvor**, não VaR Lab (decisão [D-25](../decisoes/D-25-rebrand-ruvor.md))
- A pilha: Flask e SQLite foram substituídos por Django e PostgreSQL
- A estrutura de pastas: descrita em [`docs/ARQUITETURA.md`](../ARQUITETURA.md)
