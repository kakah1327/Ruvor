import type { ReactNode } from "react";

import { MODEL_ORDER, type PortfolioRun } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatDate, formatInstant, formatInteger } from "../format/numbers";
import { textFor, useReading } from "../reading";

/** Os instantes da trilha no fuso da B3, como a trilha do ativo. */
const TRAIL_TIME_ZONE = "America/Sao_Paulo";

function instant(value: string): string {
  const [data = "", hora = ""] = formatInstant(value, TRAIL_TIME_ZONE).split(" ");
  return TEXTOS["risco.trilha.instante"](data, hora);
}

/** Quantos dos nove não têm nenhum resultado sem erro: a conta da `partial` (RF-10). */
export function modelsWithoutResult(run: PortfolioRun): number {
  const calculated = new Set(
    run.results.filter((r) => r.error === "").map((r) => r.model_name),
  );
  return MODEL_ORDER.length - calculated.size;
}

function statusText(run: PortfolioRun): string {
  if (run.status === "ok") return TEXTOS["risco.trilha.status.ok"];
  if (run.status === "failed") return TEXTOS["risco.trilha.status.failed"];
  return TEXTOS["risco.trilha.status.partial"](modelsWithoutResult(run));
}

function Item({
  label,
  children,
  hash = false,
}: {
  label: string;
  children: ReactNode;
  hash?: boolean;
}) {
  return (
    <div className={hash ? "ruvor-trail__hash-row" : undefined}>
      <dt>{label}</dt>
      <dd className={hash ? "ruvor-trail__hash" : undefined}>{children}</dd>
    </div>
  );
}

/**
 * A trilha do cálculo da carteira (M2.2b, RF-10, RF-16), como no `risco.html` aprovado: o manifesto
 * dela tem outra forma que o do ativo — a versão, os pregões em comum, quem pediu e o SHA-256 da
 * série, sem a coleta de preço. A frase da série (`carteira.risco.serie`) vem depois da frase da
 * trilha, no nível de leitura; o `price_run_id` fica de fora.
 */
export function PortfolioTrail({ run }: { run: PortfolioRun }) {
  const reading = useReading();
  const pregoes = (n: number) => TEXTOS["risco.trilha.pregoes"](formatInteger(n));
  return (
    <div className="ruvor-portfolio-trail">
      <p className="ruvor-note">{TEXTOS["risco.trilha"]}</p>
      <p className="ruvor-note" data-phrase="serie">
        {textFor("carteira.risco.serie", reading)}
      </p>
      <dl className="ruvor-trail">
        <Item label={TEXTOS["carteira.risco.trilha.versao"]}>
          {String(run.version)}
        </Item>
        <Item label={TEXTOS["risco.trilha.firstPrice"]}>
          {formatDate(run.first_date)}
        </Item>
        <Item label={TEXTOS["risco.trilha.asOf"]}>{formatDate(run.as_of_date)}</Item>
        <Item label={TEXTOS["carteira.risco.trilha.sessoes"]}>
          {formatInteger(run.session_count)}
        </Item>
        <Item label={TEXTOS["risco.trilha.train"]}>{pregoes(run.train_count)}</Item>
        <Item label={TEXTOS["risco.trilha.test"]}>{pregoes(run.test_count)}</Item>
        <Item label={TEXTOS["risco.trilha.window"]}>
          {pregoes(run.train_window_days)}
        </Item>
        <Item label={TEXTOS["risco.trilha.calculatedAt"]}>
          {instant(run.calculated_at)}
        </Item>
        <Item label={TEXTOS["risco.trilha.finishedAt"]}>
          {run.finished_at === null ? "—" : instant(run.finished_at)}
        </Item>
        <Item label={TEXTOS["risco.trilha.engine"]}>{run.engine_version || "—"}</Item>
        <Item label={TEXTOS["risco.trilha.seed"]}>{String(run.seed)}</Item>
        <Item label={TEXTOS["carteira.risco.trilha.pedidoPor"]}>
          {run.requested_by.name}
        </Item>
        <Item label={TEXTOS["carteira.risco.trilha.sha"]} hash>
          {run.series_sha256}
        </Item>
        <Item label={TEXTOS["risco.trilha.status"]}>{statusText(run)}</Item>
      </dl>
    </div>
  );
}
