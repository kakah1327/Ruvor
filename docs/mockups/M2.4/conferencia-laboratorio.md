# M2.4 — Conferência técnica: laboratório (T8)

**Lista fechada proposta: N = 9 chaves `laboratorio.*` com frase nas duas leituras.**

Só leitura. Para cada chave nova com frase, o que a frase avançada vai afirmar e o `caminho:linha` em que cada
afirmação foi conferida, no código que calcula (spec, RF-16; plano, Tarefa 8). Os caminhos são relativos à raiz do
repositório. **Afirmação sem `caminho:linha` não vai ao mockup.** Conferido no ramo `marco1/M2.4-regime-de-laboratorio`,
HEAD `fbd9cb4` (a T7, com a T5 commitada), em 2026-10-04. `engine/` só lido. Os números de exemplo são os da foto real
da T7 (`docs/mockups/M2.4/lab-ITUB4.json`, `lab-IBOV.json`).

As nove chaves e a aridade proposta (a avançada repete a assinatura, D-151):

- `laboratorio.decada` — `(inicio, fim, anos, ultimo)`: a linha da década, no alto da seção;
- `laboratorio.diferenca` — `(versao, asOf)`: a diferença honesta (RF-15), **nas duas leituras**;
- `laboratorio.violacoesAno` — `(e, cadaN)`: a nota da grade, o que é o número de cada célula; `e` é o esperado num
  trecho cheio (12,6 a 95%, 2,5 a 99%);
- `laboratorio.vereditoAno` — `(celulas)`: a nota da grade de 95%; `celulas` = modelos sem erro × trechos julgados;
- `laboratorio.anoNaoJulgado` — `(n)`: a nota do trecho curto, só quando há um;
- `laboratorio.semVereditoAno99` — texto: a nota da grade de 99%, o porquê de não haver veredito por ano;
- `laboratorio.violacoesDecada` — `(v, e, cadaN, kupiecOk)`: por modelo e nível, no detalhe dos testes;
- `laboratorio.vereditoDecada` — texto: a nota da coluna "Década", nas duas grades;
- `laboratorio.anosNaoRejeitados` — texto: a nota da coluna "Anos não rejeitados" (o "k de N"), só a 95%.

## O que vale para todas as linhas

- **A série e a década.** A série é a de `silver.price` com o `adj_close` não nulo e maior que zero, em ordem de data
  (`backend/apps/risk/decade.py:28`, `backend/apps/risk/decade.py:33`); a produção usa a mesma lista — `compute._bars`
  devolve `valid_bars` (`backend/apps/risk/compute.py:301`). A década começa no primeiro pregão dessa série
  (`backend/apps/risk/decade.py:66`), termina na mesma data de calendário dez anos depois, com 29/02 → 28/02
  (`backend/apps/risk/decade.py:37` a `backend/apps/risk/decade.py:42`, `backend/apps/risk/decade.py:67`), e a série do
  experimento são os pregões com data ≤ fim (`backend/apps/risk/decade.py:69`). Completa com o último pregão ≥ fim
  (`backend/apps/risk/decade.py:74`); suficiente com ≥ 503 pregões (`backend/apps/risk/decade.py:55`,
  `backend/apps/risk/config.py:15`).
- **O mesmo cálculo da produção.** O experimento chama o mesmo `run_models` da produção, com `full=False`, sobre
  `decade.series` (`backend/apps/risk/lab.py:492`; a produção, `backend/apps/risk/compute.py:335`); `run_models` monta o
  experimento do motor com a janela da primeira à última data da lista que recebe
  (`backend/apps/risk/compute.py:400`, `backend/apps/risk/compute.py:401`) e os parâmetros de `config`: janela de 252
  (`backend/apps/risk/config.py:11`), níveis 0,05 e 0,01 (`backend/apps/risk/config.py:20`), os quatro testes
  (`backend/apps/risk/config.py:22`), semente fixa (`backend/apps/risk/config.py:10`). Os nove modelos
  (`backend/apps/risk/compute.py:82` a `backend/apps/risk/compute.py:92`).
- **Treino e teste.** O motor tira o retorno logarítmico diário (`engine/src/engine/data/preprocessing.py:15`,
  `engine/src/engine/data/preprocessing.py:21`); os primeiros 252 retornos são o treino e o resto, o período de teste
  (`engine/src/engine/experiments/runner.py:87`, `engine/src/engine/experiments/runner.py:88`). O laboratório refaz o
  mesmo corte para ler os anos (`backend/apps/risk/lab.py:185` a `backend/apps/risk/lab.py:194`) e o mesmo alinhamento
  do `runner` (`backend/apps/risk/lab.py:133`, `backend/apps/risk/lab.py:134`;
  `engine/src/engine/experiments/runner.py:110` a `engine/src/engine/experiments/runner.py:113`). O manifesto grava
  `test_count = pregões − 1 − 252` (`backend/apps/risk/compute.py:539`) e o `as_of_date`, o último pregão da série usada
  (`backend/apps/risk/compute.py:546`).
- **A violação.** Um dia viola quando o retorno logarítmico fica abaixo de −VaR, estritamente — no trecho
  (`backend/apps/risk/lab.py:140`) como na década (`engine/src/engine/backtesting/kupiec.py:29`).
- **Os trechos.** O teste alinhado se corta em trechos de `LAB_YEAR_DAYS = 252` a partir da posição 0
  (`backend/apps/risk/config.py:27`; `backend/apps/risk/lab.py:137` a `backend/apps/risk/lab.py:139`); o último pode ser
  mais curto (a fatia `iloc[start : start + 252]` para no fim). 252 é a cadência de reajuste dos nove modelos
  (`engine/src/engine/models/traditional/_expanding.py:18`, `engine/src/engine/models/garch/_conditional.py:39`,
  `engine/src/engine/models/ml/_quantile_nn.py:51`, `engine/src/engine/models/ml/caviar.py:21`), e os trechos são os
  intervalos entre dois reajustes, iguais para os nove. `year_count = ⌈test_count / 252⌉`
  (`backend/apps/risk/lab.py:412`).
- **Os testes por trecho.** Só nos níveis de `LAB_JUDGED_ALPHAS = (0.05,)` e só no trecho com pelo menos
  `LAB_YEAR_MIN_JUDGED = 126` retornos (`backend/apps/risk/config.py:28`, `backend/apps/risk/config.py:29`;
  `backend/apps/risk/lab.py:135`, `backend/apps/risk/lab.py:141`); são os mesmos testes do motor, chamados sobre o recorte
  (`backend/apps/risk/lab.py:142` a `backend/apps/risk/lab.py:145`). O veredito do trecho é Kupiec **e**
  Christoffersen, nulo sem eles (`backend/apps/risk/lab.py:117` a `backend/apps/risk/lab.py:121`). Os dois passam com
  p-valor acima de 0,05 (`engine/src/engine/backtesting/kupiec.py:14`, `engine/src/engine/backtesting/kupiec.py:39`,
  `engine/src/engine/backtesting/christoffersen.py:16`, `engine/src/engine/backtesting/christoffersen.py:53`).
- **A soma.** As violações dos trechos somam as da década, conferidas por (modelo, nível) antes de gravar; diferente,
  o experimento inteiro vira `failed`, sem resultado (`backend/apps/risk/lab.py:174` a `backend/apps/risk/lab.py:180`,
  `backend/apps/risk/lab.py:494`, `backend/apps/risk/lab.py:495`). Modelo com erro não tem trechos
  (`backend/apps/risk/lab.py:171`, `backend/apps/risk/lab.py:172`).
- **A identidade.** Um `ok` por (ativo, versão do motor, semente, janela, primeiro pregão, fim da década, impressão das
  versões das bibliotecas), restrição parcial só sobre `ok` (`backend/apps/risk/models.py:335` a
  `backend/apps/risk/models.py:345`; os campos, `backend/apps/risk/lab.py:213` a `backend/apps/risk/lab.py:223`; as
  versões lidas no processo, `backend/apps/risk/lab.py:226` a `backend/apps/risk/lab.py:238`); com o `ok` gravado, nada
  é recalculado nem gravado de novo (`backend/apps/risk/lab.py:278`, `backend/apps/risk/lab.py:404`,
  `backend/apps/risk/lab.py:405`). A impressão digital dos preços é gravada e **não** está na identidade
  (`backend/apps/risk/lab.py:413`, `backend/apps/risk/models.py:323`).

## A tabela

| Chave | Ramo | O que a frase avançada vai afirmar | Conferido em | Parâmetros lidos (janela, nível, casas) |
|---|---|---|---|---|
| `laboratorio.decada` | `ultimo < 252` / `ultimo = 252` | A década do ativo vai do primeiro pregão válido ao último pregão até dez anos de calendário depois (`inicio` = `first_price_date`, `fim` = `as_of_date`). Os primeiros 252 retornos são o treino; o resto, o teste, se corta em `anos` trechos de 252 retornos a partir do primeiro, os intervalos entre dois reajustes dos nove modelos, que reestimam todos a cada 252 pregões. Com `ultimo < 252`, o último trecho tem `ultimo` retornos. | **Início, fim e corte em ≤:** `backend/apps/risk/decade.py:66`, `backend/apps/risk/decade.py:67`, `backend/apps/risk/decade.py:69`, `backend/apps/risk/decade.py:37` a `backend/apps/risk/decade.py:42`; o `fim` exibido é o último pregão usado, `backend/apps/risk/compute.py:546`. **Treino de 252, o resto é teste:** `backend/apps/risk/config.py:11`, `engine/src/engine/experiments/runner.py:87`, `engine/src/engine/experiments/runner.py:88`, `backend/apps/risk/lab.py:194`. **Trechos de 252 a partir do primeiro:** `backend/apps/risk/config.py:27`, `backend/apps/risk/lab.py:137` a `backend/apps/risk/lab.py:139`. **`anos`:** `backend/apps/risk/lab.py:412`. **Os nove reestimam a cada 252:** `engine/src/engine/models/traditional/_expanding.py:18`, `engine/src/engine/models/garch/_conditional.py:39`, `engine/src/engine/models/ml/_quantile_nn.py:51`, `engine/src/engine/models/ml/caviar.py:21`. **`ultimo`:** o `test_count` do último trecho, `backend/apps/risk/lab.py:151`, que sai na rota (`backend/apps/api/serializers.py:534`, `backend/apps/api/serializers.py:535`). | ITUB4: 22/09/2016 a 22/09/2026, 9 anos, o último com 222; IBOV: idem, o último com 214 (foto da T7). Datas `dd/mm/aaaa`. |
| `laboratorio.diferenca` | a frase inteira — **nas duas leituras** (RF-15, D-187) | O laboratório é o cálculo da seção de risco — mesmos nove modelos, níveis, janela de treino, semente e testes, pela mesma rotina — recortado na década do ativo, até `asOf`, e gravado uma vez por versão do motor (`versao`), semente, janela e versões das bibliotecas. Nenhum modelo usa o retorno do próprio dia; por isso a série de VaR da década é o começo exato da série da seção de risco. Os vereditos podem diferir porque a seção de risco testa também os pregões depois de `asOf` e é refeita a cada dia útil. Enquanto o motor for o mesmo, o experimento não muda; com motor novo, é refeito e a trilha mostra a versão. Um reajuste de preço por provento depois do experimento não o refaz — a trilha guarda a impressão digital dos preços usados. Um veredito do passado não garante o comportamento do modelo daqui para a frente. | **Mesmo cálculo:** `backend/apps/risk/lab.py:492`, `backend/apps/risk/compute.py:335`, `backend/apps/risk/compute.py:400`, `backend/apps/risk/compute.py:401`, `backend/apps/risk/compute.py:301`. **Recortado na década:** `backend/apps/risk/decade.py:69`. **Gravado uma vez por identidade, sem recalcular:** `backend/apps/risk/models.py:335` a `backend/apps/risk/models.py:345`, `backend/apps/risk/lab.py:213` a `backend/apps/risk/lab.py:223`, `backend/apps/risk/lab.py:278`, `backend/apps/risk/lab.py:404`. **Motor novo, experimento novo:** a versão está na identidade (`backend/apps/risk/lab.py:231`), o fecho do risco pergunta se é devido e enfileira (`backend/apps/risk/tasks.py:536`, `backend/apps/risk/tasks.py:537`, `backend/apps/risk/tasks.py:550`, `backend/apps/risk/tasks.py:551`); a rota mostra o mais recente de qualquer versão (`backend/apps/api/views.py:742` a `backend/apps/api/views.py:754`). **Nenhum modelo usa o retorno do dia:** `engine/src/engine/models/base.py:64` a `engine/src/engine/models/base.py:66`; por teste, `engine/tests/test_sem_olhar_a_frente.py:115`. **A década é o começo da série inteira:** `backend/tests/risk/test_lab_calculo.py:95`, `backend/tests/risk/test_lab_calculo.py:117`, `backend/tests/risk/test_lab_calculo.py:118` (os seis não neurais), e a T7 nos 18 pares do ITUB4 (ver "O que não se ancora"). **A seção de risco vai até o último pregão e é refeita a cada dia útil:** `backend/apps/risk/compute.py:401`; `backend/config/settings.py:203`, `backend/config/settings.py:204` (`30 19 * * 1-5`), `backend/apps/assets/tasks.py:96` a `backend/apps/assets/tasks.py:106`. **A impressão digital gravada, fora da identidade:** `backend/apps/risk/lab.py:413`, `backend/apps/risk/models.py:323`. | `versao` = `latest.engine_version` (`0.4.0` na foto); `asOf` = `latest.as_of_date` (22/09/2026). |
| `laboratorio.violacoesAno` | a nota da grade, por nível | Cada número da grade é a quantidade de violações no trecho — dias em que o retorno logarítmico ficou abaixo de −VaR do dia —; o esperado é a contagem do trecho vezes α: `e` num trecho cheio de 252, 1 dia a cada `cadaN`. A soma dos trechos é a violação da década, conferida antes de gravar. | **A violação no trecho:** `backend/apps/risk/lab.py:140`. **Esperadas = contagem × α:** `backend/apps/risk/lab.py:153`. **Trecho cheio de 252:** `backend/apps/risk/config.py:27`. **A soma conferida:** `backend/apps/risk/lab.py:174` a `backend/apps/risk/lab.py:180`. **α:** `backend/apps/risk/config.py:20`. | `e` = 12,6 (252 × 0,05) ou 2,5 (252 × 0,01), 1 casa; `cadaN` 20 ou 100; esperadas guardadas a 6 casas (`backend/apps/risk/lab.py:342`). |
| `laboratorio.vereditoAno` | a nota da grade de 95% | Veredito do trecho, só a 95%: adequado quando nem o Kupiec nem o Christoffersen rejeitam, os dois com p-valor acima de 0,05, sobre os retornos e o VaR daquele trecho; não adequado quando ao menos um rejeita. São `celulas` células julgadas e, num modelo correto, cada uma tem perto de 10% de chance de sair não adequada só por acaso (dois testes a 5%) — com 81, quase uma rejeição em nove sem defeito nenhum. O veredito que resume o modelo é o da década. | **Só a 95%:** `backend/apps/risk/config.py:29`, `backend/apps/risk/lab.py:135`, `backend/apps/risk/lab.py:141`. **Os dois testes sobre o recorte:** `backend/apps/risk/lab.py:142` a `backend/apps/risk/lab.py:145`. **Kupiec e Christoffersen:** `backend/apps/risk/lab.py:117` a `backend/apps/risk/lab.py:121`. **p > 0,05:** `engine/src/engine/backtesting/kupiec.py:14`, `engine/src/engine/backtesting/kupiec.py:39`, `engine/src/engine/backtesting/christoffersen.py:16`, `engine/src/engine/backtesting/christoffersen.py:53`. **81 = 9 × 9:** `backend/apps/risk/compute.py:82` a `backend/apps/risk/compute.py:92`, `backend/apps/risk/lab.py:412` (9 trechos na foto). **Os "perto de 10%":** ver "O que não se ancora". | Significância 0,05; `celulas` contado na tela (resultados sem erro a 95% × trechos com `adequate` não nulo). |
| `laboratorio.anoNaoJulgado` | só com um trecho de menos de 126 | Trecho de `n` retornos, abaixo do piso de 126 (meio ano de teste): as violações e as esperadas são gravadas; o Kupiec, o Christoffersen e o veredito ficam nulos. | `backend/apps/risk/config.py:28`, `backend/apps/risk/lab.py:141`, `backend/apps/risk/lab.py:142` a `backend/apps/risk/lab.py:145` (sem julgamento, `None`), `backend/apps/risk/lab.py:117` a `backend/apps/risk/lab.py:120` (veredito nulo), `backend/apps/risk/lab.py:151` a `backend/apps/risk/lab.py:153` (contagem, violações e esperadas gravadas). | Piso 126; não ocorre nas décadas de hoje (último trecho de 214 a 222) — no mockup, caso fictício. |
| `laboratorio.semVereditoAno99` | a nota da grade de 99% | Sem veredito por trecho a 99%: num trecho de 252 esperam-se 2,52 violações, e o Kupiec rejeita até o trecho sem nenhuma — com zero violações, a estatística é −2·n·ln(0,99), acima do valor crítico 3,84 a partir de 192 retornos (p ≈ 0,024 em 252). O teste por trecho quase não distingue nada nesse nível; os testes e o veredito a 99% ficam só na década, e os p-valores por trecho não são calculados. | **Só a 95% por trecho:** `backend/apps/risk/config.py:29`, `backend/apps/risk/lab.py:135`, `backend/apps/risk/lab.py:141` a `backend/apps/risk/lab.py:145`. **A estatística do Kupiec:** `engine/src/engine/backtesting/kupiec.py:17` a `engine/src/engine/backtesting/kupiec.py:21` (com x = 0, o termo de x some e sobra `−2·(n·ln(1 − α) − 0)`), `engine/src/engine/backtesting/kupiec.py:33` (qui-quadrado, 1 grau), `engine/src/engine/backtesting/kupiec.py:39`. **Esperadas 2,52:** `backend/apps/risk/lab.py:153`. **O veredito a 99% na década:** `backend/apps/risk/lab.py:327`, `backend/apps/risk/compute.py:430` a `backend/apps/risk/compute.py:440`. **Os 192 e o p de 0,024:** ver "O que não se ancora" (conta sobre a fórmula). | α = 0,01; 252 × 0,01 = 2,52. |
| `laboratorio.violacoesDecada` | `kupiecOk` verdadeiro / falso | `v` violações em todo o período de teste da década, a soma dos trechos, para `e` esperadas, os dias de teste divididos por `cadaN`; são as do Kupiec da década, sobre a série de VaR inteira. Com `kupiecOk` falso: longe o bastante do esperado para o Kupiec rejeitar — acima, o VaR subestimou a cauda; abaixo, superestimou. | **As do Kupiec da década:** `backend/apps/risk/lab.py:304`, `backend/apps/risk/lab.py:314` a `backend/apps/risk/lab.py:316`; `engine/src/engine/backtesting/kupiec.py:29`, `engine/src/engine/backtesting/kupiec.py:30`, `engine/src/engine/backtesting/kupiec.py:41`, `engine/src/engine/backtesting/kupiec.py:42`. **A soma dos trechos:** `backend/apps/risk/lab.py:174` a `backend/apps/risk/lab.py:180`. **`kupiecOk`:** `backend/apps/risk/lab.py:317`, `engine/src/engine/backtesting/kupiec.py:39`. | Violações inteiras; esperadas 1 casa (111,9 e 22,4 no ITUB4); guardadas a 6 casas (`backend/apps/risk/lab.py:316`). |
| `laboratorio.vereditoDecada` | a frase inteira (texto) | Veredito da década, nos dois níveis: adequado quando nem o Kupiec nem o Christoffersen rejeitam, os dois com p-valor acima de 0,05, sobre a série de VaR do período de teste inteiro da década; não adequado quando ao menos um rejeita; nulo quando o cálculo do modelo falhou, o que não é reprovação. O DQ é mostrado e fica fora; a zona de Basileia não é gravada no laboratório. Fala do passado do modelo, não do número de hoje. | **O par, nulo com erro:** `backend/apps/risk/lab.py:327`, `backend/apps/risk/compute.py:430` a `backend/apps/risk/compute.py:440`. **p > 0,05:** `engine/src/engine/backtesting/kupiec.py:39`, `engine/src/engine/backtesting/christoffersen.py:53`. **Sobre o teste inteiro:** `engine/src/engine/experiments/runner.py:110` a `engine/src/engine/experiments/runner.py:113`. **O DQ gravado, fora do veredito:** `backend/apps/risk/lab.py:306`, `backend/apps/risk/lab.py:325`, `backend/apps/risk/lab.py:326`, `backend/apps/risk/models.py:386`. **Sem Basileia:** `backend/apps/risk/lab.py:296` a `backend/apps/risk/lab.py:300` (o docstring de `_result_row`: `basel_zone` não existe aqui), `backend/apps/risk/models.py:360`. | Significância 0,05; os dois níveis. |
| `laboratorio.anosNaoRejeitados` | a nota da coluna, só a 95% | Para cada modelo, em quantos dos trechos julgados a 95% nem o Kupiec nem o Christoffersen rejeitaram ("k de N"); N conta só os trechos julgados, sem os curtos. Com perto de 10% de chance de rejeição por acaso em cada trecho, um modelo correto fica perto de 8 de 9. A contagem descreve cada modelo e não ordena os nove: a grade segue a ordem fixa. | **Julgados e adequados por trecho:** `backend/apps/risk/lab.py:117` a `backend/apps/risk/lab.py:121` (nulo no não julgado), `backend/apps/risk/lab.py:141`. **Só a 95%:** `backend/apps/risk/config.py:29`. **A ordem fixa:** `frontend/src/api/types.ts:13`. **Os "perto de 10%" e "perto de 8 de 9":** ver "O que não se ancora". | k e N inteiros, contados na tela sobre `years[].adequate`. |

## As reaproveitadas

Entram na seção sem mudar uma letra; as frases que já têm avançada seguem conferidas em
`docs/mockups/M2.3/conferencia-risco.md`.

| Chave | Onde na seção | Por que serve sem mudar |
|---|---|---|
| reaproveitada: risco.modelo.* (as nove) | a coluna dos modelos das duas grades e o detalhe dos testes | os mesmos nove nomes |
| reaproveitada: risco.categoria.* (as três) | a linha de baixo do nome, como na tabela do risco | as mesmas famílias |
| reaproveitada: risco.tag.adequado, risco.tag.naoAdequado, risco.tag.naoJulgado | o veredito do trecho (95%) e o da década; "não julgado" só com erro do modelo | o mesmo veredito, com rótulo — nunca só cor |
| reaproveitada: risco.erroModelo | a linha do modelo com erro, nas duas grades e no detalhe | o erro é do (modelo, nível), como no risco (`backend/apps/risk/lab.py:302` a `backend/apps/risk/lab.py:306`) |
| reaproveitada: risco.nivel.0.0500, risco.nivel.0.0100 | o título de cada grade | os mesmos níveis |
| reaproveitada: risco.kupiec, risco.christoffersen, risco.dq (com frase, as duas leituras) | os p-valores da década, no detalhe dos testes, recolhido na iniciante | descrevem o teste e o p-valor, sem dizer de que período; servem para a década sem mudar |
| reaproveitada: risco.rotulo.violacoes, risco.rotulo.kupiec, risco.rotulo.christoffersen, risco.rotulo.dq, risco.teste.passou, risco.teste.naoPassou | o detalhe dos testes | os mesmos rótulos |
| reaproveitada: risco.tabela.col.modelo | o cabeçalho da coluna dos modelos | idem |
| reaproveitada: risco.trilha.* (os rótulos, `instante`, `pregoes`, `coleta`, `fonte.yahoo-chart`, `status.ok`, `status.partial`) | a trilha do experimento | o manifesto do laboratório tem as mesmas colunas do da produção (`backend/apps/risk/lab.py:394`) |
| reaproveitada: ativo.erroSecao, ativo.tentarDeNovo | o estado 2 (erro da leitura) | o `SectionError` das outras seções |

**Não reaproveitada: `risco.veredito`** (o plano a lista entre as candidatas). A seção precisa de dois vereditos
distintos — o do trecho, só a 95%, e o da década — e a frase de `risco.veredito` fala de "o período de teste" sem
dizer qual; as duas chaves novas, `laboratorio.vereditoAno` e `laboratorio.vereditoDecada`, dizem. O portão decide.

## As frases de estado, as notas e os rótulos (uma leitura só, fora da lista fechada)

Não são número de análise: a mesma frase nas duas leituras (como `risco.estado.*`). O texto proposto está no mockup.

| Chave | Estado do RF-14 · onde | O que afirma | Conferido em |
|---|---|---|---|
| laboratorio.carregando | 1 · só para leitor de tela, com o esqueleto | carregando | — |
| (ativo.erroSecao, ativo.tentarDeNovo) | 2 · erro da leitura | reaproveitadas | — |
| laboratorio.estado.falhou.titulo, laboratorio.estado.falhou (data) | 4 · `latest` nulo, `last_failure` | a tentativa daquela data não chegou a resultado | `backend/apps/api/views.py:755` a `backend/apps/api/views.py:758` |
| laboratorio.estado.tentaDeNovo | 4 e nota (a) · **só com o ativo `active`** | tentado de novo depois do próximo cálculo do risco | `backend/apps/risk/lab.py:278` (`failed` não tira o devido), `backend/apps/risk/tasks.py:536` a `backend/apps/risk/tasks.py:551`; só ativo ativo é recalculado, `backend/apps/risk/tasks.py:578` a `backend/apps/risk/tasks.py:587`, `backend/apps/risk/compute.py:275` |
| laboratorio.estado.aCalcular.titulo, laboratorio.estado.aCalcular | 5 · `pending` | devido; roda depois do próximo cálculo do risco deste ativo; aparece ao recarregar — **sem "logo"** | `backend/apps/api/views.py:704` a `backend/apps/api/views.py:729`; `backend/apps/risk/tasks.py:550`, `backend/apps/risk/tasks.py:551` |
| laboratorio.estado.inativo.titulo, laboratorio.estado.inativo | 6 · `active` falso | o laboratório não roda para ativo inativo | `backend/apps/risk/lab.py:267`, `backend/apps/risk/lab.py:268` |
| laboratorio.estado.semDecada.titulo, laboratorio.estado.semDecada (inicio, fim) | 7 · incompleta, com preço | o primeiro pregão e a data em que a década completa | `backend/apps/risk/decade.py:67`, `backend/apps/risk/decade.py:74` |
| laboratorio.estado.serieCurta.titulo, laboratorio.estado.serieCurta (n, min) | 8 · completa e curta | os pregões da década e o mínimo | `backend/apps/risk/decade.py:55`, `backend/apps/risk/config.py:15`, `frontend/src/risk/config.ts:8` |
| laboratorio.estado.semRisco.titulo, laboratorio.estado.semRisco | 9 · sem preço ou sem risco | vem depois do primeiro cálculo do risco; o pedido é o da seção acima — **sem botão** | `backend/apps/api/views.py:759` a `backend/apps/api/views.py:764` |
| laboratorio.nota.falha (data) | 3, nota (a) · `last_failure` posterior ao `latest` | a tentativa mais recente falhou; os números são os do experimento anterior | `backend/apps/api/views.py:755` a `backend/apps/api/views.py:758` |
| laboratorio.nota.motor (antigo, novo) | 3, nota (b) · outro motor, **só com o ativo `active`** | o literal do RF-14: "este experimento é do motor {antigo}; o do motor {novo} roda depois do próximo cálculo do risco" | `backend/apps/risk/lab.py:231`, `backend/apps/api/views.py:759` a `backend/apps/api/views.py:764` |
| laboratorio.nota.parcial (n), laboratorio.nota.refeito | 3, nota (c) · `partial` do mesmo motor; o "refeito" só com `active` | quantos modelos ficaram sem resultado; refeito depois do próximo cálculo do risco | `backend/apps/risk/lab.py:531` a `backend/apps/risk/lab.py:534`, `backend/apps/risk/lab.py:278` |

Os títulos e rótulos novos, sem afirmação técnica: `laboratorio.sobrancelha`, `laboratorio.titulo` (proposta da spec,
"Como os modelos se saíram em dez anos"), `laboratorio.intro`, `laboratorio.grade.titulo.0.0500`,
`laboratorio.grade.titulo.0.0100`, `laboratorio.grade.ano`, `laboratorio.grade.periodo`, `laboratorio.grade.esperadas`,
`laboratorio.grade.col.decada`, `laboratorio.grade.col.anos`, `laboratorio.grade.kDeN`, `laboratorio.tag.anoCurto` (o
rótulo próprio do trecho não julgado, RF-15), `laboratorio.testes.abrir`, `laboratorio.testes.porAno`,
`laboratorio.testes.col.ano`, `laboratorio.testes.col.veredito`, `laboratorio.trilha.titulo`, `laboratorio.trilha`,
`laboratorio.trilha.abrir`, `laboratorio.trilha.decadeEnd`, `laboratorio.trilha.years`, `laboratorio.trilha.origin`,
`laboratorio.trilha.origin.risk_close`, `laboratorio.trilha.origin.command`, `laboratorio.trilha.snapshots`,
`laboratorio.trilha.retratos`, `laboratorio.trilha.fingerprint`. A tabela de todos os textos, com os exemplos, está no
mockup (vista "os textos").

## O que não se ancora no código — vai ao mockup só como está aqui

- **"Perto de 10% por trecho" e "quase uma rejeição em nove"** (`laboratorio.vereditoAno`,
  `laboratorio.anosNaoRejeitados`). É estatística, não código: com dois testes a 5%, a chance de ao menos uma rejeição
  num modelo correto é perto de 1 − 0,95² ≈ 9,75%, supondo os dois independentes e no tamanho nominal. O Kupiec é
  discreto e o tamanho real dele num trecho de 252 a 95% é 5,9% (a soma das probabilidades binomiais das contagens que
  ele rejeita, calculada com a mesma fórmula de `engine/src/engine/backtesting/kupiec.py:17` a
  `engine/src/engine/backtesting/kupiec.py:21`, em 2026-10-04, fora do repositório); por isso a frase diz "perto de", e
  "perto de 8 de 9" (9 × 0,9 ≈ 8,1). Vem da spec (RF-16, D-184), aprovada.
- **Os 192 retornos e o p ≈ 0,024** (`laboratorio.semVereditoAno99`). Conta sobre a fórmula do Kupiec com x = 0:
  −2·n·ln(0,99) passa de 3,8415 (o crítico da qui-quadrado de 1 grau a 5%) a partir de n = 192 (190 → p = 0,0507;
  191 → 0,0501; 192 → 0,0495; 252 → 0,0244), calculado com `scipy` em 2026-10-04. A spec e o plano dizem "~190 ou
  mais"; a frase usa o número exato.
- **O prefixo nas três redes** (`laboratorio.diferenca`). O teste do backend prova a igualdade ponto a ponto nos seis
  não neurais (`backend/tests/risk/test_lab_calculo.py:95`); as três redes, pela execução real da T7 (o ITUB4, 18
  pares, `n = 2238`, diferença máxima 0,0 — "Correções registradas" do plano, T7, passo 4). A frase afirma o prefixo
  para os nove: medido, não provado por teste de unidade.
- **"Refeita a cada dia útil"**: o agendamento padrão (`30 19 * * 1-5`) da `rotina_diaria`; a variável
  `RUVOR_BEAT_PRICES_CRON` pode mudá-lo, e o Beat pode estar parado. A frase diz o desenho, como a de `risco.estado.E3`.
- **"Um veredito do passado não garante o comportamento daqui para a frente"** e o tom de cada frase não se conferem no
  código: são do portão (D-153, RF-17).
