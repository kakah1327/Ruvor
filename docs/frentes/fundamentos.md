# Frente `fundamentos`

**Dono:** kakah1327 (Kauã)
**Bloco:** M3.1 — Fundamentos: a camada 4, com fonte adequada para a B3
([ROADMAP](../ROADMAP.md#marco-3--tudo-sobre-a-ação-completo)).
**Cerca:** uma app nova em `backend/apps/`, os testes dela e as tabelas novas em `bronze` e
`silver`. Detalhe em [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-120 a D-139.

---

## Agora

**Etapa:** spec aprovada (PR #2, mesclada em 2026-09-26); plano aprovado na quinta revisão contra
a spec — [`planos/M3.1-fundamentos.md`](../planos/M3.1-fundamentos.md); falta o portão do plano
(a PR dele, que leva também duas correções da spec vindas da revisão do plano)
**Ramo:** `fundamentos/M3.1-fundamentos`, criado em 2026-09-26
**Máquina:** pronta — Docker Desktop instalado, seis serviços `healthy`, `migrate` aplicado,
`pytest tests` no `worker` com 304 passando (2026-09-26)

## Próximo passo

1. **Portão do plano:** merge da PR do plano pelo dono da frente, com a CI verde
   ([D-85](../decisoes/D-85-o-dono-da-frente-aprova-a-propria-pr.md)).
2. **Implementação**, tarefa a tarefa, T1 a T11 do plano, um commit por tarefa neste ramo. A PR de
   implementação passa também pela `marco1` (serviço `beat` e `tests/risk/test_beat.py`).
3. A T2 baixa de novo os zips da CVM para recortar as fixtures: os CSVs medidos na spec não foram
   guardados.

## O que a spec do M3.1 encontra pronta, e precisa ler

- **A ingestão já tem modelo, e é para copiar.** O M1.1 (catálogo) e o M1.2 (preços) fizeram o
  mesmo caminho: payload bruto imutável em `bronze`, dado conformado em `silver`, transação por
  ativo. Specs em [`specs/M1.1-catalogo-de-ativos.md`](../specs/M1.1-catalogo-de-ativos.md) e
  [`specs/M1.2-ingestao-de-precos.md`](../specs/M1.2-ingestao-de-precos.md); decisões
  [D-13](../decisoes/D-13-camadas-bronze-prata-ouro.md),
  [D-47](../decisoes/D-47-fonte-do-catalogo-e-o-site-da-b3.md) e
  [D-48](../decisoes/D-48-catalogo-em-silver-por-ticker-atualizado-por-coleta.md) a
  [D-54](../decisoes/D-54-transacao-por-ativo-restringe-a-d-48.md).
- **O fundamento se liga ao ativo por `silver.asset`**, o catálogo por ticker. A tabela é da
  frente `marco1` ([contrato](../FRENTES.md#contratos-entre-frentes)): ler pode, mudar exige a
  revisão dela.
- **Uma pendência já cai neste bloco:** a capitalização de mercado ficou fora do M1.3 por não
  ter fonte, e foi registrada como do M3.1 ([ROADMAP](../ROADMAP.md#marco-1--a-ação-e-o-risco-dela)).
- **A coleta agendada entra pelo Beat**, com uma entrada própria no `CELERY_BEAT_SCHEDULE`, que é
  arquivo comum. O modelo é `apps/assets/tasks.py` e o M1.5
  ([D-69](../decisoes/D-69-o-agendamento-e-encadeado.md)). A dívida de tipos das tarefas
  Celery vence no "próximo bloco que criar uma leva de tarefas" ([ESTADO](../ESTADO.md#dívida-registrada)):
  se for este, a spec precisa dizer.
- **Os testes não saem para a rede**: há uma guarda na suíte (`backend/tests/test_guarda_de_rede.py`).
  A coleta real se prova à mão, como no M1.1 e no M1.2.

## O que esta frente espera de outras

Nada para começar. A tela dos fundamentos virá depois do casco do M1.6, e é de outro bloco.

## Registro

| Data | O que aconteceu |
|---|---|
| 2026-09-26 | frente criada pela D-84 |
| 2026-09-26 | fonte escolhida com o dono: dados abertos da CVM. Escopo: catálogo inteiro, 10 anos, até `gold`, bancos entram (lucro, PL, ROE e múltiplos valem; receita, margens e dívida nulas pelo plano), capitalização por classe, `bronze` com o zip inteiro. Spec escrita; a medição achou a escala das ações variando por companhia |
| 2026-09-26 | máquina preparada (304 testes no `worker`). Revisão adversarial 1 reprovou: 4 graves, 15 médios, 10 leves, todos absorvidos. Decidido com o dono: a dívida bruta inclui arrendamento; exercício não civil tem regra genérica; a dívida de tipos do Celery não se paga no M3.1 |
| 2026-09-26 | spec mesclada (PR #2). Plano escrito; cinco revisões contra a spec, as quatro primeiras reprovaram (T11 que não reprovava, companhia nova sem histórico, mutações sem teste), a quinta **aprovou**. Duas correções da spec vieram dessa revisão |
| 2026-09-26 | revisão 2 reprovou (3 graves: contas de bancos forma A e seguradoras, motivos da capitalização, units); revisão 3 **aprovou** (0 graves, 3 médios, 9 leves). Tudo absorvido. Spec pronta para a PR |
