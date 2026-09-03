# D-33 — O dia a dia de backend e frontend roda dentro do contêiner

**Status:** aceita · 2026-09-02

## Contexto

O [`README.md`](../../README.md) documenta execução nativa: ambiente virtual na raiz,
`pip install -e`, `npm install`, variáveis exportadas no shell, dois servidores em dois
terminais. A tabela "Comandos do dia a dia" lista `pytest engine/tests`, `pytest backend`,
`cd frontend && npm test`, todos no hospedeiro.

Com o F3, o backend passa a depender de Postgres e Redis. Manter a execução nativa
significaria instalar Postgres e Redis na máquina — que é exatamente o que o bloco existe
para eliminar.

Havia três saídas: manter tudo nativo, mover tudo para o contêiner, ou manter os dois
caminhos com o contêiner "como referência". A terceira exigiria um critério provando que os
dois concordam; sem ele, é só ambiguidade documentada.

## Decisão

**Cada coisa tem uma casa só.**

| O quê | Onde roda |
|---|---|
| `backend/` — servidor, teste, tipos | contêiner |
| `frontend/` — servidor, teste, tipos | contêiner |
| `engine/` — teste, tipos, `ruvor run` de desenvolvimento | `.venv/` nativo |

O motor é a exceção porque é pacote independente que não fala com serviço nenhum: subir
Postgres e Redis para rodar a suíte dele seria custo sem contrapartida.

## Consequências

- O `.venv/` da raiz **continua existindo e sendo instalado**. O que muda é qual execução
  vale, não a existência do ambiente — `pip install -e "./backend[dev]"` segue útil para o
  editor resolver importação e para o verificador de tipos do editor funcionar.
- Não é proibido subir o Django nativo; deixa de ser o caminho documentado.
- O F5 herda esta decisão: **a CI espelha o contêiner, não o `.venv`**.
- O `README.md` precisa ser reescrito nas seções "Pré-requisitos", "Executar" e "Comandos do
  dia a dia".
- **Não contradiz a [D-22](D-22-treino-centralizado-em-container.md).** Ela governa o
  **treino dos experimentos**, que roda em contêiner com semente fixa para que o ranking não
  dependa da máquina. A linha do `engine/` acima trata de execução de desenvolvimento — rodar
  a suíte, verificar tipos, disparar um experimento curto. São coisas diferentes, e o
  contêiner de treino da D-22 não é entregue pelo F3.

Origem: [spec F3 — Ambiente local](../specs/F3-ambiente-local.md).
