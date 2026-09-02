# F3 — Ambiente local

**Bloco:** Fundação · F3
**Status:** ✅ **aprovada** (2026-09-02) — pronta para o plano. Quatro rodadas de revisão adversarial; a última sem achado grave.
**Depende de:** [F2b — Casco da aplicação](F2b-casco-da-aplicacao.md)

---

## Problema

O F2b deixou dois processos que sobem, mas cada um exige a máquina certa e um ritual próprio.
Hoje, para ver a aplicação de pé, é preciso:

- ter Python 3.12+ e criar o `.venv/` da raiz, com dois `pip install -e`
- ter **Node 24.15+**, que nesta máquina não é o Node global — vem por `fnm`, porque o Node
  20.11 do PATH é usado por outro projeto
- exportar `RUVOR_SECRET_KEY` no shell — sem ela o processo nem sobe —, e na prática também
  `RUVOR_DEBUG` e `RUVOR_ALLOWED_HOSTS`, que têm padrão mas cujo padrão não serve para
  desenvolvimento, porque **nada carrega o `.env`** (o próprio `.env.example` diz isso e
  aponta para o F3)
- subir dois servidores em dois terminais

Além do ritual, o que falta é infraestrutura. Não existe Postgres nem Redis em lugar nenhum
do repositório — e sem eles:

- o **F4** não tem onde criar migrations
- a [D-14](../decisoes/D-14-celery-e-redis.md) (Celery + Redis) é promessa não verificada
- a [D-17](../decisoes/D-17-monorepo-engine-sem-django.md), que promete "duas imagens Docker
  do mesmo código: `web` leve, `worker` pesado", não tem uma única imagem construída para
  provar que o processo web não carrega TensorFlow

A [ARQUITETURA](../ARQUITETURA.md#ambientes) já diz o alvo: *"Local: um comando.
`docker compose up` sobe Postgres, Redis, web e worker. Não é conforto — evita 'na minha
máquina funciona' num time de 4 pessoas com sistemas diferentes, e faz alguém novo produzir
no primeiro dia."*

## Resultado esperado

1. Um comando sobe a aplicação inteira, e todos os serviços chegam a estado saudável
2. **Para subir a aplicação e trabalhar em `backend/` ou `frontend/`**, quem chega não precisa instalar Python, Node, Postgres nem Redis na máquina — só Docker. Mexer no **motor** continua exigindo Python e o `.venv/` da raiz, pelo motivo em [divisão de casas](#o-dia-a-dia-passa-a-ser-dentro-do-contêiner)
3. O Django conecta no Postgres — sem migrations e sem modelos, mas conectando de verdade
4. Uma tarefa enfileirada pela web é executada pelo worker e o resultado volta
5. A imagem `web` **não** consegue importar TensorFlow; a `worker` consegue
6. O navegador abre o frontend em contêiner, e ele alcança o backend

## Escopo

### Dentro

- Arquivo de composição e `.dockerignore` **na raiz do repositório**, e diretório `infra/` com os arquivos de construção de imagem — a colocação é decidida e justificada em [Por que dois dos quatro arquivos ficam na raiz](#por-que-dois-dos-quatro-arquivos-ficam-na-raiz)
- Serviços: **Postgres, Redis, web, worker e frontend**
- Duas imagens do backend a partir do mesmo fonte: `web` (leve) e `worker` (pesada)
- Celery instalado e ligado ao Redis, com **uma tarefa de fumaça** — sem tarefa de domínio
- Conexão do Django ao Postgres, sem migrations nem modelos
- Carga do `.env` pelo `compose`
- Portas do hospedeiro configuráveis
- Execução de teste e de verificação de tipos dentro do contêiner
- Pagamento da dívida do `RUVOR_ALLOWED_HOSTS` registrada em [ESTADO.md](../ESTADO.md)
- Atualização do `README.md` e do `.env.example`

### Fora

| Fora do escopo | Onde entra |
|---|---|
| Migrations, modelos, esquemas bronze/prata/ouro | F4 |
| Qualquer tarefa Celery de domínio, fila de risco, modo A | M1.5 |
| Integração contínua | F5 |
| Imagem e configuração de **produção** | quando houver hospedagem decidida |
| Contêiner de treino reprodutível da [D-22](../decisoes/D-22-treino-centralizado-em-container.md) | trilha do TCC — ver [riscos](#o-contêiner-de-treino-da-d-22-não-é-este) |
| Qualquer app de domínio, endpoint de negócio ou tela de produto | Marco 1 |
| Ferramenta de estilo (`ruff`, `prettier`, `eslint`) | F5 — ver [ESTADO.md](../ESTADO.md#aberto-e-aguardando-decisão) |
| Backup, réplica ou ajuste de desempenho do Postgres | nada previsto; não é necessidade deste projeto |

---

## Requisitos

| ID | Requisito |
|---|---|
| **F3-01** | Um comando sobe Postgres, Redis, web, worker e frontend, e os cinco chegam a estado saudável |
| **F3-02** | Duas imagens do backend nascem do mesmo fonte: `web` sem as dependências de ML, `worker` com elas |
| **F3-03** | Verificação automatizada de que `import tensorflow` **falha** na imagem `web` e **funciona** na `worker` |
| **F3-04** | O Django conecta no Postgres a partir do contêiner `web`, sem migrations e sem modelos |
| **F3-05** | Uma tarefa enfileirada pelo `web` é executada **pelo processo do `worker`** e o resultado é lido de volta |
| **F3-06** | `docker compose up` na raiz lê o `.env`; nenhuma variável precisa ser exportada no shell |
| **F3-07** | O frontend em contêiner é alcançável pelo navegador do hospedeiro e encaminha `/health` para o `web` |
| **F3-08** | Toda porta publicada no hospedeiro é configurável por variável, sem editar o `compose.yaml` |
| **F3-09** | Teste e verificação de tipos **do backend e do frontend** rodam dentro do contêiner, com comandos documentados |
| **F3-10** | `RUVOR_ALLOWED_HOSTS` tolera espaço após a vírgula (dívida registrada no F2b) |
| **F3-11** | `README.md` e `.env.example` descrevem o caminho novo, e o antigo não fica mentindo |

---

## Contratos externos

Congelados a partir da aprovação. O F4 consome a conexão de banco e o Celery; o F5 consome
as imagens e os comandos de verificação.

### Serviços e nomes de rede

Cinco serviços. **O nome do serviço é o nome de host dentro da rede do `compose`** — é assim
que o `web` acha o Postgres.

| Serviço | Imagem | Papel |
|---|---|---|
| `postgres` | oficial do PostgreSQL, **versão maior fixada** | banco |
| `redis` | oficial do Redis, **versão maior fixada** | corretor de fila, cache e canal de progresso ([D-14](../decisoes/D-14-celery-e-redis.md)) |
| `web` | `infra/backend.Dockerfile`, alvo `web` | Django, servidor de desenvolvimento |
| `worker` | `infra/backend.Dockerfile`, alvo `worker` | Celery |
| `frontend` | `infra/frontend.Dockerfile` | servidor de desenvolvimento do Vite |

As três nomeiam o **arquivo** de construção. O **contexto** é outra coisa, e é a raiz do
repositório em todos os casos — ver [Estrutura criada](#estrutura-criada).

**As imagens construídas recebem nome explícito** — `ruvor-web`, `ruvor-worker` e
`ruvor-frontend` —, em vez de aceitar o nome que o Compose deriva do diretório do projeto.
F3-02 e F3-03 precisam invocar as imagens por nome, e nome derivado muda se alguém renomear a
pasta do repositório ou usar outro nome de projeto: critério de aceite que quebra por causa
disso reprova sem causa real.

**Nenhuma imagem usa a etiqueta `latest`.** A versão maior é fixada explicitamente, para que
a construção de hoje e a de daqui a seis meses produzam a mesma coisa — é a mesma razão que
sustenta a camada bronze e o manifesto de execução. **O plano confirma a etiqueta exata
consultando o registro**, e não a inventa: a escolha é a última versão maior estável no
momento da implementação.

**A versão maior do Postgres não é detalhe de implementação.** Ela atravessa para o F4
(migrations), para a hospedagem de produção e para o caminho de crescimento com TimescaleDB
que a [ARQUITETURA](../ARQUITETURA.md#caminho-de-crescimento) cita. Hoje não há dado nenhum,
então trocar é grátis — mas depois do F4 deixa de ser. Por isso o plano, ao fixá-la,
**registra a escolha em `docs/decisoes/`**, para que o F4 e o bloco de hospedagem a leiam em
vez de re-derivá-la do `compose.yaml`.

### Variáveis de ambiente

Prefixo `RUVOR_*` para configuração própria, conforme o F2b. As três que já existem
permanecem com o mesmo significado. As novas:

| Variável | Uso | Quem lê |
|---|---|---|
| `RUVOR_DB_HOST` | nome de host do Postgres | Django |
| `RUVOR_DB_PORT` | porta do Postgres **dentro da rede** | Django |
| `RUVOR_DB_NAME` | nome do banco | Django; o `compose` a **mapeia** para o nome que a imagem do Postgres espera |
| `RUVOR_DB_USER` | usuário | Django; **mapeada** pelo `compose`, como acima |
| `RUVOR_DB_PASSWORD` | senha | Django; **mapeada** pelo `compose`, como acima |
| `RUVOR_REDIS_URL` | endereço do Redis | Celery, como corretor **e** como depósito de resultado — ver [a ressalva](#o-depósito-de-resultado-é-do-bloco-não-do-modelo) |
| `RUVOR_PORT_WEB` | porta publicada no hospedeiro para o `web` | `compose` |
| `RUVOR_PORT_FRONTEND` | porta publicada no hospedeiro para o `frontend` | `compose` |
| `RUVOR_PORT_POSTGRES` | porta publicada no hospedeiro para o `postgres` | `compose` |
| `RUVOR_PORT_REDIS` | porta publicada no hospedeiro para o `redis` | `compose` |

Do lado do frontend, o prefixo continua sendo `VITE_*`, exigência da ferramenta:

| Variável | Uso |
|---|---|
| `VITE_API_BASE_URL` | já existe; vazia significa mesma origem, pelo proxy |
| `VITE_PROXY_TARGET` | **nova**: para onde o proxy encaminha. Vazia, mantém o valor atual — ver [o proxy](#o-proxy-do-vite-precisa-de-dois-destinos) |

`VITE_PROXY_TARGET` é **fixada pelo `compose` no próprio serviço `frontend`**, e não vem do
`.env` da raiz. O valor é um endereço interno da rede do Compose, que aponta para o serviço
`web`: não há razão para alguém configurá-lo, e expô-lo no `.env` convidaria a mexer no que
não deve. Ela existe como variável, e não como valor literal no `vite.config.ts`, apenas para
que a execução nativa continue funcionando sem configuração — que é o oposto de ser ajustável.

**O contêiner do Postgres não lê `RUVOR_*`.** A imagem oficial espera os nomes próprios dela
(`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`), então o `compose` **mapeia** os valores
do contrato para esses nomes.

Diferente das outras armadilhas desta spec, esta **falha alto**: com o diretório de dados
ainda vazio e sem `POSTGRES_PASSWORD`, o ponto de entrada da imagem recusa inicializar e sai
com erro dizendo que a senha do superusuário não foi informada. Fica registrado justamente
por isso — para que ninguém gaste critério de aceite protegendo contra um erro que já se
denuncia sozinho, e para que a regra ("mapeie os nomes") não seja generalizada no F4 como "o
Postgres ignora o que não conhece", que é falso.

**Por que porta do banco separada da porta publicada.** Dentro da rede do `compose`, o
Postgres sempre atende na porta padrão dele; `RUVOR_PORT_POSTGRES` é só o número que aparece
no hospedeiro, para uma ferramenta gráfica se conectar. Confundir os dois é o erro clássico
de quem configura `compose` pela primeira vez, e produz uma falha de conexão que parece de
rede e é de configuração.

**As portas internas não são configuráveis, e são estas:** o `web` atende em **8000** e o
`frontend` em **5173**, dentro da rede. São os valores que o F2b já usa, e ficam fixos de
propósito — o proxy do Vite e as verificações de vida dependem deles, e torná-los ajustáveis
multiplicaria a superfície de configuração sem que ninguém precise. O que varia é só o número
publicado no hospedeiro. `RUVOR_DB_PORT` é a única porta interna nomeada, porque o Django
precisa recebê-la para montar a conexão.

### Contrato da tarefa de fumaça

O F3 instala Celery, e Celery sem nenhuma tarefa não prova nada. Uma tarefa só, de
infraestrutura — **não é tarefa de domínio**, do mesmo jeito que `GET /health` não é endpoint
de negócio:

```
tarefa:    config.tasks.ping
entrada:   nenhuma
saída:     o nome de host de quem executou a tarefa
```

Mora em `backend/config/`, junto do `health`, e não em `backend/apps/` — que não existe e
nasce no F4.

A verificação atravessa o caminho inteiro: o `web` enfileira, o Redis transporta, o `worker`
executa, o resultado volta pelo Redis. É a menor prova possível da
[D-14](../decisoes/D-14-celery-e-redis.md), e é o que o M1.5 vai substituir por trabalho de
verdade.

**A tarefa devolve o nome de host, e não uma constante como `"pong"`, de propósito.** Uma
constante torna o critério aprovável sem worker nenhum: basta `task_always_eager` ligado — uma
linha, e exatamente a linha que alguém acrescenta enquanto depura por que o worker não pega a
tarefa — para o `web` executar no próprio processo e devolver a constante na hora, com o
serviço `worker` **desligado**. O caminho que a spec chama de "a menor prova possível da D-14"
não seria tocado, e F3-05 é o único critério do bloco que o sustenta.

Devolvendo o nome de host, o resultado carrega a identidade de quem executou. E como o
serviço `worker` **fixa o próprio nome de host como `worker`** — uma linha no `compose.yaml`
—, o critério pode exigir igualdade a `"worker"`, em vez de comparar dois identificadores
aleatórios e se contentar com "é outro contêiner".

Deixa de ser possível passar verde sem worker: com o modo síncrono ligado, quem executa é o
`web` e o nome de host devolvido é o dele; com o serviço `worker` derrubado, não volta
resultado nenhum.

**`task_always_eager` fica desligado**, e isso é contrato, não configuração de conveniência.

A verificação tem **tempo limite**. Sem ele, um worker que nunca consome a fila deixa o
critério esperando para sempre, o que na prática vira "alguém interrompeu e seguiu em frente"
— pior que reprovar.

### O depósito de resultado é do bloco, não do modelo

A [D-14](../decisoes/D-14-celery-e-redis.md) e a
[ARQUITETURA](../ARQUITETURA.md#execução-e-fila) enumeram **três** trabalhos para o Redis:
corretor de fila, cache e canal de progresso. Ler o retorno de uma tarefa é um **quarto**, e
esta spec o usa.

Não é mudança de modelo, e por isso não vira decisão nova: no desenho de produto, resultado
de cálculo é gravado no banco, imutável e com manifesto
([D-15](../decisoes/D-15-manifesto-de-execucao.md),
[D-16](../decisoes/D-16-resultado-e-imutavel.md)) — a tela consulta o banco, não a fila. O
depósito de resultado existe aqui **apenas para que F3-05 possa ler o retorno de `ping`**, que
é o único jeito de provar quem executou a tarefa.

Fica registrado para que o M1.5 não herde isto como padrão: quando houver cálculo de verdade,
o resultado vai para o banco.

### O comando

**`docker compose up`**, executado na raiz do repositório. Literalmente esta linha — é a que
a [ARQUITETURA](../ARQUITETURA.md#ambientes) promete, é a que o `README.md` vai ensinar, e é
a que o F5 vai espelhar na CI.

Nomear o comando não é detalhe de redação. Ele é a superfície de entrada do bloco inteiro:
se ficar implícito, quem implementa inventa uma invocação, o README ensina a invenção e o F5
a herda.

**Na primeira vez, há um passo antes:** copiar `.env.example` para `.env`. O `.env` é
ignorado pelo Git e não existe em disco; sem ele, a interpolação de portas fica vazia e o
Django não sobe.

Para que esse passo seja **só uma cópia**, e não uma edição, o `.env.example` passa a trazer
**valores de desenvolvimento que funcionam** — inclusive uma chave secreta de
desenvolvimento, no lugar do campo hoje vazio que o `_required` do `settings.py` rejeita. É
coerente com o que a spec já assume sobre [a senha em texto claro](#a-senha-do-banco-fica-em-texto-claro-no-env):
o arquivo é de ambiente local, e não tem segredo real a proteger.

Sem isso, "um comando" seria propaganda: quem chega esbarraria num erro de variável ausente
antes de ver qualquer coisa de pé.

**As verificações usam a variante desanexada** (`up -d`), porque F3-01, F3-06 e F3-08 precisam
subir e depois consultar. A linha canônica — a que o README ensina e o F5 espelha — continua
sendo `docker compose up`.

### Estrutura criada

```
compose.yaml     <- na RAIZ: servicos, rede, volumes, verificacoes de vida
.dockerignore    <- na RAIZ: o que nao entra no contexto de construcao
infra/
├── backend.Dockerfile    dois alvos a partir do mesmo fonte: web e worker
└── frontend.Dockerfile   Node com o servidor de desenvolvimento do Vite
```

**O contexto de construção é a raiz do repositório**, não `infra/`. A imagem do backend
precisa de `engine/` e de `backend/`; a do frontend precisa de `frontend/` **e** de
`brand/ruvor/`, porque o apelido `@brand` do `frontend/vite.config.ts` resolve para fora da
raiz do frontend.

### Por que dois dos quatro arquivos ficam na raiz

Não é preferência de organização. Os dois falhariam **em silêncio** dentro de `infra/`:

| Arquivo | O que aconteceria em `infra/` |
|---|---|
| `.dockerignore` | O Docker procura o arquivo **na raiz do contexto de construção**. Com o contexto na raiz, um arquivo chamado `infra/.dockerignore` fica inerte: `.venv/` — **2,1 GB, com TensorFlow e Keras dentro** —, `frontend/node_modules/`, `.git/` e `docs/tcc/` são enviados ao daemon a cada construção. O sintoma é "a construção demora muito" — nunca um erro |
| `compose.yaml` | O Compose descobre o `.env` no **diretório do projeto**, que por padrão é o diretório do arquivo de composição. Com ele em `infra/`, o `.env` da raiz não alimenta a interpolação de `${RUVOR_PORT_*}`, e F3-08 subiria com portas vazias |

> **Precisão sobre o `.dockerignore`.** Existe um segundo mecanismo: o BuildKit também aceita
> um arquivo irmão do arquivo de construção, nomeado a partir dele — aqui seria
> `infra/backend.Dockerfile.dockerignore`. Ou seja, "em `infra/` seria necessariamente
> inerte" é forte demais como regra geral; é verdade para o **nome** `.dockerignore`, que é o
> que alguém naturalmente escreveria. A estrutura escolhida evita a armadilha e tem uma
> vantagem que o outro caminho não tem: **um arquivo só serve às duas construções**, em vez
> de dois que divergem.

Sobre o `compose.yaml`, vale dizer o que a tabela não diz: com o arquivo em `infra/`, o
próprio `docker compose up` na raiz não encontra composição nenhuma. F3-06 quebraria antes de
F3-08, e de forma total. A falha só seria parcial — e portanto confusa — para quem invocasse
o Compose apontando o caminho à mão, que é exatamente o hábito que este arranjo elimina.

Além disso, `compose.yaml` na raiz é o que faz `docker compose up` funcionar sem argumento
nenhum. Com o arquivo em `infra/`, o comando viraria
`docker compose -f infra/compose.yaml --env-file .env up` — que ninguém digita duas vezes
igual, e que contradiz a linha que a ARQUITETURA promete.

**`infra/` continua existindo e continua sendo o diretório de infraestrutura** — guarda os
arquivos de construção de imagem, e o F5 lhe acrescenta a parte de CI. O que muda em relação
ao diagrama da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) é que o `compose`
não mora lá dentro. Fica registrado como
[divergência declarada](#decisões-novas-que-este-bloco-produz).

---

## As duas imagens

A [D-17](../decisoes/D-17-monorepo-engine-sem-django.md) promete `web` leve e `worker`
pesado. O F3 é onde a promessa vira artefato verificável.

| | `web` | `worker` |
|---|---|---|
| Instala `backend/` | sim, **com o extra de desenvolvimento** | sim, **com o extra de desenvolvimento** |
| Instala `engine/` | **não** | sim, com `[traditional,garch,ml]` |
| TensorFlow presente | **não** | sim |
| Executa | servidor de desenvolvimento do Django | Celery |
| Roda a suíte e o mypy do backend (F3-09) | **sim** | não |

**As duas imagens são de desenvolvimento**, e por isso trazem o extra que declara pytest,
pytest-django, mypy e django-stubs.

Na `web` isso é exigência de F3-09, que não teria onde rodar sem ele — mesmo raciocínio que
obriga a
[imagem do frontend a carregar as dependências de desenvolvimento](#a-imagem-do-frontend-carrega-as-dependências-de-desenvolvimento).
Na `worker`, é escolha de simetria: as duas saem do mesmo estágio base, e diferenciá-las
também nas ferramentas de desenvolvimento criaria uma terceira variante para economizar
poucos megabytes numa imagem que já carrega TensorFlow. **Não enxugue a `worker` achando que
a spec pede** — o que a spec separa entre as duas é o motor e o ML, nada mais.

**A suíte do backend roda no `web`.** Escolha deliberada, e não indiferença: a `web` é a
imagem enxuta, e rodar os testes nela mantém a suíte honesta sobre o que o processo web tem
de fato. Rodá-los no `worker`, que carrega tudo, deixaria passar um teste que só funciona
porque o motor está instalado — regressão silenciosa contra a
[D-17](../decisoes/D-17-monorepo-engine-sem-django.md).

Imagem enxuta de produção, sem ferramenta de teste, é outro artefato e está
[fora do escopo](#fora) junto com o resto de produção.

**Por que o `web` não instala `engine/` de forma alguma**, em vez de instalar sem o extra de
ML: um extra é fácil de acrescentar de passagem, e a regra da D-17 é estrutural, não uma
questão de tamanho de imagem. Ausência total é mais fácil de verificar e mais difícil de
erodir. Quando o Marco 1 precisar de tipos compartilhados entre web e motor, isso vira
decisão explícita — não um efeito colateral.

**F3-03 é o teste que dá dente à D-17.** Uma imagem em que `import tensorflow` funciona no
processo web é exatamente a regressão que a decisão quer impedir, e hoje nada a detecta. A
verificação precisa cobrir os **dois** lados: sem o lado positivo (`worker` importa), um erro
de construção que produzisse duas imagens vazias passaria verde.

**Ambos os alvos saem do mesmo arquivo de construção**, com estágio base compartilhado. Dois
arquivos separados divergiriam na versão do Python — e aí "o mesmo código" deixaria de ser
verdade.

---

## O Django conecta no banco

**Esta spec decide que o F3 conecta**, e não apenas sobe o contêiner do Postgres ao lado.

O F2b deixou `DATABASES` vazio de propósito, com um teste que prova a ausência de banco:
`backend/tests/test_health.py::test_processo_nao_tem_banco`, que exige `ImproperlyConfigured`
em `connection.cursor()`. Esse teste **é removido e substituído** por um que prova o inverso.

Por que conectar agora, e não no F4:

- Um "ambiente local" em que o banco sobe mas ninguém fala com ele não prova ambiente
  nenhum. O que quebra na vida real é a configuração da conexão e a ordem de subida, não o
  contêiner do Postgres — e as duas coisas só aparecem quando alguém conecta.
- O F4 vai criar migrations. Se ele tiver que criar **e** configurar a conexão, um `makemigrations`
  que falha não diz qual dos dois está errado.
- É barato: driver, cinco variáveis e nenhum modelo.

**Sem migrations e sem modelos.** `INSTALLED_APPS` não ganha app novo. Se `python manage.py migrate`
funcionar de passagem, é efeito colateral dos apps embutidos do Django, não escopo desta spec
— e o F3 não o executa como critério.

### O que acontece com `settings_test.py`

`backend/config/settings_test.py` preenche `RUVOR_SECRET_KEY` e `RUVOR_ALLOWED_HOSTS` porque
o pytest-django chama `django.setup()` antes de qualquer `conftest.py` — armadilha já
registrada em [aprendizados](../aprendizados.md). Ele passa a precisar também das variáveis
de banco, e **continua sendo o único lugar que roda cedo o bastante**.

Consequência declarada: a suíte do backend passa a exigir um Postgres alcançável. É coerente
com F3-09 — a suíte roda dentro do contêiner, onde o Postgres existe.

**Cuidado que o formato do arquivo impõe.** `settings_test.py` usa preenchimento por omissão:
ele só fornece valor quando a variável **falta**. Se os valores de banco que ele fornecer
coincidirem com os do `compose`, um `.env` incompleto passa despercebido — o teste conecta
pelo valor de reserva e F3-04 aprova, provando "existe um Postgres" em vez de "a configuração
do `.env` alcança o Postgres", que é a frase que sustenta a escolha do mecanismo.

Portanto: os valores de reserva de banco em `settings_test.py` existem **apenas** para que o
mypy e a importação do módulo funcionem, e **não podem coincidir** com a configuração real do
`compose`.

---

## O dia a dia passa a ser dentro do contêiner

Decisão desta spec, e a que mais muda o hábito de quem trabalha no projeto.

| O quê | Onde roda | Por quê |
|---|---|---|
| `backend/` — servidor, teste, tipos | **contêiner** | passa a depender de Postgres e Redis; rodar nativo exigiria instalá-los na máquina, que é exatamente o que este bloco elimina |
| `frontend/` — servidor, teste, tipos | **contêiner** | a versão do Node deixa de depender da máquina; nesta, o Node 24 só existe por `fnm`, e o global é 20.11 de outro projeto |
| `engine/` — teste, tipos, `ruvor run` de desenvolvimento | **`.venv/` nativo** | é pacote independente e não fala com serviço nenhum: subir Postgres e Redis para rodar a suíte do motor seria custo sem contrapartida |

> **Isto não contradiz a [D-22](../decisoes/D-22-treino-centralizado-em-container.md).** Ela
> decide que **o treino dos experimentos** roda em contêiner, numa máquina só, com semente
> fixa — para que o ranking não dependa da máquina. A linha acima trata de outra coisa:
> execução de **desenvolvimento** do motor (rodar a suíte, verificar tipos, disparar um
> experimento curto para ver se o código funciona). Essa nunca esteve sob a D-22, e continua
> nativa.
>
> A execução que a D-22 governa **não acontece neste bloco** e não ganha casa aqui — ver
> [o risco correspondente](#o-contêiner-de-treino-da-d-22-não-é-este).

**Cada coisa tem uma casa só.** A alternativa — manter os dois caminhos para tudo, com o
contêiner "como referência" — obrigaria a um critério que prova que os dois concordam,
e sem ele seria só ambiguidade documentada. Não é proibido subir o Django nativo; deixa de
ser o caminho documentado.

### O código do backend é montado, não assado na imagem

`backend/` vem do hospedeiro por montagem nas duas imagens, como o `frontend/`. `engine/` é
montado **apenas no `worker`** — a `web` não o instala e não deve enxergá-lo, porque montar o
diretório ali abriria caminho para um `import engine` acidental que a
[D-17](../decisoes/D-17-monorepo-engine-sem-django.md) proíbe e que F3-03 não pegaria (o
teste olha TensorFlow, não o motor). A instalação
editável (`pip install -e`) acontece na construção da imagem e aponta para o ponto de
montagem, de modo que editar um arquivo no editor do hospedeiro tenha efeito no próximo
recarregamento do servidor.

**Sem isso, a decisão acima não se sustenta**: com o código assado na imagem, cada edição
exigiria reconstruir, e "o dia a dia roda dentro do contêiner" seria inviável na prática. É o
tipo de detalhe que parece de implementação e na verdade decide se o bloco entrega o que
promete.

O `.venv/` da raiz **continua existindo e continua sendo instalado** — o motor depende dele,
e o `pip install -e "./backend[dev]"` segue útil para o editor resolver importação e para o
verificador de tipos do editor funcionar. O que muda é qual execução vale.

O F5 herda esta decisão: a CI espelha o contêiner, não o `.venv`.

---

## O frontend em contêiner

A [ARQUITETURA](../ARQUITETURA.md#ambientes) lista quatro serviços e não menciona o frontend.
Esta spec acrescenta o quinto, pelo motivo que a própria ARQUITETURA dá para existir o
`compose`: *"evita 'na minha máquina funciona'"* e *"faz alguém novo produzir no primeiro
dia"*.

Deixar o frontend fora contradiz os dois. Ele é hoje **a peça com o pré-requisito mais
frágil** de todo o repositório: exige Node 24.15+, travado por `engine-strict` em
`frontend/.npmrc`, numa máquina cujo Node global é 20.11 e não pode ser trocado. O
[aprendizado sobre `engine-strict`](../aprendizados.md) existe justamente porque essa
armadilha já custou tempo uma vez.

Fica registrado como decisão nova, porque diverge de documento vivo.

### O proxy do Vite precisa de dois destinos

`frontend/vite.config.ts` tem hoje `proxy: { "/health": "http://127.0.0.1:8000" }` —
literal. Dentro da rede do `compose`, o Django não está em `127.0.0.1`; está no host `web`.

O destino passa a vir de `VITE_PROXY_TARGET`, **com o valor atual como padrão**. Assim o
`compose` aponta para o serviço `web`, e quem rodar nativo não precisa configurar nada — o
comportamento do F2b é preservado sem variável definida.

> O `vite.config.ts` roda **antes** de o Vite carregar arquivos `.env`, e não recebe as
> variáveis `VITE_*` automaticamente como o código da aplicação recebe. Ler a variável ali
> exige carregá-la explicitamente, ou tomá-la do ambiente do processo. É armadilha de
> implementação, não de contrato, mas do mesmo tipo que já está em
> [aprendizados](../aprendizados.md) — e sem ela o padrão silenciosamente sempre vence.

### A imagem do frontend carrega as dependências de desenvolvimento

**Instalação completa, sem omitir as dependências de desenvolvimento.** Não é descuido de
imagem inchada: é o que F3-09 exige.

Como `node_modules` passa a ser volume próprio do contêiner (item 2 abaixo), **rodar
`npm test` no hospedeiro deixa de ser o caminho** — quem chega ao projeto não terá as
dependências instaladas ali, e instalá-las é justamente o pré-requisito de Node que este
bloco elimina. Se a imagem viesse sem `vitest`,
`typescript`, `jsdom` e `@testing-library/*`, o frontend ficaria sem casa nenhuma para teste
e verificação de tipos, e o `README.md` (F3-11) documentaria comandos que nenhum critério
executou.

A imagem deste bloco é **de desenvolvimento**. Imagem enxuta de produção — que serve o
resultado de `vite build` por um servidor estático, sem Node — é outro artefato, e está
[fora do escopo](#fora) junto com o resto de produção.

> **Efeito colateral a assumir:** com `node_modules` só dentro do contêiner, o editor no
> hospedeiro perde a resolução de tipos e o autocompletar do frontend. É a contrapartida
> exata do que a spec preserva do lado do backend, onde o `.venv/` continua instalado
> justamente *"para o editor resolver importação"*. A assimetria é deliberada — instalar o
> Node no hospedeiro só para o editor recriaria o pré-requisito que este bloco remove —, mas
> quem preferir o conforto pode rodar `npm install` localmente sem quebrar nada: o contêiner
> não usa essa pasta.

### O que a conteinerização do frontend exige

Três ajustes que não são opcionais, e cuja ausência produz falha confusa:

1. **O servidor precisa escutar em todas as interfaces.** Preso ao laço local do contêiner,
   ele não é alcançável do hospedeiro, e o navegador mostra conexão recusada com o serviço
   perfeitamente de pé.
2. **`node_modules` não pode vir do hospedeiro.** O código-fonte é montado para haver recarga
   a quente, mas `node_modules/` precisa ser um volume próprio do contêiner: as dependências
   instaladas no Windows não servem ao Linux da imagem, e binário nativo — o do `rolldown`,
   que a [armadilha do `engine-strict`](../aprendizados.md) já envolveu — é justamente o que
   quebra.
3. **A recarga a quente pode precisar de sondagem.** Em montagem de disco entre Windows e
   contêiner, o aviso de mudança de arquivo frequentemente não atravessa. Se não atravessar,
   liga-se sondagem — o plano verifica qual dos dois casos é o desta máquina, em vez de
   assumir.
4. **`brand/ruvor/` é montado, não assado.** Ele entra no contexto de construção por causa do
   apelido `@brand`, mas precisa vir do hospedeiro em execução: assado na imagem, uma mudança
   em `tokens.css` só apareceria depois de reconstruir. Como o kit é consumido e nunca
   modificado pelo frontend ([F2b](F2b-casco-da-aplicacao.md#como-o-frontend-consome-os-tokens)),
   a montagem pode ser somente-leitura.

### Porta do frontend: 5173 não serve como padrão

**A porta 5173 pertence a outro projeto do usuário nesta máquina.** É por isso que toda porta
publicada é configurável (F3-08) e por isso que **5173 não é o padrão** de
`RUVOR_PORT_FRONTEND`. O padrão é uma porta que não colide com nada conhecido; o valor exato
é do plano, que verifica que está livre antes de fixá-lo.

O mesmo cuidado vale para as outras três: quem tem Postgres nativo já ocupa a porta padrão
dele, e o `compose` falharia ao subir com uma mensagem que parece de permissão.

---

## Verificação

### Critérios executáveis

O [PROCESSO §5](../PROCESSO.md#regra-dura) exige critério de aceite executável por tarefa.
Cada requisito tem o seu:

| Requisito | Verificação |
|---|---|
| **F3-01** | Sobe o conjunto e consulta o estado dos cinco serviços; todos precisam estar saudáveis, não apenas "em execução" |
| **F3-02** | As duas etiquetas são construídas a partir de **um único arquivo**, `infra/backend.Dockerfile`, variando só o alvo — mais o que F3-03 prova. Ver [abaixo](#f3-02-tem-metade-do-critério-em-f3-03) |
| **F3-03** | Quatro afirmações, todas exigidas: na `web`, `import tensorflow` falha **com módulo não encontrado** e `import django` **funciona**; na `worker`, `import tensorflow` funciona; e `python --version` é **idêntico** nas duas |
| **F3-04** | Abre um cursor no banco **configurado** de dentro do `web` e executa uma consulta trivial — ver [o mecanismo](#o-teste-de-conexão-precisa-driblar-o-bloqueio-do-pytest-django) |
| **F3-05** | Enfileira `config.tasks.ping` de dentro do `web` e recebe exatamente `"worker"`, dentro de um tempo limite |
| **F3-06** | `docker compose up` na raiz, sem nenhuma variável exportada no shell, partindo só do `.env` |
| **F3-07** | Requisição do hospedeiro à porta do frontend recebe a tela; requisição a `/health` pela mesma porta recebe `{"status": "ok"}` |
| **F3-08** | Muda **as quatro** portas no `.env`, sobe de novo, e cada serviço responde na porta nova. Uma amostra de uma porta não vale: a que ficasse de fora seria justamente a esquecida no `compose.yaml` |
| **F3-09** | Quatro comandos passam dentro do contêiner: suíte e tipos do backend, suíte e tipos do frontend |
| **F3-10** | Teste de unidade sobre a leitura da variável: `"localhost, 127.0.0.1"` produz dois hosts sem espaço |
| **F3-11** | Varredura sobre a [lista fechada de trechos](#o-que-fica-falso-vai-além-da-seção-executar-do-readme) que ficam falsos, provando que nenhum sobreviveu e que o `README.md` contém `docker compose up`; e que o `.env.example` da raiz lista **todas as `RUVOR_*` do contrato**, inclusive as quatro `RUVOR_PORT_*`, que o `settings.py` não lê. A própria varredura precisa reprovar contra o `README.md` de hoje. A redação em si é inspeção humana |

### Onde cada verificação mora

Duas formas, e a divisão importa porque decide o que a suíte do backend passa a exigir:

| Forma | Quais | Onde |
|---|---|---|
| **Teste da suíte do backend** | F3-04, F3-10 | `backend/tests/`, arquivos nomeados no [inventário](#inventário-dos-arquivos-existentes) |
| **Comando sobre o conjunto** | F3-01, 02, 03, 05, 06, 07, 08, 09, 11 | invocação de uma linha do `docker` ou do `compose`, escrita **literalmente** no critério de aceite da tarefa correspondente do plano |

**Nenhum arquivo de script é criado neste bloco.** As verificações de conjunto são comandos,
não artefatos: escrevê-los como script agora, antes de o F5 existir, seria inventar a forma
que a CI vai querer. O plano os escreve literais no critério de aceite, e o `README.md`
documenta os que servem no dia a dia — é daí que o F5 os herda.

**F3-05 é comando, não teste da suíte.** Consequência declarada, e é o motivo de a divisão
estar aqui: **a suíte do backend passa a exigir um Postgres alcançável, e nada além disso.**
Se o teste da tarefa `ping` entrasse em `backend/tests/`, a suíte passaria a exigir também
Redis e um worker vivo — e `pytest backend` deixaria de rodar com o conjunto parcialmente de
pé, que é situação comum durante o desenvolvimento.

### Cada família de verificação prova que sabe reprovar

O F2b estabeleceu o padrão e ele vale aqui: não basta a verificação passar, é preciso mostrar
que ela **reprova quando deve**. O
[ESTADO](../ESTADO.md#f2b--casco-da-aplicação) registra o resultado nessa forma — "2 mutações
reprovam", "mutação TS7006 reprova", "mutação de rótulo reprova".

Este bloco é onde o padrão mais importa, porque quase toda verificação dele é indireta: um
serviço saudável, um import que falha, uma tarefa que volta. **O plano injeta ao menos um erro
por família** e mostra a reprovação:

| Família | Mutação que precisa reprovar |
|---|---|
| Verificação de vida (F3-01) | derrubar um serviço de que outro depende |
| Isolamento das imagens (F3-03) | acrescentar o extra de ML à imagem `web` |
| **Carga do `.env` (F3-06)** | **renomear o `.env` e exigir que a subida falhe** |
| **Conexão de banco (F3-04)** | **apontar `RUVOR_DB_NAME` para um banco inexistente** |
| Fila (F3-05) | derrubar o serviço `worker` |
| Portas (F3-08) | trocar uma porta e não a outra |
| **Varredura de texto (F3-11)** | **rodar a varredura contra o `README.md` de hoje e exigir que reprove** |
| **Tipos (F3-09)** | **introduzir erro de tipo e exigir que o mypy reprove** |

As quatro acrescentadas não são simetria decorativa — cada uma tapa um buraco real:

- **A varredura de F3-11 é o critério que mais facilmente passa vazio de todo o bloco.** Ela
  prova *ausência* de trechos, e ausência é o que um padrão mal escrito, um caminho errado ou
  um casamento impossível também produzem — nos três casos, verde. Rodá-la contra o
  `README.md` **antes** da correção, e exigir reprovação, é o que separa "a varredura
  funciona" de "a varredura está desligada". É o mesmo controle que o F2b usou na verificação
  de cor literal.
- **`mypy` sobre zero arquivo sai com sucesso.** Um caminho errado na configuração dentro do
  contêiner faz F3-09 aprovar sem verificar nada.

- **Sem a mutação do `.env`**, F3-06 passa igual se quem implementa cravar a chave secreta, a
  senha e as URLs direto no `compose.yaml` e o `.env` nunca for lido. O critério diz "sem
  variável exportada no shell", e um valor embutido também satisfaz isso. Renomear o arquivo
  e ver a subida falhar é o que prova que ele é a fonte.
- **Sem a mutação do nome do banco**, a escolha do mecanismo de F3-04 fica sem sustentação. A
  spec descarta a alternativa justamente porque *"um `RUVOR_DB_NAME` errado atravessa sem ser
  notado"* — e a regra de que os valores de reserva do `settings_test.py` não podem coincidir
  com os do `compose` é, sem essa mutação, promessa em prosa que a primeira edição desatenta
  desfaz sem reprovar nada.

Sem isso, "todos os serviços saudáveis" pode significar que a verificação de vida sempre
devolve sucesso — e é a própria spec que diz, logo abaixo, que esse é o risco do mecanismo.

### Por que "em execução" não basta

Contêiner de Postgres entra em execução em menos de um segundo e só aceita conexão vários
segundos depois. Um critério que só verifique execução aprova um conjunto em que o `web`
subiu antes do banco existir e morreu — e a falha aparece de forma intermitente, que é a
pior forma.

Cada serviço declara **verificação de vida própria**, e quem depende de outro espera a saúde
dele, não a partida.

Verificação de vida é justamente o lugar onde um comando que sempre devolve sucesso aprova
tudo. Por isso a spec fixa **o que cada uma precisa provar**, e não só que exista:

| Serviço | A verificação precisa provar |
|---|---|
| `postgres` | que o banco **aceita conexão**, não que o processo subiu |
| `redis` | que o servidor **responde a um comando**, não que a porta abriu |
| `web` | que `GET /health` devolve `200` — contrato congelado no [F2b](F2b-casco-da-aplicacao.md#rota-de-saúde) exatamente para isto |
| `worker` | que o worker **responde pela fila**, e não que o processo existe. Um `worker` cujo processo vive mas não consome a fila é a falha real deste serviço |
| `frontend` | que o servidor de desenvolvimento **serve a página**, não que o Node está em execução |

Três notas de implementação que a primeira subida cobra caro se forem esquecidas:

- **`web` e `frontend` precisam de um cliente HTTP dentro da imagem** para a própria
  verificação de vida, e imagem enxuta costuma não trazer nenhum.
- **A do `worker` não pode se contentar com "o processo existe"**, porque um worker que subiu
  e não consome a fila é exatamente a falha que este serviço tem.
- **F3-08, para `postgres` e `redis`, não pode exigir cliente no hospedeiro** — seria pedir
  justamente o que este bloco promete não exigir. Prove a porta nova por conexão de rede, ou
  de dentro de um contêiner.

### Os dados do Postgres ficam em volume nomeado

Volume gerido pelo Docker, e não uma pasta dentro do repositório. Duas consequências que
valem ser escolhidas, e não herdadas por acidente:

- **O repositório não ganha diretório de dados** para ignorar, nem risco de alguém versionar
  banco por engano.
- **`docker compose down` preserva os dados**; apagá-los exige pedir explicitamente. Com o
  banco vazio de hoje isso é indiferente, mas a partir do F4 haverá migrations aplicadas, e
  perder o banco a cada parada seria atrito diário.

### F3-02 tem metade do critério em F3-03

F3-02 pede duas imagens **do mesmo fonte**, com a `web` sem dependências de ML. O critério
óbvio para o conjunto — "as duas existem, e a `worker` é maior" — é quase impossível de
reprovar e não acrescenta informação: mede bytes, quando o que importa é o que a imagem
consegue importar. Esse F3-03 já cobre.

A outra metade não sai de graça, e exige critério próprio:

| Metade de F3-02 | Quem pega |
|---|---|
| `web` sem ML, `worker` com | `import tensorflow` nos dois lados, em F3-03 |
| **mesmo fonte, estágio base compartilhado** | a construção das duas etiquetas parte de **um único arquivo**, variando apenas o alvo |

**Por que a igualdade de `python --version` não bastaria.** Ela é necessária, não suficiente:
dois arquivos de construção separados, ambos fixando a mesma imagem base, passariam com
folga. O que a spec quer impedir é a **existência** de dois arquivos, porque é ela que
permite a divergência depois — não a divergência de hoje. Um critério sobre o resultado não
pega uma estrutura que ainda não divergiu; um critério sobre a estrutura pega.

`python --version` idêntico permanece em F3-03 como rede de segurança barata, mas não é o que
sustenta esta metade.

### Por que F3-03 exige também que `import django` funcione na `web`

`import tensorflow` falhar não prova nada sozinho: uma imagem `web` **quebrada, vazia, ou com
o Python sem nada instalado** faz o mesmo import falhar, pelo motivo errado, e o critério
aprova.

Daí as duas salvaguardas: a falha precisa ser especificamente **módulo não encontrado** — não
um código de saída qualquer, que também cobre imagem sem Python — e precisa haver **controle
positivo** na mesma imagem, provando que ela de fato tem o backend instalado.

F3-01 mitiga isso na prática, exigindo a `web` saudável respondendo `GET /health`. Mas
mitigação por vizinhança some no dia em que alguém rodar F3-03 isolado, e é justamente para
esse dia que o critério existe.

### O teste de conexão precisa driblar o bloqueio do pytest-django

F3-04 tem uma armadilha que decide o formato do artefato, e por isso a spec a resolve em vez
de deixar para o plano.

**O pytest-django bloqueia acesso a banco por padrão** e levanta `RuntimeError` em qualquer
consulta fora de um teste marcado — o `docs/aprendizados.md` já registra esse bloqueio ao
tratar de `DATABASES = {}`. Há três saídas, e elas **provam coisas diferentes**:

| Saída | O que prova, e o que custa |
|---|---|
| `@pytest.mark.django_db` | alcança o servidor configurado — para criar o banco `test_*` ele precisa conectar — mas **não** exercita `RUVOR_DB_NAME`, porque usa outro nome de banco. E paga criação e derrubada de banco a cada execução |
| desbloqueio explícito do acesso, conectando ao banco configurado | alcança o servidor **e** o banco nomeados no `.env`, exatamente como estão — **é o que F3-04 quer** |
| um comando de gerenciamento em vez de teste | prova o mesmo, mas fica fora da suíte e ninguém o roda de novo |

**A spec escolhe a segunda.** O teste desbloqueia o acesso e abre um cursor contra o banco
**configurado**, não contra um banco de teste criado para a ocasião.

A diferença entre as duas primeiras é estreita e vale ser dita com precisão, para que ninguém
a use como argumento maior do que é: as duas exigem um Postgres alcançável, e a suíte quebra
sem ele nos dois casos. O que só a segunda cobre é a configuração **inteira** — um
`RUVOR_DB_NAME` errado atravessa a primeira sem ser notado, e é justamente o tipo de erro de
`.env` que este bloco existe para pegar.

### Verificação de tipos

Rigor inalterado, conforme a [D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md):
o `backend/` segue em mypy estrito. O código novo deste bloco — o módulo do Celery, a tarefa
de fumaça e a leitura das variáveis de banco — nasce sob esse rigor.

O `django-stubs` já está configurado e aponta para `config.settings_test`
(`backend/pyproject.toml`); acrescentar variáveis de banco àquele módulo mantém o arranjo
funcionando. **Celery não publica anotações completas**: se o mypy estrito reprovar no
código de fila, a saída é um `ignore_missing_imports` restrito ao módulo do Celery — nunca
`ignore_errors`, que desligaria a verificação no código novo e tornaria "mypy passa"
vacuamente verdadeiro. A distinção está registrada em
[aprendizados](../aprendizados.md#pandas-não-publica-anotações-de-tipo).

---

## Inventário dos arquivos existentes

Todo arquivo que este bloco toca durante a **implementação**, e o que acontece com ele. O que
não está aqui não é alterado — com a exceção declarada logo abaixo da tabela, para os
arquivos que o passo FECHA obriga a atualizar.

| Arquivo | O que acontece |
|---|---|
| `backend/config/settings.py` | ganha `DATABASES` real e a configuração do Celery; a leitura de `RUVOR_ALLOWED_HOSTS` é **extraída para uma função nomeada** que passa a tolerar espaço (F3-10) |
| `backend/config/settings_test.py` | ganha as variáveis de banco |
| `backend/config/__init__.py` | passa a expor a aplicação Celery — é o que faz `celery -A config` encontrá-la e o que permite o decorador de tarefa compartilhada |
| `backend/config/celery.py` | **novo** — a aplicação Celery |
| `backend/config/tasks.py` | **novo** — a tarefa `ping` |
| `backend/tests/test_health.py` | `test_processo_nao_tem_banco` é **removido**; entra um teste que prova a conexão |
| `backend/tests/test_allowed_hosts.py` | **novo** — F3-10 |
| `backend/pyproject.toml` | ganha `celery`, `redis` e o driver do PostgreSQL — **`psycopg`, versão 3**, e não o `psycopg2` antigo. O F4 herda essa escolha, então ela é nomeada aqui em vez de ficar por conta de quem implementa; o plano confirma a compatibilidade com a versão do Django em uso antes de fixá-la |
| `frontend/vite.config.ts` | destino do proxy vem de variável; servidor escuta em todas as interfaces |
| `frontend/.env.example` | ganha `VITE_PROXY_TARGET` |
| `.env.example` | ganha as variáveis de banco, de Redis e de porta |
| `.gitignore` | **intocado**. Os dados do Postgres ficam em **volume nomeado**, gerido pelo Docker, e não numa pasta dentro do repositório — logo não há o que ignorar. Ver [abaixo](#os-dados-do-postgres-ficam-em-volume-nomeado) |
| `README.md` | a seção "Executar" passa a ter o `compose` como caminho principal; a tabela "Comandos do dia a dia" é reescrita conforme a [divisão de casas](#o-dia-a-dia-passa-a-ser-dentro-do-contêiner); e os trechos [listados abaixo](#o-que-fica-falso-vai-além-da-seção-executar-do-readme), espalhados fora dessa seção, deixam de mentir |
| `frontend/.nvmrc`, `frontend/.npmrc` | **permanecem** — continuam valendo para quem editar o frontend fora do contêiner, e o `engine-strict` protege a instalação dentro da imagem também |
| `engine/` | **intocado**. O motor é instalado na imagem `worker`, e instalar não é alterar; a [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) segue respeitada |
| `brand/` | **intocado**, apenas lido — como no F2b |

### Por que a leitura do `RUVOR_ALLOWED_HOSTS` vira função

Hoje é expressão de nível de módulo (`backend/config/settings.py`), avaliada uma vez no
`django.setup()`, com o valor fixado por `settings_test.py`. **Não existe função a testar** —
e F3-10 pede "teste de unidade sobre a leitura da variável".

Sem extrair, a única alternativa seria recarregar o módulo de settings com a variável
trocada, o que reentra no `django.setup()` e é frágil o bastante para virar teste
intermitente. Extrair uma função que recebe o texto e devolve a lista de hosts torna o teste
trivial e direto. É mudança de forma em arquivo sob mypy estrito, e por isso está declarada
aqui em vez de ficar por conta de quem implementa.

### A tarefa não é descoberta sozinha

Expor a aplicação Celery em `config/__init__.py` **não** faz `config.tasks` ser encontrada. A
descoberta automática do Celery varre os apps de `INSTALLED_APPS`, que hoje contém apenas
`rest_framework` — `config` não está lá e não deve entrar, porque não é app de domínio.

A tarefa precisa ser **declarada explicitamente** à aplicação Celery. É uma linha, e é o tipo
de detalhe cuja ausência produz um `worker` saudável que nunca recebe a tarefa — falha que
F3-05, agora que discrimina quem executou, pega.

### O que fica falso vai além da seção "Executar" do README

Lista fechada, derivada da leitura dos arquivos — não da memória. Cada trecho abaixo fica
falso depois do F3, e **nenhum está onde a atenção naturalmente vai**:

| Arquivo | O que diz hoje | Por que fica falso |
|---|---|---|
| `README.md`, aviso de reconstrução | *"não há banco, API de negócio nem tela de produto"* | passa a haver banco |
| `README.md`, mesmo aviso | *"que responde `GET /health` **sem banco**"* | o Django passa a conectar |
| `README.md`, "Pré-requisitos" | Python 3.12+ e Node 24.15+ como pré-requisitos do repositório | contradiz o [Resultado esperado 2](#resultado-esperado): só o motor continua exigindo Python, e o Node deixa de ser pré-requisito |
| `README.md`, seção do frontend | *"Abra `http://localhost:5173`"* | 5173 [deixa de ser o padrão](#porta-do-frontend-5173-não-serve-como-padrão) |
| `.env.example`, cabeçalho | *"Nada as carrega deste arquivo: exporte no shell, ou deixe o docker compose (F3) le-lo"* | o F3 chegou; o `compose` passa a carregá-lo |
| `frontend/.env.example`, comentário | *"o proxy do Vite encaminha /health para o Django em :8000"* | continua verdade nativamente, mas não descreve o caminho em contêiner |
| `CLAUDE.md`, "Estado do repositório" | o parágrafo *"Não há banco…"* **e** o item de lista *"Uma rota, `GET /health`, sem banco"* | passa a haver banco nos dois casos |

Esta lista existe porque o defeito é conhecido e reincidente: corrige-se a seção óbvia e
deixa-se a afirmação equivalente três parágrafos acima, ou em outro arquivo. Sem enumerar, a
varredura de F3-11 nasce cobrindo só o que quem escreveu lembrou — e note que o próprio
`.env.example`, que é o arquivo que **aponta para este bloco**, é o mais fácil de esquecer.

### Quais variáveis moram em qual arquivo de exemplo

F3-11 exige que o exemplo liste "todas as variáveis do contrato", e o contrato tem duas
tabelas. A divisão, para não haver duas leituras:

| Arquivo | Lista |
|---|---|
| `.env.example` da raiz | **todas as `RUVOR_*`**, inclusive as quatro `RUVOR_PORT_*` |
| `frontend/.env.example` | apenas `VITE_API_BASE_URL` |

`VITE_PROXY_TARGET` **não entra em nenhum dos dois**: ela é fixada pelo `compose` no serviço
`frontend`, pelo motivo já dado — é endereço interno da rede, e expô-la convidaria a mexer no
que não deve.

### Os arquivos do passo FECHA

O [PROCESSO §3](../PROCESSO.md#o-passo-fecha) obriga a atualizar, ao fechar o bloco:
`docs/ESTADO.md`, `docs/ROADMAP.md`, `docs/aprendizados.md`, o cabeçalho de status desta spec
e do plano, `docs/specs/README.md` e `docs/planos/README.md`.

**Também a `docs/ARQUITETURA.md`**, que a lista do PROCESSO não nomeia mas que este bloco
torna falsa em dois pontos: §Ambientes diz *"`docker compose up` sobe Postgres, Redis, web e
worker"* (sem o frontend), e o diagrama de estrutura reserva `infra/` para *"docker, compose,
CI"* (o `compose` sai de lá). São exatamente as duas divergências declaradas — e registrar a
decisão **não basta**: a ARQUITETURA está na tabela "Manda" do `CLAUDE.md`, e documento que
manda com texto falso, contradito só por um registro em `decisoes/`, é a contradição
silenciosa que o PROCESSO proíbe. Foi este o argumento usado para citar ROADMAP e ESTADO na
primeira divergência; vale igual aqui.

Em `docs/aprendizados.md`, além do que a execução ensinar, há uma **poda** prevista: o
verbete *"`DATABASES = {}` não fica vazio, e 'sem banco' se prova pelo acesso"* descreve um
teste que este bloco remove.

E também **`CLAUDE.md`**, porque este bloco muda o que existe no repositório: a seção "Estado
do repositório" afirma *"Não há banco, API de negócio nem tela de produto"*, e a primeira
parte fica falsa depois do F3.

A frase vizinha — *"Um só `.venv/` na raiz para motor e backend"* — **continua verdadeira**, e
não deve ser mexida: o ambiente virtual permanece, como a
[divisão de casas](#o-dia-a-dia-passa-a-ser-dentro-do-contêiner) explica. O que muda é qual
execução vale, não a existência do ambiente.

Estão fora da tabela acima porque não são trabalho de implementação; são o fechamento. Ficam
listados para que não sejam esquecidos, que é exatamente o que o PROCESSO adverte sobre eles.

---

## Decisões que esta spec assume

- [D-11](../decisoes/D-11-pilha-tecnologica.md) — Python, Django, DRF, React, PostgreSQL
- [D-12](../decisoes/D-12-tipagem-obrigatoria.md) — tipagem obrigatória
- [D-14](../decisoes/D-14-celery-e-redis.md) — Celery e Redis; o Redis faz corretor, cache e canal de progresso
- [D-17](../decisoes/D-17-monorepo-engine-sem-django.md) — `engine/` sem Django, duas imagens
- [D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md) — o motor está congelado
- [D-22](../decisoes/D-22-treino-centralizado-em-container.md) — treino em contêiner, numa máquina só
- [D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md) — rigor de tipagem por origem
- [D-31](../decisoes/D-31-trabalho-direto-na-main.md) — trabalho direto na `main`

### Decisões novas que este bloco produz

Quatro divergências com documento vivo. Cada uma vira registro em `decisoes/` **junto com a
aprovação desta spec** — não depois, porque o PROCESSO proíbe contradição silenciosa:

| Decisão nova | Contradiz |
|---|---|
| O frontend entra no `compose` | [ARQUITETURA](../ARQUITETURA.md#ambientes) **e** [ROADMAP](../ROADMAP.md) **e** [ESTADO](../ESTADO.md), que listam os mesmos quatro serviços sem ele |
| O dia a dia de backend e frontend roda dentro do contêiner | o `README.md`, que documenta execução nativa |
| O F3 conecta o Django ao Postgres, e traz Celery e Redis | a [spec do F2b](F2b-casco-da-aplicacao.md), que pôs banco, Celery e fila no F4 — e o teste `test_processo_nao_tem_banco` que ela deixou |
| `compose.yaml` e `.dockerignore` ficam na raiz, não em `infra/` | o diagrama da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório), que reserva `infra/` para "docker, compose, CI" |

**Este bloco gera um quinto registro em `decisoes/`, que não é divergência:** a
[versão maior do Postgres](#serviços-e-nomes-de-rede), fixada pelo plano e registrada para que
o F4 e o bloco de hospedagem a leiam em vez de re-derivá-la do `compose.yaml`. São quatro
divergências e cinco registros.

**A primeira linha cita três documentos de propósito.** O ROADMAP e o ESTADO estão na tabela
"Manda" do `CLAUDE.md` tanto quanto a ARQUITETURA; uma decisão que citasse só a ARQUITETURA
deixaria os outros dois mentindo depois do fechamento.

**A terceira é mais ampla do que "banco".** A spec do F2b põe explicitamente *"Celery, Redis,
fila"* no F4, e repete *"Sem Celery, sem driver de banco — entram no F4"*. O F3 toma os três.
É a mesma decisão, e precisa ser registrada pelos três, não só pelo banco.

---

## Riscos e questões em aberto

### ✅ Pré-requisito de ambiente — resolvido

Quando esta spec foi escrita, a máquina de desenvolvimento **não tinha Docker nem WSL**, o
que tornava inexecutável todo critério de aceite do bloco. Resolvido em **2026-09-02**, antes
do plano começar:

| | Verificado |
|---|---|
| WSL | 2.7.12.0, kernel 6.18.33.2-2, versão padrão 2 |
| Docker Engine | 29.7.2 |
| Docker Compose | v5.5.0 |
| Prova de vida | `docker run --rm hello-world` baixou a imagem, criou o contêiner e executou |

Fica registrado porque é a natureza do bloco, não um acidente: **o F3 é o primeiro cujo
resultado depende de infraestrutura fora do repositório.** Quem for executar o plano em outra
máquina precisa dos mesmos pré-requisitos, e instalá-los exige privilégio administrativo e
reinício — não é trabalho que o plano faça por conta própria.

Vale prever que a primeira execução vai levar minutos construindo a imagem `worker`, que
carrega TensorFlow.

### O espaço em disco é apertado, e a imagem pesada é deste bloco

A unidade do sistema desta máquina tem **pouco mais de 7 GB livres**, e por isso a instalação
do Docker foi direcionada para outra unidade. A imagem `worker` carrega TensorFlow e vai
custar vários GB, mais o que as camadas intermediárias ocuparem durante a construção.

O plano deve **medir o espaço antes e depois** da primeira construção, e reportar. Encher a
unidade do sistema no meio de um `docker build` não produz erro claro — produz falha
esquisita em ferramenta que não tem nada a ver com o problema.

### Desempenho de montagem de disco no Windows

Montar código do Windows dentro de contêiner Linux é reconhecidamente lento, e afeta os dois
lados: a suíte do Python e o servidor do Vite. Se a lentidão inviabilizar o dia a dia, a
saída conhecida é mover o repositório para dentro do sistema de arquivos do WSL — o que muda
o fluxo de trabalho de todo mundo e **não é decisão desta spec**.

O plano deve **medir**, não supor: se a suíte do backend dentro do contêiner demorar
desproporcionalmente em relação à execução nativa, isso é achado que volta como questão, não
algo a contornar em silêncio.

### O contêiner de treino da D-22 não é este

A [D-22](../decisoes/D-22-treino-centralizado-em-container.md) exige que o treino do TCC rode
em contêiner, com semente fixa, para que o ranking não dependa da máquina. **Este bloco não
entrega isso.** A imagem `worker` carrega o motor com ML e é o passo natural nessa direção,
mas contêiner de experimento reprodutível tem outros requisitos — versões congeladas por
`engine/requirements-lock.txt`, semente, coleta de resultado — que pertencem à trilha do TCC.

Registrado aqui para que ninguém leia "worker com TensorFlow" como "a D-22 está resolvida".

### Celery sem tarefa de domínio é fila vazia

A tarefa `ping` prova o caminho e nada além. Riscos reais do modo A — repetição em falha,
cancelamento, agendamento, progresso parcial ([D-07](../decisoes/D-07-resposta-progressiva-modo-a.md))
— continuam sem verificação até o M1.5. O F3 não deve dar a impressão de que a fila está
provada para o uso que ela vai ter.

### A senha do banco fica em texto claro no `.env`

Aceitável para ambiente local, e o `.gitignore` já ignora o `.env`. **Não é o padrão para
produção**, e produção está fora do escopo. Fica registrado para que o bloco de hospedagem
não copie este arranjo.

### `INSTALLED_APPS` continua quase vazio

`backend/config/settings.py` tem hoje `INSTALLED_APPS = ["rest_framework"]` — sem
`django.contrib.contenttypes`, `auth` ou `sessions`. Conectar ao banco não exige nenhum
deles, então o F3 não os acrescenta. **O F4 vai precisar** de pelo menos parte disso para
criar migrations, e é lá que a escolha se justifica — acrescentar por antecipação aqui seria
decidir sem o problema à vista.
