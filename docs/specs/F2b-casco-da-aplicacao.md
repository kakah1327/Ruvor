# F2b — Casco da aplicação

**Bloco:** Fundação · F2b
**Status:** revisão adversarial aprovada · aguardando portão humano
**Depende de:** [F2a — Migração do motor](F2a-migracao-do-motor.md)

---

## Problema

A [arquitetura alvo](../ARQUITETURA.md#pilha-tecnológica) define Django no backend e React no
frontend. Nenhum dos dois existe: o backend é Flask e o frontend é uma aplicação React que
será descartada com a API que ela consome.

Sem os dois processos existindo, o F3 não tem o que subir no `docker compose` e o F4 não tem
onde criar migrations.

## Resultado esperado

1. O servidor de desenvolvimento do Django sobe e responde à rota de saúde
2. O servidor de desenvolvimento do React sobe e renderiza a tela de verificação
3. A tela usa os tokens de `brand/ruvor/tokens.css` — nenhuma cor escrita à mão
4. A verificação de tipos passa nos dois lados
5. Nenhum arquivo do frontend do protótipo permanece

## Escopo

### Dentro

- Projeto Django funcional, **sem apps de domínio**, com uma rota de saúde
- Projeto React funcional, com uma tela de verificação usando a identidade Ruvor
- Consumo dos tokens da marca pelo frontend
- Verificação de tipos rigorosa nos dois lados
- Variáveis de ambiente que o Django exige
- Remoção completa do frontend do protótipo

### Fora

| Fora do escopo | Onde entra |
|---|---|
| Qualquer app de domínio, modelo ou endpoint de negócio | Marco 1 |
| Migrations e conexão com banco | F4 |
| Celery, Redis, fila | F4 |
| `docker compose` | F3 |
| Integração contínua | F5 |
| Qualquer tela de produto | Marco 1 |
| Autenticação, organizações, permissões | F4 e Marco 2 |

## Requisitos

| ID | Requisito |
|---|---|
| **F2b-01** | Projeto Django sobe e responde `GET /health` conforme o contrato abaixo |
| **F2b-02** | Django não depende de banco para subir nem para responder a rota de saúde |
| **F2b-03** | Projeto React sobe e renderiza a tela de verificação |
| **F2b-04** | O frontend consome `brand/ruvor/tokens.css`; nenhum valor de cor escrito à mão |
| **F2b-05** | Frontend em TypeScript, com verificação estrita habilitada |
| **F2b-06** | Verificação de tipos do Django em modo estrito sobre `backend/` |
| **F2b-07** | `.env.example` da raiz lista as variáveis que o Django exige |
| **F2b-08** | Todo o frontend do protótipo é removido |
| **F2b-09** | Verificação automatizada de que não há valor de cor literal em `frontend/src/` |
| **F2b-10** | Teste de fumaça do frontend: a tela renderiza a marca e o estado do backend |

---

## Contratos externos

Congelados a partir da aprovação. O F3 e o F5 consomem a rota de saúde.

### Rota de saúde

```
GET /health
200  {"status": "ok"}
```

Sem autenticação, sem consulta a banco. É o que o `docker compose` do F3 usa como
verificação de vida do contêiner e o que o F5 usa como teste de fumaça.

> **Nota sobre o escopo.** A seção "Fora" exclui *endpoints de negócio*. A rota de saúde é
> infraestrutura, não domínio: não expõe dado, não tem regra e existe para que outros blocos
> saibam que o processo está vivo. Sem ela, o F3 não tem como verificar o contêiner.

### Variáveis de ambiente

Prefixo `RUVOR_*` reservado para configuração própria. O Django exige:

| Variável | Uso |
|---|---|
| `RUVOR_SECRET_KEY` | chave de assinatura do Django |
| `RUVOR_DEBUG` | modo de depuração |
| `RUVOR_ALLOWED_HOSTS` | domínios aceitos |

Variáveis de banco entram no F4. As do frontend seguem o prefixo `VITE_*` exigido pelo Vite
— convenção da ferramenta, não do projeto.

### Estrutura criada

```
backend/
├── pyproject.toml   <- dependencias e configuracao do mypy do backend
├── config/             settings, urls, wsgi, asgi
└── manage.py

frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.example
└── src/
```

Sem `apps/` — o primeiro app de domínio nasce no F4. O diagrama da
[ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) mostra `backend/apps/` porque
descreve o **estado alvo**, não este bloco.

### Onde as dependências do backend são declaradas

Em **`backend/pyproject.toml`**, projeto Python próprio, independente do
`engine/pyproject.toml`.

O F2a remove o `pyproject.toml` da raiz e estabelece **um projeto Python por diretório**
([F2a — empacotamento](F2a-migracao-do-motor.md#empacotamento)). O F2b segue a mesma regra.

Declarações mínimas deste bloco: Django, Django REST Framework, mypy, `django-stubs`,
**pytest e `pytest-django`**.

O runner de teste não é opcional: sem ele, F2b-01 e F2b-02 só se verificariam a olho, o que a
[regra dura do PROCESSO §5](../PROCESSO.md#regra-dura) proíbe — e seria incoerente exigir
Vitest do lado do React pelo mesmo motivo.

Sem Celery, sem driver de banco — entram no F4. **Sem `ruvor-engine`**: o backend não importa
o motor neste bloco (ver [riscos](#o-django-não-pode-importar-o-motor-ainda)).

### Como o backend é instalado

`backend/` **não é pacote distribuível** — é um projeto Django. Seu `pyproject.toml` existe
para declarar dependências e configurar ferramentas, e declara `config` como seu único pacote
de forma explícita, evitando a descoberta automática do setuptools, que falharia com
`manage.py` e `config/` lado a lado.

Instalação: `pip install -e ./backend`.

**Um ambiente virtual só para todo o repositório**, na raiz — o `.gitignore` já prevê `.venv/`
único. "Um projeto Python por diretório" é regra de **declaração**, não de ambiente: em
desenvolvimento os dois convivem no mesmo interpretador. A separação real acontece no F3, em
imagens Docker diferentes.

---

## O frontend nasce do zero

O projeto React do protótipo é **removido inteiro**, não adaptado:

| Removido | Motivo |
|---|---|
| `frontend/src/` | telas e componentes de uma API que deixa de existir |
| `frontend/vite.config.js` | o proxy aponta para o Flask em `:5000`, que morre |
| `frontend/package.json`, `package-lock.json` | dependências do protótipo |
| `frontend/index.html` | título "VaR Lab" |
| `frontend/.env.example` | `VITE_API_BASE_URL` do Flask |
| `frontend/.oxlintrc.json`, `public/favicon.svg` | configuração e ícone do protótipo |
| `frontend/.gitignore` | recriado pelo projeto novo; não reaproveitado |

Também é do F2b atualizar as **instruções de frontend no `README.md`** — elas mandam subir o
servidor do protótipo. O F2a cuida da parte Python do mesmo arquivo.

O corte não é por seção: o bloco de comandos do README mistura `pip install` e `npm run dev`
nas mesmas linhas. Como o F2a vem primeiro, ele deixa o bloco consistente com o que sobrou, e
o F2b o completa.

**TypeScript, não JavaScript.** O protótipo era JavaScript puro. A razão de
[D-12](../decisoes/D-12-tipagem-obrigatoria.md) — o time vem de C#, Java e Angular, e produz
mais com o compilador avisando antes de rodar — vale igual no frontend. Registrado como
[D-28](../decisoes/D-28-frontend-em-typescript.md).

**Dependências mínimas.** O projeto nasce só com o necessário para subir e renderizar.
Biblioteca de gráfico, roteamento e fonte entram quando houver tela que as use, no Marco 1 —
não antes.

O favicon usa `brand/ruvor/ruvor-mark.svg`, **copiado para `frontend/public/`**.

O destino importa: em `frontend/src/` o arquivo cairia sob a varredura do F2b-09 e reprovaria
pelo `fill="#292A2E"` do próprio símbolo. É a única exceção à regra de não copiar de `brand/`, e o motivo é técnico: o
`<link rel="icon">` do HTML não resolve apelido de caminho do empacotador. Símbolo de marca
não muda com frequência; token de cor sim — daí a assimetria.

**As fontes da marca não são instaladas neste bloco.** `tokens.css` declara Inter e JetBrains
Mono com pilha de reserva; a tela do casco técnico renderiza com a fonte de reserva, e isso é
aceito. Instalar arquivo de fonte para uma tela de fumaça contraria "dependências mínimas".
As fontes entram no Marco 1, com a primeira tela de produto.

---

## Como o frontend alcança o backend

**Proxy do servidor de desenvolvimento do Vite**, encaminhando para o Django em `:8000`.

Escolha deliberada sobre a alternativa (URL absoluta com CORS): o proxy mantém tudo na mesma
origem em desenvolvimento, o que **elimina a necessidade de `django-cors-headers`** — uma
dependência a menos e uma superfície de configuração a menos, num bloco cuja única função é
provar que os processos sobem.

| Variável do frontend | Valor padrão | Uso |
|---|---|---|
| `VITE_API_BASE_URL` | vazio | vazio significa mesma origem; preenchido, aponta para outro host |

`frontend/.env.example` é **recriado** com essa única variável. O prefixo `VITE_` é exigência
da ferramenta, não convenção do projeto — variáveis do backend seguem `RUVOR_*`.

**O proxy encaminha `/health`.** A rota de saúde fica na raiz, conforme o contrato acima —
não sob `/api`, porque não é API de negócio. O prefixo `/api` entra no Marco 1, quando existir
recurso a expor, e passa a ser um segundo caminho encaminhado.

Porta do Django em desenvolvimento: **8000**. Porta do Vite: a padrão da ferramenta.

---

## Como o frontend consome os tokens

`brand/ruvor/tokens.css` está fora da raiz do frontend.

**Decisão: apelido de caminho na configuração do Vite** — `@brand` apontando para
`brand/ruvor/`, com a raiz do repositório liberada para leitura pelo servidor de
desenvolvimento.

Duas alternativas foram descartadas:

| Alternativa | Por que não |
|---|---|
| Declarar `brand/` como dependência local do npm | obrigaria a criar um `package.json` dentro de `brand/`, que é documento que **manda** na identidade visual — mexer nele por conveniência do frontend inverte a relação |
| Copiar o arquivo para dentro do frontend | duas cópias divergem; `brand/` deixaria de ser fonte única |

**O F2b consome apenas `tokens.css`.** O kit tem outras duas folhas — `implementation.css`
(referência de componentes) e `mockups/foundation.css` (padrões dos mockups) — e **nenhuma
das duas entra neste bloco**: são referência de leitura para quem constrói tela de produto, e
a `foundation.css` usa dezenas de cores literais, que reprovariam na verificação do F2b-09.

**O F2b não altera nada dentro de `brand/`.** O diretório é consumido, nunca modificado.

### Tema: claro apenas

`brand/ruvor/tokens.css` define **só o tema claro**; o modo escuro segue como
[lacuna conhecida do kit](../../brand/ruvor/README.md#lacunas-conhecidas).

O F2b usa o que existe. Não inventa tema escuro, e não decide a questão de produto — que
segue aberta em [ESTADO.md](../ESTADO.md). Quando o kit ganhar o tema escuro, o frontend
passa a suportá-lo sem retrabalho, porque não haverá cor escrita à mão para caçar.

---

## Portão de mockup: fora do escopo por definição

A tela do F2b-03 é **casco técnico**, não tela de produto, e portanto está fora do portão de
mockup por definição — não por dispensa concedida nesta spec.

A distinção está registrada na
[D-30](../decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md) e refletida no
[PROCESSO §7](../PROCESSO.md#7-portão-de-mockup) e no `CLAUDE.md`. Sem esse registro, um
implementador que lesse as regras invioláveis primeiro encontraria contradição.

Conteúdo da tela: a marca Ruvor, o nome, e a confirmação de que o backend respondeu à rota de
saúde. Nada além disso — sem layout, navegação ou hierarquia a decidir.

**O F2b não deriva nada de `brand/ruvor/mockups/`.** Aquelas quatro telas são a linguagem
visual do produto e servem ao Marco 1 em diante; o casco técnico não tem tela de produto que
as consuma.

O portão vale integralmente a partir da primeira tela de produto, no Marco 1.

---

## Verificação

### Tipos

Rigor alto nos dois lados, conforme a
[D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md): aqui todo o código nasce
agora, então rigor é de graça — e adicioná-lo depois custa caro.

| Lado | Ferramenta | Rigor |
|---|---|---|
| `backend/` | mypy em modo estrito, **com `django-stubs` e o plugin do Django** | estrito |
| `frontend/` | TypeScript | `strict` habilitado |

O `django-stubs` não é opcional: mypy estrito sobre um projeto Django sem ele reprova no
código que o próprio `django-admin` gera. Sem o plugin, a alternativa seria relaxar o
"estrito", o que esvaziaria o requisito.

### Critérios executáveis

O [PROCESSO §5](../PROCESSO.md#regra-dura) exige critério de aceite executável por tarefa.
Os dois requisitos visuais ganham verificação automatizada:

| Requisito | Verificação |
|---|---|
| **F2b-09** — sem cor literal | Varredura em `frontend/src/` que falha ao encontrar qualquer cor literal. Cor só entra por token |
| **F2b-10** — a tela funciona | Teste de renderização que confirma a presença da marca e do indicador de estado do backend |

O padrão de varredura do F2b-09 cobre, no mínimo: hexadecimal de 3, 4, 6 e 8 dígitos
(`#fff`, `#ffff`, `#ffffff`, `#ffffffff`), as funções `rgb(`, `rgba(`, `hsl(`, `hsla(`,
`oklch(`, `lab(`, e a lista fechada de nomes: `white`, `black`, `red`, `green`, `blue`,
`gray`, `grey`, `silver`, `orange`, `yellow`, `purple`, `navy`, `teal`.

**Os nomes casam só em posição de valor**, não em qualquer lugar do texto. Sem essa
disciplina o critério gera falso positivo garantido: `red` casaria `required` e `rendered`, e
mesmo com limite de palavra `white` casaria `white-space`, que é propriedade CSS legítima.

Vale notar que `rgba(` circula legitimamente no projeto — `tokens.css` usa em
`--ruvor-shadow` —, mas dentro de `brand/`, que não é alvo da varredura.

O frontend nasce com **Vitest** — mínimo necessário para que F2b-10 seja executável e não
opinião. É dependência de desenvolvimento, e a alternativa seria aceitar "ficou bom", que a
regra dura proíbe.

---

## Decisões que esta spec assume

- [D-11](../decisoes/D-11-pilha-tecnologica.md) — Python, Django, DRF, React, PostgreSQL
- [D-12](../decisoes/D-12-tipagem-obrigatoria.md) — tipagem obrigatória
- [D-17](../decisoes/D-17-monorepo-engine-sem-django.md) — monorepo, `engine/` sem Django
- [D-28](../decisoes/D-28-frontend-em-typescript.md) — frontend em TypeScript
- [D-29](../decisoes/D-29-rigor-de-tipagem-por-origem-do-codigo.md) — rigor de tipagem graduado pela origem
- [D-30](../decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md) — portão de mockup só para tela de produto

## Riscos e questões em aberto

### O Django não pode importar o motor ainda

Nada no `backend/` depende de `engine/` neste bloco. A integração é do Marco 1, e vem pela
fila ([D-14](../decisoes/D-14-celery-e-redis.md)) — o processo web nunca carrega TensorFlow
([ARQUITETURA](../ARQUITETURA.md#a-regra-estrutural-inegociável)).

Se durante o F2b surgir necessidade de importar `engine` no `backend`, é sinal de que algo
saiu do escopo.

### DRF ainda não tem o que servir

[D-11](../decisoes/D-11-pilha-tecnologica.md) define DRF, mas sem app de domínio não há
recurso a expor. O F2b instala e configura a biblioteca; o primeiro recurso é do Marco 1. A
rota de saúde não precisa de DRF.
