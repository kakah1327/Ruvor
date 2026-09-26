# D-84 — Frentes simultâneas, cada uma com a sua cerca de pastas

**Status:** aceita · 2026-09-26 · restringe a [D-23](D-23-trabalho-dividido-por-bloco.md)

## Contexto

A [D-23](D-23-trabalho-dividido-por-bloco.md) dividiu o trabalho por bloco e imaginou quatro
frentes **dentro do Marco 1**. Até o M1.5 o desenvolvimento foi de uma pessoa por vez.

Em 2026-09-26 entra o Kauã, e um terceiro dev está previsto. Do Marco 1 restam o M1.5b e o M1.6, que ficam com quem já
os conduz — o M1.6 depende do M1.5b e as primeiras telas e a API decidem o vocabulário do
produto. Os outros blocos que podem começar sem esperar ninguém:

| Bloco | Livre agora? |
|---|---|
| M2.1 — Identidade e acesso | sim: `apps/accounts`, que nenhum bloco em curso toca |
| M2.2 — Carteira | não: depende do M2.1, do parecer da CVM e da escolha de caminho |
| M2.3 — Camada explicativa | não: precisa das telas do M1.6 |
| M2.4 — Laboratório | não: disputa `engine/` e `apps/risk/` com o M1.5b |
| M3.1 — Fundamentos | sim: fonte, app e tabelas novas |

## Decisão

**Frentes simultâneas, cada uma dona de um conjunto de pastas:**

| Frente | Blocos | Estado |
|---|---|---|
| `marco1` | M1.5b, M1.6 | ativa |
| `fundamentos` | M3.1 | ativa, com o Kauã |
| `identidade` | M2.1 | definida, espera dono |

Com dois devs, a segunda frente é a `fundamentos`, e não a `identidade`: é a que não espera
nada da `marco1`. A `identidade` precisa das convenções da API e do casco do frontend, que o
M1.6 ainda vai produzir.

A cerca de cada frente, os arquivos comuns e os contratos entre elas moram em
[`FRENTES.md`](../FRENTES.md), que é o quadro vivo desta decisão.

**O M2.1 começa antes do parecer da CVM.** A [PRODUTO](../PRODUTO.md#fronteira-regulatória-cvm)
pede o parecer "antes do Marco 2" por causa da carteira; autenticação e papéis não informam
nem recomendam investimento. O M2.2 segue esperando o parecer.

**O M3.1 começa antes de o Marco 2 fechar.** A ordem dos marcos é de entrega ao usuário, não
de construção; o que impede um bloco é dependência, e o M3.1 não tem.

**Numeração de decisão por faixa**, para duas frentes nunca criarem o mesmo número em ramos
diferentes. As faixas estão em `FRENTES.md`.

## Consequências

- Uma frente não escreve na cerca de outra. Quando precisa, combina na spec e a outra frente
  revisa a PR.
- Os arquivos comuns (configuração, compose, CI, índices) aceitam só alteração aditiva e
  mínima, declarada no inventário da spec.
- Decisões deixam de ser numeradas em ordem cronológica. O índice
  [`README.md`](README.md) é por tema, então isso não atrapalha a leitura.
- O M2.4 fica livre para uma frente quando o M1.5b fechar.
