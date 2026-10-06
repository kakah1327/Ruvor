# D-195 — O tema escuro é carvão quente: os neutros ganham o matiz do papel do tema claro, e as camadas sobem em degraus nítidos

**Status:** aceita · 2026-10-04 · frente `marco1`, no ramo `marco1/ajustes-de-tela`. A decisão foi do Kauã,
dono do repositório. Ele comparou no navegador três prévias aplicadas na tela rodando: o grafite neutro de
antes, um cinza frio "slate" e o carvão quente. Escolheu o carvão quente. A PR do ramo passa pela revisão
da `marco1`, dona de `brand/`.

## Contexto

O tema claro vem dos mockups da marca ([D-87](D-87-os-mockups-sao-a-referencia-visual-do-kit.md)): papel
quente (`--ruvor-paper` `#F8F7F4`, superfície `#FFFEFA`, borda `#D5D2CC`) e acentos sóbrios (vinho, ocre,
azul-ardósia, sálvia). O tema escuro nasceu no plano do M1.6a e foi aprovado na vitrine (RF-05). Os
neutros dele eram cinzas sem matiz, com fundo, coluna e painel muito próximos (`#1A1B1E`, `#212226`,
`#292A2F`). O dono achou o cinza apagado: a tela virava uma massa só, e sem o calor do papel o escuro não
parecia a mesma marca.

## Decisão

1. **Os neutros do escuro levam um matiz quente leve**: OKLCH com matiz 70 e croma entre 0,004 e 0,010,
   mais baixo nos extremos. É o calor do papel do tema claro, levado ao escuro.
2. **As camadas sobem em degraus nítidos**:

   | Papel | Token | De | Para |
   |---|---|---|---|
   | barra superior | `--ruvor-topbar` | `#0C0D0F` | `#090807` |
   | fundo da tela | `--ruvor-canvas` | `#1A1B1E` | `#110F0D` |
   | coluna | `--ruvor-paper` | `#212226` | `#191714` |
   | painel | `--ruvor-surface` | `#292A2F` | `#24211E` |
   | segunda superfície | `--ruvor-surface-2` | `#323338` | `#2E2B28` |
   | borda | `--ruvor-border` | `#45464B` | `#3F3B37` |
   | texto | `--ruvor-ink` | `#ECEBE7` | `#F0ECE7` |
   | texto secundário | `--ruvor-text-muted` | `#A4A4A9` | `#B5B0AA` |

   Os tokens derivados acompanham a escala: cabeçalho e linhas de tabela, faixas, controles, esqueleto,
   código, barra superior e `--ruvor-on-decision`. São 24 valores ao todo, nas duas cópias do escuro de
   `brand/ruvor/tokens.css` e em `tokens.json`.
3. **Os acentos não mudam** (`decision`, `review`, `evidence`, `validated`, `critical` e as variantes
   deles), **e o tema claro não muda**.

## Consequências

- O contraste segue acima de 4,5:1 nos dois temas e nas duas cópias do escuro. O texto secundário sobre a
  segunda superfície, o par mais apertado, fica em 6,5:1. Os testes do kit conferem o contraste e a
  igualdade entre `tokens.css` e `tokens.json`.
- Os gráficos leem as cores pelos tokens (`Chart.tsx`) e acompanham sem mudança de código.
- Os mockups de `docs/mockups/` ligam `brand/ruvor/tokens.css` e não copiam cor: no tema escuro, passam a
  mostrar a escala nova. O tema claro deles não muda.
