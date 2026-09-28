# Ruvor — Arquitetura

Como o sistema é construído. Para *o que* ele entrega, ver [PRODUTO.md](PRODUTO.md).

---

## Pilha tecnológica

| Camada | Escolha |
|---|---|
| Backend | Python + Django |
| API | Django REST Framework |
| Frontend | React |
| Banco | PostgreSQL |
| Fila e cache | Celery + Redis |
| Tipagem | obrigatória, verificada no CI |

Decisões e justificativas: [D-11](decisoes/D-11-pilha-tecnologica.md),
[D-12](decisoes/D-12-tipagem-obrigatoria.md).

**Resumo do porquê:** o time vem de C#/.NET, Java, Laravel e Angular/React. Django é o
framework Python que mais se parece com esses — ORM oficial, migrations, autenticação
pronta, estrutura convencionada. Login, permissão e auditoria são obrigatórios e
completamente commodity; cada hora reimplementando isso é hora que não foi para o motor de
risco, que é a única parte que ninguém mais tem.

---

## Estrutura do repositório

**Estado alvo.** Os blocos do roadmap chegam nele por partes — `infra/` nasceu no F3, e
`apps/` no F4, com o primeiro app: `apps/accounts`.

```
ruvor/
├── engine/            # projeto do motor numérico
│   ├── pyproject.toml     metadados de ruvor-engine
│   ├── src/
│   │   └── engine/        ← pacote importável — ZERO Django aqui dentro
│   │       ├── models/        algoritmos de VaR
│   │       ├── backtesting/   testes estatísticos
│   │       ├── data/
│   │       ├── experiments/
│   │       └── cli.py
│   └── tests/
│
├── backend/           # aplicação Django
│   ├── pyproject.toml
│   ├── manage.py
│   ├── config/            settings, urls
│   └── apps/              um app por domínio
│       ├── assets/          ações, catálogo, preços
│       ├── analytics/       camada 2 — comportamento
│       ├── risk/            camada 3 — execução, manifesto
│       ├── fundamentals/    balanços da CVM, indicadores fundamentalistas
│       ├── portfolios/      carteiras
│       ├── accounts/        organizações, usuários, permissões
│       └── audit/
│
├── frontend/          # React
├── infra/             # arquivos de construcao de imagem
├── .github/workflows/ # a CI — ver D-45
├── compose.yaml       # na raiz, nao em infra/ — ver D-35
├── .dockerignore      # na raiz: e onde o Docker o procura
├── docs/
└── brand/
```

**`compose.yaml` e `.dockerignore` ficam na raiz** porque dentro de `infra/` os dois
falhariam em silêncio: o Docker procura o `.dockerignore` na raiz do contexto de construção,
e o Compose descobre o `.env` no diretório do arquivo de composição
([D-35](decisoes/D-35-compose-e-dockerignore-na-raiz.md)).

**A CI mora em `.github/workflows/`, pela mesma razão.** O diagrama já reservou a CI para
`infra/`, mas o GitHub só lê `.github/workflows/`: o arquivo em `infra/` não seria executado,
e o sintoma seria a **ausência de execução** — sem erro e sem aviso
([D-45](decisoes/D-45-a-ci-mora-em-github-workflows.md)).

**Não existe `pyproject.toml` na raiz.** Um projeto Python por diretório: cada um declara as
próprias dependências e a configuração das próprias ferramentas. É o que permite ao F3
construir imagens diferentes — a web sem TensorFlow, o worker com.

**Layout `src/` no motor**, e não o pacote na raiz do projeto: com `src/`, `import engine` só
funciona se o pacote estiver instalado, nunca por resolução acidental a partir do diretório
de trabalho. É o que torna verificável a exigência de instalar em ambiente limpo.

### A regra estrutural inegociável

**`engine/` não importa Django.** Nunca. Paga em quatro lugares:

1. **O motor roda sem a plataforma.** A Etapa 6 do TCC pode ser executada por linha de
   comando, sem esperar o Django existir.
2. **O TensorFlow fica fora da imagem web.** Duas imagens Docker do mesmo código: `web`
   leve, `worker` pesado. O servidor que atende telas não carrega meio giga de biblioteca de
   rede neural.
3. **É testável isoladamente** — o que dá credibilidade científica.
4. **Pode ser publicado como pacote aberto.**

O quarto ponto resolve a tensão de posicionamento: o TCC afirma entregar "plataforma
funcional e de código aberto para ensino e pesquisa". Com `engine/` como pacote aberto e
Ruvor como a plataforma sobre ele, **as duas afirmações são verdadeiras ao mesmo tempo** —
sem mudar a justificativa da pesquisa.

Ver [D-17](decisoes/D-17-monorepo-engine-sem-django.md).

---

## Banco e camadas de dado

**Isso não é big data.** ~400 papéis na B3 × ~2.500 pregões em 10 anos = ~1 milhão de
linhas, algumas centenas de MB com índices. Tabela pequena para PostgreSQL. Mesmo com todas
as ações do mundo (~50 mil papéis, ~125 milhões de linhas), continua território confortável
com particionamento por data. O que viraria big data é dado tick a tick, fora de escopo.

**A separação bronze / prata / ouro está certa — por linhagem, não por volume**, e resolve
diretamente o requisito de auditoria. Implementada como **esquemas dentro do próprio
PostgreSQL**:

| Esquema | Camada | Conteúdo | Quem consulta |
|---|---|---|---|
| `core` | nenhuma — é o dado operacional | organização, usuário, e depois carteiras, limites e chaves de API | a aplicação |
| `bronze` | **Bronze** | o que o provedor devolveu, cru, imutável, com data e hora da coleta | ninguém na tela; existe para provar e reprocessar |
| `silver` | **Prata** | o catálogo de ativos — uma linha por ação negociada, mais o Ibovespa —, os preços diários limpos e conformados, com retorno logarítmico, e os eventos corporativos; as companhias abertas da CVM e os balanços trimestrais conformados delas, um por (companhia, data de referência); os comunicados à CVM (fatos relevantes, comunicados ao mercado e avisos aos acionistas), só na versão corrente; e depois validação | base de trabalho |
| `gold` | **Ouro** | métricas de comportamento, séries de VaR, backtests, indicadores fundamentalistas por ação e a comparação deles com os pares, agregados de carteira | é o que a plataforma serve |

Os quatro esquemas existem desde a primeira migration do F4. O `core` é esquema à parte
porque dado operacional não é camada de linhagem, e empurrá-lo para dentro de `bronze` ou de
`gold` mentiria sobre a origem dele
([D-37](decisoes/D-37-esquema-core-para-dado-operacional.md)). Os identificadores ficam em
inglês — `silver` e `gold`, e não `prata` e `ouro` —, ainda que o texto siga chamando as
camadas pelos nomes em português ([D-40](decisoes/D-40-identificadores-de-esquema-em-ingles.md)).
O `public` guarda o encanamento do Django: `django_migrations`, `auth_*`, `django_content_type` e
`django_session`
([D-38](decisoes/D-38-public-guarda-o-encanamento.md)).

### Por que a camada bronze é obrigatória aqui

**O histórico de preços é reescrito retroativamente.** Quando uma empresa paga dividendo ou
desdobra ações, o provedor recalcula todo o histórico anterior daquele papel. O fechamento
do ITUB4 em março de 2020 que o Yahoo entrega hoje **não é o mesmo** que entregaria daqui a
seis meses.

Guardando só o preço ajustado, os resultados históricos mudam sozinhos e um número calculado
hoje não pode ser reproduzido depois. Para uma plataforma que quer gerar evidência auditável
— e para um TCC que precisa de resultados reproduzíveis — isso é grave.

### Caminho de crescimento

Sem trocar de banco: **TimescaleDB** (extensão do próprio Postgres, com particionamento,
compressão e agregados contínuos) ou **DuckDB + Parquet** para análise pesada. Decisões
futuras, tomáveis quando houver evidência de necessidade.

Ver [D-13](decisoes/D-13-camadas-bronze-prata-ouro.md).

---

## Isolamento por organização

Existe a entidade **Organização** desde a primeira migration; todo usuário pertence a uma;
conta individual ganha organização pessoal implícita, invisível na interface.

| Compartilhado entre todos | Privado da organização |
|---|---|
| Catálogo de ativos | Carteiras |
| Preços históricos | Limites e alertas |
| Análise de comportamento por ação | Usuários |
| Risco e backtests por ação | Chaves de API |

O risco do ITUB4 é o mesmo para todo mundo — não faz sentido calcular por cliente. A
superfície de isolamento é pequena.

**O que isola não é a coluna, é a consulta filtrar.** Uma classe base **vai aplicar** o filtro
por organização por padrão, para que esquecer deixe de ser possível. Coluna sem filtro
automático é teatro: um dia alguém esquece e um cliente vê dado de outro.

**Ela ainda não existe.** O F4 entregou a coluna — o `organization` obrigatório do usuário —,
e o mecanismo é obrigação do bloco que criar a primeira tabela privada de domínio, a carteira
no M2.2, onde há contra o que prová-lo. O `user` é exceção permanente: os backends de
autenticação do Django alcançam o modelo por `_default_manager`, e a busca no login é anterior
a saber a que organização a pessoa pertence — então o M2.1 isola a listagem de usuário por outro
meio, e não pelo ORM ([D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md)): toda
consulta de usuário da gestão parte de `_org_users(actor)`, em `apps/accounts/services.py`, que filtra
pela organização de quem pede. `core.access_event` é privada e não tem filtro automático porque
nenhuma rota a lê; o filtro é do primeiro bloco que a ler
([D-104](decisoes/D-104-auditoria-de-acesso-em-core-access-event-restringe-a-d-41.md)).

Ver [D-08](decisoes/D-08-dono-do-dado-no-schema.md),
[D-24](decisoes/D-24-organizacao-desde-a-primeira-migration.md),
[D-41](decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md).

---

## Execução e fila

**Celery + Redis.** O Redis faz três trabalhos, reduzindo peças em vez de somar:

1. **Corretor de fila** — distribui pedidos de cálculo aos workers
2. **Cache** — resultado recente não recalcula
3. **Canal de progresso** — onde o worker publica "modelo 4 de 9 terminou"

O Celery também resolve o que será necessário de qualquer forma: repetição em falha,
cancelamento e **agendamento**, que é o que a ingestão diária exige.

### Modo A na prática

O pedido vira um **grupo de tarefas independentes, uma por algoritmo**. Os rápidos terminam
em segundos e gravam resultado; os de ML gravam conforme terminam. A tela consulta o estado
e vai preenchendo.

**Como o M1.5 construiu isso.** Uma tarefa por (ativo, **modelo**), cada uma gravando os seus
dois níveis em transação própria
([D-67](decisoes/D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md)); a
`risk_run` nasce no worker como `running`
([D-71](decisoes/D-71-a-risk-run-nasce-no-worker.md)), e um `chord` fecha o grupo lendo o
banco e escrevendo `ok`, `partial` ou `failed`
([D-70](decisoes/D-70-a-tarefa-nunca-levanta-e-o-fecho-le-o-banco.md),
[D-72](decisoes/D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md)). **O estado
mora no banco, não no Redis** ([D-68](decisoes/D-68-o-estado-da-execucao-mora-no-banco.md)):
o canal de progresso do item 3 acima não foi construído, e a tela conta as linhas gravadas.

**Atualização da tela por consulta periódica** (~2 segundos), não WebSocket. Para uma
operação de minutos, 2 segundos de atraso é irrelevante, e evita Django Channels e
infraestrutura extra. Trocar depois é fácil.

Ver [D-07](decisoes/D-07-resposta-progressiva-modo-a.md),
[D-14](decisoes/D-14-celery-e-redis.md).

---

## Rastreabilidade e auditoria

### Manifesto de execução

Um número de risco não significa nada sozinho. "VaR de 4,2%" só é interpretável,
reproduzível e auditável acompanhado de:

- qual algoritmo, e **em qual versão do código**
- quais hiperparâmetros (janela, camadas, número de simulações)
- qual base de dados, incluindo a **data de coleta**
- qual semente aleatória
- quando rodou, e a pedido de quem

É parte do modelo de domínio, não um log paralelo.

**O que previne:** se alguém mudar a janela da LSTM de 20 para 30 dias, todos os números
anteriores passam a ser de outro modelo — e sem versionamento isso acontece em silêncio,
tornando o histórico incomparável sem ninguém perceber.

### Imutabilidade

**Nunca se atualiza um resultado.** Recalculou? É execução nova, com manifesto novo. O
histórico é uma pilha de fatos que só cresce. Isso elimina a pergunta mais difícil de
auditoria — "quem alterou este número?" — porque ninguém altera nada.

| O que auditar | Como |
|---|---|
| **Dado** — de onde veio, quando foi coletado | camada bronze |
| **Cálculo** — o que produziu cada número | manifesto de execução, imutável |
| **Acesso e alteração** — quem viu o quê, quem mudou permissão | registro no nível da API + histórico nas tabelas sensíveis |

Só o terceiro precisa de mecanismo dedicado.

Ver [D-15](decisoes/D-15-manifesto-de-execucao.md),
[D-16](decisoes/D-16-resultado-e-imutavel.md).

---

## Laboratório e produção

**Esta é a decisão de arquitetura mais importante do projeto.** Sem ela, o produto seria
inviável.

Uma rede neural tem duas fases com custos separados por ordens de grandeza:

- **Treinar** — olha 10 anos de histórico repetidas vezes até aprender o padrão: **minutos**
- **Prever** — a rede treinada olha os últimos 20 dias e responde: **milissegundos**

É como estudar para uma prova e responder uma questão. Estuda-se uma vez, responde-se mil
vezes.

### Regime de laboratório

Os 20–60 minutos por experimento são deste regime: provar cientificamente que o modelo
funciona ao longo de uma década. Simula o passado dia a dia, retreina a cada ano de teste, e
faz busca de hiperparâmetros — 8 treinos completos por modelo. Roda algumas vezes na vida.

### Regime de produção

**Não repete o treino que já fez.** Cada modelo caro (`lstm`, `gru`, `garchnet`, `caviar`)
guarda um **retrato** do estado treinado em cada ponto de retreino, em `gold.model_snapshot`
([D-77](decisoes/D-77-os-retratos-moram-em-gold-com-impressao-digital-estrita.md)). A rotina
diária reaproveita os retratos válidos, treina só o que falta e **reconstitui a série inteira
do backtest por previsão** — igual, número a número, ao cálculo do zero
([D-78](decisoes/D-78-incremental-igual-ao-do-zero-e-full-e-a-referencia.md)). Os cinco modelos
baratos refazem o backtest inteiro, porque custa menos que guardar estado
([D-79](decisoes/D-79-os-quatro-caros-usam-retratos-e-os-cinco-baratos-nao.md)).

| Quando | O que roda | Custo |
|---|---|---|
| **Todo dia útil** | busca preços novos; reconstitui a série do backtest dos modelos caros por previsão, a partir dos retratos; refaz os cinco baratos | segundos por ativo — 4,5 a 10,3 s no fecho do M1.5b |
| **A cada 252 pregões** — o ponto de retreino do protocolo, quando a série o cruza | um retreino por (modelo caro, nível), a partir do retrato anterior | uma fração do cálculo completo — não medido em dado real |
| **Ativo novo, ou retrato invalidado** — preço já visto mudou, ou mudou a versão do motor ou de biblioteca | busca de configuração e todos os retreinos, do ponto invalidado em diante | ~2,5 min por ativo, se desde a posição 0 — 141 a 175 s no fecho do M1.5b |

A cadência é a do backtest do motor, não "semanal ou mensal": qualquer outra quebraria a
igualdade com o backtest
([D-80](decisoes/D-80-o-retreino-de-producao-e-a-cada-252-pregoes-restringe-a-d-18.md), que
restringe a D-18).

Quando o usuário pesquisa um ativo coberto, **a resposta já está no banco.**

### Cobertura em camadas

A B3 tem ~400 papéis, mas a maioria quase não é negociada.

- **Ativos cobertos** — os líquidos, os que as pessoas pesquisam. Pré-calculados, resposta
  imediata.
- **Cauda longa** — papel fora da lista entra pelo modo A: estatísticos em segundos, ML na
  fila preenchendo a tela. Dali em diante o ativo passa a ser coberto.

O modo A é **exceção de primeira consulta**, não a regra.

### A carteira é o caso realmente dinâmico

Não há como pré-calcular: a combinação de pesos que o usuário montou nunca existiu. É onde o
modo A vale de verdade, e onde o cache importa — mexer pouco nos pesos deve reaproveitar
boa parte do trabalho.

Ver [D-18](decisoes/D-18-separacao-treino-previsao.md),
[D-19](decisoes/D-19-cobertura-de-ativos-em-camadas.md).

---

## Ambientes

**Local: um comando.** `docker compose up`, na raiz, sobe **seis serviços**: Postgres, Redis,
web, worker, beat e frontend. Não é conforto — evita "na minha máquina funciona" num time de 4
pessoas com sistemas diferentes, e faz alguém novo produzir no primeiro dia.

O frontend está entre eles porque é a peça com o pré-requisito mais frágil do repositório —
exige Node 24.15+, e deixá-lo fora contradiria as duas razões acima
([D-32](decisoes/D-32-frontend-no-compose.md)).

**O dia a dia de `backend/` e `frontend/` — servidor, teste, verificação de tipos — roda
dentro do contêiner**; o `engine/` continua no ambiente virtual nativo, por ser pacote
independente que não fala com serviço nenhum
([D-33](decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)). **Na CI isso vale para dois dos
quatro trabalhos:** `backend` e `frontend` rodam dentro das imagens, porque executam a
aplicação e o ambiente decide o resultado; `estilo` e `motor` rodam direto no runner, porque
não executam a aplicação e a única imagem que conteria o `engine/` é a `worker`, de 3,79 GB
([D-43](decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)).

**CI**: `.github/workflows/ci.yml`, no GitHub Actions, disparado a cada pull request, a cada
push na `main` e à mão. Quatro trabalhos — `estilo`, `backend`, `frontend` e `motor` — cobrindo estilo, tipos e
testes. A ferramenta de estilo é o `ruff` nos dois projetos Python e o `@biomejs/biome` no
frontend, uma por lado, cada uma fazendo lint **e** formatação
([D-43](decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)).

**Não passou, não entra.** Todo bloco entra na `main` por PR
([D-82](decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md)), e PR com CI vermelha
não é aprovada ([D-83](decisoes/D-83-a-ci-barra-na-pr.md), que substitui a D-42). O
barramento automático depende da proteção da `main` no GitHub, que é configuração do
repositório. Se a `main` ficar vermelha, conserta quem fez o último merge.

O trabalho `motor` roda a suíte **sem** a linha de base numérica: ela foi capturada no
Windows e não é portátil entre plataformas — 8 das 64 reprovam num Linux limpo, com o EGARCH
caindo em outro ótimo local de uma superfície quase plana. Está registrado como dívida no
[ESTADO.md](ESTADO.md); o ajuste que não convergia em Linux foi corrigido pela
[D-46](decisoes/D-46-ajuste-garch-tenta-de-novo-quando-nao-converge.md).

**Produção**: forma definida (web + worker + beat + Postgres + Redis); hospedagem em aberto.
O **beat** é o agendador do Celery, **um só por ambiente** — dois duplicariam cada disparo.
Não calcula: agenda o catálogo, os preços, a coleta dos fundamentos na CVM e a dos
comunicados; o recálculo do
risco vem encadeado aos preços, e o cálculo dos indicadores fundamentalistas, à coleta
([D-69](decisoes/D-69-o-agendamento-e-encadeado.md)). Usa a mesma imagem do worker, porque
importa as tarefas de app, que chegam no motor. Os horários são variáveis de ambiente
(`RUVOR_BEAT_ASSETS_CRON`, `RUVOR_BEAT_PRICES_CRON`, `RUVOR_BEAT_FUNDAMENTALS_CRON`,
`RUVOR_BEAT_DISCLOSURES_CRON`), e o
valor de produção depende da hospedagem.
Inclinação para PaaS (Render/Railway, ~US$ 20–50/mês) em vez de VPS — o time não tem
capacidade de operação sobrando, e essas horas sairiam do produto.

> **Ressalva:** o worker precisa de 2–4 GB de RAM; o TensorFlow sozinho ocupa 1–2 GB.
> Camada gratuita não serve.

### Execução dos experimentos do TCC

**CPU, 4 processos em paralelo (um por ativo), dentro de container, na mesma máquina.** ~1
hora.

O time tem RTX 3060 Ti e RTX 5060, ambas em Windows — e o TensorFlow não usa GPU no Windows
nativo desde a versão 2.11. Existem saídas (Keras 3 sobre PyTorch, que tem CUDA nativo no
Windows; ou WSL2), mas **provavelmente não valem a pena**: as redes são minúsculas (16–32
unidades, janela de 20 dias, lotes de 32), e GPU brilha com matriz e lote grandes. O que
provavelmente domina o tempo é a quantidade de chamadas pequenas em sequência, não conta
pesada — e isso se resolve paralelizando, de graça.

**Tarefa de investigação pendente:** medir onde o tempo está indo antes de investir em
qualquer mudança de ambiente.

Uma máquina só, e não quatro: se cada ativo rodar numa máquina diferente e o ranking mostrar
diferença, **não é possível afirmar se veio do modelo ou da máquina** — o que destrói a
comparabilidade que o TCC tenta provar.

Ver [D-20](decisoes/D-20-experimentos-em-cpu.md),
[D-21](decisoes/D-21-motor-ml-congelado-ate-etapa-6.md),
[D-22](decisoes/D-22-treino-centralizado-em-container.md).

---

## Restrições que independem de escolha

Propriedades do problema, não do código.

**O custo dos algoritmos é assimétrico.** Estatísticos resolvem em segundos; redes neurais
precisam ser treinadas, o que leva minutos em qualquer implementação e qualquer linguagem.

**O motor pesado não pode viver no processo web.** TensorFlow passa de meio giga e ocupa CPU
por minutos. A arquitetura tem no mínimo duas peças — web (leve) e worker (pesado) —
conversando por fila. Independe do framework escolhido.

**O histórico de preços é reescrito retroativamente.** Ver a camada bronze, acima.

**A carteira exige tratar correlação.** Ver [PRODUTO.md](PRODUTO.md#6-restrições-de-produto).
