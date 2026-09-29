import type { ReactNode } from "react";

import { MODEL_ORDER, type RiskRun } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatDate, formatInstant, formatInteger } from "../format/numbers";

/** Os instantes da trilha no fuso da B3, como no `ativo.html` e no rodapé. */
const TRAIL_TIME_ZONE = "America/Sao_Paulo";

function instant(value: string): string {
  return formatInstant(value, TRAIL_TIME_ZONE);
}

/** A fonte da coleta pelo nome legível do módulo de textos; a desconhecida, crua. */
function sourceName(source: string): string {
  const key = `risco.trilha.fonte.${source}`;
  const text = (TEXTOS as Record<string, unknown>)[key];
  return typeof text === "string" ? text : source;
}

/** A situação da execução; a `partial` diz quantos modelos falharam (RF-16). */
function statusText(run: RiskRun): string {
  if (run.status === "ok") return TEXTOS["risco.trilha.status.ok"];
  if (run.status === "failed") return TEXTOS["risco.trilha.status.failed"];
  const calculated = new Set(
    run.results.filter((r) => r.error === "").map((r) => r.model_name),
  );
  return TEXTOS["risco.trilha.status.partial"](MODEL_ORDER.length - calculated.size);
}

function Item({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

/**
 * A trilha do cálculo (RF-16): o que entrou na execução, para ser conferida e refeita. Os
 * números vêm rotulados, sem frase própria (RF-21); o bloco tem uma frase só.
 */
export function RunTrail({ run }: { run: RiskRun }) {
  const pregoes = (n: number) => TEXTOS["risco.trilha.pregoes"](formatInteger(n));
  return (
    <>
      <p className="ruvor-note">{TEXTOS["risco.trilha"]}</p>
      <dl className="ruvor-trail">
        <Item label={TEXTOS["risco.trilha.asOf"]}>{formatDate(run.as_of_date)}</Item>
        <Item label={TEXTOS["risco.trilha.firstPrice"]}>
          {formatDate(run.first_price_date)}
        </Item>
        <Item label={TEXTOS["risco.trilha.priceCount"]}>
          {formatInteger(run.price_count)}
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
        <Item label={TEXTOS["risco.trilha.engine"]}>{run.engine_version}</Item>
        <Item label={TEXTOS["risco.trilha.seed"]}>{String(run.seed)}</Item>
        <Item label={TEXTOS["risco.trilha.priceRun"]}>
          {TEXTOS["risco.trilha.coleta"](
            sourceName(run.price_run.source),
            instant(run.price_run.finished_at ?? run.price_run.started_at),
          )}
        </Item>
        <Item label={TEXTOS["risco.trilha.status"]}>{statusText(run)}</Item>
      </dl>
    </>
  );
}
