# D-190 — A validação do retorno: `r2_os`, acerto de direção ao lado da parcela de alta, Diebold-Mariano no veredito; Clark-West e Pesaran-Timmermann gravados e fora dele; "não bate" é resultado normal; nenhum modelo é eleito

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do [M5.1](../specs/M5.1-retorno.md)
aprovada pelo dono (a resposta 1 do portão: o Diebold-Mariano no veredito, como proposto)

## Contexto

O veredito de adequação do risco mora no backend, e o nulo é distinto do falso
([D-64](D-64-veredito-de-adequacao-e-kupiec-e-christoffersen.md)); a plataforma não elege modelo
([D-65](D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md)). Com a referência zero aninhada nos
dois modelos, os testes de comparação de previsões não respondem à mesma pergunta.

## Decisão

1. **O que se mede**: o erro relativo à referência, `r2_os = 1 − EQM do modelo / EQM de supor zero`; o
   acerto de direção, contado só nos dias com retorno e previsão diferentes de zero, sempre ao lado da
   parcela de dias de alta.
2. **O veredito é o Diebold-Mariano**, com perda quadrática, unilateral, com a variância de longo prazo de
   Newey-West (núcleo de Bartlett, defasagem ⌊4·(n/100)^(2/9)⌋, série centrada, divisor *n*), a 5%, sobre o
   *p* quantizado a 10 casas — decidido no backend, nunca no motor.
3. **O Clark-West e o Pesaran-Timmermann são gravados e ficam fora do veredito**; aparecem na leitura
   avançada.
4. **"Não bate" é resultado normal**; o resultado com `error` é "não deu para calcular", nunca "não bate".
5. **Nenhum modelo é eleito**: a tela segue a ordem de `model_name`, sem mérito.

**Por que o DM, e não o Clark-West**: a pergunta que a tela responde é "a previsão, como foi feita, errou
menos que o zero?" — a do DM; o CW pergunta se o modelo tem informação na população, descontando o ruído
de estimação. Com a referência aninhada, o DM é conservador (Clark e McCracken, 2001) — tende a "não
bate" —, e o CW tem o tamanho certo. **O erro caro aqui é o "bate" falso**, que parece dica; o "não bate"
falso custa pouco.

## Consequências

- Nos dados da spec, o CW dava "bate" em 3 dos 12 pares (ativo, modelo), e o DM em nenhum.
- O veredito é comparado sobre o mesmo `Decimal` que vai à coluna: `0.04999999999996` grava
  `0.0500000000` e sai "não bate".
