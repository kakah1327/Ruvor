# D-43 — ruff para Python, Biome para o frontend, e onde cada verificação roda

**Status:** aceita · 2026-09-06

## Contexto

Não existia ferramenta de estilo em lugar nenhum do repositório — nem em `backend/`, nem em
`engine/`, nem em `frontend/`. A escolha tinha dono declarado desde o F2b, cujo plano registra:
*"Ferramenta de estilo — fora deste bloco. A spec do F5 é dona da escolha."*

A [D-33](D-33-dia-a-dia-dentro-do-conteiner.md) fecha dizendo que *"a CI espelha o contêiner,
não o `.venv`"*. Aplicada sem exceção, ela obrigaria a rodar estilo dentro das imagens — e a
imagem que conteria o `engine/` é a `worker`, de 3,79 GB.

## Decisão

**`ruff` para os dois projetos Python. `@biomejs/biome` para o frontend.** Uma ferramenta por
lado, cada uma fazendo lint **e** formatação — o mesmo princípio de reduzir peças que levou o
Redis a fazer três papéis ([D-14](D-14-celery-e-redis.md)).

**A D-33 fica restringida a dois dos quatro trabalhos da CI:**

| Trabalho | Onde roda | Por quê |
|---|---|---|
| backend | contêiner `web` | executa a aplicação — o ambiente decide o resultado |
| frontend | contêiner `frontend` | idem, e o Biome já vem no `npm ci` da imagem |
| **estilo** (`ruff`) | runner | não executa código: lê o fonte e nunca o importa |
| **motor** | runner | pacote isolado, e a única imagem que o contém é a `worker` |

## Consequências

- **O motivo decisivo do `ruff` no runner é o `engine/`.** Ou ele roda fora do contêiner, ou o
  motor fica sem estilo, porque a `worker` não é construída na CI. O `backend/` acompanha, para
  que o trabalho seja um só e a versão da ferramenta seja a mesma para os dois projetos.
- **Duas configurações de `ruff`, não uma** — `backend/pyproject.toml` e
  `engine/pyproject.toml` —, porque a ARQUITETURA fixa *"um projeto Python por diretório: cada
  um declara as próprias dependências e a configuração das próprias ferramentas"*. É também o
  que permite rigor diferente por origem, como a
  [D-29](D-29-rigor-de-tipagem-por-origem-do-codigo.md) já estabelece para tipagem.
- **`E501` fica fora do piso de regras, e `line-length` fixado em 88.** O formatador é quem
  impõe comprimento de linha; o `E501` só sobraria para o que ele não sabe quebrar — comentário,
  docstring, texto. Medido: com ele ligado, o motor tem 63 violações; sem ele, 24.
- **A versão de cada ferramenta é declarada nos `pyproject.toml` e no `package.json`, e o
  `ci.yml` não carrega número nenhum.** Número repetido em três lugares diverge em silêncio.
- Consequência de embalagem: acrescentar `ruff` ao grupo `dev` do backend muda a imagem `web`;
  acrescentar o Biome muda o `package-lock.json` e obriga a reconstruir a imagem do frontend com
  `--renew-anon-volumes`.

Origem: [spec F5 — Integração contínua](../specs/F5-integracao-continua.md).
