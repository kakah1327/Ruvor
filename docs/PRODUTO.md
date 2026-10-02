# Ruvor — Produto

O que a plataforma é, para quem, e o que entrega. Para *como* é construída, ver
[ARQUITETURA.md](ARQUITETURA.md).

---

## 1. O que é

Plataforma de análise de risco em ações. O usuário quer saber **quanto pode perder** se
aplicar em uma ação ou em um conjunto de ações, e a plataforma responde com transparência
sobre o método — não com um número solto.

A pergunta central, nas palavras do usuário:

> "Quero saber qual a previsão de perda se eu aplicar no ITUB4."

Entrega tudo o que se precisa saber sobre uma ação, **exceto executar a compra**. Não é
corretora e não intermedia ordem.

### Diferencial

**A quantidade de algoritmos comparados sobre a mesma base, com validação estatística de
qual deles merece confiança.**

É a lacuna levantada e comprovada no TCC: nenhuma ferramenta existente reúne métodos
tradicionais, volatilidade condicional e Machine Learning com backtesting estatístico num
fluxo comparativo único. É o único território não saturado do produto — ver
[§3](#valor-competitivo-por-camada).

### Escopo negativo

- Não executa ordens nem intermedia investimento
- Não importa carteira pronta de corretora ([D-03](decisoes/D-03-carteira-montada-pelo-usuario.md))
- Não prevê lucro/retorno na versão inicial ([D-06](decisoes/D-06-perda-e-o-foco.md))

---

## 2. Público e postura

Duas leituras do mesmo dado, não dois produtos:

- **Iniciante** — não domina o jargão, precisa entender o que cada número significa
- **Avançado** — quer profundidade, método e parâmetros

Consequência de arquitetura, não de interface: **todo número exibido carrega explicação em
linguagem clara, junto do dado.** Texto explicativo é conteúdo de primeira classe,
versionado com a métrica que explica — não um glossário à parte.

Desde o M2.3 as duas leituras existem: o visitante escolhe o nível no casco, e cada número traz a frase do nível. O
texto mora no frontend, versionado no repositório — a frase e o cálculo mudam no mesmo commit, revisados na mesma PR —,
e não no banco nem na API ([D-151](decisoes/D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md)); o
nível é do visitante, global, e o padrão é iniciante
([D-152](decisoes/D-152-o-nivel-de-leitura-e-escolha-do-visitante.md)).

| Leitura avançada | Leitura iniciante |
|---|---|
| "Volatilidade anualizada: 32%" | "Esta ação costuma variar bastante — oscilações de 30% para cima ou para baixo são esperadas em um ano normal." |

---

## 3. As cinco camadas

"Tudo sobre a ação" desmontado em cinco camadas. **Todas fazem parte da visão.** O que se
decide por marco é a ordem de chegada, não o corte.

| # | Camada | Conteúdo | Fonte |
|---|---|---|---|
| 1 | **Identidade e preço** | empresa, setor, tamanho, preço, gráfico, volume, dividendos, desdobramentos | série de preços |
| 2 | **Comportamento** | retornos por janela, volatilidade, maior queda e recuperação, relação com o Ibovespa, distribuição de retornos | série de preços |
| 3 | **Risco** | VaR por múltiplos algoritmos + qual algoritmo é confiável para aquela ação | série de preços |
| 4 | **Fundamentos** | lucro, receita, dívida, margens, múltiplos | **fonte nova** |
| 5 | **Contexto** | notícias, comparação com pares do setor | **fonte nova** |

### A fronteira que importa

Camadas **1, 2 e 3 derivam todas da série histórica de preços** — uma fonte só, o resto é
cálculo próprio. Autossuficientes.

Camadas **4 e 5 exigem ingestão nova.** Restrição concreta: o Yahoo Finance é fraco em
fundamentos de empresa brasileira — balanço, lucro e receita de ações da B3 vêm incompletos
ou desatualizados. Fundamento confiável de B3 exige outra fonte e vira subsistema próprio.

### Valor competitivo por camada

| Camada | Quem já entrega hoje |
|---|---|
| 1 e 2 | Status Invest, Investidor10, TradingView, a corretora — de graça |
| **3** | **Ninguém** |
| 4 | Status Invest, Fundamentus, Investidor10 — de graça e melhor que o Yahoo |
| 5 | InfoMoney, TradingView, Google Finance |

Quatro das cinco são território saturado com concorrentes gratuitos e maduros. Continuam
necessárias — ninguém usa ferramenta que obriga abrir outra aba para ver o preço. Mas
construir as commodity primeiro significa passar meses fazendo uma versão pior do Status
Invest antes de existir motivo para alguém trocar de ferramenta.

**É o que determina a ordem dos marcos.**

---

## 4. Marcos

### Fundação

Repositório, estrutura, banco, migrations, CI, ambientes, e o processo de trabalho
([PROCESSO.md](PROCESSO.md)). Não entrega nada ao usuário final. É o que faltou e produziu
o estado anterior.

### Marco 1 — a ação, e o risco dela

- Catálogo de ativos da B3 (nome, setor, situação) — base da busca
- Ingestão de preços: histórico + atualização diária, armazenados pela plataforma
- Camadas 1 e 2 (identidade, preço, comportamento)
- Camada 3 (risco) no regime de produção — o de laboratório foi para o Marco 2
  ([D-74](decisoes/D-74-o-marco-1-e-so-producao.md))
- Execução assíncrona no modo A + pré-cálculo dos ativos cobertos
- Aplicação web com a identidade Ruvor: busca e tela do ativo
- O risco em **1 dia** ([D-98](decisoes/D-98-o-horizonte-do-marco-1-e-1-dia-restringe-a-d-05.md)),
  com a discordância entre modelos e os não rejeitados por ativo (5.1 e 5.2,
  [D-96](decisoes/D-96-discordancia-e-aprovados-entram-no-marco-1.md))

Resultado: digita ITUB4, recebe tudo sobre o comportamento da ação **e** a comparação de
risco que ninguém mais faz. Sem login, sem carteira. Menor coisa que já justifica existir —
e coincide em grande parte com o conteúdo do TCC, então os dois avançam juntos.

### Marco 2 — vira plataforma

- Usuários, autenticação, papéis, permissões
- Carteira composta pelo usuário, com risco de carteira
- Camada explicativa iniciante/avançado como sistema
- Camada 3 no regime de laboratório ([D-04](decisoes/D-04-dois-regimes-de-operacao.md),
  [D-74](decisoes/D-74-o-marco-1-e-so-producao.md))

### Marco 3 — "tudo sobre a ação" completo

- Fundamentos (camada 4), com fonte adequada para B3
- Contexto e comparação setorial (camada 5)
- Na tela do ativo desde o M1.6c, depois do risco, com a posição entre os pares e os comunicados da companhia à CVM
  ([D-99](decisoes/D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md))

### Marco 4 — produto institucional

- Relatórios exportáveis e auditáveis
- API pública com chaves e escopos

### Marco 5

- Retorno / lucro

---

## 5. Requisitos candidatos

Ideias levantadas, ainda **não promovidas a requisito** — salvo onde marcado. As três primeiras
saem quase de graça do que já vai existir no Marco 1. **A 5.1 e a 5.2 foram promovidas ao Marco 1**
e entraram na tela do M1.6b ([D-96](decisoes/D-96-discordancia-e-aprovados-entram-no-marco-1.md)): a
5.2 como a lista dos modelos não rejeitados, sem eleger nenhum
([D-65](decisoes/D-65-a-plataforma-lista-os-aprovados-e-nao-elege-nenhum.md)).

### 5.1 Discordância entre modelos como sinal de risco

Rodando 9 algoritmos há 9 respostas — e **a distância entre elas é informação**. "Os modelos
estimam perda entre 3,1% e 5,8%" diz o que nenhuma estimativa isolada diz: métodos
concordando, leitura sólida; divergindo, momento incerto — alerta por si só.

Ninguém mostra isso porque ninguém roda 9 modelos. Gratuito para o Ruvor e impossível de
copiar sem refazer o trabalho inteiro.

### 5.2 "Em qual modelo confiar para esta ação"

O Capítulo 4 do TCC revela resultado ainda não explorado: **o melhor modelo muda conforme o
ativo e o nível de confiança.** A LSTM passou nos quatro testes a 95% e reprovou em dois a
99%; o GARCH(1,1) fez o inverso.

Não existe "o melhor modelo" — existe o melhor *para esta ação, neste nível*.

### 5.3 Estresse histórico

O período 2015–2024 contém a COVID, a recessão de 2015–16 e o ciclo de juros. Permite
responder: *"esta carteira teria perdido 38% em março de 2020"*. Custo quase zero, altíssimo
poder de comunicação, e é o formato mais fácil de entender para quem não é do mercado.

### 5.4 Expected Shortfall

O TCC está ancorado em **Basileia II (2004)**, onde o VaR é a medida oficial. Basileia III
substituiu o VaR por **Expected Shortfall** para modelos internos.

O VaR diz *"em 95% dos dias você não perde mais que 4%"* e não diz nada sobre os outros 5%.
Perder 5% ou 40% é indiferente para ele — foi por isso que falhou em 2008. O Expected
Shortfall responde: *"quando dá ruim, dá ruim quanto, em média?"*

A lista de referências do TCC já cita trabalho sobre VaR **e** Expected Shortfall, então é
extensão coerente com a literatura levantada. Tecnicamente é barato. **Para um produto que
continua depois do TCC, ficar só em VaR é postura datada.**

### 5.5 Alerta de degradação de modelo

Os testes rodam continuamente e avisam quando um modelo antes aprovado começa a falhar. É
literalmente a tela "PETR4.SA requer revisão" do kit de marca.

### 5.6 Contribuição de risco por ativo

*"VALE3 é 20% da sua carteira mas responde por 35% do seu risco."* Ferramenta institucional
tem, ferramenta de varejo não tem, e muda decisão.

### 5.7 Limite pessoal de perda

O usuário define quanto aceita perder e é avisado quando a carteira ultrapassa. Transforma a
ferramenta de passiva em ativa.

---

## 6. Restrições de produto

### Carteira muda o problema de natureza

O risco de ter ITUB4 + PETR4 + VALE3 junto **não é a soma dos riscos de cada uma**, porque
as ações se movem juntas. Se caem no mesmo dia, o risco é maior que a soma; se uma sobe
quando a outra cai, uma protege a outra.

- **Caminho barato** — trata a carteira como um ativo só: calcula o retorno diário ponderado
  pelos pesos e joga essa série única nos algoritmos existentes. Funciona, é honesto, não
  exige modelo novo. Limitação: mudar os pesos obriga a recalcular.
- **Caminho caro** — modelar explicitamente a relação entre os ativos. Exige família de
  modelos que o projeto não tem e o TCC não cobre.

**Recomendação: caminho barato.** Ainda não formalizado.

### Horizonte longo é mais difícil de validar

Risco de 1 dia sobre 10 anos: ~2.500 pontos para conferir. Risco de 4 semanas: ~120
períodos independentes. Os testes estatísticos precisam de volume para distinguir "modelo
ruim" de "azar" — com 120 pontos, quase nada é detectável.

Tem saída (janelas sobrepostas com correção estatística), mas a spec precisa assumir isso
explicitamente. Ver [D-05](decisoes/D-05-horizonte-semanas-primeiro.md).

### O diferencial é também o centro de custo

Cada análise de carteira que dispara os modelos de ML gasta minutos de CPU dedicada. Um
usuário custa centavos; mil usuários analisando carteiras diferentes por dia vira a maior
linha da conta, e cresce linearmente — cada combinação de pesos é única.

A spec do Marco 1 deve prever **cache agressivo e limite de análises pesadas por usuário**.

### Fronteira regulatória (CVM)

*Não é parecer jurídico; exige confirmação com quem tem competência.*

No Brasil, **recomendar investimento é atividade regulada pela CVM** — analista e consultor
de valores mobiliários exigem autorização. A fronteira costuma ficar entre:

- **informar / analisar** — o usuário escolhe, a plataforma mostra o risco do que ele escolheu
- **recomendar** — o sistema diz o que comprar ou sugere composição de carteira

"Montar carteira" atravessa essa linha com facilidade se a plataforma sugerir pesos.
Desenhar do lado seguro agora custa nada. **Buscar parecer antes dos blocos que tocam composição ou peso de carteira**
— o M2.2 e o que dele derivar —, não antes do Marco 2 inteiro: explicar o que já se mostra é informar
([D-153](decisoes/D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md)). Na carteira, o parecer segura o merge da
implementação, não a spec nem o plano
([D-116](decisoes/D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md)).

---

## 7. Relação com o TCC

O TCC e o Ruvor compartilham o **motor numérico** e divergem no resto. O modelo
núcleo-aberto sustenta as duas leituras ao mesmo tempo — ver
[ARQUITETURA.md](ARQUITETURA.md#estrutura-do-repositório).

Trilha paralela e independente da plataforma: a **Etapa 6** (ranking comparativo dos 9
modelos nos 4 ativos) não foi executada e o Capítulo 5 está em branco. É tempo de máquina,
não desenvolvimento.

Ver [`docs/tcc/`](tcc/) e [`docs/prototipo/`](prototipo/).

---

## 8. Pendências de produto

| Tema | Situação |
|---|---|
| Carteira: caminho barato ou caro | Recomendação: barato. Não formalizado |
| Quais requisitos candidatos entram no Marco 1 | ✅ 5.1 e 5.2 ([D-96](decisoes/D-96-discordancia-e-aprovados-entram-no-marco-1.md)); a 5.3 segue candidata |
| Política de cobertura e atualização de ativos | Quais ficam pré-calculados, com que frequência retreinar |
| Parecer sobre fronteira CVM | Pendente, antes do merge da carteira — o M2.2 e o que dele derivar ([D-153](decisoes/D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md), [D-116](decisoes/D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md)) |
| Verificação de marca e domínio "Ruvor" | Nunca feita; em paralelo, não bloqueia |

**Resolvidos no M1.6a** (2026-09-28): o tema — o kit tem claro e escuro, pelos mesmos tokens
([D-88](decisoes/D-88-o-kit-tem-dois-temas-pelos-mesmos-tokens.md)) —, e o kit incompleto — os
estados de interação, a escala tipográfica e a folha de componentes, derivados dos mockups
([D-87](decisoes/D-87-os-mockups-sao-a-referencia-visual-do-kit.md)).
