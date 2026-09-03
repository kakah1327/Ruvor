# D-32 — O frontend entra no `docker compose`

**Status:** aceita · 2026-09-02

## Contexto

A [ARQUITETURA](../ARQUITETURA.md#ambientes) descreve o ambiente local como quatro serviços:
*"`docker compose up` sobe Postgres, Redis, web e worker"*. O [ROADMAP](../ROADMAP.md) e o
[ESTADO](../ESTADO.md) repetem a mesma lista de quatro. Nenhum menciona o frontend.

A justificativa que a própria ARQUITETURA dá para existir o `compose` é dupla: *"evita 'na
minha máquina funciona' num time de 4 pessoas com sistemas diferentes"* e *"faz alguém novo
produzir no primeiro dia"*.

O frontend é hoje **a peça com o pré-requisito mais frágil do repositório**. Exige Node
24.15+, travado por `engine-strict` em `frontend/.npmrc` — que existe justamente porque a
ausência dele já custou tempo: sem `engine-strict`, o npm omite o binding nativo do rolldown
em silêncio e o `vite build` quebra depois com uma mensagem que culpa o arquivo de trava e
não a versão do Node. Na máquina de desenvolvimento atual, o Node global é 20.11 e pertence a
outro projeto; o 24 só existe por `fnm`.

Deixar o frontend fora do `compose` contradiz as duas justificativas ao mesmo tempo.

## Decisão

**O ambiente local tem cinco serviços**: `postgres`, `redis`, `web`, `worker` e `frontend`.

O serviço `frontend` roda o servidor de desenvolvimento do Vite em contêiner, com o
código-fonte montado do hospedeiro.

## Consequências

- A versão do Node deixa de ser pré-requisito da máquina. `fnm` passa a ser conveniência para
  quem quiser editar fora do contêiner, não condição para o projeto funcionar.
- `node_modules` precisa ser volume próprio do contêiner: dependência instalada no Windows
  não serve ao Linux da imagem, e binário nativo é exatamente o que quebra.
- Custo assumido: o editor no hospedeiro perde resolução de tipos do frontend, a menos que
  alguém rode `npm install` localmente por conta própria. É a contrapartida de não exigir Node
  para trabalhar no projeto.
- **A ARQUITETURA, o ROADMAP e o ESTADO passam a estar errados** enquanto não forem
  corrigidos. A correção é parte do passo FECHA do F3 — registrar esta decisão não basta,
  porque os três estão na tabela "Manda" do [`CLAUDE.md`](../../CLAUDE.md).
- Produção continua com quatro peças: lá o frontend é resultado estático de `vite build`, não
  um servidor de desenvolvimento. Esta decisão vale para o ambiente local.

Origem: [spec F3 — Ambiente local](../specs/F3-ambiente-local.md).
