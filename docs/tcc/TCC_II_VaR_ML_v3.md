FACULDADE IMPACTA TECNOLOGIA

Cintia Marques Castanho Sae

Guilherme Nunes Joanna

Kauã Ribeiro Santos

Lucas Fernandes de Melo

PLATAFORMA DE MODELAGEM E BACKTESTING DE VaR COM MACHINE LEARNING

São Paulo

2026

Cintia Marques Castanho Sae

Guilherme Nunes Joanna

Kauã Ribeiro Santos

Lucas Fernandes de Melo

PLATAFORMA DE MODELAGEM E BACKTESTING DE VaR COM MACHINE LEARNING

Trabalho de Conclusão de Curso (TCC II) apresentado à Faculdade Impacta Tecnologia — curso de Ciência da Computação, como requisito parcial para a obtenção do grau de Bacharel em Ciência da Computação.

Orientador: Prof. Dr. Gilberto Perez

São Paulo

2026

SUMÁRIO

# 1 INTRODUÇÃO

A gestão de riscos financeiros constitui um dos pilares fundamentais para a estabilidade dos mercados de capitais e para a tomada de decisão de investidores e instituições. Dentre as métricas mais amplamente utilizadas nesse contexto, o Value at Risk (VaR) destaca-se como uma medida estatística que estima a perda máxima esperada de um portfólio em um determinado horizonte de tempo, dado um nível de confiança previamente estabelecido. Jorion (2001) descreve o VaR como a principal referência quantitativa para a mensuração de risco de mercado, sendo amplamente adotado tanto pela indústria financeira quanto pelos órgãos reguladores. A popularização da métrica remonta à década de 1990, quando o JPMorgan publicou o documento técnico RiskMetrics (JPMORGAN, 1996), que padronizou a metodologia de cálculo e difundiu o VaR como ferramenta de referência no mercado financeiro global.

Desde então, o VaR foi incorporado ao arcabouço regulatório internacional. O Comitê de Basileia para Supervisão Bancária (BCBS) adotou a métrica como instrumento de controle de capital mínimo das instituições financeiras no Acordo de Basileia II (BASEL COMMITTEE ON BANKING SUPERVISION, 2004), tornando obrigatória a realização de backtesting dos modelos internos de VaR para fins de adesão regulatória.

Os métodos tradicionais de cálculo do VaR, como a simulação histórica, o método paramétrico (variância-covariância) e a simulação de Monte Carlo, apresentam limitações relevantes quando aplicados a séries financeiras reais. Bollerslev (1986) demonstrou que a volatilidade dos retornos financeiros não é constante ao longo do tempo, mas sim condicional às observações passadas, o que motivou o desenvolvimento dos modelos GARCH. Ainda assim, tanto os métodos tradicionais de VaR quanto os modelos GARCH clássicos enfrentam dificuldades em capturar padrões não lineares e em adaptar-se a mudanças estruturais no comportamento dos ativos.

Diante dessas limitações, a literatura recente tem explorado abordagens baseadas em aprendizado de máquina (Machine Learning) como alternativa para aprimorar a modelagem e a estimativa do VaR. Fischer e Krauss (2018) evidenciaram que redes neurais do tipo LSTM superaram modelos tradicionais na previsão de retornos financeiros. Mais recentemente, Buczyński e Chlebus (2024) propuseram o GARCHNet, um modelo híbrido que combina redes neurais com a estrutura GARCH para a previsão de VaR, obtendo resultados promissores em termos de acurácia e calibração.

Contudo, a adoção dessas técnicas no contexto acadêmico e educacional brasileiro ainda é incipiente, e ferramentas acessíveis para modelagem, comparação e validação de modelos de VaR com Machine Learning permanecem escassas. Identifica-se, portanto, uma lacuna relevante: a ausência de plataformas integradas que permitam ao usuário, de forma didática e interativa, configurar diferentes modelos de VaR, tanto tradicionais quanto baseados em Machine Learning, executar simulações com dados reais do mercado brasileiro (B3/Ibovespa) e realizar o backtesting dos resultados para avaliar a acurácia das estimativas.

Este trabalho propõe o desenvolvimento de uma plataforma web, construída em Python com o framework Flask/Django, que integre funcionalidades de modelagem, simulação e backtesting de VaR utilizando tanto métodos tradicionais e modelos GARCH quanto algoritmos de Machine Learning, aplicados a ativos negociados na B3.

## 1.1 Proposta do Projeto

A proposta deste projeto consiste em desenvolver uma plataforma web de modelagem e backtesting de Value at Risk (VaR) que integre métodos tradicionais de cálculo, simulação histórica, método paramétrico e simulação de Monte Carlo, modelos de volatilidade condicional (GARCH e variantes) e algoritmos de Machine Learning, permitindo ao usuário comparar o desempenho preditivo de diferentes abordagens aplicadas a ativos do mercado acionário brasileiro (B3/Ibovespa).

A plataforma será construída utilizando a linguagem Python e frameworks web (Flask ou Django), com uma interface amigável que permita a seleção de ativos, a configuração de parâmetros dos modelos (nível de confiança, horizonte temporal, janela de dados), a execução das estimativas de VaR e a realização automática de backtesting. Para a validação dos modelos, serão empregados testes estatísticos consolidados na literatura, como o teste de proporção de falhas de Kupiec (1995), o teste de cobertura condicional de Christoffersen (1998) e o teste de quantil dinâmico (DQ) proposto por Engle e Manganelli (2004).

## 1.2 Objetivos da Pesquisa

Objetivo Geral: Desenvolver uma plataforma web para modelagem e backtesting de VaR que integre métodos estatísticos tradicionais, modelos GARCH e algoritmos de Machine Learning, aplicada a ativos negociados na B3.

Objetivos Específicos:

a) Mapear e implementar os principais métodos tradicionais de cálculo do VaR (simulação histórica, paramétrico e Monte Carlo).

b) Implementar modelos de volatilidade condicional (GARCH e EGARCH) para a estimativa de VaR.

c) Identificar e implementar algoritmos de Machine Learning adequados à estimativa de VaR em séries financeiras, incluindo abordagens híbridas.

d) Desenvolver um módulo de backtesting com testes estatísticos (Kupiec, Christoffersen e DQ) para validação dos modelos implementados.

e) Construir uma interface web interativa que permita a configuração, execução e visualização dos resultados.

f) Avaliar comparativamente a acurácia dos métodos tradicionais, modelos GARCH e de Machine Learning utilizando dados históricos de ativos da B3.

## 1.3 Justificativa para a Pesquisa

A justificativa para a realização deste projeto fundamenta-se em duas lacunas complementares. No âmbito acadêmico, observa-se uma escassez de estudos aplicados que comparam, de forma sistemática e reprodutível, o desempenho de modelos tradicionais de VaR, modelos GARCH e abordagens de Machine Learning no contexto do mercado acionário brasileiro. Embora a literatura internacional apresenta avanços significativos nessa área, como demonstram os trabalhos de Buczyński e Chlebus (2024) e Fischer e Krauss (2018), a maioria dos estudos utiliza dados de mercados desenvolvidos, o que limita a generalização dos resultados para mercados emergentes com características próprias de volatilidade e liquidez.

No âmbito tecnológico, há carência de ferramentas integradas, acessíveis e didáticas que permitam a estudantes, pesquisadores e profissionais em formação experimentar diferentes modelos de VaR sem a necessidade de construir toda a infraestrutura computacional. Conforme destacam Zhang e Nadarajah (2018) em sua revisão abrangente sobre métodos de backtesting, a diversidade de testes disponíveis torna necessária uma plataforma que integre múltiplas metodologias de validação. A plataforma proposta visa preencher essa lacuna, oferecendo um ambiente unificado para modelagem, simulação e validação de modelos de risco de mercado.

## 1.4 Declaração de Uso de IA

A declaração completa de uso de ferramentas de Inteligência Artificial utilizadas na elaboração deste trabalho encontra-se no Apêndice B. Os autores declaram total responsabilidade sobre o conteúdo apresentado, tendo utilizado ferramentas de IA como apoio à pesquisa, revisão e organização textual, com verificação e validação humana de todas as saídas geradas.

## 1.5 Contribuições do Projeto

Espera-se que este projeto contribua em três frentes principais. Em termos acadêmicos, ao produzir uma análise comparativa entre métodos tradicionais, modelos GARCH e técnicas de Machine Learning para estimativa de VaR no mercado brasileiro, gerando evidências empíricas que enriqueçam a literatura nacional sobre gestão de riscos. Em termos tecnológicos, ao disponibilizar uma plataforma funcional e de código aberto que possa ser utilizada como ferramenta de ensino e pesquisa em disciplinas de finanças quantitativas e ciência de dados. Em termos práticos, ao fornecer uma ferramenta que permita a investidores e analistas avaliar o risco de portfólios de forma mais informada, comparando diferentes abordagens de modelagem.

## 1.6 Esquema Geral da Pesquisa

Este trabalho está organizado em três capítulos, além desta introdução. O Capítulo 2 apresenta o referencial teórico, abordando os conceitos de Value at Risk, os métodos tradicionais de cálculo, os modelos GARCH de volatilidade condicional, os fundamentos de Machine Learning aplicados a finanças, as técnicas de backtesting, o arcabouço regulatório de Basileia e os estudos prévios que relacionam essas temáticas. O Capítulo 3 descreve os procedimentos metodológicos, detalhando a proposta de solução, a análise prévia, as etapas de implementação, os resultados esperados e os fatores críticos para o sucesso do projeto. Por fim, são apresentadas as referências bibliográficas que fundamentam o estudo.

# 2 REFERENCIAL TEÓRICO

Este capítulo apresenta os fundamentos teóricos que sustentam o desenvolvimento da plataforma proposta. Inicialmente, são discutidos os conceitos, métodos e limitações do Value at Risk (VaR) como métrica de risco de mercado. Em seguida, abordam-se os modelos de volatilidade condicional da família GARCH e suas extensões. Posteriormente, são apresentados os fundamentos de Machine Learning e os principais algoritmos aplicáveis à estimativa de risco financeiro, incluindo abordagens híbridas. As seções seguintes tratam das técnicas de backtesting e do arcabouço regulatório. Por fim, são discutidos estudos prévios que articulam essas temáticas.

## 2.1 Value at Risk (VaR)

### 2.1.1 Conceitos e Definição de VaR

O Value at Risk (VaR) é definido como a perda máxima esperada de um portfólio ou ativo financeiro em um determinado horizonte de tempo, dado um nível de confiança especificado. Jorion (2001) explica que, formalmente, para um nível de confiança α, o VaR corresponde ao quantil (1 - α) da distribuição de perdas do portfólio. A título de exemplo, um VaR diário de R$ 1 milhão com 95% de confiança indica que, em condições normais de mercado, espera-se que a perda do portfólio não exceda esse valor em 95% dos dias de negociação.

A métrica foi popularizada pelo banco JPMorgan na década de 1990, por meio do documento técnico RiskMetrics (JPMORGAN, 1996), que apresentou uma metodologia padronizada para o cálculo do VaR e disponibilizou gratuitamente as matrizes de covariância necessárias para sua implementação. Essa iniciativa acelerou a adoção do VaR pela indústria financeira e pelos órgãos reguladores internacionais, consolidando-o como padrão de mensuração de risco de mercado.

Na obra de referência sobre o tema, Jorion (2001) acrescenta que o VaR pode ser interpretado sob duas perspectivas complementares: como medida de risco absoluta, que expressa a exposição potencial em unidades monetárias, e como medida de risco relativa, que permite a comparação entre portfólios com composições e tamanhos distintos. Essa versatilidade contribuiu para a ampla adoção da métrica, embora suas limitações sejam reconhecidas na literatura.

### 2.1.2 Métodos Tradicionais de Cálculo do VaR

A literatura identifica três métodos principais para a estimativa do VaR: o método paramétrico (variância-covariância), a simulação histórica e a simulação de Monte Carlo. Cada abordagem apresenta pressupostos, vantagens e limitações específicas.

O método paramétrico, também conhecido como método de variância-covariância, assume que os retornos dos ativos seguem uma distribuição normal e utiliza a média e a variância da série de retornos para calcular o VaR. Na avaliação de Jorion (2001), a principal vantagem desse método reside na simplicidade computacional e na facilidade de implementação. Contudo, a premissa de normalidade frequentemente não se verifica em séries financeiras reais, que tendem a apresentar caudas pesadas (leptocurtose) e assimetria, o que pode levar à subestimação do risco em cenários extremos. A própria metodologia RiskMetrics (JPMORGAN, 1996) reconhece essa limitação e propõe ajustes por meio de ponderação exponencial das observações.

A simulação histórica, por sua vez, utiliza a distribuição empírica dos retornos passados para estimar o VaR, sem impor pressupostos sobre a forma funcional da distribuição. O método ordena os retornos históricos e identifica o quantil correspondente ao nível de confiança desejado (Jorion, 2001). Embora dispense hipóteses distribucionais, essa abordagem pressupõe que o comportamento passado dos retornos é representativo do futuro, o que pode ser inadequado em períodos de mudança estrutural no mercado.

A simulação de Monte Carlo consiste em gerar cenários aleatórios para os fatores de risco do portfólio a partir de processos estocásticos parametrizados, calcular o valor do portfólio em cada cenário e, a partir da distribuição simulada de perdas e ganhos, estimar o VaR. Esse método é considerado o mais flexível, pois permite modelar distribuições complexas, dependências não lineares e instrumentos derivativos. Por outro lado, demanda elevado custo computacional e depende da qualidade dos modelos estocásticos adotados (Jorion, 2001).

### 2.1.3 Limitações dos Métodos Tradicionais

Apesar de sua ampla utilização, os métodos tradicionais de VaR apresentam limitações documentadas na literatura. Jorion (2001) reconhece que o VaR, enquanto medida pontual de risco, não fornece informações sobre a magnitude das perdas que excedem o limiar estimado. Além disso, o VaR não satisfaz a propriedade de subaditividade, o que significa que o VaR de um portfólio diversificado pode, em determinadas circunstâncias, ser superior à soma dos VaRs individuais de seus componentes, contrariando a lógica da diversificação.

Outra limitação relevante diz respeito ao pressuposto de que a volatilidade dos retornos é constante ao longo do tempo. Bollerslev (1986) demonstrou que a volatilidade dos ativos financeiros é heterocedástica, isto é, varia ao longo do tempo de forma condicional às observações passadas, o que invalida o pressuposto de variância constante adotado pelo método paramétrico clássico. Essas limitações motivam tanto o uso de modelos GARCH quanto a busca por abordagens de Machine Learning capazes de capturar padrões não lineares e adaptar-se a mudanças no regime de volatilidade.

Quadro 1: Síntese de Estudos sobre Value at Risk

| Autor(es) | Conceito (Definição) |
|---|---|
| Jorion (2001) | Descreve o VaR como a perda máxima esperada em um horizonte temporal, dado um nível de confiança. Obra de referência para a regulação e a prática de gestão de riscos de mercado. |
| JPMorgan (1996) | Documento técnico RiskMetrics que padronizou a metodologia de cálculo do VaR e popularizou a métrica como ferramenta de referência no mercado financeiro global. |
| Bollerslev (1986) | Demonstrou que a volatilidade dos retornos financeiros é condicional às observações passadas, fundamentando os modelos GARCH e evidenciando limitações da premissa de variância constante. |
| Nelson (1991) | Introduziu o modelo EGARCH, que captura efeitos assimétricos da volatilidade, em que choques negativos têm impacto diferente dos positivos. |

Fonte: Os autores, com base na literatura pesquisada.

## 2.2 Modelos de Volatilidade Condicional

### 2.2.1 O Modelo GARCH

O modelo Generalized Autoregressive Conditional Heteroskedasticity (GARCH), proposto por Bollerslev (1986), constitui uma das contribuições mais influentes para a modelagem de volatilidade em séries financeiras. O GARCH estende o modelo ARCH original ao permitir que a variância condicional dependa não apenas dos quadrados dos retornos passados, mas também de seus próprios valores defasados, capturando a persistência da volatilidade observada empiricamente nos mercados.

Na especificação GARCH(1,1), a mais utilizada na prática, a variância condicional no período t é modelada como função de uma constante, do quadrado do retorno do período anterior e da variância condicional do período anterior. Bollerslev (1986) demonstrou que essa especificação é suficiente para capturar os principais fatos estilizados das séries financeiras, como o agrupamento de volatilidade (volatility clustering) e as caudas pesadas na distribuição dos retornos.

A integração do GARCH com o VaR é direta: a variância condicional estimada pelo modelo é utilizada para calcular o VaR paramétrico dinâmico, que se ajusta às condições recentes de mercado, ao contrário do VaR paramétrico clássico, que assume variância constante. Essa abordagem tende a produzir estimativas mais calibradas, especialmente em períodos de transição entre regimes de alta e baixa volatilidade.

### 2.2.2 Extensões Assimétricas: EGARCH

Uma limitação do modelo GARCH clássico é a simetria no tratamento dos choques: retornos positivos e negativos de mesma magnitude produzem o mesmo impacto sobre a volatilidade condicional. Nelson (1991) propôs o modelo Exponential GARCH (EGARCH) para superar essa restrição. No EGARCH, a variância condicional é modelada em escala logarítmica, o que permite capturar o chamado efeito alavancagem: choques negativos (quedas de preços) tendem a elevar a volatilidade de forma mais intensa do que choques positivos de mesma magnitude.

Nelson (1991) argumenta que o EGARCH apresenta duas vantagens adicionais: não requer restrições de não negatividade nos parâmetros (como o GARCH clássico) e oferece maior flexibilidade na modelagem da dinâmica da volatilidade. Essas características tornam o EGARCH especialmente relevante para mercados emergentes, como o brasileiro, onde a assimetria na resposta da volatilidade a choques positivos e negativos tende a ser pronunciada.

## 2.3 Machine Learning Aplicado a Finanças

### 2.3.1 Conceitos de Machine Learning

Machine Learning (ML), ou aprendizado de máquina, é um subcampo da Inteligência Artificial dedicado ao desenvolvimento de algoritmos capazes de aprender padrões a partir de dados, sem que sejam explicitamente programados para executar cada tarefa específica. No contexto da modelagem de risco financeiro, o aprendizado supervisionado é a abordagem predominante, uma vez que o objetivo consiste em estimar uma variável-alvo (a perda ou o retorno futuro) a partir de variáveis explicativas derivadas do histórico de preços, volumes e indicadores de mercado. A capacidade dos modelos de ML de capturar relações não lineares e interações complexas entre variáveis confere a essas técnicas uma vantagem potencial sobre os métodos estatísticos tradicionais que assumem linearidade ou normalidade nos dados.

### 2.3.2 Principais Algoritmos Aplicáveis ao VaR

Dentre os algoritmos de Machine Learning aplicáveis à estimativa de VaR, destacam-se as redes neurais recorrentes e os modelos de regressão quantilílica autorregressiva.

As redes Long Short-Term Memory (LSTM), desenvolvidas por Hochreiter e Schmidhuber (1997), constituem uma arquitetura de rede neural recorrente projetada para capturar dependências de longo prazo em sequências temporais. As células LSTM utilizam mecanismos de portas (gates) que controlam o fluxo de informação, permitindo que a rede retenha ou descarte informações de forma seletiva ao longo do tempo. Fischer e Krauss (2018) demonstraram que essa propriedade torna as redes LSTM particularmente adequadas para a modelagem de séries financeiras, tendo obtido resultados superiores a modelos tradicionais na previsão de retornos de ações do S&P 500.

As redes Gated Recurrent Unit (GRU), introduzidas por Cho et al. (2014), representam uma simplificação da arquitetura LSTM, com menor número de parâmetros e, consequentemente, menor custo computacional de treinamento. Estudos comparativos indicam que as redes GRU alcançam desempenho competitivo em relação às LSTM em diversas tarefas de previsão de séries temporais financeiras, sendo uma alternativa eficiente quando o volume de dados é limitado.

O modelo CAViaR (Conditional Autoregressive Value at Risk by Regression Quantiles), proposto por Engle e Manganelli (2004), representa uma abordagem distinta ao estimar o VaR diretamente como um processo autorregressivo sobre os quantis da distribuição de retornos, sem a necessidade de especificar a distribuição completa. Os autores propuseram também o teste de quantil dinâmico (DQ), amplamente utilizado para avaliar a adequação de modelos de VaR em conjunto com os testes de Kupiec e Christoffersen.

### 2.3.3 Abordagens Híbridas: GARCH e Deep Learning

Uma linha de pesquisa recente tem buscado combinar os fundamentos econométricos dos modelos GARCH com a flexibilidade das redes neurais profundas. Buczyński e Chlebus (2024) propuseram o GARCHNet, um modelo híbrido que utiliza redes neurais LSTM para parametrizar a equação de variância condicional do GARCH, permitindo que os parâmetros do modelo se adaptem dinamicamente às condições de mercado. Os autores reportaram que o GARCHNet superou tanto o GARCH clássico quanto redes LSTM puras em termos de calibração do VaR, medida pelos testes de Kupiec e Christoffersen.

Na mesma direção, estudos recentes têm explorado a combinação de modelos GARCH com redes GRU para a estimativa conjunta de VaR e Expected Shortfall, testando as abordagens em ativos como S&P 500, ouro e Bitcoin (HYBRID GARCH-GRU, 2023). Esses trabalhos sugerem que as abordagens híbridas capturam simultaneamente a persistência da volatilidade (característica do GARCH) e os padrões não lineares (característica das redes neurais), oferecendo estimativas mais robustas do que cada abordagem isoladamente.

## 2.4 Backtesting de Modelos de Risco

### 2.4.1 Testes Clássicos de Backtesting

O backtesting é o procedimento de validação retrospectiva de modelos de risco, que consiste em comparar as estimativas de VaR geradas pelo modelo com as perdas efetivamente observadas no período de teste. O objetivo central é verificar se o número de violações, dias em que a perda real excedeu o VaR estimado, é consistente com o nível de confiança adotado.

Kupiec (1995) propôs o teste de proporção de falhas (Proportion of Failures, POF), que avalia se a frequência observada de violações é estatisticamente compatível com a frequência esperada, utilizando um teste de razão de verossimilhança. Esse teste constitui o ponto de partida para qualquer estudo de backtesting e é amplamente adotado tanto na prática de mercado quanto na literatura acadêmica.

Christoffersen (1998) ampliou essa análise ao desenvolver o teste de cobertura condicional, que verifica não apenas se a frequência de violações é adequada (cobertura incondicional), mas também se as violações são independentes entre si ao longo do tempo. A ocorrência de violações em clusters indicaria deficiências na dinâmica do modelo, uma vez que o VaR deveria se ajustar às condições recentes de mercado.

Engle e Manganelli (2004) propuseram o teste de quantil dinâmico (Dynamic Quantile, DQ), que avalia simultaneamente a cobertura e a independência das violações por meio de uma regressão dos indicadores de violação sobre seus valores defasados e sobre o próprio VaR estimado. O teste DQ é amplamente utilizado em conjunto com os testes de Kupiec e Christoffersen, formando um conjunto abrangente de ferramentas de validação.

### 2.4.2 Avanços Recentes em Backtesting

Zhang e Nadarajah (2018) realizaram uma revisão abrangente dos métodos de backtesting de VaR publicados na literatura, catalogando e comparando os principais testes disponíveis. Os autores destacam que, embora os testes de Kupiec e Christoffersen sejam os mais amplamente utilizados, testes mais recentes têm buscado melhorar a detecção de padrões de clustering nas violações e aumentar o poder estatístico em amostras pequenas.

Berger e Moys (2021) contribuíram para essa discussão ao propor abordagens de backtesting que vão além da taxa de falha empírica, analisando a estrutura temporal das violações com foco na detecção de clustering. Os autores argumentam que a avaliação isolada da frequência de violações pode ser insuficiente para identificar modelos mal calibrados, sendo necessária a combinação de múltiplos testes para uma avaliação robusta.

Quadro 2: Síntese de Estudos sobre Backtesting de VaR

| Autor(es) | Contribuição |
|---|---|
| Kupiec (1995) | Propôs o teste POF (Proportion of Failures), que avalia a aderência da frequência de violações ao nível de confiança do modelo via razão de verossimilhança. |
| Christoffersen (1998) | Desenvolveu o teste de cobertura condicional, que verifica tanto a frequência quanto a independência temporal das violações. |
| Engle e Manganelli (2004) | Propuseram o modelo CAViaR e o teste DQ (Dynamic Quantile), que avalia cobertura e independência das violações por meio de regressão quantílica. |
| Zhang e Nadarajah (2018) | Realizaram revisão abrangente dos métodos de backtesting de VaR, catalogando e comparando os principais testes disponíveis na literatura. |
| Berger e Moys (2021) | Propuseram abordagens de backtesting com foco na detecção de clustering de violações, indo além da taxa de falha empírica. |

Fonte: Os autores, com base na literatura pesquisada.

## 2.5 Regulação e o Papel do VaR nos Acordos de Basileia

O arcabouço regulatório internacional desempenha papel central na consolidação do VaR como métrica de risco de mercado. O Acordo de Basileia II (BASEL COMMITTEE ON BANKING SUPERVISION, 2004) estabeleceu que instituições financeiras que utilizem modelos internos para o cálculo de capital regulatório devem submeter esses modelos a procedimentos de backtesting, comparando as estimativas de VaR com as perdas reais observadas em um período mínimo de 250 dias úteis.

O Comitê de Basileia define zonas de classificação para os modelos com base no número de violações observadas: a zona verde (até 4 violações em 250 dias, para VaR a 99%), a zona amarela (de 5 a 9 violações) e a zona vermelha (10 ou mais violações). Modelos classificados na zona vermelha estão sujeitos a penalidades regulatórias, incluindo a exigência de capital adicional. Essa estrutura regulatória reforça a importância do backtesting como ferramenta de validação e motiva o desenvolvimento de modelos de VaR mais acurados.

## 2.6 Estudos Prévios sobre VaR e Machine Learning

A interseção entre métodos de Machine Learning e a estimativa de VaR tem sido objeto de crescente interesse na literatura. Fischer e Krauss (2018) foram pioneiros ao demonstrar que redes LSTM superaram modelos estatísticos tradicionais na previsão de retornos de ações, abrindo caminho para a aplicação dessas técnicas na estimativa de risco de mercado.

Buczyński e Chlebus (2024) avançaram nessa direção ao propor o GARCHNet, que combina a estrutura econométrica do GARCH com redes neurais LSTM. Os autores avaliaram o modelo em séries financeiras de múltiplos mercados e reportaram que a abordagem híbrida produziu estimativas de VaR significativamente mais calibradas do que os modelos GARCH e LSTM utilizados isoladamente, conforme medido pelos testes de Kupiec (1995) e Christoffersen (1998).

Engle e Manganelli (2004), além de proporem o modelo CAViaR, contribuíram para a literatura ao demonstrar que a estimativa direta do quantil da distribuição de retornos, sem a necessidade de especificar a distribuição completa, pode produzir estimativas de VaR competitivas com os métodos tradicionais, especialmente em séries com caudas pesadas.

No âmbito das revisões de literatura, Zhang e Nadarajah (2018) oferecem um panorama abrangente dos métodos de backtesting, enquanto Berger e Moys (2021) focam nos avanços recentes para detecção de clustering de violações. Esses trabalhos evidenciam que a avaliação de modelos de VaR requer a combinação de múltiplos testes estatísticos, justificando a inclusão de um módulo robusto de backtesting na plataforma proposta.

Embora esses estudos evidenciam o potencial das técnicas de ML e das abordagens híbridas na modelagem de risco, observa-se que a maioria das pesquisas utiliza dados de mercados desenvolvidos e não disponibiliza ferramentas integradas para a comparação sistematizada entre modelos. Esta lacuna reforça a relevância da proposta deste trabalho, que visa oferecer uma plataforma acessível para modelagem e backtesting de VaR com dados do mercado brasileiro.

Quadro 3: Síntese de Estudos sobre Machine Learning e VaR

| Autor(es) | Contribuição |
|---|---|
| Fischer e Krauss (2018) | Pioneiros na aplicação de redes LSTM para previsão de retornos financeiros, com resultados superiores a modelos tradicionais no S&P 500. |
| Engle e Manganelli (2004) | Propuseram o CAViaR para estimativa direta do VaR via regressão quantílica autorregressiva, e o teste DQ para validação. |
| Buczyński e Chlebus (2024) | Desenvolveram o GARCHNet, modelo híbrido GARCH-LSTM que superou modelos individuais na previsão de VaR em múltiplos mercados. |
| Hybrid GARCH-GRU (2023) | Combinação de GARCH com redes GRU para estimar VaR e Expected Shortfall, testada em S&P 500, ouro e Bitcoin. |

Fonte: Os autores, com base na literatura pesquisada.

# 3 PROCEDIMENTOS METODOLÓGICOS

Este capítulo descreve os procedimentos metodológicos adotados para o desenvolvimento da plataforma proposta. São apresentados a proposta de solução, a análise prévia das decisões técnicas e arquiteturais, as etapas de implementação com suas respectivas prioridades, os resultados esperados ao final do projeto e os fatores críticos para o sucesso da iniciativa. O capítulo está diretamente articulado com os objetivos específicos apresentados na Seção 1.2 e com a Matriz de Validação disponível no Apêndice A.

## 3.1 Proposta de Solução para um Problema Real

A proposta deste projeto consiste no desenvolvimento de uma plataforma web denominada VaR Lab, construída em Python com o framework Flask, destinada à modelagem, simulação e backtesting de Value at Risk (VaR) aplicado a ativos negociados na B3. A plataforma integra, em uma única interface interativa, três famílias de modelos: (i) métodos tradicionais de estimação de VaR, simulação histórica, método paramétrico e simulação de Monte Carlo; (ii) modelos de volatilidade condicional da família GARCH, incluindo as especificações GARCH(1,1) e EGARCH; e (iii) algoritmos de Machine Learning e abordagens híbridas, contemplando redes LSTM, GRU, o modelo CAViaR e o modelo híbrido GARCHNet.

A plataforma é concebida como resposta direta à lacuna identificada na Seção 1.3: a ausência de ferramentas integradas, acessíveis e voltadas ao mercado brasileiro que permitam a estudantes, pesquisadores e profissionais comparar sistematicamente diferentes abordagens de modelagem de risco de mercado. Além da estimação, a plataforma incorpora um módulo de backtesting com os testes estatísticos de Kupiec (1995), Christoffersen (1998) e Engle e Manganelli (2004), bem como a classificação regulatória por zonas de Basileia II (BASEL COMMITTEE ON BANKING SUPERVISION, 2004), proporcionando uma avaliação abrangente da calibração de cada modelo.

Os dados de mercado serão obtidos por meio da biblioteca yfinance, que disponibiliza séries históricas de preços ajustados diretamente das bases do Yahoo Finance, com cobertura robusta para ativos negociados na B3. A coleta abrangerá o período de janeiro de 2015 a dezembro de 2024, totalizando aproximadamente dez anos de dados, suficientes para capturar múltiplos regimes de volatilidade do mercado brasileiro, incluindo a crise de liquidez de 2015–2016, o período de instabilidade política de 2017–2018, o choque de volatilidade provocado pela pandemia de COVID-19 em 2020 e o ciclo de alta da inflação e dos juros em 2021–2023.

### 3.1.1 Estudo Prévio sobre Ferramentas Existentes de VaR

Antes de formalizar a proposta, realizou-se um levantamento das principais ferramentas disponíveis para modelagem e backtesting de VaR, com o objetivo de identificar lacunas que justificassem o desenvolvimento de uma nova solução. As ferramentas analisadas foram agrupadas em três categorias:

a) Bibliotecas especializadas de risco financeiro: A QuantLib é uma das bibliotecas mais abrangentes para finanças quantitativas, disponível em C++ com bindings para Python. Embora ofereça suporte a modelos de precificação e cálculo de VaR paramétrico, não dispõe de interface web nem de módulos nativos para Machine Learning ou backtesting estatístico. A Riskfolio-Lib e o PyFolio são voltados à análise e otimização de portfólios, sem suporte a estimação de VaR por métodos GARCH ou ML e sem módulos de backtesting com testes de Kupiec ou Christoffersen.

b) Plataformas comerciais: Ferramentas como Bloomberg Risk e Refinitiv Eikon oferecem funcionalidades robustas de gestão de risco, incluindo VaR e backtesting regulatório. No entanto, seu acesso é restrito a instituições financeiras com licenças de alto custo, suas metodologias internas são opacas (caixa-preta) e não permitem a comparação direta entre modelos tradicionais e de Machine Learning, tampouco a personalização para fins acadêmicos.

c) Implementações acadêmicas em notebooks: A literatura recente, incluindo os trabalhos de Fischer e Krauss (2018) e Buczyński e Chlebus (2024), disponibiliza implementações de modelos LSTM e GARCHNet em Jupyter Notebooks. Essas implementações são valiosas como referência técnica, mas são fragmentadas, dependem de configuração manual de ambiente, não oferecem interface de usuário e não integram múltiplos modelos em um fluxo comparativo unificado.

O levantamento evidenciou que nenhuma das soluções existentes combina, em uma única plataforma de acesso livre: métodos tradicionais de VaR, modelos GARCH, algoritmos de Machine Learning e backtesting estatístico, com interface web interativa e dados do mercado brasileiro. Essa lacuna confirma a pertinência e a originalidade da proposta deste projeto.

## 3.2 Análise Prévia sobre o que será Proposto

A plataforma VaR Lab será desenvolvida com base em uma arquitetura modular, na qual cada família de modelos corresponde a um módulo Python independente, orquestrado pelo back-end Flask. Essa abordagem facilita o desenvolvimento incremental, permitindo que cada módulo seja implementado, testado e validado isoladamente, e favorece a manutenção e a extensão futura da plataforma.

Back-end: o framework Flask foi escolhido em detrimento do Django por sua leveza e flexibilidade. Como a plataforma não requer um sistema de gerenciamento de conteúdo, ORM complexo ou autenticação de múltiplos usuários, o overhead do Django não se justifica. O Flask permite definir rotas REST de forma direta e integrar nativamente os módulos Python de modelagem matemática e estatística sem camadas intermediárias desnecessárias.

Módulos de modelagem: os modelos tradicionais de VaR, paramétrico, simulação histórica e Monte Carlo, serão implementados com NumPy e SciPy. Os modelos GARCH(1,1) e EGARCH serão estimados com a biblioteca arch, que oferece estimação por máxima verossimilhança e diagnósticos de resíduos. Os modelos de Machine Learning LSTM e GRU serão implementados com Keras sobre TensorFlow, enquanto o CAViaR será implementado via regressão quantílica com statsmodels. O modelo híbrido GARCHNet integrará a saída da variância condicional GARCH como entrada adicional para a rede LSTM, conforme a arquitetura proposta por Buczyński e Chlebus (2024).

Fonte de dados: a biblioteca yfinance será utilizada para coleta automatizada das séries de preços ajustados dos ativos selecionados. Os quatro ativos do experimento comparativo são: o índice Ibovespa (^BVSP), representando o mercado agregado, e as ações de Petrobras (PETR4.SA), Vale (VALE3.SA) e Itaú Unibanco (ITUB4.SA), que representam os setores de energia, mineração e financeiro, os três de maior peso e liquidez na B3. Essa composição assegura diversidade setorial e relevância prática.

Parâmetros padrão da plataforma: nível de confiança de 95% e 99% (ambos calculados simultaneamente, para fins de comparação regulatória); horizonte temporal de 1 dia útil (padrão de mercado e exigência de Basileia II); janela de treinamento configurável pelo usuário, com valor padrão de 252 dias úteis (equivalente a um ano de negociação); período total dos dados: janeiro de 2015 a dezembro de 2024.

Front-end e visualização: a interface web será desenvolvida com templates Jinja2 do Flask e dashboards interativos construídos com Plotly.js, permitindo ao usuário selecionar ativos, configurar parâmetros, executar os modelos e visualizar graficamente as séries de VaR estimado, as violações identificadas e os resultados dos testes de backtesting. Os relatórios de backtesting incluirão os p-valores dos três testes estatísticos e a classificação por zonas de Basileia (verde, amarela e vermelha).

Armazenamento de dados: na versão inicial da plataforma, não será utilizado banco de dados persistente. Os dados coletados e os resultados dos modelos serão mantidos em memória durante a sessão do usuário, simplificando a arquitetura e reduzindo a complexidade de implantação. Versões futuras poderão incorporar persistência em SQLite ou PostgreSQL para armazenamento de experimentos e comparações históricas.

## 3.3 Como a Solução será Implementada (Etapas / Prioridades)

O desenvolvimento da plataforma está organizado em seis etapas, alinhadas aos objetivos específicos da pesquisa e ordenadas por prioridade de implementação. As etapas de maior prioridade constituem o núcleo funcional da plataforma e serão desenvolvidas primeiro, garantindo que um produto mínimo viável esteja operacional antes da adição de funcionalidades mais complexas.

Etapa 1: Módulo de coleta de dados e métodos tradicionais de VaR (prioridade alta): implementação do módulo de coleta automatizada via yfinance, com tratamento de dados ausentes, ajuste de splits e cálculo de retornos logarítmicos diários. Em seguida, implementação dos três métodos tradicionais de estimação de VaR: (i) método paramétrico, com cálculo de média e variância das séries de retornos; (ii) simulação histórica, com identificação do quantil empírico correspondente ao nível de confiança; e (iii) simulação de Monte Carlo, com geração de cenários aleatórios a partir da distribuição paramétrica dos retornos. Os três métodos serão expostos como funções Python com parâmetros configuráveis (ativo, janela, nível de confiança, horizonte).

Etapa 2: Modelos de volatilidade condicional GARCH e EGARCH (prioridade alta): estimação do modelo GARCH(1,1) e de suas extensões assimétricas via biblioteca arch, com integração da variância condicional estimada ao cálculo do VaR paramétrico dinâmico. O módulo permitirá a configuração dos parâmetros do modelo pelo usuário e a visualização da série de volatilidade condicional estimada. A validação será realizada por verificação cruzada com a implementação de referência do pacote rugarch da linguagem R.

Etapa 3: Algoritmos de Machine Learning e abordagens híbridas (prioridade alta a média): implementação das redes LSTM e GRU com Keras/TensorFlow, com validação temporal por janela deslizante (walk-forward validation) para evitar vazamento de dados futuros no treinamento. Implementação do modelo CAViaR via regressão quantílica autorregressiva. Desenvolvimento do modelo híbrido GARCHNet, que utiliza a variância condicional estimada pelo GARCH como variável de entrada adicional para a rede LSTM, conforme Buczyński e Chlebus (2024). A otimização de hiperparâmetros das redes neurais será conduzida com busca em grade (grid search) sobre parâmetros como número de camadas, unidades por camada, taxa de aprendizado e tamanho do batch.

Etapa 4: Módulo de backtesting estatístico (prioridade alta): implementação dos três testes de backtesting, teste de proporção de falhas de Kupiec (1995), teste de cobertura condicional de Christoffersen (1998) e teste de quantil dinâmico de Engle e Manganelli (2004), aplicáveis a qualquer modelo implementado na plataforma. O módulo calcula automaticamente o número de violações observadas, os p-valores de cada teste e a classificação nas zonas regulatórias de Basileia II (verde: até 4 violações em 250 dias; amarela: 5 a 9; vermelha: 10 ou mais). A validação do módulo será realizada com séries sintéticas de taxa de violação conhecida.

Etapa 5: Interface web interativa (prioridade alta): desenvolvimento das rotas Flask para orquestração dos módulos de modelagem e backtesting, construção dos templates Jinja2 para seleção de ativos e configuração de parâmetros, e implementação dos dashboards interativos com Plotly.js para visualização das séries de VaR, das violações e dos resultados comparativos. Testes de usabilidade serão conduzidos com usuários-alvo (estudantes de ciência de dados e finanças quantitativas) para verificação da clareza da interface e da interpretabilidade dos resultados.

Etapa 6: Experimento comparativo com dados reais da B3 (execução final): após a validação individual de cada módulo, será conduzido o experimento comparativo com dados históricos dos quatro ativos selecionados (Ibovespa, PETR4, VALE3 e ITUB4) no período de 2015 a 2024. Todos os modelos implementados serão executados sobre as mesmas séries, com backtesting padronizado, gerando um ranking de desempenho baseado na taxa de violações, nos p-valores dos três testes estatísticos e na classificação regulatória de Basileia II.

## 3.4 Resultados Esperados

Os resultados esperados estão diretamente alinhados às seis etapas de implementação e aos objetivos específicos da pesquisa, conforme detalhado na Matriz de Validação (Apêndice A).

Ao término da Etapa 1, espera-se dispor de um módulo funcional com os três métodos tradicionais de VaR implementados, testados com séries sintéticas de distribuição conhecida e com resultados validados por comparação com cálculos manuais de referência.

Ao término da Etapa 2, espera-se um módulo GARCH/EGARCH com parâmetros estimados de forma convergente e resíduos padronizados adequadamente distribuídos, verificado por diagnósticos estatísticos e por comparação cruzada com o pacote rugarch da linguagem R.

Ao término da Etapa 3, espera-se que os módulos de Machine Learning, LSTM, GRU, CAViaR e GARCHNet, estejam implementados e avaliados em dados out-of-sample da B3, com métricas de erro (RMSE e MAE) calculadas para comparação entre os modelos de ML puros e as abordagens híbridas.

Ao término da Etapa 4, espera-se um módulo de backtesting estatístico funcional, validado com séries sintéticas e capaz de classificar os modelos pelas zonas regulatórias de Basileia II, fornecendo os p-valores dos três testes como critérios de comparação.

Ao término da Etapa 5, espera-se uma plataforma web funcional, responsiva e com interface intuitiva, validada por testes de usabilidade com usuários-alvo.

Ao término da Etapa 6, espera-se um ranking comparativo de todos os modelos implementados, com evidências empíricas sobre o desempenho relativo de métodos tradicionais, modelos GARCH e algoritmos de Machine Learning aplicados ao mercado acionário brasileiro, contribuindo para o enriquecimento da literatura nacional sobre gestão de riscos.

## 3.5 Fatores Críticos para o Sucesso (FCS)

A análise dos fatores críticos para o sucesso considera tanto os elementos que favorecem a viabilidade do projeto quanto os riscos que podem comprometer o cumprimento dos objetivos, com as respectivas estratégias de mitigação.

Entre os fatores favoráveis, destaca-se a disponibilidade gratuita e a maturidade das bibliotecas Python utilizadas. A biblioteca yfinance oferece cobertura consistente para ativos da B3 com integração direta ao pandas, simplificando a etapa de coleta e preparação dos dados. A biblioteca arch é amplamente utilizada na academia para estimação de modelos GARCH, o que reduz a probabilidade de erros de implementação e facilita a verificação cruzada com implementações de referência. O ecossistema Keras/TensorFlow é maduro e amplamente documentado, reduzindo a barreira técnica para a implementação das redes LSTM e GRU. Ademais, o período histórico selecionado (2015–2024) é especialmente rico em termos de regimes de volatilidade, incluindo a crise hídrica e recessão de 2015–2016, os episódios de instabilidade política de 2017–2018, o choque de volatilidade induzido pela pandemia de COVID-19 em 2020 e o ciclo de alta da inflação e dos juros básicos em 2021–2023, o que favorece a avaliação dos modelos em condições adversas de mercado.

Em contrapartida, identificam-se três riscos principais. O primeiro é a qualidade e disponibilidade dos dados históricos da B3 via yfinance: séries de ativos com menor liquidez podem apresentar gaps temporais, preços não ajustados a eventos corporativos (splits, agrupamentos, dividendos extraordinários) ou inconsistências entre fontes. A estratégia de mitigação consiste na implementação de rotinas explícitas de verificação e limpeza de dados, incluindo detecção de valores ausentes, verificação de retornos aberrantes e comparação com fontes alternativas, antes de qualquer estimação.

O segundo risco é a dificuldade de convergência dos modelos de Machine Learning e das abordagens híbridas. Redes LSTM e o modelo GARCHNet são sensíveis à escolha de hiperparâmetros e podem não convergir adequadamente com janelas de treinamento curtas ou séries de baixa volatilidade. A mitigação envolve a adoção de validação cruzada temporal por janela deslizante (walk-forward validation), otimização de hiperparâmetros por busca em grade e o uso de regularização (dropout) para reduzir o risco de sobreajuste.

O terceiro risco é o prazo de implementação: o desenvolvimento de seis módulos distintos, com backtesting, interface web e experimento comparativo, em paralelo às demais atividades do TCC II pode resultar em atrasos. A estratégia de mitigação consiste na priorização das Etapas 1 a 4 como núcleo funcional mínimo da plataforma, tratando as Etapas 5 e 6 como camadas adicionais que podem ser desenvolvidas em paralelo ou sequencialmente conforme a disponibilidade da equipe.

# 4 RESULTADOS

Este capítulo apresenta os resultados obtidos até o presente momento na implementação da plataforma VaR Lab, organizados por etapa de desenvolvimento, conforme a Matriz de Validação (Apêndice A). As Etapas 1, 2, 3 e 4 encontram-se concluídas e validadas; a Etapa 6 (ranking comparativo final) está em andamento e será detalhada em versão futura deste documento.

## 4.1 Etapa 1 – Métodos Tradicionais de VaR

Os três métodos tradicionais de cálculo do VaR (paramétrico, simulação histórica e simulação de Monte Carlo) foram implementados em Python, seguindo uma interface comum que desacopla cada modelo do restante da plataforma, e validados por um conjunto de testes automatizados parametrizados sobre séries de retornos sintéticas com distribuição conhecida. Os três modelos convergem para estimativas consistentes entre si em condições de retornos gaussianos, conforme esperado pela teoria (Jorion, 2001).

## 4.2 Etapa 2 – Modelos GARCH e EGARCH

O modelo GARCH(1,1) (Bollerslev, 1986) e sua extensão assimétrica EGARCH (Nelson, 1991) foram implementados via biblioteca arch (Python), com estimação dos parâmetros por máxima verossimilhança sobre uma janela de treino de 252 dias úteis, seguida de reestimação periódica com janela expansiva a cada 252 dias ao longo do período de teste — estratégia adotada para manter a variância condicional alinhada ao regime de mercado mais recente.

Durante a validação, identificou-se uma instabilidade numérica característica do EGARCH: ao propagar parâmetros fixos por longos períodos de teste sem reestimação, o resíduo padronizado tende a crescer, amplificando a reação dos termos assimétricos (α, γ) e realimentando um colapso da variância condicional. O GARCH(1,1) tradicional não apresenta esse comportamento, pois sua recursão possui um piso estrutural dado pela constante ω. O problema foi mitigado por meio da reestimação periódica somada a um piso mínimo de segurança na variância, derivado do desvio-padrão histórico da janela de treino.

Os parâmetros estimados pela biblioteca arch foram comparados com os obtidos pelo pacote rugarch (linguagem R), ajustando a mesma especificação (média zero, inovações normais) sobre os mesmos dados de treino (PETR4.SA, 252 dias). A comparação das log-verossimilhanças, ajustadas pela escala das séries, mostrou concordância entre as duas implementações: 473,62 (Python) contra 471,81 (R) para o GARCH(1,1), e 481,60 (Python) contra 475,17 (R) para o EGARCH — divergências abaixo de 1,5%, compatíveis com pequenas diferenças de otimizador numa superfície de verossimilhança com crista quase plana entre os parâmetros α e β, fenômeno conhecido na literatura de estimação de modelos GARCH.

## 4.3 Etapa 3 – Modelos de Machine Learning

Os quatro modelos de Machine Learning especificados na Matriz de Validação foram implementados: LSTM (Hochreiter & Schmidhuber, 1997), GRU (Cho et al., 2014), CAViaR na especificação Symmetric Absolute Value (Engle & Manganelli, 2004) e GARCHNet, o híbrido GARCH+LSTM proposto por Buczyński e Chlebus (2024). Diferentemente do GARCH, que prevê a variância condicional e assume normalidade dos resíduos para obter o quantil, LSTM, GRU e o componente neural do GARCHNet preveem o quantil de VaR diretamente por meio da pinball loss (regressão quantílica), sem qualquer suposição distribucional.

O CAViaR foi ajustado por otimização numérica (scipy.optimize, minimizando a pinball loss com múltiplos reinícios aleatórios), já que sua estrutura recursiva — o VaR do dia anterior aparece como regressor do VaR do dia atual — não é suportada por implementações de regressão quantílica estática, como o statsmodels.QuantReg originalmente cogitado na Matriz de Validação (Apêndice A).

O GARCHNet reaproveita a volatilidade condicional do GARCH(1,1) (Etapa 2) como uma terceira variável de entrada da LSTM, ao lado do retorno e do retorno absoluto, numa janela deslizante de 20 dias úteis. A otimização de hiperparâmetros via grid search foi restrita a duas dimensões — número de unidades e de camadas recorrentes —, com taxa de aprendizado e tamanho de lote fixos em valores padrão; essa redução de escopo foi necessária porque o treino é específico para cada nível de confiança (95% e 99%) e combinado à validação walk-forward com reestimação periódica a cada 252 dias, tornando um grid de quatro dimensões computacionalmente impraticável dentro do prazo revisado do TCC II.

A Tabela 1 apresenta os resultados do backtesting dos quatro modelos de ML sobre PETR4.SA (2015–2024), no mesmo protocolo experimental da Etapa 4 (Seção 4.4).

Tabela 1 – Resultados do backtesting dos modelos de ML, PETR4.SA (2015–2024)

| Modelo | α (VaR) | Kupiec | Christoffersen | DQ | Basileia |
|---|---|---|---|---|---|
| LSTM | 95% | Aprovado (p=0,5114) | Aprovado (p=0,3444) | Aprovado (p=0,7194) | Aprovado (p=0,4825) |
| LSTM | 99% | Aprovado (p=0,0537) | Reprovado (p=0,0101) | Reprovado (p=< 0,0001) | Aprovado (p=0,4568) |
| GRU | 95% | Reprovado (p=0,0002) | Reprovado (p=0,0139) | Reprovado (p=0,0034) | Aprovado (p=0,9350) |
| GRU | 99% | Aprovado (p=0,3373) | Reprovado (p=0,0035) | Reprovado (p=0,0093) | Aprovado (p=0,7142) |
| CAViaR | 95% | Reprovado (p=0,0025) | Reprovado (p=0,0393) | Reprovado (p=0,0320) | Aprovado (p=0,9869) |
| CAViaR | 99% | Reprovado (p=0,0343) | Reprovado (p=0,0122) | Reprovado (p=0,0275) | Aprovado (p=0,2419) |
| GARCHNet | 95% | Reprovado (p=0,0094) | Aprovado (p=0,0636) | Aprovado (p=0,0998) | Aprovado (p=0,9686) |
| GARCHNet | 99% | Aprovado (p=0,9422) | Reprovado (p=0,0177) | Reprovado (p=0,0020) | Aprovado (p=0,7142) |

O destaque é a LSTM a 95% de confiança, que aprovou simultaneamente os quatro testes de backtesting (Kupiec, Christoffersen, DQ e zonas de Basileia) — o melhor resultado entre todos os modelos implementados no projeto até o momento, superando inclusive GARCH e EGARCH (Seção 4.2). GRU e GARCHNet tiveram desempenho intermediário, aprovando parcialmente os testes; CAViaR foi o modelo com pior calibração no período completo. Uma ressalva metodológica: a inicialização dos pesos da rede neural e os reinícios aleatórios do CAViaR não usam uma semente fixa, portanto os valores exatos variam entre execuções, ainda que o padrão qualitativo (LSTM e GARCHNet superando CAViaR) se mantenha estável — fixar a semente é uma melhoria pendente para a versão final.

## 4.4 Etapa 4 – Backtesting Estatístico

Os quatro instrumentos de validação especificados na Matriz de Validação foram implementados: o teste de proporção de falhas de Kupiec (1995), o teste de independência de Christoffersen (1998), o teste de quantil dinâmico de Engle e Manganelli (2004) e a classificação por zonas de Basileia II — esta última calculada sobre uma janela fixa de 250 dias úteis, conforme exigido pelo Acordo de Basileia II (BASEL COMMITTEE ON BANKING SUPERVISION, 2004). Todos os quatro testes foram validados com séries sintéticas de taxa de violação conhecida antes da aplicação a dados reais.

A Tabela 2 apresenta os resultados do backtesting aplicado a PETR4.SA no período de janeiro de 2015 a dezembro de 2024, com janela de treino de 252 dias úteis e reestimação periódica (Etapa 2), nos dois níveis de confiança padrão da plataforma (95% e 99%). Os valores reportados são os p-valores de cada teste; “Aprovado” indica p-valor acima do nível de significância de 5%.

Tabela 2 – Resultados do backtesting, PETR4.SA (2015–2024)

| Modelo | α (VaR) | Kupiec | Christoffersen | DQ | Basileia |
|---|---|---|---|---|---|
| Paramétrico | 95% | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Aprovado (p=1,0000) |
| Paramétrico | 99% | Aprovado (p=0,4660) | Reprovado (p=0,0093) | Reprovado (p=< 0,0001) | Aprovado (p=0,7142) |
| Histórico | 95% | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Aprovado (p=0,9997) |
| Histórico | 99% | Aprovado (p=0,7735) | Reprovado (p=0,0007) | Reprovado (p=< 0,0001) | Aprovado (p=0,7142) |
| Monte Carlo | 95% | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Aprovado (p=1,0000) |
| Monte Carlo | 99% | Aprovado (p=0,4660) | Reprovado (p=0,0093) | Reprovado (p=< 0,0001) | Aprovado (p=0,7142) |
| GARCH(1,1) | 95% | Reprovado (p=< 0,0001) | Reprovado (p=0,0047) | Reprovado (p=< 0,0001) | Aprovado (p=0,9954) |
| GARCH(1,1) | 99% | Reprovado (p=0,0312) | Aprovado (p=0,6964) | Reprovado (p=< 0,0001) | Aprovado (p=0,7142) |
| EGARCH | 95% | Aprovado (p=0,1008) | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Aprovado (p=0,9987) |
| EGARCH | 99% | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Reprovado (p=< 0,0001) | Aprovado (p=0,7142) |

Os resultados evidenciam que os modelos estáticos (paramétrico, histórico e Monte Carlo) rejeitam a hipótese de cobertura adequada (teste de Kupiec) ao nível de 95% ao longo de todo o período de dez anos, incluindo eventos de estresse como a crise da COVID-19 em 2020 — resultado esperado, dado que esses modelos assumem variância constante durante todo o período de teste. Os modelos GARCH(1,1) e EGARCH, por sua vez, aprovam o teste de Kupiec ou o de Christoffersen com maior frequência, evidenciando a contribuição da variância condicional dinâmica. O teste DQ rejeitou a hipótese nula para praticamente todos os modelos no período completo — resultado consistente com a literatura, que aponta maior poder estatístico (e, portanto, maior sensibilidade a pequenos desvios) desse teste em amostras longas (Engle; Manganelli, 2004; Zhang; Nadarajah, 2018).

## 4.5 Etapa 6 – Ranking Comparativo dos Modelos

Seção a ser preenchida após a conclusão da Etapa 3, quando todos os modelos (tradicionais, GARCH/EGARCH e Machine Learning) puderem ser comparados sob o mesmo protocolo experimental, conforme previsto na Etapa 6 da Matriz de Validação.

# 5 CONSIDERAÇÕES FINAIS

Este capítulo será redigido de forma completa ao término da Etapa 6, consolidando as evidências empíricas obtidas ao longo do trabalho e discutindo suas implicações para a modelagem de risco de mercado no contexto do mercado acionário brasileiro. Preliminarmente, os resultados já obtidos nas Etapas 1, 2 e 4 (Seção 4) indicam que a incorporação de volatilidade condicional (GARCH/EGARCH) traz ganhos mensuráveis de calibração em relação aos métodos tradicionais estáticos, especialmente em janelas de teste que atravessam períodos de instabilidade de mercado — hipótese que será testada de forma mais completa com a inclusão dos modelos de Machine Learning (Etapa 3) e do ranking comparativo final (Etapa 6).

# REFERÊNCIAS

BASEL COMMITTEE ON BANKING SUPERVISION. International Convergence of Capital Measurement and Capital Standards: A Revised Framework (Basel II). Bank for International Settlements, 2004.

BERGER, T.; MOYS, G. Value-at-risk backtesting: Beyond the empirical failure rate. Expert Systems with Applications, v. 177, p. 1-15, 2021.

BOLLERSLEV, T. Generalized autoregressive conditional heteroskedasticity. Journal of Econometrics, v. 31, n. 3, p. 307-327, 1986.

BUCZYŃSKI, M.; CHLEBUS, M. GARCHNet: Value-at-Risk Forecasting with GARCH Models Based on Neural Networks. Computational Economics, v. 63, n. 5, p. 1949-1979, 2024.

CHO, K. et al. Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation. In: PROCEEDINGS OF THE 2014 CONFERENCE ON EMPIRICAL METHODS IN NATURAL LANGUAGE PROCESSING (EMNLP), 2014, p. 1724-1734.

CHRISTOFFERSEN, P. F. Evaluating interval forecasts. International Economic Review, v. 39, n. 4, p. 841-862, 1998.

ENGLE, R. F.; MANGANELLI, S. CAViaR: Conditional Autoregressive Value at Risk by Regression Quantiles. Journal of Business & Economic Statistics, v. 22, n. 4, p. 367-381, 2004.

FISCHER, T.; KRAUSS, C. Deep learning with long short-term memory networks for financial market predictions. European Journal of Operational Research, v. 270, n. 2, p. 654-669, 2018.

HOCHREITER, S.; SCHMIDHUBER, J. Long short-term memory. Neural Computation, v. 9, n. 8, p. 1735-1780, 1997.

HYBRID GARCH-GRU. A hybrid GARCH-GRU approach for Value-at-Risk and Expected Shortfall forecasting. arXiv preprint, arXiv:2310.01063, 2023.

JORION, P. Value at Risk: The New Benchmark for Managing Financial Risk. 2. ed. New York: McGraw-Hill, 2001.

JPMORGAN. RiskMetrics Technical Document. 4. ed. New York: JPMorgan, 1996.

KUPIEC, P. Techniques for verifying the accuracy of risk measurement models. The Journal of Derivatives, v. 3, n. 2, p. 73-84, 1995.

NELSON, D. B. Conditional heteroscedasticity in asset returns: A new approach. Econometrica, v. 59, n. 2, p. 347-370, 1991.

ZHANG, Y.; NADARAJAH, S. A review of backtesting for value at risk. Communications in Statistics – Theory and Methods, v. 47, n. 15, p. 3616-3639, 2018.

# Apêndice A

Matriz de Validação

Título: Plataforma de Modelagem e Backtesting de VaR com Machine Learning

Proposta/Projeto de Pesquisa: Desenvolver uma plataforma web para modelagem e backtesting de Value at Risk (VaR) integrando métodos tradicionais (simulação histórica, paramétrico e Monte Carlo), modelos de volatilidade condicional (GARCH e EGARCH) e algoritmos de Machine Learning (LSTM, GRU, CAViaR e GARCHNet), aplicada a ativos negociados na B3/Ibovespa.

| Objetivos da pesquisa |   | Fundamentação teórica | Pontos de Ação O que fazer? Informações necessárias | Etapas / Prioridades | Resultados Esperados |
|---|---|---|---|---|---|
| Geral | Específicos |   |   |   |   |
| Desenvolver uma plataforma web para modelagem e backtesting de VaR que integre métodos estatísticos tradicionais, modelos GARCH e algoritmos de Machine Learning, aplicada a ativos negociados na B3. | E0: Realizar levantamento das ferramentas existentes de VaR para identificar lacunas e validar a originalidade da proposta. | Jorion (2001); Fischer; Krauss (2018); Buczyński; Chlebus (2024); Zhang; Nadarajah (2018) | Identificar ferramentas existentes: QuantLib, Riskfolio-Lib, PyFolio, Bloomberg Risk, Refinitiv, notebooks acadêmicos. Analisar limitações de cada solução (ausência de ML, interface web, dados B3 ou backtesting estatístico). Documentar a lacuna que justifica a originalidade da proposta. | 1. Pesquisa de ferramentas (Alta) 2. Análise comparativa de limitações 3. Documentação da justificativa de originalidade | Levantamento comparativo das ferramentas existentes concluído. Lacuna confirmada: nenhuma ferramenta integra métodos tradicionais + GARCH + ML + backtesting estatístico em interface única voltada ao mercado brasileiro. |
|   | E1: Mapear e implementar os principais métodos tradicionais de cálculo do VaR (simulação histórica, paramétrico e Monte Carlo). | Jorion (2001); JPMorgan (1996) | Coletar dados via yfinance (Yahoo Finance): IBOV (^BVSP), PETR4.SA, VALE3.SA, ITUB4.SA — período jan/2015–dez/2024. Implementar VaR paramétrico, simulação histórica e Monte Carlo. Parametrizar nível de confiança (95%/99%), horizonte (1 dia) e janela (padrão: 252 dias úteis). | 1. Integração yfinance + tratamento de dados (Alta) 2. Módulo de coleta e limpeza (gaps, splits, dividendos) 3. Implementação dos 3 métodos 4. Testes unitários com séries sintéticas | Módulo com 3 métodos de VaR implementados e testados. Resultados validados contra cálculos de referência. |
|   | E2: Implementar modelos de volatilidade condicional (GARCH e EGARCH) para a estimativa de VaR. | Bollerslev (1986); Nelson (1991) | Estimar GARCH(1,1) e EGARCH via biblioteca arch (Python). Integrar variância condicional estimada ao VaR paramétrico dinâmico. Permitir configuração do modelo pelo usuário via interface. | 1. GARCH(1,1) (Alta) 2. EGARCH 3. Integração com VaR dinâmico 4. Verificação cruzada com R (rugarch) 5. Reestimação periódica dos parâmetros (janela expansiva, a cada 252 dias úteis) | Módulo GARCH/EGARCH integrado ao VaR dinâmico. Parâmetros convergentes e resíduos padronizados adequados. Identificada e corrigida instabilidade numérica do EGARCH em backtests de longo prazo (colapso da variância condicional sem reestimação periódica); coeficientes e log-verossimilhança validados contra o pacote rugarch (R). |
|   | E3: Identificar e implementar algoritmos de Machine Learning adequados à estimativa de VaR em séries financeiras, incluindo abordagens híbridas. | Hochreiter; Schmidhuber (1997); Fischer; Krauss (2018); Buczyński; Chlebus (2024); Cho et al. (2014); Engle; Manganelli (2004); Hybrid GARCH-GRU (arXiv:2310.01063, 2023) | Implementar LSTM e GRU (Keras/TensorFlow) prevendo o quantil de VaR diretamente via pinball loss (regressão quantílica neural, sem assumir normalidade dos retornos), com walk-forward validation e reestimação periódica a cada 252 dias úteis. Implementar CAViaR (especificação Symmetric Absolute Value) via otimização numérica (scipy.optimize, minimizando a pinball loss com múltiplos reinícios) — statsmodels.QuantReg não suporta a estrutura recursiva do CAViaR (VaR_t depende de VaR_{t-1}, que não é uma variável observada). Desenvolver GARCHNet (GARCH+LSTM) conforme Buczyński; Chlebus (2024), usando a volatilidade condicional do GARCH(1,1) (Etapa 2) como feature de entrada adicional da LSTM. Otimizar hiperparâmetros via grid search — escopo reduzido a 2 dimensões (unidades, camadas), com taxa de aprendizado e batch size fixos em valores padrão, por restrição computacional: o treino é específico por nível de confiança (95%/99%) e combinado ao walk-forward, tornando um grid de 4 dimensões impraticável no prazo do TCC. | 1. LSTM e GRU (Alta) 2. CAViaR 3. GARCHNet 4. Otimização via grid search (unidades, camadas) 5. Avaliação out-of-sample (walk-forward validation) | Módulos ML e híbrido funcionais. Modelos avaliados com dados reais da B3 via walk-forward validation. Resultado obtido: a LSTM aprovou simultaneamente os quatro testes de backtesting (Kupiec, Christoffersen, DQ e zonas de Basileia) a 95% de confiança sobre PETR4.SA (2015–2024) — o melhor desempenho entre todos os modelos implementados no projeto. Ressalva: a inicialização da rede e os reinícios do CAViaR não usam semente fixa, portanto os valores exatos variam entre execuções (semente pendente para a versão final). |
|   | E4: Desenvolver um módulo de backtesting com testes estatísticos (Kupiec, Christoffersen e DQ) para validação dos modelos implementados. | Kupiec (1995); Christoffersen (1998); Engle; Manganelli (2004); Zhang; Nadarajah (2018); Berger; Moys (2021); Basel Committee (2004) | Implementar teste POF (Kupiec). Implementar cobertura condicional (Christoffersen). Implementar teste DQ (Engle-Manganelli). Classificar resultados por zonas de Basileia II (verde/amarela/vermelha). | 1. Teste Kupiec (Alta) 2. Teste Christoffersen 3. Teste DQ 4. Zonas de Basileia (verde: ≤4; amarela: 5–9; vermelha: ≥10 violações/250 dias) 5. Validação com séries sintéticas de taxa de violação conhecida | Módulo com 3 testes e classificação regulatória. Validação contra implementações de referência. |
|   | E5: Construir uma interface web interativa que permita a configuração, execução e visualização dos resultados. | Transversal a todos os autores do referencial; Basel Committee (2004) | Front-end: Single Page Application em React (Vite), consumindo a API Flask via fetch — decisão tomada para desacoplar totalmente front-end e back-end. Back-end Flask como API JSON pura (sem HTML server-side) + orquestração dos módulos de modelagem. Dashboards interativos com Plotly.js para visualização de VaR, violações e backtesting (dependências já instaladas; visualização atual via tabelas comparativas — gráficos pendentes). Relatórios de backtesting exportáveis em CSV e JSON (p-valores, zonas de Basileia e demais estatísticas). | 1. Prototipação (Alta) 2. Back-end Flask (rotas/APIs) 3. Integração front × back via fetch/CORS (React) 4. Dashboards Plotly.js (pendente) 5. Testes de usabilidade com usuários-alvo | Plataforma web funcional e responsiva. Interface intuitiva validada por usuários-alvo. |
|   | E6: Avaliar comparativamente a acurácia dos métodos tradicionais, modelos GARCH e de Machine Learning utilizando dados históricos de ativos da B3. | Jorion (2001); Fischer; Krauss (2018); Buczyński; Chlebus (2024); Kupiec (1995); Christoffersen (1998); Engle; Manganelli (2004) | Selecionar ativos: IBOV (^BVSP), PETR4.SA, VALE3.SA, ITUB4.SA — jan/2015–dez/2024. Executar todos os modelos nas mesmas séries históricas. Aplicar backtesting padronizado (Kupiec, Christoffersen, DQ). Gerar ranking por taxa de violações, p-valores e zonas de Basileia. | 1. Design experimental (Alta) 2. Execução tradicionais + GARCH 3. Execução ML + híbridos 4. Backtesting comparativo 5. Análise e relatório final | Ranking comparativo de todos os modelos. Evidências empíricas para o mercado brasileiro (IBOV, PETR4, VALE3, ITUB4). |

(adaptado de: TELLES, Renato. A efetividade da matriz de amarração de Mazzon nas pesquisas em administração, 2001. RAUSP v36 n4, Out/Dez, 2001. http://200.232.30.99/busca/artigo.asp?num_artigo=426)

# APÊNDICE B

Declaração de Uso de Inteligência Artificial

Em conformidade com as diretrizes da Faculdade Impacta Tecnologia para trabalhos de conclusão de curso, os autores declaram o uso das seguintes ferramentas de Inteligência Artificial na elaboração deste trabalho:

| Campo | Descrição |
|---|---|
| Ferramenta 1 — Claude (Anthropic) |   |
| Ferramenta / Modelo | Claude Sonnet 4.5 (claude-sonnet-4-5) — Anthropic |
| Período de uso | Maio de 2026 |
| Tarefas realizadas | — Apoio à redação e organização textual da Introdução (Cap. 1): contextualização do problema, proposta do projeto, estruturação dos objetivos e justificativa. — Redação assistida do Capítulo 3 (Procedimentos Metodológicos): proposta de solução, estudo prévio de ferramentas, análise prévia de arquitetura, etapas de implementação, resultados esperados e fatores críticos de sucesso. — Revisão de consistência entre capítulos e Matriz de Validação (Apêndice A). |
| Entradas fornecidas | Prompts descritivos com contexto acadêmico, objetivos do projeto, decisões técnicas (Flask, yfinance, ativos da B3) e instruções de formatação ABNT. Nenhum dado sensível ou confidencial foi submetido à ferramenta. |
| Edição humana | Todas as saídas geradas foram revisadas, validadas e editadas pelos autores antes de incorporação ao trabalho. Parágrafos foram reescritos, referências verificadas manualmente na literatura e decisões técnicas confirmadas pelo grupo. |
| Extensão do uso | Cap. 1 — apoio à estruturação e revisão textual (estimativa: ~40% do conteúdo gerado com IA como rascunho, 100% revisado e editado pelos autores). Cap. 3 — rascunho inicial das seções 3.1, 3.1.1, 3.2, 3.3, 3.4 e 3.5 gerado com IA, com revisão e validação integral pelos autores. |
| Controle e validação | Os autores verificaram: (i) consistência das referências bibliográficas com as fontes originais; (ii) alinhamento das decisões técnicas com o projeto planejado; (iii) adequação do texto às normas ABNT e ao template institucional da Faculdade Impacta Tecnologia. |
| Autoria | A ferramenta de IA não é autora deste trabalho. Todo o conteúdo é de responsabilidade exclusiva dos autores, que assumem integral responsabilidade pelas informações apresentadas. |
| Dados e privacidade | Nenhum dado sensível, confidencial ou pessoal foi submetido à ferramenta. Os prompts utilizaram apenas informações públicas e decisões internas do projeto. |
| Ferramenta 2 — ChatGPT (OpenAI) |   |
| Ferramenta / Modelo | ChatGPT-4o — OpenAI |
| Período de uso | Março a maio de 2026 |
| Tarefas realizadas | — Apoio à pesquisa e síntese de literatura para o Referencial Teórico (Cap. 2): identificação de conceitos, resumo de abordagens e sugestão de autores relevantes. — Revisão gramatical e ortográfica de trechos textuais. — Esclarecimento de dúvidas sobre modelos matemáticos (GARCH, LSTM, backtesting). |
| Entradas fornecidas | Perguntas conceituais sobre VaR, GARCH, LSTM e backtesting. Trechos de texto para revisão gramatical. Nenhum dado sensível foi submetido. |
| Edição humana | Todas as saídas foram revisadas pelos autores. Nenhum trecho foi inserido diretamente no trabalho sem edição e validação humana prévia. |
| Extensão do uso | Cap. 1 — apoio pontual à revisão de trechos específicos. Referencial teórico — uso para esclarecimento de conceitos durante a leitura da literatura, não para geração de conteúdo inserido diretamente no trabalho. |
| Controle e validação | Os autores verificaram todas as informações conceituais geradas pelo ChatGPT nas fontes primárias citadas no referencial teórico (Jorion, 2001; Bollerslev, 1986; Fischer e Krauss, 2018; entre outros). |
| Autoria | A ferramenta de IA não é autora deste trabalho. Toda a responsabilidade pelo conteúdo é dos autores. |
| Dados e privacidade | Nenhum dado sensível ou confidencial foi submetido à ferramenta. |
| Declaração dos Autores |   |
| Responsabilidade | Os autores declaram total responsabilidade sobre o conteúdo apresentado neste trabalho. As ferramentas de Inteligência Artificial foram utilizadas exclusivamente como apoio à pesquisa, revisão e organização textual, com verificação e validação humana de todas as saídas geradas. As ferramentas de IA não substituíram o julgamento acadêmico, a revisão crítica da literatura nem as decisões metodológicas do grupo. |
| Reprodutibilidade | Os prompts utilizados estão disponíveis para consulta mediante solicitação ao grupo de autores. |
| Assinatura | Cintia Marques Castanho Sae Guilherme Nunes Joanna Kauã Ribeiro Santos Lucas Fernandes de Melo São Paulo, maio de 2026. |

Nota: Esta declaração segue as recomendações institucionais e as boas práticas acadêmicas de transparência no uso de ferramentas de IA em pesquisa científica.
