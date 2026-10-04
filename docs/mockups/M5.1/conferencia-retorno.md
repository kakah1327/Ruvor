# M5.1 — Conferência técnica: retorno (T8)

**N = 7** — as chaves `retorno.*` **com frase** (as duas leituras, a lista fechada do RF-20 proposta ao portão):
`retorno.veredito`, `retorno.r2_os`, `retorno.acerto`, `retorno.dm`, `retorno.cw`, `retorno.pt`, `retorno.previsao`.

Só leitura. Para cada chave com frase e cada ramo dela, o que a frase avançada vai afirmar e o `caminho:linha` em que
cada afirmação foi conferida, no código que calcula (RF-20). Os caminhos são relativos à raiz do repositório.
**Afirmação sem `caminho:linha` não vai ao mockup.** Conferido no ramo `marco1/M5.1-retorno`, HEAD `19833d9` (depois da
fase A), em 2026-10-04. Os números de exemplo são os gravados pelo motor `0.5.0` na fase A (`gold.return_run` 1 a 6).

**O formato garante que o `N` só conta chaves com frase**: a tabela abaixo é a única do arquivo com linhas que começam
por `` | ` `` (crase depois da barra), e toda linha dela é de uma das sete chaves. As frases de estado, as da previsão
ausente e o `retorno.aviso` — uma leitura só, fora do `N` — vão na lista de hífens de "As chaves sem a avançada".

## O que vale para todas as linhas

- **A série.** O motor recebe o `adj_close` de `silver.price` na coluna `close` (`backend/apps/risk/provider.py:54`,
  `backend/apps/risk/provider.py:56`), só as linhas com `adj_close` não nulo e maior que zero
  (`backend/apps/risk/compute.py:302`), e tira dela o retorno logarítmico diário
  (`engine/src/engine/data/preprocessing.py:15`, `engine/src/engine/data/preprocessing.py:20`). A janela é a série inteira
  do ativo (`backend/apps/returns/compute.py:210`, `backend/apps/returns/compute.py:211`).
- **Treino e teste.** Os primeiros 252 retornos são o treino inicial; todo o resto é o período de teste
  (`engine/src/engine/returns/runner.py:51`, `engine/src/engine/returns/runner.py:52`; `backend/apps/risk/config.py:11`),
  com o piso de 503 pregões (`backend/apps/risk/config.py:15`, `backend/apps/returns/compute.py:198`). `test_count =
  pregões − 1 − 252` (`backend/apps/returns/compute.py:347`). Nos seis ativos, 2.221 a 2.246 dias de teste.
- **Sem olhar à frente; a reestimação.** O teste é cortado em trechos de 252 pregões (`engine/src/engine/returns/models.py:23`,
  `engine/src/engine/returns/models.py:27`, `engine/src/engine/returns/models.py:28`); os parâmetros do trecho que começa
  na posição `s` são estimados com todos os retornos conhecidos até ali — treino e teste antes de `s`, janela que cresce
  (`engine/src/engine/returns/models.py:49`) — e ficam fixos dentro do trecho
  (`engine/src/engine/returns/models.py:51`). A previsão do dia `t` usa só retornos até `t − 1`
  (`engine/src/engine/returns/models.py:50`).
- **A referência é o zero.** O erro da referência é o próprio retorno (`engine/src/engine/returns/evaluation.py:76`); não
  é modelo do registry, e os dois modelos são exatamente `ar_1` e `historical_mean` (`backend/apps/returns/config.py:17`,
  `backend/apps/returns/compute.py:212`).
- **O nível.** 5%, comparado no backend com o *p* já arredondado a 10 casas, o número que a tabela grava e a API devolve
  (`backend/apps/returns/config.py:12`, `backend/apps/returns/compute.py:259`, `backend/apps/returns/compute.py:293`).

## A tabela

| Chave | Ramo | O que a frase avançada vai afirmar | Conferido em |
|---|---|---|---|
| `retorno.veredito` | nenhum bate | O veredito de cada modelo é o teste de Diebold-Mariano com perda quadrática, **unilateral** (a alternativa é "o modelo erra menos que o zero"), contra a referência de retorno zero, no período de teste inteiro: o modelo bate quando o *p*, arredondado a 10 casas, fica abaixo de 5%. Nenhum dos dois ficou: no período, nenhum errou menos que supor zero por uma diferença que dificilmente seja acaso, e as previsões dos dois não são mais informativas que supor retorno zero. | `engine/src/engine/returns/evaluation.py:80`, `engine/src/engine/returns/evaluation.py:60`, `engine/src/engine/returns/evaluation.py:61` (`1 − Φ`, unilateral); `backend/apps/returns/compute.py:293`, `backend/apps/returns/compute.py:295`; `backend/apps/returns/config.py:12` |
| `retorno.veredito` | um bate, ou os dois | O(s) modelo(s) com *p* do DM abaixo de 5% erraram menos que supor zero; como o DM só é positivo quando o erro quadrático médio do modelo é menor que o da referência, bater implica `r2_os` positivo, e a frase diz o tamanho da vantagem por ele. Com dois modelos e muitos ativos, alguns casos assim aparecem por acaso; o acerto de direção (PT) **não** entra no veredito. | `engine/src/engine/returns/evaluation.py:60` (o sinal do DM é o de `média(d)`), `engine/src/engine/returns/evaluation.py:75`, `engine/src/engine/returns/evaluation.py:76`, `engine/src/engine/returns/evaluation.py:77`, `engine/src/engine/returns/evaluation.py:80`; `backend/apps/returns/compute.py:295` (só o DM), `backend/apps/returns/compute.py:296` (o PT à parte) |
| `retorno.veredito` | com `error` | Quando o cálculo de um modelo falhou, não há veredito nem número para ele — "não deu para julgar", diferente de "não bate". | `backend/apps/returns/compute.py:269`, `backend/apps/returns/compute.py:286` (o veredito nulo, com todos os números) |
| `retorno.r2_os` | positivo ou negativo | O erro relativo à referência é `1 − EQM do modelo / EQM de supor zero`, com EQM a média do quadrado do erro sobre os dias de teste (o R² fora da amostra com referência zero). Positivo: o modelo errou menos que o zero; negativo: errou mais. Na fase A, ficou entre −0,95% (AALR3, `ar_1`) e +0,40% (PETR4, `ar_1`). | `engine/src/engine/returns/evaluation.py:74`, `engine/src/engine/returns/evaluation.py:75`, `engine/src/engine/returns/evaluation.py:76`, `engine/src/engine/returns/evaluation.py:77`; os dias de teste, `engine/src/engine/returns/runner.py:52` |
| `retorno.acerto` | — (com a parcela de alta) | O acerto de direção é a parcela dos dias em que o sinal da previsão foi o do retorno, contada só nos dias com retorno **e** previsão diferentes de zero — o dia sem variação de preço não tem direção. Fica sempre ao lado da parcela de dias de alta nesses mesmos dias, a régua: quem diz "sobe" todo dia acerta exatamente essa parcela. | `engine/src/engine/returns/evaluation.py:83`, `engine/src/engine/returns/evaluation.py:84`, `engine/src/engine/returns/evaluation.py:93` (a parcela de alta), `engine/src/engine/returns/evaluation.py:95` (o acerto) |
| `retorno.dm` | — (o *p*) | O Diebold-Mariano compara, dia a dia, o quadrado do retorno (o erro de supor zero) com o quadrado do erro do modelo; a estatística é a média dessa diferença dividida pelo seu erro-padrão de longo prazo (Newey-West, núcleo de Bartlett, defasagem `⌊4·(n/100)^(2/9)⌋` — 7 com os *n* de hoje —, sobre a série centrada, divisor *n*). O *p* é unilateral, `1 − Φ(DM)`. | `engine/src/engine/returns/evaluation.py:80`; `engine/src/engine/returns/evaluation.py:41`, `engine/src/engine/returns/evaluation.py:46`, `engine/src/engine/returns/evaluation.py:48`, `engine/src/engine/returns/evaluation.py:50`; `engine/src/engine/returns/evaluation.py:60`, `engine/src/engine/returns/evaluation.py:61` |
| `retorno.cw` | — (o *p*) | O Clark-West pergunta se o modelo tem informação que o zero não tem, levando em conta que o zero é um caso particular dele: a diferença diária é o quadrado do retorno menos (o quadrado do erro do modelo menos o quadrado da previsão), com o mesmo Newey-West e o *p* unilateral. É mostrado e não entra no veredito. | `engine/src/engine/returns/evaluation.py:81`, `engine/src/engine/returns/evaluation.py:60`, `engine/src/engine/returns/evaluation.py:61`; fora do veredito, `backend/apps/returns/compute.py:295` |
| `retorno.pt` | com *p* | O Pesaran-Timmermann pergunta se o acerto de direção é maior que o de um palpite independente com as mesmas proporções de alta prevista e realizada: compara o acerto com `P* = p_y·p_x + (1 − p_y)(1 − p_x)`, pela diferença das variâncias do artigo; *p* unilateral. Não entra no veredito. | `engine/src/engine/returns/evaluation.py:99`, `engine/src/engine/returns/evaluation.py:100`, `engine/src/engine/returns/evaluation.py:101`, `engine/src/engine/returns/evaluation.py:107`, `engine/src/engine/returns/evaluation.py:108`; fora do veredito, `backend/apps/returns/compute.py:296` |
| `retorno.pt` | nulo (direção constante) | Quando o modelo previu a mesma direção em todos os dias (ou a ação foi para o mesmo lado em todos), o teste não tem o que medir e fica sem *p*: o acerto do modelo é, então, a própria parcela de dias de alta (ou de queda). Na fase A, o `historical_mean` previu alta em todos os dias de teste em cinco dos seis ativos. | `engine/src/engine/returns/evaluation.py:106`; `backend/apps/returns/compute.py:296` (sem *p*, sem veredito de direção) |
| `retorno.previsao` | mostrada, modelo que não bate | A previsão do próximo pregão é o mesmo cálculo do teste aplicado ao dia seguinte ao último preço: os parâmetros do trecho corrente (reestimados com tudo até o último preço quando ele abre um trecho de 252); no `historical_mean`, a média dos retornos conhecidos; no `ar_1`, `c + φ` vezes o retorno do último pregão. A data é o primeiro dia de semana depois do último preço, sem o calendário de feriados. Como o modelo não bate a referência, a previsão não é mais informativa que supor zero. | `engine/src/engine/returns/models.py:28` (a posição *n* abre trecho se for múltipla de 252), `engine/src/engine/returns/models.py:47`, `engine/src/engine/returns/models.py:54`; `engine/src/engine/returns/models.py:79`; `engine/src/engine/returns/models.py:50`, `engine/src/engine/returns/models.py:103` (a véspera da posição *n* é o último retorno); `backend/apps/returns/compute.py:146`, `backend/apps/returns/compute.py:298`; `backend/apps/returns/compute.py:295` |
| `retorno.previsao` | mostrada, modelo que bate | A mesma regra de cálculo e de data; o modelo bateu a referência no período, o que não garante que a próxima previsão acerte — é um número estatístico, gravado com 10 casas. | `engine/src/engine/returns/models.py:47`, `engine/src/engine/returns/models.py:54`; `backend/apps/returns/compute.py:297`, `backend/apps/returns/compute.py:259`, `backend/apps/returns/compute.py:298` |

## As chaves sem a avançada (uma leitura só, fora do `N`)

Frases de estado e de previsão ausente, e o aviso. Cada uma diz o que o código faz, conferido:

- `retorno.estado.inativo` — R4: o ativo está inativo, e o cálculo diário só roda para ativo ativo com preço
  (`backend/apps/risk/compute.py:274`, o `_resolve` que o retorno importa em `backend/apps/returns/compute.py:49`).
- `retorno.estado.semSerie` — R5: o `/prices` falhou; não se afirma o motivo.
- `retorno.estado.naoCoberto` — R6: sem preço, a validação chega junto com o cálculo do risco pedido na seção de risco
  (a cadeia sob demanda, `backend/apps/assets/tasks.py:171`).
- `retorno.estado.serieCurta` — R7: quantos pregões há e os 503 precisos (`backend/apps/risk/config.py:15`,
  `frontend/src/risk/config.ts:8`).
- `retorno.estado.naoCalculado` — R8: entra no próximo cálculo diário (o quinto elo da rotina,
  `backend/apps/assets/tasks.py:109`).
- `retorno.previsao.inativo` — a previsão gravada é de quando o ativo negociava, e não é mostrada.
- `retorno.previsao.passada` — a data prevista já passou (comparada com hoje no fuso do navegador,
  `frontend/src/screens/AssetScreen.tsx:117`); a próxima entra no próximo cálculo diário.
- `retorno.aviso` — o aviso do RF-19, sempre aberto em R3 a R8, nas duas leituras, isento da lista ampliada do RF-21.

## O que muda no portão

- A lista fechada proposta é a de partida da spec (RF-20), sem acréscimo: **N = 7**. As frases de estado (cinco), as
  duas de previsão ausente e o aviso são oito chaves de uma leitura só.
- O "um bate" e o "os dois batem" ficam no mesmo ramo da tabela porque a afirmação técnica é a mesma; o mockup tem as
  três frases do RF-17 (nenhum, um, os dois) mais a de `error`.
- A frase avançada de `retorno.previsao` diz "sem o calendário de feriados": num feriado, a previsão vale para o pregão
  seguinte (a spec, riscos). Se o portão preferir não mencionar, a afirmação continua conferida.
