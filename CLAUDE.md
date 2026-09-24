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
ações** da B3 e dez anos de preço de quatro ativos — e as primeiras **métricas de
comportamento** em `gold`. Ainda não existe API de negócio nem tela de produto.

- `engine/` — motor numérico: pacote Python isolado (`ruvor-engine`), 9 modelos de VaR, 4
  testes de backtesting, 64 testes e linha de base numérica. Roda por linha de comando:
  `ruvor run`. **Nunca importa Django**, e um teste prova isso.
- `backend/` — projeto Django com três apps, `apps/accounts`, `apps/assets` e
  `apps/analytics`. Uma rota, `GET /health`. Conecta no PostgreSQL e tem fila Celery sobre
  Redis, com a tarefa de fumaça `config.tasks.ping`.
  Configuração por variáveis `RUVOR_*`; mypy estrito; 199 testes com pytest-django.
  `migrate` num banco vazio cria os quatro esquemas — `core`, `bronze`, `silver` e `gold` —,
  as tabelas `core.organization` e `core.user`, a organização fixa do Marco 1 (`slug`
  `ruvor`), as quatro tabelas da `bronze`, e `silver.asset`, `silver.price` e
  `silver.corporate_event`, e as duas tabelas da `gold`, `gold.behavior_metric` e
  `gold.return_histogram_bin` — dezoito ao todo. O `AUTH_USER_MODEL`
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
  deixou de estar vazio no M1.3**; o cálculo usa só a biblioteca padrão, e o backend segue sem
  `numpy` e sem `pandas`.
- `frontend/` — React em TypeScript estrito, Vite, Vitest. Uma tela de verificação, que
  consome `brand/ruvor/tokens.css` pelo apelido `@brand`; uma varredura automatizada reprova
  cor literal em `frontend/src/`. Lint e formatação são do **Biome**, por `npm run lint`
  ([D-43](docs/decisoes/D-43-ruff-e-biome-e-onde-cada-verificacao-roda.md)) — do lado Python,
  os dois projetos usam `ruff`. O `package.json` exige **Node 24.15+**, travado por
  `engine-strict` — mas isso é da imagem `node:24-slim`, não da máquina: quem não sair do
  contêiner não precisa de Node instalado.
- `compose.yaml` na raiz — `docker compose up` sobe cinco serviços: `postgres`, `redis`,
  `web`, `worker` e `frontend`. Backend e frontend rodam aí no dia a dia; o motor segue no
  `.venv/` nativo ([D-33](docs/decisoes/D-33-dia-a-dia-dentro-do-conteiner.md)).

Um só `.venv/` na raiz para motor e backend. O protótipo Flask, o SQLite e o frontend antigo
foram removidos por inteiro.
