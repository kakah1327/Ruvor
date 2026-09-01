# 07 — Backlog de specs

Lacunas abertas, cada uma com contexto suficiente para virar especificação de
implementação. Ordenadas por dependência, não por esforço.

## Panorama

| # | Item | Requisito | Bloqueia |
|---|---|---|---|
| 1 | Reprodutibilidade das redes neurais | RNF-05 | Etapa 6 |
| 2 | Executar experimento pela interface | RF-17 | testes de usabilidade |
| 3 | Ranking comparativo completo | RF-20 | conclusão do TCC |
| 4 | Visualização gráfica | RF-18 | testes de usabilidade |
| 5 | Métricas de erro comparáveis | RF-13 | — |
| 6 | Ativar o cache de dados | — | — |
| 7 | Limpeza de dados: outliers | RF-02 | — |
| 8 | Horizonte configurável na CLI | RF-04 | — |
| 9 | Verificação com R na suíte | RF-07 | — |

---

## RNF-05 — reprodutibilidade das redes neurais

**Problema.** LSTM, GRU e GARCHNet não fixam semente; a inicialização de pesos do Keras
varia a cada execução. Os p-valores publicados no TCC §4.3 não são reproduzíveis.

**Por que vem primeiro.** O ranking da Etapa 6 é o resultado central do trabalho. Publicar
números que ninguém consegue reproduzir — inclusive a banca — é um problema de método,
não de engenharia. Precisa estar resolvido **antes** de rodar o experimento final.

**Escopo.** Semente derivada de forma determinística, no mesmo espírito do `caviar`
(`seed = int(alpha*10000)`), aplicada a `tf.keras.utils.set_random_seed` no início de
`_fit_for_alpha`. Deve cobrir também o *warm start* dos blocos de reestimação, senão a
divergência reaparece no walk-forward.

**Critério de aceite.** Duas execuções de `varlab run` com os mesmos argumentos produzem
`ranking_table()` idêntica. Teste automatizado com série sintética curta.

**Efeito colateral a decidir.** Semente fixa esconde a variância do modelo. Vale expor a
semente como parâmetro, para que a variabilidade possa ser medida de propósito — a
dispersão dos p-valores entre sementes é um resultado defensável na dissertação.

**Correção de texto associada.** O §4.3 e a Matriz de Validação afirmam que o CAViaR não
tem semente fixa; ele tem. Só as redes neurais são não reprodutíveis.

---

## RF-17 — executar experimento pela interface

**Problema.** A API é somente leitura ([06](06-api.md#a-api-é-somente-leitura)). Só a CLI
gera resultados. O objetivo específico (e) do TCC — "interface que permita a configuração,
execução e visualização" — não está cumprido, e é o nome do projeto.

**Restrição dura.** Um experimento leva de 20 a 60 minutos
([05](05-dados-e-protocolo.md#custo-computacional)). Não cabe em requisição síncrona.

**Escopo.**

- `POST /api/experiments` recebendo `{ticker, start, end, models[], backtests[], alphas[], train_window_days}`, validando contra os registries, e devolvendo `202` com um id.
- `GET /api/experiments/<id>` para consultar estado (`pending` | `running` | `done` | `error`).
- Execução fora do ciclo da requisição.
- Formulário no React, montado dinamicamente a partir de `/api/models` e `/api/backtests` — assim um modelo novo aparece no formulário sem mexer no frontend, preservando o RNF-01.

**Decisão em aberto — mecanismo de execução.** Vale escolher explicitamente antes de
implementar:

| Opção | A favor | Contra |
|---|---|---|
| `threading` no processo Flask | zero dependência nova, coerente com o escopo | morre com o processo; sem fila |
| Fila com worker (RQ/Celery) | robusto, cancelável, observável | traz Redis e mais um processo — desproporcional ao escopo |
| Enfileirar e executar por comando | simples, auditável | não é "executar pela interface" de fato |

Recomendação: **thread com estado persistido**, o suficiente para cumprir o requisito sem
inflar a infraestrutura de um TCC.

**Cuidado.** Sem limite, a interface deixa qualquer visitante disparar horas de CPU.
Convém limitar execuções concorrentes e validar o intervalo de datas.

---

## RF-20 — ranking comparativo completo (Etapa 6)

**Problema.** O TCC §4.5 está vazio e o Capítulo 5 depende dele. O que foi executado até
agora cobre **apenas PETR4.SA**; o trabalho promete 4 ativos em quatro pontos distintos do
texto.

**Escopo.** Executar os 9 modelos × 4 tickers × 2 alphas × 4 backtests, período
2015–2024, e consolidar em ranking com taxa de violação, p-valores e zona de Basileia.

**Custo.** 4 execuções completas — estimativa de 2 a 4 horas de CPU, serializadas.
Planejar como tempo de máquina, não como sessão de trabalho.

**Depende de:** item 1 (senão o ranking não é reproduzível).

**Decisão em aberto.** Manter os 4 tickers ou reduzir a PETR4 + IBOV? Reduzir custa uma
correção de texto em quatro lugares e economiza horas; manter é o que está prometido.

**Saída esperada.** Preenchimento do §4.5, redação do Capítulo 5, e a evidência empírica
que responde a pergunta de pesquisa.

---

## RF-18 — visualização gráfica

**Problema.** `plotly.js` está instalado e nunca importado. O `ResultDetail` mostra
apenas tabela.

**Bloqueio de dados, não de frontend.** O `ranking` persistido guarda só o veredito
agregado — não guarda a série de VaR nem as violações
([06](06-api.md#formato-de-ranking)). **Não é possível desenhar o gráfico principal a
partir de um run salvo.** A spec precisa cobrir os dois lados:

1. persistir a série de VaR e o indicador de violação por `(modelo, alpha)`;
2. só então o gráfico: retornos, curva de VaR por modelo, violações marcadas.

Cuidado com o volume: 9 modelos × 2 alphas × ~2200 dias é da ordem de 40 mil pontos por
run. Vale decidir se persiste tudo, ou só os modelos selecionados.

---

## RF-13 — métricas de erro comparáveis

**Problema.** O TCC §3.4 promete, para a Etapa 3, "métricas de erro (RMSE e MAE)
calculadas para comparação entre os modelos de ML puros e as abordagens híbridas". Não
existe nada disso no código.

**Ressalva metodológica.** RMSE e MAE sobre VaR são fracos: VaR é um **quantil**, não uma
previsão de nível, e não existe valor observado de VaR contra o qual medir erro. A métrica
natural é a **pinball loss média** no nível de alpha — que é exatamente a função que os
modelos de ML minimizam, e que se aplica igualmente a GARCH e aos tradicionais, permitindo
ranquear as três famílias na mesma escala.

**Recomendação.** Implementar a pinball loss média como métrica de comparação e ajustar o
§3.4, defendendo a escolha. Se RMSE/MAE forem mantidos por compromisso com o texto,
calcular contra o retorno realizado e declarar a limitação.

**Escopo.** Coluna adicional em `ranking_table()`, calculada no runner sobre o par
alinhado — vale para todo modelo, sem tocar na camada de modelos.

---

## Ativar o cache de dados

**Problema.** `varlab/data/cache.py` está implementado, testado por ninguém e **chamado
por ninguém** — nem `fetch_returns` nem o provider o usam. Toda execução rebaixa da rede.

**Escopo.** Ligar o cache no caminho de leitura, com invalidação por `(ticker, start,
end)` — chave que a implementação atual já usa. Ou remover o módulo, se a decisão for não
usá-lo; código morto em documentação técnica é pior que ausência.

**Ganho.** Relevante para o item 3: 4 execuções longas sobre os mesmos dados.

---

## RF-02 — limpeza de dados

**Problema.** `clean_prices` só descarta `close <= 0` e nulo. O TCC §3.5 promete detecção
de retornos aberrantes e comparação com fontes alternativas, como mitigação declarada do
risco de qualidade de dados do yfinance.

**Escopo mínimo defensável.** Detecção e registro de outliers (por exemplo, retorno
absoluto acima de N desvios), sem descartar automaticamente — em série financeira, retorno
extremo costuma ser **o dado que mais importa**, não ruído. Descartar outlier num trabalho
sobre risco de cauda seria contraproducente.

A comparação com fontes alternativas exige um segundo provider; avaliar se compensa dentro
do escopo, ou se o texto deve ser ajustado.

---

## RF-04 — horizonte configurável na CLI

**Problema.** `ExperimentConfig.horizon` existe e todo modelo respeita, mas `varlab run`
não expõe a flag — o horizonte é sempre 1.

**Escopo.** Adicionar `--horizon`. Trivial.

**Ressalva.** A regra da raiz do tempo usada para `horizon > 1` é aproximação em todos os
modelos, e nunca foi exercitada. Se a flag for exposta, vale documentar a limitação junto —
ou manter fixo em 1 e ajustar o texto, já que 1 dia é a exigência de Basileia II.

---

## RF-07 — verificação com R na suíte

**Situação.** A verificação cruzada com `rugarch` foi feita e os números estão no §4.2, mas
o procedimento é manual (`tools/garch_rcheck/`), fora do `pytest`, porque nem todo ambiente
tem R.

**Escopo possível.** Congelar os coeficientes de referência do R num fixture e testar a
saída do `arch` contra eles, com tolerância. Dá regressão automatizada sem exigir R
instalado.

---

## Divergências entre o texto do TCC e o código

Correções de texto, sem trabalho de engenharia. Todas na seção 3.2 (Análise Prévia), que
não foi atualizada quando o Capítulo 4 e o Apêndice A foram.

| Onde | O texto diz | O código faz |
|---|---|---|
| §1 e §3.2 | frontend em templates Jinja2 (e "Flask/Django") | SPA React + Vite, Flask como API JSON pura |
| §3.2 | CAViaR via `statsmodels.QuantReg` | `scipy.optimize`, Nelder-Mead com 10 reinícios |
| §3.2 | sem banco persistente, tudo em memória | SQLite via repository pattern, e a API depende dele |
| §3.2 | grid search inclui learning rate e batch size | apenas `units` e `n_layers` |
| §4.3, Apêndice A | CAViaR sem semente fixa | CAViaR é determinístico; só as redes neurais não são |
| §3.5 | limpeza com detecção de aberrantes e fontes alternativas | apenas descarte de nulos e não positivos |

As três primeiras já estão corrigidas no Capítulo 4 ou no Apêndice A — o que resta é
alinhar a §3.2, que hoje contradiz o resto do próprio documento.

A quinta é uma **afirmação incorreta**, não desatualização: vale corrigir mesmo que nada
mais mude.
