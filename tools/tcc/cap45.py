# Capítulos 4 e 5. Cada item: ("H1"|"H2", texto) | ("P", texto) | ("FIG", arquivo, legenda, fonte)
# | ("TAB", nome, legenda, fonte)

FONTE_EXP = "Fonte: Os autores, a partir dos resultados gravados pela plataforma."
FONTE_TELA = "Fonte: Os autores, captura da plataforma."

CAP4 = [
    ("H1", "4 RESULTADOS"),
    ("P", "Este capítulo apresenta os resultados da implementação do Ruvor, organizados por etapa, conforme a Matriz "
          "de Validação (Apêndice A). As seis etapas foram concluídas. Os números das Seções 4.4 e 4.6 vêm do "
          "experimento comparativo da Etapa 6, executado pela própria plataforma e gravado no banco de dados com a "
          "versão do motor de cálculo (0.5.0), a semente aleatória (42) e as versões das bibliotecas, o que permite "
          "refazê-lo e obter os mesmos valores. O experimento foi executado em 4 de outubro de 2026, ao fim do "
          "cálculo diário de risco: no mesmo dia, as redes neurais foram treinadas do zero com a versão 0.5.0 do "
          "motor, e o experimento reaproveitou os estados treinados, o que, como descrito na Seção 4.3, produz a "
          "mesma série de um treino completo."),
    ("H2", "4.1 Etapa 1 – Métodos Tradicionais de VaR"),
    ("P", "Os três métodos tradicionais de cálculo do VaR (paramétrico, simulação histórica e simulação de Monte "
          "Carlo) foram implementados em Python, seguindo uma interface comum que desacopla cada modelo do restante "
          "da plataforma, e validados por um conjunto de testes automatizados parametrizados sobre séries de "
          "retornos sintéticas com distribuição conhecida. Os três modelos convergem para estimativas consistentes "
          "entre si em condições de retornos gaussianos, conforme esperado pela teoria (Jorion, 2001)."),
    ("P", "Na versão final, os três métodos são reestimados a cada 252 dias úteis em janela expansiva — a estimativa "
          "de cada trecho usa todos os retornos observados até o início dele —, em vez de aplicar a todo o período "
          "de teste um único quantil, estimado no primeiro ano. Como o paramétrico e o Monte Carlo partem da mesma "
          "distribuição normal, ajustada aos mesmos dados, e o Monte Carlo usa semente fixa e 100.000 cenários por "
          "estimativa, os dois produzem, na prática, o mesmo VaR, o que se observa em todos os resultados a seguir."),
    ("H2", "4.2 Etapa 2 – Modelos GARCH e EGARCH"),
    ("P", "O modelo GARCH(1,1) (Bollerslev, 1986) e sua extensão assimétrica EGARCH (Nelson, 1991) foram "
          "implementados com a biblioteca arch (Python), com estimação dos parâmetros por máxima verossimilhança "
          "sobre uma janela de treino de 252 dias úteis, seguida de reestimação periódica com janela expansiva a "
          "cada 252 dias ao longo do período de teste — estratégia adotada para manter a variância condicional "
          "alinhada ao regime de mercado mais recente."),
    ("P", "Durante a validação, identificou-se uma instabilidade numérica característica do EGARCH: ao propagar "
          "parâmetros fixos por longos períodos de teste sem reestimação, o resíduo padronizado tende a crescer, "
          "amplificando a reação dos termos assimétricos (α, γ) e realimentando um colapso da variância condicional. "
          "O GARCH(1,1) tradicional não apresenta esse comportamento, pois sua recursão possui um piso estrutural "
          "dado pela constante ω. O problema foi mitigado por meio da reestimação periódica somada a um piso mínimo "
          "de segurança na volatilidade, derivado do desvio-padrão histórico da janela de treino."),
    ("P", "Os parâmetros estimados pela biblioteca arch foram comparados com os obtidos pelo pacote rugarch (linguagem "
          "R), ajustando a mesma especificação (média zero, inovações normais) sobre os mesmos dados de treino "
          "(PETR4, 252 dias). A comparação das log-verossimilhanças, ajustadas pela escala das séries, mostrou "
          "concordância entre as duas implementações: 473,62 (Python) contra 471,81 (R) para o GARCH(1,1), e 481,60 "
          "(Python) contra 475,17 (R) para o EGARCH — divergências abaixo de 1,5%, compatíveis com pequenas "
          "diferenças de otimizador numa superfície de verossimilhança com crista quase plana entre os parâmetros α "
          "e β, fenômeno conhecido na literatura de estimação de modelos GARCH."),
    ("P", "Na revisão do motor de cálculo, identificou-se um defeito na versão usada nos resultados preliminares do "
          "TCC I: o VaR do GARCH e do EGARCH para o dia t era calculado com uma variância condicional que já "
          "incorporava o retorno do próprio dia t, isto é, o modelo usava o dado que deveria prever. Na versão final, "
          "a volatilidade do dia t é obtida exclusivamente dos retornos até o dia t − 1. A correção é verificada por "
          "um teste automatizado de perturbação: alterar o retorno de um dia, ou de qualquer dia seguinte, não pode "
          "mudar o VaR estimado para aquele dia; o teste cobre os seis modelos não neurais. Por esse defeito e pela "
          "troca do quantil fixo pela janela expansiva (Seção 4.1), os resultados preliminares do TCC I foram "
          "descartados e refeitos (Seções 4.4 e 4.6)."),
    ("H2", "4.3 Etapa 3 – Modelos de Machine Learning"),
    ("P", "Os quatro modelos de Machine Learning especificados na Matriz de Validação foram implementados: LSTM "
          "(Hochreiter; Schmidhuber, 1997), GRU (Cho et al., 2014), CAViaR na especificação Symmetric Absolute Value "
          "(Engle; Manganelli, 2004) e GARCHNet, o híbrido GARCH e LSTM proposto por Buczyński e Chlebus (2024). "
          "Diferentemente do GARCH, que prevê a variância condicional e assume normalidade dos resíduos para obter "
          "o quantil, a LSTM, a GRU e o componente neural do GARCHNet preveem o quantil de VaR diretamente por meio "
          "da pinball loss (regressão quantílica), sem qualquer suposição distribucional."),
    ("P", "O CAViaR foi ajustado por otimização numérica (scipy.optimize, minimizando a pinball loss com múltiplos "
          "reinícios aleatórios), já que sua estrutura recursiva — o VaR do dia anterior aparece como regressor do "
          "VaR do dia atual — não é suportada por implementações de regressão quantílica estática, como o "
          "statsmodels.QuantReg originalmente cogitado na Matriz de Validação (Apêndice A)."),
    ("P", "O GARCHNet reaproveita a volatilidade condicional do GARCH(1,1) (Etapa 2) como uma terceira variável de "
          "entrada da LSTM, ao lado do retorno e do retorno absoluto, numa janela deslizante de 20 dias úteis. A "
          "otimização de hiperparâmetros por grid search foi restrita a duas dimensões — 16 ou 32 unidades e uma ou "
          "duas camadas recorrentes —, com taxa de aprendizado de 0,001 e lote de 32 exemplos; essa redução de "
          "escopo foi necessária porque o treino é específico para cada nível de confiança (95% e 99%) e combinado "
          "à validação walk-forward com reestimação periódica a cada 252 dias, o que torna um grid de quatro "
          "dimensões computacionalmente impraticável."),
    ("P", "Para garantir a reprodutibilidade, a semente dos geradores aleatórios é fixada em cada treino e em cada "
          "retreino das redes e gravada junto com o resultado — o que resolve a ressalva registrada no TCC I, em que "
          "os valores variavam entre execuções. Para reduzir o custo do cálculo diário, os quatro modelos mais caros "
          "(LSTM, GRU, GARCHNet e CAViaR) guardam o estado treinado em cada ponto de retreino e o reaproveitam nos "
          "cálculos seguintes; a série reconstituída a partir desses estados é idêntica à de um treino completo. Os "
          "resultados dos quatro modelos, comparados aos demais, estão nas Seções 4.4 e 4.6."),
    ("H2", "4.4 Etapa 4 – Backtesting Estatístico"),
    ("P", "Os quatro instrumentos de validação especificados na Matriz de Validação foram implementados: o teste de "
          "proporção de falhas de Kupiec (1995), o teste de independência de Christoffersen (1998), o teste de "
          "quantil dinâmico de Engle e Manganelli (2004) e a classificação por zonas de Basileia II, calculada sobre "
          "uma janela de 250 dias úteis, conforme o Acordo de Basileia II (BASEL COMMITTEE ON BANKING SUPERVISION, "
          "2004). Todos foram validados com séries sintéticas de taxa de violação conhecida antes da aplicação a "
          "dados reais."),
    ("P", "O protocolo do experimento é o mesmo para todos os modelos e ativos. Para cada ativo, toma-se a década de "
          "preços disponível — de 27 de setembro de 2016 a 25 de setembro de 2026. Os primeiros 252 dias úteis "
          "formam a janela de treino inicial, e os 2.238 dias seguintes (2.230 no Ibovespa) formam o período de "
          "teste, fora da amostra, em que cada modelo estima o VaR de cada dia usando apenas os dados anteriores a "
          "ele. O período de teste é ainda recortado em nove anos de 252 pregões (o último, incompleto, com 214), "
          "avaliados separadamente. Um modelo é considerado adequado quando não é rejeitado, ao nível de "
          "significância de 5%, pelo teste de Kupiec e pelo de Christoffersen. O teste DQ e as zonas de Basileia são "
          "reportados, mas não entram no veredito: o DQ rejeita quase todos os modelos em amostras longas, e as "
          "zonas de Basileia foram definidas para janelas de 250 dias, e não para uma década."),
    ("P", "A Tabela 1 apresenta o resultado dos nove modelos para PETR4, nos dois níveis de confiança."),
    ("TAB", "petr4", "Tabela 1 – Backtesting dos nove modelos, PETR4 (setembro de 2017 a setembro de 2026)",
     "Fonte: Os autores, a partir dos resultados gravados pela plataforma. Nota: p-valores dos testes; o veredito é "
     "“adequado” quando Kupiec e Christoffersen não rejeitam a hipótese nula a 5%."),
    ("P", "A 95%, apenas a LSTM e o GARCHNet foram considerados adequados; os dois estão também entre os cinco "
          "modelos não rejeitados pelo teste DQ, com o CAViaR, a GRU e o GARCH(1,1). Os modelos paramétrico e de "
          "Monte Carlo estimaram um VaR conservador demais — 53 violações contra 111,9 esperadas —, o que leva à "
          "rejeição pelo teste de Kupiec: o modelo erra para o lado da prudência, mas erra. A 99%, o quadro muda: "
          "sete dos nove modelos passam no teste de Kupiec, mas seis deles são rejeitados pelo de Christoffersen, "
          "e apenas o CAViaR foi considerado adequado."),
    ("P", "A Figura 2 mostra por que os dois testes discordam. Ela compara, para PETR4 a 99%, o VaR da simulação "
          "histórica e o do GARCH(1,1) com os retornos diários. O VaR histórico muda pouco — só a cada reestimação "
          "anual —, e 16 das suas 19 violações, em número compatível com as 22,4 esperadas, concentram-se em quatro "
          "episódios: a greve dos caminhoneiros (maio e junho de 2018), o choque da pandemia (fevereiro e março de "
          "2020), a troca de comando da Petrobras (fevereiro de 2021) e o período eleitoral (outubro a dezembro de "
          "2022). O GARCH(1,1) acompanha a volatilidade e se ajusta logo depois de cada choque, mas, nos períodos "
          "calmos, estima um VaR menor do que o necessário e acumula 35 violações. O teste de Kupiec, que olha a "
          "frequência das violações, reprova o GARCH(1,1) pelo excesso; o de Christoffersen, que olha também a "
          "independência entre elas, reprova o histórico pelo agrupamento."),
    ("FIG", "serie_petr4.png", "Figura 2 – VaR a 99% e violações da simulação histórica e do GARCH(1,1), PETR4",
     FONTE_EXP),
    ("H2", "4.5 Etapa 5 – Interface Web"),
    ("P", "A interface web foi implementada como uma aplicação React que consome a API REST. A página inicial traz "
          "a busca no catálogo de ações da B3, que ignora acentos e maiúsculas. Cada ativo tem uma página com seis "
          "abas — Visão geral, Risco, Laboratório, Retorno, Fundamentos e Comunicados —, cada uma com endereço "
          "próprio, e a interface oferece duas leituras, uma para iniciantes e outra avançada, e os temas claro e "
          "escuro. A Figura 3 mostra a visão geral de PETR4, com o preço ajustado dos dez anos."),
    ("FIG", "02-visao-geral.png", "Figura 3 – Visão geral do ativo PETR4", FONTE_TELA),
    ("P", "A aba Risco (Figura 4) responde à pergunta central da plataforma — quanto se pode perder em um dia — com "
          "a faixa de perda estimada pelos modelos a 95% e a 99% e os modelos não rejeitados pelos testes. Abaixo, "
          "cada um dos nove modelos mostra a perda estimada, as violações observadas e esperadas, os p-valores dos "
          "três testes e o veredito. Uma coluna lateral, a trilha do cálculo, registra a série usada, a divisão "
          "entre treino e teste, a versão do motor e a semente, para que o cálculo possa ser conferido e refeito."),
    ("FIG", "03-risco.png", "Figura 4 – Aba Risco do ativo PETR4", FONTE_TELA),
    ("P", "A aba Laboratório (Figura 5) apresenta o experimento da década descrito na Seção 4.4, com o resultado de "
          "cada modelo na década inteira e ano a ano. A aba Retorno traz, como complemento, dois modelos simples de "
          "previsão do retorno do dia seguinte (a média histórica e um modelo autorregressivo de primeira ordem), "
          "validados fora da amostra contra a previsão de retorno zero; nos ativos avaliados, nenhum dos dois "
          "superou essa referência, e a plataforma mostra a previsão sempre junto dessa validação."),
    ("FIG", "04-laboratorio.png", "Figura 5 – Aba Laboratório do ativo PETR4", FONTE_TELA),
    ("P", "Os testes de usabilidade com usuários-alvo, previstos na Etapa 5, não foram realizados dentro do prazo. A "
          "interface foi verificada por testes automatizados (1.830 testes do front-end) e por roteiros que abrem "
          "as telas em um navegador real e conferem os valores exibidos contra os da API; cada tela passou antes "
          "por um protótipo visual aprovado pela equipe. A avaliação com usuários permanece como trabalho futuro."),
    ("H2", "4.6 Etapa 6 – Ranking Comparativo dos Modelos"),
    ("P", "O experimento comparativo executou os nove modelos, nos dois níveis de confiança, sobre os quatro ativos "
          "— 72 combinações, todas concluídas sem erro. A Figura 6 resume o resultado: para cada combinação, a "
          "razão entre as violações observadas e as esperadas — 1 indica calibração perfeita; abaixo de 1, um VaR "
          "conservador; acima de 1, um VaR que subestima o risco — e, marcadas com asterisco, as combinações "
          "consideradas adequadas."),
    ("FIG", "razao_violacoes.png",
     "Figura 6 – Violações observadas sobre esperadas, por modelo, ativo e nível de confiança",
     "Fonte: Os autores, a partir dos resultados gravados pela plataforma. Nota: * modelo adequado (Kupiec e "
     "Christoffersen não rejeitam a 5%)."),
    ("P", "Três padrões se destacam. Primeiro, nenhum modelo é adequado em todos os casos: o melhor, o CAViaR, é "
          "adequado em quatro das oito combinações de ativo e nível. Segundo, o ativo pesa tanto quanto o modelo: "
          "no Itaú Unibanco (ITUB4), cinco modelos são adequados a 95%; na Vale (VALE3), nenhum. A série da Vale "
          "contém choques idiossincráticos, como a queda de 28,2% no pregão seguinte ao rompimento da barragem de "
          "Brumadinho, em janeiro de 2019, e todos os modelos ficaram conservadores demais a 95% nesse ativo, com "
          "menos violações do que as esperadas. Terceiro, a 99% o teste de Christoffersen é o principal obstáculo: "
          "as violações, raras, tendem a se concentrar nas mesmas crises, e a independência entre elas é rejeitada "
          "mesmo quando a quantidade está correta."),
    ("P", "A Tabela 2 ordena os modelos pelo número de combinações adequadas e, no empate, pelo número de "
          "combinações em que o modelo também não é rejeitado pelo DQ, depois pelo número de aprovações no DQ e, por "
          "fim, pelo menor desvio médio entre as violações observadas e as esperadas. A última coluna traz a "
          "classificação de Basileia aplicada a cada ano completo de 252 pregões a 99%: a zona verde corresponde a "
          "até quatro violações no ano. O ranking reflete esse critério, definido pelos autores: as diferenças entre "
          "posições vizinhas são pequenas e não foram submetidas a um teste estatístico de comparação entre "
          "modelos, de modo que a ordem deve ser lida como indicativa, e não como prova de superioridade."),
    ("TAB", "ranking", "Tabela 2 – Ranking dos nove modelos nos quatro ativos e dois níveis de confiança",
     "Fonte: Os autores, a partir dos resultados gravados pela plataforma. Nota: as quatro primeiras colunas de "
     "números contam as 8 combinações de ativo e nível; a zona verde conta os 32 anos completos a 99% (4 ativos × 8 "
     "anos)."),
    ("P", "O CAViaR, que estima o quantil diretamente, sem supor uma distribuição para os retornos, ficou em "
          "primeiro lugar no critério adotado e foi o único não rejeitado pelo teste de Christoffersen em sete das oito combinações. O "
          "GARCH(1,1) ficou em segundo e foi o único modelo que não caiu na zona vermelha de Basileia em nenhum ano. "
          "A LSTM ficou em terceiro e teve o menor desvio médio entre violações observadas e esperadas (16,6%), isto "
          "é, foi a mais bem calibrada em quantidade, mas foi rejeitada com frequência pela dependência entre as "
          "violações. Os modelos paramétrico e de Monte Carlo não foram adequados em nenhuma combinação."),
    ("P", "A análise ano a ano (Figura 7) confirma a ordem. A 95%, o CAViaR é adequado em 28 dos 36 anos avaliados, "
          "seguido da LSTM e do GARCHNet (25) e do GARCH(1,1) (24); os modelos paramétrico e de Monte Carlo, em "
          "apenas 13. A 99%, com cerca de 2,5 violações esperadas por ano, os testes não são aplicados ano a ano."),
    ("FIG", "anos_adequados.png", "Figura 7 – Anos considerados adequados a 95%, por modelo", FONTE_EXP),
    ("P", "Esses resultados revisam as conclusões preliminares do TCC I. Lá, a LSTM a 95% sobre PETR4 havia sido o "
          "único modelo aprovado nos quatro testes, e os modelos GARCH pareciam superiores aos tradicionais. Com a "
          "semente fixa, a correção do motor e a janela expansiva, a LSTM segue entre os melhores para PETR4 a 95% "
          "— adequada e não rejeitada pelo DQ —, mas não domina nos demais ativos e níveis; e a vantagem dos modelos "
          "de volatilidade condicional sobre os tradicionais aparece no GARCH(1,1), mas não no EGARCH, cujo desvio "
          "médio foi o maior entre os nove (51,9%)."),
]

CAP5 = [
    ("H1", "5 CONSIDERAÇÕES FINAIS"),
    ("P", "Este trabalho teve como objetivo desenvolver uma plataforma web para modelagem e backtesting de VaR que "
          "integrasse métodos estatísticos tradicionais, modelos GARCH e algoritmos de Machine Learning, aplicada a "
          "ativos negociados na B3. O objetivo foi alcançado: o Ruvor calcula, para qualquer ação da B3 com histórico "
          "suficiente, o VaR por nove modelos nos níveis de 95% e 99%, valida cada estimativa por quatro "
          "instrumentos de backtesting e apresenta os resultados em uma interface web, com a trilha do cálculo. Os "
          "objetivos específicos foram atendidos na ordem da Matriz de Validação: os métodos tradicionais (a), os "
          "modelos GARCH e EGARCH (b), os modelos de Machine Learning e o híbrido GARCHNet (c), o módulo de "
          "backtesting (d), a interface web (e) e a avaliação comparativa sobre quatro ativos da B3 (f)."),
    ("P", "O principal resultado empírico é que nenhum modelo foi adequado em todos os casos. O CAViaR, o GARCH(1,1) "
          "e a LSTM ocuparam as primeiras posições no critério adotado, com diferenças pequenas entre si, e os "
          "métodos paramétrico e de Monte Carlo, as últimas; mas a ordem muda conforme o ativo e o nível de confiança, e em um dos ativos, a VALE3, nenhum modelo foi "
          "adequado a 95%. Os modelos de Machine Learning não foram uniformemente superiores aos estatísticos: os "
          "que ficaram à frente foram os que estimam o quantil diretamente, como o CAViaR e a LSTM. Esse resultado "
          "sustenta o diferencial proposto para a plataforma — comparar vários modelos sobre a mesma base, com "
          "validação estatística, para cada ativo — em vez de adotar um único modelo para todos."),
    ("P", "O desenvolvimento também deixou uma lição de método. As conclusões preliminares do TCC I mudaram depois "
          "de três correções: a semente fixa nos modelos aleatórios, a eliminação do uso do retorno do próprio dia "
          "no VaR do GARCH e do EGARCH e a reestimação dos modelos tradicionais em janela expansiva. Por isso, a "
          "plataforma grava cada resultado com a versão do motor, a semente e as versões das bibliotecas, de forma "
          "imutável, e mantém testes automatizados que provam que nenhum modelo usa informação do futuro."),
    ("P", "O trabalho tem limitações. O experimento cobre quatro ativos e uma década, o horizonte de um dia e um "
          "único ativo por vez. O veredito considera os testes de Kupiec e de Christoffersen; o DQ e as zonas de "
          "Basileia são apenas reportados, e a classificação de Basileia foi aplicada a anos de 252 pregões, e não "
          "a janelas móveis de 250 dias. A ordem do ranking não foi submetida a um teste estatístico de comparação entre "
          "modelos, e o experimento foi executado uma única vez, sobre a série de cada ativo disponível na data. A "
          "busca de hiperparâmetros das redes foi reduzida a duas dimensões, e os testes de usabilidade com "
          "usuários-alvo não foram realizados."),
    ("P", "Como trabalhos futuros, propõem-se a avaliação da interface com usuários-alvo; a comparação "
          "estatística entre os modelos, para verificar se as diferenças do ranking são significativas; a ampliação do experimento "
          "a mais ativos, o que a plataforma já permite, pois calcula sob demanda qualquer ação do catálogo; a "
          "inclusão do Expected Shortfall e de horizontes de mais de um dia; as telas de risco de carteiras, cujo "
          "cálculo já existe na plataforma; e a incorporação dos testes de backtesting voltados ao agrupamento de "
          "violações discutidos por Berger e Moys (2021)."),
]
