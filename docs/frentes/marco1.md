# Frente `marco1`

**Dono:** darkside171
**Blocos:** M1.5b ✅ → M1.6a ✅ → M1.6b ✅ → M1.6c ✅ → M2.1m ✅; com spec e plano aprovados e na `main`, seis blocos em paralelo — M1.6d,
M1.5c, M1.7, M3.3, M2.3 e M2.1b. O M1.6b fechou o Marco 1: digita ITUB4, recebe o comportamento e o risco; o M1.6c
completou a tela com as camadas 4 e 5.
**Cerca:** ver [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-75 a D-81 (todas usadas pelo M1.5b), depois D-85 a D-99 (todas usadas; a D-99 é do M1.6c) e
D-140 a D-159, reservadas pela spec do M1.6c e divididas entre os seis blocos abertos em 2026-09-29 — usadas D-140,
D-143 e D-144, D-146 a D-153 (ver [FRENTES.md](../FRENTES.md#numeração-de-decisão)).

---

## Agora

**Seis blocos com spec e plano aprovados e na `main`** (PRs #19 a #24, mescladas em 2026-09-30); a implementação começa. Cada ramo tem o seu worktree em
`E:/Temp/Trilobit/varlab-wt/<bloco>`; spec e plano entram juntos, num commit, e a PR mesclada pelo dono foi o portão
dos dois; a implementação de cada bloco sai do mesmo ramo, numa PR própria. Todas as specs passaram por revisão adversarial (a do M1.6d, inline) e foram aprovadas pelo dono; todos
os planos passaram por revisão contra a spec, alguns em duas ou três rodadas.

| Bloco | Ramo | PR | Tarefas | Portões de mockup | Revisão de outra frente |
|---|---|---|---|---|---|
| [M1.6d — Acabamento](../specs/M1.6d-acabamento.md) | `marco1/M1.6d-acabamento` | #19 | 6 | — | — |
| [M1.5c — Execução presa](../specs/M1.5c-execucao-presa.md) | `marco1/M1.5c-execucao-presa` | #23 | 10 | — | `identidade` (cruza com a T14 do M2.1a) |
| [M1.7 — Busca e catálogo](../specs/M1.7-busca-e-catalogo.md) | `marco1/M1.7-busca-e-catalogo` | #21 | 9 | 1 | `fundamentos` (o grupo de pares com vírgula) |
| [M3.3 — Estresse histórico](../specs/M3.3-estresse-historico.md) | `marco1/M3.3-estresse-historico` | #20 | 9 | 1 | — |
| [M2.3 — Camada explicativa](../specs/M2.3-camada-explicativa.md) | `marco1/M2.3-camada-explicativa` | #22 | 16 | 4 | — (estende a cerca de mockups da `marco1`) |
| [M2.1b — Telas de acesso](../specs/M2.1b-telas-de-acesso.md) | `marco1/M2.1b-telas-de-acesso` | #24 | 16 | 5 | `identidade` (o `POST /risk` exige conta, D-140) |

**Ordem de merge proposta:** #19 → #23 → #21 → #20 → #22 → #24. O M2.3 depende do M1.6d mesclado; o M2.1b espera
combinar com a `identidade` a ordem com a T14 do M2.1a, cujo teste de pedido anônimo passa a esperar 401.

**Como a implementação roda** (regra escrita em todos os planos): testes em contêiner avulso com o worktree montado,
uma suíte de backend por vez na máquina (o banco de teste é um só); quando um bloco precisa do stack servindo o
ramo — mockup com dado real, tela, execução real —, o orquestrador põe o checkout principal em
`git switch --detach <HEAD do ramo>`, com ele livre, e o devolve no fim; parar e subir o Beat é do orquestrador.

## Próximo passo

1. Implementar, bloco a bloco na ordem acima — o M1.6d primeiro —, cada ramo recebendo a `main` antes de começar,
   com os portões de mockup de cada um.
2. Combinar com a `identidade` a ordem entre o M2.1b e a T14 do M2.1a.
3. Olhar a zona de Basileia a 5% (ver *Aberto* no [ESTADO](../ESTADO.md#aberto-e-aguardando-decisão)).

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
