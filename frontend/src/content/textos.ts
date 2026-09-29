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

  // O rodapé (RF-04).
  "rodape.ressalva": RESSALVA,
  "rodape.fonte": "Fontes: catálogo de ativos da B3 e preços do Yahoo Finance.",
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
    `Desde o primeiro pregão do ano, com os proventos: R$ 100 viraram ${x}.`,
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
  // A lista dos adequate = true, sem eleger nenhum (RF-14).
  "risco.naoRejeitados": (k: number, julgados: number, total: number): string => {
    const faltam = total - julgados;
    const semJulgar =
      faltam > 0
        ? ` ${faltam} ${faltam === 1 ? "modelo não pôde ser julgado" : "modelos não puderam ser julgados"}, porque o cálculo falhou — isso não conta como reprovação.`
        : "";
    if (julgados === 0)
      return "Não foi possível julgar nenhum modelo neste nível: o cálculo falhou em todos, e isso não conta como reprovação.";
    if (k === 0)
      return `Nenhum dos métodos julgados descreveu bem este ativo neste nível${faltam > 0 ? ` (${julgados} de ${total} julgados)` : ""}. Não é erro do cálculo: é informação sobre o ativo — nenhum dos métodos testados acompanhou o comportamento dele no período de teste.${semJulgar}`;
    const quem =
      k === 1
        ? `1 dos ${julgados} modelos julgados passou`
        : `${k} dos ${julgados} modelos julgados passaram`;
    return `${quem} nos testes de Kupiec e de Christoffersen neste nível: os dias em que a perda passou do limite ficaram perto do esperado e não vieram em sequência. O veredito fala do comportamento de cada modelo no período de teste — não garante o número de hoje —, e passar não põe um modelo acima dos outros que também passaram: a lista segue a ordem fixa da tabela.${semJulgar}`;
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
  "risco.veredito":
    "O veredito junta dois testes feitos no período de teste: adequado quando o modelo passa no Kupiec e no Christoffersen; não adequado quando falha em pelo menos um; não julgado quando o cálculo falhou. Fala de como o modelo se comportou no passado, não de quanto o número de hoje está certo.",
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
  "fundamentos.ebit_ttm": (negativo: boolean) =>
    negativo
      ? "Negativo: a operação deu prejuízo nos últimos 12 meses, antes dos juros e dos impostos sobre o lucro."
      : "O que a operação rendeu nos últimos 12 meses, antes dos juros e dos impostos sobre o lucro.",
  "fundamentos.net_income_ttm": (negativo: boolean) =>
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
  "fundamentos.net_debt": (negativo: boolean) =>
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
  "fundamentos.equity_parent": (negativo: boolean) =>
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
  // abaixoDeTodas(n − 1) — no lugar de posicao quando k = 0 (ajuste do portão, 2026-09-29)
  "fundamentos.pares.abaixoDeTodas": (outras: string) =>
    `Abaixo de todas as outras ${outras} companhias do grupo com este indicador calculado.`,
  "fundamentos.pares.mediana": (m: string) => `Mediana do grupo: ${m}.`,
  "fundamentos.pares.semComparacao": "Sem comparação para este indicador.",
} as const;

export type TextoKey = keyof typeof TEXTOS;
