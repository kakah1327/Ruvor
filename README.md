# Ruvor

Plataforma de análise de risco em ações da B3.

Responde **quanto você pode perder** ao aplicar em uma ação ou carteira — comparando
múltiplos algoritmos sobre a mesma base e mostrando, com validação estatística, qual deles
merece confiança para aquele ativo.

> ## ⚠️ Este repositório está em reconstrução
>
> A plataforma Ruvor **ainda não foi construída**: não há banco, API de negócio nem tela de
> produto.
>
> O que já existe:
>
> - o **motor numérico**, em [`engine/`](engine/) — pacote Python isolado, com suíte de
>   testes e linha de base numérica próprias
> - o **casco da aplicação**: um projeto Django em [`backend/`](backend/), que responde
>   `GET /health` sem banco, e um projeto React em TypeScript em [`frontend/`](frontend/),
>   que renderiza uma tela de verificação com a marca e o estado do backend
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

- **Python 3.12 ou superior**, num ambiente virtual na raiz — `.venv/`. É o único ambiente
  Python do repositório: motor e backend são instalados nele.
- **Node.js 24.15 ou superior**, só para o frontend. O `frontend/.npmrc` liga `engine-strict`:
  com Node mais antigo, o `npm install` recusa em vez de instalar quebrado. A versão está
  declarada em `frontend/.nvmrc` — com fnm ou nvm, `fnm use` / `nvm use` dentro de
  `frontend/` ativa o Node certo sem trocar o global da máquina.

```bash
python -m venv .venv
.venv\Scripts\activate                    # Windows
pip install -e ./engine                   # use ./engine[all] para GARCH, ML e testes
pip install -e "./backend[dev]"           # Django, DRF e as ferramentas de teste e de tipos
```

### Motor

Roda pela linha de comando. Experimento:

```bash
ruvor run --ticker PETR4.SA --start 2015-01-01 --end 2024-12-31 \
    --model garch_1_1 --model lstm \
    --backtest kupiec --backtest christoffersen
```

### Backend

O Django lê toda a configuração de variáveis `RUVOR_*` (`backend/config/settings.py`) e não
tem banco. Copie `.env.example` para `.env` e preencha `RUVOR_SECRET_KEY`. **Nada carrega o
arquivo** até o F3: as variáveis precisam estar exportadas no shell que sobe o servidor.

```bash
export RUVOR_SECRET_KEY=troque-isto RUVOR_DEBUG=true RUVOR_ALLOWED_HOSTS=localhost,127.0.0.1
cd backend && python manage.py runserver 8000
```

No PowerShell, `$env:RUVOR_SECRET_KEY = "troque-isto"`, e assim por diante. Sem
`RUVOR_SECRET_KEY` o processo não sobe, e a mensagem diz qual variável falta.

`curl http://127.0.0.1:8000/health` responde `{"status": "ok"}`. É a única rota.

### Frontend

```bash
cd frontend && npm install && npm run dev
```

Abra `http://localhost:5173` — `localhost`, não `127.0.0.1`: no Windows, `localhost` resolve
para IPv6 e é lá que o Vite escuta. A tela mostra a marca e `Backend: ok` quando o Django
está de pé na porta 8000 — o servidor de desenvolvimento encaminha `/health` para ele. Com o
backend fora do ar, `Backend: indisponível`.

`frontend/.env.example` documenta `VITE_API_BASE_URL`; vazia, que é o padrão, a tela usa o
proxy.

### Comandos do dia a dia

| O quê | Comando |
|---|---|
| Testes do motor | `pytest engine/tests` |
| Tipos do motor | `cd engine && mypy` — o mypy lê a configuração do diretório corrente |
| Construir o pacote do motor | `python -m build --no-isolation engine` |
| Testes do backend | `pytest backend` — não precisa de variável exportada |
| Tipos do backend | `cd backend && mypy` |
| Testes do frontend | `cd frontend && npm test` |
| Tipos do frontend | `cd frontend && npm run typecheck` |
| Construir o frontend | `cd frontend && npm run build` |

O interpretador do projeto é o do ambiente virtual: **`.venv/Scripts/python.exe`** no Windows,
`.venv/bin/python` no Linux. Reproduzir o ambiente exato que gerou a linha de base numérica:
`pip install -r engine/requirements-lock.txt`.
