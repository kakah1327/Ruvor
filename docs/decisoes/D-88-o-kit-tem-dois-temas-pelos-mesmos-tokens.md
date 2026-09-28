# D-88 — O kit tem dois temas, pelos mesmos tokens de cor

**Status:** aceita · 2026-09-28

## Contexto

O kit era só claro, e o [ESTADO](../ESTADO.md) carregava "tema claro vs escuro" como decisão de
produto pendente — o próprio `README` do kit declarava a falta. Os mockups não têm tema escuro:
a barra superior é escura, e o resto é papel claro.

## Decisão

1. **Dois temas, claro e escuro, pelos mesmos nomes de token.** O escuro não cria token novo nem
   classe nova: redefine o valor dos tokens de cor.
2. **Como se escolhe:** `:root` e `[data-theme="light"]` são o claro; `[data-theme="dark"]` é o
   escuro; sem atributo, `prefers-color-scheme: dark` escolhe o escuro. As duas cópias do escuro —
   a do atributo e a da `@media` — têm exatamente as mesmas declarações.
3. **Só cor muda.** Tipografia, espaço, raio e sombra são os mesmos nos dois temas.
4. **O contraste vale inteiro no escuro** — 4,5:1 para texto, 3:1 para sinal e anel de foco —, e
   as cinco semânticas mantêm o significado.
5. **Os valores do escuro não têm fonte nos mockups**: nascem no
   [plano do M1.6a](../planos/M1.6a-fundacao-da-aplicacao.md#o-kit) e são aprovados na vitrine. A
   barra superior continua distinta do fundo — no escuro, por uma borda inferior de 1 px
   (`topbar-edge`), que no claro some.

## Consequências

- Testes conferem que o claro e o escuro têm o mesmo conjunto de nomes, que as duas cópias do
  escuro são iguais, que `tokens.json` tem os mesmos tokens nos dois temas, e o contraste de cada
  par nos dois temas e nas duas cópias ([spec do M1.6a](../specs/M1.6a-fundacao-da-aplicacao.md#rf-05)).
- A tela de verificação do frontend fica escura num sistema com preferência escura — efeito
  esperado, não regressão.
- A primeira versão do `decision` escuro (`#D07E8E`) ficava abaixo de 4,5:1 como texto em três
  fundos; a revisão da vitrine a trocou por `#D38595`, e o `decision-hover` escuro por `#E0A0AC`.
- As telas do M1.6b nascem nos dois temas: o mockup de cada uma mostra os dois.
