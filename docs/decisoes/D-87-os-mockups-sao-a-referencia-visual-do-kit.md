# D-87 — Os mockups são a referência visual; tokens e componentes derivam deles, e o texto das tags é escurecido o mínimo para 4,5:1

**Status:** aceita · 2026-09-28 · substitui a hierarquia que o `README` do kit declarava
("`tokens.css` vence os mockups")

## Contexto

O kit de marca tinha três referências que divergiam entre si. O `README` de `brand/ruvor/`
dizia que `tokens.css` vencia os mockups; os quatro mockups de `brand/ruvor/mockups/` usavam uma
folha própria, `foundation.css`, que não importava os tokens e divergia deles — outra fonte, outro
papel, outra borda, outros raios e cerca de uma dezena de cores literais nos componentes —; e
`implementation.css` era uma terceira folha de componentes, sem consumidor no frontend. A
direção visual que o dono da frente aprovou é a dos mockups.

Medido sobre os valores dos mockups ([spec do M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md#rf-04)),
o texto das tags passa de 4,5:1 em três semânticas e fica abaixo em uma: `review`, `#80672C`
sobre `#F1EAD9`, **4,497:1**.

## Decisão

1. **Os mockups são a referência visual.** A hierarquia do kit passa a ser: `mockups/` →
   `tokens.css`/`tokens.json` e `components.css`, derivados deles → `examples/` → `estudos/`.
2. **Os tokens do tema claro refletem `foundation.css`**, token a token, pela tabela de
   correspondência do [plano do M1.6a](../planos/M1.6a-fundacao-da-aplicacao.md#o-kit) — cor de
   base, cor semântica com os tons `-soft` e `-text`, cada cor literal de componente, as duas
   pilhas de fonte, os raios, as duas sombras e a escala tipográfica. Os nomes antigos que o
   frontend consome (`--ruvor-text`, `--ruvor-bg`, `--ruvor-panel`) continuam, apontando para os
   novos.
3. **Onde o mockup não chega a 4,5:1 no texto, o token `-text` é escurecido o mínimo** — um passo
   de 0,5 ponto de L em HSL, matiz e saturação mantidos —; o `-soft` e a cor da marca não mudam.
   Hoje, só `review-text`: `#7E652B`, 4,63:1. O que os mockups não têm — o tema escuro
   ([D-88](D-88-o-kit-tem-dois-temas-pelos-mesmos-tokens.md)), os estados de interação, a tag e o
   sinal de `decision` — nasce no plano e é aprovado na vitrine.
4. **`components.css` é a folha de componentes do produto**, sem cor literal e sem tamanho de
   fonte literal, e não estiliza `html`, `body` nem títulos soltos. `implementation.css` sai;
   `foundation.css` fica como folha dos mockups, histórico da direção visual.

## Consequências

- Um teste compara os tokens do claro com `foundation.css` (V-01), e `review-text` é a única
  exceção por valor; outro mede o contraste de cada par texto × fundo da folha (V-04).
- Os estudos de `brand/ruvor/examples/` perderam o estilo com a saída de `implementation.css`;
  o `README` de `examples/` diz isso.
- A vitrine `docs/mockups/M1.6a/kit.html` mostra o texto da tag `review` do mockup ao lado do
  escurecido, e foi aprovada pelo dono da frente em 2026-09-28.
- Tela nova do produto parte dos mockups e da folha; divergência entre os dois é defeito da folha,
  não licença da tela.
