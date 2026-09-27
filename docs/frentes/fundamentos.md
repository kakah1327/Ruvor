# Frente `fundamentos`

**Dono:** kakah1327 (Kauã)
**Blocos:** M3.1 — Fundamentos ✅ (camada 4) → M3.2 — Contexto ✅ (camada 5)
([ROADMAP](../ROADMAP.md#marco-3--tudo-sobre-a-ação-completo)).
**Cerca:** a app `apps/fundamentals`, os testes dela e as tabelas novas em `bronze`, `silver` e
`gold`, da própria app. Detalhe em [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-120 a D-139.

---

## Agora

**Bloco:** M3.2 — Contexto (camada 5: comunicados da companhia à CVM e comparação com os pares)
**Etapa:** **fechado** em 2026-09-27 — implementação, revisão final (aprovou) e FECHA; falta a PR de implementação
**Ramo:** `fundamentos/M3.2-contexto`, criado em 2026-09-27 a partir da `main` com o M3.1 mesclado (PR #5)

## Próximo passo

1. A PR de implementação do M3.2, que passa pela `marco1` (o serviço `beat`,
   `tests/risk/test_beat.py`, os comentários das tarefas e o override do `pyproject.toml`); o
   merge é do dono da frente, com a CI verde (D-85).
2. Depois do merge, o próximo bloco da frente, que não está definido: o Marco 3 não tem outro. A
   escolha é do dono.

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
| 2026-09-27 | implementação T1 a T11, dezenove commits. A T11 reprovou a V-08 (ITR e DFP na mesma data) → RF-13b e T11b, vale o DFP; carga refeita do zero, 4 min 43 s, 339 companhias, V-13 igual à divulgação de PETR4, VALE3 e ITUB4. Revisão final: a primeira reprovou (lucro só na mãe saía 0) → RF-08b e T11c, vale a mãe; a segunda **aprovou**. **Bloco fechado**, D-120 a D-129 |
| 2026-09-27 | M3.1 mesclado (PR #5, revisado pela `marco1`). M3.2 escolhido; decidido com o dono: notícias pelo IPE da CVM, pares pelo segmento com recuo para o subsetor, comparação pelos fundamentos do M3.1, coleta diária em entrada própria do Beat |
| 2026-09-27 | auto-revisão da spec do M3.2: o IPE vazava para os índices do M3.1 (`_current_versions` sem filtro; `cvm_url` recusava `ipe`) → RF-02b; a comparação não cabia na transação do indicador → duas fases (RF-10, RF-15); vinte e sete tabelas, não vinte e seis. Decidido com o dono: **a dívida de tipos do Celery se paga no M3.2** (RF-20, D-134), medida no `worker` com `celery-types` 0.26.0. |
| 2026-09-27 | revisão adversarial 1 **reprovou** (3 graves: grupo de pares pelo nome, que se repete entre setores; o que a coleta conforma; reapresentações acumulando na `silver`; 4 médios, 8 leves). Decidido com o dono: pares pela tupla (setor, subsetor, segmento), 12 companhias sem grupo hoje; a coleta conforma os anos novos e o histórico inteiro da companhia nova; a versão superada sai da `silver`. Tudo absorvido (RF-04a, RF-04b, RF-07b, RF-11, RF-15) |
| 2026-09-27 | revisão adversarial 2 **aprovou** (0 graves, 3 médios, 3 leves). Absorvidos: o RF-04b media links divergentes que a fonte não traz (são todos idênticos); o RF-07b ganhou ordem, exclusão dos anos de (a) e o rótulo `novas {A}`; o conjunto do RF-04a passou a ser o conformado, e link que muda de companhia é atualizado; a mensagem do `CommandError` entra no inventário. Spec pronta para a PR |
| 2026-09-27 | PR #6 da spec aberta. Plano escrito, doze tarefas (T1 os tipos do Celery, antes de tudo; T11 as 26 mutações; T12 a execução real); o formato do IPE conferido no zip de 2026 (datas ISO, latin-1, `
`). |
| 2026-09-27 | revisão do plano: a 1 **reprovou** (1 grave: a remoção do RF-04a dependia da ordem das companhias → `year_links`, o conjunto conformado do ano inteiro; 7 médios, quase todos mutações que o critério não pegava); a 2 **aprovou** (0 graves, 0 médios, 3 leves, absorvidos). Plano pronto para a PR |
| 2026-09-27 | PR #6 (spec) mesclada pelo dono da frente, sem revisão da `marco1` registrada na PR. PR do plano aberta |
| 2026-09-27 | M3.2: spec e plano mesclados (PRs #6 e #7). Implementação T1 a T12, um commit por tarefa. As 26 mutações da T11 reprovam, todas com código 1. V-05 a V-10 conferem. A carga real do IPE levou 118 s, com pico de ~152 MiB, e gravou 80.900 comunicados de 339 companhias. Os 80.842 da spec contavam pares (protocolo, versão) distintos; a conta por link soma os 58 pares repetidos. Na comparação, 471 ações: 390 por segmento, 64 por subsetor e 17 sem grupo (12 companhias, como medido). Suíte com 622 testes |
| 2026-09-27 | M3.2: revisão final **aprovou** numa rodada (0 graves, 0 médios, 3 leves, registrados no ESTADO). FECHA: ESTADO, ROADMAP, índices, `CLAUDE.md`, `aprendizados.md` e D-130 a D-134. **Bloco fechado** |
