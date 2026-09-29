/**
 * Uma rota da API como estado de tela (RF-06): cada seção da tela do ativo carrega sozinha,
 * com carregando, erro próprio e "tentar de novo".
 */

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiGet } from "./client";

/** A situação de uma rota: carregando, com erro (o `ApiError` do cliente) ou com o dado. */
export type Load<T> =
  | { state: "loading" }
  | { state: "error"; error: ApiError }
  | { state: "ok"; data: T };

function asApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(0, "unexpected_response", String(error));
}

/**
 * Pede `path` ao montar e a cada `reload()`. A resposta de um pedido que outro já substituiu
 * — ou que chega depois de a tela sair — é descartada.
 *
 * `reload()` **não apaga o que já chegou**: com o dado na tela, ele continua lá até a resposta
 * nova, que o substitui (ou vira erro); só a seção em erro volta a carregando. É o que deixa o
 * `reloadAll()` da tela do ativo recarregar sem piscar (RF-20).
 */
export function useResource<T>(path: string): { load: Load<T>; reload: () => void } {
  const [load, setLoad] = useState<Load<T>>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);

  // biome-ignore lint/correctness/useExhaustiveDependencies: `attempt` não é lido; mudar de valor é o que dispara o pedido de novo.
  useEffect(() => {
    let live = true;
    apiGet<T>(path).then(
      (data) => {
        if (live) setLoad({ state: "ok", data });
      },
      (error: unknown) => {
        if (live) setLoad({ state: "error", error: asApiError(error) });
      },
    );
    return () => {
      live = false;
    };
  }, [path, attempt]);

  const reload = useCallback(() => {
    setLoad((current) => (current.state === "ok" ? current : { state: "loading" }));
    setAttempt((n) => n + 1);
  }, []);

  return { load, reload };
}
