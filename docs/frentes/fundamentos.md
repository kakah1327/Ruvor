# Frente `fundamentos`

**Dono:** kakah1327 (Kauã)
**Bloco:** M3.1 — Fundamentos: a camada 4, com fonte adequada para a B3
([ROADMAP](../ROADMAP.md#marco-3--tudo-sobre-a-ação-completo)).
**Cerca:** uma app nova em `backend/apps/`, os testes dela e as tabelas novas em `bronze` e
`silver`. Detalhe em [FRENTES.md](../FRENTES.md#cercas).
**Faixa de decisões:** D-120 a D-139.

---

## Agora

**Etapa:** não começou
**Ramo:** `fundamentos/M3.1-fundamentos`, ainda não criado

## Próximo passo

1. Ler, nesta ordem: [`CLAUDE.md`](../../CLAUDE.md), [`PROCESSO.md`](../PROCESSO.md),
   [`aprendizados.md`](../aprendizados.md) e [`FRENTES.md`](../FRENTES.md).
2. Preparar a máquina e provar que ela funciona, antes de qualquer código. O único
   pré-requisito é o Docker com `compose`; o detalhe está no [`README`](../../README.md#executar).

   ```bash
   cp .env.example .env
   docker compose up -d --build --wait
   docker compose exec -T worker python manage.py migrate
   docker compose exec -T worker pytest tests
   ```

   A suíte tem de passar inteira **no `worker`**. No hospedeiro ela reprova de propósito — o
   README explica por quê. A primeira construção demora: a imagem do `worker` passa de 3 GB,
   por causa do TensorFlow. O `.venv/` nativo só serve ao motor, que está fora desta frente.
3. Criar o ramo a partir da `main`.
4. **Escrever a spec do M3.1**, conversando com o dono da frente. **A primeira pergunta é a
   fonte:** o Yahoo não serve para fundamentos da B3, e nenhuma fonte está escolhida. Vira
   decisão da faixa desta frente, com o porquê.

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
