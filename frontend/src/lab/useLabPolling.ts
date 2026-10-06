/**
 * A releitura limitada do `/lab` (M2.4, RF-18): **uma janela de 2 minutos abre quando
 * `reloadToken` muda** — o `reloadAll` que o fim do acompanhamento do risco chama
 * (`risk/usePolling.ts`) —, e não na montagem. Dentro da janela, com o `/lab` recebido e
 * `pending` verdadeiro, o `/lab` é pedido de novo `POLL_INTERVAL_MS` depois de cada resposta.
 * Para no primeiro `latest` ou `last_failure` **novo** — de `id` diferente do que havia quando a
 * janela abriu (RF-18 da spec; o plano dizia "não nulos", e vale a spec: com o `latest` de outra
 * versão do motor já presente, a releitura segue até chegar o experimento novo) —, ao fim dos
 * 120 000 ms e ao desmontar; a aba oculta suspende, e voltar a ficar visível pede na hora (o molde de
 * `usePolling`).
 */

import { useEffect, useRef, useState } from "react";

import type { Lab } from "../api/types";
import { POLL_INTERVAL_MS } from "../risk/usePolling";

/** A duração da janela de releitura, a partir da mudança de `reloadToken`. */
export const LAB_POLL_WINDOW_MS = 120_000;

/** Os `id` do `latest` e do `last_failure` de um `/lab` (nulos sem eles, ou sem `/lab`). */
type Seen = { latestId: number | null; failureId: number | null };

function seen(lab: Lab | null): Seen {
  return {
    latestId: lab?.latest?.id ?? null,
    failureId: lab?.last_failure?.id ?? null,
  };
}

/** Há `latest` ou `last_failure` de `id` diferente do visto quando a janela abriu. */
function isNew(lab: Lab, before: Seen): boolean {
  return (
    (lab.latest !== null && lab.latest.id !== before.latestId) ||
    (lab.last_failure !== null && lab.last_failure.id !== before.failureId)
  );
}

/**
 * `lab` é o último `/lab` recebido (nulo enquanto a primeira carga não chegou, ou com a rota em
 * erro); `reloadLab` pede o `/lab` de novo; `reloadToken` é o da tela (`useAssetData`).
 */
export function useLabPolling(
  lab: Lab | null,
  reloadLab: () => void,
  reloadToken: number,
): void {
  // A janela aberta guarda os `id` do `latest` e do `last_failure` de quando abriu; fechada, nula.
  const [opened, setOpened] = useState<Seen | null>(null);
  const windowOpen = opened !== null;

  // O último `/lab` recebido, para a janela ler ao abrir sem depender dele.
  const latestLab = useRef(lab);
  latestLab.current = lab;

  // A janela: abre a cada mudança de `reloadToken` depois da montagem, e fecha em 2 minutos.
  const mountedToken = useRef(reloadToken);
  useEffect(() => {
    if (reloadToken === mountedToken.current) return;
    setOpened(seen(latestLab.current));
    const timer = setTimeout(() => setOpened(null), LAB_POLL_WINDOW_MS);
    return () => clearTimeout(timer);
  }, [reloadToken]);

  // O experimento novo chegou (ou uma falha nova): a janela fecha.
  const arrived = opened !== null && lab !== null && isNew(lab, opened);
  useEffect(() => {
    if (arrived) setOpened(null);
  }, [arrived]);

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
