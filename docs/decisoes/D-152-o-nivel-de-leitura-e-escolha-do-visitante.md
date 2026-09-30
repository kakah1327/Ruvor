# D-152 — O nível de leitura é escolha do visitante, global, lembrada no navegador; o padrão é iniciante

**Status:** aceita · 2026-09-29 · com a aprovação da [spec do M2.3](../specs/M2.3-camada-explicativa.md)

## Contexto

A [PRODUTO §2](../PRODUTO.md#2-público-e-postura) desenha duas leituras do mesmo dado, iniciante e avançada, "não dois
produtos". A tela do ativo é pública, sem conta, e a única preferência lembrada hoje é o tema, em `localStorage`
(`frontend/src/theme.ts`).

## Decisão

1. **O visitante escolhe o nível** num alternador global no casco, ao lado do tema. O padrão é **iniciante**.
2. **A escolha é lembrada no navegador**, na chave `ruvor-reading` (`beginner` ou `advanced`), no molde do tema;
   não exige conta.
3. **O nível muda o texto e o que nasce aberto — nunca o número nem o dado.** Cada número mostra uma frase só, a do
   nível: a avançada substitui a iniciante. Na leitura iniciante, os detalhes técnicos de uma lista fechada nascem
   recolhidos; **recolher nunca remove** — tudo se abre com um controle.
4. Vale para as telas futuras: número de análise novo nasce com as duas frases.

## Consequências

- O nível não segue a pessoa entre navegadores; quando houver conta, um bloco futuro decide se a conta sobrepõe o
  navegador (campo em `core.user`, da `identidade`).
- A lista fechada do que tem duas frases e do que nasce recolhido é fixada por teste.

Origem: [spec M2.3 — Camada explicativa](../specs/M2.3-camada-explicativa.md).
