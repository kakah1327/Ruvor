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
| `marco1` | darkside171 | M1.5b ✅ → M1.6a ✅ → M1.6b | [frentes/marco1.md](frentes/marco1.md) | `marco1/M1.6-aplicacao-web` — M1.6a fechado, PR de implementação a abrir pelo dono da frente |
| `identidade` | ⏸ **sem dono** — espera o próximo dev | M2.1 | [frentes/identidade.md](frentes/identidade.md) | `identidade/M2.1-identidade-e-acesso` |
| `fundamentos` | kakah1327 (Kauã) | M3.1 ✅ → M3.2 | [frentes/fundamentos.md](frentes/fundamentos.md) | `fundamentos/M3.2-contexto` |

**Hoje são duas frentes ativas**, `marco1` e `fundamentos`. A `identidade` está definida — cerca,
contratos e próximo passo prontos — para quem entrar no time; até lá, ninguém escreve na cerca
dela.

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
| `marco1` | `engine/`; `backend/apps/risk/`, `backend/apps/analytics/`, `backend/apps/assets/`, `backend/apps/api/` (a API, criada pelo M1.6a), e os testes delas em `backend/tests/`; `frontend/`; `brand/`; `docs/mockups/M1.6*/`; os serviços `worker` e `beat` no `compose.yaml` |
| `identidade` | `backend/apps/accounts/`; `backend/tests/test_usuario.py`, `test_organizacao.py` e os testes novos do M2.1; as telas de login **numa pasta própria** de `frontend/src/`, **só depois** de o M1.6 entregar o casco (ver contratos) |
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
| **Convenções da API HTTP**: prefixo de rota, versão, formato de erro, autenticação | `marco1` (M1.6) e `identidade` (M2.1) | as duas | ✅ existe. Decidido pela [D-86](decisoes/D-86-convencoes-da-api-http.md) e aplicado pelo M1.6a: `/api/v1/`, `REST_FRAMEWORK` com o tratador do formato de erro, permissão padrão `IsAuthenticated` e cada view declarando a sua. **O mecanismo de autenticação é do M2.1**; mudar o formato de erro ou a regra de permissão exige a revisão das duas frentes |
| **Casco do frontend e kit completo**: layout, navegação, escala tipográfica, estados de interação | `marco1` (M1.6) | `identidade` (telas de login) | 🟡 **o kit está entregue** (M1.6a): `brand/ruvor/tokens.css` e `tokens.json` nos dois temas, com a escala tipográfica e os estados; `components.css`; e `icons/`, o conjunto fechado do Phosphor ([D-87](decisoes/D-87-os-mockups-sao-a-referencia-visual-do-kit.md), [D-88](decisoes/D-88-o-kit-tem-dois-temas-pelos-mesmos-tokens.md), [D-93](decisoes/D-93-os-icones-do-produto-vem-do-phosphor.md)), mostrado em `docs/mockups/M1.6a/kit.html`. **O casco — layout e navegação em tela — é do M1.6b**, e ainda não existe. A `identidade` faz o backend primeiro |
| **`gold.risk_run.requested_by`**: a dívida é do M2.1, o arquivo é de `apps/risk/` | `identidade` define o usuário; `marco1` é dona do arquivo | — | ⬜ a spec do M2.1 combina com a `marco1` quem escreve a linha |
| **`silver.asset`**: o catálogo, por ticker | `marco1` | `fundamentos` liga fundamento a ativo | ✅ existe. **Só cresce**: coluna nova pode, mudar ou tirar coluna exige a revisão da `fundamentos` |
| **`silver.price`**: o preço diário, por ativo | `marco1` | `fundamentos` lê `asset`, `date` e `close` para os múltiplos | ✅ existe. **Só cresce**, como o catálogo: mudar o sentido dessas colunas exige a revisão da `fundamentos` |
| **`core.user` e `core.organization`** | `identidade` | todas, no futuro | ✅ existe. A `identidade` muda. Enquanto nada fora de `accounts` depende deles, não há consumidor a proteger |
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
| D-85 a D-99 | `marco1` | D-85 a D-93 |
| D-100 a D-119 | `identidade` | — |
| D-120 a D-139 | `fundamentos` | D-120 a D-129 |

Acabou a faixa: a frente reserva a próxima livre de vinte, com uma linha nesta tabela, na PR da
spec seguinte.
