# M2.3 — Conferência técnica: risco (T8)

Só leitura. Para cada uma das nove chaves `risco.*` da lista do RF-04, o que a frase avançada vai afirmar e o
`caminho:linha` em que cada afirmação foi conferida, no código que calcula (spec, RF-05). Os caminhos são relativos à
raiz do repositório. **Afirmação sem `caminho:linha` não vai ao mockup.** Conferido no ramo
`marco1/M2.3-camada-explicativa` (HEAD `48ce7ff`, a T0), em 2026-10-01. `engine/` só lido.

As nove chaves e a aridade que têm hoje (a avançada repete a assinatura, RF-05):

- `risco.perda95`, `risco.perda99` — texto (`frontend/src/content/textos.ts:268`, `frontend/src/content/textos.ts:270`),
  um ou outro conforme o nível do painel (`frontend/src/components/LossSummary.tsx:52`);
- `risco.discordancia` — função de seis argumentos `(min, max, n, total, cadaN, unico)`
  (`frontend/src/content/textos.ts:273`), chamada em `frontend/src/components/LossSummary.tsx:55` com `unico = min`
  (`frontend/src/components/LossSummary.tsx:61`);
- `risco.naoRejeitados` — função de três argumentos `(k, julgados, total)` (`frontend/src/content/textos.ts:293`),
  chamada em `frontend/src/components/LossSummary.tsx:79`;
- `risco.veredito` — texto (`frontend/src/content/textos.ts:331`), na nota `data-phrase="veredito"` do cabeçalho da
  tabela (`frontend/src/components/ModelTable.tsx:224`);
- `risco.violacoes` — função `(v, e, cadaN, kupiecOk)` (`frontend/src/content/textos.ts:339`), chamada em
  `frontend/src/components/ModelTable.tsx:157`;
- `risco.kupiec`, `risco.christoffersen`, `risco.dq` — funções `(p, ok)` (`frontend/src/content/textos.ts:341`,
  `frontend/src/content/textos.ts:343`, `frontend/src/content/textos.ts:345`), chamadas pela mesma linha
  `frontend/src/components/ModelTable.tsx:118`, só quando o p-valor e o `passed` existem
  (`frontend/src/components/ModelTable.tsx:108`).

## O que vale para todas as linhas

Conferido uma vez, citado abaixo onde a frase depende disto.

- **A série.** O motor recebe o `adj_close` de `silver.price` na coluna `close` (`backend/apps/risk/provider.py:51`,
  `backend/apps/risk/provider.py:54`) e tira dela o retorno logarítmico diário (`engine/src/engine/data/preprocessing.py:15`,
  `engine/src/engine/data/preprocessing.py:21`). A janela pedida é a série inteira do ativo, da primeira à última data
  guardada (`backend/apps/risk/compute.py:291`, `backend/apps/risk/compute.py:402`, `backend/apps/risk/compute.py:403`).
- **Treino e teste.** Os **primeiros** 252 retornos são o treino; **todo o resto** é o período de teste
  (`engine/src/engine/experiments/runner.py:87`, `engine/src/engine/experiments/runner.py:88`;
  `backend/apps/risk/config.py:11`; `backend/apps/risk/compute.py:407`). O manifesto grava `test_count = pregões − 1 −
  252` (`backend/apps/risk/compute.py:541`). O piso de 503 pregões garante ao menos 250 dias de teste
  (`backend/apps/risk/config.py:15`).
- **Os níveis e o horizonte.** α = 0,05 e 0,01 (`backend/apps/risk/config.py:20`), horizonte de 1 dia
  (`engine/src/engine/experiments/runner.py:29`). "1 dia a cada N" é 20 e 100 (`frontend/src/components/LossSummary.tsx:12`).
- **O VaR é uma série.** Cada modelo produz um VaR por dia do período de teste (`engine/src/engine/models/base.py:60`),
  e os quatro testes rodam sobre essa série inteira contra os retornos do mesmo dia
  (`engine/src/engine/experiments/runner.py:110`, `engine/src/engine/experiments/runner.py:113`,
  `engine/src/engine/experiments/runner.py:116`). O número exibido, `var_latest`, é **o último ponto** da série
  (`backend/apps/risk/compute.py:485`); ele não tem teste próprio. É a distinção da D-64.
- **A violação.** Um dia viola quando o retorno logarítmico fica abaixo de −VaR, estritamente
  (`engine/src/engine/backtesting/kupiec.py:29`, `engine/src/engine/backtesting/christoffersen.py:24`,
  `engine/src/engine/backtesting/dq.py:25`). Como a tela mostra `1 − e^(−VaR)` (`frontend/src/format/var.ts:11`),
  "o retorno log abaixo de −VaR" é o mesmo que "a perda simples acima da perda exibida".
- **O que cada família faz com o tempo** — para a frase avançada **não generalizar**:
  - histórico, paramétrico e Monte Carlo são ajustados **uma vez, só nos 252 retornos do treino** — os do começo da
    série —, e o VaR é constante no teste inteiro (`engine/src/engine/experiments/runner.py:93`;
    `engine/src/engine/models/traditional/historical.py:24`, `engine/src/engine/models/traditional/historical.py:27`;
    `engine/src/engine/models/traditional/parametric.py:17`, `engine/src/engine/models/traditional/parametric.py:18`,
    `engine/src/engine/models/traditional/parametric.py:27`; `engine/src/engine/models/traditional/monte_carlo.py:33`,
    `engine/src/engine/models/traditional/monte_carlo.py:44`, `engine/src/engine/models/traditional/monte_carlo.py:45`).
    O `var_latest` deles é, portanto, calculado sobre o primeiro ano da série;
  - GARCH(1,1) e EGARCH: VaR = −z_α · σ_t, com distribuição normal e média zero, σ_t propagado dia a dia e os
    parâmetros reestimados a cada 252 dias com janela expansiva (`engine/src/engine/models/garch/_conditional.py:39`,
    `engine/src/engine/models/garch/_conditional.py:41`, `engine/src/engine/models/garch/_conditional.py:60`,
    `engine/src/engine/models/garch/_conditional.py:123`, `engine/src/engine/models/garch/_conditional.py:134`);
  - LSTM, GRU e GARCHNet preveem o quantil α direto, pela perda pinball, sobre uma janela de 20 dias de retorno e
    retorno absoluto (o GARCHNet soma o σ do GARCH(1,1)), e continuam o treino a cada 252 dias
    (`engine/src/engine/models/ml/_quantile_nn.py:36`, `engine/src/engine/models/ml/_quantile_nn.py:50`,
    `engine/src/engine/models/ml/_quantile_nn.py:51`, `engine/src/engine/models/ml/_quantile_nn.py:246`,
    `engine/src/engine/models/ml/lstm.py:24`, `engine/src/engine/models/ml/gru.py:24`,
    `engine/src/engine/models/ml/garchnet.py:31`);
  - CAViaR: VaR_t = β0 + β1·VaR_{t−1} + β2·|r_{t−1}|, pela perda pinball, reajustado a cada 252 dias
    (`engine/src/engine/models/ml/caviar.py:31`, `engine/src/engine/models/ml/caviar.py:42`,
    `engine/src/engine/models/ml/caviar.py:21`, `engine/src/engine/models/ml/caviar.py:150`).

## A tabela

| Chave | Ramo | O que a frase avançada vai afirmar | Conferido em | Parâmetros lidos (janela, anualização, nível, casas) |
|---|---|---|---|---|
| `risco.perda95` | — (texto) | É o VaR de 1 dia a 95%: o valor que o retorno logarítmico de um dia só deve ficar abaixo, em negativo, em 5% dos dias. Cada modelo estima esse quantil do seu jeito; o número mostrado é o VaR do último pregão da série, convertido de retorno logarítmico em perda percentual simples, `1 − e^(−VaR)`. | `backend/apps/risk/config.py:20` (α = 0,05); `engine/src/engine/backtesting/kupiec.py:29` (a violação é `retorno < −VaR`); `backend/apps/risk/compute.py:485` (o exibido é o último ponto da série); `frontend/src/format/var.ts:11` e `frontend/src/format/var.ts:15` (a conversão e a casa); `frontend/src/components/LossSummary.tsx:52` (o painel de 95% usa esta chave) | α = 0,05; horizonte 1 dia (`engine/src/engine/experiments/runner.py:29`); sem anualização; perda com 1 casa (`frontend/src/format/var.ts:15`, `frontend/src/format/numbers.ts:16`); `var_latest` guardado a 10 casas (`backend/apps/risk/compute.py:105`). |
| `risco.perda99` | — (texto) | O mesmo a 99%: o valor que o retorno logarítmico de um dia só deve ficar abaixo, em negativo, em 1% dos dias; mostrado como `1 − e^(−VaR)` do último pregão. | `backend/apps/risk/config.py:20` (α = 0,01); `engine/src/engine/backtesting/kupiec.py:29`; `backend/apps/risk/compute.py:485`; `frontend/src/format/var.ts:11`; `frontend/src/components/LossSummary.tsx:52` | α = 0,01; horizonte 1 dia; sem anualização; 1 casa. |
| `risco.discordancia` | `n = 0` (nenhum modelo com VaR neste nível) | Nenhum dos nove produziu VaR neste nível: o cálculo falhou em todos, e não há faixa. | `frontend/src/risk/summary.ts:24` e `frontend/src/risk/summary.ts:26` (sem `var_latest` não nulo, nulo); `frontend/src/components/LossSummary.tsx:58` (`n` vira 0); `frontend/src/content/textos.ts:281`; `backend/apps/risk/compute.py:471` e `backend/apps/risk/compute.py:484` (modelo com erro grava `var_latest` nulo) | Nível do painel; total = 9 (`frontend/src/risk/summary.ts:33`, `frontend/src/api/types.ts:13`). |
| `risco.discordancia` | `n = 1` | Só um modelo produziu VaR neste nível; o valor mostrado é o dele, convertido em perda simples. | `frontend/src/risk/summary.ts:30` a `frontend/src/risk/summary.ts:32` (com um só, mínimo = máximo, `n = 1`); `frontend/src/components/LossSummary.tsx:40` (mostra só o mínimo) e `frontend/src/components/LossSummary.tsx:61` (`unico` é o mínimo); `frontend/src/content/textos.ts:283` | 1 casa; "1 dia a cada" 20 ou 100 (`frontend/src/components/LossSummary.tsx:12`). |
| `risco.discordancia` | `n ≥ 2` (todos, ou parte, com a contagem dos que falharam) | A faixa vai da menor à maior perda entre os modelos que produziram VaR neste nível, cada uma o `var_latest` do modelo convertido em `1 − e^(−VaR)`; a largura da faixa mede o quanto os métodos discordam sobre o último pregão. Modelo sem linha, numa execução parcial, conta como não calculado. Não afirma qual extremo está certo. | `frontend/src/risk/summary.ts:23` a `frontend/src/risk/summary.ts:25` (filtro do nível, `var_latest` não nulo, conversão); `frontend/src/risk/summary.ts:30` e `frontend/src/risk/summary.ts:31` (mínimo e máximo); `frontend/src/risk/summary.ts:33` (total = 9, modelo sem linha conta como não calculado); `frontend/src/components/LossSummary.tsx:35` e `frontend/src/components/LossSummary.tsx:36` (1 casa, sem converter duas vezes); `frontend/src/content/textos.ts:285` a `frontend/src/content/textos.ts:289` | Nível do painel; 1 casa; total 9; `n` e `total − n` (`frontend/src/content/textos.ts:288`). |
| `risco.veredito` | a frase inteira (texto, sem ramo) — **exigida a expressão da D-64** | O veredito é por modelo e por nível: adequado quando passa no Kupiec **e** no Christoffersen, ambos a 5% de significância; não adequado quando falha em ao menos um; não julgado quando o cálculo do modelo falhou (nulo, não reprovação). DQ e Basileia são gravados e não entram. Os testes avaliam a série de VaR do período de teste inteiro, não o último ponto exibido — e a frase contém a expressão proposta abaixo para esta chave. | `backend/apps/risk/compute.py:432` a `backend/apps/risk/compute.py:442` (`None if error else (kupiec_passed and christoffersen_passed)`); `backend/apps/risk/compute.py:503` (gravado por linha, isto é, por modelo e nível); `engine/src/engine/backtesting/kupiec.py:39` e `engine/src/engine/backtesting/christoffersen.py:53` (`passed = p > 0,05`); `backend/apps/risk/config.py:22` (os quatro testes rodam); `engine/src/engine/experiments/runner.py:115` e `engine/src/engine/experiments/runner.py:116` (sobre a série alinhada do teste); `backend/apps/risk/compute.py:485` (o exibido é o último ponto) | Significância 0,05 (`engine/src/engine/backtesting/kupiec.py:14`, `engine/src/engine/backtesting/christoffersen.py:16`); período de teste = retornos após os 252 primeiros (`engine/src/engine/experiments/runner.py:88`). |
| `risco.naoRejeitados` | `k ≥ 1` — **exigida a expressão da D-64** | `k` dos `julgados` modelos têm veredito adequado neste nível (Kupiec e Christoffersen não rejeitaram a cobertura e a independência das violações na série de teste); a lista segue a ordem fixa dos nove, não o valor. Os testes falam do período de teste, não do `var_latest`. Os não julgados (erro) são contados à parte e não contam como reprovação. | `frontend/src/risk/summary.ts:47` a `frontend/src/risk/summary.ts:51` (`adequados` em `MODEL_ORDER`; `julgados` = `adequate` não nulo); `frontend/src/components/LossSummary.tsx:80` a `frontend/src/components/LossSummary.tsx:82` (`k`, `julgados`, 9); `frontend/src/content/textos.ts:303` a `frontend/src/content/textos.ts:307`; `frontend/src/content/textos.ts:294` a `frontend/src/content/textos.ts:297` (`faltam`); `backend/apps/risk/compute.py:442` | Nível do painel; total 9 (`frontend/src/api/types.ts:13`). |
| `risco.naoRejeitados` | `k = 0` — **exigida a expressão da D-64** | Todos os julgados neste nível foram rejeitados por ao menos um dos dois testes na série de teste. Fala do período de teste, não do número exibido hoje — e contém a mesma expressão do ramo `k ≥ 1`. | `frontend/src/risk/summary.ts:48` a `frontend/src/risk/summary.ts:51`; `frontend/src/content/textos.ts:301` e `frontend/src/content/textos.ts:302`; `backend/apps/risk/compute.py:442` (`False` quando um dos dois falha) | Nível do painel; `julgados de total` quando `faltam > 0` (`frontend/src/content/textos.ts:302`). |
| `risco.naoRejeitados` | `julgados = 0` — isento (não há veredito) | Nenhum modelo pôde ser julgado neste nível: o cálculo falhou em todos, e falha não é reprovação. | `frontend/src/risk/summary.ts:51` (`adequate` nulo não conta); `frontend/src/content/textos.ts:299` e `frontend/src/content/textos.ts:300`; `backend/apps/risk/compute.py:442` (`None` quando há erro) | — |
| `risco.violacoes` | `kupiecOk` verdadeiro | Violações são os dias do período de teste em que o retorno logarítmico ficou abaixo de −VaR; o esperado é `n · α`, com `n` os dias de teste. Os dois números vêm do Kupiec, sobre o período de teste inteiro (não os 250 dias da Basileia). | `engine/src/engine/backtesting/kupiec.py:29` e `engine/src/engine/backtesting/kupiec.py:30` (contagem); `engine/src/engine/backtesting/kupiec.py:41` e `engine/src/engine/backtesting/kupiec.py:42` (`violations`, `expected = n · α`); `backend/apps/risk/compute.py:461` a `backend/apps/risk/compute.py:463` e `backend/apps/risk/compute.py:490`, `backend/apps/risk/compute.py:491`; `frontend/src/components/ModelTable.tsx:147` e `frontend/src/components/ModelTable.tsx:148`; `frontend/src/content/textos.ts:339` | Violações inteiras; esperadas com 1 casa (`frontend/src/components/ModelTable.tsx:148`), guardadas a 6 (`backend/apps/risk/compute.py:104`); "1 dia a cada" 20/100. |
| `risco.violacoes` | `kupiecOk` falso | O mesmo, e: a contagem ficou longe o bastante de `n · α` para o Kupiec rejeitar — acima, o VaR subestimou a cauda; abaixo, superestimou. | `frontend/src/content/textos.ts:340` (o ramo); `frontend/src/components/ModelTable.tsx:161` (`kupiecOk` é o `kupiec_passed`); `engine/src/engine/backtesting/kupiec.py:39` | Idem. |
| `risco.kupiec` | `ok` verdadeiro / falso | Teste de proporção de falhas de Kupiec (1995): razão de verossimilhança entre a taxa de violações observada `x/n` e a esperada α, comparada a uma qui-quadrado com 1 grau de liberdade; testa a **cobertura incondicional**. Passa com p-valor acima de 0,05. | `engine/src/engine/backtesting/kupiec.py:1` e `engine/src/engine/backtesting/kupiec.py:2`; `engine/src/engine/backtesting/kupiec.py:17` a `engine/src/engine/backtesting/kupiec.py:21` (a razão); `engine/src/engine/backtesting/kupiec.py:33` (`chi2`, `df=1`); `engine/src/engine/backtesting/kupiec.py:39` (`p > 0,05`); `frontend/src/components/ModelTable.tsx:167` | p-valor com 3 casas, "< 0,001" abaixo disso (`frontend/src/components/ModelTable.tsx:25` a `frontend/src/components/ModelTable.tsx:27`); guardado a 10 casas (`backend/apps/risk/compute.py:493`). |
| `risco.christoffersen` | `ok` verdadeiro / falso | Teste de independência de Christoffersen (1998): uma cadeia de Markov de 1ª ordem sobre o indicador de violação compara a chance de violar depois de um dia violado com a de violar depois de um dia normal; qui-quadrado com 1 grau de liberdade. O p-valor mostrado é **o da independência** — a cobertura condicional (com 2 graus) é calculada pelo motor mas não é gravada nem mostrada. Passa com p-valor acima de 0,05. | `engine/src/engine/backtesting/christoffersen.py:1` a `engine/src/engine/backtesting/christoffersen.py:3`; `engine/src/engine/backtesting/christoffersen.py:25` a `engine/src/engine/backtesting/christoffersen.py:34` (as transições); `engine/src/engine/backtesting/christoffersen.py:43` e `engine/src/engine/backtesting/christoffersen.py:44` (`lr_ind`, `df=1`); `engine/src/engine/backtesting/christoffersen.py:46` e `engine/src/engine/backtesting/christoffersen.py:47` (o condicional só em `details`); `engine/src/engine/backtesting/christoffersen.py:53`; `backend/apps/risk/compute.py:497` e `backend/apps/risk/compute.py:498` (grava só o `p_value`) | 3 casas na tela; 10 guardadas (`backend/apps/risk/compute.py:498`). |
| `risco.dq` | `ok` verdadeiro / falso | Teste de quantil dinâmico de Engle e Manganelli (2004): regride o indicador de violação centrado em α sobre uma constante, as quatro violações anteriores e o próprio VaR do dia, e testa se os coeficientes são todos zero; qui-quadrado com 6 graus de liberdade. Pega ao mesmo tempo taxa errada e violações previsíveis. Passa com p-valor acima de 0,05. Gravado, fora do veredito. | `engine/src/engine/backtesting/dq.py:1` a `engine/src/engine/backtesting/dq.py:4`; `engine/src/engine/backtesting/dq.py:17` (4 defasagens); `engine/src/engine/backtesting/dq.py:25` (`hit − α`); `engine/src/engine/backtesting/dq.py:27` e `engine/src/engine/backtesting/dq.py:38` a `engine/src/engine/backtesting/dq.py:43` (os regressores); `engine/src/engine/backtesting/dq.py:46` e `engine/src/engine/backtesting/dq.py:47` (estatística, `df = 6`); `engine/src/engine/backtesting/dq.py:53`; `backend/apps/risk/compute.py:435` e `backend/apps/risk/compute.py:442` (fora do veredito) | 3 casas na tela; 10 guardadas (`backend/apps/risk/compute.py:501`). |

## A tabela do RF-08, conferida

| Chave | Ramo | Onde o ramo mora | Iniciante | Avançada |
|---|---|---|---|---|
| `risco.veredito` | a frase inteira (texto, sem ramo) | `frontend/src/content/textos.ts:331` | exigida — **cumpre hoje** com "não de quanto o número de hoje está certo" | exigida |
| `risco.naoRejeitados` | `k ≥ 1` | `frontend/src/content/textos.ts:303` a `frontend/src/content/textos.ts:307` | exigida — **cumpre hoje** com "não garante o número de hoje" | exigida |
| `risco.naoRejeitados` | `k = 0` | `frontend/src/content/textos.ts:301` e `frontend/src/content/textos.ts:302` | exigida — **não cumpre hoje**: fala do período de teste e não diz do número de hoje | exigida |
| `risco.naoRejeitados` | `julgados = 0` | `frontend/src/content/textos.ts:299` e `frontend/src/content/textos.ts:300` | isento | isento |

Os ramos são decididos pelos argumentos que `naoRejeitados` produz: `julgados` conta os `adequate` não nulos do nível
e `k` os `adequate = true`, em `MODEL_ORDER` (`frontend/src/risk/summary.ts:48` a `frontend/src/risk/summary.ts:51`).
O teste é feito na ordem `julgados = 0` antes de `k = 0` (`frontend/src/content/textos.ts:299`,
`frontend/src/content/textos.ts:301`), então `k = 0` só vale com ao menos um julgado.

## As duas expressões propostas da D-64

Uma expressão por chave, a mesma nos dois níveis e em todos os ramos exigidos daquela chave (RF-08). O portão da T9
aprova; o `d64.test.ts` da T10 as escreve literais.

**Proposta — a que menos muda a iniciante.** Cada chave fica com a expressão que a iniciante de hoje já usa; a única
iniciante que muda é o ramo `k = 0` de `risco.naoRejeitados`, o mínimo que o RF-08 exige.

1. **`risco.veredito`:** `não de quanto o número de hoje está certo`
   - iniciante: **sem mudança** (já contém, `frontend/src/content/textos.ts:332`);
   - avançada: contém a expressão, por exemplo "… os dois testes avaliam a série de VaR do período de teste, não o
     último valor exibido: falam do passado do modelo, não de quanto o número de hoje está certo."
2. **`risco.naoRejeitados`:** `não garante o número de hoje`
   - iniciante `k ≥ 1`: **sem mudança** (já contém, `frontend/src/content/textos.ts:307`);
   - iniciante `k = 0`: **muda** — ganha a expressão, por exemplo acrescentando, depois de "… no período de teste.":
     "Como o veredito, isso fala do período de teste e não garante o número de hoje, nem para mais nem para menos.";
   - avançada `k ≥ 1` e `k = 0`: contêm a expressão;
   - `julgados = 0`: isento nos dois níveis.

**Alternativa, se o portão preferir uma expressão só para as duas chaves:** `não do número de hoje` ("o veredito fala
do período de teste, não do número de hoje"). Lê bem nos três ramos exigidos, inclusive no `k = 0`, onde "não garante"
soa estranho; custa mudar as três iniciantes exigidas (`risco.veredito` e os dois ramos de `risco.naoRejeitados`), não
uma.

Nenhuma das duas usa palavra da varredura de vocabulário (melhor, melhores, recomendado e flexões, recomendamos,
confiável, confiáveis) nem sugere ação (D-153).

## O que não se ancora no código — não vai ao mockup como afirmação

- **"Sem olhar o dia testado" não vale para o GARCH(1,1) nem para o EGARCH.** A docstring diz que cada ponto só usa
  retornos até a véspera (`engine/src/engine/models/garch/_conditional.py:94`, `engine/src/engine/models/garch/_conditional.py:95`),
  mas a linha `n_train + pos` do `forecast` do `arch` é a previsão **feita com** o retorno daquele dia, para o dia
  seguinte, e ela é atribuída ao `sigma_1d[pos]`, que é comparado com o retorno do mesmo dia `pos`
  (`engine/src/engine/models/garch/_conditional.py:115` a `engine/src/engine/models/garch/_conditional.py:117`,
  `engine/src/engine/experiments/runner.py:110`). Conferido executando o `arch` do `.venv` sobre uma série
  sintética: a linha 250 de `forecast(start=250)` é igual a `ω + α·ε²₂₅₀ + β·σ²₂₅₀`, isto é, usa o retorno 250. As
  redes (`engine/src/engine/models/ml/_quantile_nn.py:213` a `engine/src/engine/models/ml/_quantile_nn.py:215`) e o
  CAViaR (`engine/src/engine/models/ml/caviar.py:31`) usam só até a véspera. Consequência para as frases: **nenhuma
  avançada afirma que todos os modelos preveem cada dia só com a véspera**; e o `var_latest` não tem a mesma data de
  referência em todas as famílias. Isto é um possível defeito do motor, fora da cerca desta tarefa — relatado, não
  corrigido.
- **"Os modelos usam o último ano" é falso para os três tradicionais**: o ajuste é só no primeiro ano da série
  (ver "O que cada família faz com o tempo"). Nenhuma frase das nove precisa dizer de que ano vem o VaR; se o mockup
  quiser dizer, tem de ser por família.
- **Os nomes e anos dos autores** (Kupiec 1995, Christoffersen 1998, Engle e Manganelli 2004) estão ancorados só nas
  docstrings (`engine/src/engine/backtesting/kupiec.py:1`, `engine/src/engine/backtesting/christoffersen.py:1`,
  `engine/src/engine/backtesting/dq.py:1`), não no cálculo. Podem ir à frase, mas a âncora é documental.
- **"Não sugere ação" e o tom de cada frase** não se conferem no código: são do portão (D-153).
