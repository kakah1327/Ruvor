# Ruvor — base de identidade

## Para quem implementa

Comece por [IMPLEMENTER-START-HERE.md](IMPLEMENTER-START-HERE.md). Os exemplos em `examples/` são telas funcionais estáticas que demonstram o uso dos tokens, não artes soltas.

## Assinatura

- `ruvor-logo.svg`: uso padrão sobre fundos claros (`#F7F6F2`).
- `ruvor-logo-reverse.svg`: uso sobre grafite (`#292A2E`).
- `ruvor-mark.svg` e `ruvor-mark-reverse.svg`: ícone para app, favicon e áreas compactas.

O símbolo é uma matriz de sinais analíticos. Deve ser usado sempre em uma única cor, sem gradiente, sombra ou semáforo aplicado aos pontos.

## Paleta

| Token | Cor | Uso |
|---|---|---|
| `--ruvor-ink` | `#292A2E` | Marca, tipografia e estrutura. |
| `--ruvor-paper` | `#F7F6F2` | Fundo principal e versão reversa da marca. |
| `--ruvor-surface` | `#E9E7E2` | Cards e superfícies secundárias. |
| `--ruvor-border` | `#C8C4BC` | Divisórias e campos. |
| `--ruvor-decision` | `#8F3B4B` | Decisão, limite e foco de ação. |
| `--ruvor-review` | `#B79754` | Revisão e atenção. |
| `--ruvor-evidence` | `#54727B` | Evidência, séries e comparação. |
| `--ruvor-validated` | `#587060` | Validação e condição preservada. |
| `--ruvor-critical` | `#B4524C` | Exceção crítica; não substituir pelo vinho de decisão. |

## Regras rápidas

- Espaço livre: ao menos a largura de um ponto grande do símbolo em todos os lados.
- Tamanho mínimo digital: 24 px para o símbolo; 120 px para assinatura completa.
- A cor precisa de texto ou ícone de apoio em estados críticos; nunca depende só do tom.
