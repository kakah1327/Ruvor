# M2.3 — Conferência técnica: fundamentos (T11)

As 19 chaves `fundamentos.*` e as 3 dos pares do RF-04 da spec, conferidas no código que calcula
(RF-05): `backend/apps/fundamentals/` — `conform.py` (as contas, o trimestre isolado, as ações),
`indicators.py` (os indicadores e a capitalização), `compute.py` (o preço, os tickers de classe, a
segunda fase) e `peers.py` (o grupo, a mediana, o percentil) —, e o que a tela deriva em
`frontend/src/components/FundamentalsSection.tsx`. Decisões: D-122 (conta pela descrição, plano de
contas, dívida com arrendamento), D-123 (trimestre isolado, 4º trimestre, 12 meses por soma),
D-124 (capitalização por classe, escala das ações inferida pelo LPA) e D-132 (pares pela tupla,
percentil).

**Caso: PETR4**, lido da API local em 2026-10-01 (`GET /api/v1/assets/PETR4/fundamentals`, a linha
de maior `calculated_at`, `backend/apps/api/views.py:359`): cálculo de 2026-09-28 08:02, balanço
ITR de 30/06/2026, consolidado, plano `general`; receita 12m R$ 548.493 mi, EBIT 12m R$ 185.746 mi,
lucro 12m R$ 133.376 mi, PL R$ 480.950 mi, ativo R$ 1.279.019 mi, dívida bruta R$ 366.533 mi, caixa
R$ 53.764 mi, dívida líquida R$ 312.769 mi; margem líquida 0,2432, margem EBIT 0,3386, ROE 0,2773,
dívida líquida/PL 0,6503; preço de 25/09/2026, R$ 48,07; 12.888.732.761 ações; LPA 10,348263, VPA
37,315538, P/L 4,645224, P/VP 1,288203; **valor de mercado nulo** (`missing_class_price`). Pares no
segmento "Exploração. Refino e Distribuição": ROE no percentil 1,0000 de 7, margem líquida e EBIT
1,0000 de 8, dívida líquida/PL 0,5000 de 7; P/L e P/VP sem comparação. A identidade traz o último
pregão em 01/10/2026 — então o PETR4 cai em `closeOutraData`, não em `close`.

Todo valor em reais é o `VL_CONTA` vezes a `ESCALA_MOEDA` (`MIL` × 1000, `UNIDADE` × 1)
(`backend/apps/fundamentals/conform.py:33`, `backend/apps/fundamentals/conform.py:407`). Os
números de balanço (PL, ativo, dívida, caixa) são a posição do **balanço mais recente** da
companhia (`backend/apps/fundamentals/indicators.py:238`, `backend/apps/fundamentals/compute.py:236`).
Os de resultado "12 meses" são a **soma dos quatro balanços mais recentes**, cada um com o trimestre
isolado, quando os quatro estão no mesmo escopo e cada intervalo entre datas tem de 88 a 93 dias;
senão, nulo — não se procura outra janela mais antiga
(`backend/apps/fundamentals/indicators.py:154`, `backend/apps/fundamentals/indicators.py:217`).
O trimestre isolado do ITR é o valor de maior `DT_INI_EXERC`
(`backend/apps/fundamentals/conform.py:529`); o 4º trimestre é o anual do DFP menos o acumulado do
ITR do mesmo exercício com a data imediatamente anterior, a 88–93 dias, no mesmo escopo
(`backend/apps/fundamentals/conform.py:543`, `backend/apps/fundamentals/conform.py:560`); ITR na
mesma data de um DFP é descartado (`backend/apps/fundamentals/conform.py:493`). O escopo é o
consolidado quando o documento o tem, senão o individual (`backend/apps/fundamentals/conform.py:297`).

| Chave | Ramo | O que a frase avançada vai afirmar | Conferido em | Parâmetros lidos (janela, anualização, nível, casas) |
|---|---|---|---|---|
| `fundamentos.revenue_ttm` | texto | A conta 3.01 da DRE (localizada por código), somada nos quatro últimos trimestres isolados; só no plano `general` — banco, seguradora e plano desconhecido saem nulos. | backend/apps/fundamentals/conform.py:45, backend/apps/fundamentals/conform.py:182, backend/apps/fundamentals/indicators.py:245, backend/apps/fundamentals/indicators.py:217, backend/apps/fundamentals/conform.py:316 | 12 meses = 4 trimestres consecutivos (88–93 dias, mesmo escopo); reais, 2 casas (`backend/apps/fundamentals/indicators.py:36`) |
| `fundamentos.ebit_ttm` | `negativo = false` | A conta "Resultado Antes do Resultado Financeiro e dos Tributos" da DRE (pela descrição, D-122), somada nos quatro últimos trimestres isolados; só no plano `general`. | backend/apps/fundamentals/conform.py:114, backend/apps/fundamentals/conform.py:183, backend/apps/fundamentals/indicators.py:246 | 12 meses; reais, 2 casas |
| `fundamentos.ebit_ttm` | `negativo = true` | A mesma soma de quatro trimestres, abaixo de zero: o resultado antes do financeiro e dos tributos foi negativo nos 12 meses. | backend/apps/fundamentals/indicators.py:246, frontend/src/components/FundamentalsSection.tsx:126, frontend/src/components/FundamentalsSection.tsx:144 | ramo pelo sinal do valor gravado |
| `fundamentos.net_income_ttm` | `negativo = false` | O lucro atribuído aos sócios da controladora (no consolidado, a filha "Atribuído a/aos Sócios da Empresa Controladora" do lucro consolidado; no individual, o lucro do período), somado nos quatro últimos trimestres isolados; vale em todo plano de contas. | backend/apps/fundamentals/conform.py:115, backend/apps/fundamentals/conform.py:121, backend/apps/fundamentals/conform.py:184, backend/apps/fundamentals/conform.py:191, backend/apps/fundamentals/indicators.py:247 | 12 meses; reais, 2 casas; sem filtro de plano |
| `fundamentos.net_income_ttm` | `negativo = true` | A mesma soma, abaixo de zero: prejuízo atribuído à controladora nos 12 meses. | backend/apps/fundamentals/indicators.py:247, frontend/src/components/FundamentalsSection.tsx:144 | ramo pelo sinal |
| `fundamentos.net_margin` | `negativo = false` | O lucro de 12 meses da controladora dividido pela receita de 12 meses; nulo com receita nula ou não positiva. A tela mostra em porcentagem, uma casa, e a frase usa o valor × 100 em reais. | backend/apps/fundamentals/indicators.py:254, backend/apps/fundamentals/indicators.py:255, frontend/src/components/FundamentalsSection.tsx:92, frontend/src/components/FundamentalsSection.tsx:115, frontend/src/components/FundamentalsSection.tsx:149 | razão, 10 casas no banco (`backend/apps/fundamentals/indicators.py:37`); exibida a 1 casa de % |
| `fundamentos.net_margin` | `negativo = true` | A mesma razão, negativa porque o lucro de 12 meses é prejuízo (a receita é sempre positiva quando há margem). | backend/apps/fundamentals/indicators.py:254, frontend/src/components/FundamentalsSection.tsx:115 | a frase recebe o módulo (`Math.abs`); o ramo diz o sinal |
| `fundamentos.ebit_margin` | `negativo = false` | O EBIT de 12 meses dividido pela receita de 12 meses; nulo com receita não positiva; só no plano `general`. | backend/apps/fundamentals/indicators.py:260, frontend/src/components/FundamentalsSection.tsx:149 | razão, 10 casas; exibida a 1 casa de % |
| `fundamentos.ebit_margin` | `negativo = true` | A mesma razão, negativa porque o EBIT de 12 meses é negativo. | backend/apps/fundamentals/indicators.py:260, frontend/src/components/FundamentalsSection.tsx:115 | módulo na frase |
| `fundamentos.roe` | `negativo = false` | O lucro de 12 meses da controladora dividido pelo patrimônio da controladora **na data do balanço mais recente** (não a média do período); nulo com patrimônio nulo ou não positivo. | backend/apps/fundamentals/indicators.py:248, backend/apps/fundamentals/indicators.py:265, frontend/src/components/FundamentalsSection.tsx:149 | numerador 12 meses, denominador posição na data; razão, 10 casas; exibida a 1 casa de % |
| `fundamentos.roe` | `negativo = true` | A mesma razão, negativa porque o lucro de 12 meses é prejuízo (o patrimônio é sempre positivo quando há ROE). | backend/apps/fundamentals/indicators.py:265, frontend/src/components/FundamentalsSection.tsx:115 | módulo na frase |
| `fundamentos.gross_debt` | texto | A soma das filhas diretas fixas "Empréstimos e Financiamentos" do Passivo Circulante e do Passivo Não Circulante, na data do balanço; inclui o arrendamento (D-122); só no plano `general`. No PETR4, 2T26: R$ 366.533 mi. | backend/apps/fundamentals/conform.py:108, backend/apps/fundamentals/conform.py:110, backend/apps/fundamentals/conform.py:165, backend/apps/fundamentals/indicators.py:249 | posição na data; reais, 2 casas |
| `fundamentos.cash` | texto | A soma das filhas diretas fixas "Caixa e Equivalentes de Caixa" e "Aplicações Financeiras" do **Ativo Circulante** (a aplicação de longo prazo não entra), na data do balanço; só no plano `general`. | backend/apps/fundamentals/conform.py:105, backend/apps/fundamentals/conform.py:156, backend/apps/fundamentals/indicators.py:250 | posição na data; reais, 2 casas |
| `fundamentos.net_debt` | `negativo = false` | A dívida bruta menos o caixa e aplicações, na data do balanço; nula se um dos dois é nulo. | backend/apps/fundamentals/indicators.py:251 | posição na data; reais, 2 casas |
| `fundamentos.net_debt` | `negativo = true` | Negativa quando o caixa e aplicações do circulante passam da dívida bruta. | backend/apps/fundamentals/indicators.py:251, frontend/src/components/FundamentalsSection.tsx:144 | ramo pelo sinal |
| `fundamentos.net_debt_to_equity` | `negativo = false` | A dívida líquida dividida pelo patrimônio da controladora, os dois na data do balanço; nula com patrimônio não positivo. | backend/apps/fundamentals/indicators.py:270, frontend/src/components/FundamentalsSection.tsx:149 | razão, 10 casas; exibida a 1 casa de % |
| `fundamentos.net_debt_to_equity` | `negativo = true` | Negativa porque a dívida líquida é negativa (o patrimônio é sempre positivo quando há razão). | backend/apps/fundamentals/indicators.py:270, frontend/src/components/FundamentalsSection.tsx:115 | módulo na frase |
| `fundamentos.close` | `price_date` não anterior ao último pregão da identidade | O `close` do pregão (o fechamento da cotação do Yahoo, não o `adj_close`), o último com data entre 10 dias corridos antes da data local do cálculo e ela; é o preço que entra no P/L e no P/VP. | backend/apps/fundamentals/compute.py:60, backend/apps/fundamentals/compute.py:264, backend/apps/assets/conform_prices.py:93, backend/apps/fundamentals/indicators.py:288, frontend/src/components/FundamentalsSection.tsx:152 | janela de 10 dias corridos; data local de `calculated_at` (`backend/apps/fundamentals/compute.py:196`, fuso `backend/config/settings.py:234`); 6 casas |
| `fundamentos.closeOutraData` | `price_date` anterior ao último pregão da identidade | O mesmo `close` da janela de 10 dias, de um pregão anterior ao último coletado, porque o cálculo roda por agenda semanal (padrão: segunda, 8h, configurável) e não a cada pregão. No PETR4: 25/09/2026 contra 01/10/2026. | frontend/src/components/FundamentalsSection.tsx:152, frontend/src/components/FundamentalsSection.tsx:412, backend/apps/fundamentals/compute.py:264, backend/config/settings.py:206 | janela de 10 dias; agenda `RUVOR_BEAT_FUNDAMENTALS_CRON`, padrão `0 8 * * 1` |
| `fundamentos.eps` | `negativo = false` | O lucro de 12 meses da controladora dividido pela soma das ações ON e PN do balanço mais recente, cada classe já descontadas as em tesouraria, na escala inferida pelo LPA que a própria companhia informa (unidades ou milhares, aceita só dentro de um fator 2, D-124); a CVM só informa a quantidade de 2020 em diante. | backend/apps/fundamentals/indicators.py:275, backend/apps/fundamentals/indicators.py:278, backend/apps/fundamentals/conform.py:617, backend/apps/fundamentals/conform.py:632, backend/apps/fundamentals/conform.py:514 | numerador 12 meses, ações na data; 6 casas (`backend/apps/fundamentals/indicators.py:38`) |
| `fundamentos.eps` | `negativo = true` | O mesmo quociente, negativo porque o lucro de 12 meses é prejuízo. | backend/apps/fundamentals/indicators.py:278, frontend/src/components/FundamentalsSection.tsx:158 | ramo pelo sinal |
| `fundamentos.bvps` | texto-função (sem ramo) | O patrimônio da controladora na data do balanço dividido pela mesma soma de ações ON e PN, líquidas de tesouraria. | backend/apps/fundamentals/indicators.py:283, frontend/src/components/FundamentalsSection.tsx:160 | posição na data; 6 casas |
| `fundamentos.pe` | `negativo = false` | O `close` da janela de 10 dias dividido pelo LPA de 12 meses; nulo com LPA zero ou nulo. A frase mostra uma casa; o número em destaque, duas. | backend/apps/fundamentals/indicators.py:290, frontend/src/components/FundamentalsSection.tsx:161, frontend/src/components/FundamentalsSection.tsx:96 | 6 casas no banco; frase 1 casa, destaque 2 casas |
| `fundamentos.pe` | `negativo = true` | Negativo porque o LPA é negativo (prejuízo de 12 meses); o quociente existe, mas não é um número de anos. | backend/apps/fundamentals/indicators.py:290, frontend/src/components/FundamentalsSection.tsx:166 | ramo pelo sinal |
| `fundamentos.pb` | texto-função (sem ramo) | O `close` da janela de 10 dias dividido pelo VPA; nulo com VPA não positivo (por isso nunca negativo). | backend/apps/fundamentals/indicators.py:291, frontend/src/components/FundamentalsSection.tsx:169 | 6 casas no banco; frase e destaque 2 casas |
| `fundamentos.equity_parent` | `negativo = false` | No consolidado, a filha "Patrimônio Líquido Atribuído ao Controlador", se o balanço a tem; senão, o Patrimônio Líquido menos a "Participação dos Acionistas Não Controladores". No individual, o Patrimônio Líquido. Na data do balanço. | backend/apps/fundamentals/conform.py:111, backend/apps/fundamentals/conform.py:174, backend/apps/fundamentals/conform.py:181, backend/apps/fundamentals/conform.py:334, backend/apps/fundamentals/indicators.py:248 | posição na data; reais, 2 casas |
| `fundamentos.equity_parent` | `negativo = true` | O mesmo patrimônio da controladora, abaixo de zero; com ele não positivo, ROE, dívida líquida/PL e P/VP saem nulos. | backend/apps/fundamentals/indicators.py:265, backend/apps/fundamentals/indicators.py:270, backend/apps/fundamentals/indicators.py:291 | ramo pelo sinal |
| `fundamentos.total_assets` | texto | A conta raiz `1` do balanço patrimonial ativo (localizada por código), na data do balanço; vale em todo plano de contas. | backend/apps/fundamentals/conform.py:155, backend/apps/fundamentals/indicators.py:299 | posição na data; reais, 2 casas |
| `fundamentos.market_cap` | texto | Para cada classe com quantidade maior que zero (ON, PN), o `close` do único ticker ativo da classe — sufixo 3 para ON, 4 a 8 para PN, a unit nunca — vezes a quantidade da classe, líquida de tesouraria, somados; nulo se falta o preço de alguma classe ou a classe tem mais de um ticker (D-124). No PETR4: nulo, `missing_class_price` — o mockup usa a frase do nulo ou outra ação. | backend/apps/fundamentals/indicators.py:190, backend/apps/fundamentals/compute.py:62, backend/apps/fundamentals/compute.py:283, backend/apps/fundamentals/conform.py:640 | preço da janela de 10 dias; ações do balanço mais recente; balanço a até 460 dias (`backend/apps/fundamentals/indicators.py:31`); reais, 2 casas |
| `fundamentos.pares.posicao` | `k ≥ 1` | O percentil é a fração das outras companhias do grupo com o indicador calculado cujo valor é **estritamente menor**: menores / (n − 1), gravado a 4 casas; a tela recupera `k = round(percentil × (n − 1))`. "Acima de k" conta só as estritamente abaixo; empate não entra. Um valor por companhia (por código CVM), o da própria ação para a dela, o do ticker de menor ordem com valor para as outras. No PETR4, ROE: 1,0000 de 7 → acima de 6 das outras 6. | backend/apps/fundamentals/peers.py:145, backend/apps/fundamentals/peers.py:149, backend/apps/fundamentals/peers.py:164, backend/apps/fundamentals/peers.py:173, frontend/src/components/FundamentalsSection.tsx:200 | n ≥ 3 (`backend/apps/fundamentals/peers.py:36`); percentil a 4 casas (`backend/apps/fundamentals/peers.py:37`); seis indicadores (`backend/apps/fundamentals/peers.py:27`) |
| `fundamentos.pares.abaixoDeTodas` | `k = 0` | Nenhuma das outras n − 1 companhias com o indicador calculado tem valor estritamente menor (percentil 0). Com empate no menor valor, a ação está **empatada** com alguma, não abaixo dela. O PETR4 não tem nenhum indicador neste ramo. | backend/apps/fundamentals/peers.py:164, frontend/src/components/FundamentalsSection.tsx:205 | n ≥ 3; percentil a 4 casas |
| `fundamentos.pares.mediana` | texto-função (sem ramo) | A mediana dos valores do grupo **incluída a própria ação**, um por companhia; com n par, a média dos dois do meio; o grupo é o segmento da B3 pela tupla (setor, subsetor, segmento), ou, com menos de 3 companhias, o subsetor pela tupla (setor, subsetor); a classificação de cada companhia é a do ticker de menor ordem; só as linhas gravadas na mesma execução entram (D-132). Margens, ROE e dívida líquida/PL em %, uma casa; P/L e P/VP em vezes, duas casas. No PETR4, dívida líquida/PL: mediana 0,6503 de 7, o próprio valor. | backend/apps/fundamentals/peers.py:148, backend/apps/fundamentals/peers.py:158, backend/apps/fundamentals/peers.py:85, backend/apps/fundamentals/peers.py:119, backend/apps/fundamentals/compute.py:352, frontend/src/components/FundamentalsSection.tsx:173 | mínimo de 3 companhias no grupo e de 3 valores (`backend/apps/fundamentals/peers.py:36`, `backend/apps/fundamentals/peers.py:156`); mediana às casas da coluna (`backend/apps/fundamentals/peers.py:28`) |

## Os nulos que tocam estas frases (não mudam com o nível, RF-05)

- O motivo por ação anula por cima, na ordem: unit; balanço com mais de 460 dias; sem quantidade de
  ações; escala desconhecida; sem preço (`backend/apps/fundamentals/indicators.py:56`,
  `backend/apps/fundamentals/indicators.py:174`, `backend/apps/fundamentals/indicators.py:326`).
- Valor que não cabe na coluna vira nulo (`backend/apps/fundamentals/indicators.py:226`,
  `backend/apps/fundamentals/indicators.py:313`).
- A frase avançada só aparece com o número presente: o nulo sai pela frase de `nulos.ts`, igual nos
  dois níveis (`frontend/src/components/FundamentalsSection.tsx:242`).

## O que não se ancorou em `caminho:linha`

- **"Receita líquida", "descontados os impostos sobre a venda, as devoluções e os abatimentos"**
  (a iniciante de `fundamentos.revenue_ttm`, `frontend/src/content/textos.ts:493`): o código só diz
  que a receita é a conta `3.01` da DRE (`backend/apps/fundamentals/conform.py:182`). Que a 3.01
  é a receita líquida é conhecimento do plano de contas da CVM, não do código. A frase avançada
  não deve afirmar o conteúdo da 3.01 além de "a conta 3.01 da DRE".
- **"Desde o IFRS 16, os empréstimos e financiamentos contêm o arrendamento"**: está na D-122
  (medido na carga real, PETR4 2T26), não no código, que só soma as duas filhas
  (`backend/apps/fundamentals/conform.py:165`). A avançada pode citar a regra de soma; o
  arrendamento dentro dela vem da decisão.
- **Por que a agenda é semanal**: o código só fixa o padrão `0 8 * * 1`, configurável por
  `RUVOR_BEAT_FUNDAMENTALS_CRON` (`backend/config/settings.py:206`). "Uma vez por semana" vale para
  o padrão; um `.env` que mude o cron desmente a frase.

## Divergências achadas entre as iniciantes e o código

Não corrigidas — o "Fora" da spec não toca as iniciantes de Fundamentos; registradas para o portão
da T12 decidir.

1. **`fundamentos.pares.abaixoDeTodas` com empate.** O percentil conta só os estritamente menores
   (`backend/apps/fundamentals/peers.py:164`): com `k = 0`, a ação pode estar empatada com o menor
   valor do grupo, e "Abaixo de todas as outras" (`frontend/src/content/textos.ts:601`) seria
   falso nesse caso. A avançada proposta acima não afirma "abaixo de todas".
2. **`fundamentos.pares.leitura`** (fora da lista das 55) diz "acima de quantas companhias do
   grupo o número está" — coerente com o estritamente menor; não muda.
3. **`fundamentos.cash`**: "as aplicações financeiras" (`frontend/src/content/textos.ts:518`) —
   o código soma só as do **Ativo Circulante** (`backend/apps/fundamentals/conform.py:161`). Não é
   falso, mas é menos preciso; a avançada diz "do circulante".
4. **`fundamentos.market_cap`** e o PETR4: o caso escolhido pela T11/T12 sai com valor de mercado
   nulo (`missing_class_price`), então a frase do número presente não é exercitada pelo PETR4; o
   mockup precisa de outra ação para ela (a D-124 cita a VALE3) ou mostra só o nulo.
5. **O ramo `negativo = true`** de nenhuma chave é exercitado pelo PETR4 (todos os valores
   positivos), nem `fundamentos.close` (o PETR4 cai em `closeOutraData`) nem
   `fundamentos.pares.abaixoDeTodas`. A prova por seção da T13 precisa de fixture própria para eles.
