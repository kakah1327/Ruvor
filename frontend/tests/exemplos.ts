/**
 * Os registros de exemplos das funções de texto: uma lista de argumentos por chave-função,
 * que cobre cada ramo. Não é teste — é importado pelos testes que chamam as funções.
 *
 * - `EXEMPLOS`: as chaves-função de `TEXTOS` e as traduções de `motivos.ts` (V-09 do M1.6b).
 * - `EXEMPLOS_AVANCADOS`: as chaves-função de `TEXTOS_AVANCADOS`, cobrindo os ramos da
 *   avançada, que podem não ser os da iniciante (V-07 do M2.3).
 */

// Um conjunto de argumentos por ramo de cada função de texto.
export const EXEMPLOS: Readonly<Record<string, ReadonlyArray<readonly unknown[]>>> = {
  "busca.contagem": [
    [1, "itub"],
    [1234, "itub"],
  ],
  "busca.mostrando": [[20, 1234]],
  "busca.semResultado": [["xpto"]],
  "busca.suspensaRodape": [[8, 1234]],
  // O "e mais N" da sugestão (M1.7): os ramos da tabela de textos do busca-sugestao.html.
  "busca.sugestaoMais": [[1], [3], [1234]],
  "rodape.ultimoPregao": [["26/09/2026"]],
  "rodape.calculadoEm": [["26/09/2026", "18:40"]],
  "ativo.listagem": [["N1"]],
  "ativo.ultimoFechamento": [["26/09/2026"]],
  "ativo.eventos.periodo": [["26/09/2026"]],
  "ativo.eventos.valor": [["R$ 0,50"]],
  "ativo.eventos.proporcao": [["2", "1"]],
  "ativo.eventos.verTodos": [["42"]],
  "ativo.naoEncontrado": [["XPTO3"]],
  "grafico.dicaPreco": [["26/09/2026", "R$ 30,00"]],
  "grafico.resumoPreco": [
    [
      "26/09/2016",
      "26/09/2026",
      "R$ 9,00",
      "20/01/2016",
      "R$ 40,00",
      "01/08/2025",
      "R$ 38,00",
    ],
  ],
  "grafico.faixa": [["−0,5%", "0,0%"]],
  "grafico.dicaBarra": [
    ["de −0,5% a 0,0%", 1],
    ["de −0,5% a 0,0%", 5],
  ],
  "grafico.resumoHistograma": [
    ["de 0,0% a 0,5%", "300", 1, 1],
    ["de 0,0% a 0,5%", "300", 3, 2],
  ],
  "comportamento.ate": [["26/09/2026"]],
  "comportamento.nota.ibov": [["1.230"]],
  "comportamento.nota.distribuicao": [["1.230"]],
  "comportamento.nulo.janela": [[60]],
  "comportamento.nulo.pregoes": [[252]],
  "comportamento.return_1m": [["R$ 102,00"]],
  "comportamento.return_3m": [["R$ 102,00"]],
  "comportamento.return_6m": [["R$ 102,00"]],
  "comportamento.return_12m": [["R$ 102,00"]],
  "comportamento.return_36m": [["R$ 102,00"]],
  "comportamento.return_60m": [["R$ 102,00"]],
  "comportamento.return_120m": [["R$ 102,00"]],
  "comportamento.return_ytd": [["R$ 102,00"]],
  "comportamento.volatility_12m": [["25,0%"]],
  "comportamento.volatility_60m": [["25,0%"]],
  "comportamento.max_drawdown": [
    ["31,2%", "05/01/2022", "12/10/2022", "22/09/2016", "03/03/2024"],
    ["31,2%", "05/01/2022", "12/10/2022", "22/09/2016", null],
  ],
  "comportamento.max_drawdown_recovery_sessions": [["1,4"]],
  // Os momentos de estresse (M3.3): o `EXEMPLOS` do `ativo-estresse.html`, cobrindo os ramos.
  "comportamento.estresse.recorte": [["17/05/2017", "30/06/2017"]],
  "comportamento.estresse.janela": [["14/11/2025", "30/12/2025"]],
  "comportamento.estresse.period_return": [
    ["R$ 79,24", "17/05/2017", "30/06/2017"],
    ["R$ 141,00", "07/06/2021", "14/07/2022"],
  ],
  "comportamento.estresse.benchmark_period_return": [["R$ 93,13"]],
  "comportamento.estresse.drawdown": [
    // inteira = false (PETR4, JBS), e inteira = true (IBOV, juros).
    ["25,4%", "17/05/2017", "21/06/2017", false],
    ["26,5%", "07/06/2021", "14/07/2022", true],
  ],
  "comportamento.estresse.benchmark_drawdown": [
    ["10,0%", false],
    ["26,5%", true],
  ],
  "comportamento.estresse.recovery_sessions": [["20/09/2017"]],
  "comportamento.estresse.benchmark_recovery_sessions": [["33 pregões"]],
  "comportamento.estresse.pregoes": [["33"]],
  "comportamento.beta_60m": [
    ["0,85%", false],
    ["0,15%", true],
  ],
  "comportamento.correlation_60m": [["0,62"]],
  "comportamento.skewness": [
    ["−0,35", -1],
    ["0,35", 1],
    ["0,00", 0],
  ],
  "comportamento.excess_kurtosis": [
    ["5,10", 1],
    ["−0,20", -1],
  ],
  "comportamento.dividend_yield_12m": [["26/09/2026", "R$ 6,10"]],
  "comportamento.unidade.volume": [["25,3"]],
  "risco.faixa": [["2,1%", "2,7%"]],
  "risco.discordancia": [
    [null, null, 0, 9, 20, null],
    [null, null, 1, 9, 100, "3,9%"],
    ["2,1%", "2,7%", 9, 9, 20, null],
    ["2,1%", "2,7%", 8, 9, 20, null],
    ["2,1%", "2,7%", 7, 9, 100, null],
  ],
  "risco.naoRejeitados": [
    [0, 0, 9],
    [0, 9, 9],
    [0, 8, 9],
    [0, 7, 9],
    [1, 9, 9],
    [3, 8, 9],
    [3, 7, 9],
  ],
  "risco.tabela.abrir": [["Histórico"]],
  "risco.violacoes": [
    ["25", "25,1", 20, true],
    ["40", "25,1", 20, false],
  ],
  "risco.kupiec": [
    ["0,919", true],
    ["0,021", false],
  ],
  "risco.christoffersen": [
    ["0,919", true],
    ["0,021", false],
  ],
  "risco.dq": [
    ["0,082", true],
    ["< 0,001", false],
  ],
  "risco.erroModelo": [["texto do erro do motor"]],
  "risco.trilha.pregoes": [["1.980"]],
  "risco.trilha.coleta": [["Yahoo Finance", "26/09/2026 às 18:40"]],
  "risco.trilha.instante": [["26/09/2026", "18:40"]],
  "risco.trilha.status.partial": [[2]],
  "risco.estado.recalculando": [[12, 18]],
  "risco.estado.E4": [[3, 18]],
  "risco.pedido.erro": [["Erro interno. Tente de novo mais tarde."]],
  // laboratorio.*: o registro EXEMPLOS do `laboratorio.html` aprovado (M2.4, T9), cobrindo os
  // ramos — o último trecho curto e cheio; acima, abaixo e dentro do esperado; um e dois modelos.
  "laboratorio.decada": [
    ["22/09/2016", "22/09/2026", 9, 222],
    ["22/09/2016", "22/09/2026", 9, 252],
  ],
  "laboratorio.diferenca": [["0.4.0", "22/09/2026"]],
  "laboratorio.violacoesAno": [
    ["12,6", 20],
    ["2,5", 100],
  ],
  "laboratorio.vereditoAno": [[81]],
  "laboratorio.anoNaoJulgado": [[110]],
  "laboratorio.violacoesDecada": [
    ["108", "111,9", 20, true],
    ["50", "22,4", 100, false],
    ["10", "22,4", 100, false],
    ["1", "2,5", 100, false],
  ],
  "laboratorio.estado.falhou": [["05/10/2026"]],
  "laboratorio.estado.semDecada": [["28/10/2016", "28/10/2026"]],
  "laboratorio.estado.serieCurta": [["480", "503"]],
  "laboratorio.nota.falha": [["05/10/2026"]],
  "laboratorio.nota.motor": [["0.4.0", "0.5.0"]],
  "laboratorio.nota.parcial": [[1], [2]],
  "laboratorio.grade.ano": [[1]],
  "laboratorio.grade.periodo": [["set/2017", "set/2018"]],
  "laboratorio.grade.esperadas": [["12,6"]],
  "laboratorio.grade.kDeN": [[4, 9]],
  "laboratorio.trilha.retratos": [["72", "0"]],
  // retorno.*: o registro EXEMPLOS do `retorno.html` aprovado (M5.1, T9), cobrindo os ramos —
  // nenhum bate, um, os dois, um e dois sem veredito; menos e mais; o PT nulo nos dois lados.
  "retorno.veredito": [
    ["ITUB4", "2.246", "02/10/2026", [], ["AR(1)", "Média histórica"], 0],
    ["PETR4", "2.246", "02/10/2026", [["AR(1)", "0,40%"]], ["Média histórica"], 0],
    [
      "PETR4",
      "2.246",
      "02/10/2026",
      [
        ["AR(1)", "0,40%"],
        ["Média histórica", "0,14%"],
      ],
      [],
      0,
    ],
    ["ITUB4", "2.246", "02/10/2026", [], ["Média histórica"], 1],
    ["ITUB4", "2.246", "02/10/2026", [["Média histórica", "0,01%"]], [], 1],
    ["ITUB4", "2.246", "02/10/2026", [], [], 2],
  ],
  "retorno.r2_os": [
    ["0,04%", true],
    ["0,95%", false],
    ["0,00%", false],
  ],
  "retorno.acerto": [["50,6%", "51,1%"]],
  "retorno.dm": [
    ["0,458", false],
    ["0,031", true],
  ],
  "retorno.cw": [["0,049"]],
  "retorno.pt": [
    ["0,445", null],
    [null, true],
    [null, false],
  ],
  "retorno.previsao": [
    ["−0,05%", "05/10/2026", false],
    ["+0,09%", "05/10/2026", true],
  ],
  "retorno.estado.serieCurta": [["312", "503"]],
  "retorno.previsao.passada": [["28/09/2026"]],
  "retorno.previsao.rotulo": [["05/10/2026"]],
  "retorno.acerto.valor": [["50,6%", "51,1%"]],
  "retorno.erroModelo": [["matriz singular no trecho 4"]],
  // fundamentos.*: os do registro EXEMPLOS do ativo-fundamentos.html (M1.6c), um por ramo.
  "fundamentos.proveniencia": [["30/06/2026", "ITR", "28/09/2026 às 08:02"]],
  "fundamentos.vezes": [["4,65"]],
  "fundamentos.ebit_ttm": [[false], [true]],
  "fundamentos.net_income_ttm": [[false], [true]],
  "fundamentos.net_margin": [
    ["R$ 24,32", false],
    ["R$ 4,21", true],
  ],
  "fundamentos.ebit_margin": [
    ["R$ 33,86", false],
    ["R$ 2,10", true],
  ],
  "fundamentos.roe": [
    ["R$ 27,73", false],
    ["R$ 6,12", true],
  ],
  "fundamentos.net_debt": [[false], [true]],
  "fundamentos.net_debt_to_equity": [
    ["R$ 65,03", false],
    [null, true],
  ],
  "fundamentos.close": [["25/09/2026"]],
  "fundamentos.closeOutraData": [["25/09/2026", "28/09/2026"]],
  "fundamentos.eps": [
    ["12.888.732.761", false],
    ["4.980.000.000", true],
  ],
  "fundamentos.bvps": [["12.888.732.761"]],
  "fundamentos.pe": [
    ["25/09/2026", "R$ 48,07", "4,6", false],
    ["25/09/2026", "R$ 12,15", "−28,7", true],
  ],
  "fundamentos.pb": [["25/09/2026", "R$ 48,07", "1,29"]],
  "fundamentos.equity_parent": [[false], [true]],
  "fundamentos.pares.segmento": [["Exploração, Refino e Distribuição"]],
  "fundamentos.pares.subsetor": [["Petróleo, Gás e Biocombustíveis"]],
  "fundamentos.pares.posicao": [
    ["6", "6"],
    ["2", "3"],
  ],
  "fundamentos.pares.abaixoDeTodas": [["7"]],
  "fundamentos.pares.mediana": [["11,3%"], ["7,20 vezes"]],
  // comunicados.*: os do registro EXEMPLOS do ativo-fundamentos.html (M1.6c).
  "comunicados.companhia": [["PETROLEO BRASILEIRO S.A. PETROBRAS", "9512"]],
  "comunicados.companhiaSemNome": [["9512"]],
  "comunicados.referencia": [["11/09/2026"]],
  "comunicados.mostrando": [["10", "2.765"]],
  "comunicados.filtroVazio": [
    ["fato relevante"],
    ["comunicado ao mercado"],
    ["aviso aos acionistas"],
  ],
  "motivos.serieCurta": [["312", "503"]],
  "motivos.expirado": [["30"]],
  "motivos.desconhecido": [["qualquer outro texto"]],
  // acesso.*: o registro EXEMPLOS do entrada.html (M2.1b) — segundos, minutos e sem o número.
  "acesso.erro.tentativas": [[42], [900], [null]],
  // senha.*: o registro EXEMPLOS do senha.html (M2.1b) — o e-mail de quem entrou.
  "senha.obrigatoria.conta": [["ana.souza@exemplo.com"]],
  // conta.*: o registro EXEMPLOS do conta.html (M2.1b) — o nome de quem entrou.
  "conta.menu.rotulo": [["Ana Beatriz Souza"]],
  // usuarios.*: o registro EXEMPLOS do usuarios.html (M2.1b) — a contagem nos dois ramos.
  "usuarios.sub": [["Gestora Exemplo"]],
  "usuarios.erro.muitos": [[12]],
  "usuarios.lista.contagem": [[1], [63]],
  "usuarios.ultimoAcesso": [["03/10/2026", "10:41"]],
  "usuarios.mostrando": [[50, 63]],
  "usuarios.acoes.rotulo": [["Ana Lima"]],
  "usuarios.confirmar.admin.titulo": [["Elisa Prado"]],
  "usuarios.confirmar.member.titulo": [["Bruno Costa"]],
  "usuarios.confirmar.desativar.titulo": [["Elisa Prado"]],
  "usuarios.confirmar.reativar.titulo": [["Diego Alves"]],
  "usuarios.confirmar.senha.titulo": [["Ana Lima"]],
  "usuarios.senha.criado.texto": [["Gabriela Rocha", "gabriela.rocha@exemplo.com"]],
  "usuarios.senha.nova.texto": [["Ana Lima", "ana.lima@exemplo.com"]],
  "usuarios.membro.texto": [["Gestora Exemplo"]],
  // carteiras.*: o registro EXEMPLOS do lista.html (M2.2b) — a contagem nos dois ramos.
  "carteiras.sub.organizacao": [["Gestora Exemplo"]],
  "carteiras.lista.contagem": [[1], [57]],
  "carteiras.acoes": [[1], [4]],
  "carteiras.mostrando": [[50, 57]],
  "carteiras.arquivada": [["Bancos e energia"]],
  "carteiras.seletor.nenhumaServe": [["IBOV"]],
  "carteiras.peso.rotulo": [["PETR4"]],
  "carteiras.remover": [["PETR4"]],
  "carteiras.soma.abaixo": [["0,01"]],
  "carteiras.soma.acima": [["0,50"]],
  "carteiras.soma.foraDaSoma": [[1], [2]],
  "carteiras.erro.contagem": [[1], [21]],
  "carteiras.erro.soma": [["99,99"]],
  // carteira.*: o registro EXEMPLOS do carteira.html (M2.2b), sem as três frases do cálculo em
  // curso, que entram com a seção de risco (T9).
  "carteira.mudouEm": [["02/10/2026", "16:41"]],
  "carteira.composicao.salva": [[4]],
  "carteira.composicao.nadaMudou": [[3]],
  "carteira.composicao.outraPessoa": [[5]],
  "carteira.erro.muitos": [[12]],
  "carteira.arquivar.titulo": [["Bancos e energia"]],
};

// Um conjunto de argumentos por ramo de cada função de `TEXTOS_AVANCADOS`. Cresce seção a seção.
export const EXEMPLOS_AVANCADOS: Readonly<
  Record<string, ReadonlyArray<readonly unknown[]>>
> = {
  // O cabeçalho (T4): a linha do `casco-e-preco.html`. `ativo.precoAjustado` é texto.
  "ativo.ultimoFechamento": [["26/09/2026"]],
  // O comportamento (T7): o `EXEMPLOS_AVANCADOS` do `comportamento.html`, cobrindo os ramos da
  // avançada; o primeiro de cada um é o do ITUB4 em 01/10/2026. As chaves de texto não entram.
  "comportamento.return_1m": [["R$ 110,75"]],
  "comportamento.return_3m": [["R$ 104,16"]],
  "comportamento.return_6m": [["R$ 101,90"]],
  "comportamento.return_12m": [["R$ 128,19"]],
  "comportamento.return_36m": [["R$ 231,07"]],
  "comportamento.return_60m": [["R$ 231,82"]],
  "comportamento.return_120m": [["R$ 413,95"]],
  "comportamento.return_ytd": [["R$ 114,98"]],
  "comportamento.volatility_12m": [["24,5%"]],
  "comportamento.volatility_60m": [["24,9%"]],
  "comportamento.max_drawdown": [
    // A volta preenchida (ITUB4), e a volta nula.
    ["44,3%", "02/01/2020", "23/03/2020", "22/09/2016", "13/12/2023"],
    ["61,8%", "18/05/2021", "04/11/2022", "22/09/2016", null],
  ],
  "comportamento.max_drawdown_recovery_sessions": [["3,7"]],
  // Os momentos de estresse (M3.3): os mesmos ramos da iniciante.
  "comportamento.estresse.period_return": [
    ["R$ 79,24", "17/05/2017", "30/06/2017"],
    ["R$ 141,00", "07/06/2021", "14/07/2022"],
  ],
  "comportamento.estresse.benchmark_period_return": [["R$ 93,13"]],
  "comportamento.estresse.drawdown": [
    ["25,4%", "17/05/2017", "21/06/2017", false],
    ["26,5%", "07/06/2021", "14/07/2022", true],
  ],
  "comportamento.estresse.benchmark_drawdown": [
    ["10,0%", false],
    ["26,5%", true],
  ],
  "comportamento.estresse.recovery_sessions": [["20/09/2017"]],
  "comportamento.estresse.benchmark_recovery_sessions": [["33 pregões"]],
  "comportamento.beta_60m": [
    // oposta = false (ITUB4), e oposta = true.
    ["1,01%", false],
    ["0,18%", true],
  ],
  "comportamento.correlation_60m": [["0,70"], ["−0,12"]],
  "comportamento.skewness": [
    // sinal < 0 (ITUB4), sinal > 0 e sinal = 0.
    ["−1,44", -1],
    ["0,37", 1],
    ["0,00", 0],
  ],
  "comportamento.excess_kurtosis": [
    // sinal > 0 (ITUB4), sinal < 0 e sinal = 0.
    ["20,93", 1],
    ["−0,41", -1],
    ["0,00", 0],
  ],
  "comportamento.dividend_yield_12m": [["01/10/2026", "R$ 7,06"]],
  // O risco (T10): o `EXEMPLOS_AVANCADOS` do `risco.html`, cobrindo os ramos da avançada; os
  // marcados ITUB4 são os da execução 85, de 01/10/2026, e os outros, fictícios. As chaves de
  // texto não entram. Em `risco.naoRejeitados`, os ramos k ≥ 1 e k = 0 — os da D-64, que o
  // `d64.test.ts` confere — e o julgados = 0, isento.
  "risco.discordancia": [
    // n = total (ITUB4, 95%); n ≥ 2 com 2 sem VaR; n ≥ 2 com 1 sem VaR; n = 1; n = 0.
    ["2,2%", "3,1%", 9, 9, 20, "2,2%"],
    ["2,6%", "3,1%", 7, 9, 20, "2,6%"],
    ["3,7%", "5,6%", 8, 9, 100, "3,7%"],
    ["4,1%", "4,1%", 1, 9, 100, "4,1%"],
    [null, null, 0, 9, 20, null],
  ],
  "risco.naoRejeitados": [
    // k ≥ 1 (ITUB4, 95% e 99%); k = 1 com 1 sem veredito; k = 0; k = 0 com 2 sem veredito;
    // k = 0 com um só julgado; julgados = 0 (isento da D-64).
    [6, 9, 9],
    [2, 9, 9],
    [1, 8, 9],
    [0, 9, 9],
    [0, 7, 9],
    [0, 1, 9],
    [0, 0, 9],
  ],
  "risco.violacoes": [
    // kupiecOk (CAViaR 95%, ITUB4); acima, rejeitado (CAViaR 99%, ITUB4); abaixo, rejeitado
    // (EGARCH 99%, ITUB4); singular.
    ["111", "112,3", 20, true],
    ["50", "22,5", 100, false],
    ["7", "22,5", 100, false],
    ["1", "4,0", 100, false],
  ],
  "risco.kupiec": [
    // ok (CAViaR 95%, ITUB4); rejeitado (CAViaR 99%, ITUB4).
    ["0,903", true],
    ["< 0,001", false],
  ],
  "risco.christoffersen": [
    // ok (CAViaR 95%, ITUB4); rejeitado (GARCH(1,1) 99%, ITUB4).
    ["0,225", true],
    ["0,042", false],
  ],
  "risco.dq": [
    // ok (CAViaR 95%, ITUB4); rejeitado (CAViaR 99%, ITUB4).
    ["0,082", true],
    ["< 0,001", false],
  ],
  // Os fundamentos (T13): o `EXEMPLOS_AVANCADOS` do `fundamentos.html`, cobrindo os ramos da
  // avançada; o primeiro de cada um é o do PETR4 no cálculo de 28/09/2026 (o de
  // `abaixoDeTodas`, o da VALE3), e os do ramo negativo, inventados — o PETR4 não tem número
  // negativo. As chaves de texto não entram.
  "fundamentos.ebit_ttm": [[false], [true]],
  "fundamentos.net_income_ttm": [[false], [true]],
  "fundamentos.net_margin": [
    ["R$ 24,32", false],
    ["R$ 4,21", true],
  ],
  "fundamentos.ebit_margin": [
    ["R$ 33,86", false],
    ["R$ 2,10", true],
  ],
  "fundamentos.roe": [
    ["R$ 27,73", false],
    ["R$ 6,12", true],
  ],
  "fundamentos.net_debt": [[false], [true]],
  "fundamentos.net_debt_to_equity": [
    ["R$ 65,03", false],
    ["R$ 12,40", true],
  ],
  "fundamentos.close": [["25/09/2026"]],
  "fundamentos.closeOutraData": [["25/09/2026", "01/10/2026"]],
  "fundamentos.eps": [
    ["12.888.732.761", false],
    ["4.980.000.000", true],
  ],
  "fundamentos.bvps": [["12.888.732.761"]],
  "fundamentos.pe": [
    ["25/09/2026", "R$ 48,07", "4,6", false],
    ["25/09/2026", "R$ 12,15", "−28,7", true],
  ],
  "fundamentos.pb": [["25/09/2026", "R$ 48,07", "1,29"]],
  "fundamentos.equity_parent": [[false], [true]],
  "fundamentos.pares.posicao": [
    // k ≥ 1: o ROE e a dívida líquida sobre o patrimônio (PETR4).
    ["6", "6"],
    ["3", "6"],
  ],
  "fundamentos.pares.abaixoDeTodas": [["3"]],
  "fundamentos.pares.mediana": [["11,3%"], ["7,20 vezes"]],
  // laboratorio.*: o registro EXEMPLOS (as avançadas) do `laboratorio.html` aprovado (M2.4, T9), cobrindo os
  // ramos — o último trecho curto e cheio; acima, abaixo e dentro do esperado; um e dois modelos.
  "laboratorio.decada": [
    ["22/09/2016", "22/09/2026", 9, 222],
    ["22/09/2016", "22/09/2026", 9, 252],
  ],
  "laboratorio.diferenca": [["0.4.0", "22/09/2026"]],
  "laboratorio.violacoesAno": [
    ["12,6", 20],
    ["2,5", 100],
  ],
  "laboratorio.vereditoAno": [[81]],
  "laboratorio.anoNaoJulgado": [[110]],
  "laboratorio.violacoesDecada": [
    ["108", "111,9", 20, true],
    ["50", "22,4", 100, false],
    ["10", "22,4", 100, false],
    ["1", "2,5", 100, false],
  ],
  // retorno.*: o registro EXEMPLOS do `retorno.html` aprovado (M5.1, T9), cobrindo os ramos —
  // nenhum bate, um, os dois, um e dois sem veredito; menos e mais; o PT nulo nos dois lados.
  "retorno.veredito": [
    ["ITUB4", "2.246", "02/10/2026", [], ["AR(1)", "Média histórica"], 0],
    ["PETR4", "2.246", "02/10/2026", [["AR(1)", "0,40%"]], ["Média histórica"], 0],
    [
      "PETR4",
      "2.246",
      "02/10/2026",
      [
        ["AR(1)", "0,40%"],
        ["Média histórica", "0,14%"],
      ],
      [],
      0,
    ],
    ["ITUB4", "2.246", "02/10/2026", [], ["Média histórica"], 1],
    ["ITUB4", "2.246", "02/10/2026", [["Média histórica", "0,01%"]], [], 1],
    ["ITUB4", "2.246", "02/10/2026", [], [], 2],
  ],
  "retorno.r2_os": [
    ["0,04%", true],
    ["0,95%", false],
    ["0,00%", false],
  ],
  "retorno.acerto": [["50,6%", "51,1%"]],
  "retorno.dm": [
    ["0,458", false],
    ["0,031", true],
  ],
  "retorno.cw": [["0,049"]],
  "retorno.pt": [
    ["0,445", null],
    [null, true],
    [null, false],
  ],
  "retorno.previsao": [
    ["−0,05%", "05/10/2026", false],
    ["+0,09%", "05/10/2026", true],
  ],
};
