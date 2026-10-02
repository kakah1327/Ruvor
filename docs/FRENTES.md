# Frentes

Quem está fazendo o quê, e onde cada um pode escrever. É o quadro vivo da
[D-84](decisoes/D-84-frentes-com-cerca-de-pastas.md); a regra de ramo e PR é a
[D-82](decisoes/D-82-ramo-por-bloco-e-pr-revisada-por-outra-frente.md).

**Este arquivo muda pouco**, só quando uma frente troca de dono ou de bloco, ou quando um
contrato muda. **O andamento de cada frente mora no arquivo dela**, em [`frentes/`](frentes/).
Cada frente escreve só no próprio, e por isso as frentes não brigam por uma linha de status.

---

## Qual é a minha frente?

```
git branch --show-current
```

O prefixo antes da `/` é a frente: `identidade/M2.1-identidade-e-acesso` é a frente
`identidade`. Abra `docs/frentes/<frente>.md` e siga o **Próximo passo** de lá.

Na `main`, ou num ramo sem prefixo de frente, **não comece trabalho**. Pergunte ao humano qual é
a frente e crie o ramo pelo formato abaixo.

---

## As frentes

| Frente | Dono | Blocos, em ordem | Arquivo | Ramo atual |
|---|---|---|---|---|
| `marco1` | darkside171 | M1.5b ✅ → M1.6a ✅ → M1.6b ✅ → M1.6c ✅ → M2.1m ✅ → M1.6d ✅ → M1.5c ✅ → M2.3 ✅; o M1.7 fechado no ramo próprio; spec e plano aprovados, a implementar: M3.3, M2.1b | [frentes/marco1.md](frentes/marco1.md) | `marco1/M2.3-camada-explicativa` — M2.3 fechado, a PR de implementação é do dono; `marco1/M1.7-busca-e-catalogo`, fechado, com a PR também a abrir; os outros dois ramos, cada um no seu worktree, com spec e plano na `main` (PRs #20 e #24) |
| `identidade` | kakah1327 (Kauã), desde 2026-09-27 | M2.1 ✅ → M4.2 ✅ → M4.1 ✅ → M2.2a (pronto no ramo em 2026-10-02; o merge espera o parecer da CVM, D-116) | [frentes/identidade.md](frentes/identidade.md) | `identidade/M2.2-carteira` |
| `fundamentos` | kakah1327 (Kauã) | M3.1 ✅ → M3.2 ✅ | [frentes/fundamentos.md](frentes/fundamentos.md) | — (parada; o M3.2 foi mesclado) |

**Hoje são duas frentes ativas**, `marco1` e `identidade` — esta com a carteira (M2.2a, só o backend; as telas, M2.2b, são da `marco1`). A `fundamentos` fechou o M3.2 e está
parada, sem próximo bloco definido; o Kauã, dono dela, assumiu a `identidade` em 2026-09-27.

**Ramo:** `<frente>/<bloco>-<assunto>`. Um ramo por bloco, com três PRs: spec, plano e
implementação. **O merge da PR pelo dono da frente, com a CI verde, é o portão
humano** ([D-85](decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md), que restringe a D-82);
PR que muda contrato entre frentes passa também pela frente que o consome. Merge com
commit de merge, nunca _squash_.

---

## Cercas

Onde cada frente escreve. **Fora da cerca, não se escreve**: combina na spec, e a frente dona
revisa a PR.

| Frente | Pastas |
|---|---|
| `marco1` | `engine/`; `backend/apps/risk/`, `backend/apps/analytics/`, `backend/apps/assets/`, `backend/apps/api/` (a API, criada pelo M1.6a), e os testes delas em `backend/tests/`; `frontend/`; `brand/`; `docs/mockups/`; os serviços `worker` e `beat` no `compose.yaml` |
| `identidade` | `backend/apps/accounts/`; `backend/tests/test_usuario.py`, `test_organizacao.py` e os testes novos do M2.1 (`backend/tests/accounts/`); desde o M2.2a, `backend/apps/portfolios/` e `backend/tests/portfolios/`, inclusive as tabelas novas da app em `core` e em `gold`, com nome próprio ([D-119](decisoes/D-119-o-risco-da-carteira-e-sob-demanda-em-gold-na-app-da-frente.md)). **Sem telas:** toda interface visual — telas, mockups, kit — é da `marco1` (decisão do darkside171, 2026-09-27), inclusive as de login, que consomem as rotas do M2.1 |
| `fundamentos` | a app nova do M3.1 em `backend/apps/` (`apps/fundamentals`, pela [spec do M3.1](specs/M3.1-fundamentos.md)) e os testes dela; as tabelas novas em `bronze`, `silver` e `gold`, da própria app, com nome próprio |

**Migration:** cada app tem sequência própria, e ninguém cria migration em app de outra frente.

### Arquivos comuns

Todas as frentes podem precisar deles. Regra: **alteração aditiva e mínima** — acrescentar a
linha, não reescrever a vizinha —, **declarada no inventário da spec**. Em conflito de merge,
resolve quem fizer o merge por último.

- `backend/config/settings.py` (`INSTALLED_APPS`, `CELERY_BEAT_SCHEDULE`), `backend/config/urls.py`
- `compose.yaml`, `.env.example`, `.github/workflows/ci.yml`
- `backend/pyproject.toml`, `engine/pyproject.toml`, `frontend/package.json`
- `CLAUDE.md`, `README.md`, `docs/ROADMAP.md`, `docs/ESTADO.md`, `docs/ARQUITETURA.md`,
  `docs/PRODUTO.md`, `docs/aprendizados.md`
- os índices `docs/specs/README.md`, `docs/planos/README.md`, `docs/decisoes/README.md`: cada
  frente só acrescenta a própria linha

**`ESTADO.md` é atualizado no fecho de um bloco**, dentro da PR de implementação, e não a cada
sessão. O andamento do dia fica no arquivo da frente.

---

## Contratos entre frentes

O que uma frente entrega e outra consome. Só a frente que produz um contrato o muda, e a PR da
mudança passa pela revisão da frente que o consome.

| Contrato | Produz | Consome | Estado |
|---|---|---|---|
| **Convenções da API HTTP**: prefixo de rota, versão, formato de erro, autenticação | `marco1` (M1.6) e `identidade` (M2.1) | as duas | ✅ existe. Decidido pela [D-86](decisoes/D-86-convencoes-da-api-http.md) e aplicado pelo M1.6a: `/api/v1/`, `REST_FRAMEWORK` com o tratador do formato de erro, permissão padrão `IsAuthenticated` e cada view declarando a sua. **O mecanismo de autenticação é do M2.1**; mudar o formato de erro ou a regra de permissão exige a revisão das duas frentes; o mecanismo de autenticação é do M2.1, sessão do Django ([D-100](decisoes/D-100-a-api-autentica-por-sessao-do-django-com-csrf.md)), e, desde o M4.2, a chave pessoal de leitura ([D-108](decisoes/D-108-a-api-aceita-chave-pessoal-de-leitura.md)): **toda view nova declara `api_key_scope`** (`"read"` ou `None`) e `extend_schema` em cada método ([D-110](decisoes/D-110-a-descricao-da-api-e-o-esquema-openapi-gerado.md)); toda rota tem taxa ([D-109](decisoes/D-109-toda-rota-da-api-tem-taxa.md)) |
| **Casco do frontend e kit completo**: layout, navegação, escala tipográfica, estados de interação | `marco1` (M1.6) | `marco1` — as telas, inclusive as de login, são dela | ✅ existe. O kit (M1.6a) e o casco (M1.6b): as rotas `/` e `/ativos/{ticker}`, a barra com a busca, o alternador de leitura e a chave de tema (em `.ruvor-topbar__prefs`, por posição — o menu de conta do M2.1b refaz esses seletores), o nível em `ruvor-reading`/`useReading` (D-152), que tela nova consome com as duas entradas de texto por número, o rodapé com a ressalva e a proveniência, e a coluna lateral por `setRail` — em `frontend/src/components/Shell.tsx`. A `identidade` não consome: não tem tela |
| **`gold.risk_run.requested_by`**: a dívida é do M2.1, o arquivo é de `apps/risk/` | `identidade` define o usuário; `marco1` é dona do arquivo | — | ✅ fechado. A coluna de `core.compute_request` e a migration dela vieram da `marco1` (M2.1m); o preenchimento, da T14 do M2.1a: o `POST /risk` logado grava o autor no pedido novo, e a abertura repassa o autor para a `risk_run`. A rotina, o caminho síncrono e o pedido anônimo gravam nulo. Quando a [D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md) entrar (M2.1b), o caso anônimo do `tests/accounts/test_requested_by.py` passa a esperar 401, e quem o ajusta é a `identidade` |
| **As rotas de conta**: `/api/v1/auth/*` e `/api/v1/organization/users` | `identidade` (M2.1a) | `marco1` (as telas de login e de gestão) | ✅ existem, na `main` desde a PR #13 (fase 2 do M2.1a): as rotas e os corpos da tabela do RF-29 da [spec](specs/M2.1a-identidade-e-acesso.md#contratos-externos); escrita logada exige `X-CSRFToken`, e o `csrftoken` muda depois de `login` e `signup` |
| **As colunas do risco que o relatório lê**: as de `gold.risk_run`, `gold.risk_result`, `silver.asset` e da coleta de preço (`bronze.collection_run`) que o formato 1 do relatório grava — o RF-03 da [spec do M4.1](specs/M4.1-relatorios.md#rf-03) —, e os `PROTECT` de `core.report` para `gold.risk_run` e `silver.asset` | `marco1` (as tabelas) | `identidade` (M4.1, `apps/accounts/reports.py`) | 🟡 existe; pede-se **"só cresce"**, como o do catálogo com a `fundamentos`: coluna nova pode; renomear, tirar ou mudar o sentido de uma lida quebra a geração de relatório **novo** (os guardados não mudam), e o V-04 do M4.1 reprova. Execução ou ativo citado por relatório não se apaga. A revisar pela `marco1` na PR do M4.1 |
| **As rotas de relatório**: `/api/v1/reports*` | `identidade` (M4.1) | `marco1`, se fizer tela de relatório | ✅ existe ([D-113](decisoes/D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md) a [D-115](decisoes/D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md)). Gerar pela sessão; listar, ler e baixar `/json` e `/csv` pela sessão ou pela chave; o `id` é o UUID que vai na URL da tela |
| **`silver.asset`**: o catálogo, por ticker | `marco1` | `fundamentos` liga fundamento a ativo | ✅ existe. **Só cresce**: coluna nova pode, mudar ou tirar coluna exige a revisão da `fundamentos` |
| **`silver.price`**: o preço diário, por ativo | `marco1` | `fundamentos` lê `asset`, `date` e `close` para os múltiplos | ✅ existe. **Só cresce**, como o catálogo: mudar o sentido dessas colunas exige a revisão da `fundamentos` |
| **`core.user` e `core.organization`** | `identidade` | todas, no futuro | ✅ existe. A `identidade` muda. Enquanto nada fora de `accounts` depende deles, não há consumidor a proteger |
| **O filtro automático por organização**: `apps/accounts/tenancy.py` | `identidade` (M4.2) | toda frente que criar tabela privada (a primeira é o M2.2) | ✅ existe ([D-112](decisoes/D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)). Outras frentes o **usam**, não o mudam: tabela privada nova usa o `OrganizationScopedManager` como gerente padrão, com `organization_field` e um gerente base sem escopo |
| **`gold.fundamental_indicator`**: o último indicador por ação | `fundamentos` | `marco1` (a rota `/fundamentals`, M1.6c) | ✅ contrato **"só cresce"** ([D-99](decisoes/D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md)): as colunas do RF-02 da [spec do M1.6c](specs/M1.6c-fundamentos-e-contexto.md), mais `asset` e `statement`. Coluna nova pode; mudar o sentido, renomear ou tirar uma lida exige a revisão da `marco1` |
| **`gold.peer_comparison`**: a posição entre os pares | `fundamentos` | `marco1` | ✅ "só cresce": `peer_level`, `group_*`, as dezoito `{ind}_peer_median`/`_percentile`/`_peer_count` e a ligação um-para-um com o indicador — a tela lê a comparação **do próprio indicador** |
| **`silver.disclosure`**: os comunicados da companhia à CVM | `fundamentos` | `marco1` (a rota `/disclosures`) | ✅ "só cresce": as colunas do RF-03 do M1.6c, mais `code_cvm` e `company_name`; a ligação é direta por `silver.asset.code_cvm` |
| **`silver.company`** e três colunas de **`silver.financial_statement`** | `fundamentos` | `marco1` | ✅ "só cresce": `company.code_cvm`, `company.name`; `reference_date`, `source`, `scope` do balanço do indicador |
| **As listas de valores que a tela traduz**: `account_plan`, `per_share_missing` (com os campos que cada motivo anula, `REASON_NULLS`), `market_cap_missing` (os literais de `market_cap()`), `peer_level`, `category` | `fundamentos` | `marco1` | ✅ **valor novo é mudança de contrato**: a PR da `fundamentos` passa pela revisão da `marco1`, que atualiza a tradução e `backend/tests/api/test_valores_fundamentos.py` — o teste lê as listas da fonte e reprova a mudança |
| **O que a carteira lê do risco**: `apps/risk/config.py` (`DEFAULT_SEED`, `TRAIN_WINDOW_DAYS`, `MIN_SESSIONS`, `ALPHAS`, `BACKTESTS`), de `apps/risk/compute.py` `status_for`, `Q4`, `Q6`, `Q10` e `ModelsMissing`, `RiskRun.Status`, e, só nos testes de paridade, `MODELS` e `_row`; `silver.asset` (`ticker`, `name`, `kind`, `status`), `silver.price` (`asset`, `date`, `adj_close`, `run`) e os `PROTECT` para `silver.asset` e `assets.CollectionRun` | `marco1` | `identidade` (M2.2a, `apps/portfolios`) | 🟡 implementado no ramo `identidade/M2.2-carteira` (2026-10-02); a `marco1` revisa na PR de implementação do [M2.2a](specs/M2.2a-carteira.md). Pede-se **"só cresce"**: renomear ou mudar o sentido de um deles quebra a carteira; o teste de paridade da conversão (RF-23) reprova na PR que mudar `_row` |
| **As rotas de carteira**: `/api/v1/portfolios*` e os `reason` de `invalid_holdings` | `identidade` (M2.2a) | `marco1` (M2.2b, as telas) | 🟡 implementado no ramo (2026-10-02), conforme a [spec do M2.2a](specs/M2.2a-carteira.md#contratos-externos); entra na `main` com o parecer da CVM; valor novo de `reason` é mudança de contrato |
| **`CELERY_BEAT_SCHEDULE`** | cada frente, a própria entrada | — | ✅ arquivo comum. A `fundamentos` acrescenta a sua e não mexe no horário das outras |

---

## Numeração de decisão

Cada frente numera na sua faixa, e duas frentes nunca criam o mesmo número em ramos
diferentes. A decisão que vale para todas usa a faixa de quem a escreve, e a PR dela passa pelas
outras frentes.

| Faixa | De quem | Usadas |
|---|---|---|
| D-75 a D-81 | `marco1`, reservadas pela spec do M1.5b | todas — as sete decisões do M1.5b |
| D-82 a D-84 | a divisão em frentes | todas |
| D-85 a D-99 | `marco1` | todas — a D-99 é do M1.6c |
| D-140 a D-159 | `marco1`, reservadas pela spec do M1.6c e divididas em 2026-09-29: M2.1b D-140–142, M1.7 D-143–145, M3.3 D-146–148, M1.5c D-149–150, M2.3 D-151–154, M1.6d D-155–156 | D-140, D-143, D-144, D-146 a D-153 (a D-143 e a D-144 com o M1.7, fechado, que deixa a D-145 sem uso; a D-149 e a D-150 com o M1.5c, fechado; a D-151 a D-153 com o M2.3, fechado, que deixou a D-154 sem uso) |
| D-100 a D-119 | `identidade` | todas — D-116 a D-119 são do M2.2a |
| D-160 a D-179 | `identidade`, reservada pela spec do M2.2a | — |
| D-120 a D-139 | `fundamentos` | D-120 a D-134 |

Acabou a faixa: a frente reserva a próxima livre de vinte, com uma linha nesta tabela, na PR da
spec seguinte.
