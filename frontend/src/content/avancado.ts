/**
 * As frases da leitura avançada (RF-05, D-152): uma por chave da lista fechada do RF-04, com a
 * mesma chave e a mesma assinatura da iniciante em `textos.ts`. Na leitura avançada, a frase
 * daqui **substitui** a iniciante; quem monta a frase chama `textFor` (`src/reading.ts`).
 *
 * Toda afirmação sobre o cálculo é conferida no código que calcula, pelos arquivos de
 * conferência de `docs/mockups/M2.3/`, e copiada do mockup aprovado.
 *
 * A avançada declara todos os parâmetros da iniciante, na mesma ordem, inclusive os que não
 * usa — com o prefixo `_` —, para o `Function.length` bater (V-02).
 *
 * `ativo.*`: do `casco-e-preco.html` (T3), literais; as afirmações são as de
 * `conferencia-casco.md`. `comportamento.*`: do `comportamento.html` (T6), literais; as
 * afirmações são as de `conferencia-comportamento.md`. `risco.*`: do `risco.html` (T9),
 * literais — com a alternativa da D-64 aprovada no portão, a expressão única "não do número de
 * hoje" em `risco.veredito` e nos ramos k ≥ 1 e k = 0 de `risco.naoRejeitados` (as constantes
 * da vista `d64`); as afirmações são as de `conferencia-risco.md`. `fundamentos.*`: do
 * `fundamentos.html` (T12), literais; as afirmações são as de `conferencia-fundamentos.md`.
 * Com eles, `LEITURA_KEYS` são as 55 do RF-04; o M3.3 acrescenta as seis medidas do estresse, do
 * `ativo-estresse.html` (T4): são 61.
 */
import type { TEXTOS, TextoKey } from "./textos";

/** Texto vira `string`; função mantém a assinatura (mesma chave, mesmos argumentos: RF-05). */
export type Leitura<T> = T extends string ? string : T;

/** As chaves já com frase avançada: as 55 do RF-04 do M2.3 e as seis do estresse (M3.3). */
export const LEITURA_KEYS = [
  // O cabeçalho e o preço (T4).
  "ativo.ultimoFechamento",
  "ativo.precoAjustado",
  // O comportamento (T7).
  "comportamento.return_1m",
  "comportamento.return_3m",
  "comportamento.return_6m",
  "comportamento.return_12m",
  "comportamento.return_36m",
  "comportamento.return_60m",
  "comportamento.return_120m",
  "comportamento.return_ytd",
  "comportamento.volatility_12m",
  "comportamento.volatility_60m",
  "comportamento.max_drawdown",
  "comportamento.max_drawdown_recovery_sessions",
  "comportamento.beta_60m",
  "comportamento.correlation_60m",
  "comportamento.histograma",
  "comportamento.skewness",
  "comportamento.excess_kurtosis",
  "comportamento.dividends_12m",
  "comportamento.dividend_payments_12m",
  "comportamento.dividend_yield_12m",
  "comportamento.avg_volume_21d",
  "comportamento.avg_volume_252d",
  // Os momentos de estresse (M3.3): as seis medidas novas nascem com as duas frases (D-152).
  "comportamento.estresse.period_return",
  "comportamento.estresse.benchmark_period_return",
  "comportamento.estresse.drawdown",
  "comportamento.estresse.benchmark_drawdown",
  "comportamento.estresse.recovery_sessions",
  "comportamento.estresse.benchmark_recovery_sessions",
  // O risco (T10).
  "risco.perda95",
  "risco.perda99",
  "risco.discordancia",
  "risco.veredito",
  "risco.naoRejeitados",
  "risco.violacoes",
  "risco.kupiec",
  "risco.christoffersen",
  "risco.dq",
  // Os fundamentos (T13): os 18 números e a variante do preço…
  "fundamentos.revenue_ttm",
  "fundamentos.ebit_ttm",
  "fundamentos.net_income_ttm",
  "fundamentos.net_margin",
  "fundamentos.ebit_margin",
  "fundamentos.roe",
  "fundamentos.gross_debt",
  "fundamentos.cash",
  "fundamentos.net_debt",
  "fundamentos.net_debt_to_equity",
  "fundamentos.close",
  "fundamentos.eps",
  "fundamentos.bvps",
  "fundamentos.pe",
  "fundamentos.pb",
  "fundamentos.equity_parent",
  "fundamentos.total_assets",
  "fundamentos.market_cap",
  "fundamentos.closeOutraData",
  // …e a posição entre os pares.
  "fundamentos.pares.posicao",
  "fundamentos.pares.abaixoDeTodas",
  "fundamentos.pares.mediana",
] as const satisfies readonly TextoKey[];

export type LeituraKey = (typeof LEITURA_KEYS)[number];

export const TEXTOS_AVANCADOS: {
  readonly [K in LeituraKey]: Leitura<(typeof TEXTOS)[K]>;
} = {
  "ativo.ultimoFechamento": (data: string) =>
    `O fechamento do pregão de ${data}, o mais recente coletado, como o Yahoo Finance o informa — sem o ajuste por proventos do preço ajustado. A data é a do pregão no fuso da bolsa.`,
  "ativo.precoAjustado":
    "Fechamento ajustado como o Yahoo Finance o informa; o Ruvor não refaz o ajuste. A série vai do primeiro pregão coletado — a primeira coleta pede dez anos — até o último, e é pedida de novo inteira quando chega provento ou desdobramento novo, porque o ajuste muda todo o passado. Dela sai o retorno diário, o logaritmo da razão entre o fechamento ajustado e o do pregão anterior, que é o que vai aos modelos de risco.",
  // O comportamento (T7): do `comportamento.html` aprovado, literais; as afirmações são as de
  // `conferencia-comportamento.md`.
  "comportamento.return_1m": (x: string) =>
    `Retorno simples, não logarítmico, do fechamento ajustado que o Yahoo Finance informa, na janela de 1 mês de calendário: o fechamento ajustado do último pregão sobre o do primeiro pregão da janela, menos 1. A janela começa no último pregão em ou antes de um mês de calendário antes do último pregão. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_3m": (x: string) =>
    `O mesmo cálculo, na janela de 3 meses de calendário. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_6m": (x: string) =>
    `O mesmo cálculo, na janela de 6 meses de calendário. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_12m": (x: string) =>
    `O mesmo cálculo, na janela de 12 meses de calendário. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_36m": (x: string) =>
    `O mesmo cálculo, na janela de 36 meses de calendário, acumulado, não anualizado. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_60m": (x: string) =>
    `O mesmo cálculo, na janela de 60 meses de calendário, acumulado, não anualizado. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_120m": (x: string) =>
    `O mesmo cálculo, na janela de 120 meses de calendário, acumulado, não anualizado. Sem pregão em ou antes do início da janela, o número é nulo. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.return_ytd": (x: string) =>
    `Retorno simples do preço ajustado desde o fechamento do último pregão antes do ano corrente (em regra, o do ano anterior) até o último pregão — não desde o primeiro pregão do ano corrente. Sem pregão antes do ano corrente, o número é nulo. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.volatility_12m": (v: string) =>
    `Desvio-padrão amostral (divisor n − 1) dos retornos logarítmicos diários — o logaritmo da razão entre o fechamento ajustado e o do pregão anterior — na janela de 12 meses de calendário, vezes √252 para a base anual: ${v}. Fica de fora o retorno do primeiro pregão da janela, que mede o movimento anterior a ela; com menos de 2 retornos, o número é nulo.`,
  "comportamento.volatility_60m": (v: string) =>
    `O mesmo desvio-padrão amostral (divisor n − 1) dos retornos logarítmicos diários, na janela de 60 meses de calendário, vezes √252: ${v}.`,
  "comportamento.max_drawdown": (
    queda: string,
    topo: string,
    fundo: string,
    desde: string,
    volta: string | null,
  ) =>
    `A maior queda da série inteira do fechamento ajustado que o Yahoo Finance informa, desde ${desde}: a razão mais negativa entre o fechamento ajustado de um pregão e o topo anterior a ele, menos 1 — do topo de ${topo} ao fundo de ${fundo}, uma queda de ${queda}. No empate, ficam o primeiro topo de um platô e a primeira queda de mesma profundidade. ${volta ? `A volta é o primeiro pregão depois do fundo cujo fechamento ajustado alcança o do topo: ${volta}.` : "Nenhum pregão depois do fundo alcançou o fechamento ajustado do topo: a volta nula é informação, não falta de histórico."}`,
  "comportamento.max_drawdown_recovery_sessions": (anos: string) =>
    `Pregões contados do fundo, exclusive, à volta ao topo, inclusive — fundo no pregão 5 e volta no 8 dão 3. Divididos por 252, o ano de bolsa, dão cerca de ${anos} anos.`,
  "comportamento.beta_60m": (b: string, oposta: boolean) =>
    `Inclinação da regressão linear por mínimos quadrados dos retornos logarítmicos diários da ação sobre os do Ibovespa, na janela de 60 meses de calendário da ação; cada retorno se emparelha com o do índice na mesma data, e o par só vale com o do índice não nulo. Com menos de 30 pares, nulo. Inclinação ${oposta ? "negativa" : "positiva ou nula"}: ${b} de retorno logarítmico da ação para cada 1% de retorno logarítmico do índice, em média.`,
  "comportamento.correlation_60m": (c: string) =>
    `Coeficiente de correlação de Pearson entre os retornos logarítmicos diários da ação e os do Ibovespa, sobre os mesmos pares do beta: 60 meses de calendário, emparelhados por data, mínimo de 30. Aqui, ${c}.`,
  "comportamento.histograma":
    "Contagem dos retornos logarítmicos diários da janela de 60 meses de calendário em 42 baldes: 40 de largura 0,005 (0,5 ponto), de −0,10 a +0,10, fechados à esquerda e abertos à direita, mais as duas pontas abertas — abaixo de −0,10 e a partir de +0,10. Têm a cor de queda os baldes cujo limite de cima não passa de zero; o dia de retorno exatamente zero cai no balde [0; 0,005), que tem a cor de alta.",
  "comportamento.skewness": (s: string, sinal: number) =>
    `Assimetria pelo estimador enviesado g1: o terceiro momento central, com divisor n, sobre o desvio-padrão populacional (divisor n) ao cubo, nos retornos logarítmicos diários da janela de 60 meses. Nula abaixo de 4 retornos ou com desvio zero. ${sinal < 0 ? `Aqui, ${s}: negativa.` : sinal > 0 ? `Aqui, ${s}: positiva.` : "Aqui, exatamente zero."}`,
  "comportamento.excess_kurtosis": (k: string, sinal: number) =>
    `Curtose em excesso pelo estimador enviesado g2: o quarto momento central, com divisor n, sobre o desvio-padrão populacional à quarta, menos 3 — zero é a curva normal. Mesma janela de 60 meses e mesmos mínimos da assimetria. Aqui, ${k}: ${sinal > 0 ? "acima de zero" : "zero ou abaixo"}.`,
  "comportamento.dividends_12m":
    "Soma dos valores dos eventos de dividendo que o Yahoo Finance informa, com data entre a do último pregão menos 12 meses de calendário e a do último pregão, inclusive nos dois extremos. Evento sem valor fica de fora; sem pagamento, a soma é zero, não nula.",
  "comportamento.dividend_payments_12m":
    "Quantidade dos mesmos eventos de dividendo que o Yahoo Finance informa, na janela de 12 meses de calendário, inclusive nos dois extremos — só os que têm valor.",
  "comportamento.dividend_yield_12m": (d: string, x: string) =>
    `A soma de 12 meses dos proventos dividida pelo fechamento não ajustado de ${d}, o último pregão. R$ 100 × o rendimento = ${x}.`,
  "comportamento.avg_volume_21d":
    "Média aritmética do volume dos últimos 21 pregões da série — contagem de pregões, não de meses —, com o volume de cada pregão como vem do Yahoo Finance. Com menos de 21 pregões, o número é nulo, nunca uma média parcial.",
  "comportamento.avg_volume_252d":
    "A mesma média aritmética do volume, sobre os últimos 252 pregões da série. Com menos de 252 pregões, nula — nunca uma média parcial.",
  // Os momentos de estresse (M3.3): do `ativo-estresse.html` aprovado (T4), literais; cada
  // afirmação confere em `backend/apps/analytics/stress.py` (a coluna "confere em" da vista
  // "os textos" do mockup).
  "comportamento.estresse.period_return": (x: string, inicio: string, fim: string) =>
    `Retorno simples do fechamento ajustado que o Yahoo Finance informa, do pregão-base ao pregão final: o pregão-base é o último em ou antes da data de início do episódio, e o final, o último em ou antes da data de fim — aqui, ${inicio} e ${fim}. O fechamento ajustado do final sobre o do pregão-base, menos 1. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.estresse.benchmark_period_return": (x: string) =>
    `O mesmo retorno simples, sobre o fechamento do Ibovespa, com o pregão-base e o final tirados da série do próprio índice, pelas mesmas datas de calendário — as datas do índice e as da ação não se emparelham. R$ 100 × (1 + retorno) = ${x}.`,
  "comportamento.estresse.drawdown": (
    queda: string,
    topo: string,
    fundo: string,
    inteira: boolean,
  ) =>
    `A razão mais negativa, entre o pregão-base e o final, do fechamento ajustado de um pregão sobre o maior fechamento ajustado anterior a ele dentro da janela, menos 1 — topo de antes do episódio não entra. Do topo de ${topo} ao fundo de ${fundo}: ${queda}. No empate, ficam o primeiro topo de um platô e a primeira queda de mesma profundidade.${inteira ? " Aqui o topo é o pregão-base e o fundo é o final: a queda coincide com o retorno do recorte." : ""}`,
  "comportamento.estresse.benchmark_drawdown": (queda: string, inteira: boolean) =>
    `A mesma maior queda dentro da janela, na série do Ibovespa: ${queda}.${inteira ? " Aqui o topo é o pregão-base e o fundo é o final: a queda coincide com o retorno do recorte." : ""}`,
  "comportamento.estresse.recovery_sessions": (volta: string) =>
    `Pregões contados do fundo, exclusive, ao primeiro pregão da série inteira — não só da janela — cujo fechamento ajustado alcança o do topo da queda, inclusive: ${volta}. Sem esse pregão até o último calculado, o número é nulo.`,
  "comportamento.estresse.benchmark_recovery_sessions": (volta: string) =>
    `A mesma contagem, do fundo, exclusive, à volta ao topo, inclusive, na série inteira do Ibovespa: ${volta}.`,
  // O risco (T10): do `risco.html` aprovado, literais; as afirmações são as de
  // `conferencia-risco.md`. `risco.veredito` e os ramos k ≥ 1 e k = 0 de `risco.naoRejeitados`
  // são os da alternativa da D-64 (a vista `d64`: `altAvVeredito`, `altAvK1`, `altAvK0`).
  "risco.perda95":
    "VaR de 1 dia a 95%: o quantil de 5% do retorno logarítmico diário, com o sinal trocado — espera-se um retorno abaixo de −VaR em 5% dos dias. Cada modelo estima esse quantil do seu jeito; o número mostrado é, nos três tradicionais — histórico, paramétrico e Monte Carlo —, o quantil estimado uma vez sobre os 252 primeiros retornos da série e repetido no teste inteiro; nos outros seis, o do último pregão. Vai à tela como perda percentual simples, 1 − e^(−VaR).",
  "risco.perda99":
    "O mesmo VaR a 99%: o quantil de 1% — espera-se um retorno abaixo de −VaR em 1% dos dias —, com a mesma janela por família e mostrado da mesma forma.",
  "risco.discordancia": (
    min: string | null,
    max: string | null,
    n: number,
    total: number,
    _cadaN: number,
    unico: string | null,
  ): string => {
    if (n === 0)
      return "Nenhum dos nove produziu VaR neste nível: o cálculo falhou em todos, e não há faixa.";
    if (n === 1)
      return `Só um modelo produziu VaR neste nível: ${unico} é o dele, tomado e convertido como na perda acima. Sem um segundo, não há faixa.`;
    const quem =
      n === total
        ? "Os nove modelos produziram VaR neste nível"
        : `${n} de ${total} modelos produziram VaR neste nível; ${total - n === 1 ? "o outro não: o cálculo dele falhou ou ele ficou" : `os outros ${total - n} não: o cálculo falhou ou eles ficaram`} sem resultado nesta execução`;
    return `${quem}. A faixa vai da menor perda entre eles, ${min}, à maior, ${max}, cada uma tomada e convertida como na perda acima. A largura mede o quanto os números mostrados pelos métodos diferem entre si; não diz qual extremo está certo.`;
  },
  "risco.veredito":
    "Veredito por modelo e por nível: adequado quando nem o Kupiec nem o Christoffersen rejeitam, os dois com p-valor acima de 0,05; não adequado quando ao menos um rejeita; não julgado quando o cálculo do modelo falhou, o que não é reprovação. O DQ fica fora. Os testes avaliam a série de VaR do período de teste: falam do passado do modelo, não do número de hoje.",
  "risco.naoRejeitados": (k: number, julgados: number, total: number): string => {
    const faltam = total - julgados;
    const semVeredito =
      faltam > 0
        ? ` ${faltam} ${faltam === 1 ? "modelo ficou sem veredito porque o cálculo falhou: conta" : "modelos ficaram sem veredito porque o cálculo falhou: contam"} à parte, não como reprovação.`
        : "";
    if (julgados === 0)
      return "Nenhum modelo pôde ser julgado neste nível: o cálculo falhou em todos, e falha não é reprovação.";
    if (k === 0)
      return `${julgados === 1 ? "O único modelo julgado neste nível foi rejeitado" : `Os ${julgados} modelos julgados neste nível foram rejeitados`} pelo Kupiec, pelo Christoffersen ou pelos dois, na série de VaR do período de teste. Os testes avaliam essa série inteira: o veredito fala dela, não do número de hoje.${semVeredito}`;
    const quem =
      k === 1
        ? `1 dos ${julgados} modelos julgados tem`
        : `${k} dos ${julgados} modelos julgados têm`;
    return `${quem} veredito adequado neste nível: nem o Kupiec rejeitou a hipótese de cobertura correta, nem o Christoffersen a de independência das violações, na série de VaR do período de teste. Os testes avaliam essa série inteira: o veredito fala dela, não do número de hoje. A lista segue a ordem fixa dos nove, não o valor.${semVeredito}`;
  },
  "risco.violacoes": (v: string, e: string, cadaN: number, kupiecOk: boolean) =>
    `${v === "1" ? "1 violação — dia" : `${v} violações — dias`} do período de teste em que o retorno logarítmico ficou abaixo de −VaR do dia — para ${e} esperadas, os dias de teste divididos por ${cadaN}.${kupiecOk ? "" : " Longe o bastante do esperado para o Kupiec rejeitar: acima, o VaR subestimou a cauda; abaixo, superestimou."}`,
  "risco.kupiec": (p: string, ok: boolean) =>
    `Teste de proporção de falhas de Kupiec: razão de verossimilhança entre a taxa de violações observada e a esperada, contra uma qui-quadrado com 1 grau de liberdade; testa a cobertura incondicional. Aqui, ${p}: a cobertura correta ${ok ? "não é rejeitada" : "é rejeitada"}.`,
  "risco.christoffersen": (p: string, ok: boolean) =>
    `Teste de independência de Christoffersen: numa cadeia de Markov de 1ª ordem, compara a chance de violar no dia seguinte a uma violação com a de violar no dia seguinte a um dia sem violação, contra uma qui-quadrado com 1 grau de liberdade; o p-valor é o da independência. Aqui, ${p}: a independência ${ok ? "não é rejeitada" : "é rejeitada"}.`,
  "risco.dq": (p: string, ok: boolean) =>
    `Teste de quantil dinâmico: regride a violação de cada dia (1 ou 0), menos a taxa esperada, sobre uma constante, as violações dos quatro dias anteriores e o VaR do dia, e testa se todos os coeficientes são zero, contra uma qui-quadrado com 6 graus de liberdade. Pega ao mesmo tempo taxa errada e violações previsíveis. Passa com p-valor acima de 0,05 e fica fora do veredito. Aqui, ${p}: coeficientes nulos ${ok ? "não rejeitados" : "rejeitados"}.`,
  // Os fundamentos (T13): do `fundamentos.html` aprovado, literais; as afirmações são as de
  // `conferencia-fundamentos.md`. A frase do nulo não tem avançada: é a mesma nos dois níveis.
  "fundamentos.revenue_ttm":
    "A conta 3.01 da demonstração do resultado, somada nos quatro balanços mais recentes, cada um reduzido ao próprio trimestre — o quarto trimestre é o anual menos o acumulado até o trimestre anterior. Os quatro têm de ser trimestres seguidos, de 88 a 93 dias entre uma data e a outra; senão, não há número. Só no plano de contas geral: banco, seguradora e plano não reconhecido ficam sem valor.",
  "fundamentos.ebit_ttm": (negativo: boolean) =>
    `A linha "Resultado Antes do Resultado Financeiro e dos Tributos" da demonstração do resultado, achada pela descrição, somada nos mesmos quatro trimestres da receita; só no plano de contas geral.${negativo ? " Abaixo de zero: nos 12 meses, o resultado antes do financeiro e dos tributos foi negativo." : ""}`,
  "fundamentos.net_income_ttm": (negativo: boolean) =>
    `O lucro atribuído aos sócios da controladora — no balanço consolidado, a parte do lucro que cabe a eles; no individual, o lucro do período —, somado nos mesmos quatro trimestres. Calculado em todo plano de contas, banco e seguradora inclusive.${negativo ? " Abaixo de zero: prejuízo da controladora nos 12 meses." : ""}`,
  "fundamentos.net_margin": (x: string, negativo: boolean) =>
    `O lucro de 12 meses da controladora dividido pela receita de 12 meses; sem valor quando a receita falta ou não é positiva. ${negativo ? `Negativa porque o lucro foi prejuízo: ${x} de prejuízo a cada R$ 100 de receita.` : `${x} de lucro a cada R$ 100 de receita.`}`,
  "fundamentos.ebit_margin": (x: string, negativo: boolean) =>
    `O EBIT de 12 meses dividido pela mesma receita de 12 meses, com a mesma exigência de receita positiva. ${negativo ? `Negativa porque o EBIT foi negativo: ${x} abaixo de zero a cada R$ 100 de receita.` : `${x} de EBIT a cada R$ 100 de receita.`}`,
  "fundamentos.roe": (x: string, negativo: boolean) =>
    `O lucro de 12 meses da controladora dividido pelo patrimônio da controladora na data do balanço mais recente — a posição daquele dia, não a média do período; sem valor quando o patrimônio falta ou não é positivo. ${negativo ? `Negativo porque o lucro foi prejuízo: ${x} de prejuízo a cada R$ 100 de patrimônio.` : `${x} de lucro a cada R$ 100 de patrimônio.`}`,
  "fundamentos.gross_debt":
    'A soma das linhas "Empréstimos e Financiamentos" logo abaixo do passivo circulante e do passivo não circulante, na data do balanço mais recente; só no plano de contas geral.',
  "fundamentos.cash":
    'A soma das linhas "Caixa e Equivalentes de Caixa" e "Aplicações Financeiras" logo abaixo do ativo circulante, na data do balanço; a aplicação de longo prazo não entra. Só no plano de contas geral.',
  "fundamentos.net_debt": (negativo: boolean) =>
    `A dívida bruta menos o caixa e aplicações, os dois na mesma data; sem valor se um dos dois falta.${negativo ? " Negativa: o caixa e as aplicações do circulante passam da dívida bruta." : ""}`,
  "fundamentos.net_debt_to_equity": (x: string, negativo: boolean) =>
    `A dívida líquida dividida pelo patrimônio da controladora, os dois na data do balanço; sem valor com o patrimônio não positivo. ${negativo ? "Negativa porque a dívida líquida é negativa: o caixa e as aplicações passam da dívida." : `${x} de dívida líquida a cada R$ 100 de patrimônio.`}`,
  "fundamentos.close": (data: string) =>
    `O fechamento sem ajuste por proventos do pregão de ${data}, como o Yahoo Finance o informa: o último pregão entre 10 dias corridos antes do dia do cálculo e o próprio dia. É o preço do P/L e do P/VP.`,
  "fundamentos.closeOutraData": (data: string, ultimo: string) =>
    `O fechamento sem ajuste por proventos do pregão de ${data}, como o Yahoo Finance o informa — o último entre 10 dias corridos antes do dia do cálculo e o próprio dia —, e não o do último pregão coletado, ${ultimo}: os fundamentos são calculados por agenda semanal, não a cada pregão. É o preço do P/L e do P/VP.`,
  "fundamentos.eps": (acoes: string, negativo: boolean) =>
    `O lucro de 12 meses da controladora dividido por ${acoes} ações: as ordinárias mais as preferenciais do balanço mais recente, cada classe sem as ações em tesouraria. A escala — unidades ou milhares — é a que deixa o lucro acumulado no exercício desse balanço, dividido pelas ações, mais perto do lucro por ação básico que a companhia declara para o mesmo período; aceita só a menos de um fator 2 dele.${negativo ? " Negativo porque o lucro de 12 meses foi prejuízo." : ""}`,
  "fundamentos.bvps": (acoes: string) =>
    `O patrimônio da controladora na data do balanço dividido pelas mesmas ${acoes} ações, ordinárias mais preferenciais, sem as de tesouraria.`,
  "fundamentos.pe": (data: string, preco: string, x: string, negativo: boolean) =>
    `O fechamento de ${data}, ${preco}, dividido pelo lucro por ação de 12 meses; sem valor com o lucro por ação zero ou ausente. ${negativo ? `Negativo porque o lucro por ação é negativo: o quociente, ${x}, existe, mas não é um número de anos.` : `Aqui, ${x} (o destaque tem duas casas): o preço equivale a ${x} vezes o lucro por ação de 12 meses.`}`,
  "fundamentos.pb": (data: string, preco: string, x: string) =>
    `O fechamento de ${data}, ${preco}, dividido pelo patrimônio por ação: ${x}. Sem valor quando o patrimônio por ação não é positivo — por isso nunca é negativo.`,
  "fundamentos.equity_parent": (negativo: boolean) =>
    `No balanço consolidado, a linha "Patrimônio Líquido Atribuído ao Controlador", quando existe; senão, o patrimônio líquido menos a participação dos acionistas não controladores. No individual, o patrimônio líquido. Na data do balanço mais recente.${negativo ? " Abaixo de zero: com ele não positivo, o ROE, a dívida líquida sobre o patrimônio e o P/VP ficam sem valor." : ""}`,
  "fundamentos.total_assets":
    "O ativo total — a linha de topo do balanço patrimonial ativo —, na data do balanço mais recente; calculado em todo plano de contas.",
  "fundamentos.market_cap":
    "Para cada classe com ações, ordinária e preferencial, o fechamento sem ajuste do único código ativo da classe, da mesma janela de 10 dias do preço usado — final 3 na ordinária, de 4 a 8 na preferencial; a unit nunca entra —, vezes a quantidade da classe no balanço mais recente, sem as de tesouraria, e as classes somadas. Sem valor se falta o preço de uma das classes ou se uma classe tem mais de um código.",
  "fundamentos.pares.posicao": (k: string, outras: string) =>
    `Percentil: a fração das outras companhias do grupo com o indicador calculado cujo valor é estritamente menor — aqui, ${k} das ${outras}; empate não conta.`,
  "fundamentos.pares.abaixoDeTodas": (outras: string) =>
    `Percentil zero: nenhuma das outras ${outras} companhias do grupo com o indicador calculado tem valor estritamente menor; a que tiver o mesmo valor está empatada, não acima.`,
  "fundamentos.pares.mediana": (m: string) =>
    `Mediana do grupo, esta companhia inclusa, um valor por companhia (com número par, a média dos dois do meio): ${m}.`,
};

/**
 * Os textos de bloco da leitura avançada, **fora da contagem das 55** do RF-04 (o RF-06 da spec,
 * "O texto que manda abrir"): não são frase de número, e por isso não entram em `LEITURA_KEYS`
 * nem em `TEXTOS_AVANCADOS`. `risco.tabela.intro`: a entrada avançada que o portão do
 * `risco.html` (T9) aprovou — na avançada, as linhas de teste já nascem abertas.
 */
export const BLOCOS_AVANCADOS = {
  "risco.tabela.intro":
    "Em ordem fixa, por família de método; a ordem não depende dos números. As barras usam uma escala só nas duas colunas; a escala é a da maior perda da tabela. Os testes de cada modelo, nos dois níveis, vêm abertos abaixo da linha dele.",
} as const satisfies { readonly [K in TextoKey]?: string };
