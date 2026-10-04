# Roadmap

Até onde vamos e em que ordem. Onde estamos agora está em [ESTADO.md](ESTADO.md).

Cada bloco recebe spec própria → plano próprio → implementação, conforme
[PROCESSO.md](PROCESSO.md). Um marco fecha quando todos os seus blocos fecham.

**Legenda:** ⬜ não começou · 🟡 em andamento · ✅ fechado

**Frentes trabalham ao mesmo tempo** desde 2026-09-26
([D-84](decisoes/D-84-frentes-com-cerca-de-pastas.md)): `marco1` fica com o M1.5b e o
M1.6, `fundamentos` com o M3.1 e o M3.2; `identidade`, com o M2.1, o M4.2, o M4.1 e o M2.2a (o backend da carteira), é do Kauã desde 2026-09-27 — sem telas: toda interface visual é da `marco1`. A ordem dos marcos é a da entrega ao
usuário; o que impede um bloco de começar é dependência. Quem faz o quê está em
[FRENTES.md](FRENTES.md).

---

## Fundação

Não entrega nada ao usuário final. É o alicerce, e é o que faltou antes.

**✅ Fechada em 2026-09-08.** Sete blocos, do F1 ao F5. O último provou o repositório
numa máquina que não é a do desenvolvedor — e foi lá que se descobriu que a linha de
base numérica do motor não é portátil entre plataformas.

| | Bloco | Entrega |
|---|---|---|
| ✅ | **F1 — Documentação de base** | PROCESSO, PRODUTO, ARQUITETURA, decisões, ROADMAP, ESTADO, CLAUDE.md |
| ✅ | **F6 — Agentes do projeto** (antecipado) | definições em `.claude/agents/`, com restrição por ferramenta |
| ✅ | **F2a — Migração do motor** | `engine/` isolado, rebrand, empacotamento próprio, linha de base numérica |
| ✅ | **F2b — Casco da aplicação** | projeto Django e projeto React funcionais, com identidade Ruvor |
| ✅ | **F3 — Ambiente local** | `docker compose up` sobe Postgres, Redis, web, worker e frontend; duas imagens do backend (web leve, worker com ML); cria `infra/` |
| ✅ | **F4 — Fundação de dados** | primeiras migrations, os quatro esquemas, Organização e usuário próprio |
| ✅ | **F5 — Integração contínua** | estilo, tipos e testes a cada push; quatro trabalhos em máquina limpa |

---

## Marco 1 — a ação, e o risco dela

**✅ Fechado em 2026-09-29**, com o M1.6b. O M1.6c, que mora nesta tabela, completa na tela o
Marco 3 ([D-95](decisoes/D-95-o-m1-6-em-tres-blocos.md)).

Digita ITUB4, recebe tudo sobre o comportamento da ação **e** a comparação de risco que
ninguém mais faz. Sem login, sem carteira.

Coincide em grande parte com o conteúdo do TCC — os dois avançam juntos.

| | Bloco | Entrega |
|---|---|---|
| ✅ | **M1.1 — Catálogo de ativos** | lista de papéis da B3 com nome, setor e situação; base da busca — fechado em 2026-09-21, 473 ações + Ibovespa |
| ✅ | **M1.2 — Ingestão de preços** | histórico + atualização incremental, `bronze` com data de coleta, `silver.price` e eventos — fechado em 2026-09-22, quatro ativos de dez anos |
| ✅ | **M1.3 — Camadas 1 e 2** | identidade, preço, gráfico, volume, dividendos, retornos, volatilidade, quedas, **distribuição de retornos** e relação com o Ibovespa — fechado em 2026-09-24, `gold` povoado pelos quatro ativos. **O tamanho não entrou aqui:** a capitalização de mercado não tinha fonte no repositório, e o M3.1 a entregou em `gold.fundamental_indicator` — soma das classes, nula quando falta preço de alguma classe, e sempre nula para PNA e PNB, que a CVM não separa ([D-124](decisoes/D-124-capitalizacao-soma-as-classes-e-a-escala-das-acoes-e-inferida.md)) |
| ✅ | **M1.4 — Motor de risco** | semente fixa nos três modelos neurais, manifesto de execução e o veredito de adequação por (modelo, nível) — `manage.py compute_risk` no contêiner `worker`, `gold.risk_run` e `gold.risk_result` (a migração é do F2a). Fechado em 2026-09-24, quatro ativos × 18 resultados. **A fila não é deste bloco:** a linha original dizia "integração com a fila", o M1.5 dizia a mesma coisa, e a spec do M1.4 resolveu a divergência **a favor do M1.5** — aqui o comando é síncrono |
| ✅ | **M1.5 — Execução assíncrona** | fila, modo A com transação por (ativo, modelo), estado da execução, Beat e o agendamento das ingestões (`import_assets`, `import_prices`) — `compute_risk --async`, sete tarefas em `apps/*/tasks.py` e o serviço `beat`. Fechado em 2026-09-25: a execução real reproduziu os 72 resultados do M1.4 campo a campo, e um tique real do Beat rodou coleta e recálculo sozinho. **Não derruba os 2 min por ativo** — quem faz isso é o M1.5b |
| ✅ | **M1.5b — Treino separado da previsão** | a [D-18](decisoes/D-18-separacao-treino-previsao.md), restringida pela [D-80](decisoes/D-80-o-retreino-de-producao-e-a-cada-252-pregoes-restringe-a-d-18.md): os quatro modelos caros guardam um **retrato** por ponto de retreino em `gold.model_snapshot`, e o recálculo reaproveita os válidos, treina só o que falta e reconstitui a série inteira do backtest por previsão — igual, campo a campo, ao cálculo do zero (`compute_risk --full`). Motor `0.3.0`, imagem do `worker` travada pelo lock, `--max-tasks-per-child=5`. Fechado em 2026-09-27: o cálculo completo custou 141 a 175 s por ativo, e o recálculo sem treino, **4,5 a 10,3 s** — 3,2% a 6,3% do completo. Nasceu ao dividir o M1.5, que ficara com quatro frentes |
| ✅ | **M1.6a — Fundação da aplicação** | o kit completo (tokens dos mockups, escala tipográfica, estados, tema escuro, componentes e a vitrine), as convenções da API aplicadas ([D-86](decisoes/D-86-convencoes-da-api-http.md)), a API de leitura e o **cálculo sob demanda** para ativo não coberto (a cauda longa da [D-19](decisoes/D-19-cobertura-de-ativos-em-camadas.md)), e as métricas na rotina diária. O M1.6 foi dividido em dois em 2026-09-27. Fechado em 2026-09-28: o kit nos dois temas com a folha de componentes e os ícones do Phosphor, a vitrine aprovada no portão de mockup; seis rotas em `/api/v1/` e o `POST` do pedido em `core.compute_request`; um ativo sem preço (`BBDC4`) pedido e calculado em **99,6 s** — coleta, métricas e risco |
| ✅ | **M1.6b — As telas** | casco, busca e tela do ativo com as camadas 1 a 3, cada uma com mockup aprovado antes do código; a discordância entre modelos e os não rejeitados por ativo (5.1 e 5.2, [D-96](decisoes/D-96-discordancia-e-aprovados-entram-no-marco-1.md)), o VaR de 1 dia ([D-98](decisoes/D-98-o-horizonte-do-marco-1-e-1-dia-restringe-a-d-05.md)), gráficos pelo uPlot ([D-94](decisoes/D-94-os-graficos-sao-do-uplot.md)). Fechado em 2026-09-29: um ativo sem preço (`AALR3`) pedido pela tela e calculado em **100,8 s**; a tela do `ITUB4` pronta em **312 ms**; 731 testes no frontend e 28 mutações reprovando |
| ✅ | **M1.6c — Fundamentos e contexto na tela** | as camadas 4 e 5 na tela do ativo, depois do risco, com as rotas `/fundamentals` e `/disclosures` escritas pela `marco1` em `apps/api` e as tabelas da `fundamentos` como contrato ([D-95](decisoes/D-95-o-m1-6-em-tres-blocos.md), [D-99](decisoes/D-99-as-camadas-4-e-5-depois-do-risco-e-as-tabelas-da-fundamentos-sao-contrato.md)). Fechado em 2026-09-29: os 17 indicadores com a frase de cada um e o porquê de cada nulo, a posição entre os pares em contagem exata, os comunicados da companhia à CVM com filtro; 240 conferências na execução real |
| ✅ | **M1.6d — Acabamento** | **fechado em 2026-09-30**; o `aria-live` só no andamento das três seções, o `preset` do Biome e a guarda de dependência numérica no backend — [spec](specs/M1.6d-acabamento.md) e [plano](planos/M1.6d-acabamento.md) aprovados (PR #19), frente `marco1` |
| ✅ | **M1.5c — Execução presa** | **fechado em 2026-09-30**; a varredura fecha a `risk_run` presa em `running` pela regra do fecho, na `rotina_diaria` e por comando ([D-149](decisoes/D-149-a-execucao-presa-e-fechada-pela-regra-do-fecho.md), [D-150](decisoes/D-150-o-fecho-so-escreve-sobre-execucao-em-running.md)) — spec e plano aprovados (PR #23), frente `marco1` |
| ✅ | **M1.7 — Busca e catálogo** | **fechado em 2026-10-02**; a busca sem acento pelo `unaccent` ([D-143](decisoes/D-143-a-busca-ignora-acento-pelo-unaccent.md)), a sugestão pela API com `has_risk` e a classificação da B3 com vírgula na saída da API ([D-144](decisoes/D-144-a-classificacao-da-b3-se-corrige-na-saida-da-api-estende-a-d-47.md)) — [spec](specs/M1.7-busca-e-catalogo.md) e [plano](planos/M1.7-busca-e-catalogo.md) aprovados (PR #21), frente `marco1`; paga três dívidas do M1.6b; na execução real, a sugestão igual à primeira página de `has_risk=true` (seis ativos) e "itaú" achando o `ITUB4` |
| ✅ | **M1.4b — Correção do motor** | **fechado em 2026-10-03**; o GARCH e o EGARCH sem olhar à frente, os três tradicionais em janela expansiva reestimada a cada 252 pregões, o motor `0.4.0`, a linha de base e a referência do trecho 0 recapturadas e os seis ativos cobertos recalculados do zero, na ordem em que nenhum cálculo roda com código e versão desencontrados ([D-157](decisoes/D-157-alteracao-no-motor-em-lista-fechada-para-a-correcao-do-m1-4b-restringe-a-d-76.md) a [D-159](decisoes/D-159-a-linha-de-base-numerica-e-a-do-motor-0-4-0-restringe-a-d-44.md)) — [spec](specs/M1.4b-correcao-do-motor.md) e [plano](planos/M1.4b-correcao-do-motor.md) aprovados pelo dono, frente `marco1`, a PR única — spec, plano e implementação — a abrir. Nasceu da conferência técnica do M2.3; na execução real, o `lstm`, o `gru` e o `caviar` iguais campo a campo, o GARCH e o EGARCH com as violações perto das esperadas, e a zona de Basileia sem defeito |

**Candidatos promovidos a este marco** ([D-96](decisoes/D-96-discordancia-e-aprovados-entram-no-marco-1.md),
2026-09-28): a discordância entre modelos (5.1) e os modelos não rejeitados por ativo (5.2), na tela
do M1.6b. O estresse histórico (5.3) entrou depois, no M3.3, fora do Marco 1
([PRODUTO.md](PRODUTO.md#5-requisitos-candidatos), [D-146](decisoes/D-146-o-estresse-historico-vira-bloco-so-do-ativo-e-so-com-preco.md)).

**O regime de laboratório não é deste marco**
([D-74](decisoes/D-74-o-marco-1-e-so-producao.md), 2026-09-25). A camada 3 do Marco 1 é só
produção; o laboratório vai para o Marco 2, como M2.4.

---

## Marco 2 — vira plataforma

| | Bloco | Entrega |
|---|---|---|
| ✅ | **M2.1a — Identidade e acesso** | **fechado em 2026-09-30** (fase 1 em 2026-09-27; fase 2 na `main` pela PR #13, e a T14 depois do M2.1m); o backend: sessão, cadastro, entrada, papéis `admin`/`member` por organização, gestão de usuários pela administradora, auditoria de acesso e `requested_by` — frente `identidade`, em duas fases ([D-107](decisoes/D-107-m2-1a-em-duas-fases-restringe-a-d-82.md)): a 1 sem nada do M1.6a, a 2 com as rotas, depois do M1.6a. As telas que consomem as rotas são da `marco1` |
| ✅ | **M2.1m — A coluna do autor do pedido** | **fechado em 2026-09-29**; a metade da `marco1` no M2.1a: `core.compute_request.requested_by`, a coluna que a T14 do M2.1a preenche ([spec](specs/M2.1m-requested-by.md)) — frente `marco1` |
| ✅ | **M2.1b — Telas de acesso** | **fechado em 2026-10-03**; entrar, cadastro, troca de senha (inclusive a obrigatória), menu de conta e gestão de usuários, cada uma com mockup aprovado, sobre o casco e o kit do M1.6b e as rotas do M2.1a; o pedido de cálculo passa a exigir conta ([D-140](decisoes/D-140-o-pedido-de-calculo-exige-conta-restringe-a-d-90.md)) — spec e plano aprovados (PR #24), **frente `marco1`** (toda interface visual é dela, decisão do darkside171, 2026-09-27). Cinco portões de mockup, 1621 testes no frontend e, na execução real, 133 conferências do roteiro de acesso, com 36 comparações com os mockups sem diferença; a PR de implementação espera o ajuste da `identidade` no caso anônimo do `test_requested_by.py` |
| ✅ | **M2.2a — Carteira** | composição pelo usuário — pesos em %, versionada — e risco de carteira pelo caminho barato, sob demanda, nos nove modelos ([D-116](decisoes/D-116-o-parecer-da-cvm-nao-bloqueia-a-spec-da-carteira-e-segura-a-implementacao.md) a [D-119](decisoes/D-119-o-risco-da-carteira-e-sob-demanda-em-gold-na-app-da-frente.md)) — [spec](specs/M2.2a-carteira.md) e [plano](planos/M2.2a-carteira.md) aprovados (PR #31) e **fechado em 2026-10-02** (T0 a T8, execução real feita) e na `main` pela PR #34, frente `identidade`, só backend; sem o parecer da CVM ([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)) |
| ⬜ | **M2.2b — Telas da carteira** | montar, editar e ver o risco da carteira, cada tela com mockup aprovado, sobre as rotas do M2.2a — **frente `marco1`** (toda interface visual é dela) |
| ✅ | **M2.3 — Camada explicativa** | **fechado em 2026-10-02**; leitura iniciante/avançado como sistema: alternador global no casco, uma frase avançada por número, detalhes técnicos recolhidos na iniciante ([D-151](decisoes/D-151-o-texto-das-duas-leituras-mora-no-frontend-restringe-a-d-97.md) a [D-153](decisoes/D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md)) — spec e plano aprovados (PR #22), frente `marco1`. As 55 chaves com a frase avançada conferida no código que calcula, quatro portões de mockup, 1206 testes no frontend e 631 conferências na execução real, nos dois níveis |
| ⬜ | **M2.4 — Regime de laboratório** | a camada 3 validada ao longo de uma década, na plataforma ([D-04](decisoes/D-04-dois-regimes-de-operacao.md)); veio do Marco 1 pela [D-74](decisoes/D-74-o-marco-1-e-so-producao.md) |

**Sem pré-requisito externo:** o parecer sobre a fronteira regulatória da CVM só vale antes de comercializar a
plataforma, não antes de bloco nenhum ([D-160](decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md), que substitui a D-116, item 2, e a
[D-153](decisoes/D-153-o-parecer-da-cvm-nao-bloqueia-o-m2-3.md), item 2). O lado seguro do desenho continua: a
pessoa escolhe ativos e pesos, e a plataforma não sugere.

---

## Marco 3 — "tudo sobre a ação" completo

| | Bloco | Entrega |
|---|---|---|
| ✅ | **M3.1 — Fundamentos** | camada 4, com fonte adequada para B3 (Yahoo não serve) — dados abertos da CVM (ITR e DFP, 2016 em diante) em `bronze`, companhias e balanços trimestrais em `silver`, indicadores e capitalização em `gold`; `import_fundamentals`, `compute_fundamentals` e a coleta semanal encadeada no Beat. Fechado em 2026-09-27, frente `fundamentos`: 339 companhias, 471 ações calculadas, e lucro, PL e dívida de PETR4, VALE3 e ITUB4 iguais à divulgação das companhias. **EBITDA fica de fora** |
| ✅ | **M3.2 — Contexto** | camada 5: notícias e comparação setorial — os comunicados da companhia à CVM (IPE: fato relevante, comunicado ao mercado e aviso aos acionistas) em `silver.disclosure`, só na versão corrente, coletados de segunda a sexta pela quarta entrada do Beat; e a comparação com os pares do segmento da B3, ou do subsetor, em `gold.peer_comparison`, gravada pelo `compute_fundamentals` depois dos indicadores. Fechado em 2026-09-27, frente `fundamentos`: 80.900 comunicados de 339 companhias, 471 ações comparadas, 17 sem grupo. **Imprensa e o texto do documento ficam de fora** ([D-130](decisoes/D-130-noticia-e-o-que-a-companhia-divulga-na-cvm.md)) |
| ✅ | **M3.3 — Estresse histórico** | **fechado em 2026-10-02**; o requisito candidato 5.3, só do ativo e só com preço: quatro episódios curados, com queda, retorno, recuperação e o Ibovespa lado a lado, em `gold.stress_episode` pelo `/metrics` ([D-146](decisoes/D-146-o-estresse-historico-vira-bloco-so-do-ativo-e-so-com-preco.md) a [D-148](decisoes/D-148-o-estresse-e-tabela-filha-da-metrica-e-sai-pelo-metrics.md)) — spec e plano aprovados (PR #20), frente `marco1`. O bloco "Em momentos de estresse" na seção Comportamento, nas duas leituras, com um portão de mockup; o oráculo SQL bateu nos oito conjuntos do IBOV e da PETR4, e a execução real fechou com 642 conferências |

---

## Marco 4 — produto institucional

| | Bloco | Entrega |
|---|---|---|
| ✅ | **M4.1 — Relatórios** | **fechado em 2026-09-30**: o relatório de risco de um ativo, exportável e auditável — gerado pela sessão em `POST /api/v1/reports`, guardado para sempre em `core.report` com os bytes exatos do JSON e o SHA-256 deles, imutável no Django e no banco (o primeiro gatilho), baixado em JSON (o original) ou CSV (derivado), e lido também pela chave de leitura ([D-113](decisoes/D-113-o-relatorio-e-uma-foto-guardada-com-sha-256.md) a [D-115](decisoes/D-115-a-chave-de-leitura-le-o-relatorio-da-organizacao-estende-a-d-108.md)) — frente `identidade` |
| ✅ | **M4.2 — API pública** | **fechado em 2026-09-28**: chave pessoal de leitura (`/api/v1/api-keys`), taxa em toda rota — por chave, por usuário e por IP —, o filtro automático por organização em `core.api_key` e o esquema OpenAPI em `/api/v1/schema`, gerado pelo drf-spectacular sem aviso nem erro ([D-108](decisoes/D-108-a-api-aceita-chave-pessoal-de-leitura.md) a [D-112](decisoes/D-112-o-filtro-automatico-por-organizacao-nasce-no-m4-2.md)) — frente `identidade` |

---

## Marco 5

| | Bloco | Entrega |
|---|---|---|
| ⬜ | **M5.1 — Retorno** | estimativa de retorno/lucro |

---

## Trilha paralela — TCC

Independente da plataforma. É tempo de máquina, não desenvolvimento.

| | Tarefa | Observação |
|---|---|---|
| ✅ | Fixar semente das redes neurais | **feito no M1.4** — `engine/src/engine/seeding.py`, aplicada no início de cada treino ([D-63](decisoes/D-63-semente-fixa-entra-no-manifesto.md)). Era pré-requisito de tudo abaixo |
| ⬜ | Refazer a Tabela 1 (modelos de ML) | os números atuais vieram de execução sem semente |
| ⬜ | Refazer a Tabela 2 e a conclusão preliminar | saíram do motor com os dois defeitos que o M1.4b corrigiu — o GARCH e o EGARCH viam o retorno do dia, e os tradicionais eram o quantil do primeiro ano; a conclusão "GARCH/EGARCH ganham dos tradicionais estáticos" não se sustenta sem refazer. A Tabela 1 também tem o `garchnet`, que mudou no `0.4.0` |
| ⬜ | Executar a Etapa 6 | 9 modelos × 4 ativos × 2 níveis; ~1h em CPU paralelizada |
| ⬜ | Escrever §4.5 e o Capítulo 5 | dependem da Etapa 6 |
| ⬜ | Renomear VaR Lab → Ruvor no texto | |
| ⬜ | Corrigir divergências do §3.2 | Flask/Jinja2, QuantReg, ausência de banco |

Detalhe das divergências em
[`docs/prototipo/07-backlog-specs.md`](prototipo/07-backlog-specs.md).

---

## Fora de escopo, registrado

Levantado e deliberadamente adiado ou descartado:

- Execução de ordens e intermediação de investimento — nunca
- Importação de carteira de corretora — [D-03](decisoes/D-03-carteira-montada-pelo-usuario.md)
- Dados tick a tick — [D-04](decisoes/D-04-dois-regimes-de-operacao.md)
- Modelagem multivariada de correlação (caminho caro da carteira) — a decidir
- Expected Shortfall — candidato, sem marco definido
