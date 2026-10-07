# M2.2b — Conferência técnica: o risco da carteira (T1)

**N = 13** chaves distintas — **5 novas** com frase e **8 `risco.*` do ativo reaproveitadas**. Lista fechada proposta,
para o portão do `risco.html` (T4) aprovar.

Só leitura. Para cada chave com frase que a seção de risco da carteira vai mostrar, o que a frase avançada afirma e o
`caminho:linha` em que cada afirmação foi conferida, no código que calcula o risco **da carteira** (spec, RF-13). Os
caminhos são relativos à raiz do repositório. **Afirmação sem `caminho:linha` não vai ao mockup.** Conferido no ramo
`marco1/M2.2b-telas-da-carteira` (HEAD `e935c4a`, o plano aprovado; o código é o da `main` em `7684c21`, depois do
M1.4b), em 2026-10-03. `backend/` e `engine/` só lidos. As âncoras do motor que esta conferência não repete — o que cada
família faz com o tempo — estão em `docs/mockups/M2.3/conferencia-risco.md` ("O que vale para todas as linhas"),
reconferidas no M1.4b; o motor não mudou desde então.

## A lista fechada proposta

**Novas (5)** — nenhuma existe hoje em `frontend/src/content/`; nome, assinatura e texto são proposta:

- `carteira.risco.perdaReais` — função `(valor: string, cadaN: number)`, a frase da faixa em reais de cada nível;
- `carteira.risco.valorAgora` — texto, a frase de que os reais são calculados na leitura, com o valor de agora;
- `carteira.risco.serie` — texto, a frase da série da carteira (rebalanceada a cada pregão, a interseção, o piso);
- `carteira.risco.asOf` — função `(data: string)`, a frase da data dos preços usados (`as_of_date`);
- `carteira.risco.naoRejeitados` — função `(k: number, julgados: number, total: number)`, a mesma assinatura de
  `risco.naoRejeitados`: a iniciante do ativo fala "deste ativo" no ramo `k = 0` (ver a tabela).

**Reaproveitadas (8)** — já em `AS_61`, com a iniciante e a avançada de hoje, sem mudar texto:

- `risco.perda95`, `risco.perda99`, `risco.discordancia`, `risco.veredito`, `risco.violacoes`, `risco.kupiec`,
  `risco.christoffersen`, `risco.dq`.

**Para a T9:** só as 5 novas entram em `AS_N` (`AS_N` = 61 + 5 = **66**) e na `LISTA_FECHADA` de
`frontend/tests/textos.test.ts`. As 8 reaproveitadas já estão em `AS_61`.

**Se o portão preferir não ter `carteira.risco.naoRejeitados`** (ver "Defeito para o plano", no fim): a alternativa é
trocar, na iniciante de `risco.naoRejeitados`, "este ativo"/"o ativo"/"dele" por palavras que sirvam aos dois — o que
muda o texto da tela do ativo. Nesse caso a lista é 4 novas + 9 reaproveitadas, **N continua 13**, e `AS_N` = 65.

## O que vale para todas as linhas

Conferido uma vez, citado abaixo onde a frase depende disto.

- **O caminho é o do ativo, com outra série.** A tarefa por modelo da carteira reconstrói a série da execução
  (`backend/apps/portfolios/tasks.py:164`) e chama o mesmo `run_experiment` do motor com os testes, os níveis, a janela
  de treino e a semente do ativo (`backend/apps/portfolios/tasks.py:169` a `backend/apps/portfolios/tasks.py:179`;
  `backend/apps/risk/config.py:10`, `backend/apps/risk/config.py:11`, `backend/apps/risk/config.py:20`,
  `backend/apps/risk/config.py:22`). Os modelos são os nove (`backend/apps/portfolios/config.py:17` a
  `backend/apps/portfolios/config.py:27`; `backend/apps/portfolios/services.py:423`). **O motor não muda** (D-117).
- **A série que o motor recebe é o índice da carteira, na coluna `close`** (`backend/apps/portfolios/provider.py:25` a
  `backend/apps/portfolios/provider.py:37`). O motor tira dela o retorno logarítmico, como do preço de um ativo
  (`engine/src/engine/data/preprocessing.py:15`, `engine/src/engine/data/preprocessing.py:21`) — com o índice, é
  `ln(1 + R_k)`, o log-retorno da carteira (`backend/apps/portfolios/series.py:11`).
- **O índice.** As datas são a interseção das datas em que cada ação da versão tem `adj_close > 0`
  (`backend/apps/portfolios/series.py:97`, `backend/apps/portfolios/series.py:60`). O retorno de cada data é o simples
  ponderado pelos pesos fixos — `R_k = Σ (w_i/100)·(adj_i(d_k)/adj_i(d_{k−1}) − 1)`, rebalanceado a cada data
  (`backend/apps/portfolios/series.py:8` a `backend/apps/portfolios/series.py:10`, `backend/apps/portfolios/series.py:63`
  a `backend/apps/portfolios/series.py:67`) —, e `I_0 = 1`, `I_k = I_{k−1}·(1 + R_k)`
  (`backend/apps/portfolios/series.py:61`, `backend/apps/portfolios/series.py:68`). Uma data que falta a uma ação sai da
  série inteira, e o retorno da data seguinte cobre o intervalo todo (`backend/apps/portfolios/series.py:9`,
  `backend/apps/portfolios/series.py:10`).
- **Treino e teste.** Os primeiros 252 retornos são o treino e o resto é o teste
  (`engine/src/engine/experiments/runner.py:87`, `engine/src/engine/experiments/runner.py:88`). O manifesto da carteira
  grava `session_count` = datas da série, `train_count` = 252 e `test_count = datas − 1 − 252`
  (`backend/apps/portfolios/services.py:418` a `backend/apps/portfolios/services.py:422`). O piso é o do ativo, 503
  datas (`backend/apps/portfolios/services.py:348` a `backend/apps/portfolios/services.py:353`;
  `backend/apps/risk/config.py:13` a `backend/apps/risk/config.py:15`), que deixam ao menos 250 dias de teste.
- **Sem retratos.** A tarefa da carteira não passa retrato ao motor (`backend/apps/portfolios/tasks.py:169` a
  `backend/apps/portfolios/tasks.py:178`, sem `snapshots`), e o resultado não tem as colunas de retrato
  (`backend/apps/portfolios/compute.py:7`; `backend/apps/portfolios/models.py:272` a
  `backend/apps/portfolios/models.py:274`): cada cálculo treina do zero (D-119, item 4).
- **A conversão do resultado é a do ativo**, copiada: com `error`, os números nulos; `violations` e
  `expected_violations` do Kupiec; o veredito, Kupiec **e** Christoffersen, nulo com erro; os mesmos quantizadores
  (`backend/apps/portfolios/compute.py:4` a `backend/apps/portfolios/compute.py:6`,
  `backend/apps/portfolios/compute.py:34` a `backend/apps/portfolios/compute.py:41`,
  `backend/apps/portfolios/compute.py:64` a `backend/apps/portfolios/compute.py:84`). O `var_latest` é o último ponto da
  série de VaR (`backend/apps/portfolios/compute.py:65`).
- **A perda em reais.** `notional × (1 − e^(−VaR))`, quantizada ao centavo, metade para cima
  (`backend/apps/portfolios/services.py:275` a `backend/apps/portfolios/services.py:279`), calculada **na leitura** com o
  `notional` da carteira naquele instante (`backend/apps/portfolios/views.py:286` a
  `backend/apps/portfolios/views.py:290`), por modelo (`backend/apps/portfolios/views.py:275`) e nos extremos de cada nível
  (`backend/apps/portfolios/views.py:217` a `backend/apps/portfolios/views.py:226`). Nenhuma coluna guarda reais
  (`backend/apps/portfolios/models.py:286` a `backend/apps/portfolios/models.py:302`).

## A tabela

| Chave | Ramo | O que a frase avançada vai afirmar | Conferido em | Parâmetros lidos (janela, anualização, nível, casas) |
|---|---|---|---|---|
| `carteira.risco.perdaReais` | — (um só ramo; só aparece com valor) | A perda em reais é `valor × (1 − e^(−VaR))`, arredondada ao centavo, metade para cima: a mesma perda simples do percentual, aplicada ao valor. A faixa vai da conversão do menor à do maior VaR do nível, entre os modelos que calcularam; na tabela, cada modelo tem a sua. Supõe o valor distribuído pelos pesos da composição, como a série da carteira, rebalanceada a cada pregão. | **A fórmula e o centavo:** `backend/apps/portfolios/services.py:275` a `backend/apps/portfolios/services.py:279`. **A mesma conversão do %:** `frontend/src/format/var.ts:11`. **A faixa, do menor ao maior VaR dos que calcularam:** `backend/apps/portfolios/views.py:214` a `backend/apps/portfolios/views.py:226` (a conversão é crescente no VaR, então o mínimo em reais é o do menor VaR). **Por modelo:** `backend/apps/portfolios/views.py:275`. **Só com valor:** `backend/apps/portfolios/services.py:277`, `backend/apps/portfolios/services.py:278` (sem `notional`, nulo). **Os pesos fixos, rebalanceados a cada data:** `backend/apps/portfolios/series.py:8` a `backend/apps/portfolios/series.py:10`, `backend/apps/portfolios/series.py:63` a `backend/apps/portfolios/series.py:67`. | Reais com 2 casas (`backend/apps/portfolios/serializers.py:111`, `backend/apps/portfolios/serializers.py:112`); nível α = 0,05 e 0,01 (`backend/apps/risk/config.py:20`); "1 dia a cada" 20 e 100 (`frontend/src/components/LossSummary.tsx:13`); VaR a 10 casas (`backend/apps/portfolios/serializers.py:107`, `backend/apps/portfolios/serializers.py:108`). |
| `carteira.risco.valorAgora` | — (texto) | O valor aplicado fica fora do cálculo: não entra na série nem nos modelos, mudá-lo não cria versão nem muda a série, e por isso não abre cálculo novo. Os reais são calculados a cada leitura com o valor guardado naquele momento; nenhum valor em reais fica gravado com o resultado. | **Fora da série e dos modelos:** `backend/apps/portfolios/series.py:91` a `backend/apps/portfolios/series.py:111` (só pesos e preços); `backend/apps/portfolios/services.py:347` (o pedido monta a série da versão, sem `notional`). **Mudar o valor não cria versão:** `backend/apps/portfolios/services.py:216` a `backend/apps/portfolios/services.py:232`. **Não abre cálculo novo:** a recusa compara só a data e o SHA-256 da série (`backend/apps/portfolios/services.py:382` a `backend/apps/portfolios/services.py:392`). **Na leitura, com o valor de agora:** `backend/apps/portfolios/views.py:286` a `backend/apps/portfolios/views.py:290`. **Nada em reais gravado:** `backend/apps/portfolios/models.py:286` a `backend/apps/portfolios/models.py:302` (sem coluna de reais). | Valor com 2 casas, maior que zero (`backend/apps/portfolios/serializers.py:24` a `backend/apps/portfolios/serializers.py:32`). |
| `carteira.risco.serie` | — (texto) | A carteira vai aos modelos como uma série só: um índice que começa em 1 e anda pelo retorno simples ponderado pelos pesos, fixos e rebalanceados a cada data. As datas são as em que todas as ações da composição têm fechamento ajustado positivo; numa data que falta a uma delas, a data fica fora, e o retorno da seguinte cobre o intervalo. O motor tira do índice o retorno logarítmico — o da carteira, não a média ponderada dos de cada ação — e roda os mesmos nove modelos, testes, níveis e semente do ativo, com os primeiros 252 retornos de treino e o resto de teste, treinando do zero a cada cálculo. O piso é de 503 datas em comum, que deixam ao menos 250 dias de teste. | **O índice e o retorno ponderado, rebalanceado:** `backend/apps/portfolios/series.py:8` a `backend/apps/portfolios/series.py:11`, `backend/apps/portfolios/series.py:61` a `backend/apps/portfolios/series.py:68`. **A interseção, com `adj_close > 0`:** `backend/apps/portfolios/series.py:7`, `backend/apps/portfolios/series.py:60`, `backend/apps/portfolios/series.py:97`. **A lacuna cobre o intervalo:** `backend/apps/portfolios/series.py:9`, `backend/apps/portfolios/series.py:10`, `backend/apps/portfolios/series.py:64`. **O índice como `close` e o log-retorno:** `backend/apps/portfolios/provider.py:34` a `backend/apps/portfolios/provider.py:37`; `engine/src/engine/data/preprocessing.py:15`, `engine/src/engine/data/preprocessing.py:21`. **Os mesmos modelos, testes, níveis e semente:** `backend/apps/portfolios/tasks.py:169` a `backend/apps/portfolios/tasks.py:178`; `backend/apps/portfolios/config.py:17` a `backend/apps/portfolios/config.py:27`. **Treino e teste:** `engine/src/engine/experiments/runner.py:87`, `engine/src/engine/experiments/runner.py:88`; `backend/apps/portfolios/services.py:420` a `backend/apps/portfolios/services.py:422`. **Do zero:** `backend/apps/portfolios/compute.py:7`; `backend/apps/portfolios/tasks.py:169` a `backend/apps/portfolios/tasks.py:178` (sem `snapshots`). **O piso:** `backend/apps/portfolios/services.py:348`, `backend/apps/portfolios/services.py:349`; `backend/apps/risk/config.py:13` a `backend/apps/risk/config.py:15`. | Treino 252 (`backend/apps/risk/config.py:11`); piso 503 (`backend/apps/risk/config.py:15`); semente 42 (`backend/apps/risk/config.py:10`); α 0,05 e 0,01 (`backend/apps/risk/config.py:20`); horizonte 1 dia (`engine/src/engine/experiments/runner.py:29`); sem anualização. |
| `carteira.risco.asOf` | — (um só ramo) | A data dos preços é a última da série: a mais recente em que todas as ações da composição têm fechamento ajustado positivo — no máximo, a do último preço da ação mais atrasada. Um pedido novo só abre cálculo quando essa data ou a série mudam: com a mesma data e o mesmo SHA-256 da série do cálculo fechado mais recente, concluído ou parcial, a resposta é que o risco desta versão já está calculado. | **A última data da interseção:** `backend/apps/portfolios/series.py:60`, `backend/apps/portfolios/services.py:419` (`as_of_date = s.dates[-1]`); sai pela rota (`backend/apps/portfolios/views.py:246`). **No máximo, a da ação mais atrasada:** a interseção só tem datas que todas têm (`backend/apps/portfolios/series.py:60`). **Quando o pedido recusa:** `backend/apps/portfolios/services.py:377` a `backend/apps/portfolios/services.py:392`. | Data ISO na API (`backend/apps/portfolios/serializers.py:163`). |
| `carteira.risco.naoRejeitados` | `k ≥ 1` — **exigida a expressão da D-64** ("não do número de hoje") | A mesma afirmação da avançada de `risco.naoRejeitados` (`frontend/src/content/avancado.ts:217` a `frontend/src/content/avancado.ts:221`), que vale igual para a carteira: `k` dos `julgados` modelos têm veredito adequado neste nível — nem o Kupiec nem o Christoffersen rejeitaram, na série de VaR do período de teste; o veredito fala dela, não do número de hoje; a lista segue a ordem fixa dos nove; os sem veredito contam à parte. | **O veredito da carteira:** `backend/apps/portfolios/compute.py:34` a `backend/apps/portfolios/compute.py:41`, `backend/apps/portfolios/compute.py:83`; `engine/src/engine/backtesting/kupiec.py:39`, `engine/src/engine/backtesting/christoffersen.py:53`. **Sobre a série do teste:** `engine/src/engine/experiments/runner.py:110` a `engine/src/engine/experiments/runner.py:117`. **A contagem e a ordem fixa:** `frontend/src/risk/summary.ts:47` a `frontend/src/risk/summary.ts:51`; `frontend/src/components/LossSummary.tsx:85` a `frontend/src/components/LossSummary.tsx:88` (total = 9, os nove da carteira: `backend/apps/portfolios/config.py:17` a `backend/apps/portfolios/config.py:27`). **Por que chave própria:** a iniciante do ativo, ramo `k = 0`, diz "este ativo", "o ativo" e "dele" (`frontend/src/content/textos.ts:376`). | Nível do painel; total 9 (`frontend/src/api/types.ts:13`). |
| `carteira.risco.naoRejeitados` | `k = 0` — **exigida a expressão da D-64** | A mesma afirmação de `frontend/src/content/avancado.ts:215` e `frontend/src/content/avancado.ts:216`: todos os julgados foram rejeitados por ao menos um dos dois testes na série de VaR do período de teste; o veredito fala dela, não do número de hoje. A iniciante troca "este ativo" por "esta carteira". | `backend/apps/portfolios/compute.py:41` (`False` quando um dos dois falha); `frontend/src/risk/summary.ts:48` a `frontend/src/risk/summary.ts:51`; o ramo do ativo, `frontend/src/content/textos.ts:375`, `frontend/src/content/textos.ts:376`. | Nível do painel; `julgados de total` quando faltam. |
| `carteira.risco.naoRejeitados` | `julgados = 0` — isento | Nenhum modelo pôde ser julgado neste nível: o cálculo falhou em todos, e falha não é reprovação. | `backend/apps/portfolios/compute.py:36`, `backend/apps/portfolios/compute.py:41` (`None` com erro); `backend/apps/portfolios/compute.py:88` a `backend/apps/portfolios/compute.py:94` (o par de erro); `frontend/src/risk/summary.ts:51`; `frontend/src/content/avancado.ts:213`, `frontend/src/content/avancado.ts:214`. | — |
| `risco.perda95` | — (texto) — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:184`) vale igual: o VaR de 1 dia a 95% é o quantil de 5% do retorno logarítmico diário — aqui, o da série da carteira —, com o sinal trocado; nenhum modelo usa o retorno do próprio dia; nos seis que se atualizam a cada pregão, o número é o do último pregão da série; nos três tradicionais, só muda a cada 252 pregões; vai à tela como `1 − e^(−VaR)`. "Pregão" e "dia" são as datas da série da carteira, com a ressalva da lacuna que a `carteira.risco.serie` faz. | **A série é o log-retorno do índice:** `backend/apps/portfolios/provider.py:34` a `backend/apps/portfolios/provider.py:37`; `engine/src/engine/data/preprocessing.py:15`. **O mesmo motor, os mesmos modelos e α:** `backend/apps/portfolios/tasks.py:169` a `backend/apps/portfolios/tasks.py:179`; `backend/apps/risk/config.py:20`. **Nunca o retorno do dia:** `engine/src/engine/models/base.py:66`; provado para seis em `engine/tests/test_sem_olhar_a_frente.py:115`. **Os tradicionais a cada 252:** `engine/src/engine/models/traditional/_expanding.py:18`, `engine/src/engine/models/traditional/_expanding.py:38`. **O último ponto:** `backend/apps/portfolios/compute.py:65`. **A conversão:** `frontend/src/format/var.ts:11`. **O painel usa a chave:** `frontend/src/components/LossSummary.tsx:56` a `frontend/src/components/LossSummary.tsx:58`. | α = 0,05; horizonte 1 dia (`engine/src/engine/experiments/runner.py:29`); treino 252 (`backend/apps/risk/config.py:11`); perda com 1 casa (`frontend/src/format/var.ts:15`). |
| `risco.perda99` | — (texto) — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:186`) vale igual: o mesmo VaR a 99%, estimado e mostrado da mesma forma; cada afirmação da linha de `risco.perda95` vale com α = 0,01, pelas mesmas âncoras. | `backend/apps/risk/config.py:20`; `backend/apps/portfolios/tasks.py:175`; as âncoras da linha de `risco.perda95`; `frontend/src/components/LossSummary.tsx:58`. | α = 0,01; o resto, idem. |
| `risco.discordancia` | `n = 0` — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:195`, `frontend/src/content/avancado.ts:196`) vale igual: nenhum dos nove produziu VaR neste nível, e não há faixa. | Modelo com erro grava `var_latest` nulo: `backend/apps/portfolios/compute.py:51`, `backend/apps/portfolios/compute.py:56`, `backend/apps/portfolios/compute.py:64`, `backend/apps/portfolios/compute.py:65`; `frontend/src/risk/summary.ts:24`, `frontend/src/risk/summary.ts:26`. | Total 9 (`frontend/src/risk/summary.ts:33`). |
| `risco.discordancia` | `n = 1` — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:197`, `frontend/src/content/avancado.ts:198`) vale igual: só um modelo produziu VaR; o número é o dele. | `frontend/src/risk/summary.ts:29` a `frontend/src/risk/summary.ts:32`; `frontend/src/components/LossSummary.tsx:44`. | 1 casa. |
| `risco.discordancia` | `n ≥ 2` — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:199` a `frontend/src/content/avancado.ts:203`) vale igual: a faixa vai da menor à maior perda entre os que produziram VaR, e modelo sem resultado (o cálculo falhou ou ficou sem linha nesta execução) conta à parte; não diz qual extremo está certo. A faixa em reais, quando há valor, é da `carteira.risco.perdaReais`, não desta chave. | A carteira tem os nove: `backend/apps/portfolios/config.py:17` a `backend/apps/portfolios/config.py:27`; a execução parcial pela regra do ativo, `backend/apps/portfolios/tasks.py:208` a `backend/apps/portfolios/tasks.py:213`; `frontend/src/risk/summary.ts:23` a `frontend/src/risk/summary.ts:33`. | Nível do painel; total 9. |
| `risco.veredito` | a frase inteira — **reaproveitada**, com a expressão da D-64 | A avançada de hoje (`frontend/src/content/avancado.ts:206`) vale igual: o veredito é por modelo e por nível — adequado quando nem o Kupiec nem o Christoffersen rejeitam, a 0,05; não adequado quando um rejeita; não julgado com erro —; o DQ fica fora; os testes avaliam a série do período de teste, não do número de hoje. A frase não fala da Basileia, que a carteira grava e a rota não devolve. | `backend/apps/portfolios/compute.py:34` a `backend/apps/portfolios/compute.py:41`; `engine/src/engine/backtesting/kupiec.py:14`, `engine/src/engine/backtesting/kupiec.py:39`; `engine/src/engine/backtesting/christoffersen.py:16`, `engine/src/engine/backtesting/christoffersen.py:53`; `engine/src/engine/experiments/runner.py:115` a `engine/src/engine/experiments/runner.py:117`; a Basileia gravada e não devolvida, `backend/apps/portfolios/compute.py:82` e `backend/apps/portfolios/serializers.py:116`; a nota da tabela, `frontend/src/components/ModelTable.tsx:256`. | Significância 0,05. |
| `risco.violacoes` | `kupiecOk` verdadeiro — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:223`, `frontend/src/content/avancado.ts:224`) vale igual: violações são os dias do período de teste — as datas da série da carteira — em que o retorno logarítmico ficou abaixo de −VaR; o esperado é o número de dias de teste vezes α. | `backend/apps/portfolios/compute.py:70`, `backend/apps/portfolios/compute.py:71` (os do Kupiec); `engine/src/engine/backtesting/kupiec.py:29`, `engine/src/engine/backtesting/kupiec.py:30`, `engine/src/engine/backtesting/kupiec.py:41`, `engine/src/engine/backtesting/kupiec.py:42`; `frontend/src/components/ModelTable.tsx:161` a `frontend/src/components/ModelTable.tsx:165`. | Esperadas guardadas a 6 casas (`backend/apps/risk/compute.py:104`); "1 dia a cada" 20/100. |
| `risco.violacoes` | `kupiecOk` falso — **reaproveitada** | O mesmo, e: longe o bastante do esperado para o Kupiec rejeitar. | `backend/apps/portfolios/compute.py:72`; `engine/src/engine/backtesting/kupiec.py:39`; `frontend/src/components/ModelTable.tsx:165`. | Idem. |
| `risco.kupiec` | `ok` verdadeiro / falso — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:225`, `frontend/src/content/avancado.ts:226`) vale igual: proporção de falhas, razão de verossimilhança contra qui-quadrado com 1 grau; cobertura incondicional. | `backend/apps/portfolios/tasks.py:174` (os quatro testes do ativo); `engine/src/engine/backtesting/kupiec.py:17` a `engine/src/engine/backtesting/kupiec.py:21`, `engine/src/engine/backtesting/kupiec.py:33`, `engine/src/engine/backtesting/kupiec.py:39`; `backend/apps/portfolios/compute.py:73`. | p-valor a 10 casas (`backend/apps/risk/compute.py:105`). |
| `risco.christoffersen` | `ok` verdadeiro / falso — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:227`, `frontend/src/content/avancado.ts:228`) vale igual: independência, cadeia de Markov de 1ª ordem, 1 grau; o p-valor é o da independência. | `backend/apps/portfolios/tasks.py:174`; `engine/src/engine/backtesting/christoffersen.py:25` a `engine/src/engine/backtesting/christoffersen.py:34`, `engine/src/engine/backtesting/christoffersen.py:43`, `engine/src/engine/backtesting/christoffersen.py:44`; `backend/apps/portfolios/compute.py:77`, `backend/apps/portfolios/compute.py:78`. | Idem. |
| `risco.dq` | `ok` verdadeiro / falso — **reaproveitada** | A avançada de hoje (`frontend/src/content/avancado.ts:229`, `frontend/src/content/avancado.ts:230`) vale igual: quantil dinâmico, quatro defasagens e o VaR do dia, 6 graus; fora do veredito. | `backend/apps/portfolios/tasks.py:174`; `engine/src/engine/backtesting/dq.py:17`, `engine/src/engine/backtesting/dq.py:25`, `engine/src/engine/backtesting/dq.py:27`, `engine/src/engine/backtesting/dq.py:46`, `engine/src/engine/backtesting/dq.py:47`; `backend/apps/portfolios/compute.py:81`; fora do veredito, `backend/apps/portfolios/compute.py:41`. | Idem. |

## Os textos propostos das chaves novas

Para o mockup copiar e o portão aprovar. Nenhum usa palavra da varredura de `frontend/tests/vocabulario.test.ts`
(melhor, melhores, recomendado e flexões, recomendamos, confiável, confiáveis), e nenhum sugere peso, composição, ou
tirar ou pôr ação (RF-14, D-116 item 3). Cada avançada é a afirmação da tabela.

**`carteira.risco.perdaReais(valor, cadaN)`**

- iniciante: `` `Em reais, sobre ${valor}: a mesma perda em %, aplicada ao valor da carteira. Em 1 dia a cada ${cadaN}, espera-se que a perda passe desse limite.` ``
- avançada: `` `Valor × (1 − e^(−VaR)), com o valor de ${valor}, arredondado ao centavo, metade para cima: a mesma perda simples do percentual. A faixa vai da conversão do menor à do maior VaR do nível, entre os modelos que calcularam; na tabela, cada modelo tem a sua. Supõe o valor distribuído pelos pesos da composição, como a série da carteira, rebalanceada a cada pregão.` `` (declara `_cadaN`, para a mesma assinatura)

**`carteira.risco.valorAgora`**

- iniciante: "Os valores em reais usam o valor que a carteira tem agora. Mudar o valor muda os reais na hora, sem um cálculo novo: o valor não entra nos modelos."
- avançada: "O valor aplicado fica fora do cálculo: não entra na série nem nos modelos, e mudá-lo não cria versão nem muda a série — por isso não abre cálculo novo. Os reais são calculados a cada leitura, com o valor guardado naquele momento; nenhum valor em reais fica gravado com o resultado."

**`carteira.risco.serie`**

- iniciante: "A carteira entra nos modelos como uma série só: em cada pregão em que todas as ações têm preço, o retorno de cada uma conta pelo seu peso, como se os pesos fossem refeitos todo dia. Os nove modelos são os mesmos do risco de uma ação, e pedem ao menos 503 pregões em comum — cerca de dois anos de bolsa."
- avançada: "Um índice que começa em 1 e anda pelo retorno simples ponderado pelos pesos, fixos e rebalanceados a cada data. As datas são as em que todas as ações da composição têm fechamento ajustado positivo; numa data que falta a uma delas, a data fica fora, e o retorno da seguinte cobre o intervalo. O motor tira do índice o retorno logarítmico — o da carteira, não a média ponderada dos de cada ação — e roda os mesmos nove modelos, testes, níveis e semente do ativo, com os primeiros 252 retornos de treino e o resto de teste, treinando do zero a cada cálculo. O piso é de 503 datas em comum, que deixam ao menos 250 dias de teste."

**`carteira.risco.asOf(data)`**

- iniciante: `` `Preços até ${data}: o último pregão em que todas as ações da carteira têm preço. Se uma delas fica sem preço novo, a data para nela.` ``
- avançada: `` `${data} é a última data da série: a mais recente em que todas as ações da composição têm fechamento ajustado positivo — no máximo, a do último preço da ação mais atrasada. Um pedido novo só abre cálculo quando essa data ou a série mudam: com a mesma data e o mesmo SHA-256 da série do cálculo fechado mais recente, concluído ou parcial, a resposta é que o risco desta versão já está calculado.` ``

**`carteira.risco.naoRejeitados(k, julgados, total)`**

- iniciante: a de `risco.naoRejeitados` (`frontend/src/content/textos.ts:367` a `frontend/src/content/textos.ts:382`), com o ramo
  `k = 0` assim: `` `Nenhum dos métodos julgados descreveu bem esta carteira neste nível${faltam > 0 ? ` (${julgados} de ${total} julgados)` : ""}. Não é erro do cálculo: é informação sobre a carteira — nenhum dos métodos testados acompanhou o comportamento da série dela no período de teste. O veredito fala desse período, não do número de hoje.${semJulgar}` ``; os ramos `julgados = 0` e
  `k ≥ 1` iguais aos do ativo;
- avançada: a de `risco.naoRejeitados`, igual (`frontend/src/content/avancado.ts:207` a `frontend/src/content/avancado.ts:222`).
  As duas mantêm a expressão "não do número de hoje" nos ramos `k ≥ 1` e `k = 0`.

## Fora da contagem — textos `risco.*` sem frase que a seção da carteira não pode reaproveitar

Não são número com frase (não estão em `AS_61`), e não entram em `N`; ficam aqui porque o mockup da T4 vai precisar de
um texto próprio no lugar de cada um. A afirmação errada para a carteira, com a âncora:

- `risco.estado.E3` diz que "a rotina diária calcula o risco deste ativo de novo" (`frontend/src/content/textos.ts:463`,
  `frontend/src/content/textos.ts:464`) — a carteira é só sob demanda (D-119, item 3; nenhuma tarefa do Beat a chama:
  `backend/apps/portfolios/tasks.py:218` a `backend/apps/portfolios/tasks.py:226` são as três, todas da fila do pedido).
- `risco.estado.E8` e `risco.estado.E5.coletando.nota` falam em coletar preços e calcular o comportamento antes
  (`frontend/src/content/textos.ts:469` a `frontend/src/content/textos.ts:479`) — o pedido da carteira não coleta nada:
  monta a série com o que já está em `silver.price` (`backend/apps/portfolios/services.py:347`), e a ação sem preço
  vira o `insufficient_history` (`backend/apps/portfolios/services.py:349` a `backend/apps/portfolios/services.py:368`).
- `risco.carregando` e `risco.estado.E8.titulo` dizem "deste ativo" (`frontend/src/content/textos.ts:454`,
  `frontend/src/content/textos.ts:477`).
- `risco.estado.E4.nota` ("Cada modelo grava um resultado por nível, 95% e 99%") vale para a carteira
  (`backend/apps/portfolios/compute.py:88` a `backend/apps/portfolios/compute.py:94`;
  `backend/apps/portfolios/views.py:310`, `backend/apps/portfolios/views.py:311`: `results_expected` = 9 × 2).
- `risco.trilha.priceRun`/`risco.trilha.fonte.*` (coleta de preço, Yahoo) e os retratos não têm lugar: a trilha da
  carteira é componente próprio (RF-16), e o manifesto dela traz `price_run_id` (o maior `run_id` de preço das datas da
  série, `backend/apps/portfolios/series.py:88`, `backend/apps/portfolios/series.py:113` a
  `backend/apps/portfolios/series.py:116`) e `series_sha256`, sem retratos.
- A mensagem do `409 portfolio_risk_up_to_date` do RF-11 ("já está calculado com os preços até {as_of_date}") se apoia na
  mesma regra da `carteira.risco.asOf` (`backend/apps/portfolios/services.py:382` a
  `backend/apps/portfolios/services.py:392`). Os três casos do RF-12 se apoiam em
  `backend/apps/portfolios/series.py:117` a `backend/apps/portfolios/series.py:124` (por ação, `first_date` nulo sem
  preço, `sessions` contadas sozinha) e `backend/apps/portfolios/services.py:349` a
  `backend/apps/portfolios/services.py:368` (`sessions` em comum, `minimum`).

## O que não se ancora no código — não vai ao mockup como afirmação

- **"A diferença do rebalanceamento é pequena em 1 dia"** é da D-117 (Consequências), não do código. A frase pode dizer
  que a série é rebalanceada; não que a diferença para a carteira que deriva é pequena.
- **"A ação inativa prende a data"** (spec, riscos) depende de a coleta parar para ação inativa, que esta conferência não
  abriu. A `carteira.risco.asOf` diz só o que a interseção garante: a ação que fica sem preço novo segura a data.
- **"Cerca de dois anos de bolsa"** na iniciante da `carteira.risco.serie` repete a aproximação da iniciante do ativo
  (`frontend/src/content/textos.ts:474`); 503 pregões é o número ancorado.
- **"Não sugere ação" e o tom** não se conferem no código: são do portão (D-153, D-116 item 3).

## Defeito para o plano (não corrigido aqui)

- **A superfície do `LossSummary` não deixa trocar a chave do `naoRejeitados`.** O plano fixa
  `LossSummary<R>({ results, brlRange })`, e o componente chama `textFor("risco.naoRejeitados", …)` por dentro
  (`frontend/src/components/LossSummary.tsx:85`). Com `carteira.risco.naoRejeitados`, a T5 precisa de uma prop a mais
  (ou outra forma de escolher a chave) — mudança no contrato literal da T5. A alternativa sem prop é a do começo:
  neutralizar a iniciante do ativo, o que muda a tela do ativo. Decisão do portão da T4 e do orquestrador.
- **O `d64.test.ts` cobre só `risco.veredito` e `risco.naoRejeitados`.** Uma chave nova com veredito
  (`carteira.risco.naoRejeitados`) precisa da mesma prova da expressão da D-64; o plano não diz quem a escreve (a T9
  copia as chaves para `AS_N` e `LISTA_FECHADA`, não para o `d64.test.ts`).
