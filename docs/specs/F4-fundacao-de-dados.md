# F4 — Fundação de dados

**Bloco:** Fundação · F4
**Status:** ✅ **aprovada** (2026-09-04) — em implementação
Duas rodadas de revisão adversarial. O contrato do esquema embutido no `db_table` foi medido
de ponta a ponta contra o `postgres:18` do `compose`, e produz exatamente a lista fechada
declarada aqui. As cinco decisões que ela produz estão registradas:
[D-37](../decisoes/D-37-esquema-core-para-dado-operacional.md) a
[D-41](../decisoes/D-41-filtro-por-organizacao-na-primeira-tabela-privada.md).
**Depende de:** [F3 — Ambiente local](F3-ambiente-local.md)

---

## Problema

O F3 deixou o Django conectando no PostgreSQL e nada mais. Hoje, no `backend/`:

- `INSTALLED_APPS` é `["rest_framework"]` — nem `contenttypes`, nem `auth`
- não existe diretório `apps/`, não existe modelo, não existe uma única migration
- `manage.py migrate` nunca foi executado neste repositório

Enquanto isso, quatro decisões registradas continuam sendo promessa não verificada:

- [D-13](../decisoes/D-13-camadas-bronze-prata-ouro.md) manda implementar bronze, prata e
  ouro como esquemas dentro do PostgreSQL — não existe esquema nenhum
- [D-24](../decisoes/D-24-organizacao-desde-a-primeira-migration.md) diz que a Organização
  existe *desde a primeira migration* — que ainda não foi escrita
- [D-08](../decisoes/D-08-dono-do-dado-no-schema.md) diz que toda tabela privada nasce
  sabendo a quem pertence — não há tabela
- [D-16](../decisoes/D-16-resultado-e-imutavel.md) e
  [D-15](../decisoes/D-15-manifesto-de-execucao.md) descrevem um modelo de domínio que
  ainda não tem onde morar

E há uma janela que se fecha. **Trocar o modelo de usuário do Django é barato exatamente
uma vez: antes da primeira migration.** Depois, `AUTH_USER_MODEL` só muda com migração de
dados sobre chaves estrangeiras espalhadas. Hoje o custo é uma linha em `settings.py`. No
primeiro `migrate` que rodar sem ele, deixa de ser.

O M1.1 (catálogo de ativos) é o próximo consumidor: ele precisa de um lugar para as
tabelas nascerem e de uma convenção de migration para seguir. Sem o F4, ele inventa as
duas — e inventa diferente do M1.2.

---

## Resultado esperado

1. `migrate` num banco vazio cria os quatro esquemas e as tabelas do projeto, e termina sem
   erro; rodar de novo não faz nada
2. Existe a entidade **Organização**, e existe um **modelo de usuário próprio** apontado por
   `AUTH_USER_MODEL`, ambos na primeira migration
3. **Nenhuma tabela de domínio nasce no `public`** — cada uma declara o esquema em que mora
4. Existe a organização fixa do Marco 1, criada por migration de dados e idempotente
5. `GET /health` continua respondendo sem tocar no banco, como o F2b congelou

---

## Escopo

### Dentro

- Os quatro esquemas do banco, criados por migration versionada
- O app `accounts` — o único deste bloco —, com `Organization` e `User`
- `AUTH_USER_MODEL` apontando para o usuário próprio, **antes** da primeira migration
- `django.contrib.contenttypes` e `django.contrib.auth` em `INSTALLED_APPS`
- A organização fixa do Marco 1, por migration de dados
- Convenção de migration — nomeação, revisão e o que nunca se faz
- Crescimento de `backend/pyproject.toml` para cobrir o pacote novo em `packages` e em
  `[tool.mypy] files`
- Atualização do `README.md` e dos documentos vivos que passam a mentir

### Fora

| Fora do escopo | Onde entra |
|---|---|
| Catálogo de ativos — tabelas, ingestão, papéis da B3 | M1.1 |
| Preços, camada bronze com dado dentro | M1.2 |
| Manifesto de execução ([D-15](../decisoes/D-15-manifesto-de-execucao.md)) e imutabilidade de resultado ([D-16](../decisoes/D-16-resultado-e-imutavel.md)) | M1.4 — ver [por quê](#por-que-o-manifesto-não-entra-aqui) |
| Telas de login, fluxo de autenticação, papéis, permissões atribuídas | M2.1 |
| Carteiras, limites, alertas | M2.2 |
| A base abstrata e o gerente que aplicam o filtro por organização | M2.2 — ver [por que o filtro automático é adiado](#por-que-o-filtro-automático-é-adiado) |
| Qualquer endpoint do DRF sobre os modelos novos | Marco 1 |
| `django.contrib.admin` | nada previsto; entra quando houver quem o use |
| Os apps `assets`, `analytics`, `risk`, `portfolios`, `audit` do diagrama da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) | cada um no bloco que o consome — **este bloco não cria app vazio** |
| Particionamento por data, TimescaleDB, ajuste de desempenho | quando houver evidência de necessidade ([ARQUITETURA](../ARQUITETURA.md#caminho-de-crescimento)) |
| Registro de acesso e alteração (a terceira linha da tabela de auditoria) | Marco 2 |

---

## Requisitos

| ID | Requisito |
|---|---|
| **F4-01** | Os quatro esquemas — `core`, `bronze`, `silver`, `gold` — existem no banco depois de `migrate`, criados por migration versionada e não por passo manual |
| **F4-02** | Toda tabela criada por app do projeto nasce no esquema que declara; o `public` não recebe nenhuma delas |
| **F4-03** | Existe `Organization`, com chave estável, e existe organização fixa do Marco 1 criada por migration de dados, idempotente |
| **F4-04** | `AUTH_USER_MODEL` aponta para um modelo de usuário do projeto, presente na primeira migration, com vínculo obrigatório a uma organização |
| **F4-05** | `migrate` num banco vazio termina sem erro, e a segunda execução não aplica nada |
| **F4-06** | `makemigrations --check --dry-run` não encontra migration faltando — modelo e migration em sincronia |
| **F4-07** | mypy estrito cobre o código novo; a lista de arquivos do `pyproject.toml` cresce junto |
| **F4-08** | A suíte do backend continua passando, e `GET /health` continua respondendo sem tocar no banco |
| **F4-09** | O `pip install -e "./backend[dev]"` da imagem continua funcionando com o pacote novo declarado |
| **F4-10** | `README.md`, `CLAUDE.md`, `ESTADO.md`, `ARQUITETURA.md`, `ROADMAP.md` e os dois índices em `docs/specs/` e `docs/planos/` descrevem o estado novo, e nenhum trecho antigo fica mentindo |

---

## Contratos externos

Congelados a partir da aprovação. O M1.1 consome os esquemas e a convenção de migration; o
M1.2 consome a camada bronze; o M2.1 consome o modelo de usuário; o M2.2 herda a obrigação do
filtro por organização.

### Os quatro esquemas

| Esquema | Conteúdo | Camada da [D-13](../decisoes/D-13-camadas-bronze-prata-ouro.md) |
|---|---|---|
| `core` | dado operacional: organização, usuário, e depois carteiras, limites, chaves | — |
| `bronze` | o que o provedor devolveu, cru e imutável, com data e hora da coleta | bronze |
| `silver` | preços limpos e conformados, retornos calculados | prata |
| `gold` | métricas, séries de VaR, backtests, agregados | ouro |

**Os identificadores ficam em inglês**, como manda o [CLAUDE.md](../../CLAUDE.md#idioma):
`silver` e `gold` são os nomes no banco; *prata* e *ouro* seguem sendo os nomes em prosa,
na D-13 e na ARQUITETURA. Não é contradição, é a regra de idioma aplicada — mas é escolha, e
está listada em [riscos](#o-idioma-dos-nomes-de-esquema-é-escolha-desta-spec).

`core` é o quarto esquema, que a D-13 não previa: ela nomeia as três camadas de linhagem e
cala sobre o dado operacional. Sem ele, organização e usuário cairiam no `public` por
omissão — e a fronteira entre dado operacional e dado analítico viraria convenção em vez de
estrutura.

### Como uma tabela declara o esquema

**O Django 6.1 não tem opção de esquema.** Não existe `db_schema` em lugar nenhum da árvore
instalada, e `db/models/options.py:37` lista `db_table` entre as opções de `Meta`, sem par
para esquema. Como a seção da sonda já elimina o `search_path`, sobra um caminho, e ele é
contrato — não escolha de quem implementa:

```
class Meta:
    db_table = 'core"."organization'
```

O identificador vai com o esquema embutido e as aspas no meio. Funciona porque duas partes
do Django tratam identificador em duas peças, ambas conferidas na fonte:

- `db/backends/postgresql/operations.py:190-192` — `quote_name` não requota o que já tem
  aspas, então `core"."organization` sai como `"core"."organization"`
- `db/backends/base/schema.py:1550` — `_create_index_name` chama `split_identifier`, então o
  nome derivado de índice e de restrição não engole o esquema

**As tabelas M2M herdam o esquema sozinhas.** `db/models/fields/related.py:1997` monta o nome
como `strip_quotes(opts.db_table) + "_" + nome_do_campo`, e `strip_quotes`
(`db/backends/utils.py:335`) só tira aspas quando a string começa **e** termina com elas —
`core"."user` volta intacta, e a M2M vira `core"."user_groups`. Medido: aplicando este
contrato contra o `postgres:18`, as quatro tabelas do bloco nascem em `core`, os nomes de
índice e de restrição saem sem esquema embutido, e o `public` recebe exatamente as cinco
tabelas de encanamento da lista.

**As duas alternativas descartadas**, para que ninguém as re-derive:

- `ALTER TABLE ... SET SCHEMA` por `RunSQL` depois do `CreateModel` move a tabela no banco e
  **não** move o `db_table` do modelo. O ORM continua emitindo `"organization"` sem
  qualificação em toda consulta, e o `search_path` — que a sonda eliminou — voltaria a ser
  obrigatório em tempo de execução. O `makemigrations --check` não percebe nada disso: ele
  compara o estado reconstruído do grafo de migrations com o derivado dos `models.py`, e
  **nunca olha o banco**.
- `search_path` por conexão é o que a sonda eliminou, pelo motivo da seção dela.

### Onde cada tabela nasce, e por que o `public` não fica vazio

O `public` **guarda o encanamento do Django, e nunca dado de domínio**:

| Tabela | Esquema | Quem cria |
|---|---|---|
| `django_migrations` | `public` | o executor de migrations do Django |
| `django_content_type` | `public` | `django.contrib.contenttypes` |
| `auth_permission`, `auth_group`, `auth_group_permissions` | `public` | `django.contrib.auth` |
| `organization` | `core` | este bloco |
| `user` | `core` | este bloco |
| `user_groups`, `user_user_permissions` | `core` | este bloco, pelas M2M do `PermissionsMixin` |
| tudo que vier do M1.1 em diante | `bronze`, `silver`, `gold`, `core` | o bloco que o cria |

**A lista é fechada, e foi derivada das migrations do Django, não de memória.** Só
`contrib/auth/migrations/0001_initial.py` cria tabela em todo o app — nenhuma das outras onze
tem `CreateModel`; elas alteram campo, declaram dependência ou movem dado —, e nela o modelo
`User` é declarado `swappable: AUTH_USER_MODEL` (linha 196). Com
o modelo próprio deste bloco, **`auth_user` não nasce**; sobram `auth_permission`,
`auth_group` e `auth_group_permissions`. O `contenttypes` cria uma só, `django_content_type`.

**O banco está vazio hoje:** consulta ao `pg_tables` do banco `ruvor` devolve zero linhas
fora dos catálogos do sistema. `migrate` nunca rodou aqui, e é o que torna toda escolha
deste bloco ainda reversível.

**Isso foi medido, não suposto.** A alternativa — apontar o `search_path` para `core` e
deixar tudo cair lá — não é implementável sem um passo de preparação fora do ciclo de
migrations, porque o Django cria a tabela de controle antes de aplicar qualquer migration.
A medição está em [O que a sonda mostrou](#o-que-a-sonda-mostrou), e é o que sustenta este
contrato.

A fronteira, portanto, é **encanamento contra domínio**, não *vazio contra cheio*. Em troca,
`migrate` num banco vazio é a única coisa que qualquer ambiente precisa executar — sem
script de inicialização, sem permissão especial mantida em produção, e sem passo que só
funciona em volume novo.

### `Organization`

Tabela `organization`, no esquema `core`.

| Campo | Tipo | Regra |
|---|---|---|
| `id` | chave primária padrão do projeto | `DEFAULT_AUTO_FIELD` do Django 6.1 já é `BigAutoField` — conferido na fonte, não é preciso declarar |
| `name` | texto, `max_length=120` | obrigatório |
| `slug` | texto, `max_length=60`, **único** | chave estável de referência; é por ele que a organização do Marco 1 é encontrada, e não pelo `id` |
| `created_at` | data e hora | preenchido na criação |

Os comprimentos entram na migration e mudá-los depois é `AlterField` — por isso estão aqui, e
não deixados a critério de quem implementa.

**Não existe campo `personal` neste bloco.** A [D-24](../decisoes/D-24-organizacao-desde-a-primeira-migration.md)
prevê organização pessoal implícita para conta individual, mas nada no F4 nem no Marco 1 lê
esse sinal, e acrescentar coluna depois é migration aditiva barata — ao contrário do modelo
de usuário, que é o motivo de este bloco existir agora. Quem precisa do campo é o M2.1.

### `User`

Tabela `user`, no esquema `core`. Herda de `AbstractBaseUser` e `PermissionsMixin` — **não**
de `AbstractUser`.

| Campo | Tipo | Regra |
|---|---|---|
| `email` | texto, `max_length=254`, **único** | é o `USERNAME_FIELD` e o `EMAIL_FIELD` |
| `name` | texto, `max_length=120` | obrigatório |
| `organization` | chave estrangeira para `Organization`, `PROTECT` | **obrigatória** — é a D-08 aplicada ao usuário |
| `is_active` | booleano | padrão verdadeiro |
| `is_staff` | booleano | padrão falso |
| `created_at` | data e hora | preenchido na criação |

Herdados, e por isso ausentes da tabela mas presentes na migration: `password` e `last_login`,
de `AbstractBaseUser`; `is_superuser`, `groups` e `user_permissions`, de `PermissionsMixin`.

`REQUIRED_FIELDS` não inclui `email`, porque o `USERNAME_FIELD` nunca entra nessa lista —
é o que a verificação `auth.E002` do Django reprova.

**Por que `AbstractBaseUser` e não `AbstractUser`:** o `AbstractUser` traz `username` como
identificador e `first_name`/`last_name`. Trocar o `USERNAME_FIELD` depois é justamente a
migração cara que este bloco existe para evitar; e o produto autentica por e-mail, que é o
que o M2.1 vai construir. Escolher agora custa uma classe base.

**Por que `PermissionsMixin` entra:** ele acrescenta `is_superuser` e as duas relações para
`auth.Group` e `auth.Permission`. Sem ele, o `auth` fica instalado pela metade — presente
para sustentar o `AUTH_USER_MODEL`, inútil para qualquer outra coisa. É aditivo e barato
agora; depois, é migração sobre a tabela de usuário.

Acompanha um gerente com `create_user` e `create_superuser` que **exigem organização** —
sem ele, `createsuperuser` não tem como criar usuário válido, já que o campo é obrigatório.

### O filtro por organização: a coluna nasce aqui, o filtro não

A [D-24](../decisoes/D-24-organizacao-desde-a-primeira-migration.md) é explícita: *"o que
isola não é a coluna, é a consulta filtrar. Uma classe base aplica o filtro por padrão, para
que esquecer deixe de ser possível."*

Este bloco entrega **a coluna** — o `organization` obrigatório do `User` — e **não** a classe
base. O motivo está em [por que o filtro automático é adiado](#por-que-o-filtro-automático-é-adiado)
e vira decisão registrada, porque contradiz a
[ARQUITETURA](../ARQUITETURA.md#isolamento-por-organização) por escrito.

O contrato que atravessa para o M2.2, e que a decisão precisa fixar:

- **A primeira tabela privada de domínio nasce junto com o filtro automático.** Não existe
  tabela privada nova sem ele; é obrigação do bloco que a cria, não dívida difusa.
- **O `user` é exceção permanente, não pendência.** Os backends de autenticação do Django
  alcançam o modelo por `UserModel._default_manager` — dez ocorrências em
  `django/contrib/auth/backends.py`, conferidas na fonte —, e um gerente que recusasse
  consulta sem escopo quebraria `authenticate` inteiro. Não é buraco: a busca do usuário no
  login é necessariamente anterior a saber a qual organização ele pertence.

### A organização do Marco 1

A [D-08](../decisoes/D-08-dono-do-dado-no-schema.md) diz: *"durante o Marco 1 existe um dono
fixo e a interface nunca menciona isso."* Este bloco cria esse dono.

- Nasce por **migration de dados**, não por comando manual nem por fixture
- `name` = **`Ruvor`** e `slug` = **`ruvor`**. Os dois valores são o contrato; o `slug` é a
  chave estável pela qual todos os blocos seguintes a encontram, e está escrito aqui para
  que ninguém o invente
- A migration é **idempotente**: rodar de novo não duplica nem falha
- O `id` **não** é congelado; nada pode depender dele valer `1`

### Convenção de migration

O que o M1.1 em diante herda:

- **Toda migration é versionada e revisada como código.** Não existe alteração de esquema
  aplicada à mão no banco.
- **Migration de esquema e migration de dados não se misturam** no mesmo arquivo.
- **Migration de dados é idempotente** e não importa modelo do `models.py` — usa o modelo
  histórico que o `apps.get_model` devolve, que é o único que corresponde ao estado daquele
  ponto da história.
- **Nome descritivo**, não o gerado automaticamente: `0002_marco1_organization`, não
  `0002_auto_20260904_1530`.
- **Migration é reversível, ou declara por que não é.** O `RunSQL` que cria os esquemas leva
  `reverse_sql`; sem ele a `0001` fica irreversível e `migrate accounts zero` deixa de
  funcionar, que é o caminho normal de refazer o bloco enquanto não há dado.
- **Tabela nova declara o esquema** em que mora. Não existe tabela de domínio sem esquema
  declarado.

### Variáveis de ambiente

**Nenhuma variável nova.** O `slug` da organização do Marco 1 é constante do código, não
configuração: se fosse variável, dois ambientes teriam donos diferentes para o mesmo dado, e
a migration de dados deixaria de ser reproduzível.

---

## O que a sonda mostrou

A alternativa natural — `search_path` apontando para `core`, tudo caindo lá, `public` vazio —
foi medida contra o PostgreSQL 18 do próprio `compose`, num banco de sonda criado e removido
durante a escrita desta spec. O banco `ruvor` não foi tocado.

| `search_path` | `core` existe? | Resultado de `CREATE TABLE` sem qualificar |
|---|---|---|
| `core` | não | **erro** — `no schema has been selected to create in` |
| `core,public` | não | a tabela nasce em **`public`**, sem aviso |
| `core,public` | sim | a tabela nasce em `core` |

A esperança seria a ordem resolver: se a primeira migration criasse os esquemas, a
`django_migrations` nasceria depois, já em `core`. **Não resolve.**
`MigrationExecutor.migrate()` chama `self.recorder.ensure_schema()` antes de aplicar o plano
— `django/db/migrations/executor.py:109` — sempre que há algo a aplicar. A tabela de
controle é criada primeiro, e nenhuma migration chega antes dela.

Sobram três saídas, e as três foram pesadas:

| Saída | O que custa |
|---|---|
| **Esquema criado fora do ciclo de migrations** (script de inicialização) | só roda em volume novo; quem já tem banco recebe a divisão silenciosa da linha 2 da tabela. E o F5 e a hospedagem herdam a obrigação de repetir o passo, num ambiente que ainda não foi escolhido |
| **`CREATE SCHEMA` a cada conexão** | DDL em toda conexão, e o usuário do banco precisa manter permissão de criação para sempre, inclusive em produção |
| **`public` guarda o encanamento** ← escolhida | o `public` não fica vazio. Em troca, não existe passo nenhum fora do `migrate` |

A escolha segue o princípio que o projeto já aplica em outros lugares: **erro silencioso é
pior que cerimônia.** As duas primeiras saídas dependem de alguém lembrar de um passo, e a
falha, quando vier, é a tabela nascendo no esquema errado sem ninguém perceber — que é o
defeito mais caro que existe aqui.

---

## Verificação

### Critérios executáveis

| Requisito | Verificação |
|---|---|
| **F4-01** | Consulta ao catálogo do PostgreSQL depois do `migrate`: os quatro nomes de esquema estão presentes |
| **F4-02** | Consulta que lista esquema e tabela de tudo que existe no banco, e confere contra a lista fechada da seção [Onde cada tabela nasce](#onde-cada-tabela-nasce-e-por-que-o-public-não-fica-vazio). Nenhuma tabela de app do projeto no `public`, e nenhuma tabela do encanamento fora dele |
| **F4-03** | Depois do `migrate`, existe **exatamente uma** organização com o `slug` congelado. Rodar `migrate` de novo mantém exatamente uma |
| **F4-04** | `settings.AUTH_USER_MODEL` aponta para o modelo do projeto; a primeira migration do app **contém** a criação do usuário, e migration posterior reprova; e criar usuário sem organização falha nas **duas camadas**, provadas separadamente: o gerente recusa a chamada, e o campo é `NOT NULL` no banco |
| **F4-05** | `migrate` contra banco vazio devolve código 0; a segunda execução devolve 0 e não aplica nada |
| **F4-06** | `makemigrations --check --dry-run` devolve código 0 |
| **F4-07** | `mypy` dentro do contêiner passa, e a lista de arquivos verificados **inclui** os módulos novos — contar arquivos não basta, a lista precisa nomeá-los |
| **F4-08** | A suíte do backend passa dentro do contêiner; o teste de `GET /health` do F2b continua passando sem marca de banco |
| **F4-09** | A imagem reconstrói do zero e o `pip install -e "./backend[dev]"` conclui |
| **F4-10** | Varredura sobre a [lista fechada de trechos](#o-que-fica-falso) que passam a mentir, provando que nenhum sobreviveu — e que a própria varredura reprova contra os arquivos de hoje. **Mais uma ausência:** a tabela "Dívida registrada" do `ESTADO.md` precisa conter a linha do filtro adiado, e a verificação reprova se ela faltar |

### Onde cada verificação mora

Mesma divisão que o F3 estabeleceu, e pelo mesmo motivo: ela decide o que a suíte passa a
exigir.

| Forma | Quais | Onde |
|---|---|---|
| **Teste da suíte do backend** | F4-01, 02, 03, 04, 08 | `backend/tests/` |
| **Comando sobre o conjunto** | F4-05, 06, 07, 09, 10 | invocação de uma linha, escrita **literalmente** no critério de aceite da tarefa do plano |

**A suíte do backend passa a exigir um banco migrado**, e não apenas alcançável, como no F3.
É consequência declarada: F4-01, 02 e 03 leem o estado do banco. Os testes que precisam
disso usam o mesmo mecanismo de desbloqueio que o `test_conexao_com_o_banco` do F3 já usa —
`django_db_blocker` —, porque a marca `django_db` conecta em `test_<nome>`, que é banco
recriado pelo pytest e **não** é o banco que o `migrate` do dia a dia toca.

**Nenhum arquivo de script é criado.** Continua valendo o que o F3 decidiu: as verificações
de conjunto são comandos, e escrevê-las como script antes de o F5 existir é inventar a forma
que a CI vai querer.

### Cada família de verificação prova que sabe reprovar

O padrão do F2b e do F3 vale aqui. O plano registra a mutação, a execução e a saída de cada
uma:

| Mutação | Precisa reprovar |
|---|---|
| Remover um dos quatro `CREATE SCHEMA` da migration | F4-01 |
| Remover o esquema de um dos modelos, deixando a tabela cair no `public` | F4-02 |
| Deixar a migration de esquemas depender de passo manual, fora do `migrate` | F4-05 |
| Fazer a view do `/health` tocar no banco | F4-08 |
| Declarar o pacote novo sem copiá-lo no `Dockerfile` | F4-09 |
| Trocar a migration de dados por uma que crie a organização sem verificar se já existe | F4-03, na segunda execução |
| Mover a criação do usuário para uma segunda migration | F4-04 |
| Tirar a exigência de organização do `create_user` | F4-04, camada do gerente |
| Declarar o `organization` do usuário com `null=True` | F4-04, camada do banco |
| Acrescentar campo ao modelo sem gerar migration | F4-06 |
| Deixar o pacote novo fora de `[tool.mypy] files` | F4-07 |

**A mutação do `/health` é pela view, não pelo teste.** Acrescentar `pytest.mark.django_db`
ao teste **não** o faz falhar — a marca *concede* acesso ao banco, nunca exige que ele seja
usado, e foi medido que a suíte segue passando com ela. Quem garante F4-08 é o bloqueio do
pytest-django sobre o teste **sem** marca: por isso a mutação mexe na view, e o teste
existente precisa quebrar com acesso a banco não permitido.

A mutação do `public` é a mais importante das onze: é exatamente o defeito que a sonda
mostrou acontecer **em silêncio**.

### Verificação de tipos

`backend/pyproject.toml` declara hoje `files = ["config", "manage.py", "tests"]` — conferido
no arquivo. O pacote novo entra nessa lista, senão o mypy passa a aprovar por omissão: o
código novo simplesmente não é olhado, e "mypy passa" vira verdade vazia.

O mesmo vale para `[tool.setuptools] packages = ["config"]`, que hoje existe com um
comentário explicando que a declaração explícita evita a descoberta automática falhar. O
pacote novo precisa entrar lá também — e é daí que sai o risco de construção da imagem, na
seção seguinte.

---

## Inventário dos arquivos existentes

Todo arquivo que este bloco toca, com destino. O que não está na lista, o bloco não toca.

### Altera

| Arquivo | O que muda |
|---|---|
| `backend/config/settings.py` | `INSTALLED_APPS` recebe `contenttypes`, `auth` e o app novo; nasce `AUTH_USER_MODEL` |
| `backend/pyproject.toml` | `[tool.setuptools] packages` e `[tool.mypy] files` passam a cobrir o pacote novo |
| `infra/backend.Dockerfile` | **vai exigir** mudança, e a razão está medida — ver [abaixo](#a-imagem-quebra-ao-declarar-o-pacote-novo-e-isso-foi-medido) |
| `README.md` | a tabela "Comandos do dia a dia" ganha a linha do `migrate`. **Só isso** — o resumo do backend, que diz apenas que o Django responde `GET /health` e conecta no PostgreSQL, continua verdadeiro depois do F4 |
| `CLAUDE.md` | "projeto Django sem app de domínio" deixa de ser verdade |
| `docs/ESTADO.md` | passo FECHA **e** uma linha nova na tabela "Dívida registrada": o filtro automático por organização, adiado para o M2.2 |
| `docs/ROADMAP.md`, `docs/aprendizados.md` | passo FECHA |
| `docs/ARQUITETURA.md` | a nota "`apps/` nasce no F4" cumpre-se; a tabela de esquemas ganha o `core` |
| `docs/specs/README.md`, `docs/planos/README.md` | as tabelas de índice |

**`backend/config/settings.py` não ganha middleware.** Conferido em
`django/contrib/auth/checks.py`: a exigência de `AuthenticationMiddleware` só existe quando
`LoginRequiredMiddleware` está presente — `auth.E013`, linha 258 —, e ela não está. O `auth`
instalado sozinho não impõe middleware nenhum. Sessão e autenticação de requisição são do
M2.1.

**`backend/config/settings_test.py` não muda.** Ele preenche variáveis e reexporta
`config.settings`; nada no F4 acrescenta variável obrigatória.

**`backend/config/celery.py` não muda.** O comentário dele explica que o registro é por
import explícito porque `INSTALLED_APPS` não continha o `config`. Isso continua verdadeiro:
o app novo entra em `INSTALLED_APPS`, mas ele não tem tarefa nenhuma, e a descoberta
automática continua sem alcançar `config.tasks`. Mexer aqui seria mudança sem requisito.

### Cria

| Arquivo | Conteúdo |
|---|---|
| `backend/apps/__init__.py` | pacote |
| `backend/apps/accounts/__init__.py`, `apps.py` | app |
| `backend/apps/accounts/models.py` | `Organization` e `User` |
| `backend/apps/accounts/managers.py` | o gerente do usuário, com `create_user` e `create_superuser` exigindo organização |
| `backend/apps/accounts/migrations/__init__.py` | sem ele o Django não enxerga o pacote de migrations |
| `backend/apps/accounts/migrations/0001_esquemas_organization_user.py` | os quatro esquemas **e** os dois modelos, nesta ordem |
| `backend/apps/accounts/migrations/0002_marco1_organization.py` | a organização do Marco 1 |
| `backend/tests/test_esquemas.py` | F4-01 e F4-02 — os quatro esquemas existem, e cada tabela está no esquema declarado |
| `backend/tests/test_organizacao.py` | F4-03 — existe exatamente uma organização com o `slug` congelado |
| `backend/tests/test_usuario.py` | F4-04 — `AUTH_USER_MODEL` aponta para o modelo do projeto, e usuário sem organização falha |

**Os quatro esquemas e os dois modelos ficam na mesma migration**, e a ordem das operações
importa: `CREATE SCHEMA` antes de `CreateModel`, senão a tabela não tem onde nascer. Separar
em duas migrations funcionaria igual; ficam juntas porque uma migration inicial que deixa o
banco inutilizável no meio não tem por que existir.

### O que fica falso

Lista fechada, derivada dos arquivos, que a varredura de F4-10 precisa cobrir:

| Onde | Trecho |
|---|---|
| `CLAUDE.md` | "projeto Django sem app de domínio" |
| `CLAUDE.md` | "Existem o **motor**, o **casco da aplicação** e o **ambiente local em contêiner**. Ainda não existe API de negócio nem tela de produto." — a segunda frase continua verdadeira; a primeira precisa citar a fundação de dados |
| `docs/ESTADO.md` | "Ainda não há migrations, API de negócio nem tela de produto" |
| `docs/ESTADO.md` | "**Bloco:** F3 fechado e integrado; **F4 é o próximo**" |
| `docs/ESTADO.md` | a seção "Próximo passo" inteira, que manda escrever esta spec |
| `docs/ESTADO.md` | "`INSTALLED_APPS` ainda é só `rest_framework`: o F4 vai precisar de pelo menos parte de `contenttypes`/`auth`" — é afirmação factual, não status, e o F4 a falsifica |
| `docs/ARQUITETURA.md` | "`apps/` nasce no F4" — nota de estado alvo que deixa de ser futuro |
| `docs/ROADMAP.md` | a linha do F4 na tabela da Fundação, marcada ⬜ |
| `docs/specs/README.md`, `docs/planos/README.md` | as tabelas de índice, que não têm linha do F4 |
| `README.md` | "Comandos do dia a dia", que não tem linha de `migrate` |

O `README.md` afirma também, sobre o `/health`: *"É a única rota."* **Continua verdadeiro** —
o F4 não cria endpoint. Está na lista para não ser removido por engano.

---

## Decisões que esta spec assume

- [D-08](../decisoes/D-08-dono-do-dado-no-schema.md) — dono do dado no esquema desde a primeira migration
- [D-11](../decisoes/D-11-pilha-tecnologica.md) — Django e PostgreSQL
- [D-12](../decisoes/D-12-tipagem-obrigatoria.md) — tipagem obrigatória
- [D-13](../decisoes/D-13-camadas-bronze-prata-ouro.md) — bronze, prata e ouro como esquemas
- [D-24](../decisoes/D-24-organizacao-desde-a-primeira-migration.md) — Organização desde a primeira migration (o filtro por padrão que ela também manda é o que esta spec adia, e registra)
- [D-31](../decisoes/D-31-trabalho-direto-na-main.md) — trabalho direto na `main`
- [D-33](../decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) — o dia a dia do backend roda no contêiner
- [D-36](../decisoes/D-36-versao-do-postgres.md) — PostgreSQL 18

### Decisões novas que este bloco produz

Cada uma vira registro em `decisoes/` **junto com a aprovação desta spec**, porque o
[PROCESSO](../PROCESSO.md#spec-não-é-documento-vivo) proíbe contradição silenciosa:

| Decisão nova | Por quê |
|---|---|
| Existe um quarto esquema, `core`, para o dado operacional | a [D-13](../decisoes/D-13-camadas-bronze-prata-ouro.md) nomeia três camadas e cala sobre o resto; a [ARQUITETURA](../ARQUITETURA.md#banco-e-camadas-de-dado) repete as três |
| O `public` guarda o encanamento do Django | é o contrário do que "esquemas nomeados para tudo" sugere, e a razão é uma medição — precisa ficar registrada, senão alguém a re-deriva |
| O usuário do projeto herda `AbstractBaseUser` e autentica por e-mail | atravessa para o M2.1 inteiro, e é a decisão que não se refaz barato |
| Os identificadores de esquema ficam em inglês (`silver`, `gold`) | a prosa do projeto diz *prata* e *ouro*; sem registro, o M1.2 escreve `prata` no `db_table` |
| O filtro automático por organização é obrigação da primeira tabela privada de domínio, e o `user` é exceção permanente | contradiz a [ARQUITETURA](../ARQUITETURA.md#isolamento-por-organização) — *"uma classe base aplica o filtro por organização por padrão"* e *"coluna sem filtro automático é teatro"* —, e a tabela ao lado lista **Usuários** como privado da organização |

---

## Riscos e questões em aberto

### A imagem quebra ao declarar o pacote novo, e isso foi medido

O `infra/backend.Dockerfile` instala o backend copiando **apenas** `backend/pyproject.toml`
e `backend/config/__init__.py`, e então roda `pip install --no-cache-dir -e "./backend[dev]"`.
O `pyproject.toml` declara `packages = ["config"]` explicitamente.

Acrescentar o pacote novo a essa lista faz o `pip install` da imagem referenciar um diretório
que **não foi copiado** para o contexto de construção. Não é hipótese — foi medido, com
`packages = ["config", "apps"]` e `backend/apps/` ausente:

```
error: package directory 'apps' does not exist
error: metadata-generation-failed
```

Quebra na imagem, não no hospedeiro, onde o diretório existe. **A correção é contrato deste
bloco, não escolha de quem implementa:** o `Dockerfile` passa a copiar também os
`__init__.py` do pacote novo antes do `pip install`, exatamente como já faz com o `config`.

Também foi medido que `packages = ["config", "apps"]` **basta** — o subpacote `apps.accounts`
não precisa ser listado. Isso vale para a instalação editável, que é a única que este
repositório usa; uma construção de distribuição exigiria a lista completa, e não existe.

### Por que o manifesto não entra aqui

O manifesto da [D-15](../decisoes/D-15-manifesto-de-execucao.md) registra algoritmo, versão
do código, hiperparâmetros, semente, base de dados e data de coleta. **Quais hiperparâmetros
existem é propriedade do motor**, e o motor está congelado até a Etapa 6
([D-21](../decisoes/D-21-motor-ml-congelado-ate-etapa-6.md)). Modelar as colunas agora seria
derivá-las de memória — o primeiro dos seis padrões de defeito registrados em
[aprendizados.md](../aprendizados.md). O M1.4 integra o motor e é lá que a lista é derivada
da fonte.

Consequência aceita: o esquema `gold` nasce vazio e continua vazio até o M1.4.

### Por que o filtro automático é adiado

A saída natural seria entregar aqui a base abstrata com o gerente que recusa consulta sem
escopo. Ela foi descartada, e a razão é medida, não estética: **um gerente padrão que levanta
erro colide com o ORM em pontos que este bloco não consegue alcançar.** Conferido na fonte
do Django 6.1:

| Onde | O que quebra |
|---|---|
| `db/models/base.py:1571` e `:1612` | `_perform_unique_checks` passa por `_default_manager` — todo `full_clean()`/`validate_unique()` levantaria |
| `db/models/fields/related_descriptors.py:680` e `:1060` | o acessor reverso é construído a partir de `_default_manager.__class__`; `org.portfolios.all()`, no M2.2, nasceria levantando |
| `db/models/fields/related.py:1298` e `:2138` | `formfield` também passa por `_default_manager` |

E o agravante: **o F4 não tem modelo concreto**, então nenhuma dessas colisões seria
detectável dentro do bloco. Ele entregaria verde um contrato que o primeiro consumidor real
não conseguiria usar — que é o pior resultado possível para um artefato cujo propósito é ser
copiado pelos blocos seguintes.

Então o F4 entrega **a coluna e a regra**, e o M2.2 entrega o mecanismo, junto da primeira
tabela privada de domínio — onde há contra o que provar: acessor reverso, `full_clean`,
`base_manager_name` e o resto.

**A dívida fica registrada**, em decisão e em `ESTADO.md`, e é o que impede que "adiado"
vire "esquecido". Se ela for honrada, a D-24 é cumprida no momento em que passa a ter
sentido; se não for, o defeito é o mesmo que a D-24 descreve — e o registro é o que permite
alguém cobrar.

### O idioma dos nomes de esquema é escolha desta spec

`silver` e `gold` contra `prata` e `ouro`. A regra de idioma do
[CLAUDE.md](../../CLAUDE.md#idioma) manda inglês em nome de variável, função e classe, e não
menciona nome de tabela nem de esquema. A spec estende a regra, porque nome de esquema é
identificador de código como os outros — mas a extensão é interpretação, e o portão humano é
o lugar de derrubá-la. Derrubar custa uma busca e substituição, hoje; depois do M1.2, custa
migração.

### O `public` continua alcançável

Este bloco impede que tabela de domínio **nasça** no `public`, e prova isso por consulta ao
catálogo depois do `migrate`. Não impede que alguém, no futuro, crie uma lá de propósito. A
garantia viva é a verificação de F4-02, que precisa continuar rodando à medida que M1.1 e
M1.2 acrescentam tabelas — e é por isso que ela confere contra **lista fechada**, e não
contra amostra.

### Não há dado para migrar

Nenhum ambiente tem tabela de domínio hoje, então toda escolha deste bloco ainda é
reversível por `docker compose down -v` e um `migrate` novo. **É a última vez.** A partir do
M1.2, com preços dentro, mudar esquema, nome de tabela ou modelo de usuário passa a exigir
migração de dados. É a razão de o bloco existir antes do Marco 1, e não durante.
