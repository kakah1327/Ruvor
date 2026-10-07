/**
 * A fonte do risco da carteira (M2.2b, RF-09 e RF-11): o `GET /api/v1/portfolios/{id}/risk`
 * guardado de um jeito que o `useResource` (`api/resource.ts`) não guarda — **o último corpo bom
 * e o erro em separado**. Lá, a releitura que falha troca o dado por `{state: "error"}`; aqui,
 * ela mantém o `data`, e a seção segue mostrando o que mostrava (RF-09: "um erro numa consulta
 * repetida mantém o estado mostrado e tenta na consulta seguinte").
 *
 * - Uma leitura com erro **mantém o `data`** e sobe o `attempt` — o que reagenda a consulta
 *   (`risk/usePolling.ts`). `firstError` guarda o erro da leitura que falhou desde o último corpo
 *   bom; a ordem dos estados (`riskState.ts`) só o lê quando não há corpo da versão corrente —
 *   a primeira leitura, ou a primeira depois de um `PUT` que mudou a versão.
 * - **401** em qualquer leitura chama o `expired()` da sessão; **404** zera o `data` e liga
 *   `notFound`. Nenhum dos dois sobe o `attempt` nem "mantém o estado": a consulta para.
 * - **Só vale a resposta do pedido mais recente**: a de um pedido já substituído — por outro
 *   `reload()`, pelo `accept()`, ou pela saída da página — é descartada.
 * - O corpo do **202** entra por `accept()` como uma leitura (sobe o `attempt`).
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, apiGet } from "../api/client";
import type { PortfolioRisk } from "../api/types";
import { useSession } from "../session/SessionProvider";

export type RiskSource = {
  data: PortfolioRisk | null; // o último corpo bom (a leitura ou o 202)
  firstError: ApiError | null; // só o erro da primeira leitura
  notFound: boolean; // um 404 em qualquer leitura: a página vai a "não encontrada"
  loading: boolean; // a primeira leitura ainda não voltou
  attempt: number; // sobe a cada resposta, boa ou com erro — reagenda a consulta
};

const INITIAL: RiskSource = {
  data: null,
  firstError: null,
  notFound: false,
  loading: true,
  attempt: 0,
};

/** O caminho do risco de uma carteira. */
export function portfolioRiskPath(portfolioId: string): string {
  return `/api/v1/portfolios/${encodeURIComponent(portfolioId)}/risk`;
}

function asApiError(error: unknown): ApiError {
  return error instanceof ApiError
    ? error
    : new ApiError(0, "unexpected_response", String(error));
}

export function useRiskSource(portfolioId: string): {
  source: RiskSource;
  reload(): void; // um GET .../risk
  accept(body: PortfolioRisk): void; // o corpo do 202 entra como a leitura (sobe o attempt)
} {
  const { expired } = useSession();
  const [state, setState] = useState<{ id: string; source: RiskSource }>({
    id: portfolioId,
    source: INITIAL,
  });

  let source = state.source;
  if (state.id !== portfolioId) {
    // Outra carteira: a fonte recomeça, ainda no desenho (o molde do `ModelTable`).
    source = INITIAL;
    setState({ id: portfolioId, source });
  }

  // O número do pedido mais recente: a resposta de outro número é descartada.
  const latest = useRef(0);

  const update = useCallback(
    (next: (current: RiskSource) => RiskSource) => {
      setState((current) =>
        current.id === portfolioId
          ? { id: current.id, source: next(current.source) }
          : current,
      );
    },
    [portfolioId],
  );

  const fetchRisk = useCallback(() => {
    latest.current += 1;
    const ticket = latest.current;
    apiGet<{ portfolio_risk: PortfolioRisk }>(portfolioRiskPath(portfolioId)).then(
      (body) => {
        if (ticket !== latest.current) return;
        update((current) => ({
          data: body.portfolio_risk,
          firstError: null,
          notFound: false,
          loading: false,
          attempt: current.attempt + 1,
        }));
      },
      (raw: unknown) => {
        if (ticket !== latest.current) return;
        const error = asApiError(raw);
        if (error.status === 401) {
          update((current) => ({ ...current, loading: false }));
          expired();
          return;
        }
        if (error.status === 404) {
          update((current) => ({
            ...current,
            data: null,
            firstError: null,
            notFound: true,
            loading: false,
          }));
          return;
        }
        update((current) => ({
          ...current,
          firstError: error,
          loading: false,
          attempt: current.attempt + 1,
        }));
      },
    );
  }, [portfolioId, update, expired]);

  useEffect(() => {
    fetchRisk();
    return () => {
      // A saída da página (ou a troca de carteira): a resposta em voo não vale mais.
      latest.current += 1;
    };
  }, [fetchRisk]);

  const reload = useCallback(() => {
    // Sem corpo bom (a primeira leitura falhou), o "tentar de novo" volta a carregando.
    update((current) =>
      current.data === null ? { ...current, firstError: null, loading: true } : current,
    );
    fetchRisk();
  }, [update, fetchRisk]);

  const accept = useCallback(
    (body: PortfolioRisk) => {
      latest.current += 1; // a leitura em voo é mais velha que o 202
      update((current) => ({
        data: body,
        firstError: null,
        notFound: false,
        loading: false,
        attempt: current.attempt + 1,
      }));
    },
    [update],
  );

  return { source, reload, accept };
}
