# 01 — Visão geral e requisitos

## Problema

Estimar o Value at Risk (VaR) de um ativo exige escolher um modelo, e essa escolha muda
materialmente o resultado. Não existe ferramenta livre que permita rodar métodos
tradicionais, GARCH e Machine Learning **sobre a mesma série, com o mesmo protocolo** e
comparar a calibração de cada um por testes estatísticos reconhecidos:

- bibliotecas de risco (QuantLib, Riskfolio-Lib, PyFolio) não têm ML nem backtesting estatístico;
- plataformas comerciais (Bloomberg, Refinitiv) são caixa-preta e de acesso restrito;
- implementações acadêmicas em notebook são fragmentadas e não comparáveis entre si.

O VaR Lab preenche essa lacuna: um sistema onde adicionar um modelo novo custa um arquivo,
e onde todo modelo é automaticamente submetido ao mesmo backtesting.

## Escopo

### Dentro do escopo

- Séries de **um único ativo** por experimento (não há VaR de portfólio).
- Ativos da B3 via Yahoo Finance, e qualquer ticker que o `yfinance` resolva.
- Horizonte de **1 dia útil**, níveis de confiança de **95% e 99%**.
- 9 modelos de VaR e 4 instrumentos de validação (ver [03](03-modelos.md) e [04](04-backtesting.md)).
- Execução headless por CLI e consulta de resultados por API/SPA.

### Fora do escopo

- VaR de portfólio, correlações entre ativos, Expected Shortfall.
- Autenticação, multiusuário, controle de acesso.
- Dados intradiários ou em tempo real; a granularidade é diária.
- Treino distribuído ou uso de GPU (ver [05 — custo computacional](05-dados-e-protocolo.md#custo-computacional)).

## Requisitos funcionais

Rastreáveis aos objetivos específicos do TCC (Matriz de Validação, Apêndice A). A coluna
*Etapa* preserva a numeração E0–E6 usada no trabalho acadêmico, para que as duas
referências continuem cruzáveis.

| ID | Etapa | Requisito | Status |
|---|---|---|---|
| RF-01 | E1 | Coletar séries de preços ajustados por ticker e período | ✅ |
| RF-02 | E1 | Limpar preços inválidos e converter para log-retornos | ⚠️ sem detecção de outliers |
| RF-03 | E1 | Estimar VaR paramétrico, histórico e de Monte Carlo | ✅ |
| RF-04 | E1 | Parametrizar nível de confiança, horizonte e janela de treino | ⚠️ horizonte não exposto na CLI |
| RF-05 | E2 | Estimar VaR dinâmico por GARCH(1,1) e EGARCH | ✅ |
| RF-06 | E2 | Reestimar parâmetros periodicamente com janela expansiva | ✅ |
| RF-07 | E2 | Verificar a estimação contra implementação de referência (rugarch/R) | ⚠️ script manual, fora da suíte |
| RF-08 | E3 | Estimar VaR por LSTM e GRU via regressão quantílica neural | ✅ |
| RF-09 | E3 | Estimar VaR por CAViaR (Symmetric Absolute Value) | ✅ |
| RF-10 | E3 | Estimar VaR pelo híbrido GARCHNet (GARCH + LSTM) | ✅ |
| RF-11 | E3 | Otimizar hiperparâmetros por grid search | ✅ escopo reduzido a 2 dimensões |
| RF-12 | E3 | Validar out-of-sample por walk-forward, sem look-ahead | ✅ |
| RF-13 | E3 | Reportar métricas de erro comparáveis entre modelos | ❌ |
| RF-14 | E4 | Aplicar Kupiec, Christoffersen e DQ a qualquer modelo | ✅ |
| RF-15 | E4 | Classificar por zonas de Basileia II | ✅ |
| RF-16 | E5 | Expor os resultados por API JSON | ✅ |
| RF-17 | E5 | Permitir configurar e **executar** um experimento pela interface | ❌ |
| RF-18 | E5 | Visualizar série de VaR, violações e resultados em gráfico | ❌ |
| RF-19 | E5 | Exportar relatório de backtesting em CSV e JSON | ✅ |
| RF-20 | E6 | Executar todos os modelos sobre os mesmos dados e ranquear | ⚠️ orquestrador pronto, execução parcial |
| RF-21 | — | Persistir experimentos para consulta posterior | ✅ |

Os itens ❌ e ⚠️ estão detalhados e priorizados em [07 — Backlog de specs](07-backlog-specs.md).

## Requisitos não funcionais

| ID | Requisito | Situação |
|---|---|---|
| RNF-01 | Adicionar um modelo novo não deve exigir alteração em web, CLI, backtesting ou experiments | ✅ garantido pelo registry ([02](02-arquitetura.md)) |
| RNF-02 | Dependências pesadas (TensorFlow, arch) devem ser opcionais | ✅ extras do `pyproject.toml`; registry ignora módulo cujo import falha |
| RNF-03 | Backtesting não pode conhecer implementação de modelo | ✅ recebe apenas `returns` e `var_series` |
| RNF-04 | Modelo novo deve ser testado sem escrever teste novo | ✅ suíte parametrizada sobre o registry |
| RNF-05 | Resultados devem ser reprodutíveis entre execuções | ❌ redes neurais sem semente fixa |
| RNF-06 | Nenhum modelo pode usar informação futura na estimativa | ✅ walk-forward em todos os modelos condicionais |
| RNF-07 | Falha de um modelo não pode derrubar o experimento | ✅ erro isolado por `(modelo, alpha)` |

## Critérios de aceite por etapa

Traduzidos da seção "Resultados Esperados" do TCC para condições verificáveis.

| Etapa | Critério de aceite | Situação |
|---|---|---|
| E1 | Os 3 métodos batem com cálculo de referência independente | ✅ `tests/models/test_traditional_reference.py` |
| E2 | Parâmetros convergem e resíduos padronizados são bem comportados | ✅ `tests/models/test_garch_diagnostics.py` |
| E2 | Log-verossimilhança concorda com o rugarch (R) | ✅ divergência < 1,5% em PETR4.SA |
| E3 | Os 4 modelos de ML avaliados out-of-sample em dados reais da B3 | ⚠️ apenas PETR4.SA |
| E4 | Testes validados contra séries sintéticas de violação conhecida | ✅ `tests/backtesting/test_formulas.py` |
| E5 | Interface permite configurar, executar e visualizar | ❌ hoje só consulta |
| E6 | Ranking comparativo dos 9 modelos nos 4 ativos | ❌ |
