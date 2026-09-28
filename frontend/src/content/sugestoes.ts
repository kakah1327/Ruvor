/**
 * As sugestões da página inicial e o mínimo de pregões do cálculo de risco.
 *
 * MIN_SESSIONS é cópia de `MIN_SESSIONS` em backend/apps/risk/config.py; o teste de
 * contrato dos motivos o fixa dos dois lados (RF-17, RF-18).
 */

export const SUGESTOES = ["ITUB4", "PETR4", "VALE3", "BBDC4", "IBOV"] as const;

export const MIN_SESSIONS = 503;
