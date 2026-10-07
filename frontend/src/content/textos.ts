/**
 * O módulo de textos (RF-21): todo texto visível das telas mora aqui, chave → texto ou
 * função dos valores. Os textos vêm dos mockups aprovados, literais.
 *
 * `casco.*` e `rodape.*`: do `busca.html` (T2), com os nomes de chave que o
 * `ativo-estados.html` (T4) registrou; `rodape.ultimoPregao` e `rodape.calculadoEm`, do
 * `ativo.html` (T3). `busca.*`: do `busca.html` (T2) — o HTML da página inicial e o objeto
 * `T` do script. A ressalva mora em `ressalva.ts`.
 *
 * `ativo.*`, `grafico.*`, `comportamento.*` e `risco.*`: do registro `TEXTOS` do `ativo.html`
 * (T3), com os ajustes do portão já aplicados; o que nasceu no `ativo-estados.html` (T4) —
 * `ativo.preco.vazio*`, `ativo.naoEncontrado*`, `comportamento.naoCalculado*`,
 * `comportamento.irParaRisco`, `risco.carregando`, `risco.estado.*`, `risco.pedido.*` e
 * `motivos.*` — do registro dele. As chaves comuns aos dois mockups têm o mesmo texto.
 * As funções recebem os valores já formatados, como no mockup, e têm os mesmos ramos; o
 * número só entra cru onde o ramo depende dele.
 */

import { formatInteger } from "../format/numbers";
import { RESSALVA } from "./ressalva";

/** Um número já formatado em pt-BR ("1.234,5") de volta a número. */
function numeroBR(texto: string): number {
  return Number(texto.replace(/\./g, "").replace(",", "."));
}

/**
 * O lado da rejeição do Kupiec da década (M2.4, portão do `laboratorio.html`): as violações
 * (`v`) acima das esperadas (`e`), os dois já formatados. A rejeição sozinha não diz o lado.
 */
export function acimaDe(v: string, e: string): boolean {
  return numeroBR(v) > numeroBR(e);
}

/** Um modelo que bate a referência na frase do veredito (M5.1): o nome e quanto errou menos. */
export type ModeloQueBate = readonly [nome: string, quantoMenos: string];

/** A frase dos modelos sem veredito (M5.1, `retorno.veredito`): o cálculo falhou. */
function falhaFrase(falhos: number): string {
  if (falhos === 0) return "";
  return falhos === 1
    ? " O cálculo de um dos modelos falhou, e ele não foi julgado."
    : " O cálculo dos dois modelos falhou, e nenhum foi julgado.";
}

export const TEXTOS = {
  // A barra superior.
  "casco.marca": "RUVOR",
  "casco.marca.rotulo": "Ruvor, ir para a busca",
  "casco.busca.placeholder": "Buscar ativo",
  "casco.busca.rotulo": "Buscar ativo",
  "casco.tema.rotulo": "Tema",
  "casco.tema.claro": "Claro",
  "casco.tema.escuro": "Escuro",
  "casco.tema.sistema": "Sistema",
  // O alternador do nível de leitura (RF-01 do M2.3): do `casco-e-preco.html` aprovado.
  "casco.leitura.rotulo": "Nível de leitura",
  "casco.leitura.iniciante": "Iniciante",
  "casco.leitura.avancada": "Avançada",

  // A página não encontrada. O endereço digitado vai entre `antes` e `depois`, citado.
  "casco.naoEncontrada.eyebrow": "Endereço desconhecido",
  "casco.naoEncontrada.titulo": "Página não encontrada.",
  "casco.naoEncontrada.antes": "Nenhuma página do Ruvor fica em ",
  "casco.naoEncontrada.depois": ". O endereço pode ter sido digitado errado.",
  "casco.naoEncontrada.dica":
    "Para chegar a um ativo, busque pelo código ou pelo nome.",
  "casco.irParaBusca": "Ir para a busca",

  // A busca (RF-05): a página inicial e a lista suspensa da barra. O limpar e os estados
  // valem nos dois campos.
  "busca.eyebrow": "Busca",
  "busca.titulo": "Qual ativo você quer analisar?",
  "busca.sub":
    "Digite o código ou o nome de uma ação da B3, ou do Ibovespa. Na página do ativo, você vê como o preço se comportou e quanto nove métodos estimam que ele pode perder em um dia.",
  "busca.rotulo": "Buscar ativo por código ou nome",
  "busca.placeholder": "Código ou nome, como PETR4",
  "busca.limpar": "Limpar a busca",
  "busca.sugestaoTitulo": "ativos com risco calculado",
  "busca.sugestaoNota":
    "Os outros ativos do catálogo podem ter o risco calculado na página de cada um.",
  // A sugestão vinda da API (M1.7, RF-10 e RF-11): do objeto `T` do busca-sugestao.html.
  "busca.sugestaoCarregando": "Carregando os ativos com risco calculado.",
  "busca.sugestaoErro": "A lista de ativos com risco calculado não carregou.",
  "busca.sugestaoErroDica": "Busque pelo código ou pelo nome do ativo, no campo acima.",
  "busca.sugestaoNenhum": "Nenhum ativo tem o risco calculado ainda.",
  "busca.sugestaoNenhumNota":
    "Os ativos do catálogo podem ter o risco calculado na página de cada um.",
  "busca.sugestaoMais": (n: number) =>
    n === 1 ? "e mais 1 ativo" : `e mais ${formatInteger(n)} ativos`,
  "busca.contagem": (n: number, q: string) =>
    `${n === 1 ? "1 ativo" : `${formatInteger(n)} ativos`} para “${q}”`,
  "busca.mostrando": (a: number, n: number) =>
    `Mostrando ${formatInteger(a)} de ${formatInteger(n)}.`,
  "busca.mostrarMais": "Mostrar mais",
  "busca.buscando": "Buscando…",
  "busca.semResultado": (q: string) => `Nenhum ativo com “${q}”.`,
  "busca.semResultadoDica": "Confira o código ou tente uma parte do nome.",
  "busca.erroTitulo": "A busca não respondeu.",
  "busca.erroTexto": "Pode ser uma falha passageira do servidor.",
  "busca.tentarDeNovo": "Tentar de novo",
  "busca.suspensaRodape": (a: number, n: number) =>
    `${formatInteger(a)} de ${formatInteger(n)} · continue digitando para filtrar`,
  "busca.tagIndice": "índice",
  "busca.tagInativo": "inativo",
  "busca.tagSemDados": "sem dados ainda",
  // A página inicial abaixo do campo: os números do método e o que a página do ativo mostra.
  "busca.metodoTitulo": "O método, em números",
  "busca.metodo": [
    { valor: "9", rotulo: "métodos de estimar a perda em um dia" },
    { valor: "4", rotulo: "testes que conferem cada método no passado" },
    { valor: "2", rotulo: "níveis de confiança: 95% e 99%" },
    { valor: "10 anos", rotulo: "de preço diário por ativo" },
  ],
  "busca.paginaTitulo": "O que a página do ativo mostra",
  "busca.pagina": [
    {
      titulo: "Comportamento",
      texto:
        "O preço, os proventos, a volatilidade, as maiores quedas e como o ativo se saiu nos momentos de estresse do mercado.",
    },
    {
      titulo: "Risco",
      texto:
        "Quanto o ativo pode perder em um dia, segundo nove métodos, e quais deles passaram nos testes sobre o histórico do próprio ativo.",
    },
    {
      titulo: "Laboratório",
      texto:
        "Os mesmos nove métodos ano a ano, ao longo de uma década, para ver em que anos cada um acertou e errou.",
    },
    {
      titulo: "Fundamentos e comunicados",
      texto:
        "Os indicadores do último balanço, a posição entre as empresas do mesmo segmento e o que a companhia divulgou à CVM.",
    },
  ],

  // As abas da tela do ativo: cada uma com o seu endereço debaixo de /ativos/{ticker}.
  "ativo.abas.rotulo": "Seções do ativo",
  "ativo.aba.visaoGeral": "Visão geral",
  "ativo.aba.risco": "Risco",
  "ativo.aba.laboratorio": "Laboratório",
  "ativo.aba.retorno": "Retorno",
  "ativo.aba.fundamentos": "Fundamentos",
  "ativo.aba.comunicados": "Comunicados",
  "ativo.explicacoes": "Explicações",

  // O rodapé (RF-04).
  "rodape.ressalva": RESSALVA,
  "rodape.fonte":
    "Fontes: catálogo de ativos da B3, preços do Yahoo Finance, e balanços e comunicados da CVM.",
  "rodape.ultimoPregao": (data: string) => `Último pregão usado: ${data}.`,
  "rodape.calculadoEm": (data: string, hora: string) =>
    `Risco calculado em ${data} às ${hora}.`,

  // ativo.* — cabeçalho, preço, eventos, erros de seção.
  "ativo.tipo.stock": "ação",
  "ativo.tipo.index": "índice",
  "ativo.situacao.active": "em negociação",
  "ativo.situacao.inactive": "inativo",
  "ativo.listagem": (s: string) => `segmento de listagem ${s}`,
  "ativo.classificacao": "Classificação na B3",
  "ativo.ultimoFechamento.rotulo": "Último fechamento",
  "ativo.ultimoFechamento": (data: string) =>
    `O preço de fechamento do último pregão coletado, ${data}, como foi negociado na bolsa — sem ajuste por proventos.`,
  "ativo.semPreco": "sem preço coletado ainda",
  "ativo.preco.titulo": "Preço ajustado",
  "ativo.precoAjustado":
    "Preço corrigido por proventos e desdobramentos: os valores antigos são ajustados para que a linha mostre quanto a ação rendeu de fato, sem os saltos dos pagamentos. É a mesma série que vai aos modelos de risco.",
  "ativo.preco.vazio": "Ainda não há preços coletados deste ativo.",
  "ativo.preco.vazio.nota":
    "A série de preços é coletada junto com o cálculo do risco.",
  "ativo.eventos.titulo": "Proventos e desdobramentos",
  "ativo.eventos.periodo": (d: string) => `nos 12 meses até ${d}`,
  "ativo.eventos.col.data": "Data",
  "ativo.eventos.col.tipo": "Tipo",
  "ativo.eventos.col.valor": "Valor ou proporção",
  "ativo.eventos.dividend": "provento",
  "ativo.eventos.split": "desdobramento",
  "ativo.eventos.valor": (v: string) => `${v} por ação`,
  "ativo.eventos.proporcao": (num: string, den: string) =>
    `cada ${den} ações viraram ${num}`,
  "ativo.eventos.verTodos": (n: string) => `Ver todos (${n})`,
  "ativo.eventos.verMenos": "Ver só os últimos 12 meses",
  "ativo.eventos.nenhum":
    "Não houve proventos nem desdobramentos nos últimos 12 meses.",
  "ativo.erroSecao": "Não foi possível carregar esta parte da página.",
  "ativo.tentarDeNovo": "Tentar de novo",
  "ativo.naoEncontrado.sobrancelha": "Código desconhecido",
  "ativo.naoEncontrado.titulo": "Ativo não encontrado.",
  "ativo.naoEncontrado": (t: string) =>
    `O catálogo não tem nenhum ativo com o código ${t}.`,
  "ativo.naoEncontrado.dica": "Confira o código, ou busque pelo nome da empresa.",

  // grafico.* — atalhos, pontas, dicas, resumos.
  "grafico.atalhos": "Período do gráfico",
  "grafico.atalho.1a": "1 ano",
  "grafico.atalho.5a": "5 anos",
  "grafico.atalho.tudo": "Tudo",
  "grafico.arrasto":
    "Arraste sobre o gráfico para aproximar; clique duas vezes para ver tudo de novo.",
  "grafico.dicaPreco": (data: string, preco: string) => `${data} · ${preco}`,
  "grafico.resumoPreco": (
    ini: string,
    fim: string,
    min: string,
    dmin: string,
    max: string,
    dmax: string,
    ult: string,
  ) =>
    `De ${ini} a ${fim}, o preço ajustado foi do mínimo de ${min}, em ${dmin}, ao máximo de ${max}, em ${dmax}; o último é ${ult}.`,
  "grafico.pontaInferior": "abaixo de −10%",
  "grafico.pontaSuperior": "acima de +10%",
  "grafico.faixa": (lo: string, hi: string) => `de ${lo} a ${hi}`,
  "grafico.dicaBarra": (faixa: string, n: number) =>
    `${faixa}: ${n} ${n === 1 ? "pregão" : "pregões"}`,
  "grafico.legendaQueda": "dias de queda",
  "grafico.legendaAlta": "dias de alta ou estáveis",
  "grafico.resumoHistograma": (
    faixa: string,
    n: string,
    abaixo: number,
    acima: number,
  ) =>
    `A faixa com mais pregões é ${faixa}, com ${n}. Nas pontas, ${abaixo} ${abaixo === 1 ? "pregão ficou" : "pregões ficaram"} abaixo de −10% e ${acima} acima de +10%.`,

  // comportamento.* — a camada 2.
  "comportamento.sobrancelha": "O que já aconteceu",
  "comportamento.titulo": "Comportamento",
  "comportamento.ate": (d: string) => `até ${d}`,
  "comportamento.intro":
    "Como a ação se comportou até aqui: quanto rendeu, quanto oscilou, quanto já caiu e como se move junto com o Ibovespa.",
  "comportamento.bloco.retornos": "Retornos",
  "comportamento.bloco.volatilidade": "Volatilidade",
  "comportamento.bloco.queda": "Maior queda",
  "comportamento.bloco.ibov": "Relação com o Ibovespa",
  "comportamento.bloco.distribuicao": "Distribuição dos retornos diários",
  "comportamento.bloco.proventos": "Proventos",
  "comportamento.bloco.volume": "Volume",
  "comportamento.nota.retornos":
    "Variação do preço ajustado, que já inclui proventos e desdobramentos.",
  "comportamento.nota.ibov": (n: string) =>
    `Calculado sobre ${n} pregões em comum com o Ibovespa.`,
  "comportamento.nota.distribuicao": (n: string) =>
    `Calculado sobre ${n} retornos diários dos últimos 60 meses.`,
  "comportamento.nulo.janela": (n: number) => `a série é mais curta que ${n} meses`,
  "comportamento.nulo.pregoes": (n: number) => `a série tem menos de ${n} pregões`,
  "comportamento.nulo.naoRecuperou": "ainda não recuperou",
  "comportamento.nulo.referencia": "o Ibovespa é a própria referência",
  "comportamento.histogramaCurto":
    "A série é curta demais para a distribuição: ela pede 60 meses de pregões.",
  "comportamento.naoCalculado": "O comportamento ainda não foi calculado.",
  "comportamento.naoCalculado.nota":
    "Ele é calculado junto com o risco: o mesmo pedido, na seção de risco, calcula os dois.",
  "comportamento.irParaRisco": "Ir para o risco",
  "comportamento.rotulo.return_1m": "1 mês",
  "comportamento.rotulo.return_3m": "3 meses",
  "comportamento.rotulo.return_6m": "6 meses",
  "comportamento.rotulo.return_12m": "12 meses",
  "comportamento.rotulo.return_36m": "36 meses",
  "comportamento.rotulo.return_60m": "60 meses",
  "comportamento.rotulo.return_120m": "120 meses",
  "comportamento.rotulo.return_ytd": "No ano",
  "comportamento.rotulo.volatility_12m": "12 meses",
  "comportamento.rotulo.volatility_60m": "60 meses",
  "comportamento.rotulo.max_drawdown": "Do topo ao fundo",
  "comportamento.rotulo.max_drawdown_recovery_sessions": "Pregões até recuperar",
  "comportamento.rotulo.beta_60m": "Beta, 60 meses",
  "comportamento.rotulo.correlation_60m": "Correlação, 60 meses",
  "comportamento.rotulo.skewness": "Assimetria",
  "comportamento.rotulo.excess_kurtosis": "Curtose em excesso",
  "comportamento.rotulo.dividends_12m": "Por ação, 12 meses",
  "comportamento.rotulo.dividend_payments_12m": "Pagamentos, 12 meses",
  "comportamento.rotulo.dividend_yield_12m": "Sobre o preço, 12 meses",
  "comportamento.rotulo.avg_volume_21d": "Média de 21 pregões",
  "comportamento.rotulo.avg_volume_252d": "Média de 252 pregões",
  "comportamento.return_1m": (x: string) =>
    `No último mês, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_3m": (x: string) =>
    `Nos últimos 3 meses, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_6m": (x: string) =>
    `Nos últimos 6 meses, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_12m": (x: string) =>
    `Nos últimos 12 meses, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_36m": (x: string) =>
    `Nos últimos 3 anos, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_60m": (x: string) =>
    `Nos últimos 5 anos, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_120m": (x: string) =>
    `Nos últimos 10 anos, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.return_ytd": (x: string) =>
    `Desde o fechamento do último pregão do ano passado, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.volatility_12m": (v: string) =>
    `O quanto o preço oscilou no último ano, em base anual: num ano como esse, variações de ${v} para cima ou para baixo são o normal.`,
  "comportamento.volatility_60m": (v: string) =>
    `A mesma medida nos últimos 5 anos, ${v}: comparada com a de 12 meses, mostra se o último ano foi mais calmo ou mais agitado que o habitual.`,
  "comportamento.max_drawdown": (
    queda: string,
    topo: string,
    fundo: string,
    desde: string,
    volta: string | null,
  ) =>
    `A maior queda do preço ajustado desde ${desde}: de ${topo} a ${fundo}, caiu ${queda}. ${volta ? `Voltou ao topo anterior em ${volta}.` : "Ainda não voltou ao topo anterior."}`,
  "comportamento.max_drawdown_recovery_sessions": (anos: string) =>
    `Pregões entre o fundo e a volta ao topo anterior — cerca de ${anos} anos de bolsa.`,
  // Os momentos de estresse (M3.3): do `ativo-estresse.html` aprovado (T4), literais. As
  // funções recebem os valores já formatados; `inteira` é o ramo da queda que começa no topo
  // (o primeiro pregão da janela) e termina no fundo (o último).
  "comportamento.bloco.estresse": "Em momentos de estresse",
  "comportamento.nota.estresse":
    "Quatro momentos em que o mercado brasileiro inteiro caiu forte, os mesmos para toda ação, em ordem de data. Cada número usa o preço ajustado, com proventos e desdobramentos, e o Ibovespa é medido no mesmo recorte de datas. Os pregões até recuperar contam também o que veio depois do fim do episódio: o que hoje ainda não recuperou pode ganhar número num cálculo futuro.",
  "comportamento.estresse.episodio.jbs_2017": "A delação da JBS",
  "comportamento.estresse.episodio.truckers_2018": "A greve dos caminhoneiros",
  "comportamento.estresse.episodio.covid_2020": "A chegada da covid",
  "comportamento.estresse.episodio.rates_2021": "A alta dos juros",
  "comportamento.estresse.recorte": (inicio: string, fim: string) =>
    `de ${inicio} a ${fim}`,
  "comportamento.estresse.janela": (p0: string, pn: string) =>
    `pregões de ${p0} a ${pn}`,
  "comportamento.estresse.rotulo.period_return": "Do início ao fim",
  "comportamento.estresse.rotulo.benchmark_period_return": "Ibovespa, do início ao fim",
  "comportamento.estresse.rotulo.drawdown": "Maior queda no episódio",
  "comportamento.estresse.rotulo.benchmark_drawdown":
    "Ibovespa, maior queda no episódio",
  "comportamento.estresse.rotulo.recovery_sessions": "Pregões até recuperar",
  "comportamento.estresse.rotulo.benchmark_recovery_sessions":
    "Ibovespa, pregões até recuperar",
  "comportamento.estresse.period_return": (x: string, inicio: string, fim: string) =>
    `Do primeiro ao último pregão do episódio, de ${inicio} a ${fim}, com os proventos: R$ 100 viraram ${x}.`,
  "comportamento.estresse.benchmark_period_return": (x: string) =>
    `O Ibovespa no mesmo recorte de datas: R$ 100 viraram ${x}.`,
  "comportamento.estresse.drawdown": (
    queda: string,
    topo: string,
    fundo: string,
    inteira: boolean,
  ) =>
    `Dentro do episódio, o preço ajustado caiu ${queda}, de ${topo} a ${fundo}.${inteira ? " Começou o episódio no topo e terminou no fundo: por isso a queda é igual ao resultado do início ao fim." : ""}`,
  "comportamento.estresse.benchmark_drawdown": (queda: string, inteira: boolean) =>
    `A maior queda do Ibovespa dentro do mesmo recorte: ${queda}.${inteira ? " O índice começou o recorte no topo e terminou no fundo: por isso a queda é igual ao resultado do início ao fim." : ""}`,
  "comportamento.estresse.recovery_sessions": (volta: string) =>
    `Pregões entre o fundo dessa queda e a volta ao topo dela, em ${volta} — contando também depois do fim do episódio.`,
  "comportamento.estresse.benchmark_recovery_sessions": (volta: string) =>
    `O mesmo para o Ibovespa: do fundo da queda dele à volta ao topo dela, ${volta}.`,
  // A contagem que entra na frase do índice (o mockup monta "N pregões").
  "comportamento.estresse.pregoes": (n: string) => `${n} pregões`,
  "comportamento.estresse.semDado.rotulo": "Sem dado",
  "comportamento.estresse.semDado.starts_after":
    "O ativo ainda não tinha preço no início deste episódio.",
  "comportamento.estresse.semDado.stale_start":
    "O último preço do ativo antes deste episódio é de mais de 10 dias antes dele.",
  "comportamento.estresse.semDado.ends_before":
    "A série do ativo termina antes do fim deste episódio.",
  "comportamento.estresse.semDado.no_trading":
    "O ativo não negociou durante este episódio.",
  "comportamento.estresse.semQueda":
    "Dentro do episódio, o preço nunca ficou abaixo do maior preço alcançado até ali.",
  "comportamento.estresse.nadaARecuperar": "sem queda no episódio, nada a recuperar",
  "comportamento.estresse.semIbov": "sem o Ibovespa neste recorte",
  "comportamento.estresse.naoCalculado":
    "Os momentos de estresse ainda não foram calculados para estes números. Entram no próximo cálculo do comportamento, no dia útil seguinte.",
  "comportamento.beta_60m": (b: string, oposta: boolean) =>
    `Nos últimos 5 anos, quando o Ibovespa subiu ou caiu 1%, a ação se moveu em média ${b} ${oposta ? "na direção oposta" : "na mesma direção"}.`,
  "comportamento.correlation_60m": (c: string) =>
    `De −1 a 1, o quanto os movimentos diários da ação e do Ibovespa andam juntos: perto de 1, juntos; perto de 0, sem relação; abaixo de 0, em sentidos opostos. Aqui, ${c}.`,
  "comportamento.histograma":
    "Quantos pregões dos últimos 60 meses tiveram cada tamanho de retorno diário. Cada barra é uma faixa de 0,5 ponto, em retorno logarítmico — que, abaixo de 10%, quase coincide com a variação percentual. As barras dos dias de queda têm cor própria, e as duas pontas juntam tudo o que passou de 10% para baixo ou para cima.",
  "comportamento.skewness": (s: string, sinal: number) =>
    sinal < 0
      ? `Negativa, como aqui (${s}), quer dizer que as quedas fortes foram mais frequentes que as altas fortes do mesmo tamanho.`
      : sinal > 0
        ? `Positiva, como aqui (${s}), quer dizer que as altas fortes foram mais frequentes que as quedas fortes do mesmo tamanho.`
        : `Zero, como aqui, quer dizer que altas e quedas fortes do mesmo tamanho apareceram na mesma medida.`,
  "comportamento.excess_kurtosis": (k: string, sinal: number) =>
    sinal > 0
      ? `Acima de zero, como aqui (${k}), os dias extremos — de alta ou de queda — apareceram mais vezes do que a curva normal prevê.`
      : `Em zero ou abaixo, como aqui (${k}), os dias extremos apareceram com a frequência que a curva normal prevê, ou menos.`,
  "comportamento.dividends_12m":
    "Soma dos proventos pagos por ação nos últimos 12 meses.",
  "comportamento.dividend_payments_12m":
    "Quantas vezes a companhia pagou proventos nos últimos 12 meses.",
  "comportamento.dividend_yield_12m": (d: string, x: string) =>
    `Os proventos de 12 meses divididos pelo fechamento de ${d}: a cada R$ 100 em ações, ${x} em proventos.`,
  "comportamento.avg_volume_21d":
    "Quantas ações trocaram de mão por pregão, em média, no último mês.",
  "comportamento.avg_volume_252d":
    "A mesma média no último ano: comparada com a do mês, mostra se o interesse recente está acima ou abaixo do habitual.",
  "comportamento.unidade.volume": (m: string) => `${m} milhões`,
  // O controle de recolher da assimetria e da curtose (RF-06, RF-07 do M2.3): do
  // `comportamento.html` aprovado — um rótulo só, nos dois estados e nos dois níveis.
  "comportamento.momentos.abrir": "Ver a assimetria e a curtose",
  "comportamento.verMais":
    "Ver mais: estresse, Ibovespa, proventos, distribuição e volume",
  "comportamento.verMenos": "Ver menos",

  // risco.* — a camada 3.
  "risco.sobrancelha": "O que pode acontecer",
  "risco.titulo": "Quanto se pode perder em 1 dia",
  "risco.intro":
    "Nove métodos estimam, cada um do seu jeito, o limite da perda de um dia. A plataforma não escolhe nenhum: eles aparecem lado a lado, com o resultado dos testes de cada um.",
  "risco.horizonte": "em 1 dia",
  "risco.nivel.0.0500": "A 95%",
  "risco.nivel.0.0100": "A 99%",
  "risco.faixa": (min: string, max: string) => `${min} a ${max}`,
  "risco.perda95":
    "A 95%, o limite é o valor que a perda de um dia deve respeitar em 19 de cada 20 dias. Em 1 dia a cada 20, espera-se que a perda passe dele.",
  "risco.perda99":
    "A 99%, o limite é o valor que a perda de um dia deve respeitar em 99 de cada 100 dias. Em 1 dia a cada 100, espera-se que a perda passe dele.",
  // A faixa entre os modelos que calcularam (RF-13).
  "risco.discordancia": (
    min: string | null,
    max: string | null,
    n: number,
    total: number,
    cadaN: number,
    unico: string | null,
  ): string => {
    if (n === 0)
      return "Nenhum modelo calculou este nível: o cálculo falhou em todos. A trilha do cálculo mostra o que houve.";
    if (n === 1)
      return `Só um modelo calculou este nível, e não há faixa para comparar: ele põe em ${unico} o limite que a perda de um dia só deve passar em 1 dia a cada ${cadaN}.`;
    const quem =
      n === total
        ? "Os nove modelos põem"
        : `${n} de ${total} modelos calcularam; ${total - n} ${total - n === 1 ? "falhou" : "falharam"}. Eles põem`;
    return `${quem} entre ${min} e ${max} o limite que a perda de um dia só deve passar em 1 dia a cada ${cadaN}. A distância entre eles também é informação: modelos próximos indicam uma leitura mais sólida; distantes, um momento mais incerto, em que o número depende mais do método.`;
  },
  "risco.naoRejeitados.titulo": "Não rejeitados pelos testes",
  // A lista dos adequate = true, sem eleger nenhum (RF-14). Os ramos k = 0 e k ≥ 1 levam a
  // expressão da D-64 aprovada no portão do `risco.html` (T9 do M2.3), "não do número de
  // hoje" — a exceção ao "Fora" da spec; os ramos julgados = 0 e o dos que faltam, intactos.
  "risco.naoRejeitados": (k: number, julgados: number, total: number): string => {
    const faltam = total - julgados;
    const semJulgar =
      faltam > 0
        ? ` ${faltam} ${faltam === 1 ? "modelo não pôde ser julgado" : "modelos não puderam ser julgados"}, porque o cálculo falhou — isso não conta como reprovação.`
        : "";
    if (julgados === 0)
      return "Não foi possível julgar nenhum modelo neste nível: o cálculo falhou em todos, e isso não conta como reprovação.";
    if (k === 0)
      return `Nenhum dos métodos julgados descreveu bem este ativo neste nível${faltam > 0 ? ` (${julgados} de ${total} julgados)` : ""}. Não é erro do cálculo: é informação sobre o ativo — nenhum dos métodos testados acompanhou o comportamento dele no período de teste. O veredito fala desse período, não do número de hoje.${semJulgar}`;
    const quem =
      k === 1
        ? `1 dos ${julgados} modelos julgados passou`
        : `${k} dos ${julgados} modelos julgados passaram`;
    return `${quem} nos testes de Kupiec e de Christoffersen neste nível: os dias em que a perda passou do limite ficaram perto do esperado e não vieram em sequência. O veredito fala do comportamento de cada modelo no período de teste, não do número de hoje; e passar não põe um modelo acima dos outros que também passaram: a lista segue a ordem fixa da tabela.${semJulgar}`;
  },
  "risco.tabela.titulo": "Os nove modelos",
  "risco.tabela.intro":
    "Em ordem fixa, por família de método; a ordem não depende dos números. As barras usam a mesma escala nas duas colunas. Abra um modelo para ver os testes.",
  "risco.tabela.col.modelo": "Modelo",
  "risco.tabela.col.0.0500": "Perda a 95% em 1 dia",
  "risco.tabela.col.0.0100": "Perda a 99% em 1 dia",
  "risco.tabela.abrir": (m: string) => `Ver os testes de ${m}`,
  "risco.categoria.traditional": "Tradicionais",
  "risco.categoria.garch": "GARCH",
  "risco.categoria.ml": "Aprendizado de máquina",
  "risco.modelo.historical": "Histórico",
  "risco.modelo.parametric": "Paramétrico",
  "risco.modelo.monte_carlo": "Monte Carlo",
  "risco.modelo.garch_1_1": "GARCH(1,1)",
  "risco.modelo.egarch": "EGARCH",
  "risco.modelo.lstm": "LSTM",
  "risco.modelo.gru": "GRU",
  "risco.modelo.garchnet": "GARCHNet",
  "risco.modelo.caviar": "CAViaR",
  "risco.tag.adequado": "adequado",
  "risco.tag.naoAdequado": "não adequado",
  "risco.tag.naoJulgado": "não julgado",
  // A expressão da D-64 aprovada no portão do `risco.html` (T9 do M2.3): exceção ao "Fora".
  "risco.veredito":
    "O veredito junta dois testes feitos no período de teste: adequado quando o modelo passa no Kupiec e no Christoffersen; não adequado quando falha em pelo menos um; não julgado quando o cálculo falhou. Fala de como o modelo se comportou no período de teste, não do número de hoje.",
  "risco.teste.passou": "passou",
  "risco.teste.naoPassou": "não passou",
  "risco.rotulo.violacoes": "Violações × esperadas",
  "risco.rotulo.kupiec": "Kupiec",
  "risco.rotulo.christoffersen": "Christoffersen",
  "risco.rotulo.dq": "DQ",
  "risco.violacoes": (v: string, e: string, cadaN: number, kupiecOk: boolean) =>
    `Em ${v} pregões de teste a perda passou do limite, para cerca de ${e} esperados (1 dia a cada ${cadaN}).${kupiecOk ? "" : " Bem acima do esperado, o modelo subestimou o risco; bem abaixo, superestimou."}`,
  "risco.kupiec": (p: string, ok: boolean) =>
    `Confere se a quantidade de dias acima do limite é compatível com a esperada; passa com p-valor acima de 0,05. Aqui, ${p}: ${ok ? "compatível" : "longe demais do esperado para ser acaso"}.`,
  "risco.christoffersen": (p: string, ok: boolean) =>
    `Confere se os dias acima do limite vêm espalhados, e não em sequência; passa com p-valor acima de 0,05. Aqui, ${p}: ${ok ? "vieram espalhados" : "tenderam a vir em sequência"}.`,
  "risco.dq": (p: string, ok: boolean) =>
    `O mais exigente: confere se os dias acima do limite podiam ser previstos pelos anteriores; passa com p-valor acima de 0,05. Aqui, ${p}: ${ok ? "não podiam" : "podiam, em parte"}. Não entra no veredito.`,
  "risco.erroModelo": (msg: string) =>
    `O cálculo deste modelo falhou neste nível (${msg}).`,
  "risco.trilha.titulo": "Trilha do cálculo",
  "risco.trilha":
    "O que entrou neste cálculo — a série, a divisão entre treino e teste e a versão do método —, para que ele possa ser conferido e refeito.",
  "risco.trilha.asOf": "Último pregão usado",
  "risco.trilha.firstPrice": "Primeiro pregão",
  "risco.trilha.priceCount": "Pregões",
  "risco.trilha.train": "Treino",
  "risco.trilha.test": "Teste",
  "risco.trilha.window": "Janela de treino",
  "risco.trilha.calculatedAt": "Calculado em",
  "risco.trilha.finishedAt": "Terminou em",
  "risco.trilha.engine": "Versão do motor",
  "risco.trilha.seed": "Semente",
  "risco.trilha.priceRun": "Coleta de preço",
  "risco.trilha.status": "Situação",
  "risco.trilha.pregoes": (n: string) => `${n} pregões`,
  "risco.trilha.coleta": (fonte: string, quando: string) => `${fonte}, ${quando}`,
  // O instante da trilha, como o `fInstant` do `ativo.html`: "27/09/2026 às 02:50".
  "risco.trilha.instante": (data: string, hora: string) => `${data} às ${hora}`,
  "risco.trilha.fonte.yahoo-chart": "Yahoo Finance",
  "risco.trilha.status.ok": "concluído, os nove modelos calcularam",
  "risco.trilha.status.partial": (n: number) => `parcial: ${n} de 9 modelos falharam`,
  "risco.trilha.status.failed": "o cálculo falhou inteiro",
  // Os controles de recolher da tabela dos nove e da trilha (RF-06, RF-07 do M2.3): do
  // `risco.html` aprovado — um rótulo só, nos dois estados e nos dois níveis.
  "risco.modelos.abrir": "Ver os nove modelos",
  "risco.trilha.abrir": "Ver o que entrou no cálculo",

  // risco.estado.* — os estados da seção (RF-17). `risco.carregando` é só para leitor de
  // tela.
  "risco.carregando": "Carregando o risco deste ativo.",
  "risco.estado.atualiza": "Esta parte da página se atualiza sozinha.",
  "risco.estado.recalculando": (w: number, e: number) =>
    `Recalculando: ${w} de ${e} resultados`,
  "risco.estado.recalculando.nota":
    "Os números abaixo são os do último cálculo. Quando o novo terminar, a página mostra os dele.",
  "risco.estado.recalculando.notaFalha":
    "Um cálculo novo está em andamento. Quando terminar, a página mostra o resultado dele.",
  "risco.estado.E3.titulo": "O último cálculo falhou.",
  "risco.estado.E3":
    "Nenhum modelo chegou a um resultado. A rotina diária calcula o risco deste ativo de novo, sem precisar de pedido. A trilha do cálculo mostra o que entrou nele.",
  "risco.estado.E4": (w: number, e: number) => `Calculando: ${w} de ${e} resultados`,
  "risco.estado.E4.nota": "Cada modelo grava um resultado por nível, 95% e 99%.",
  "risco.estado.E5.fila": "Na fila",
  "risco.estado.E5.fila.nota": "O pedido foi aceito e espera a vez de começar.",
  "risco.estado.E5.coletando": "Coletando preços e métricas",
  "risco.estado.E5.coletando.nota":
    "Antes do risco, o Ruvor coleta a série de preços do ativo e calcula o comportamento dele. Depois, os nove modelos começam.",
  "risco.estado.serieCurta.titulo": "Série curta demais para o risco",
  "risco.estado.serieCurta.nota":
    "Com menos que isso — cerca de dois anos de bolsa —, os modelos não têm como treinar e ser testados. Por isso esta página não oferece o cálculo.",
  "risco.estado.E7.titulo": "O cálculo não terminou.",
  "risco.estado.E7.nota": "Você pode pedir o cálculo de novo.",
  "risco.estado.E8.titulo": "O risco deste ativo ainda não foi calculado.",
  "risco.estado.E8":
    "O cálculo coleta a série de preços, calcula o comportamento e roda os nove modelos. Leva cerca de 2 minutos, e esta parte da página acompanha o andamento.",
  "risco.estado.E9.titulo": "Ativo inativo na B3: o risco não é calculado.",
  "risco.estado.E9": "O cálculo é feito só para ativos em negociação.",

  // risco.pedido.* — o botão e as respostas do POST (RF-19). `erro` leva a mensagem da D-86;
  // `network_error` e `unexpected_response` mostram `semResposta`.
  "risco.pedido.calcular": "Calcular o risco",
  "risco.pedido.deNovo": "Calcular de novo",
  "risco.pedido.enviando": "Enviando o pedido…",
  "risco.pedido.filaCheia": "Muitos cálculos na fila agora; tente em alguns minutos.",
  "risco.pedido.erro": (msg: string) => `O pedido de cálculo não foi aceito. ${msg}`,
  "risco.pedido.semResposta":
    "O pedido de cálculo não teve resposta do servidor. Tente de novo em instantes.",

  // laboratorio.* — a seção do laboratório (M2.4): do `laboratorio.html` aprovado (T9), literais.
  // As nove com frase nas duas leituras (a lista fechada, N = 9) vêm primeiro; a avançada delas
  // mora em `avancado.ts`, e as afirmações são as de `conferencia-laboratorio.md`.
  "laboratorio.decada": (
    inicio: string,
    fim: string,
    anos: number,
    ultimo: number,
  ): string =>
    `De ${inicio} a ${fim}, os dez primeiros anos de preço deste ativo. O primeiro ano serve para os modelos aprenderem; os ${anos} seguintes, para testá-los, um de cada vez${ultimo < 252 ? ` — o último, mais curto, com ${ultimo} pregões` : ""}.`,
  "laboratorio.diferenca": (versao: string, asOf: string): string =>
    `Por que o veredito daqui pode ser diferente do da aba Risco: aqui estão os mesmos nove métodos, mas só nos dez primeiros anos de preço deste ativo, até ${asOf}, calculados uma vez e guardados. A aba Risco é refeita a cada dia útil e inclui os dias depois de ${asOf}. Este resultado, do motor de cálculo ${versao}, não muda enquanto o motor for o mesmo; com um motor novo, o experimento é refeito. E um veredito do passado não garante como o modelo vai se comportar daqui para a frente.`,
  "laboratorio.violacoesAno": (e: string, cadaN: number): string =>
    `Cada número é a quantidade de pregões daquele ano de teste em que a perda passou do limite do modelo. Num ano inteiro, de 252 pregões, espera-se cerca de ${e} (1 dia a cada ${cadaN}); o cabeçalho de cada ano diz quantos eram esperados nele.`,
  "laboratorio.vereditoAno": (celulas: number): string =>
    `A 95%, cada ano de teste tem o próprio veredito: os mesmos dois testes da aba Risco, aplicados só aos dias daquele ano. Nesta grade são ${celulas} anos julgados, e mesmo um modelo sem defeito sai não adequado em cerca de 1 ano a cada 14, só por acaso. O veredito que resume cada modelo é o da década.`,
  "laboratorio.anoNaoJulgado": (n: number): string =>
    `O último ano de teste tem só ${n} pregões, menos de meio ano: é pouco para julgar. Ele mostra quantas vezes a perda passou do limite, sem veredito.`,
  "laboratorio.semVereditoAno99":
    "A 99%, espera-se que a perda passe do limite só 2 ou 3 vezes num ano: é pouco para um teste dizer algo de um ano sozinho — até um ano sem nenhuma vez seria reprovado. Por isso esta grade mostra, ano a ano, só quantas vezes a perda passou do limite, e o veredito fica na década.",
  "laboratorio.violacoesDecada": (
    v: string,
    e: string,
    cadaN: number,
    kupiecOk: boolean,
  ): string =>
    `Na década, ${v === "1" ? "em 1 pregão" : `em ${v} pregões`} de teste a perda passou do limite, para cerca de ${e} esperados (1 dia a cada ${cadaN}): a soma dos anos.${kupiecOk ? "" : acimaDe(v, e) ? " Bem acima do esperado: o modelo subestimou o risco." : " Bem abaixo do esperado: o modelo superestimou o risco."}`,
  "laboratorio.vereditoDecada":
    "O veredito da década junta os mesmos dois testes sobre todos os anos de teste juntos: adequado quando o modelo passa no Kupiec e no Christoffersen; não adequado quando falha em pelo menos um; não julgado quando o cálculo falhou. Fala de como o modelo se comportou nesses anos, não do número de hoje.",
  "laboratorio.anosNaoRejeitados":
    "Em quantos dos anos de teste julgados o modelo não foi rejeitado, a 95%. É um fato de cada modelo, não uma comparação entre eles: a tabela segue sempre a mesma ordem, e um ano ruim de vez em quando — cerca de 1 ano a cada 14 — é esperado mesmo num modelo sem defeito.",
  // Os estados, as notas, os títulos e os rótulos: uma leitura só, fora da lista fechada.
  "laboratorio.sobrancelha": "Laboratório",
  "laboratorio.titulo": "Como os modelos se saíram em dez anos",
  "laboratorio.intro":
    "Os mesmos nove métodos da aba Risco, testados ano a ano nos dez primeiros anos de preço deste ativo. O experimento é calculado uma vez e guardado, e a plataforma não escolhe nenhum método.",
  "laboratorio.carregando": "Carregando o laboratório deste ativo.",
  "laboratorio.estado.falhou.titulo": "O experimento deste ativo falhou.",
  "laboratorio.estado.falhou": (data: string) =>
    `A tentativa de ${data} não chegou a nenhum resultado.`,
  "laboratorio.estado.tentaDeNovo":
    "O experimento é tentado de novo depois do próximo cálculo do risco deste ativo.",
  "laboratorio.estado.aCalcular.titulo":
    "O experimento deste ativo ainda não foi calculado.",
  "laboratorio.estado.aCalcular":
    "Este ativo já tem dez anos de preço e o risco calculado. O experimento roda depois do próximo cálculo do risco deste ativo e aparece aqui ao recarregar a página.",
  "laboratorio.estado.inativo.titulo": "Ativo inativo na B3: o laboratório não roda.",
  "laboratorio.estado.inativo": "O experimento é feito só para ativos em negociação.",
  "laboratorio.estado.semDecada.titulo": "Ainda não há dez anos de preço.",
  "laboratorio.estado.semDecada": (inicio: string, fim: string) =>
    `A série deste ativo começa em ${inicio}, e a década se completa em ${fim}. O experimento roda depois do primeiro cálculo do risco a partir dessa data.`,
  "laboratorio.estado.serieCurta.titulo": "Série curta demais para o laboratório",
  "laboratorio.estado.serieCurta": (n: string, min: string) =>
    `A década deste ativo tem ${n} pregões; o experimento pede no mínimo ${min}.`,
  "laboratorio.estado.semRisco.titulo": "O laboratório vem depois do risco.",
  "laboratorio.estado.semRisco":
    "O experimento roda depois do primeiro cálculo do risco deste ativo. O pedido de cálculo fica na aba Risco.",
  "laboratorio.nota.falha": (data: string) =>
    `A tentativa de refazer o experimento em ${data} falhou. Os números abaixo são os do experimento anterior.`,
  "laboratorio.nota.motor": (antigo: string, novo: string) =>
    `Este experimento é do motor ${antigo}; o do motor ${novo} roda depois do próximo cálculo do risco.`,
  "laboratorio.nota.parcial": (n: number): string =>
    n === 1
      ? "1 dos 9 modelos ficou sem resultado em ao menos um nível neste experimento."
      : `${n} dos 9 modelos ficaram sem resultado em ao menos um nível neste experimento.`,
  "laboratorio.nota.refeito":
    "O experimento é refeito depois do próximo cálculo do risco deste ativo.",
  "laboratorio.grade.titulo.0.0500": "Os dias acima do limite e o veredito de cada ano",
  "laboratorio.grade.titulo.0.0100": "Os dias acima do limite em cada ano",
  "laboratorio.grade.ano": (n: number) => `Ano ${n}`,
  "laboratorio.grade.periodo": (inicio: string, fim: string) => `${inicio} a ${fim}`,
  "laboratorio.grade.esperadas": (e: string) => `${e} esperados`,
  "laboratorio.grade.col.decada": "Década",
  "laboratorio.grade.col.anos": "Anos não rejeitados",
  "laboratorio.grade.kDeN": (k: number, n: number) => `${k} de ${n}`,
  "laboratorio.tag.anoCurto": "curto, sem veredito",
  "laboratorio.testes.abrir": "Ver os testes de cada modelo",
  "laboratorio.grade.anoAAno": "Ano a ano",
  "laboratorio.testes.porAno": "Os testes de cada ano, a 95%",
  "laboratorio.testes.col.ano": "Ano",
  "laboratorio.testes.col.veredito": "Veredito",
  "laboratorio.trilha.titulo": "Trilha do experimento",
  "laboratorio.trilha":
    "O que entrou neste experimento — a década, a divisão entre treino e teste, a versão do método e os preços usados —, para que ele possa ser conferido.",
  "laboratorio.trilha.abrir": "Ver o que entrou no experimento",
  "laboratorio.trilha.decadeEnd": "Fim da década",
  "laboratorio.trilha.years": "Anos de teste",
  "laboratorio.trilha.origin": "Disparado",
  "laboratorio.trilha.origin.risk_close": "depois do cálculo do risco",
  "laboratorio.trilha.origin.command": "pelo operador",
  "laboratorio.trilha.snapshots": "Treinos dos modelos de aprendizado",
  "laboratorio.trilha.retratos": (r: string, t: string) =>
    `${r} reaproveitados, ${t} novos`,
  "laboratorio.trilha.fingerprint": "Impressão digital dos preços",

  // retorno.* — a seção do retorno (M5.1): do `retorno.html` aprovado (T9), com os ajustes da
  // revisão do mockup, literais. As sete com frase nas duas leituras (a lista fechada, N = 7) vêm
  // primeiro; a avançada delas mora em `avancado.ts`, e as afirmações são as de
  // `conferencia-retorno.md`. As funções recebem os valores já formatados.
  "retorno.veredito": (
    ticker: string,
    n: string,
    fim: string,
    batem: readonly ModeloQueBate[],
    naoBatem: readonly string[],
    falhos: number,
  ): string => {
    const periodo = `nos ${n} pregões de teste até ${fim}`;
    if (batem.length === 0 && naoBatem.length === 0)
      return `Não deu para julgar os modelos de ${ticker}: o cálculo dos dois falhou.`;
    if (batem.length === 0) {
      const quem =
        naoBatem.length === 2
          ? "Nenhum dos dois modelos errou"
          : `O modelo ${naoBatem[0]} não errou`;
      const prev =
        naoBatem.length === 2
          ? "as previsões abaixo não são mais informativas"
          : "a previsão dele não é mais informativa";
      return `${quem} menos do que supor retorno zero ao prever o retorno diário de ${ticker}, ${periodo}. Por isso, ${prev} que supor retorno zero.${falhaFrase(falhos)}`;
    }
    const quem =
      batem.length === 2
        ? `Os dois modelos erraram menos do que supor retorno zero ao prever o retorno diário de ${ticker}, ${periodo} (${batem.map(([nm, x]) => `${nm}, ${x} menos`).join("; ")})`
        : `O modelo ${batem[0]?.[0]} errou ${batem[0]?.[1]} menos do que supor retorno zero ao prever o retorno diário de ${ticker}, ${periodo}`;
    const outro = naoBatem.length
      ? ` O modelo ${naoBatem[0]} não errou menos, e a previsão dele não é mais informativa que supor retorno zero.`
      : "";
    return `${quem}, e o teste indica que a diferença dificilmente é acaso nesta série. A vantagem é pequena, e, entre muitos ativos e dois modelos, alguns casos assim aparecem por acaso.${outro}${falhaFrase(falhos)}`;
  },
  "retorno.r2_os": (valor: string, menos: boolean): string =>
    `${menos ? `Errou ${valor} menos` : `Errou ${valor} mais`} do que supor retorno zero nos pregões de teste, medindo o erro de cada dia ao quadrado.`,
  "retorno.acerto": (acerto: string, alta: string): string =>
    `Acertou se o dia seria de alta ou de queda em ${acerto} dos dias; a ação subiu em ${alta} deles. Quem dissesse “alta” todo dia acertaria ${alta}.`,
  "retorno.dm": (p: string, bate: boolean): string =>
    `O teste que decide o veredito: com p-valor abaixo de 0,05, a diferença para o retorno zero dificilmente é acaso. Aqui, ${p}: ${bate ? "bate a referência" : "não bate"}.`,
  "retorno.cw": (p: string): string =>
    `Outro teste do mesmo erro, que desconta o ruído de estimar os parâmetros, já que o zero é um caso particular do modelo. Aqui, ${p}. Não entra no veredito.`,
  "retorno.pt": (p: string | null, todosAlta: boolean | null): string =>
    p !== null
      ? `Confere se o acerto de alta ou queda é maior que o de um palpite ao acaso com as mesmas proporções. Aqui, ${p}. Não entra no veredito.`
      : `O modelo previu ${todosAlta ? "alta" : "queda"} em todos os dias: o acerto dele é a parcela de dias de ${todosAlta ? "alta" : "queda"}, e não há o que testar.`,
  "retorno.previsao": (valor: string, data: string, bate: boolean): string =>
    bate
      ? `O modelo calcula ${valor} para ${data}. É um número estatístico, não uma expectativa nem uma indicação: ter batido a referência no passado não diz que ele acerta o próximo pregão.`
      : `O modelo calcula ${valor} para ${data}; como ele não bate a referência, esse número não é mais informativo que supor retorno zero.`,
  // Os estados, a previsão ausente, os títulos, os rótulos e o aviso: uma leitura só, fora da
  // lista fechada. O `retorno.aviso` é a única entrada `retorno.*` isenta da lista ampliada do
  // RF-21: diz "comprar, vender ou manter" e "vai fazer" de propósito, para negar.
  "retorno.sobrancelha": "Retorno",
  "retorno.titulo": "Os modelos de retorno, postos à prova",
  "retorno.intro":
    "Dois modelos estatísticos simples tentam prever o retorno de cada pregão desta ação, e a plataforma confere, no passado, se eles erraram menos do que supor retorno zero.",
  "retorno.aviso":
    "Esta seção mede se dois modelos estatísticos simples, no passado, teriam errado menos ao prever o retorno diário desta ação do que supor que ele é zero. Não é recomendação de investimento: nada aqui indica comprar, vender ou manter um ativo, e nada aqui diz o que o preço vai fazer. A previsão de cada modelo para o próximo pregão é um número estatístico, não uma expectativa nem uma indicação; a de um modelo que não bate a referência não é mais informativa que supor zero. Não bater essa referência é o resultado mais comum — o retorno de um dia é quase imprevisível. Um modelo que bateu no passado pode deixar de bater, e a vantagem, quando aparece, é pequena.",
  "retorno.carregando": "Carregando a validação do retorno deste ativo.",
  "retorno.estado.inativo.titulo":
    "Ativo inativo na B3: a validação do retorno não é calculada.",
  "retorno.estado.inativo":
    "O cálculo diário é feito só para ativos em negociação e com preço.",
  "retorno.estado.semSerie.titulo": "Não foi possível saber se este ativo tem preço.",
  "retorno.estado.semSerie":
    "A validação depende da série de preços, que não carregou.",
  "retorno.estado.naoCoberto.titulo": "Este ativo ainda não tem preço.",
  "retorno.estado.naoCoberto":
    "A validação do retorno chega junto com o cálculo do risco, que se pede na aba Risco.",
  "retorno.estado.serieCurta.titulo": "Série curta demais para a validação",
  "retorno.estado.serieCurta": (n: string, min: string) =>
    `Este ativo tem ${n} pregões; a validação pede no mínimo ${min}.`,
  "retorno.estado.naoCalculado.titulo":
    "A validação deste ativo ainda não foi calculada.",
  "retorno.estado.naoCalculado": "Ela entra no próximo cálculo diário.",
  "retorno.previsao.inativo":
    "Ativo inativo: a previsão gravada é de quando ele negociava e não é mostrada.",
  "retorno.previsao.passada": (data: string) =>
    `A previsão era para ${data}, que já passou. A próxima entra no próximo cálculo diário.`,
  "retorno.previsao.rotulo": (data: string) => `Previsão do modelo para ${data}`,
  "retorno.previsao.referencia": "referência: 0,00%",
  "retorno.modelo.ar_1": "AR(1)",
  "retorno.modelo.historical_mean": "Média histórica",
  "retorno.tag.bate": "bate a referência",
  "retorno.tag.naoBate": "não bate a referência",
  "retorno.tag.erro": "não deu para calcular",
  "retorno.rotulo.r2": "Erro relativo à referência",
  "retorno.rotulo.acerto": "Acerto de alta ou queda",
  "retorno.rotulo.dm": "Diebold-Mariano",
  "retorno.rotulo.cw": "Clark-West",
  "retorno.rotulo.pt": "Pesaran-Timmermann",
  "retorno.rotulo.mse": "Erro quadrático médio do modelo",
  "retorno.rotulo.mseRef": "Erro quadrático médio de supor zero",
  "retorno.acerto.valor": (acerto: string, alta: string) =>
    `${acerto} · subiu em ${alta}`,
  "retorno.semPt": "sem teste",
  "retorno.erroModelo": (msg: string) => `O cálculo deste modelo falhou (${msg}).`,
  "retorno.detalhes.abrir": "Ver os erros e os outros dois testes",
  "retorno.trilha.abrir": "Ver o que entrou no cálculo",
  "retorno.trilha.titulo": "Trilha do cálculo",
  "retorno.trilha":
    "O que entrou nesta validação — a série, a divisão entre treino e teste, a versão do método e os preços usados —, para que ela possa ser conferida.",
  "retorno.trilha.refit": "Reestimação",
  "retorno.trilha.refitValor": "a cada 252 pregões, em janela que cresce",
  "retorno.trilha.referencia": "Referência",
  "retorno.trilha.referenciaValor": "retorno zero",

  // motivos.* — a tradução de cada motivo de backend/apps/api/ondemand.py (RF-18), por
  // `traduzirMotivo` em `motivos.ts`.
  "motivos.calculado": "O cálculo terminou.",
  "motivos.serieCurta": (n: string, min: string) =>
    `A série tem ${n} pregões; o risco pede no mínimo ${min}.`,
  "motivos.falhouColeta": "A coleta dos preços deste ativo falhou.",
  "motivos.falhouMetricas":
    "Os preços foram coletados, mas o cálculo do comportamento falhou.",
  "motivos.falhouAbertura":
    "Os preços e o comportamento ficaram prontos, mas o cálculo do risco não conseguiu começar.",
  "motivos.execucaoFalhou":
    "O cálculo do risco começou, mas nenhum modelo chegou a um resultado.",
  "motivos.brokerRecusou":
    "O pedido não chegou a entrar na fila de cálculo, por uma falha do servidor.",
  "motivos.expirado": (n: string) =>
    `O pedido passou de ${n} minutos sem terminar e foi encerrado.`,
  "motivos.desconhecido": (raw: string) =>
    `O pedido terminou sem um motivo conhecido (${raw}).`,

  // fundamentos.* — a seção Fundamentos (M1.6c, RF-05 a RF-10): do registro `TEXTOS` do
  // `docs/mockups/M1.6c/ativo-fundamentos.html` aprovado, com o ajuste do portão
  // (`fundamentos.pares.abaixoDeTodas`, no lugar de `posicao` quando k = 0). Os argumentos
  // chegam formatados; `negativo` escolhe o ramo.
  "fundamentos.sobrancelha": "O que o balanço mostra",
  "fundamentos.titulo": "Fundamentos",
  "fundamentos.intro":
    "Os números do último balanço que a companhia entregou à CVM: quanto vendeu, quanto lucrou, quanto deve e quanto vale cada ação no papel. Ao lado de seis deles, a posição da companhia entre as do mesmo grupo na B3.",
  // proveniencia(data do balanço, "ITR"|"DFP", instante do cálculo) — RF-05
  "fundamentos.proveniencia": (ref: string, fonte: string, calc: string) =>
    `balanço de ${ref} (${fonte}), calculado em ${calc}`,
  "fundamentos.fonte.itr": "ITR",
  "fundamentos.fonte.dfp": "DFP",
  "fundamentos.fonteNota":
    "ITR é o balanço trimestral e DFP, o anual; os dois são entregues pela companhia à CVM. Os fundamentos são calculados de novo uma vez por semana.",
  "fundamentos.carregando": "Carregando os fundamentos deste ativo.",
  "fundamentos.naoCalculado.titulo": "Os fundamentos deste ativo não foram calculados.",
  "fundamentos.naoCalculado.indice":
    "O Ibovespa não é uma companhia: não tem balanço, nem fundamentos.",
  "fundamentos.naoCalculado.nota":
    "Eles saem dos balanços trimestrais e anuais entregues à CVM, e o cálculo, semanal, não tem resultado para este ativo.",

  // fundamentos.bloco.* e fundamentos.nota.* — os cinco blocos (RF-06)
  "fundamentos.bloco.resultado": "Resultado em 12 meses",
  "fundamentos.bloco.rentabilidade": "Rentabilidade",
  "fundamentos.bloco.endividamento": "Endividamento",
  "fundamentos.bloco.porAcao": "Por ação e múltiplos",
  "fundamentos.bloco.tamanho": "Tamanho",
  "fundamentos.nota.resultado":
    "Os três somam os quatro últimos trimestres do balanço.",
  "fundamentos.nota.endividamento":
    "A dívida bruta são os empréstimos e financiamentos, incluindo o arrendamento; o caixa inclui as aplicações financeiras.",
  "fundamentos.nota.porAcao":
    "O lucro e o patrimônio por ação usam a quantidade de ações do balanço; o P/L e o P/VP, o preço de um pregão.",
  "fundamentos.nota.tamanho":
    "O patrimônio e o ativo são a posição na data do balanço; o valor de mercado usa o preço das ações.",

  // fundamentos.rotulo.* — o nome de cada número
  "fundamentos.rotulo.revenue_ttm": "Receita líquida",
  "fundamentos.rotulo.ebit_ttm": "Resultado operacional (EBIT)",
  "fundamentos.rotulo.net_income_ttm": "Lucro líquido",
  "fundamentos.rotulo.net_margin": "Margem líquida",
  "fundamentos.rotulo.ebit_margin": "Margem operacional (EBIT)",
  "fundamentos.rotulo.roe": "Retorno sobre o patrimônio (ROE)",
  "fundamentos.rotulo.gross_debt": "Dívida bruta",
  "fundamentos.rotulo.cash": "Caixa e aplicações",
  "fundamentos.rotulo.net_debt": "Dívida líquida",
  "fundamentos.rotulo.net_debt_to_equity": "Dívida líquida sobre o patrimônio",
  "fundamentos.rotulo.close": "Preço usado",
  "fundamentos.rotulo.eps": "Lucro por ação (LPA)",
  "fundamentos.rotulo.bvps": "Patrimônio por ação (VPA)",
  "fundamentos.rotulo.pe": "Preço sobre lucro (P/L)",
  "fundamentos.rotulo.pb": "Preço sobre patrimônio (P/VP)",
  "fundamentos.rotulo.equity_parent": "Patrimônio líquido",
  "fundamentos.rotulo.total_assets": "Ativo total",
  "fundamentos.rotulo.market_cap": "Valor de mercado",
  "fundamentos.vezes": (x: string) => `${x} vezes`,
  "fundamentos.semValor": "sem valor",

  // fundamentos.<campo> — a frase de cada número presente (D-97). negativo: boolean.
  "fundamentos.revenue_ttm":
    "O que a companhia vendeu nos últimos 12 meses, descontados os impostos sobre a venda, as devoluções e os abatimentos.",
  "fundamentos.ebit_ttm": (negativo: boolean): string =>
    negativo
      ? "Negativo: a operação deu prejuízo nos últimos 12 meses, antes dos juros e dos impostos sobre o lucro."
      : "O que a operação rendeu nos últimos 12 meses, antes dos juros e dos impostos sobre o lucro.",
  "fundamentos.net_income_ttm": (negativo: boolean): string =>
    negativo
      ? "Negativo: nos últimos 12 meses, custos, juros e impostos passaram do que a companhia vendeu, e ela teve prejuízo."
      : "O que sobrou para os acionistas da companhia nos últimos 12 meses, depois de custos, juros e impostos.",
  // margens e ROE: (cada R$ 100 → valor, negativo)
  "fundamentos.net_margin": (x: string, negativo: boolean) =>
    negativo
      ? `De cada R$ 100 vendidos, a companhia perdeu ${x}.`
      : `De cada R$ 100 vendidos, ${x} viraram lucro para os acionistas.`,
  "fundamentos.ebit_margin": (x: string, negativo: boolean) =>
    negativo
      ? `De cada R$ 100 vendidos, a operação perdeu ${x}, antes de juros e impostos.`
      : `De cada R$ 100 vendidos, ${x} sobraram da operação, antes de juros e impostos.`,
  "fundamentos.roe": (x: string, negativo: boolean) =>
    negativo
      ? `Cada R$ 100 do patrimônio dos acionistas tiveram ${x} de prejuízo nos últimos 12 meses.`
      : `Cada R$ 100 do patrimônio dos acionistas geraram ${x} de lucro nos últimos 12 meses.`,
  "fundamentos.gross_debt":
    "Os empréstimos e financiamentos, de curto e de longo prazo, incluindo o arrendamento — os aluguéis de longo prazo que o balanço conta como dívida.",
  "fundamentos.cash": "O dinheiro em caixa mais as aplicações financeiras.",
  "fundamentos.net_debt": (negativo: boolean): string =>
    negativo
      ? "Negativa: o caixa é maior que a dívida bruta."
      : "A dívida bruta menos o caixa: o que restaria de dívida se todo o caixa fosse usado para pagá-la.",
  "fundamentos.net_debt_to_equity": (x: string, negativo: boolean) =>
    negativo
      ? "Negativa: o caixa é maior que a dívida bruta, e não sobra dívida para comparar com o patrimônio."
      : `A dívida líquida perto do patrimônio dos acionistas: para cada R$ 100 de patrimônio, ${x} de dívida líquida.`,
  // close(data do preço) e closeOutraData(data do preço, último pregão da identidade) — RF-06
  "fundamentos.close": (data: string) =>
    `O fechamento de ${data}, o preço que entra no P/L e no P/VP.`,
  "fundamentos.closeOutraData": (data: string, ultimo: string) =>
    `O fechamento de ${data}, não o do último pregão coletado (${ultimo}): os fundamentos são calculados uma vez por semana, com o último preço de até 10 dias antes do cálculo.`,
  // eps(quantidade de ações, negativo), bvps(quantidade de ações)
  "fundamentos.eps": (acoes: string, negativo: boolean) =>
    negativo
      ? `O prejuízo dos últimos 12 meses dividido pelas ${acoes} ações da companhia, somadas todas as classes.`
      : `O lucro dos últimos 12 meses dividido pelas ${acoes} ações da companhia, somadas todas as classes.`,
  "fundamentos.bvps": (acoes: string) =>
    `O patrimônio dos acionistas dividido pelas mesmas ${acoes} ações.`,
  // pe(data, preço, P/L com uma casa, negativo) e pb(data, preço, P/VP) — o preço usado (RF-06)
  "fundamentos.pe": (data: string, preco: string, x: string, negativo: boolean) =>
    negativo
      ? `Negativo porque a companhia teve prejuízo nos últimos 12 meses. Com o fechamento de ${data}, ${preco}, ele não diz em quantos anos o lucro pagaria o preço: não houve lucro.`
      : `O preço dividido pelo lucro por ação, com o fechamento de ${data}, ${preco}: o preço equivale a ${x} anos do lucro dos últimos 12 meses.`,
  "fundamentos.pb": (data: string, preco: string, x: string) =>
    `O preço dividido pelo patrimônio por ação, com o fechamento de ${data}, ${preco}: a bolsa paga ${x} vezes o valor que o balanço dá a cada ação.`,
  "fundamentos.equity_parent": (negativo: boolean): string =>
    negativo
      ? "Negativo: a companhia deve mais do que tem, descontada a parte dos sócios de fora nas controladas."
      : "O que é dos acionistas da companhia: tudo o que ela tem, menos o que deve e a parte dos sócios de fora nas controladas.",
  "fundamentos.total_assets":
    "Tudo o que a companhia tem no balanço: caixa, créditos a receber, estoques, investimentos, imóveis e equipamentos.",
  "fundamentos.market_cap":
    "O preço de cada classe de ação vezes a quantidade dela, somados: quanto a bolsa diz que a companhia inteira vale.",

  // fundamentos.nulo.* — o porquê de cada nulo (RF-07), pela atribuição de `nulos.ts`. bank e
  // insurance dividem a frase.
  "fundamentos.nulo.planoFinanceiro":
    "Bancos e seguradoras publicam o balanço em outro formato, e este número não se aplica a eles.",
  "fundamentos.nulo.planoDesconhecido":
    "O plano de contas desta companhia não foi reconhecido, e receita, margens e dívida não são calculadas.",
  "fundamentos.nulo.porAcao.unit":
    "Este código é uma unit, um pacote com ações de mais de uma classe: o preço e os números por ação não valem para ele.",
  "fundamentos.nulo.porAcao.stale_statement":
    "O último balanço entregue tem mais de 460 dias, velho demais para os números por ação e para o preço de hoje.",
  "fundamentos.nulo.porAcao.no_share_count":
    "O balanço não informa a quantidade de ações — a CVM só a traz de 2020 em diante —, e sem ela não há número por ação.",
  "fundamentos.nulo.porAcao.share_scale_unknown":
    "O balanço informa a quantidade de ações sem dizer se ela está em unidades ou em milhares, e não foi possível descobrir; sem isso, não há número por ação.",
  "fundamentos.nulo.porAcao.no_price":
    "Não há preço desta ação coletado até 10 dias antes do cálculo, e sem preço não há P/L nem P/VP.",
  "fundamentos.nulo.valorMercado.stale_statement":
    "O último balanço entregue tem mais de 460 dias, e a quantidade de ações dele não serve para o valor de mercado de hoje.",
  "fundamentos.nulo.valorMercado.no_share_count":
    "O balanço não informa a quantidade de ações — a CVM só a traz de 2020 em diante —, e sem ela não há valor de mercado.",
  "fundamentos.nulo.valorMercado.share_scale_unknown":
    "O balanço informa a quantidade de ações sem dizer se ela está em unidades ou em milhares, e não foi possível descobrir; sem isso, não há valor de mercado.",
  "fundamentos.nulo.valorMercado.ambiguous_class":
    "A companhia tem mais de um código negociado na mesma classe de ação, e não há como saber qual preço usar.",
  "fundamentos.nulo.valorMercado.no_price":
    "Não há preço coletado de nenhuma classe de ação da companhia.",
  "fundamentos.nulo.valorMercado.missing_class_price":
    "Falta o preço de uma das classes de ação da companhia, ordinária ou preferencial, e o valor de mercado soma todas.",
  "fundamentos.nulo.generico": "O balanço não permite calcular este número.",

  // fundamentos.pares.* — o grupo e a posição (RF-09, RF-10). Sem julgar: acima não é bom.
  "fundamentos.pares.segmento": (segmento: string) =>
    `Comparado com as companhias do segmento ${segmento}, na B3.`,
  "fundamentos.pares.subsetor": (subsetor: string) =>
    `Comparado com as companhias do subsetor ${subsetor}, na B3: o segmento desta companhia não formou grupo, porque tem menos de três companhias ou não está informado.`,
  "fundamentos.pares.nenhum":
    "Não há companhias comparáveis suficientes no segmento nem no subsetor desta companhia.",
  "fundamentos.pares.indisponivel":
    "A comparação com os pares não está disponível para este cálculo.",
  "fundamentos.pares.leitura":
    "A posição diz acima de quantas companhias do grupo o número está, contando só as que têm aquele indicador calculado. Acima não quer dizer bom, nem abaixo quer dizer ruim: numa dívida, estar acima é dever mais.",
  "fundamentos.pares.rotulo": "Entre os pares",
  // posicao(k, n − 1) — k = round(percentile × (n − 1)), n = count
  "fundamentos.pares.posicao": (k: string, outras: string) =>
    `Acima de ${k} das outras ${outras} companhias do grupo com este indicador calculado.`,
  // abaixoDeTodas(n − 1) — no lugar de posicao quando k = 0 (ajuste do portão, 2026-09-29).
  // "Nenhuma … tem número menor", não "abaixo de todas": o percentil conta só os estritamente
  // menores, e o empate no menor valor também dá k = 0 (terceira exceção ao "Fora" do M2.3).
  "fundamentos.pares.abaixoDeTodas": (outras: string) =>
    `Nenhuma das outras ${outras} companhias do grupo com este indicador calculado tem número menor.`,
  "fundamentos.pares.mediana": (m: string) => `Mediana do grupo: ${m}.`,
  "fundamentos.pares.semComparacao": "Sem comparação para este indicador.",

  // comunicados.* — a seção Comunicados (M1.6c, RF-11 a RF-14): do registro `TEXTOS` do
  // `docs/mockups/M1.6c/ativo-fundamentos.html` aprovado. Nenhuma forma da palavra da imprensa
  // (D-130). Os argumentos chegam formatados.
  "comunicados.sobrancelha": "O que a companhia divulgou",
  "comunicados.titulo": "Comunicados da companhia à CVM",
  "comunicados.intro":
    "Fatos relevantes, comunicados ao mercado e avisos aos acionistas: o que a companhia é obrigada a divulgar, do jeito que ela entregou à CVM. A lista vem da CVM uma vez por dia, não em tempo real.",
  "comunicados.saida":
    "Cada título abre o documento no site da CVM, fora do Ruvor, numa aba nova.",
  "comunicados.linkSaida": "abre no site da CVM, fora do Ruvor, numa aba nova",
  "comunicados.companhia": (nome: string, codigo: string) =>
    `Entregues por ${nome}, código ${codigo} na CVM.`,
  "comunicados.companhiaSemNome": (codigo: string) =>
    `Entregues pela companhia de código ${codigo} na CVM.`,
  "comunicados.filtro.rotulo": "Categoria dos comunicados",
  "comunicados.filtro.todas": "Todas",
  "comunicados.filtro.fato_relevante": "Fatos relevantes",
  "comunicados.filtro.comunicado": "Comunicados ao mercado",
  "comunicados.filtro.aviso_acionistas": "Avisos aos acionistas",
  "comunicados.categoria.fato_relevante": "fato relevante",
  "comunicados.categoria.comunicado": "comunicado ao mercado",
  "comunicados.categoria.aviso_acionistas": "aviso aos acionistas",
  "comunicados.entregueEm": "Entregue em",
  "comunicados.referencia": (data: string) => `Referente a ${data}.`,
  "comunicados.mostrando": (mostrados: string, total: string) =>
    `Mostrando ${mostrados} de ${total}.`,
  "comunicados.mostrarMais": "Mostrar mais",
  "comunicados.carregandoMais": "Carregando mais comunicados…",
  "comunicados.erroMais": "Não foi possível carregar mais comunicados.",
  "comunicados.carregando": "Carregando os comunicados desta companhia.",
  "comunicados.vazio":
    "A companhia não entregou comunicados destas categorias desde 2016.",
  // filtroVazio(categoria no singular, de comunicados.categoria.*)
  "comunicados.filtroVazio": (categoria: string) =>
    `Nenhum ${categoria} entregue pela companhia desde 2016.`,
  "comunicados.verTodas": "Ver todas as categorias",
  "comunicados.indice": "O Ibovespa não é uma companhia e não entrega comunicados.",
  "comunicados.semCodigo":
    "O catálogo não tem o código desta companhia na CVM, e os comunicados dela não puderam ser ligados.",
  "comunicados.semLigacao": "Os comunicados desta companhia não puderam ser ligados.",

  // acesso.* — a tela de entrada (M2.1b, RF-06): do registro `TEXTOS` do
  // `docs/mockups/M2.1b/entrada.html` aprovado. Os sobretítulos ficam em caixa normal, como
  // `busca.eyebrow`; a folha os põe em maiúsculas. A mensagem da API nunca entra aqui: a tela
  // traduz pelo `code`.
  "acesso.cena.marca": "Ruvor",
  "acesso.cena.eyebrow": "Inteligência de risco",
  "acesso.cena.titulo": "Decisões financeiras com evidência à vista.",
  "acesso.cena.texto":
    "Veja quanto uma ação pode perder, por nove modelos sobre a mesma base, com o método à vista.",
  "acesso.eyebrow": "Acesso à plataforma",
  "acesso.titulo": "Que bom te ver de novo.",
  "acesso.sub": "Entre com o e-mail e a senha da sua conta.",
  "acesso.email.rotulo": "E-mail",
  "acesso.email.placeholder": "nome@exemplo.com",
  "acesso.senha.rotulo": "Senha",
  "acesso.senha.nota":
    "Não há recuperação de senha por e-mail. Numa organização, peça uma senha provisória a quem a administra; numa conta pessoal, a senha não pode ser recuperada.",
  "acesso.entrar": "Entrar",
  "acesso.entrando": "Entrando…",
  "acesso.semConta": "Ainda não tem conta?",
  "acesso.criarConta": "Criar conta",
  "acesso.continuar": "Continuar sem entrar",
  "acesso.erro.emailVazio": "Informe o e-mail.",
  "acesso.erro.senhaVazia": "Informe a senha.",
  "acesso.erro.credenciais": "E-mail ou senha incorretos.",
  // tentativas(n) — n: `details.wait_seconds`, inteiro; ausente (null) → a frase sem o número;
  // de 60 s em diante, em minutos arredondados para cima (o bloqueio por e-mail e IP dura 900 s).
  "acesso.erro.tentativas": (n: number | null): string =>
    n == null
      ? "Muitas tentativas. Aguarde um pouco e tente de novo."
      : n < 60
        ? `Muitas tentativas. Tente de novo em ${n} s.`
        : `Muitas tentativas. Tente de novo em ${Math.ceil(n / 60)} min.`,
  "acesso.erro.csrf": "A página ficou desatualizada. Recarregue e tente de novo.",
  "acesso.erro.rede": "Não foi possível falar com o servidor. Tente de novo.",
  "acesso.erro.outro": "Não foi possível entrar agora. Tente de novo.",
  // A dica da senha e a confirmação diferente, compartilhadas pelo cadastro e pelas duas trocas
  // de senha (os portões da T6 e da T7): do registro `COMPARTILHADOS` do `senha.html` aprovado,
  // o mesmo texto do `cadastro.html`. Cada requisito é um validador de `AUTH_PASSWORD_VALIDATORS`.
  "acesso.senha.dica": "A senha precisa:",
  "acesso.senha.requisito.tamanho": "ter no mínimo 10 caracteres;",
  "acesso.senha.requisito.numeros": "não ser só números;",
  "acesso.senha.requisito.parecida": "não ser parecida com o seu e-mail ou o seu nome;",
  "acesso.senha.requisito.comum": "não ser uma senha comum.",
  "acesso.erro.confirmacaoDiferente": "As duas senhas não são iguais.",

  // cadastro.* — criar conta (M2.1b, RF-07): do registro `TEXTOS` do
  // `docs/mockups/M2.1b/cadastro.html` aprovado, as chaves novas; as da entrada são reaproveitadas.
  // As mensagens da API por campo (`details.fields`) não entram aqui: são dado.
  "cadastro.titulo": "Crie a sua conta.",
  "cadastro.sub": "Informe o seu nome, o e-mail e uma senha.",
  "cadastro.nome.rotulo": "Nome",
  "cadastro.confirmacao.rotulo": "Repita a senha",
  "cadastro.pessoal": "A conta é pessoal: você é a única pessoa da organização dela.",
  "cadastro.pessoal.organizacao":
    "Se você vai usar o Ruvor numa organização, peça a conta a quem a administra.",
  "cadastro.criar": "Criar conta",
  "cadastro.criando": "Criando a conta…",
  "cadastro.temConta": "Já tem conta?",
  "cadastro.erro.nomeVazio": "Informe o nome.",
  "cadastro.erro.confirmacaoVazia": "Repita a senha.",
  "cadastro.erro.emailTaken": "Este e-mail já tem conta.",
  "cadastro.erro.emailTakenLink": "Entrar",
  "cadastro.erro.outro": "Não foi possível criar a conta agora. Tente de novo.",

  // senha.* — trocar a senha, voluntária e obrigatória (M2.1b, RF-08): do registro `TEXTOS` do
  // `docs/mockups/M2.1b/senha.html` aprovado.
  "senha.eyebrow": "Sua conta",
  "senha.titulo": "Trocar a senha",
  "senha.sub": "Confirme a senha atual e escolha uma nova.",
  "senha.obrigatoria.eyebrow": "Senha provisória",
  "senha.obrigatoria.titulo": "Troque a senha para continuar.",
  "senha.obrigatoria.sub":
    "A sua senha é provisória e precisa ser trocada antes de usar o Ruvor.",
  // conta(email) — o e-mail de quem entrou (`me.email`).
  "senha.obrigatoria.conta": (email: string): string => `Você entrou como ${email}.`,
  "senha.obrigatoria.sair": "Sair",
  "senha.atual.rotulo": "Senha atual",
  "senha.nova.rotulo": "Senha nova",
  "senha.confirmacao.rotulo": "Repita a senha nova",
  "senha.trocar": "Trocar a senha",
  "senha.trocando": "Trocando…",
  "senha.erro.atualVazia": "Informe a senha atual.",
  "senha.erro.novaVazia": "Informe a senha nova.",
  "senha.erro.confirmacaoVazia": "Repita a senha nova.",
  "senha.erro.atualIncorreta": "Senha atual incorreta.",
  "senha.erro.outro": "Não foi possível trocar a senha agora. Tente de novo.",
  "senha.sucesso.titulo": "Senha trocada.",
  "senha.sucesso.texto":
    "As outras sessões desta conta foram encerradas. Esta continua aberta.",
  "senha.sucesso.continuar": "Continuar",

  // conta.* — o menu de conta (RF-09, RF-10), o convite a entrar para calcular (RF-15) e os dois
  // avisos do RF-16: do registro `TEXTOS` do `docs/mockups/M2.1b/conta.html` aprovado. Nenhuma é
  // número com frase: não têm leitura avançada.
  "conta.entrar": "Entrar",
  // rotulo(nome) — o `aria-label` do botão de conta, com o nome de quem entrou (`me.name`).
  "conta.menu.rotulo": (nome: string): string => `Conta de ${nome}`,
  "conta.menu.organizacao": "Organização",
  "conta.menu.pessoal": "Conta pessoal",
  "conta.menu.senha": "Trocar a senha",
  "conta.menu.usuarios": "Usuários da organização",
  "conta.menu.sair": "Sair",
  "conta.menu.sairFalhou": "Não foi possível sair agora. Tente de novo.",
  "conta.convite.entrar": "Entrar para calcular",
  "conta.convite.frase": "Pedir um cálculo exige entrar na conta.",
  "conta.aviso.terminou": "A sua sessão terminou.",
  "conta.aviso.paraQuemEntrou": "Esta página é para quem entrou na conta.",
  "conta.aviso.volta": "Depois de entrar, você volta para esta página.",

  // usuarios.* — a gestão de usuários (M2.1b, RF-11 a RF-14): do registro `TEXTOS` do
  // `docs/mockups/M2.1b/usuarios.html` aprovado, com o papel `admin` mostrado como
  // "Administração" (o portão da T9). Os avisos do RF-16 são os `conta.aviso.*`. As mensagens
  // da API por campo (`details.fields`) não entram aqui: são dado. Nenhuma é número com frase:
  // não têm leitura avançada.
  // A página.
  "usuarios.eyebrow": "Organização",
  "usuarios.titulo": "Usuários da organização",
  // sub(org) — o nome da organização (`me.organization.name`).
  "usuarios.sub": (org: string): string =>
    `Quem entra no Ruvor pela ${org}. Aqui você cria contas, muda o papel de cada pessoa, desativa quem não deve mais entrar e gera senhas provisórias.`,
  // A criação (RF-13).
  "usuarios.criar.titulo": "Novo usuário",
  "usuarios.criar.texto":
    "A conta nasce com uma senha provisória, que a pessoa troca no primeiro acesso. O Ruvor não envia e-mail: a senha aparece para você entregar.",
  "usuarios.campo.nome": "Nome",
  "usuarios.campo.email": "E-mail",
  "usuarios.campo.email.exemplo": "nome@exemplo.com",
  "usuarios.campo.papel": "Papel",
  "usuarios.campo.papel.dica":
    "Membro usa o Ruvor. Administração usa e também gere os usuários desta página.",
  "usuarios.papel.member": "Membro",
  "usuarios.papel.admin": "Administração",
  "usuarios.criar.botao": "Criar usuário",
  "usuarios.criar.enviando": "Criando…",
  // Os erros.
  "usuarios.erro.nomeVazio": "Informe o nome.",
  "usuarios.erro.emailVazio": "Informe o e-mail.",
  "usuarios.erro.emailTaken": "Este e-mail já tem conta no Ruvor.",
  // muitos(n) — n: `details.wait_seconds`; sem ele, `usuarios.erro.muitosSemTempo`.
  "usuarios.erro.muitos": (n: number): string =>
    `Muitos pedidos seguidos. Tente de novo em ${n} s.`,
  "usuarios.erro.muitosSemTempo":
    "Muitos pedidos seguidos. Aguarde um pouco e tente de novo.",
  "usuarios.erro.csrf": "A página ficou desatualizada. Recarregue e tente de novo.",
  "usuarios.erro.rede": "Não foi possível falar com o servidor. Tente de novo.",
  "usuarios.erro.outro": "Não foi possível concluir agora. Tente de novo.",
  "usuarios.erro.lastAdmin":
    "A organização precisa de ao menos uma pessoa ativa na administração. Mude outra pessoa para administração antes.",
  "usuarios.erro.naoEncontrado":
    "Esta pessoa não está mais na organização. A lista foi atualizada.",
  // A lista (RF-11).
  "usuarios.lista.titulo": "Usuários",
  // contagem(n) — o `count` da API.
  "usuarios.lista.contagem": (n: number): string =>
    n === 1 ? "1 usuário" : `${n} usuários`,
  "usuarios.col.nome": "Nome",
  "usuarios.col.email": "E-mail",
  "usuarios.col.papel": "Papel",
  "usuarios.col.situacao": "Situação",
  "usuarios.col.ultimoAcesso": "Último acesso",
  "usuarios.col.acoes": "Ações",
  "usuarios.voce": "você",
  "usuarios.situacao.ativa": "ativa",
  "usuarios.situacao.desativada": "desativada",
  "usuarios.provisoria": "senha provisória por trocar",
  "usuarios.nuncaEntrou": "nunca entrou",
  // ultimoAcesso(data, hora) — o `last_login` no fuso da B3, já formatado.
  "usuarios.ultimoAcesso": (data: string, hora: string): string => `${data} às ${hora}`,
  // mostrando(n, total) — as linhas na tela e o `count` da API.
  "usuarios.mostrando": (n: number, total: number): string =>
    `Mostrando ${n} de ${total}.`,
  "usuarios.mostrarMais": "Mostrar mais",
  "usuarios.erroLista": "Não foi possível carregar a lista de usuários.",
  "usuarios.erroMais": "Não foi possível carregar mais usuários.",
  "usuarios.tentarDeNovo": "Tentar de novo",
  // As ações da linha (RF-14). acoes.rotulo(nome) — o `aria-label` do grupo de botões.
  "usuarios.acoes.rotulo": (nome: string): string => `Ações para ${nome}`,
  "usuarios.acao.admin": "Mudar para administração",
  "usuarios.acao.member": "Mudar para membro",
  "usuarios.acao.desativar": "Desativar",
  "usuarios.acao.reativar": "Reativar",
  "usuarios.acao.senha": "Nova senha provisória",
  // As confirmações (RF-14); os títulos com o nome da pessoa da linha.
  "usuarios.confirmar.admin.titulo": (nome: string): string =>
    `Mudar ${nome} para administração?`,
  "usuarios.confirmar.admin.texto":
    "A pessoa passa a ver esta página e a criar, mudar, desativar e reativar os usuários da organização, e a gerar senhas provisórias para eles.",
  "usuarios.confirmar.member.titulo": (nome: string): string =>
    `Mudar ${nome} para membro?`,
  "usuarios.confirmar.member.texto":
    "A pessoa deixa de gerir os usuários da organização. O resto do Ruvor continua igual para ela.",
  "usuarios.confirmar.rebaixarSi.titulo": "Deixar de administrar a organização?",
  "usuarios.confirmar.rebaixarSi.texto":
    "Você passa a membro e perde a gestão dos usuários: esta página deixa de abrir para você. Para voltar à administração, outra pessoa da administração precisa mudar o seu papel.",
  "usuarios.confirmar.desativar.titulo": (nome: string): string => `Desativar ${nome}?`,
  "usuarios.confirmar.desativar.texto":
    "A pessoa deixa de conseguir entrar. As sessões abertas e as chaves de API dela são encerradas agora. A conta continua na lista e pode ser reativada.",
  "usuarios.confirmar.reativar.titulo": (nome: string): string => `Reativar ${nome}?`,
  "usuarios.confirmar.reativar.texto":
    "A pessoa volta a entrar com a senha que já tinha. As chaves de API encerradas na desativação não voltam.",
  "usuarios.confirmar.senha.titulo": (nome: string): string =>
    `Gerar uma senha provisória nova para ${nome}?`,
  "usuarios.confirmar.senha.texto":
    "A senha atual da pessoa deixa de valer, e as sessões abertas e as chaves de API dela são encerradas agora. A senha nova aparece uma vez, para você entregar.",
  "usuarios.confirmar.desativada":
    "A conta está desativada: a mudança vale quando ela for reativada.",
  "usuarios.confirmar.cancelar": "Cancelar",
  "usuarios.confirmar.fechar": "Fechar",
  "usuarios.confirmar.enviando": "Enviando…",
  // O diálogo da senha provisória (RF-13, RF-14); os textos com o nome e o e-mail da pessoa.
  "usuarios.senha.criado.titulo": "Usuário criado",
  "usuarios.senha.criado.texto": (nome: string, email: string): string =>
    `${nome} (${email}) já pode entrar, com a senha provisória abaixo.`,
  "usuarios.senha.nova.titulo": "Senha provisória nova",
  "usuarios.senha.nova.texto": (nome: string, email: string): string =>
    `A senha de ${nome} (${email}) foi trocada por esta. As sessões e as chaves de API da pessoa foram encerradas.`,
  "usuarios.senha.campo": "Senha provisória",
  "usuarios.senha.umaVez":
    "Ela aparece só agora. Depois de fechar esta janela, não será mostrada de novo.",
  "usuarios.senha.trocar":
    "No primeiro acesso, a pessoa entra com ela e precisa trocá-la antes de usar o Ruvor.",
  "usuarios.senha.entrega":
    "O Ruvor não envia e-mail: entregue a senha à pessoa por outro meio, de forma reservada.",
  "usuarios.senha.copiar": "Copiar",
  "usuarios.senha.copiada": "Copiada",
  "usuarios.senha.copiadaAviso": "Senha copiada para a área de transferência.",
  "usuarios.senha.copiaFalhou":
    "Não foi possível copiar. Selecione a senha e copie com o teclado.",
  "usuarios.senha.fechar": "Fechar",
  // Quem não pode gerir (RF-12). membro.texto(org) — o nome da organização.
  "usuarios.membro.titulo": "Só quem administra a organização gere os usuários.",
  "usuarios.membro.texto": (org: string): string =>
    `Você é membro da ${org}. Para criar uma conta, mudar um papel ou gerar uma senha provisória, fale com quem administra a organização.`,
  "usuarios.pessoal.titulo": "A conta pessoal não tem outros usuários.",
  "usuarios.pessoal.texto":
    "Ela é só sua. Uma organização com várias pessoas é criada pela equipe que opera o Ruvor.",

  // As carteiras (M2.2b, RF-01 a RF-06, D-180, D-181): o registro TEXTOS do `lista.html`
  // aprovado, literal. Nenhuma é número com frase (D-97): não ganham leitura avançada.
  "carteiras.nav": "Carteiras",
  "carteiras.nav.rotulo": "Navegação",
  "carteiras.eyebrow": "Carteiras",
  "carteiras.titulo": "Quanto a sua carteira pode perder?",
  "carteiras.sub":
    "Monte a carteira com as ações e os pesos que você escolher. A plataforma estima a perda de 1 dia nos nove modelos, lado a lado.",
  "carteiras.sub.organizacao": (org: string): string =>
    `As carteiras são da organização ${org}: quem é dela vê e muda cada uma.`,
  "carteiras.nova": "Nova carteira",
  "carteiras.lista.titulo": "As carteiras",
  "carteiras.lista.contagem": (n: number): string =>
    n === 1 ? "1 carteira" : `${formatInteger(n)} carteiras`,
  "carteiras.col.nome": "Nome",
  "carteiras.col.acoes": "Ações",
  "carteiras.col.versao": "Versão",
  "carteiras.col.valor": "Valor",
  "carteiras.col.mudou": "Composição mudou em",
  "carteiras.acoes": (n: number): string =>
    n === 1 ? "1 ação" : `${formatInteger(n)} ações`,
  "carteiras.semValor": "sem valor",
  "carteiras.lista.carregando": "Carregando as carteiras.",
  "carteiras.lista.vazia.titulo": "Nenhuma carteira ainda.",
  "carteiras.lista.vazia.texto":
    "Uma carteira junta de 2 a 20 ações, cada uma com o peso que você der. Depois de criada, a plataforma calcula quanto ela pode perder em 1 dia.",
  "carteiras.lista.vazia.criar": "Criar a primeira carteira",
  "carteiras.lista.erro.titulo": "A lista de carteiras não carregou.",
  "carteiras.lista.erro.texto": "Pode ser uma falha passageira do servidor.",
  "carteiras.tentarDeNovo": "Tentar de novo",
  "carteiras.mostrarMais": "Mostrar mais",
  "carteiras.mostrando": (a: number, n: number): string =>
    `Mostrando ${formatInteger(a)} de ${formatInteger(n)}.`,
  "carteiras.carregandoMais": "Carregando mais carteiras…",
  "carteiras.maisErro": "As próximas carteiras não carregaram.",
  "carteiras.arquivada": (nome: string): string =>
    `A carteira “${nome}” foi arquivada. O que foi calculado para ela fica guardado.`,
  "carteiras.criar.titulo": "Nova carteira",
  "carteiras.campo.nome": "Nome",
  "carteiras.campo.nomeDica": "Até 100 caracteres.",
  "carteiras.campo.valor": "Valor (opcional)",
  "carteiras.campo.valorDica":
    "Em reais, como 10.000,00. Com o valor, a perda aparece também em reais; sem ele, só em %.",
  "carteiras.composicao.titulo": "Composição",
  "carteiras.composicao.dica":
    "De 2 a 20 ações. O peso de cada uma é em %, com até 2 casas, e a soma fecha em 100,00.",
  "carteiras.seletor.rotulo": "Acrescentar ação",
  "carteiras.seletor.placeholder": "Código ou nome da ação",
  "carteiras.seletor.motivo.indice": "Índice: a carteira só aceita ações.",
  "carteiras.seletor.motivo.inativa": "Ação inativa: não entra na carteira.",
  "carteiras.seletor.motivo.naComposicao": "Já está na composição.",
  "carteiras.seletor.nenhumaServe": (q: string): string =>
    `Nada do que a busca por “${q}” trouxe pode entrar na carteira.`,
  "carteiras.seletor.nenhumaServeDica":
    "Só ação ativa entra. Tente um termo mais preciso, como o código da ação.",
  "carteiras.seletor.limite": "A composição já tem 20 ações, o máximo.",
  "carteiras.col.acao": "Ação",
  "carteiras.col.peso": "Peso (%)",
  "carteiras.col.remover": "Remover",
  "carteiras.peso.rotulo": (ticker: string): string => `Peso de ${ticker}, em %`,
  "carteiras.remover": (ticker: string): string => `Remover ${ticker} da composição`,
  "carteiras.editor.vazio":
    "Nenhuma ação na composição ainda. Busque acima pelo código ou pelo nome.",
  "carteiras.soma.rotulo": "Soma",
  "carteiras.soma.exata": "Fecha em 100,00.",
  "carteiras.soma.abaixo": (d: string): string => `${d} abaixo de 100,00.`,
  "carteiras.soma.acima": (d: string): string => `${d} acima de 100,00.`,
  "carteiras.soma.foraDaSoma": (n: number): string =>
    n === 1
      ? "1 peso ainda não é número e fica fora da soma."
      : `${formatInteger(n)} pesos ainda não são números e ficam fora da soma.`,
  "carteiras.erro.nome": "Dê um nome à carteira.",
  "carteiras.erro.valor":
    "Use um valor em reais com até 2 casas, de 0,01 até 16 algarismos antes da vírgula, como 10.000,00.",
  "carteiras.erro.pesoFormato": "Use um número com até 2 casas, com vírgula ou ponto.",
  "carteiras.erro.peso": "O peso vai de 0,01 a 100,00.",
  "carteiras.erro.contagem": (n: number): string =>
    `A carteira precisa de 2 a 20 ações; a composição tem ${formatInteger(n)}.`,
  "carteiras.erro.soma": (s: string): string =>
    `A soma dos pesos precisa ser exatamente 100,00; está em ${s}.`,
  "carteiras.erro.repetida": "Esta ação aparece em outra linha da composição.",
  "carteiras.erro.desconhecida": "Este código não está no catálogo.",
  "carteiras.erro.naoAcao": "Este código é de um índice; a carteira só aceita ações.",
  "carteiras.erro.inativa":
    "Esta ação está inativa no catálogo e não entra na carteira.",
  "carteiras.erro.forma":
    "A composição não chegou no formato esperado. Confira os pesos e o valor e tente de novo.",
  "carteiras.erro.envio":
    "Não foi possível criar a carteira agora. O que você digitou continua aqui; tente de novo.",
  "carteiras.criar": "Criar carteira",
  "carteiras.criando": "Criando…",
  "carteiras.cancelar": "Cancelar",
  // A página da carteira (M2.2b, RF-02, RF-07, RF-08): o registro TEXTOS do `carteira.html`
  // aprovado, literal. As três frases do cálculo em curso (`carteira.composicao.emCurso`,
  // `.salvaEmCurso`, `.riscoEmCurso`) dependem do `in_progress` do risco e entram com a seção de
  // risco (T9).
  "carteira.voltar": "Todas as carteiras",
  "carteira.sobrancelha": "Carteira",
  "carteira.carregando": "Carregando a carteira.",
  "carteira.erro.titulo": "Não foi possível carregar a carteira.",
  "carteira.erro.texto": "Pode ser uma falha passageira do servidor.",
  "carteira.naoEncontrada.titulo": "Carteira não encontrada.",
  "carteira.naoEncontrada.texto":
    "Ela pode ter sido arquivada, ou este endereço não é de uma carteira da sua organização.",
  "carteira.naoEncontrada.voltar": "Ver as carteiras",
  "carteira.fatos.rotulo": "Sobre a carteira",
  "carteira.valor.rotulo": "Valor aplicado",
  "carteira.valor.nota.com":
    "A perda estimada aparece também em reais, calculada com este valor.",
  "carteira.valor.nota.sem": "Sem valor, a perda estimada aparece só em %.",
  "carteira.versao.rotulo": "Versão da composição",
  "carteira.mudouEm.rotulo": "Composição mudou em",
  "carteira.mudouEm": (data: string, hora: string): string => `${data} às ${hora}`,
  "carteira.criadaPor.rotulo": "Criada por",
  "carteira.nome.mudar": "Mudar o nome",
  "carteira.nome.campo": "Nome da carteira",
  "carteira.valor.mudar": "Mudar o valor",
  "carteira.valor.informar": "Informar um valor",
  "carteira.valor.tirar": "Tirar o valor",
  "carteira.valor.campo": "Valor aplicado, em reais",
  "carteira.salvar": "Salvar",
  "carteira.salvando": "Salvando…",
  "carteira.composicao.ordem": "Na ordem do código.",
  "carteira.composicao.total": "Total",
  "carteira.composicao.editar": "Editar composição",
  "carteira.composicao.salvar": "Salvar a composição",
  "carteira.composicao.nota":
    "Salvar uma composição diferente cria a versão seguinte. O risco mostrado é sempre o da versão corrente.",
  "carteira.composicao.salva": (n: number): string =>
    `Composição salva como a versão ${n}.`,
  "carteira.composicao.nadaMudou": (n: number): string =>
    `Nada mudou: a composição enviada é igual à da versão ${n}.`,
  "carteira.composicao.outraPessoa": (n: number): string =>
    `Outra pessoa também mudou esta carteira enquanto você editava. A composição abaixo, da versão ${n}, é a que ficou salva.`,
  "carteira.erro.forma":
    "A composição não foi aceita. Confira os pesos e tente de novo.",
  "carteira.erro.rede": "Não foi possível falar com o servidor. Tente de novo.",
  "carteira.erro.muitos": (n: number): string =>
    `Muitos pedidos seguidos. Tente de novo em ${n} s.`,
  "carteira.erro.muitosSemTempo":
    "Muitos pedidos seguidos. Aguarde um pouco e tente de novo.",
  "carteira.erro.csrf": "A página ficou desatualizada. Recarregue e tente de novo.",
  "carteira.erro.outro": "Não foi possível concluir agora. Tente de novo.",
  "carteira.erro.mantido": "Nada foi alterado.",
  "carteira.arquivar": "Arquivar",
  "carteira.arquivar.titulo": (nome: string): string =>
    `Arquivar a carteira “${nome}”?`,
  "carteira.arquivar.texto":
    "A carteira sai da lista da organização e deixa de abrir, para todas as pessoas dela. A composição e o risco já calculado ficam guardados.",
  "carteira.arquivar.semVolta": "A tela não tem como desarquivar.",
  "carteira.arquivar.confirmar": "Arquivar a carteira",
  "carteira.arquivar.enviando": "Arquivando…",
} as const;

export type TextoKey = keyof typeof TEXTOS;
