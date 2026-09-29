/**
 * O acompanhamento (RF-20): enquanto `shouldPoll` for verdadeiro, o `/risk` é pedido de novo
 * **5 s** depois de cada resposta; a aba oculta suspende, e voltar a ficar visível pede na
 * hora; desmontar cancela. **Quando `shouldPoll` passa de verdadeiro a falso** — o cálculo
 * terminou, em qualquer estado de chegada —, a tela recarrega as cinco rotas: a cadeia sob
 * demanda pode ter coletado preço e calculado métricas mesmo quando o risco não fecha `ok`.
 */

import { useEffect, useRef } from "react";

import type { Risk } from "../api/types";
import { shouldPoll } from "./state";

/** O intervalo entre um `/risk` e o próximo, enquanto há o que acompanhar. */
export const POLL_INTERVAL_MS = 5000;

/**
 * `risk` é o último `/risk` recebido (nulo enquanto a primeira carga não chegou, ou com a
 * rota em erro); `reloadRisk` pede o `/risk` de novo; `reloadAll`, as cinco rotas.
 *
 * Cada `/risk` novo é um objeto novo: o efeito recomeça e agenda o próximo pedido a partir
 * dele. Um `/risk` em erro não conta como fim do acompanhamento — o "tentar de novo" da
 * seção o retoma.
 */
export function usePolling(
  risk: Risk | null,
  reloadRisk: () => void,
  reloadAll: () => void,
): void {
  const active = risk !== null && shouldPoll(risk);

  // O pedido seguinte, 5 s depois de cada resposta, só com a aba visível.
  useEffect(() => {
    if (risk === null || !shouldPoll(risk)) return;

    let timer: ReturnType<typeof setTimeout> | undefined;
    const schedule = () => {
      clearTimeout(timer);
      timer = undefined;
      if (document.visibilityState === "hidden") return;
      timer = setTimeout(reloadRisk, POLL_INTERVAL_MS);
    };
    const onVisibility = () => {
      if (document.visibilityState === "hidden") {
        clearTimeout(timer);
        timer = undefined;
      } else {
        // Voltou: pede na hora; a resposta agenda o próximo.
        clearTimeout(timer);
        timer = undefined;
        reloadRisk();
      }
    };

    schedule();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [risk, reloadRisk]);

  // O fim do acompanhamento: de verdadeiro a falso, com um `/risk` recebido.
  const wasActive = useRef(false);
  useEffect(() => {
    if (risk === null) return;
    if (wasActive.current && !active) reloadAll();
    wasActive.current = active;
  }, [risk, active, reloadAll]);
}
