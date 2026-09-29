import { useCallback, useId } from "react";

import { type Load, useResource } from "../api/resource";
import type { AssetDetail, Events, Metrics, Prices, Risk } from "../api/types";
import { AssetHeader } from "../components/AssetHeader";
import { BehaviorSection } from "../components/BehaviorSection";
import { EventsSection } from "../components/EventsSection";
import { PriceSection } from "../components/PriceSection";
import { SearchBox } from "../components/SearchBox";
import { TEXTOS } from "../content/textos";

/** As cinco rotas do ativo, cada uma com o seu estado e o seu "tentar de novo". */
export type AssetData = {
  asset: Load<AssetDetail>;
  prices: Load<Prices>;
  events: Load<Events>;
  metrics: Load<Metrics>;
  risk: Load<Risk>;
  reload: {
    asset: () => void;
    prices: () => void;
    events: () => void;
    metrics: () => void;
    risk: () => void;
  };
  /**
   * Pede as cinco de novo (RF-20: o fim do acompanhamento). Não apaga o que está na tela: cada
   * seção mostra o dado anterior até o novo chegar (`useResource`).
   */
  reloadAll: () => void;
};

/**
 * As cinco rotas do ativo em paralelo (RF-06): cada seção carrega sozinha, e a lenta não
 * segura a rápida.
 */
export function useAssetData(ticker: string): AssetData {
  const base = `/api/v1/assets/${encodeURIComponent(ticker)}`;
  const asset = useResource<AssetDetail>(base);
  const prices = useResource<Prices>(`${base}/prices`);
  const events = useResource<Events>(`${base}/events`);
  const metrics = useResource<Metrics>(`${base}/metrics`);
  const risk = useResource<Risk>(`${base}/risk`);

  const reloadAsset = asset.reload;
  const reloadPrices = prices.reload;
  const reloadEvents = events.reload;
  const reloadMetrics = metrics.reload;
  const reloadRisk = risk.reload;
  const reloadAll = useCallback(() => {
    reloadAsset();
    reloadPrices();
    reloadEvents();
    reloadMetrics();
    reloadRisk();
  }, [reloadAsset, reloadPrices, reloadEvents, reloadMetrics, reloadRisk]);

  return {
    asset: asset.load,
    prices: prices.load,
    events: events.load,
    metrics: metrics.load,
    risk: risk.load,
    reload: {
      asset: reloadAsset,
      prices: reloadPrices,
      events: reloadEvents,
      metrics: reloadMetrics,
      risk: reloadRisk,
    },
    reloadAll,
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
 * A tela do ativo (RF-06 a RF-11): o cabeçalho, o preço, os proventos e o comportamento, e o
 * espaço da seção de risco.
 *
 * `data-ready="true"` no raiz quando o cabeçalho **e** o risco terminaram, com sucesso ou erro
 * — é o que a execução real espera. O "risco terminou" é uma linha só, `riskDone`: hoje, o
 * `/risk` respondeu; a T11 a troca pelo que a seção de risco disser.
 */
export function AssetScreen({ ticker }: { ticker: string }) {
  const data = useAssetData(ticker);
  const { asset, prices, events, metrics } = data;

  if (asset.state === "error" && asset.error.code === "asset_not_found") {
    return <AssetNotFound ticker={ticker} />;
  }

  const headDone = asset.state !== "loading";
  const riskDone = data.risk.state !== "loading";
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

      {/*
        A seção de risco (RF-12 a RF-20) é da T11 e entra aqui, no lugar deste espaço, com
        `id="risco"` — o destino do "Ir para o risco" do comportamento. Ela recebe
        `data.risk`, `data.reload.risk`, `data.reloadAll` (o fim do acompanhamento) e a
        identidade e os preços, que `riskState` pede.
      */}
      <div id="risco" />
    </div>
  );
}
