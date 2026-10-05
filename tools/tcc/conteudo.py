# Texto novo do TCC II: capítulos 4 e 5, Resumo e Abstract, e as trocas pontuais nos capítulos 1 a 3.

RESUMO = (
    "O Value at Risk (VaR) é a medida de referência para estimar a perda máxima de um investimento em um "
    "horizonte e um nível de confiança dados, mas os métodos de cálculo divergem entre si, e são escassas as "
    "ferramentas que permitem compará-los, com validação estatística, sobre dados do mercado brasileiro. Este "
    "trabalho apresenta o Ruvor, uma plataforma web que calcula o VaR de ações da B3 por nove modelos — três "
    "tradicionais (simulação histórica, paramétrico e Monte Carlo), dois de volatilidade condicional (GARCH(1,1) "
    "e EGARCH) e quatro de Machine Learning (LSTM, GRU, CAViaR e o híbrido GARCHNet) — e valida cada estimativa "
    "pelos testes de Kupiec, de Christoffersen e de quantil dinâmico e pelas zonas de Basileia. A plataforma foi "
    "construída em Python, com Django, PostgreSQL e uma interface em React, e grava cada resultado com a versão "
    "do motor de cálculo e a semente aleatória, o que permite refazê-lo. No experimento comparativo, com dez anos "
    "de dados do Ibovespa, de PETR4, de VALE3 e de ITUB4, nos níveis de 95% e 99%, nenhum modelo foi adequado em "
    "todos os casos: no critério adotado, o CAViaR ficou à frente, adequado em quatro das oito combinações de "
    "ativo e nível, seguido do GARCH(1,1) e da LSTM, com diferenças pequenas entre eles, enquanto os métodos paramétrico e de Monte Carlo não foram adequados em nenhuma. O resultado "
    "indica que o modelo mais confiável depende do ativo e do nível de confiança, e reforça a utilidade de "
    "comparar os modelos sob o mesmo protocolo antes de confiar em um deles."
)
PALAVRAS = "Palavras-chave: Value at Risk; backtesting; Machine Learning; mercado de ações; B3."

ABSTRACT = (
    "Value at Risk (VaR) is the reference measure for estimating the maximum loss of an investment over a given "
    "horizon and confidence level, but the methods used to compute it disagree, and tools that compare them with "
    "statistical validation on Brazilian market data are scarce. This work presents Ruvor, a web platform that "
    "computes the VaR of stocks listed on B3 with nine models — three traditional ones (historical simulation, "
    "parametric and Monte Carlo), two conditional volatility models (GARCH(1,1) and EGARCH) and four Machine "
    "Learning models (LSTM, GRU, CAViaR and the hybrid GARCHNet) — and validates every estimate with the Kupiec, "
    "Christoffersen and dynamic quantile tests and the Basel traffic-light zones. The platform was built in Python, "
    "with Django, PostgreSQL and a React interface, and stores every result together with the engine version and "
    "the random seed, so that it can be reproduced. In the comparative experiment, with ten years of data for the "
    "Ibovespa index, PETR4, VALE3 and ITUB4 at the 95% and 99% levels, no model was adequate in every case: CAViaR "
    "ranked first under the adopted criterion, adequate in four of the eight asset and level combinations, "
    "followed by GARCH(1,1) and LSTM, with small differences among them, while the parametric and Monte Carlo methods were adequate in none. The result indicates that the most reliable model "
    "depends on the asset and on the confidence level, and supports comparing models under the same protocol "
    "before relying on any of them."
)
KEYWORDS = "Keywords: Value at Risk; backtesting; Machine Learning; stock market; B3."

# (prefixo do parágrafo, trecho antigo, trecho novo) — troca dentro do parágrafo
TROCAS = [
    ("Este trabalho propõe o desenvolvimento", "com o framework Flask/Django,",
     "com o framework Django no servidor e a biblioteca React na interface,"),
    ("A justificativa para a realização", "Embora a literatura internacional apresenta", "Embora a literatura internacional apresente"),
    ("Embora esses estudos evidenciam", "Embora esses estudos evidenciam", "Embora esses estudos evidenciem"),
    ("A proposta deste projeto consiste no desenvolvimento", "construída em Python com o framework Flask,",
     "construída em Python com o framework Django,"),
    ("Etapa 1: Módulo de coleta", "coleta automatizada via yfinance,", "coleta automatizada do Yahoo Finance,"),
    ("Etapa 6: Experimento comparativo", "(Ibovespa, PETR4, VALE3 e ITUB4) no período de 2015 a 2024.",
     "(Ibovespa, PETR4, VALE3 e ITUB4), nos dez anos de dados de cada um."),
    ("Entre os fatores favoráveis",
     "A biblioteca yfinance oferece cobertura consistente para ativos da B3 com integração direta ao pandas, simplificando a etapa de coleta e preparação dos dados.",
     "O serviço de cotações do Yahoo Finance oferece cobertura consistente para ativos da B3, com preços ajustados a proventos e desdobramentos, o que simplifica a etapa de coleta e preparação dos dados."),
    ("Entre os fatores favoráveis",
     "o período histórico selecionado (2015–2024) é especialmente rico em termos de regimes de volatilidade, incluindo a crise hídrica e recessão de 2015–2016, os episódios de instabilidade política de 2017–2018,",
     "o período histórico do experimento (2016–2026) é especialmente rico em termos de regimes de volatilidade, incluindo a greve dos caminhoneiros de 2018, o rompimento da barragem de Brumadinho em 2019,"),
    ("Em contrapartida, identificam-se", "dados históricos da B3 via yfinance:", "dados históricos da B3 obtidos de uma fonte gratuita:"),
]

# parágrafos reescritos inteiros: (prefixo, texto novo)
REESCRITOS = [
    ("A plataforma será construída utilizando",
     "A plataforma foi construída em Python, com o framework Django no servidor, banco de dados PostgreSQL e "
     "interface web em React, e permite consultar um ativo da B3 e ver, lado a lado, a perda estimada por cada "
     "modelo nos níveis de 95% e 99% de confiança, para o horizonte de um dia, junto com o backtesting automático "
     "de cada estimativa. Para a validação dos modelos, são empregados testes estatísticos consolidados na "
     "literatura: o teste de proporção de falhas de Kupiec (1995), o teste de cobertura condicional de "
     "Christoffersen (1998) e o teste de quantil dinâmico (DQ) proposto por Engle e Manganelli (2004)."),
    ("Este trabalho está organizado em",
     "Este trabalho está organizado em quatro capítulos, além desta introdução. O Capítulo 2 apresenta o "
     "referencial teórico: os conceitos de Value at Risk, os métodos tradicionais de cálculo, os modelos GARCH de "
     "volatilidade condicional, os fundamentos de Machine Learning aplicados a finanças, as técnicas de "
     "backtesting, o arcabouço regulatório de Basileia e os estudos prévios que relacionam essas temáticas. O "
     "Capítulo 3 descreve os procedimentos metodológicos: a proposta de solução, as decisões de arquitetura, as "
     "etapas de implementação, os resultados esperados e os fatores críticos para o sucesso. O Capítulo 4 "
     "apresenta os resultados de cada etapa, com o experimento comparativo dos nove modelos sobre quatro ativos "
     "da B3, e o Capítulo 5 traz as considerações finais, as limitações e os trabalhos futuros."),
    ("Os dados de mercado serão obtidos",
     "Os dados de mercado são obtidos do serviço de cotações do Yahoo Finance, consultado diretamente por HTTP, "
     "que fornece séries históricas de preços ajustados a proventos e desdobramentos para os ativos negociados na "
     "B3; o catálogo de ações vem do site da própria B3. A coleta abrange os dez anos mais recentes de cada ativo "
     "— no experimento deste trabalho, de setembro de 2016 a setembro de 2026 —, período que atravessa vários "
     "regimes de volatilidade do mercado brasileiro, como a greve dos caminhoneiros de 2018, o choque da pandemia "
     "de COVID-19 em 2020, a troca de comando da Petrobras em 2021 e o ciclo de alta dos juros de 2021–2023."),
    ("Etapa 5: Interface web interativa",
     "Etapa 5: Interface web interativa (prioridade alta): desenvolvimento da API REST que expõe os resultados dos "
     "módulos de modelagem e backtesting, construção da interface em React para a busca de ativos e a consulta "
     "dos resultados, e implementação dos gráficos e das tabelas comparativas dos modelos. Testes de usabilidade "
     "com usuários-alvo (estudantes de ciência de dados e finanças quantitativas) estavam previstos para verificar "
     "a clareza da interface e a interpretabilidade dos resultados."),
]

# a seção 3.2 inteira (substitui os sete parágrafos antigos); "FIG:" marca uma figura
SECAO_32 = [
    "O Ruvor foi desenvolvido com base em uma arquitetura modular, representada na Figura 1. O núcleo numérico — "
    "os nove modelos de VaR e os quatro testes de backtesting — forma um pacote Python independente, o motor de "
    "cálculo, que não depende do servidor web e pode ser executado isoladamente por linha de comando. Cada modelo "
    "cumpre uma interface comum e é registrado em um catálogo de modelos, o que permite acrescentar um modelo novo "
    "sem alterar o restante da plataforma.",
    "FIG:arquitetura.png|Figura 1 – Arquitetura do Ruvor",
    "Back-end: na proposta do TCC I, o framework Flask havia sido escolhido por sua leveza, em uma plataforma sem "
    "banco de dados e sem autenticação. Ao longo do desenvolvimento, a plataforma passou a guardar o histórico de "
    "preços e de cálculos, a ter contas de usuário e a executar cálculos demorados em segundo plano, e o framework "
    "Django foi adotado no lugar do Flask, por oferecer de forma integrada o mapeamento objeto-relacional, as "
    "migrações do banco de dados e a autenticação. A API segue o padrão REST, com o Django REST Framework, e os "
    "cálculos rodam em uma fila de tarefas Celery, com uma rotina diária agendada.",
    "Módulos de modelagem: os modelos tradicionais (paramétrico, simulação histórica e Monte Carlo) são "
    "implementados com NumPy e SciPy; o GARCH(1,1) e o EGARCH, com a biblioteca arch; a LSTM, a GRU e o componente "
    "neural do GARCHNet, com Keras sobre TensorFlow; e o CAViaR, por otimização numérica com SciPy (Seção 4.3). Os "
    "modelos com componente aleatório usam semente fixa, de modo que o mesmo cálculo, repetido, produz o mesmo "
    "resultado.",
    "Fonte de dados e armazenamento: diferentemente do previsto no TCC I, os dados não ficam apenas em memória. O "
    "banco PostgreSQL é organizado em três camadas: bronze, com os dados brutos como chegaram da fonte; silver, com "
    "os preços conformados e os retornos logarítmicos diários; e gold, com os resultados dos cálculos — o VaR de "
    "cada modelo, os testes de backtesting e o veredito —, gravados de forma imutável, junto com a versão do motor, "
    "a semente e as versões das bibliotecas, para que qualquer resultado possa ser conferido e refeito.",
    "Parâmetros padrão: níveis de confiança de 95% e 99%, calculados simultaneamente; horizonte de um dia útil; "
    "janela de treino inicial de 252 dias úteis, com reestimação a cada 252 dias úteis em janela expansiva. "
    "Diferentemente do previsto, esses parâmetros são fixos: em vez de o usuário configurar cada cálculo, a "
    "plataforma calcula os nove modelos para cada ativo coberto, todos sobre a mesma série, o que torna os "
    "resultados diretamente comparáveis.",
    "Front-end e visualização: a interface é uma aplicação React em TypeScript, separada do servidor, que consome "
    "a API REST. Os gráficos usam a biblioteca uPlot, e as tabelas comparativas mostram, para cada modelo e nível "
    "de confiança, a perda estimada, o número de violações, os p-valores dos testes e o veredito de adequação. Pela "
    "API, o relatório de risco de um ativo pode ser gerado e baixado em JSON e CSV, guardado com o seu resumo "
    "criptográfico (SHA-256).",
]
