import { type ReactNode, useId } from "react";

import type { Load } from "../api/resource";
import {
  type AssetDetail,
  type Fundamentals,
  type Indicator,
  PEER_INDICATORS,
  type PeerIndicatorName,
  type Peers,
} from "../api/types";
import { type NullableField, nullReason } from "../content/nulos";
import { TEXTOS } from "../content/textos";
import {
  formatCompactCurrency,
  formatCurrency,
  formatDate,
  formatDecimal,
  formatInstant,
  formatInteger,
  formatPercent,
  typographicMinus,
} from "../format/numbers";
import { type Reading, textFor, useReading } from "../reading";
import { Glyph } from "./Glyph";
import { SectionError, SectionSkeleton } from "./SectionStatus";

/** O instante do cálculo no fuso da B3, como a trilha do risco e o mockup. */
const PROVENANCE_TIME_ZONE = "America/Sao_Paulo";

/** Os campos que viram número em destaque (RF-06); `price_date` e `shares_total` entram nas frases. */
type StatField = Exclude<NullableField, "price_date" | "shares_total">;

type Kind = "money" | "ratio" | "perShare" | "multiple";

const KIND: Record<StatField, Kind> = {
  revenue_ttm: "money",
  ebit_ttm: "money",
  net_income_ttm: "money",
  equity_parent: "money",
  total_assets: "money",
  gross_debt: "money",
  cash: "money",
  net_debt: "money",
  market_cap: "money",
  net_margin: "ratio",
  ebit_margin: "ratio",
  roe: "ratio",
  net_debt_to_equity: "ratio",
  close: "perShare",
  eps: "perShare",
  bvps: "perShare",
  pe: "multiple",
  pb: "multiple",
};

type BlockName =
  | "resultado"
  | "rentabilidade"
  | "endividamento"
  | "porAcao"
  | "tamanho";

/** Os cinco blocos (RF-06), na ordem do mockup; o preço usado abre o bloco "por ação". */
const BLOCKS: ReadonlyArray<readonly [BlockName, readonly StatField[]]> = [
  ["resultado", ["revenue_ttm", "ebit_ttm", "net_income_ttm"]],
  ["rentabilidade", ["net_margin", "ebit_margin", "roe"]],
  ["endividamento", ["gross_debt", "cash", "net_debt", "net_debt_to_equity"]],
  ["porAcao", ["close", "eps", "bvps", "pe", "pb"]],
  ["tamanho", ["equity_parent", "total_assets", "market_cap"]],
];

/** A nota ao pé de cada bloco; a rentabilidade não tem. */
const BLOCK_NOTE: Record<BlockName, string | null> = {
  resultado: TEXTOS["fundamentos.nota.resultado"],
  rentabilidade: null,
  endividamento: TEXTOS["fundamentos.nota.endividamento"],
  porAcao: TEXTOS["fundamentos.nota.porAcao"],
  tamanho: TEXTOS["fundamentos.nota.tamanho"],
};

const NULL = "—";

function isPeerField(field: StatField): field is PeerIndicatorName {
  return (PEER_INDICATORS as readonly string[]).includes(field);
}

/** Valor em reais inteiro, com o menos tipográfico: a leitura de acessibilidade. */
function fullCurrency(value: number): string {
  return typographicMinus(formatCurrency(value));
}

function ratio(value: number): string {
  return typographicMinus(formatPercent(value, 1));
}

function times(value: number): string {
  return TEXTOS["fundamentos.vezes"](typographicMinus(formatDecimal(value, 2)));
}

/** O número presente como aparece, e a forma inteira para leitor de tela (só em reais). */
function display(field: StatField, value: number): { text: string; full?: string } {
  switch (KIND[field]) {
    case "money":
      return { text: formatCompactCurrency(value), full: fullCurrency(value) };
    case "ratio":
      return { text: ratio(value) };
    case "perShare":
      return { text: fullCurrency(value) };
    case "multiple":
      return { text: times(value) };
  }
}

/** "R$ 24,32": de cada R$ 100, o valor da fração, sem sinal — o ramo negativo diz o sinal. */
function per100(value: number): string {
  return formatCurrency(Math.abs(100 * value));
}

/**
 * A frase de um número presente (D-97), no nível pedido (RF-05 do M2.3): a avançada substitui a
 * iniciante, com os mesmos argumentos. A frase do nulo não passa por aqui: é a mesma nos dois.
 */
function phrase(
  field: StatField,
  indicator: Indicator,
  lastPriceDate: string | null,
  reading: Reading,
): string {
  const value = Number(indicator[field]);
  const negative = value < 0;
  const shares =
    indicator.shares_total === null ? NULL : formatInteger(indicator.shares_total);
  const priceDate =
    indicator.price_date === null ? NULL : formatDate(indicator.price_date);
  const close = indicator.close === null ? NULL : fullCurrency(Number(indicator.close));

  switch (field) {
    case "revenue_ttm":
    case "gross_debt":
    case "cash":
    case "total_assets":
    case "market_cap":
      return textFor(`fundamentos.${field}`, reading);
    case "ebit_ttm":
    case "net_income_ttm":
    case "net_debt":
    case "equity_parent":
      return textFor(`fundamentos.${field}`, reading)(negative);
    case "net_margin":
    case "ebit_margin":
    case "roe":
    case "net_debt_to_equity":
      return textFor(`fundamentos.${field}`, reading)(per100(value), negative);
    case "close":
      // O preço de outra data (RF-06): o do cálculo é anterior ao último pregão da identidade.
      return lastPriceDate !== null &&
        indicator.price_date !== null &&
        indicator.price_date < lastPriceDate
        ? textFor("fundamentos.closeOutraData", reading)(
            priceDate,
            formatDate(lastPriceDate),
          )
        : textFor("fundamentos.close", reading)(priceDate);
    case "eps":
      return textFor("fundamentos.eps", reading)(shares, negative);
    case "bvps":
      return textFor("fundamentos.bvps", reading)(shares);
    case "pe":
      return textFor("fundamentos.pe", reading)(
        priceDate,
        close,
        typographicMinus(formatDecimal(value, 1)),
        negative,
      );
    case "pb":
      return textFor("fundamentos.pb", reading)(
        priceDate,
        close,
        formatDecimal(value, 2),
      );
  }
}

function median(field: PeerIndicatorName, value: number): string {
  return KIND[field] === "ratio" ? ratio(value) : times(value);
}

/**
 * A posição entre os pares (RF-10): `k = round(percentile × (n − 1))`, com `n = count`, só com
 * `n ≥ 3` e as três colunas presentes. A barra é a do kit, na cor neutra da evidência, nunca a
 * de aprovação; `k = 0` tem frase própria (ajuste do portão). A posição e a mediana seguem o
 * nível (RF-05 do M2.3); o rótulo e o "sem comparação", não.
 */
function PeerSlot({ field, peers }: { field: PeerIndicatorName; peers: Peers }) {
  const reading = useReading();
  const peer = peers[field];
  const label = (
    <span className="ruvor-peer__label">{TEXTOS["fundamentos.pares.rotulo"]}</span>
  );
  if (
    peer.median === null ||
    peer.percentile === null ||
    peer.count === null ||
    peer.count < 3
  ) {
    return (
      <div className="ruvor-peer">
        {label}
        <p className="ruvor-note">{TEXTOS["fundamentos.pares.semComparacao"]}</p>
      </div>
    );
  }
  const n = peer.count;
  const percentile = Number(peer.percentile);
  const k = Math.round(percentile * (n - 1));
  const others = formatInteger(n - 1);
  const position =
    k === 0
      ? textFor("fundamentos.pares.abaixoDeTodas", reading)(others)
      : textFor("fundamentos.pares.posicao", reading)(formatInteger(k), others);
  const groupMedian = textFor(
    "fundamentos.pares.mediana",
    reading,
  )(median(field, Number(peer.median)));
  return (
    <div className="ruvor-peer" data-peer-k={k} data-peer-n={n - 1}>
      {label}
      <span className="ruvor-bar ruvor-bar--evidence" aria-hidden="true">
        <span
          className="ruvor-bar__fill"
          style={{ width: `${(100 * percentile).toFixed(1)}%` }}
        />
      </span>
      <p className="ruvor-note">{`${position} ${groupMedian}`}</p>
    </div>
  );
}

function Stat({
  field,
  indicator,
  peers,
  lastPriceDate,
}: {
  field: StatField;
  indicator: Indicator;
  peers: Peers | null;
  lastPriceDate: string | null;
}) {
  const reading = useReading();
  const raw = indicator[field];
  // A leitura de acessibilidade (RF-06) vai num texto só para leitor de tela, e a forma
  // visível fica `aria-hidden`: `aria-label` num `span` sem papel não é lido (o ARIA proíbe
  // nomear elemento genérico, e o Biome o barra).
  let value: ReactNode;
  let note: string;
  if (raw === null) {
    const reason = nullReason(indicator, field);
    value = (
      <span className="ruvor-stat__value ruvor-num" data-null-reason={reason.code}>
        <span aria-hidden="true">{NULL}</span>
        <span className="ruvor-sr-only">{TEXTOS["fundamentos.semValor"]}</span>
      </span>
    );
    note = reason.text;
  } else {
    const shown = display(field, Number(raw));
    value = (
      <span className="ruvor-stat__value ruvor-num">
        {shown.full === undefined ? (
          shown.text
        ) : (
          <>
            <span aria-hidden="true">{shown.text}</span>
            <span className="ruvor-sr-only">{shown.full}</span>
          </>
        )}
      </span>
    );
    note = phrase(field, indicator, lastPriceDate, reading);
  }
  return (
    <div className="ruvor-stat" data-field={field}>
      <span className="ruvor-stat__label">{TEXTOS[`fundamentos.rotulo.${field}`]}</span>
      {value}
      <p className="ruvor-note">{note}</p>
      {peers !== null && isPeerField(field) && <PeerSlot field={field} peers={peers} />}
    </div>
  );
}

/** Um aviso ou painel de estado, com o sinal duotone da evidência (D-93). */
function StatePanel({
  title,
  text,
  notice = false,
}: {
  title: string;
  text?: string;
  notice?: boolean;
}) {
  const inner = (
    <>
      <span className="ruvor-icon ruvor-icon--evidence">
        <Glyph name="info" weight="duotone" />
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">{title}</p>
        {text !== undefined && <p className="ruvor-state__text">{text}</p>}
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

/** O grupo, uma vez, no topo (RF-09); sem comparação, o porquê (RF-10). */
function PeersNotice({ peers }: { peers: Peers | null }) {
  if (peers === null) {
    return <StatePanel notice title={TEXTOS["fundamentos.pares.indisponivel"]} />;
  }
  if (peers.peer_level === "segment") {
    return (
      <StatePanel
        notice
        title={TEXTOS["fundamentos.pares.segmento"](peers.group_segment ?? NULL)}
        text={TEXTOS["fundamentos.pares.leitura"]}
      />
    );
  }
  if (peers.peer_level === "subsector") {
    return (
      <StatePanel
        notice
        title={TEXTOS["fundamentos.pares.subsetor"](peers.group_subsector ?? NULL)}
        text={TEXTOS["fundamentos.pares.leitura"]}
      />
    );
  }
  return <StatePanel notice title={TEXTOS["fundamentos.pares.nenhum"]} />;
}

function Blocks({
  indicator,
  peers,
  lastPriceDate,
}: {
  indicator: Indicator;
  peers: Peers | null;
  lastPriceDate: string | null;
}) {
  const stat = (field: StatField) => (
    <Stat
      key={field}
      field={field}
      indicator={indicator}
      peers={peers}
      lastPriceDate={lastPriceDate}
    />
  );
  return (
    <div className="ruvor-stack">
      <PeersNotice peers={peers} />
      {BLOCKS.map(([block, fields]) => {
        const note = BLOCK_NOTE[block];
        return (
          <section className="ruvor-panel" key={block}>
            <div className="ruvor-panel__head">
              <h3 className="ruvor-h3">{TEXTOS[`fundamentos.bloco.${block}`]}</h3>
            </div>
            <div className="ruvor-panel__body">
              {block === "porAcao" ? (
                // O preço usado numa linha própria, acima dos quatro que dependem dele.
                <>
                  <div className="ruvor-stats">{stat(fields[0])}</div>
                  <div className="ruvor-divider ruvor-divider--spaced" />
                  <div className="ruvor-stats">{fields.slice(1).map(stat)}</div>
                </>
              ) : (
                <div className="ruvor-stats">{fields.map(stat)}</div>
              )}
              {note !== null && <p className="ruvor-note ruvor-panel__note">{note}</p>}
            </div>
          </section>
        );
      })}
      <p className="ruvor-note">{TEXTOS["fundamentos.fonteNota"]}</p>
    </div>
  );
}

function provenance(indicator: Indicator): string {
  const [data = "", hora = ""] = formatInstant(
    indicator.calculated_at,
    PROVENANCE_TIME_ZONE,
  ).split(" ");
  return TEXTOS["fundamentos.proveniencia"](
    formatDate(indicator.statement.reference_date),
    TEXTOS[`fundamentos.fonte.${indicator.statement.source}`],
    TEXTOS["risco.trilha.instante"](data, hora),
  );
}

type Props = {
  /** `/fundamentals` do ativo. */
  load: Load<Fundamentals>;
  /** A identidade (`/assets/{ticker}`): o `kind` do índice e o último pregão do preço. */
  asset: Load<AssetDetail>;
  onRetry: () => void;
};

/**
 * Os fundamentos (M1.6c, RF-05 a RF-10; camada 3): a última linha de `/fundamentals` em cinco
 * blocos, cada número com a sua frase; o nulo é "—" com o porquê de `nulos.ts`; ao lado dos
 * seis indicadores comparados, a posição entre os pares. `indicator: null` diz que não foi
 * calculado — e, no índice, por quê; enquanto a identidade carrega, a seção segue carregando
 * (RF-14, que vale para o RF-08).
 */
export function FundamentalsSection({ load, asset, onRetry }: Props) {
  const titleId = useId();
  const indicator = load.state === "ok" ? load.data.indicator : null;
  const lastPriceDate =
    asset.state === "ok" && asset.data.last_price !== null
      ? asset.data.last_price.date
      : null;

  let state: "loading" | "error" | "ready" | "empty";
  // Por que a seção está vazia, para a execução real distinguir o índice da identidade que
  // falhou: as duas frases genéricas saem iguais (`unlinked` e `not-calculated`).
  let emptyReason: "index" | "unlinked" | "not-calculated" | undefined;
  let body: ReactNode;
  if (load.state === "loading") {
    state = "loading";
  } else if (load.state === "error") {
    state = "error";
  } else if (indicator !== null) {
    state = "ready";
  } else {
    state = asset.state === "loading" ? "loading" : "empty";
  }

  if (state === "loading") {
    body = (
      <div role="status" aria-busy="true">
        <SectionSkeleton />
        <span className="ruvor-sr-only">{TEXTOS["fundamentos.carregando"]}</span>
      </div>
    );
  } else if (state === "error") {
    body = <SectionError onRetry={onRetry} />;
  } else if (indicator === null || load.state !== "ok") {
    const isIndex = asset.state === "ok" && asset.data.kind === "index";
    emptyReason = isIndex
      ? "index"
      : asset.state === "error"
        ? "unlinked"
        : "not-calculated";
    body = (
      <StatePanel
        title={TEXTOS["fundamentos.naoCalculado.titulo"]}
        text={
          isIndex
            ? TEXTOS["fundamentos.naoCalculado.indice"]
            : TEXTOS["fundamentos.naoCalculado.nota"]
        }
      />
    );
  } else {
    body = (
      <Blocks
        indicator={indicator}
        peers={load.data.peers}
        lastPriceDate={lastPriceDate}
      />
    );
  }

  return (
    <section
      className="ruvor-stack"
      data-section="fundamentals"
      data-state={state}
      data-empty-reason={state === "empty" ? emptyReason : undefined}
      aria-labelledby={titleId}
    >
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["fundamentos.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["fundamentos.titulo"]}
          </h2>
        </div>
        {state === "ready" && indicator !== null && (
          <span className="ruvor-tag ruvor-tag--evidence">{provenance(indicator)}</span>
        )}
      </div>
      <p className="ruvor-sub">{TEXTOS["fundamentos.intro"]}</p>
      <div>{body}</div>
    </section>
  );
}
