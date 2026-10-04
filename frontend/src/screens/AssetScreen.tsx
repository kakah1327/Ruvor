import { useCallback, useEffect, useId, useState } from "react";

import { type Load, useResource } from "../api/resource";
import type {
  AssetDetail,
  Events,
  Fundamentals,
  Lab,
  Metrics,
  Prices,
  Returns,
  Risk,
} from "../api/types";
import { AssetHeader } from "../components/AssetHeader";
import { BehaviorSection } from "../components/BehaviorSection";
import { DisclosuresSection } from "../components/DisclosuresSection";
import { EventsSection } from "../components/EventsSection";
import { FundamentalsSection } from "../components/FundamentalsSection";
import { LabSection } from "../components/LabSection";
import { PriceSection } from "../components/PriceSection";
import { ReturnsSection } from "../components/ReturnsSection";
import {
  RiskSection,
  sectionPending,
  sectionStateOf,
  wantsRail,
} from "../components/RiskSection";
import { SearchBox } from "../components/SearchBox";
import { useShellContext } from "../components/Shell";
import { TEXTOS } from "../content/textos";
import { useLabPolling } from "../lab/useLabPolling";
import { usePolling } from "../risk/usePolling";

/**
 * As oito rotas do ativo que a tela pede, cada uma com o seu estado e o seu "tentar de novo" —
 * a sétima, `/lab`, é a do laboratório (M2.4, RF-18), e a oitava, `/returns`, a do retorno
 * (M5.1). A nona, `/disclosures`, a seção Comunicados pede sozinha (M1.6c, "Quem carrega os
 * comunicados").
 */
export type AssetData = {
  asset: Load<AssetDetail>;
  prices: Load<Prices>;
  events: Load<Events>;
  metrics: Load<Metrics>;
  risk: Load<Risk>;
  fundamentals: Load<Fundamentals>;
  lab: Load<Lab>;
  returns: Load<Returns>;
  reload: {
    asset: () => void;
    prices: () => void;
    events: () => void;
    metrics: () => void;
    risk: () => void;
    fundamentals: () => void;
    lab: () => void;
    returns: () => void;
  };
  /**
   * Pede as oito de novo e incrementa `reloadToken` (RF-20 do M1.6b, RF-15 do M1.6c: o fim do
   * acompanhamento). Não apaga o que está na tela: cada seção mostra o dado anterior até o novo
   * chegar (`useResource`).
   */
  reloadAll: () => void;
  /** Muda a cada `reloadAll()`: a seção Comunicados volta à primeira página, com o filtro. */
  reloadToken: number;
};

/**
 * As oito rotas do ativo em paralelo (RF-06 do M1.6b, RF-15 do M1.6c, RF-18 do M2.4, M5.1):
 * cada seção carrega sozinha, e a lenta não segura a rápida.
 */
export function useAssetData(ticker: string): AssetData {
  const base = `/api/v1/assets/${encodeURIComponent(ticker)}`;
  const asset = useResource<AssetDetail>(base);
  const prices = useResource<Prices>(`${base}/prices`);
  const events = useResource<Events>(`${base}/events`);
  const metrics = useResource<Metrics>(`${base}/metrics`);
  const risk = useResource<Risk>(`${base}/risk`);
  const fundamentals = useResource<Fundamentals>(`${base}/fundamentals`);
  const lab = useResource<Lab>(`${base}/lab`);
  const returns = useResource<Returns>(`${base}/returns`);
  const [reloadToken, setReloadToken] = useState(0);

  const reloadAsset = asset.reload;
  const reloadPrices = prices.reload;
  const reloadEvents = events.reload;
  const reloadMetrics = metrics.reload;
  const reloadRisk = risk.reload;
  const reloadFundamentals = fundamentals.reload;
  const reloadLab = lab.reload;
  const reloadReturns = returns.reload;
  const reloadAll = useCallback(() => {
    reloadAsset();
    reloadPrices();
    reloadEvents();
    reloadMetrics();
    reloadRisk();
    reloadFundamentals();
    reloadLab();
    reloadReturns();
    setReloadToken((n) => n + 1);
  }, [
    reloadAsset,
    reloadPrices,
    reloadEvents,
    reloadMetrics,
    reloadRisk,
    reloadFundamentals,
    reloadLab,
    reloadReturns,
  ]);

  return {
    asset: asset.load,
    prices: prices.load,
    events: events.load,
    metrics: metrics.load,
    risk: risk.load,
    fundamentals: fundamentals.load,
    lab: lab.load,
    returns: returns.load,
    reload: {
      asset: reloadAsset,
      prices: reloadPrices,
      events: reloadEvents,
      metrics: reloadMetrics,
      risk: reloadRisk,
      fundamentals: reloadFundamentals,
      lab: reloadLab,
      returns: reloadReturns,
    },
    reloadAll,
    reloadToken,
  };
}

/** A data de hoje no fuso do navegador, `AAAA-MM-DD`. */
function today(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/**
 * O fim da janela dos proventos: o último fechamento, como no `ativo.html`; sem ele — ativo sem
 * preço, ou a identidade em erro —, hoje. Nulo enquanto a identidade carrega.
 */
function eventsReference(asset: Load<AssetDetail>): string | null {
  if (asset.state === "loading") return null;
  if (asset.state === "ok" && asset.data.last_price !== null) {
    return asset.data.last_price.date;
  }
  return today();
}

/** O código fora do catálogo (`404 asset_not_found` na identidade): a tela inteira, com a busca. */
function AssetNotFound({ ticker }: { ticker: string }) {
  const titleId = useId();
  return (
    <section className="ruvor-notfound" aria-labelledby={titleId} data-ready="true">
      <p className="ruvor-eyebrow">{TEXTOS["ativo.naoEncontrado.sobrancelha"]}</p>
      <h1 className="ruvor-display" id={titleId}>
        {TEXTOS["ativo.naoEncontrado.titulo"]}
      </h1>
      <p className="ruvor-sub">{TEXTOS["ativo.naoEncontrado"](ticker)}</p>
      <p className="ruvor-sub">{TEXTOS["ativo.naoEncontrado.dica"]}</p>
      <SearchBox variant="page" />
    </section>
  );
}

/**
 * O que a resposta do pedido de cálculo (RF-19) põe no lugar do `/risk`: o corpo do 202 (ou o
 * `details` do 409), ou o 422 `asset_inactive`. Vale só enquanto o `/risk` da rota for o
 * mesmo de quando a resposta chegou (`base`): o próximo `/risk` recebido — o do
 * acompanhamento — o substitui.
 */
type Posted =
  | { base: Load<Risk>; kind: "risk"; risk: Risk }
  | { base: Load<Risk>; kind: "inactive" };

/**
 * A tela do ativo (RF-06 a RF-20 do M1.6b, RF-15 do M1.6c): o cabeçalho, o preço, os
 * proventos, o comportamento, o risco e, depois dele, o laboratório (M2.4), o retorno (M5.1),
 * os fundamentos e os comunicados, com a trilha na coluna lateral do casco e a proveniência no
 * rodapé.
 *
 * `data-ready="true"` no raiz quando o cabeçalho **e** a seção de risco terminaram, com
 * sucesso ou erro — é o que a execução real espera. A seção terminou quando saiu do
 * carregando: o do `/risk` e o da identidade e da série que o estado pede. As duas seções do
 * M1.6c, o `/lab` do laboratório (M2.4, RF-13) e o `/returns` do retorno (M5.1) não entram nele.
 */
export function AssetScreen({ ticker }: { ticker: string }) {
  const data = useAssetData(ticker);
  const { asset, prices, events, metrics } = data;
  const { setProvenance, setRail, railElement } = useShellContext();

  const [posted, setPosted] = useState<Posted | null>(null);
  const current = posted !== null && posted.base === data.risk ? posted : null;
  const riskLoad: Load<Risk> =
    current?.kind === "risk" ? { state: "ok", data: current.risk } : data.risk;
  const risk = riskLoad.state === "ok" ? riskLoad.data : null;
  const state = sectionStateOf(riskLoad, asset, prices, current?.kind === "inactive");

  usePolling(risk, data.reload.risk, data.reloadAll);
  // A releitura limitada do `/lab` depois do fim do acompanhamento (RF-18 do M2.4).
  useLabPolling(
    data.lab.state === "ok" ? data.lab.data : null,
    data.reload.lab,
    data.reloadToken,
  );

  const notFound = asset.state === "error" && asset.error.code === "asset_not_found";

  // A coluna lateral (a trilha) e a proveniência do rodapé (RF-04, RF-16): a do último
  // cálculo fechado `ok` ou `partial`.
  const railOn = !notFound && wantsRail(state, risk);
  useEffect(() => {
    setRail(railOn);
  }, [setRail, railOn]);

  const latest = risk?.latest ?? null;
  const closed = latest !== null && latest.status !== "failed" ? latest : null;
  const asOfDate = notFound ? null : (closed?.as_of_date ?? null);
  const calculatedAt = notFound ? null : (closed?.calculated_at ?? null);
  useEffect(() => {
    setProvenance(
      asOfDate === null || calculatedAt === null ? null : { asOfDate, calculatedAt },
    );
  }, [setProvenance, asOfDate, calculatedAt]);

  const baseRisk = data.risk;
  const onRisk = useCallback(
    (next: Risk) => setPosted({ base: baseRisk, kind: "risk", risk: next }),
    [baseRisk],
  );
  const onInactive = useCallback(
    () => setPosted({ base: baseRisk, kind: "inactive" }),
    [baseRisk],
  );

  if (notFound) {
    return <AssetNotFound ticker={ticker} />;
  }

  const headDone = asset.state !== "loading";
  const riskDone = !sectionPending(state);
  const ready = headDone && riskDone;

  return (
    <div
      className="ruvor-stack ruvor-stack--loose"
      data-ready={ready ? "true" : undefined}
    >
      <AssetHeader load={asset} onRetry={data.reload.asset} />
      <PriceSection load={prices} onRetry={data.reload.prices} />
      <EventsSection
        load={events}
        referenceDate={eventsReference(asset)}
        onRetry={data.reload.events}
      />
      <BehaviorSection load={metrics} ticker={ticker} onRetry={data.reload.metrics} />

      {/* `id="risco"`: o destino do "Ir para o risco" do comportamento. */}
      <div id="risco">
        <RiskSection
          ticker={ticker}
          state={state}
          risk={risk}
          pricesCount={prices.state === "ok" ? prices.data.results.length : null}
          rail={railElement}
          onRetry={data.reload.risk}
          onRisk={onRisk}
          onInactive={onInactive}
        />
      </div>

      {/* O laboratório (M2.4, RF-13): colado no risco, antes do retorno do M5.1 e dos
          Fundamentos; fora do `data-ready`. */}
      <LabSection load={data.lab} onRetry={data.reload.lab} />

      {/* O retorno (M5.1): depois do laboratório e antes dos Fundamentos; fora do
          `data-ready`. */}
      <ReturnsSection
        load={data.returns}
        asset={asset}
        prices={prices}
        today={today()}
        onRetry={data.reload.returns}
        onRetryPrices={data.reload.prices}
      />

      <FundamentalsSection
        load={data.fundamentals}
        asset={asset}
        onRetry={data.reload.fundamentals}
      />
      <DisclosuresSection
        ticker={ticker}
        asset={asset}
        reloadToken={data.reloadToken}
      />
    </div>
  );
}
