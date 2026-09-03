# D-35 — `compose.yaml` e `.dockerignore` ficam na raiz, não em `infra/`

**Status:** aceita · 2026-09-02

## Contexto

O diagrama de estrutura da [ARQUITETURA](../ARQUITETURA.md#estrutura-do-repositório) reserva
`infra/` para *"docker, compose, CI"*. A leitura natural é pôr os quatro arquivos de
infraestrutura lá dentro.

Ao especificar o F3, os dois primeiros se mostraram **inviáveis** nessa posição — e o modo de
falhar é o que decidiu a questão.

## Decisão

`compose.yaml` e `.dockerignore` ficam na **raiz do repositório**. `infra/` guarda os arquivos
de construção de imagem, e o F5 lhe acrescenta a parte de CI.

## Consequências

Os dois falhariam em silêncio dentro de `infra/`:

- **`.dockerignore`** — o Docker procura o arquivo **na raiz do contexto de construção**, e o
  contexto aqui é a raiz do repositório (a imagem do backend precisa de `engine/` e
  `backend/`; a do frontend precisa de `frontend/` e `brand/ruvor/`, por causa do apelido
  `@brand`). Um arquivo chamado `infra/.dockerignore` ficaria inerte, e o `.venv/` — 2,1 GB,
  com TensorFlow dentro — seria enviado ao daemon a cada construção. O sintoma é "a construção
  demora muito", nunca um erro.
  > Nuance: o BuildKit também aceita um irmão do arquivo de construção, nomeado a partir dele
  > (`infra/backend.Dockerfile.dockerignore`). Seriam dois arquivos que divergem; um só na raiz
  > serve às duas construções.
- **`compose.yaml`** — o Compose descobre o `.env` no **diretório do projeto**, que por padrão
  é o diretório do arquivo de composição. Com ele em `infra/`, o `.env` da raiz não alimenta a
  interpolação de `${RUVOR_PORT_*}` e as portas subiriam vazias. E `docker compose up` na raiz
  não encontraria composição nenhuma — o Compose busca em diretórios pai, nunca em filhos.

Consequência positiva: **`docker compose up` funciona sem argumento**, que é literalmente a
linha que a ARQUITETURA promete. Com o arquivo em `infra/`, o comando viraria
`docker compose -f infra/compose.yaml --env-file .env up`, que ninguém digita duas vezes
igual.

O diagrama da ARQUITETURA passa a estar errado quanto ao `compose`, e a correção é parte do
passo FECHA do F3.

Origem: [spec F3 — Ambiente local](../specs/F3-ambiente-local.md).
