# D-192 — A tela mostra a validação e, junto dela, a previsão do próximo pregão de cada modelo, nunca sozinha; o aviso é obrigatório; sem comercialização, o parecer da CVM não segura o M5.1 — estende a D-160

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do [M5.1](../specs/M5.1-retorno.md)
aprovada pelo dono (as respostas 2 e 3 do portão: a previsão mostrada, com destaque menor que o veredito;
o M5.1 segue a D-160). A D-160 é da `identidade`: a PR da spec passou pelo dono dela.

## Contexto

Um número de retorno ao lado de uma ação é o mais perto da linha de recomendação que a plataforma pode
mostrar. A spec propunha não mostrar a previsão: nos dados dela, nenhum modelo batia o zero. O dono
decidiu mostrá-la no portão (2026-10-03). A [D-160](D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)
diz que, sem comercialização, o parecer da CVM não segura a carteira.

## Decisão

1. **A seção** fica na tela do ativo, depois do risco e do laboratório, antes dos Fundamentos, nas duas
   leituras ([D-151](D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md),
   [D-152](D-152-o-nivel-de-leitura-e-escolha-do-visitante.md)).
2. **A previsão do próximo pregão** de cada modelo sai só na linha dele, depois do veredito e do histórico
   de acerto, ao lado da referência zero, com a data, **sem seta nem cor de direção**, com destaque menor
   que o veredito; ausente no ativo inativo e com a data passada. No modelo que não bate, a nota "não é
   mais informativa que supor retorno zero". O veredito que bate é a tag `--evidence`, nunca a
   `--validated`: nenhum sinal de "bom" ao lado de um número de previsão (portão do mockup).
3. **O aviso** `retorno.aviso`, sempre aberto, nas duas leituras, de R3 a R8, que diz que a previsão é "um
   número estatístico, não uma expectativa nem uma indicação" e que nada ali é recomendação.
4. **A lista ampliada do vocabulário** nas `retorno.*`, nas duas leituras, pela forma (b) da varredura (as
   saídas, pelos exemplos), com as formas de futuro proibidas; `retorno.aviso` é a única isenta.
5. **O M5.1 segue a D-160**: sem comercialização, o parecer da CVM não o segura. **O parecer, quando vier
   antes de comercializar, precisa cobrir o M5.1 nomeadamente.**

## Consequências

- A lista ampliada não cabe na forma (a), sobre o texto-fonte: os textos dos fundamentos dizem "lucro" e
  "venda".
- O que acompanha o número — o veredito, o histórico, a nota, o aviso e o destaque menor — é a resposta do
  desenho ao risco de o número parecer dica.
