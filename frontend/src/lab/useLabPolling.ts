/**
 * A releitura limitada do `/lab` (M2.4, RF-18): **uma janela de 2 minutos abre quando
 * `reloadToken` muda** — o `reloadAll` que o fim do acompanhamento do risco chama
 * (`risk/usePolling.ts`) —, e não na montagem. Dentro da janela, com o `/lab` recebido e
 * `pending` verdadeiro, o `/lab` é pedido de novo `POLL_INTERVAL_MS` depois de cada resposta.
 * Para no primeiro `/lab` com `latest` ou `last_failure` não nulos, ao fim dos 120 000 ms e ao
 * desmontar; a aba oculta suspende, e voltar a ficar visível pede na hora (o molde de
 * `usePolling`).
 */

import { useEffect, useRef, useState } from "react";

import type { Lab } from "../api/types";
import { POLL_INTERVAL_MS } from "../risk/usePolling";

/** A duração da janela de releitura, a partir da mudança de `reloadToken`. */
export const LAB_POLL_WINDOW_MS = 120_000;

/**
 * `lab` é o último `/lab` recebido (nulo enquanto a primeira carga não chegou, ou com a rota em
 * erro); `reloadLab` pede o `/lab` de novo; `reloadToken` é o da tela (`useAssetData`).
 */
export function useLabPolling(
  lab: Lab | null,
  reloadLab: () => void,
  reloadToken: number,
): void {
  const [windowOpen, setWindowOpen] = useState(false);

  // A janela: abre a cada mudança de `reloadToken` depois da montagem, e fecha em 2 minutos.
  const mountedToken = useRef(reloadToken);
  useEffect(() => {
    if (reloadToken === mountedToken.current) return;
    setWindowOpen(true);
    const timer = setTimeout(() => setWindowOpen(false), LAB_POLL_WINDOW_MS);
    return () => clearTimeout(timer);
  }, [reloadToken]);

  // O experimento chegou (ou a falha dele): a janela fecha.
  const arrived = lab !== null && (lab.latest !== null || lab.last_failure !== null);
  useEffect(() => {
    if (windowOpen && arrived) setWindowOpen(false);
  }, [windowOpen, arrived]);

  // O pedido seguinte, `POLL_INTERVAL_MS` depois de cada resposta, só com a aba visível.
  useEffect(() => {
    if (!windowOpen || lab === null || !lab.pending || arrived) return;

    let timer: ReturnType<typeof setTimeout> | undefined;
    const schedule = () => {
      clearTimeout(timer);
      timer = undefined;
      if (document.visibilityState === "hidden") return;
      timer = setTimeout(reloadLab, POLL_INTERVAL_MS);
    };
    const onVisibility = () => {
      clearTimeout(timer);
      timer = undefined;
      // Voltou: pede na hora; a resposta agenda o próximo.
      if (document.visibilityState !== "hidden") reloadLab();
    };

    schedule();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [windowOpen, lab, arrived, reloadLab]);
}
