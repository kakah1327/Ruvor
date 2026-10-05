# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b ✅ → M1.6c ✅ → M2.1m ✅ → M1.6d ✅ → M1.5c ✅ → M1.7 ✅ → M2.3 ✅ → M3.3 ✅ → M1.4b ✅ →
M2.1b ✅ → M2.4 ✅ → M5.1 ✅; o M2.2b no ramo dele. O M1.6b fechou o Marco 1: digita ITUB4, recebe o
comportamento e o risco; o M1.6c completou a tela com as camadas 4 e 5; o M2.3 deu a ela as duas leituras, iniciante e
avançada; o M3.3, o estresse histórico na seção Comportamento; o M1.4b corrigiu o motor (`0.4.0`): o GARCH e o EGARCH
sem olhar à frente, e os tradicionais em janela expansiva; o M2.1b, as telas de acesso — entrar, cadastro, troca de senha,
menu de conta e gestão de usuários — e o pedido de cálculo só com conta (D-140); o M2.4, o regime de laboratório — o
experimento fixo da década de cada ativo, ano a ano, numa seção logo depois do risco (D-183 a D-187); o M5.1, o retorno —
dois modelos simples validados contra o retorno zero e a previsão do próximo pregão junto do veredito, no motor `0.5.0`
(D-188 a D-192), terminado pelo Kauã na máquina dele.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 (todas usadas; a D-99 é do M1.6c) e
D-140 a D-159, reservadas pela spec do M1.6c e divididas entre os seis blocos abertos em 2026-09-29 — usadas D-140,
D-143 e D-144, D-146 a D-153 — a D-140 com o M2.1b, fechado (a D-141 e a D-142 ficam sem uso); a D-146 a D-148 com o M3.3, fechado; a D-143 e a D-144 com o M1.7, fechado (a D-145 fica sem uso); a D-149 e a D-150 com o
M1.5c, fechado; a D-151 a D-153 com o M2.3, fechado, e a D-154 sem uso; e a D-157 a D-159, tomadas pela spec do M1.4b,
fechado; e a D-180 a D-199, reservada pela spec do M2.2b (D-180 a D-182) e dividida com o M2.4, que usou a D-183 a
D-187, e com o M5.1, que usou a D-188 a D-192 (ver [FRENTES.md](../FRENTES.md#numeração-de-decisão)).

---

## Agora

**Seis blocos com spec e plano aprovados e na `main`** (PRs #19 a #24, mescladas em 2026-09-30); o **M1.6d fechou em 2026-09-30** (PR #27), o **M1.5c em 2026-09-30** (PR #30, mesclada em 2026-10-01) e o
**M1.7 em 2026-10-02** (PR #32, mesclada no mesmo dia); o **M2.3 fechou em 2026-10-02** (PR #33); o **M3.3 fechou em 2026-10-02**, a T5 em diante noutra máquina, com o ramo no checkout principal, e entrou pela PR #37; o **M1.4b fechou em 2026-10-03** — a correção do motor, nascida da conferência técnica do M2.3 —, com spec, plano e implementação numa PR só, e entrou pela PR #38; o **M2.1b fechou em 2026-10-03** — as telas de acesso, com os cinco portões de mockup —, com a PR de implementação a abrir, depois do ajuste da `identidade` no caso anônimo do `test_requested_by.py`. Cada ramo tem o seu worktree em
`E:/Temp/Trilobit/varlab-wt/<bloco>`; spec e plano entram juntos, num commit, e a PR mesclada pelo dono foi o portão
dos dois; a implementação de cada bloco sai do mesmo ramo, numa PR própria. Todas as specs passaram por revisão adversarial (a do M1.6d, inline) e foram aprovadas pelo dono; todos
os planos passaram por revisão contra a spec, alguns em duas ou três rodadas.

| Bloco | Ramo | PR | Tarefas | Portões de mockup | Revisão de outra frente |
|---|---|---|---|---|---|
| [M1.6d — Acabamento](../specs/M1.6d-acabamento.md) ✅ | `marco1/M1.6d-acabamento` | #19 | 6 | — | — |
| [M1.5c — Execução presa](../specs/M1.5c-execucao-presa.md) ✅ | `marco1/M1.5c-execucao-presa` | #23 | 10 | — | `identidade` (cruza com a T14 do M2.1a) |
| [M1.7 — Busca e catálogo](../specs/M1.7-busca-e-catalogo.md) ✅ | `marco1/M1.7-busca-e-catalogo` | #21 | 9 | 1 | `fundamentos` (o grupo de pares com vírgula) |
| [M3.3 — Estresse histórico](../specs/M3.3-estresse-historico.md) ✅ | `marco1/M3.3-estresse-historico` | #20 | 9 | 1 | — |
| [M2.3 — Camada explicativa](../specs/M2.3-camada-explicativa.md) ✅ | `marco1/M2.3-camada-explicativa` | #22 | 16 | 4 | — (estende a cerca de mockups da `marco1`) |
| [M2.1b — Telas de acesso](../specs/M2.1b-telas-de-acesso.md) ✅ | `marco1/M2.1b-telas-de-acesso` | #24 | 16 | 5 | `identidade` (o `POST /risk` exige conta, D-140) |
| [M1.4b — Correção do motor](../specs/M1.4b-correcao-do-motor.md) ✅ | `marco1/M1.4b-correcao-do-motor` | #38 (spec, plano e implementação) | 9 (T0 a T7, com a T6b) | — (D-158) | — (aviso à `identidade`: a imagem `0.4.0`) |
| [M2.4 — Regime de laboratório](../specs/M2.4-regime-de-laboratorio.md) ✅ | `marco1/M2.4-regime-de-laboratorio` | #40 | 15 (T0 a T14) | 1 | — |
| [M5.1 — Retorno](../specs/M5.1-retorno.md) ✅ | `marco1/M5.1-retorno` | #41 (implementação) | 15 (T0 a T14; T10 a T14 pelo Kauã) | 1 | — (a D-192 estende a D-160, da `identidade`: a PR da spec passou pelo dono dela) |

**Ordem de merge das PRs de spec e plano (cumprida):** #19 → #23 → #21 → #20 → #22 → #24. A implementação segue M1.7 → M2.3 → M3.3 → M2.1b. O M2.3 depende do M1.6d mesclado; o M2.1b espera
combinar com a `identidade` a ordem com a T14 do M2.1a, cujo teste de pedido anônimo passa a esperar 401.

**Como a implementação roda** (regra escrita em todos os planos): testes em contêiner avulso com o worktree montado,
uma suíte de backend por vez na máquina (o banco de teste é um só); quando um bloco precisa do stack servindo o
ramo — mockup com dado real, tela, execução real —, o orquestrador põe o checkout principal em
`git switch --detach <HEAD do ramo>`, com ele livre, e o devolve no fim; parar e subir o Beat é do orquestrador.

## Próximo passo

1. **Rever o `frontend/e2e/capturas.mjs`** antes da próxima execução real: foi escrito para a página em rolagem, e a
   tela do ativo agora tem seis abas (D-193). Ver as abas e o carvão quente no celular. Os ajustes de tela entraram pela
   PR #42 (2026-10-05) e o M5.1 pela PR #41: a imagem do `worker` diz `0.5.0`.
2. **O M2.2b**, no ramo dele (96 commits atrás da `main` em 2026-10-05): recebe a `main` com o M5.1 e os ajustes de tela antes da tela; a ordem das seções —
   risco → laboratório → retorno → Fundamentos → Comunicados — é a ordem das abas.
3. Pedir à `identidade` o `verbose_name` em `User.name` e `User.email` (a mensagem de semelhança da senha cita o campo em
   inglês).
4. Os achados da revisão da PR #37 (M3.3), registrados como dívida no [ESTADO](../ESTADO.md#dívida-registrada).

## Depois

O M2.2a (carteira) entrou na `main` pela PR #34: sem comercialização, o parecer da CVM não a segura
([D-160](../decisoes/D-160-sem-comercializacao-o-parecer-da-cvm-nao-segura-a-carteira-substitui-a-d-116-item-2.md)); o
M5.1 (retorno) segue a mesma decisão, registrada na
[D-192](../decisoes/D-192-a-tela-mostra-a-validacao-e-a-previsao-junto-dela-com-o-aviso-estende-a-d-160.md). A política de retenção dos retratos tem agora a primeira medida em
dia útil: o provento do BBDC4 de 2026-10-02 retreinou a linhagem inteira dele (72 retratos), e os outros cinco ativos não
gravaram nenhum (ver o fecho do M1.4b no ESTADO).

## O que esta frente deve a outras

| Para | O quê | Estado |
|---|---|---|
| `identidade` | convenções da API | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md), aplicada pelo M1.6a |
| `identidade` | casco do frontend e kit | ✅ o kit (M1.6a) e o casco (M1.6b) |
| `identidade` | a coluna `core.compute_request.requested_by` | ✅ M2.1m; o preenchimento é da T14 do M2.1a |
| `identidade` | as telas das rotas de conta | ✅ M2.1b, no ramo; a PR de implementação passa pela revisão dela (D-140) |

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84; a spec do M1.5b chega aprovada na revisão adversarial |
| 2026-09-26 | spec do M1.5b aprovada pelo dono da frente; plano escrito no ramo; D-85: o dono da frente mescla a própria PR |
| 2026-09-26 | plano do M1.5b aprovado; implementação começa pela T1 |
| 2026-09-27 | M1.5b fechado: T1 a T9, execução real, D-75 a D-81; a PR de implementação fica para o dono abrir |
| 2026-09-28 | M1.6a fechado: T1 a T14 e a T4b, a vitrine aprovada no portão, D-87 a D-93; a PR de implementação fica para o dono abrir |
| 2026-09-28 | M1.6a mesclado (PR #12). M1.6b aberto: telas com as camadas 1 a 3; as 4 e 5 vão para o M1.6c (D-95); 5.1 e 5.2 entram (D-96); frase fixa por número (D-97); 1 dia (D-98); três bibliotecas de gráfico comparadas com dado real, o uPlot escolhido (D-94) |
| 2026-09-29 | M1.6b fechado: T1 a T13, os três portões de mockup, D-94 a D-98; o AALR3 pedido pela tela e calculado em 100,8 s; a PR de implementação fica para o dono abrir |
| 2026-09-29 | M1.6b mesclado (PR #16). M1.6c fechado: T0 a T8, o mockup aprovado, D-99; as tabelas da `fundamentos` viraram contrato; a taxa do anônimo medida; a PR de implementação fica para o dono abrir |
| 2026-09-29 | M1.6c mesclado (PR #17) pelo dono da `fundamentos`, a frente que consome o contrato (D-99). M2.1m aberto: a coluna `core.compute_request.requested_by`; spec com duas rodadas de revisão, aprovada pelo dono; plano com uma |
| 2026-09-29 | M2.1m fechado: a T1 (`4825389`), 1218 testes no backend, as três mutações reprovando; a PR de implementação fica para o dono abrir |
| 2026-09-29 | M2.1m mesclado (PR #18). Seis blocos abertos em paralelo, cada um no seu worktree: M1.6d, M1.5c, M1.7, M3.3, M2.3 e M2.1b; specs revisadas e aprovadas no portão, planos revisados contra a spec; D-140, D-143, D-144 e D-146 a D-153; spec e plano em PR (#19 a #24). A dispensa de portão do login (a antiga D-141) foi retirada: o login ganha mockup derivado do `01-login` |
| 2026-09-30 | As seis PRs de spec e plano mescladas pelo dono (#19 a #24): os planos aprovados; a implementação começa pelo M1.6d |
| 2026-09-30 | M1.6d fechado: T1 a T4 (`218e26a`, `90638cb`, `6c98a15`, `d999e94`), as sete mutações reprovando duas vezes, 1099 testes no frontend e 1299 no backend; três dívidas pagas, e a do roteiro riscada como paga no M1.6c; a PR de implementação fica para o dono abrir |
| 2026-09-30 | M1.5c fechado: T1 a T8 (`15df430` a `f0ae2d2`), as onze mutações reprovando, 1330 testes no backend; na execução real, a presa (10 de 18) fechada `partial` pela tarefa, e as reservadas que voltaram 1 h depois descartadas; a PR de implementação fica para o dono abrir, com a revisão da `identidade` |
| 2026-10-01 | M1.5c mesclado (PR #30) |
| 2026-10-02 | M1.7 fechado: T0 a T8 (`1713174` a `ea0f35c`), o mockup da sugestão aprovado no portão, D-143 e D-144; as vinte mutações reprovando; na execução real, 258 conferências sem falha — a sugestão igual à primeira página de `has_risk=true`, "itaú" achando o `ITUB4`, o `PETR4` com vírgula; três dívidas do M1.6b pagas; a PR de implementação fica para o dono abrir, com a revisão da `fundamentos`. Na conferência do M2.3, duas entradas novas do motor em *Aberto* |
| 2026-10-02 | M1.7 mesclado (PR #32) |
| 2026-10-02 | M2.3 fechado: dezesseis tarefas, as quatro conferências técnicas e os quatro portões de mockup aprovados pelo dono, com três iniciantes emendadas (`comportamento.return_ytd`, `fundamentos.pares.abaixoDeTodas` e a D-64 pela expressão única); D-151 a D-153; as 39 mutações reprovando, 1206 testes no frontend, 631 conferências na execução real nos dois níveis; a PR de implementação fica para o dono abrir. O ramo recebeu a `main` com o M1.7 antes da PR |
| 2026-10-02 | M3.3 fechado: o mockup aprovado no portão sem ajuste; T5 (`442e984`) e T6 (`7d42e07`), as 22 mutações das T1 a T3 e da T6 reprovando de novo na T7; na execução real, o oráculo bateu nos oito conjuntos do IBOV e da PETR4, e o roteiro fechou com 642 conferências (a primeira rodada falhou só o tempo do RF-24, 3,5 s; a segunda, 1,5 s, sem falha); 1263 testes no frontend e 1747 no backend; a PR de implementação fica para o dono abrir |
| 2026-10-03 | M1.4b fechado: T0 a T7, com a revisão da implementação (T6b) antes da execução real; D-157 a D-159; o motor `0.4.0`; na execução real, na ordem do RF-13 — a referência `0.3.0` (execuções 89 a 94), a imagem nova, o trecho 0 recapturado (só o `garchnet` mudou), o recálculo `0.4.0` (95 a 100) —, o `lstm`, o `gru` e o `caviar` iguais campo a campo, os outros seis com o VaR mudado, e a zona de Basileia sem defeito no ITUB4; o primeiro build morreu por falta de memória e o checkout voltou à `main` até a imagem existir. O ramo recebeu a `main` com o M2.2a, o M3.3 (PR #37) e a D-160 antes da execução real. 1747 testes no backend, 152 no motor, 25 na linha de base, 1265 no frontend; a PR, com spec, plano e implementação, a abrir |
| 2026-10-03 | M1.4b mesclado (PR #38). M2.1b fechado: dezesseis tarefas, os cinco portões de mockup aprovados pelo dono (o menu de conta por último na barra, a barra estreita até 840 px, "Administração"); o `POST /risk` exige conta (D-140); 1621 testes no frontend e 1753 no backend — 1 falha, o caso anônimo do `test_requested_by.py`, que a `identidade` ajusta; na execução real, o `acesso.mjs` com 133 conferências e 36 comparações com os mockups sem diferença, na segunda rodada (a primeira achou o diálogo que reabria antes do `close` do navegador, corrigido em `45a06c5`), e o `capturas.mjs` com 644; a PR de implementação fica para o dono abrir, depois do ajuste da `identidade` |
| 2026-10-04 | M5.1 retomado pelo Kauã, na máquina dele: a `main` com o M2.4 recebida, os ajustes do mockup, T10 a T13, a correção do V-09 instável do laboratório, a fase A refeita (os 108 pares iguais, o oráculo a 4,98e-11), a fase B (558 conferências, 0 falhas) e o FECHA |
| 2026-10-04 | PR #41 (M5.1) mesclada. Ajustes de tela pelo Kauã, no ramo `marco1/ajustes-de-tela`, vistos no navegador e aprovados na conversa: as seis abas com endereço (D-193), o botão Explicações e o detalhe recolhido (D-194), a página inicial centrada, o tema escuro em carvão quente (D-195); 1830 testes no frontend; o `capturas.mjs` não rodado, a rever |
| 2026-10-05 | PR #42 (ajustes de tela) mesclada. Documentos postos no estado atual: nenhuma PR aberta na frente; o M2.2b segue no ramo dele |
