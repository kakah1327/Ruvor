# Ruvor

Plataforma de análise de risco em ações da B3.

Responde **quanto você pode perder** ao aplicar em uma ação ou carteira — comparando
múltiplos algoritmos sobre a mesma base e mostrando, com validação estatística, qual deles
merece confiança para aquele ativo.

> ## ⚠️ Este repositório está em reconstrução
>
> A plataforma Ruvor **ainda não foi construída**: não há camada web, banco nem API.
>
> O que já existe é o **motor numérico**, em [`engine/`](engine/) — pacote Python isolado,
> com suíte de testes e linha de base numérica próprias. O protótipo que o originou foi
> removido. O `frontend/` ainda é o do protótipo e será substituído no **F2b**.
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

## Executar o motor

> Não há API: a camada web chega no F2b. O motor roda pela linha de comando.

```bash
python -m venv .venv
.venv\Scripts\activate                    # Windows
pip install -e ./engine                   # use ./engine[all] para GARCH, ML e testes
```

Experimento:

```bash
ruvor run --ticker PETR4.SA --start 2015-01-01 --end 2024-12-31 \
    --model garch_1_1 --model lstm \
    --backtest kupiec --backtest christoffersen
```

Testes: `pytest engine/tests`

O `frontend/` ainda é o do protótipo e não fala com o motor — a API que ele consumia deixou
de existir. Ele é substituído no F2b.
