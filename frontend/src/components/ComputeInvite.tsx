import { useEffect, useRef, useState } from "react";

import { ApiError, apiPost } from "../api/client";
import type { Risk } from "../api/types";
import { TEXTOS } from "../content/textos";
import { Glyph } from "./Glyph";

/** A resposta do pedido que fica junto do botão (RF-19); as outras mudam o estado da seção. */
type Reply =
  | { kind: "queueFull" }
  | { kind: "error"; message: string }
  | { kind: "noResponse" };

/** O corpo do `/risk` no `details` do 409 — a forma mínima que a seção lê. */
function isRisk(value: unknown): value is Risk {
  if (typeof value !== "object" || value === null) return false;
  const body = value as Record<string, unknown>;
  return (
    typeof body.ticker === "string" &&
    "latest" in body &&
    "in_progress" in body &&
    "request" in body
  );
}

/**
 * O botão que pede o cálculo (RF-19): `POST /api/v1/assets/{ticker}/risk`, com o
 * `X-CSRFToken` do cliente quando o cookie existe.
 *
 * - 202: o corpo é o `/risk`, e a seção passa ao estado dele (`onRisk`) — e o acompanhamento
 *   começa;
 * - 409 `asset_already_covered`: o `/risk` do `details` — alguém calculou antes;
 * - 422 `asset_inactive`: E9 (`onInactive`);
 * - 429 `on_demand_queue_full`: a frase da fila cheia, e o botão de volta;
 * - erro de rede ou fora do formato da D-86: a frase fixa de sem resposta; outro erro, a
 *   mensagem da D-86 dentro da frase do pedido não aceito — e o botão de volta.
 *
 * Enquanto o `POST` não volta, o botão fica `aria-busy` e desabilitado.
 */
export function ComputeInvite({
  ticker,
  again,
  onRisk,
  onInactive,
}: {
  ticker: string;
  /** "Calcular de novo" (E7) em vez de "Calcular o risco" (E8). */
  again: boolean;
  onRisk: (risk: Risk) => void;
  onInactive: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [reply, setReply] = useState<Reply | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const request = async () => {
    setBusy(true);
    setReply(null);
    let next: Reply | null = null;
    try {
      const body = await apiPost<Risk>(
        `/api/v1/assets/${encodeURIComponent(ticker)}/risk`,
      );
      if (!mounted.current) return;
      onRisk(body);
    } catch (error) {
      if (!mounted.current) return;
      if (!(error instanceof ApiError)) {
        next = { kind: "noResponse" };
      } else if (error.code === "asset_already_covered" && isRisk(error.details)) {
        onRisk(error.details);
      } else if (error.code === "asset_inactive") {
        onInactive();
      } else if (error.code === "on_demand_queue_full") {
        next = { kind: "queueFull" };
      } else if (
        error.code === "network_error" ||
        error.code === "unexpected_response"
      ) {
        next = { kind: "noResponse" };
      } else {
        next = { kind: "error", message: error.message };
      }
    }
    setBusy(false);
    setReply(next);
  };

  return (
    <>
      <button
        className="ruvor-btn ruvor-btn--primary"
        type="button"
        aria-busy={busy ? true : undefined}
        disabled={busy}
        onClick={() => {
          void request();
        }}
      >
        {busy ? (
          <Glyph name="spinner-gap" className="ruvor-spin" />
        ) : (
          <Glyph name="chart-line" />
        )}
        <span>
          {again ? TEXTOS["risco.pedido.deNovo"] : TEXTOS["risco.pedido.calcular"]}
        </span>
      </button>
      {busy && (
        <p className="ruvor-state__reply ruvor-state__reply--muted" role="status">
          {TEXTOS["risco.pedido.enviando"]}
        </p>
      )}
      {reply?.kind === "queueFull" && (
        <p className="ruvor-state__reply" role="alert">
          {TEXTOS["risco.pedido.filaCheia"]}
        </p>
      )}
      {reply?.kind === "error" && (
        <p className="ruvor-state__reply ruvor-state__reply--critical" role="alert">
          {TEXTOS["risco.pedido.erro"](reply.message)}
        </p>
      )}
      {reply?.kind === "noResponse" && (
        <p className="ruvor-state__reply ruvor-state__reply--critical" role="alert">
          {TEXTOS["risco.pedido.semResposta"]}
        </p>
      )}
    </>
  );
}
