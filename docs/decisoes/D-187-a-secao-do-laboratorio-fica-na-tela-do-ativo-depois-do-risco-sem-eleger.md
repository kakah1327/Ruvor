# D-187 — A seção do laboratório fica na tela do ativo, logo depois do risco, para todos, pela rota `/lab`; mostra a grade modelo × ano e o veredito da década sem eleger nem ordenar, e diz por que o veredito pode diferir do da seção de risco

**Status:** aceita · 2026-10-03 · frente `marco1`, com a spec do
[M2.4](../specs/M2.4-regime-de-laboratorio.md) aprovada pelo dono (a escolha 2 dele: na tela do ativo,
para todos)

## Contexto

O laboratório valida o risco do mesmo ativo; a Etapa 6 do TCC termina num ranking, e a plataforma não
elege modelo ([D-65](D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md)).

## Decisão

1. **O lugar e o público**: a seção entra na tela do ativo logo depois da seção de risco, antes dos
   Fundamentos (e do retorno do M5.1, quando ele mesclar), para todos, sem conta, nas duas leituras
   ([D-151](D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md),
   [D-152](D-152-o-nivel-de-leitura-e-escolha-do-visitante.md)).
2. **A rota própria** `GET /api/v1/assets/{ticker}/lab` ([D-86](D-86-convencoes-da-api-http.md)), lida
   também pela chave pessoal, com o custo de um pedido a mais por carga contra a taxa do anônimo
   ([D-109](D-109-toda-rota-da-api-tem-taxa.md)). A `web` não importa o motor: a rota lê os modelos e o
   módulo puro da década.
3. **A diferença honesta**: o texto que diz por que o veredito do laboratório pode diferir do da seção de
   risco é obrigatório nas duas leituras.
4. **`MODEL_ORDER` sempre**, sem ranking, sem destaque, sem ordenar por violações, e o vocabulário de
   ranking ("pior", "vencedor", "campeão"…) recusado nas frases.

## Consequências

- O "ranking" da Etapa 6 não existe na plataforma; o TCC, se quiser um, o faz fora dela.
- A tela pede o `/lab` na carga, fora do `data-ready`, e o relê por no máximo 2 minutos depois do fim do
  acompanhamento do risco, enquanto o experimento estiver devido.
