# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b ✅ → M1.6c ✅ → M2.1m ✅ → M1.6d ✅ → M1.5c ✅ → M1.7 ✅ → M2.3 ✅ → M3.3 ✅; com
spec e plano aprovados e na `main`, um bloco a implementar — o M2.1b. O M1.6b fechou o Marco 1: digita ITUB4, recebe o
comportamento e o risco; o M1.6c completou a tela com as camadas 4 e 5; o M2.3 deu a ela as duas leituras, iniciante e
avançada; o M3.3, o estresse histórico na seção Comportamento.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 (todas usadas; a D-99 é do M1.6c) e
D-140 a D-159, reservadas pela spec do M1.6c e divididas entre os seis blocos abertos em 2026-09-29 — usadas D-140,
D-143 e D-144, D-146 a D-153 — a D-146 a D-148 com o M3.3, fechado; a D-143 e a D-144 com o M1.7, fechado (a D-145 fica sem uso); a D-149 e a D-150 com o
M1.5c, fechado; a D-151 a D-153 com o M2.3, fechado, e a D-154 sem uso (ver
[FRENTES.md](../FRENTES.md#numeração-de-decisão)).

---

## Agora

**Seis blocos com spec e plano aprovados e na `main`** (PRs #19 a #24, mescladas em 2026-09-30); o **M1.6d fechou em 2026-09-30** (PR #27), o **M1.5c em 2026-09-30** (PR #30, mesclada em 2026-10-01) e o
**M1.7 em 2026-10-02** (PR #32, mesclada no mesmo dia); o **M2.3 fechou em 2026-10-02** (PR #33); o **M3.3 fechou em 2026-10-02**, a T5 em diante noutra máquina, com o ramo no checkout principal, e a PR de implementação a abrir; o M2.1b espera a vez. Cada ramo tem o seu worktree em
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
| [M2.1b — Telas de acesso](../specs/M2.1b-telas-de-acesso.md) | `marco1/M2.1b-telas-de-acesso` | #24 | 16 | 5 | `identidade` (o `POST /risk` exige conta, D-140) |

**Ordem de merge das PRs de spec e plano (cumprida):** #19 → #23 → #21 → #20 → #22 → #24. A implementação segue M1.7 → M2.3 → M3.3 → M2.1b. O M2.3 depende do M1.6d mesclado; o M2.1b espera
combinar com a `identidade` a ordem com a T14 do M2.1a, cujo teste de pedido anônimo passa a esperar 401.

**Como a implementação roda** (regra escrita em todos os planos): testes em contêiner avulso com o worktree montado,
uma suíte de backend por vez na máquina (o banco de teste é um só); quando um bloco precisa do stack servindo o
ramo — mockup com dado real, tela, execução real —, o orquestrador põe o checkout principal em
`git switch --detach <HEAD do ramo>`, com ele livre, e o devolve no fim; parar e subir o Beat é do orquestrador.

## Próximo passo

1. **Abrir a PR do M3.3** (implementação, T5 a T8) e mesclá-la com a CI verde. O M2.3 entrou pela PR #33, e o ramo do
   M3.3 já nasceu da `main` com ele: as seis medidas novas têm a frase avançada e entraram na lista fechada do V-02 (61).
2. **Implementar o M2.1b**, com os seus portões de mockup, recebendo a `main` antes de começar; o menu de conta, se
   entrar em `.ruvor-topbar__prefs`, refaz os seletores por posição da T4 do M2.3.
3. Combinar com a `identidade` a ordem entre o M2.1b e a T14 do M2.1a.
4. Olhar a zona de Basileia a 5%, junto com as duas entradas do motor achadas na conferência do M2.3 — o GARCH e o
   EGARCH olham um dia à frente, e os tradicionais ficam no primeiro ano da série (ver *Aberto* no
   [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão)).

## Depois

Os blocos que dependem de decisão externa: M2.2 (carteira) e M5.1 (retorno) esperam o parecer sobre a fronteira da
CVM; a política de retenção dos retratos espera a taxa de invalidação medida em dia útil.

## O que esta frente deve a outras

| Para | O quê | Estado |
|---|---|---|
| `identidade` | convenções da API | ✅ [D-86](../decisoes/D-86-convencoes-da-api-http.md), aplicada pelo M1.6a |
| `identidade` | casco do frontend e kit | ✅ o kit (M1.6a) e o casco (M1.6b) |
| `identidade` | a coluna `core.compute_request.requested_by` | ✅ M2.1m; o preenchimento é da T14 do M2.1a |

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
