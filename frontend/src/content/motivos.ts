/**
 * A tradução dos motivos do pedido sob demanda (RF-18). A API manda o motivo sem acento, da
 * lista fechada de `backend/apps/api/ondemand.py`; a tela nunca mostra o texto cru.
 *
 * O contrato é fixado dos dois lados: `backend/tests/api/test_motivos.py` confere a lista
 * produzida pelo backend, e `frontend/tests/motivos.test.ts` confere esta tradução contra a
 * mesma lista, escrita no teste. Os textos são os `motivos.*` de `textos.ts`, do
 * `ativo-estados.html` aprovado (T4); a lógica é a do `traduzirMotivo` de lá.
 */

import { formatInteger } from "../format/numbers";
import { TEXTOS } from "./textos";

/** A lista fechada do RF-18; `N` é o número que o motivo traz. */
export const MOTIVOS_CONHECIDOS = [
  "calculado",
  "serie curta (N pregoes, minimo 503)",
  "falhou na coleta",
  "falhou nas metricas",
  "falhou na abertura",
  "a execucao falhou",
  "o broker recusou o pedido",
  "expirado (N min)",
] as const;

// Os seis sem número, por igualdade.
const MOTIVO_FIXO: ReadonlyMap<string, string> = new Map([
  ["calculado", TEXTOS["motivos.calculado"]],
  ["falhou na coleta", TEXTOS["motivos.falhouColeta"]],
  ["falhou nas metricas", TEXTOS["motivos.falhouMetricas"]],
  ["falhou na abertura", TEXTOS["motivos.falhouAbertura"]],
  ["a execucao falhou", TEXTOS["motivos.execucaoFalhou"]],
  ["o broker recusou o pedido", TEXTOS["motivos.brokerRecusou"]],
]);

const SERIE_CURTA = /^serie curta \((\d+) pregoes, minimo (\d+)\)$/;
const EXPIRADO = /^expirado \((\d+) min\)$/;

/** O motivo cru da API como frase; um motivo desconhecido cai na frase genérica. */
export function traduzirMotivo(reason: string): string {
  const fixo = MOTIVO_FIXO.get(reason);
  if (fixo !== undefined) return fixo;
  let match = SERIE_CURTA.exec(reason);
  if (match !== null) {
    return TEXTOS["motivos.serieCurta"](
      formatInteger(Number(match[1])),
      formatInteger(Number(match[2])),
    );
  }
  match = EXPIRADO.exec(reason);
  if (match !== null) {
    return TEXTOS["motivos.expirado"](formatInteger(Number(match[1])));
  }
  return TEXTOS["motivos.desconhecido"](reason);
}
