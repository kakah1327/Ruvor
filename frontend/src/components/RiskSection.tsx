import { type ReactNode, useId } from "react";
import { createPortal } from "react-dom";

import type { Load } from "../api/resource";
import type { AssetDetail, InProgress, Prices, Risk } from "../api/types";
import { traduzirMotivo } from "../content/motivos";
import { MIN_SESSIONS } from "../content/sugestoes";
import { TEXTOS } from "../content/textos";
import { formatInteger } from "../format/numbers";
import { type RiskState, riskState } from "../risk/state";
import { Collapsible } from "./Collapsible";
import { ComputeInvite } from "./ComputeInvite";
import { Glyph } from "./Glyph";
import { LossSummary } from "./LossSummary";
import { ModelTable } from "./ModelTable";
import { RunTrail } from "./RunTrail";
import { SectionError, SectionSkeleton } from "./SectionStatus";

/**
 * O estado da seção, em `data-risk-state` (RF-17, RF-20): os de `riskState`, mais o próprio
 * `/risk` carregando na primeira carga e o `/risk` em erro.
 */
export type SectionState = RiskState | "RISCO_CARREGANDO" | "RISCO_ERRO";

/**
 * Decide o estado a partir das três rotas que ele pede. `inactive` é o 422 `asset_inactive`
 * do pedido (RF-19), que leva ao E9 qualquer que seja o `/risk`.
 */
export function sectionStateOf(
  risk: Load<Risk>,
  asset: Load<AssetDetail>,
  prices: Load<Prices>,
  inactive: boolean,
): SectionState {
  if (inactive) return "E9";
  if (risk.state === "loading") return "RISCO_CARREGANDO";
  if (risk.state === "error") return "RISCO_ERRO";
  return riskState(
    asset.state === "ok"
      ? { state: "ok", status: asset.data.status }
      : { state: asset.state },
    risk.data,
    prices.state === "ok"
      ? { state: "ok", count: prices.data.results.length }
      : { state: prices.state },
  );
}

/** A seção ainda não tem o que mostrar: o `/risk`, ou a identidade e a série que ele pede. */
export function sectionPending(state: SectionState): boolean {
  return state === "RISCO_CARREGANDO" || state === "CARREGANDO";
}

type Tone = "evidence" | "review";

/**
 * O painel de estado (`.ruvor-state`): o sinal, o título, a frase, o andamento, as notas e a
 * ação. Os sinais são só duotone (D-93): info na evidência, warning na revisão.
 */
function StatePanel({
  tone = "evidence",
  title,
  text,
  progress,
  notes = [],
  actions,
  notice = false,
}: {
  tone?: Tone;
  title: string;
  text?: string;
  progress?: InProgress;
  notes?: string[];
  actions?: ReactNode;
  notice?: boolean;
}) {
  const inner = (
    <>
      <span className={`ruvor-icon ruvor-icon--${tone}`}>
        {tone === "review" ? (
          <Glyph name="warning" weight="duotone" />
        ) : (
          <Glyph name="info" weight="duotone" />
        )}
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">{title}</p>
        {text !== undefined && <p className="ruvor-state__text">{text}</p>}
        {progress !== undefined && (
          <span
            className="ruvor-progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={progress.results_expected}
            aria-valuenow={progress.results_written}
            aria-label={title}
          >
            <span
              className="ruvor-progress__fill"
              style={{ width: `${progressPercent(progress).toFixed(1)}%` }}
            />
          </span>
        )}
        {notes.map((note) => (
          <p className="ruvor-note" key={note}>
            {note}
          </p>
        ))}
        {actions !== undefined && <div className="ruvor-state__actions">{actions}</div>}
      </div>
    </>
  );
  return notice ? (
    <div className="ruvor-state ruvor-state--notice">{inner}</div>
  ) : (
    <div className="ruvor-panel">
      <div className="ruvor-panel__body ruvor-state">{inner}</div>
    </div>
  );
}

function progressPercent(progress: InProgress): number {
  if (progress.results_expected <= 0) return 0;
  return Math.min(100, (100 * progress.results_written) / progress.results_expected);
}

/** O aviso de recálculo acima do resultado (E2) ou da falha (E3 com `in_progress`). */
function Recalculating({
  progress,
  failed,
}: {
  progress: InProgress;
  failed: boolean;
}) {
  return (
    <StatePanel
      notice
      title={TEXTOS["risco.estado.recalculando"](
        progress.results_written,
        progress.results_expected,
      )}
      progress={progress}
      notes={[
        failed
          ? TEXTOS["risco.estado.recalculando.notaFalha"]
          : TEXTOS["risco.estado.recalculando.nota"],
      ]}
    />
  );
}

/** O carregando da seção: o esqueleto, e o texto só para leitor de tela. */
function Loading() {
  return (
    <div role="status" aria-busy="true">
      <SectionSkeleton />
      <span className="ruvor-sr-only">{TEXTOS["risco.carregando"]}</span>
    </div>
  );
}

/**
 * O texto da região viva da seção (RF-01 do M1.6d): só o andamento, nunca o resultado. A
 * ordem é a da tabela do RF-01; qualquer outro estado deixa a região vazia.
 */
export function liveText(state: SectionState, risk: Risk | null): string {
  const progress = risk?.in_progress ?? null;
  if (state === "E4") {
    return progress === null
      ? ""
      : TEXTOS["risco.estado.E4"](progress.results_written, progress.results_expected);
  }
  if (state === "E5") {
    return risk?.request?.status === "running"
      ? TEXTOS["risco.estado.E5.coletando"]
      : TEXTOS["risco.estado.E5.fila"];
  }
  if ((state === "E2" || state === "E3") && progress !== null) {
    return TEXTOS["risco.estado.recalculando"](
      progress.results_written,
      progress.results_expected,
    );
  }
  return "";
}

/**
 * O conteúdo da coluna lateral: a trilha, ou o esqueleto dela enquanto o `/risk` carrega. A
 * trilha fica atrás do controle de recolher (RF-06 do M2.3): fechada na iniciante, aberta na
 * avançada; o título fica à vista nos dois níveis.
 */
function Trail({ risk }: { risk: Risk | null }) {
  const titleId = useId();
  const run = risk?.latest ?? null;
  return (
    <section className="ruvor-rail__inner" aria-labelledby={titleId}>
      <p className="ruvor-eyebrow" id={titleId}>
        {TEXTOS["risco.trilha.titulo"]}
      </p>
      {run === null ? (
        <div aria-busy="true">
          <SectionSkeleton />
        </div>
      ) : (
        <Collapsible name="trail" label={TEXTOS["risco.trilha.abrir"]}>
          <RunTrail run={run} />
        </Collapsible>
      )}
    </section>
  );
}

/** A coluna lateral tem conteúdo: o `/risk` carregando (o esqueleto) ou uma execução. */
export function wantsRail(state: SectionState, risk: Risk | null): boolean {
  if (state === "RISCO_CARREGANDO") return true;
  if (state === "RISCO_ERRO" || state === "E9") return false;
  return risk?.latest != null;
}

/**
 * A seção de risco (RF-12 a RF-20): um corpo para cada estado, e a trilha na coluna lateral
 * do casco (`rail`), por portal.
 */
export function RiskSection({
  ticker,
  state,
  risk,
  pricesCount,
  rail,
  onRetry,
  onRisk,
  onInactive,
}: {
  ticker: string;
  state: SectionState;
  /** O último `/risk` recebido (ou o que o pedido devolveu); nulo sem nenhum. */
  risk: Risk | null;
  /** Os pregões de `/prices`, para o E6b. */
  pricesCount: number | null;
  rail: HTMLElement | null;
  onRetry: () => void;
  onRisk: (risk: Risk) => void;
  onInactive: () => void;
}) {
  const titleId = useId();
  const latest = risk?.latest ?? null;
  const progress = risk?.in_progress ?? null;
  const request = risk?.request ?? null;

  let body: ReactNode = null;
  switch (state) {
    case "RISCO_CARREGANDO":
    case "CARREGANDO":
      body = <Loading />;
      break;
    case "RISCO_ERRO":
      body = <SectionError onRetry={onRetry} />;
      break;
    case "E1":
    case "E2":
      body = latest !== null && (
        <div className="ruvor-stack">
          {state === "E2" && progress !== null && (
            <Recalculating progress={progress} failed={false} />
          )}
          <LossSummary results={latest.results} />
          {/* A tabela dos nove recolhida inteira na iniciante (RF-06 do M2.3); o painel acima
              fica aberto nos dois níveis. */}
          <Collapsible name="models" label={TEXTOS["risco.modelos.abrir"]}>
            <ModelTable results={latest.results} />
          </Collapsible>
        </div>
      );
      break;
    case "E3": {
      const failed = (
        <StatePanel
          tone="review"
          title={TEXTOS["risco.estado.E3.titulo"]}
          text={TEXTOS["risco.estado.E3"]}
        />
      );
      body =
        progress === null ? (
          failed
        ) : (
          <div className="ruvor-stack">
            <Recalculating progress={progress} failed={true} />
            {failed}
          </div>
        );
      break;
    }
    case "E4":
      body = progress !== null && (
        <StatePanel
          title={TEXTOS["risco.estado.E4"](
            progress.results_written,
            progress.results_expected,
          )}
          progress={progress}
          notes={[TEXTOS["risco.estado.E4.nota"], TEXTOS["risco.estado.atualiza"]]}
        />
      );
      break;
    case "E5":
      body =
        request?.status === "running" ? (
          <StatePanel
            title={TEXTOS["risco.estado.E5.coletando"]}
            text={TEXTOS["risco.estado.E5.coletando.nota"]}
            notes={[TEXTOS["risco.estado.atualiza"]]}
          />
        ) : (
          <StatePanel
            title={TEXTOS["risco.estado.E5.fila"]}
            text={TEXTOS["risco.estado.E5.fila.nota"]}
            notes={[TEXTOS["risco.estado.atualiza"]]}
          />
        );
      break;
    case "E6":
      body = (
        <StatePanel
          title={TEXTOS["risco.estado.serieCurta.titulo"]}
          text={traduzirMotivo(request?.reason ?? "")}
          notes={[TEXTOS["risco.estado.serieCurta.nota"]]}
        />
      );
      break;
    case "E6b":
      body = (
        <StatePanel
          title={TEXTOS["risco.estado.serieCurta.titulo"]}
          text={TEXTOS["motivos.serieCurta"](
            formatInteger(pricesCount ?? 0),
            formatInteger(MIN_SESSIONS),
          )}
          notes={[TEXTOS["risco.estado.serieCurta.nota"]]}
        />
      );
      break;
    case "E7":
      body = (
        <StatePanel
          tone="review"
          title={TEXTOS["risco.estado.E7.titulo"]}
          text={traduzirMotivo(request?.reason ?? "")}
          notes={[TEXTOS["risco.estado.E7.nota"]]}
          actions={
            <ComputeInvite
              ticker={ticker}
              again={true}
              onRisk={onRisk}
              onInactive={onInactive}
            />
          }
        />
      );
      break;
    case "E8":
      body = (
        <StatePanel
          title={TEXTOS["risco.estado.E8.titulo"]}
          text={TEXTOS["risco.estado.E8"]}
          actions={
            <ComputeInvite
              ticker={ticker}
              again={false}
              onRisk={onRisk}
              onInactive={onInactive}
            />
          }
        />
      );
      break;
    case "E9":
      body = (
        <StatePanel
          title={TEXTOS["risco.estado.E9.titulo"]}
          text={TEXTOS["risco.estado.E9"]}
        />
      );
      break;
  }

  return (
    <section className="ruvor-stack" aria-labelledby={titleId} data-risk-state={state}>
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["risco.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["risco.titulo"]}
          </h2>
        </div>
      </div>
      <p className="ruvor-sub">{TEXTOS["risco.intro"]}</p>
      {/* O andamento é anunciado pelo leitor de tela (RF-20 do M1.6b, RF-01 do M1.6d) por uma
          região própria, sempre montada e vazia sem andamento — uma região criada junto com o
          texto não é anunciada. O texto só muda quando o estado, os resultados escritos ou o
          status do pedido mudam: o /risk repetido a cada 5 s com o mesmo andamento não muda
          nada. Sem role: um segundo "status" na seção colidiria com o carregando. */}
      <p className="ruvor-sr-only" aria-live="polite">
        {liveText(state, risk)}
      </p>
      <div>{body}</div>
      {rail !== null &&
        wantsRail(state, risk) &&
        createPortal(<Trail risk={risk} />, rail)}
    </section>
  );
}
