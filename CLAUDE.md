# Ruvor

Plataforma de análise de risco em ações. O usuário quer saber **quanto pode perder** se
aplicar em uma ação ou carteira, e a plataforma responde com transparência sobre o método.

**Diferencial:** múltiplos algoritmos comparados sobre a mesma base, com validação
estatística de qual deles merece confiança para aquele ativo.

---

## Comece por aqui

1. **[`docs/ESTADO.md`](docs/ESTADO.md)** — onde paramos e o que está aberto. **Leia sempre.**
2. **[`docs/PROCESSO.md`](docs/PROCESSO.md)** — como se trabalha aqui. **Leia antes de produzir qualquer coisa.**
3. **[`docs/aprendizados.md`](docs/aprendizados.md)** — armadilhas já descobertas. Leia antes de implementar.

Antes de mandar spec ou plano para revisão, rode a
[lista de verificação](docs/PROCESSO.md#antes-de-mandar-revisar). A primeira spec do projeto
custou cinco rodadas de revisão pelos seis defeitos que ela cobre.

---

## Autoridade dos documentos

Nem tudo no repositório é referência. Esta tabela resolve dúvida.

### Manda

| Documento | Sobre |
|---|---|
| [`docs/PROCESSO.md`](docs/PROCESSO.md) | como spec, plano e código nascem e são revisados |
| [`docs/PRODUTO.md`](docs/PRODUTO.md) | o que a plataforma é, para quem, marcos |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | pilha, estrutura, banco, execução, auditoria |
| [`docs/decisoes/`](docs/decisoes/) | decisões tomadas, com o porquê — **append-only** |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | ordem dos blocos e status |
| [`docs/ESTADO.md`](docs/ESTADO.md) | posição atual |
| [`docs/specs/`](docs/specs/) e [`docs/planos/`](docs/planos/) | o trabalho corrente |
| [`brand/ruvor/`](brand/ruvor/) | tokens, logo, regras e as quatro telas de referência (`mockups/`) |

### NÃO é referência

| Caminho | O que é | Cuidado |
|---|---|---|
| [`docs/prototipo/`](docs/prototipo/) | documentação do protótipo **VaR Lab**, que está sendo substituído | linha de base de revisão, **não** modelo de spec nem de código |
| [`docs/tcc/`](docs/tcc/) | trabalho acadêmico | escopo de pesquisa, **não** especificação de produto |
| `brand/ruvor/estudos/` | histórico de como se chegou à marca | em divergência com o kit, **o kit vence** |
| `brand/ruvor/examples/` | estudos visuais anteriores | em divergência, **`brand/ruvor/mockups/` vence** |

Se um documento antigo contradiz um destes, **estes vencem**.

---

## Regras invioláveis

**Commits sem assinatura de ferramenta.** Nenhum commit leva `Co-Authored-By`, referência a
assistente de IA ou link de sessão. A autoria é do time. Sem exceção
([D-27](docs/decisoes/D-27-commits-sem-assinatura.md)).

**Não commitar nem enviar por iniciativa própria.** Exceto o commit por tarefa dentro do
ramo do plano.

**Nunca inventar.** Não existe função, parâmetro, caminho ou endpoint "provável". Verifica
antes de usar.

**Perguntar quando** a resposta muda o resultado e não dá para derivar da spec, das decisões
ou do código. **Não perguntar quando** é derivável, convenção, ou barato de reverter.

**O lugar de perguntar é a spec, não a implementação.**

**Contrato congelado durante a implementação.** Mudou, para e escala.

**Relatar fielmente.** Teste falhou, diz que falhou, com a saída. Etapa pulada, diz que
pulou. Não existe "deve funcionar".

**`engine/` não importa Django.** Nunca ([D-17](docs/decisoes/D-17-monorepo-engine-sem-django.md)).

**Toda tela de produto passa por mockup aprovado antes de virar código**
([PROCESSO.md §7](docs/PROCESSO.md#7-portão-de-mockup)). Casco técnico — tela que só prova
que a infraestrutura responde — está fora
([D-30](docs/decisoes/D-30-portao-de-mockup-so-para-tela-de-produto.md)).

---

## Como o trabalho anda

```
ROADMAP → SPEC → ✋ → PLANO → ✋ → IMPLEMENTAÇÃO (contínua) → REVISÃO → fecha
                                    └ tarefa visual → mockup → ✋ → implementa
```

**Portões humanos:** spec, plano e cada mockup. O resto roda sozinho.
**Princípio:** portão humano onde o erro é caro e a máquina não detecta; autonomia onde o
teste detecta.

Detalhe completo, incluindo a anatomia de spec e de plano, em
[`docs/PROCESSO.md`](docs/PROCESSO.md).

---

## Idioma

Documentação, specs, planos, decisões, comentários e mensagens de commit **em português**.
Código — nomes de variável, função, classe — em inglês.

---

## Estado do repositório

Existem o **motor**, o **casco da aplicação**, o **ambiente local em contêiner**, a
**fundação de dados** — os quatro esquemas do banco, as primeiras tabelas, o **catálogo de
ações** da B3 e dez anos de preço de quatro ativos —, as primeiras **métricas de
comportamento** e o **risco** em `gold`: nove modelos de VaR, quatro backtests e o veredito
de adequação por ativo —, calculado **pela fila** e **agendado** pelo Celery Beat. Ainda não
existe API de negócio nem tela de produto.

- `engine/` — motor numérico: pacote Python isolado (`ruvor-engine`) na versão **0.2.0**, 9
  modelos de VaR, 4 testes de backtesting, 102 testes e linha de base numérica. Roda por linha
  de comando: `ruvor run`. **Nunca importa Django**, e um teste prova isso. Os três modelos
  neurais fixam semente por `engine/src/engine/seeding.py`
  ([D-63](docs/decisoes/D-63-semente-fixa-entra-no-manifesto.md)), e o `py.typed` deixa o
  `mypy` do backend enxergar os tipos dele.
- `backend/` — projeto Django com quatro apps, `apps/accounts`, `apps/assets`,
  `apps/analytics` e `apps/risk`. Uma rota, `GET /health`. Conecta no PostgreSQL e tem fila Celery sobre
  Redis: a tarefa de fumaça `config.tasks.ping`, por import explícito, e as sete tarefas de
  app, por descoberta automática — `apps/risk/tasks.py` (a abertura, uma por (ativo, modelo),
  o fecho e o leque `recalcular_cobertos`) e `apps/assets/tasks.py` (catálogo, preços e a
  `rotina_diaria`, que encadeia preços → risco). O `CELERY_BEAT_SCHEDULE` tem duas entradas,
  com horário em `RUVOR_BEAT_ASSETS_CRON` e `RUVOR_BEAT_PRICES_CRON`
  ([D-67](docs/decisoes/D-67-uma-tarefa-por-ativo-e-modelo-restringe-o-rf-12-do-m1-4.md) a
  [D-72](docs/decisoes/D-72-o-fecho-escreve-metadado-de-execucao-restringe-a-d-16.md)).
  Configuração por variáveis `RUVOR_*`; mypy estrito; 304 testes com pytest-django, que
  **rodam no contêiner `worker`** — é o único que tem o motor
  ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md) segue valendo para o resto).
  `migrate` num banco vazio cria os quatro esquemas — `core`, `bronze`, `silver` e `gold` —,
  as tabelas `core.organization` e `core.user`, a organização fixa do Marco 1 (`slug`
  `ruvor`), as quatro tabelas da `bronze`, e `silver.asset`, `silver.price` e
  `silver.corporate_event`, e as quatro tabelas da `gold`, `gold.behavior_metric`,
  `gold.return_histogram_bin`, `gold.risk_run` e `gold.risk_result` — vinte ao todo. O `AUTH_USER_MODEL`
  é próprio e autentica por e-mail
  ([D-39](docs/decisoes/D-39-usuario-proprio-autentica-por-email.md)). `manage.py
  import_assets` consulta a B3 e conforma o catálogo de ações em `silver.asset`
  ([D-47](docs/decisoes/D-47-fonte-do-catalogo-e-o-site-da-b3.md),
  [D-48](docs/decisoes/D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md));
  `manage.py import_prices` consulta o Yahoo e conforma dez anos de preços com retorno
  logarítmico ([D-50](docs/decisoes/D-50-preco-vem-do-chart-v8-do-yahoo-por-http-direto.md) a
  [D-54](docs/decisoes/D-54-transacao-por-ativo-restringe-a-d-48.md)); `manage.py
  compute_metrics` lê `silver` e escreve em `gold`, por ativo e em transação, a linha imutável
  de métricas de comportamento mais os 42 baldes do histograma de retornos
  ([D-55](docs/decisoes/D-55-metrica-de-comportamento-e-imutavel.md) a
  [D-60](docs/decisoes/D-60-metrica-descritiva-sem-manifesto-restringe-a-d-15.md)). **`gold`
  deixou de estar vazio no M1.3**; o cálculo da camada 2 usa só a biblioteca padrão.
  `manage.py compute_risk` roda os nove modelos de VaR sobre `silver.price` e grava em `gold`
  a execução com o manifesto e os resultados, cada um com o VaR, os quatro backtests e o
  veredito de adequação
  ([D-61](docs/decisoes/D-61-backend-alimenta-o-motor-por-dataprovider.md) a
  [D-66](docs/decisoes/D-66-registry-incompleto-e-erro-restringe-o-silencio-do-motor.md));
  com `--async`, enfileira uma abertura por ativo e devolve — a `risk_run` nasce no `worker`
  como `running`, cada modelo grava os seus dois resultados em transação própria, e o fecho
  escreve `status` (`ok`, `partial` ou `failed`) e `finished_at`. O
  backend **não declara** `numpy` nem `pandas`: o `pandas` chega pelo motor, que só é
  instalado no `worker`.
- `frontend/` — React em TypeScript estrito, Vite, Vitest. Uma tela de verificação, que
  consome `brand/ruvor/tokens.css` pelo apelido `@brand`; uma varredura automatizada reprova
  cor literal em `frontend/src/`. Lint e formatação são do **Biome**, por `npm run lint`
  ([D-43](docs/decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)) — do lado Python,
  os dois projetos usam `ruff`. O `package.json` exige **Node 24.15+**, travado por
  `engine-strict` — mas isso é da imagem `node:24-slim`, não da máquina: quem não sair do
  contêiner não precisa de Node instalado.
- `compose.yaml` na raiz — `docker compose up` sobe seis serviços: `postgres`, `redis`,
  `web`, `worker`, `beat` e `frontend`. O `worker` roda com `--concurrency=2`; o `beat` usa a
  imagem do `worker`, sem `build` próprio, e **agenda coleta real** — `docker compose stop
  beat` quando isso não for desejado. Backend e frontend rodam aí no dia a dia; o motor segue
  no `.venv/` nativo ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)).

Um só `.venv/` na raiz para motor e backend. O protótipo Flask, o SQLite e o frontend antigo
foram removidos por inteiro.
