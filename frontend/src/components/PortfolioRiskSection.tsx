import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router";

import { ApiError, apiPost } from "../api/client";
import type { Portfolio, PortfolioRisk, PortfolioRun } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatDate, formatInteger } from "../format/numbers";
import {
  type PortfolioRiskState,
  portfolioRiskState,
  shouldPollPortfolio,
} from "../portfolio/riskState";
import { portfolioRiskPath, useRiskSource } from "../portfolio/useRiskSource";
import { textFor, useReading } from "../reading";
import { usePolling } from "../risk/usePolling";
import { useSession } from "../session/SessionProvider";
import { assetTabPath } from "./AssetTabs";
import { Collapsible } from "./Collapsible";
import { Glyph } from "./Glyph";
import { type BrlRange, LossSummary } from "./LossSummary";
import { ModelTable } from "./ModelTable";
import { modelsWithoutResult, PortfolioTrail } from "./PortfolioTrail";
import { Recalculating, StatePanel } from "./RiskSection";
import { SectionError, SectionSkeleton } from "./SectionStatus";
import { useShellContext } from "./Shell";
import { SignInNotice } from "./SignInNotice";

/** A carteira não recarrega nada no fim do acompanhamento: o corpo do `/risk` já é tudo. */
function noEnd(): void {}

/** A resposta do pedido que fica junto do botão (RF-11); as outras mudam o estado da seção. */
type Reply =
  | { kind: "sending" }
  | { kind: "upToDate" }
  | { kind: "busy" }
  | { kind: "serviceBusy"; seconds: string | null }
  | { kind: "noResponse" }
  | { kind: "error"; message: string };

/** Uma ação do `details` do `409 insufficient_history` (RF-12). */
type ShortAsset = { ticker: string; first_date: string | null; sessions: number };
type ShortHistory = { sessions: number; minimum: number; assets: ShortAsset[] };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** O `details` do histórico curto; fora da forma, nulo (a tela mostra o erro do pedido). */
function shortHistoryOf(details: unknown): ShortHistory | null {
  if (!isRecord(details) || !Array.isArray(details.assets)) return null;
  const { sessions, minimum } = details;
  if (typeof sessions !== "number" || typeof minimum !== "number") return null;
  const assets: ShortAsset[] = [];
  for (const a of details.assets) {
    if (
      !isRecord(a) ||
      typeof a.ticker !== "string" ||
      typeof a.sessions !== "number" ||
      !(a.first_date === null || typeof a.first_date === "string")
    ) {
      return null;
    }
    assets.push({ ticker: a.ticker, first_date: a.first_date, sessions: a.sessions });
  }
  return { sessions, minimum, assets };
}

/** O corpo `{portfolio_risk}` do 202, na forma mínima que a fonte lê. */
function riskOf(body: unknown): PortfolioRisk | null {
  if (!isRecord(body) || !isRecord(body.portfolio_risk)) return null;
  const risk = body.portfolio_risk;
  return typeof risk.version === "number" && "latest" in risk && "in_progress" in risk
    ? (risk as unknown as PortfolioRisk)
    : null;
}

/**
 * O histórico curto (RF-12): os três casos, nesta ordem — as ações sem preço, com o link para a
 * página de cada uma, e as curtas juntas quando as duas existem; a sobreposição curta só quando
 * toda ação tem o mínimo.
 */
function ShortHistoryPanel({ details }: { details: ShortHistory }) {
  const noPrice = details.assets.filter((a) => a.first_date === null);
  const short = details.assets.filter(
    (a) => a.first_date !== null && a.sessions < details.minimum,
  );
  const item = (a: ShortAsset) => (
    <li key={a.ticker}>
      <b>{a.ticker}</b>
      <span>
        {TEXTOS["carteira.risco.curta.item"](
          formatInteger(a.sessions),
          a.first_date === null ? "—" : formatDate(a.first_date),
        )}
      </span>
    </li>
  );
  return (
    <div className="ruvor-panel" role="alert" data-part="historico-curto">
      <div className="ruvor-panel__body ruvor-state">
        <span className="ruvor-icon ruvor-icon--review">
          <Glyph name="warning" weight="duotone" />
        </span>
        <div className="ruvor-state__body ruvor-short-history">
          <div>
            <p className="ruvor-state__title">
              {TEXTOS["carteira.risco.curta.titulo"]}
            </p>
            <p className="ruvor-state__text">
              {TEXTOS["carteira.risco.curta"](
                formatInteger(details.sessions),
                formatInteger(details.minimum),
              )}
            </p>
          </div>
          {noPrice.length > 0 && (
            <div className="ruvor-short-history__group" data-group="sem-preco">
              <p className="ruvor-level__title">
                {TEXTOS["carteira.risco.curta.semPreco.titulo"]}
              </p>
              <p className="ruvor-note">
                {TEXTOS["carteira.risco.curta.semPreco"](noPrice.length)}
              </p>
              <ul className="ruvor-asset-list">
                {noPrice.map((a) => (
                  <li key={a.ticker}>
                    <b>{a.ticker}</b>
                    <span>{TEXTOS["carteira.risco.curta.itemSemPreco"]}</span>
                    <Link to={assetTabPath(a.ticker, "risco")}>
                      {TEXTOS["carteira.risco.curta.irPara"](a.ticker)}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {short.length > 0 && (
            <div className="ruvor-short-history__group" data-group="curtas">
              <p className="ruvor-level__title">
                {TEXTOS["carteira.risco.curta.curtas.titulo"]}
              </p>
              <p className="ruvor-note">
                {TEXTOS["carteira.risco.curta.curtas"](short.length)}
              </p>
              <ul className="ruvor-asset-list">{short.map(item)}</ul>
            </div>
          )}
          {noPrice.length === 0 && short.length === 0 && (
            <div className="ruvor-short-history__group" data-group="sobreposicao">
              <p className="ruvor-level__title">
                {TEXTOS["carteira.risco.curta.sobreposicao.titulo"]}
              </p>
              <p className="ruvor-note">
                {TEXTOS["carteira.risco.curta.sobreposicao"]}
              </p>
              <ul className="ruvor-asset-list">{details.assets.map(item)}</ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/** A faixa em reais de cada nível, do `summary` (RF-10); sem valor, nula. */
function brlRangeOf(run: PortfolioRun): BrlRange {
  const range: Record<string, readonly [string, string] | null> = {};
  for (const level of run.summary) {
    range[level.alpha] =
      level.loss_brl_min !== null && level.loss_brl_max !== null
        ? [level.loss_brl_min, level.loss_brl_max]
        : null;
  }
  return range;
}

/** O texto da região viva: só o andamento, nunca o resultado (o molde do ativo). */
function liveText(state: PortfolioRiskState): string {
  if (state.kind === "result_recalculating") {
    return TEXTOS["risco.estado.recalculando"](
      state.progress.results_written,
      state.progress.results_expected,
    );
  }
  if (state.kind === "calculating") {
    return TEXTOS["risco.estado.E4"](
      state.progress.results_written,
      state.progress.results_expected,
    );
  }
  return "";
}

/**
 * A seção de risco da carteira (M2.2b, RF-09 a RF-12), como o `risco.html` aprovado: os sete
 * estados na ordem de `portfolio/riskState.ts`, o pedido nos estados 5, 6 e 7, o histórico curto
 * e a trilha na coluna lateral do casco, por portal.
 *
 * - **A fonte** é `useRiskSource`: só monta com a carteira aberta e a sessão logada (a página
 *   garante), e a consulta repetida segue enquanto há `in_progress` (D-182) — parada na leitura
 *   só leitura, depois de um 401.
 * - **Depois de um `PUT` que muda a versão, e de um `PATCH` que muda o valor**, a seção pede o
 *   `GET .../risk` de novo: o risco é só o da versão corrente, e os reais saem do valor de agora.
 *   Até a releitura voltar, o corpo é de outra versão, e a ordem dos estados mostra "carregando"
 *   (ou o erro) — nunca o resultado da versão anterior.
 * - **O pedido**: o 202 entra como a leitura; o `409 portfolio_risk_up_to_date` relê e diz a data
 *   do `latest`; o `409 insufficient_history` abre o histórico curto; os 429 e as falhas ficam
 *   junto do botão; o 401 chama `expired()` e a página põe o aviso no lugar do botão
 *   (`endedHere`); o 404 leva a página a "não encontrada".
 */
export function PortfolioRiskSection({
  portfolio,
  readOnly,
  endedHere,
  onNotFound,
  onRunning,
}: {
  portfolio: Portfolio;
  /** Depois de um 401, a página é só leitura: nenhum botão de pedido, e a consulta para. */
  readOnly: boolean;
  /** O 401 chegou por esta seção: o aviso de sessão terminada no lugar do botão. */
  endedHere: boolean;
  onNotFound: () => void;
  /** Se há cálculo em curso da versão corrente (as frases da composição, RF-07). */
  onRunning: (running: boolean) => void;
}) {
  const titleId = useId();
  const railTitleId = useId();
  const reading = useReading();
  const session = useSession();
  const { setRail, railElement } = useShellContext();
  const { source, reload, accept } = useRiskSource(portfolio.id);
  const [reply, setReply] = useState<Reply | null>(null);
  const [short, setShort] = useState<ShortHistory | null>(null);
  const noticeLink = useRef<HTMLAnchorElement>(null);
  const askedEnded = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  usePolling(
    readOnly ? null : source.data,
    shouldPollPortfolio,
    reload,
    noEnd,
    source.attempt,
  );

  // A versão ou o valor mudaram (a resposta de um `PUT` ou de um `PATCH`): um `GET` novo.
  const seen = useRef({ version: portfolio.version, notional: portfolio.notional });
  useEffect(() => {
    const before = seen.current;
    if (
      before.version === portfolio.version &&
      before.notional === portfolio.notional
    ) {
      return;
    }
    seen.current = { version: portfolio.version, notional: portfolio.notional };
    setReply(null);
    setShort(null);
    reload();
  }, [portfolio.version, portfolio.notional, reload]);

  useEffect(() => {
    if (source.notFound) onNotFound();
  }, [source.notFound, onNotFound]);

  const state = portfolioRiskState(source, portfolio.version);
  const current =
    source.data !== null && source.data.version === portfolio.version
      ? source.data
      : null;
  const running = current !== null && current.in_progress !== null;
  useEffect(() => {
    onRunning(running);
  }, [running, onRunning]);

  // A trilha: o esqueleto carregando, ou a execução da versão corrente.
  const railLatest = state.kind === "loading" ? null : (current?.latest ?? null);
  const railOn = state.kind === "loading" || railLatest !== null;
  useEffect(() => {
    setRail(railOn);
  }, [setRail, railOn]);
  useEffect(() => () => setRail(false), [setRail]);

  // O 401 do pedido: o foco vai ao "Entrar" do aviso que tomou o lugar do botão.
  useEffect(() => {
    if (endedHere && askedEnded.current) {
      askedEnded.current = false;
      noticeLink.current?.focus();
    }
  }, [endedHere]);

  const request = async () => {
    setReply({ kind: "sending" });
    setShort(null);
    let next: Reply | null = null;
    try {
      const body = riskOf(await apiPost<unknown>(portfolioRiskPath(portfolio.id)));
      if (!mounted.current) return;
      if (body === null) {
        next = { kind: "noResponse" };
      } else {
        accept(body);
      }
    } catch (error) {
      if (!mounted.current) return;
      if (!(error instanceof ApiError)) {
        next = { kind: "noResponse" };
      } else if (error.code === "not_authenticated") {
        askedEnded.current = true;
        session.expired();
      } else if (error.code === "password_change_required") {
        void session.reload();
      } else if (error.code === "portfolio_not_found") {
        onNotFound();
        return;
      } else if (error.code === "portfolio_risk_up_to_date") {
        next = { kind: "upToDate" };
        reload();
      } else if (error.code === "insufficient_history") {
        const details = shortHistoryOf(error.details);
        if (details === null) {
          next = { kind: "error", message: error.message };
        } else {
          setShort(details);
        }
      } else if (error.code === "portfolio_compute_busy") {
        next = { kind: "busy" };
      } else if (error.code === "portfolio_queue_full") {
        next = { kind: "serviceBusy", seconds: null };
      } else if (error.code === "too_many_requests") {
        const wait = error.details.wait_seconds;
        next = {
          kind: "serviceBusy",
          seconds: typeof wait === "number" ? formatInteger(wait) : null,
        };
      } else if (
        error.code === "network_error" ||
        error.code === "unexpected_response"
      ) {
        next = { kind: "noResponse" };
      } else {
        next = { kind: "error", message: error.message };
      }
    }
    setReply(next);
  };

  /** O botão do pedido e a resposta junto dele; depois de um 401, o aviso ou nada. */
  function requestControl(again: boolean, asOf: string | null): ReactNode {
    if (endedHere) return <SignInNotice ended linkRef={noticeLink} />;
    if (readOnly) return null;
    const busy = reply?.kind === "sending";
    return (
      <>
        <button
          className="ruvor-btn ruvor-btn--primary"
          type="button"
          aria-busy={busy ? true : undefined}
          disabled={busy}
          data-part="pedido"
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
        {reply?.kind === "upToDate" && (
          <p
            className="ruvor-state__reply ruvor-state__reply--muted"
            role="status"
            data-part="atualizado"
          >
            {TEXTOS["carteira.risco.pedido.atualizado"](asOf ?? "—")}
          </p>
        )}
        {reply?.kind === "busy" && (
          <p className="ruvor-state__reply" role="alert" data-part="resposta-pedido">
            {TEXTOS["carteira.risco.pedido.ocupada"]}
          </p>
        )}
        {reply?.kind === "serviceBusy" && (
          <p className="ruvor-state__reply" role="alert" data-part="resposta-pedido">
            {TEXTOS["carteira.risco.pedido.servicoOcupado"](reply.seconds)}
          </p>
        )}
        {reply?.kind === "noResponse" && (
          <p
            className="ruvor-state__reply ruvor-state__reply--critical"
            role="alert"
            data-part="resposta-pedido"
          >
            {TEXTOS["risco.pedido.semResposta"]}
          </p>
        )}
        {reply?.kind === "error" && (
          <p
            className="ruvor-state__reply ruvor-state__reply--critical"
            role="alert"
            data-part="resposta-pedido"
          >
            {TEXTOS["risco.pedido.erro"](reply.message)}
          </p>
        )}
      </>
    );
  }

  /** O resultado (RF-10): o alto, os dois níveis, a frase do valor e a tabela dos nove. */
  function result(latest: PortfolioRun, action: ReactNode): ReactNode {
    const notional = current?.notional ?? null;
    return (
      <>
        <div className="ruvor-panel">
          <div className="ruvor-panel__body ruvor-portfolio-run" data-part="alto">
            <div className="ruvor-portfolio-run__facts">
              <p className="ruvor-note" data-phrase="asOf">
                {textFor("carteira.risco.asOf", reading)(formatDate(latest.as_of_date))}
              </p>
              {latest.status === "partial" && (
                <p className="ruvor-note" data-part="parcial">
                  {TEXTOS["carteira.risco.estado.parcial"](modelsWithoutResult(latest))}
                </p>
              )}
              {action !== null && (
                <p className="ruvor-note">{TEXTOS["carteira.risco.semRotina"]}</p>
              )}
            </div>
            {action !== null && (
              <div className="ruvor-portfolio-run__action">{action}</div>
            )}
          </div>
        </div>
        <LossSummary
          results={latest.results}
          brlRange={brlRangeOf(latest)}
          notional={notional}
          notRejectedKey="carteira.risco.naoRejeitados"
        />
        {notional !== null ? (
          <p className="ruvor-note" data-phrase="valorAgora">
            {textFor("carteira.risco.valorAgora", reading)}
          </p>
        ) : (
          <p className="ruvor-note" data-part="sem-valor">
            {TEXTOS["carteira.risco.semValor"]}
          </p>
        )}
        <div>
          <Collapsible name="models" label={TEXTOS["risco.modelos.abrir"]}>
            <ModelTable
              results={latest.results}
              lossBrl={notional !== null ? (r) => r.loss_brl : undefined}
            />
          </Collapsible>
        </div>
      </>
    );
  }

  let body: ReactNode = null;
  switch (state.kind) {
    case "loading":
      body = (
        <div role="status" aria-busy="true">
          <SectionSkeleton />
          <span className="ruvor-sr-only">{TEXTOS["carteira.risco.carregando"]}</span>
        </div>
      );
      break;
    case "error":
      body = <SectionError onRetry={reload} />;
      break;
    case "result_recalculating":
      body = (
        <div className="ruvor-stack">
          <Recalculating progress={state.progress} failed={false} />
          {result(state.latest, endedHere ? requestControl(true, null) : null)}
        </div>
      );
      break;
    case "calculating":
      body =
        state.failed === null ? (
          <StatePanel
            title={TEXTOS["risco.estado.E4"](
              state.progress.results_written,
              state.progress.results_expected,
            )}
            progress={state.progress}
            notes={[TEXTOS["risco.estado.E4.nota"], TEXTOS["risco.estado.atualiza"]]}
            actions={endedHere ? requestControl(false, null) : undefined}
          />
        ) : (
          <div className="ruvor-stack">
            <Recalculating progress={state.progress} failed={true} />
            <StatePanel
              tone="review"
              title={TEXTOS["risco.estado.E3.titulo"]}
              text={TEXTOS["carteira.risco.estado.falhou"]}
              actions={endedHere ? requestControl(true, null) : undefined}
            />
          </div>
        );
      break;
    case "ready":
      body = (
        <div className="ruvor-stack">
          {result(
            state.latest,
            requestControl(true, formatDate(state.latest.as_of_date)),
          )}
        </div>
      );
      break;
    case "failed":
      body = (
        <StatePanel
          tone="review"
          title={TEXTOS["risco.estado.E3.titulo"]}
          text={TEXTOS["carteira.risco.estado.falhou"]}
          notes={[TEXTOS["carteira.risco.semRotina"]]}
          actions={requestControl(true, null)}
        />
      );
      break;
    case "never":
      body = (
        <StatePanel
          title={TEXTOS["carteira.risco.estado.nunca.titulo"]}
          text={TEXTOS["carteira.risco.estado.nunca"]}
          notes={[TEXTOS["carteira.risco.semRotina"]]}
          actions={requestControl(false, null)}
        />
      );
      break;
  }

  return (
    <section
      className="ruvor-stack"
      aria-labelledby={titleId}
      data-part="risco"
      data-risk-state={state.kind}
    >
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["risco.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["risco.titulo"]}
          </h2>
        </div>
      </div>
      <p className="ruvor-sub">{TEXTOS["risco.intro"]}</p>
      <p className="ruvor-sr-only" aria-live="polite">
        {liveText(state)}
      </p>
      <div className="ruvor-stack">
        {body}
        {short !== null && <ShortHistoryPanel details={short} />}
      </div>
      {railElement !== null &&
        railOn &&
        createPortal(
          <section className="ruvor-rail__inner" aria-labelledby={railTitleId}>
            <p className="ruvor-eyebrow" id={railTitleId}>
              {TEXTOS["risco.trilha.titulo"]}
            </p>
            {railLatest === null ? (
              <div aria-busy="true">
                <SectionSkeleton />
              </div>
            ) : (
              <Collapsible name="trail" label={TEXTOS["risco.trilha.abrir"]}>
                <PortfolioTrail run={railLatest} />
              </Collapsible>
            )}
          </section>,
          railElement,
        )}
    </section>
  );
}
