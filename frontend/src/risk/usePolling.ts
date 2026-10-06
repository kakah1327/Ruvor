/**
 * A consulta repetida (RF-20 do M1.6a; genérica desde o M2.2b, RF-17 e D-182): enquanto
 * `shouldPoll(value)` for verdadeiro, `reload` é chamado **5 s** depois de cada resposta; a aba
 * oculta suspende, e voltar a ficar visível pede na hora; desmontar cancela. **Quando
 * `shouldPoll` passa de verdadeiro a falso**, com um valor recebido, `onEnd()`.
 *
 * - **O ativo** passa o `/risk`, o `shouldPoll` de `risk/state.ts`, a releitura do `/risk` e,
 *   em `onEnd`, a recarga das rotas — a cadeia sob demanda pode ter coletado preço e calculado
 *   métricas mesmo quando o risco não fecha `ok`. Sem `attempt`: um `/risk` em erro (`value`
 *   nulo) para a consulta, e o "tentar de novo" da seção a retoma.
 * - **A carteira** passa o `attempt` da fonte (`portfolio/useRiskSource.ts`): um erro numa
 *   releitura mantém o `value` e sobe o `attempt`, e a consulta segue.
 */

import { useEffect, useRef } from "react";

/** O intervalo entre uma leitura e a próxima, enquanto há o que acompanhar. */
export const POLL_INTERVAL_MS = 5000;

/**
 * `value` é o último corpo recebido (nulo enquanto a primeira leitura não chegou, ou com a rota
 * em erro, no ativo); `reload` pede de novo; `onEnd` roda no fim do acompanhamento; `attempt`,
 * quando vem, sobe a cada resposta — inclusive a de erro, que mantém o `value`.
 *
 * Cada resposta é um `value` novo ou um `attempt` novo: o efeito recomeça e agenda o próximo
 * pedido a partir dela. `shouldPoll`, `reload` e `onEnd` precisam ser estáveis.
 */
export function usePolling<T>(
  value: T | null,
  shouldPoll: (v: T) => boolean,
  reload: () => void,
  onEnd: () => void,
  attempt?: number,
): void {
  const active = value !== null && shouldPoll(value);

  // O pedido seguinte, 5 s depois de cada resposta, só com a aba visível.
  // biome-ignore lint/correctness/useExhaustiveDependencies: `attempt` não é lido; mudar de valor é o que reagenda o pedido.
  useEffect(() => {
    if (value === null || !shouldPoll(value)) return;

    let timer: ReturnType<typeof setTimeout> | undefined;
    const schedule = () => {
      clearTimeout(timer);
      timer = undefined;
      if (document.visibilityState === "hidden") return;
      timer = setTimeout(reload, POLL_INTERVAL_MS);
    };
    const onVisibility = () => {
      if (document.visibilityState === "hidden") {
        clearTimeout(timer);
        timer = undefined;
      } else {
        // Voltou: pede na hora; a resposta agenda o próximo.
        clearTimeout(timer);
        timer = undefined;
        reload();
      }
    };

    schedule();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [value, shouldPoll, reload, attempt]);

  // O fim do acompanhamento: de verdadeiro a falso, com um valor recebido.
  const wasActive = useRef(false);
  useEffect(() => {
    if (value === null) return;
    if (wasActive.current && !active) onEnd();
    wasActive.current = active;
  }, [value, active, onEnd]);
}
