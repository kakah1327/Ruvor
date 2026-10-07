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
 * `ativo-estresse.html` (T4): são 61. O M2.4 acrescenta as nove `laboratorio.*` da lista fechada
 * do `laboratorio.html` (T9), literais, com as afirmações de `conferencia-laboratorio.md`: são 70.
 * O M5.1 acrescenta as sete `retorno.*` da lista fechada do `retorno.html` (T9), literais, com as
 * afirmações de `conferencia-retorno.md`: são 77. O M2.2b acrescenta as cinco `carteira.risco.*`
 * da lista fechada do `risco.html` (T4), literais, com as afirmações de
 * `docs/mockups/M2.2b/conferencia-risco.md`: são 82.
 */
import { acimaDe, type ModeloQueBate, type TEXTOS, type TextoKey } from "./textos";

/** "A", "A e B": os nomes dos modelos na frase avançada do veredito (M5.1). */
function nomes(lista: readonly string[]): string {
  return lista.length === 1
    ? (lista[0] ?? "")
    : `${lista.slice(0, -1).join(", ")} e ${lista.at(-1)}`;
}

/**
 * A avançada dos não rejeitados, a mesma para o ativo (`risco.naoRejeitados`) e a carteira
 * (`carteira.risco.naoRejeitados`, M2.2b): a conferência da carteira confirma cada afirmação.
 */
function naoRejeitadosAvancado(k: number, julgados: number, total: number): string {
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
}

/** Texto vira `string`; função mantém a assinatura (mesma chave, mesmos argumentos: RF-05). */
export type Leitura<T> = T extends string ? string : T;

/**
 * As chaves já com frase avançada: as 55 do RF-04 do M2.3, as seis do estresse (M3.3) e as nove
 * do laboratório (M2.4).
 */
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
  // O laboratório (M2.4): a lista fechada do `laboratorio.html` aprovado, N = 9.
  "laboratorio.decada",
  "laboratorio.diferenca",
  "laboratorio.violacoesAno",
  "laboratorio.vereditoAno",
  "laboratorio.anoNaoJulgado",
  "laboratorio.semVereditoAno99",
  "laboratorio.violacoesDecada",
  "laboratorio.vereditoDecada",
  "laboratorio.anosNaoRejeitados",
  // O retorno (M5.1): a lista fechada do `retorno.html` aprovado, N = 7.
  "retorno.veredito",
  "retorno.r2_os",
  "retorno.acerto",
  "retorno.dm",
  "retorno.cw",
  "retorno.pt",
  "retorno.previsao",
  // O risco da carteira (M2.2b): as cinco novas da lista fechada do `risco.html` aprovado, N = 13
  // com as oito `risco.*` reaproveitadas, que já estão acima.
  "carteira.risco.perdaReais",
  "carteira.risco.valorAgora",
  "carteira.risco.serie",
  "carteira.risco.asOf",
  "carteira.risco.naoRejeitados",
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
  // `risco.perda95` e `risco.perda99`: literais do RF-14 do M1.4b (D-158), não do `risco.html`.
  "risco.perda95":
    "VaR de 1 dia a 95%: o quantil de 5% do retorno logarítmico diário, com o sinal trocado — espera-se um retorno abaixo de −VaR em 5% dos dias. Cada modelo estima esse quantil do seu jeito, nunca com o retorno do próprio dia: nos seis que se atualizam a cada pregão, o número mostrado é o do último pregão, com os dados até a véspera; nos três tradicionais — histórico, paramétrico e Monte Carlo —, ele só muda quando o modelo é reestimado, a cada 252 pregões, sobre todos os retornos conhecidos até ali. Vai à tela como perda percentual simples, 1 − e^(−VaR).",
  "risco.perda99":
    "O mesmo VaR a 99%: o quantil de 1% — espera-se um retorno abaixo de −VaR em 1% dos dias —, estimado e mostrado da mesma forma.",
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
  "risco.naoRejeitados": naoRejeitadosAvancado,
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
  // O laboratório (M2.4): do `laboratorio.html` aprovado (T9), literais; as afirmações são as de
  // `conferencia-laboratorio.md` (com o 192 e os ~7% da revisão do mockup).
  "laboratorio.decada": (inicio: string, fim: string, anos: number, ultimo: number) =>
    `A década do ativo: do primeiro pregão válido, ${inicio}, ao último pregão até dez anos de calendário depois, ${fim}. Os primeiros 252 retornos são o treino; o resto, o período de teste, se corta em ${anos} trechos de 252 retornos a partir do primeiro — os intervalos entre dois reajustes dos nove modelos, que reestimam todos a cada 252 pregões.${ultimo < 252 ? ` O último trecho tem ${ultimo}.` : ""}`,
  "laboratorio.diferenca": (versao: string, asOf: string) =>
    `O laboratório é o cálculo da aba Risco — os mesmos nove modelos, níveis, janela de treino, semente e testes, pela mesma rotina — recortado na década do ativo, até ${asOf}, e gravado uma vez por versão do motor (esta, ${versao}), semente, janela e versões das bibliotecas. Nenhum modelo usa o retorno do próprio dia, e por isso a série de VaR da década é o começo exato da série da aba Risco; os vereditos podem diferir porque a aba Risco testa também os pregões depois de ${asOf} e é refeita a cada dia útil. Enquanto o motor for o mesmo, este experimento não muda; com um motor novo, ele é refeito e a trilha mostra a versão. Um reajuste de preço por provento depois do experimento não o refaz: a trilha guarda a impressão digital dos preços usados. Um veredito do passado não garante o comportamento do modelo daqui para a frente.`,
  "laboratorio.violacoesAno": (e: string, cadaN: number) =>
    `Cada célula conta as violações do trecho — dias em que o retorno logarítmico ficou abaixo de −VaR do dia. O esperado é a contagem do trecho vezes α: ${e} num trecho cheio de 252, 1 dia a cada ${cadaN}. A soma dos trechos é a violação da década, conferida antes de gravar.`,
  "laboratorio.vereditoAno": (celulas: number) =>
    `Veredito do trecho, só a 95%: adequado quando nem o Kupiec nem o Christoffersen rejeitam, os dois com p-valor acima de 0,05, sobre os retornos e o VaR daquele trecho; não adequado quando ao menos um rejeita. São ${celulas} células julgadas, e, num modelo correto, cada trecho tem perto de 7% de chance de sair não adequado só por acaso — o Kupiec rejeita ~6% dos trechos de 252 e o Christoffersen, com tão poucas violações, quase nunca —, cerca de um trecho a cada 14. O veredito que resume o modelo é o da década.`,
  "laboratorio.anoNaoJulgado": (n: number) =>
    `Trecho de ${n} retornos, abaixo do piso de 126 (meio ano de teste): as violações e as esperadas são gravadas; o Kupiec, o Christoffersen e o veredito ficam nulos.`,
  "laboratorio.semVereditoAno99":
    "Sem veredito por trecho a 99%: num trecho de 252 esperam-se 2,52 violações, e o Kupiec rejeita até o trecho sem nenhuma — com zero violações, a estatística é −2·n·ln(0,99), acima do valor crítico de 3,84 a partir de 192 retornos (p ≈ 0,024 em 252). O teste por trecho quase não distingue nada neste nível; os testes e o veredito a 99% ficam só na década.",
  "laboratorio.violacoesDecada": (
    v: string,
    e: string,
    cadaN: number,
    kupiecOk: boolean,
  ) =>
    `${v === "1" ? "1 violação" : `${v} violações`} em todo o período de teste da década — a soma dos trechos — para ${e} esperadas, os dias de teste divididos por ${cadaN}; são as do Kupiec da década, sobre a série de VaR inteira.${kupiecOk ? "" : acimaDe(v, e) ? " Acima do esperado o bastante para o Kupiec rejeitar: o VaR subestimou a cauda." : " Abaixo do esperado o bastante para o Kupiec rejeitar: o VaR superestimou a cauda."}`,
  "laboratorio.vereditoDecada":
    "Veredito da década, nos dois níveis: adequado quando nem o Kupiec nem o Christoffersen rejeitam, os dois com p-valor acima de 0,05, sobre a série de VaR do período de teste inteiro da década; não adequado quando ao menos um rejeita; não julgado quando o cálculo do modelo falhou, o que não é reprovação. O DQ é mostrado e fica fora; a zona de Basileia não é gravada no laboratório. Fala do passado do modelo, não do número de hoje.",
  "laboratorio.anosNaoRejeitados":
    "Para cada modelo, em quantos dos trechos julgados a 95% nem o Kupiec nem o Christoffersen rejeitaram; o total conta só os trechos julgados. Com perto de 7% de chance de rejeição por acaso em cada trecho, um modelo correto fica perto de 8 ou 9 de 9. A contagem descreve cada modelo e não ordena os nove: a grade segue a ordem fixa.",
  // O retorno (M5.1): do `retorno.html` aprovado (T9), com os ajustes da revisão do mockup,
  // literais; as afirmações são as de `conferencia-retorno.md`.
  "retorno.veredito": (
    _ticker: string,
    n: string,
    fim: string,
    batem: readonly ModeloQueBate[],
    naoBatem: readonly string[],
    falhos: number,
  ) => {
    const base = `Veredito por modelo: o teste de Diebold-Mariano com perda quadrática, unilateral (a alternativa é "o modelo erra menos que o zero"), contra a referência de retorno zero, nos ${n} pregões de teste até ${fim}; bate quando o p-valor, arredondado a 10 casas, fica abaixo de 0,05.`;
    const falha = falhos
      ? ` ${falhos === 1 ? "Um modelo ficou" : "Os dois ficaram"} sem veredito: o cálculo falhou.`
      : "";
    if (batem.length === 0) {
      return `${base} ${naoBatem.length === 2 ? "Nenhum dos dois ficou abaixo" : naoBatem.length === 1 ? `${naoBatem[0]} não ficou abaixo` : "Nenhum foi julgado"}${naoBatem.length ? ": as previsões não são mais informativas que supor retorno zero." : "."}${falha}`;
    }
    return `${base} ${nomes(batem.map(([nm]) => nm))} ${batem.length === 2 ? "ficaram" : "ficou"} abaixo. O DM só é positivo quando o erro quadrático médio do modelo é menor que o da referência, e bater implica erro relativo positivo. Com dois modelos e muitos ativos, alguns casos assim aparecem por acaso; o acerto de direção (PT) não entra no veredito.${falha}`;
  },
  "retorno.r2_os": (valor: string, menos: boolean) =>
    `Erro relativo à referência: 1 − EQM do modelo / EQM de supor zero, com EQM a média do quadrado do erro sobre os pregões de teste (o R² fora da amostra com referência zero). Aqui, ${valor === "0,00%" ? valor : `${menos ? "+" : "−"}${valor}`}: o modelo errou ${menos ? "menos" : "mais"} que o zero.`,
  "retorno.acerto": (acerto: string, alta: string) =>
    `Acerto de direção: a parcela dos dias em que o sinal da previsão foi o do retorno, contada só nos dias com retorno e previsão diferentes de zero; ${acerto}. A régua é a parcela de dias de alta nesses mesmos dias, ${alta}.`,
  "retorno.dm": (p: string, bate: boolean) =>
    `Diebold-Mariano: a média da diferença diária entre o quadrado do retorno e o quadrado do erro do modelo, dividida pelo erro-padrão de longo prazo de Newey-West (núcleo de Bartlett, defasagem ⌊4·(n/100)^(2/9)⌋, série centrada, divisor n); p unilateral, 1 − Φ(DM). Aqui, ${p}: ${bate ? "abaixo de 0,05" : "não fica abaixo de 0,05"}.`,
  "retorno.cw": (p: string) =>
    `Clark-West: a diferença diária é o quadrado do retorno menos (o quadrado do erro do modelo menos o quadrado da previsão), porque o zero é um caso particular do modelo; o mesmo Newey-West e p unilateral. Aqui, ${p}. Não entra no veredito.`,
  "retorno.pt": (p: string | null, todosAlta: boolean | null) =>
    p !== null
      ? `Pesaran-Timmermann: compara o acerto de direção com P* = p_y·p_x + (1 − p_y)(1 − p_x), o de um palpite independente com as mesmas proporções de alta realizada e prevista, pela diferença das variâncias do artigo; p unilateral. Aqui, ${p}. Não entra no veredito.`
      : `Pesaran-Timmermann sem p-valor: a parcela de alta prevista é ${todosAlta ? "1" : "0"} — o modelo previu ${todosAlta ? "alta" : "queda"} em todos os dias —, e o teste não tem o que medir; o acerto é a parcela de dias de ${todosAlta ? "alta" : "queda"}.`,
  // O risco da carteira (M2.2b): do `risco.html` aprovado (T4), literais; as afirmações são as
  // de `docs/mockups/M2.2b/conferencia-risco.md`. A de `carteira.risco.naoRejeitados` é a de
  // `risco.naoRejeitados`, com a expressão da D-64 nos ramos k ≥ 1 e k = 0.
  "carteira.risco.perdaReais": (valor: string, _cadaN: number) =>
    `Valor × (1 − e^(−VaR)), com o valor de ${valor}, arredondado ao centavo, metade para cima: a mesma perda simples do percentual. A faixa vai da conversão do menor à do maior VaR do nível, entre os modelos que calcularam; na tabela, cada modelo tem a sua. Supõe o valor distribuído pelos pesos da composição, como a série da carteira, rebalanceada a cada pregão.`,
  "carteira.risco.valorAgora":
    "O valor aplicado fica fora do cálculo: não entra na série nem nos modelos, e mudá-lo não cria versão nem muda a série — por isso não abre cálculo novo. Os reais são calculados a cada leitura, com o valor guardado naquele momento; nenhum valor em reais fica gravado com o resultado.",
  "carteira.risco.serie":
    "Um índice que começa em 1 e anda pelo retorno simples ponderado pelos pesos, fixos e rebalanceados a cada data. As datas são as em que todas as ações da composição têm fechamento ajustado positivo; numa data que falta a uma delas, a data fica fora, e o retorno da seguinte cobre o intervalo. O motor tira do índice o retorno logarítmico — o da carteira, não a média ponderada dos de cada ação — e roda os mesmos nove modelos, testes, níveis e semente do ativo, com os primeiros 252 retornos de treino e o resto de teste, treinando do zero a cada cálculo. O piso é de 503 datas em comum, que deixam ao menos 250 dias de teste.",
  "carteira.risco.asOf": (data: string) =>
    `${data} é a última data da série: a mais recente em que todas as ações da composição têm fechamento ajustado positivo — no máximo, a do último preço da ação mais atrasada. Um pedido novo só abre cálculo quando essa data ou a série mudam: com a mesma data e o mesmo SHA-256 da série do cálculo fechado mais recente, concluído ou parcial, a resposta é que o risco desta versão já está calculado.`,
  "carteira.risco.naoRejeitados": naoRejeitadosAvancado,
  "retorno.previsao": (valor: string, data: string, bate: boolean) =>
    `A previsão do próximo pregão é o mesmo cálculo do teste aplicado ao dia seguinte ao último preço: os parâmetros do trecho corrente, reestimados com tudo até o último preço quando ele abre um trecho de 252; na média histórica, a média dos retornos conhecidos; no AR(1), c + φ vezes o retorno do último pregão. A data, ${data}, é o primeiro dia de semana depois do último preço, sem o calendário de feriados. Aqui, ${valor}${bate ? ", de um modelo que bateu a referência no período — um número estatístico, gravado com 10 casas" : ", de um modelo que não bate a referência: não é mais informativa que supor zero"}.`,
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
