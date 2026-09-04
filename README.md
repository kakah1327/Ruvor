# Ruvor

Plataforma de análise de risco em ações da B3.

Responde **quanto você pode perder** ao aplicar em uma ação ou carteira — comparando
múltiplos algoritmos sobre a mesma base e mostrando, com validação estatística, qual deles
merece confiança para aquele ativo.

> ## ⚠️ Este repositório está em reconstrução
>
> A plataforma Ruvor **ainda não foi construída**: não existe API de negócio nem tela de
> produto.
>
> O que já existe:
>
> - o **motor numérico**, em [`engine/`](engine/) — pacote Python isolado, com suíte de
>   testes e linha de base numérica próprias
> - o **casco da aplicação**: um projeto Django em [`backend/`](backend/), que responde
>   `GET /health` e conecta no PostgreSQL, e um projeto React em TypeScript em
>   [`frontend/`](frontend/), que renderiza uma tela de verificação com a marca e o estado
>   do backend
> - o **ambiente local em contêiner**: `docker compose up` sobe Postgres, Redis, o Django, um
>   worker Celery e o servidor de desenvolvimento do frontend
>
> O protótipo que originou o motor foi removido por inteiro, frontend incluído.
>
> - **O que a plataforma será:** [`docs/PRODUTO.md`](docs/PRODUTO.md) e [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md)
> - **Onde estamos:** [`docs/ESTADO.md`](docs/ESTADO.md)
> - **O protótipo, já removido:** [`docs/prototipo/`](docs/prototipo/) — não é referência de padrão

---

## O diferencial

Nenhuma ferramenta disponível hoje reúne, num fluxo comparativo único:

- métodos tradicionais de VaR (paramétrico, histórico, Monte Carlo)
- modelos de volatilidade condicional (GARCH, EGARCH)
- algoritmos de Machine Learning (LSTM, GRU, CAViaR, GARCHNet)
- validação estatística (Kupiec, Christoffersen, Quantil Dinâmico, zonas de Basileia)

Bibliotecas de risco não têm ML nem backtesting. Plataformas comerciais são caixa-preta e
caras. Implementações acadêmicas são fragmentadas e não comparáveis entre si.

O resultado prático: em vez de um número de risco solto, o Ruvor responde **em qual modelo
confiar para esta ação, neste nível de confiança** — e mostra a evidência.

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [PRODUTO](docs/PRODUTO.md) | o que é, para quem, as cinco camadas, marcos |
| [ARQUITETURA](docs/ARQUITETURA.md) | pilha, estrutura, banco, execução, auditoria |
| [PROCESSO](docs/PROCESSO.md) | como spec, plano e código nascem e são revisados |
| [ROADMAP](docs/ROADMAP.md) | ordem dos blocos e status |
| [ESTADO](docs/ESTADO.md) | onde estamos agora |
| [Decisões](docs/decisoes/) | o que foi decidido e por quê |

Identidade visual em [`brand/ruvor/`](brand/ruvor/).

---

## Pilha

| Camada | Tecnologia |
|---|---|
| Backend | Python + Django + Django REST Framework |
| Frontend | React |
| Banco | PostgreSQL |
| Fila e cache | Celery + Redis |
| Motor numérico | pacote Python isolado, sem dependência do framework web |

---

## Origem acadêmica

O motor de risco nasceu de um Trabalho de Conclusão de Curso em Ciência da Computação na
Faculdade Impacta Tecnologia, que implementa e valida cientificamente os modelos —
inclusive com verificação cruzada contra o pacote `rugarch` da linguagem R.

O motor numérico permanece como pacote independente, reutilizável e auditável; o Ruvor é a
plataforma construída sobre ele.

Material acadêmico em [`docs/tcc/`](docs/tcc/).

---

## Executar

### Pré-requisitos

- **Docker**, com o plugin `compose`. É o único pré-requisito do repositório: PostgreSQL,
  Redis, Django, o worker Celery e o servidor de desenvolvimento do frontend sobem em
  contêiner, e nada disso precisa estar instalado na máquina.
- **Python 3.12 ou superior**, num ambiente virtual na raiz — `.venv/`. É exigência do
  **motor**, que continua rodando nativo
  ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)). O mesmo ambiente serve para
  o editor resolver as importações do `backend/`, ainda que o backend execute no contêiner.
- **Node.js não é exigido na máquina.** O frontend roda sobre a imagem `node:24-slim`, que
  casa com `frontend/.nvmrc`. Só quem insistir em rodar `npm` fora do contêiner precisa de
  Node 24.15 ou superior: o `frontend/.npmrc` liga `engine-strict` e, com Node mais antigo,
  a instalação recusa em vez de instalar quebrado.

### Subir o ambiente

Na primeira vez é preciso criar o `.env`: ele é ignorado pelo git e não vem no clone. Os
valores do exemplo funcionam como estão — não há segredo real neles e nada precisa ser
editado.

```bash
cp .env.example .env
docker compose up -d --wait
```

O `docker compose` lê o `.env` da raiz sozinho; nenhuma variável precisa ser exportada no
shell. O `--wait` só devolve quando os cinco serviços estão saudáveis, e sai com erro se
algum não chegar lá.

| Serviço | Onde atende no hospedeiro |
|---|---|
| `frontend` | <http://localhost:5273> |
| `web` (Django) | <http://localhost:8000/health> |
| `postgres` | `localhost:55432` |
| `redis` | `localhost:56379` |
| `worker` | sem porta publicada |

**As portas publicadas não são as padrão das ferramentas.** O frontend atende em **5273**, e
não em 5173, porque 5173 pertence a outro projeto desta máquina; Postgres em **55432** e
Redis em **56379** para não colidir com uma instalação nativa. As quatro saem do `.env`
(`RUVOR_PORT_WEB`, `RUVOR_PORT_FRONTEND`, `RUVOR_PORT_POSTGRES`, `RUVOR_PORT_REDIS`); trocar
é editar o arquivo e repetir o `docker compose up -d --wait`, que recria os contêineres.

Depois de mexer em `backend/pyproject.toml` ou em `frontend/package.json`, reconstrua:
`docker compose up -d --build --renew-anon-volumes`. Sem `--renew-anon-volumes` o
`node_modules` do contêiner sobrevive à recriação, e a dependência nova não aparece.

Para derrubar tudo, `docker compose down`; com `-v`, leva junto o volume do banco.

### Motor

O motor é a exceção que roda nativo, porque é pacote independente e não fala com serviço
nenhum.

```bash
python -m venv .venv
.venv\Scripts\activate                    # Windows
pip install -e ./engine                   # use ./engine[all] para GARCH, ML e testes
pip install -e "./backend[dev]"           # opcional: só para o editor resolver o backend
```

Experimento, pela linha de comando:

```bash
ruvor run --ticker PETR4.SA --start 2015-01-01 --end 2024-12-31 \
    --model garch_1_1 --model lstm \
    --backtest kupiec --backtest christoffersen
```

### Backend

O Django lê toda a configuração de variáveis `RUVOR_*` (`backend/config/settings.py`),
inclusive as do PostgreSQL e a URL do Redis. Quem as preenche é o `compose`, a partir do
`.env`. Se faltar alguma obrigatória, a subida falha dizendo qual.

`curl http://localhost:8000/health` responde `{"status": "ok"}`. É a única rota.

Um shell dentro do serviço: `docker compose exec web bash`.

### Frontend

O serviço sobe junto com o conjunto. Abra `http://localhost:5273` — `localhost`, não
`127.0.0.1`: no Windows, `localhost` resolve para IPv6 e é lá que o Vite escuta.

A tela mostra a marca e `Backend: ok`; o servidor de desenvolvimento leva `/health` até o
serviço `web` pelo destino em `VITE_PROXY_TARGET`, que o `compose` fixa em
`http://web:8000`. Com o backend fora do ar, `Backend: indisponível`.

`frontend/.env.example` documenta `VITE_API_BASE_URL`; vazia, que é o padrão, a tela usa o
proxy.

### Comandos do dia a dia

Backend e frontend rodam **dentro do contêiner**; o motor, no `.venv/` nativo
([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)). O conjunto precisa estar de pé
(`docker compose up -d --wait`) para as cinco primeiras linhas.

| O quê | Comando |
|---|---|
| Testes do backend | `docker compose exec -T web pytest tests` |
| Tipos do backend | `docker compose exec -T web mypy` |
| Testes do frontend | `docker compose exec -T frontend npm test` |
| Tipos do frontend | `docker compose exec -T frontend npm run typecheck` |
| Construir o frontend | `docker compose exec -T frontend npm run build` |
| Testes do motor | `pytest engine/tests` |
| Tipos do motor | `cd engine && mypy` — o mypy lê a configuração do diretório corrente |
| Construir o pacote do motor | `python -m build --no-isolation engine` |

**`pytest backend` no hospedeiro reprova um teste, e é de propósito.** O
`backend/config/settings_test.py` fixa valores de banco inexistentes (`nao-usar`) justamente
para que um `.env` incompleto não passe despercebido; com isso,
`test_conexao_com_o_banco` só passa dentro do contêiner, onde as variáveis vêm do `compose`.
No hospedeiro ele falha com `OperationalError: failed to resolve host 'nao-usar'`. Não é
regressão: é a suíte rodando fora da casa dela.

O interpretador nativo do projeto é o do ambiente virtual: **`.venv/Scripts/python.exe`** no
Windows, `.venv/bin/python` no Linux. Reproduzir o ambiente exato que gerou a linha de base
numérica do motor: `pip install -r engine/requirements-lock.txt`.
