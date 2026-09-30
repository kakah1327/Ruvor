/**
 * Os tipos das respostas de /api/v1/ — o contrato é o de backend/apps/api/serializers.py.
 *
 * Decimal chega como string (o padrão do DRF, D-86) e é convertido por Number() só na hora
 * de formatar ou calcular. Data (AAAA-MM-DD) e instante (ISO com deslocamento) chegam como
 * string.
 */

/** Decimal da API. */
export type Dec = string;

/** A ordem fixa dos modelos (RF-15): a da tabela, da lista dos não rejeitados e da faixa. */
export const MODEL_ORDER = [
  "historical",
  "parametric",
  "monte_carlo",
  "garch_1_1",
  "egarch",
  "lstm",
  "gru",
  "garchnet",
  "caviar",
] as const;

export type ModelName =
  | "historical"
  | "parametric"
  | "monte_carlo"
  | "garch_1_1"
  | "egarch"
  | "lstm"
  | "gru"
  | "garchnet"
  | "caviar";

export type AssetItem = {
  ticker: string;
  name: string;
  trading_name: string;
  kind: "stock" | "index";
  sector: string | null;
  status: "active" | "inactive";
  has_prices: boolean;
};

export type AssetPage = {
  count: number;
  limit: number;
  offset: number;
  results: AssetItem[];
};

export type AssetDetail = AssetItem & {
  subsector: string | null;
  segment: string | null;
  listing_segment: string | null;
  last_price: { date: string; close: Dec; adj_close: Dec } | null;
};

export type PriceRow = {
  date: string;
  open: Dec;
  high: Dec;
  low: Dec;
  close: Dec;
  adj_close: Dec;
  volume: number;
};

export type Prices = {
  ticker: string;
  from: string | null;
  to: string | null;
  results: PriceRow[];
};

export type EventRow = {
  date: string;
  kind: "dividend" | "split";
  amount: Dec | null;
  numerator: Dec | null;
  denominator: Dec | null;
};

export type Events = { ticker: string; results: EventRow[] };

export type HistogramBin = {
  bin_index: number;
  lower_bound: Dec | null;
  upper_bound: Dec | null;
  count: number;
};

/** A linha de métrica: o cabeçalho, as 26 colunas de METRIC_COLUMNS, na ordem, e os baldes. */
export type Metric = {
  calculated_at: string;
  as_of_date: string;
  first_price_date: string;
  price_count: number;
  return_1m: Dec | null;
  return_3m: Dec | null;
  return_6m: Dec | null;
  return_12m: Dec | null;
  return_36m: Dec | null;
  return_60m: Dec | null;
  return_120m: Dec | null;
  return_ytd: Dec | null;
  volatility_12m: Dec | null;
  volatility_60m: Dec | null;
  max_drawdown: Dec | null;
  max_drawdown_peak_date: string | null;
  max_drawdown_trough_date: string | null;
  max_drawdown_recovery_date: string | null;
  max_drawdown_recovery_sessions: number | null;
  beta_60m: Dec | null;
  correlation_60m: Dec | null;
  benchmark_observations: number | null;
  skewness: Dec | null;
  excess_kurtosis: Dec | null;
  statistical_observations: number | null;
  dividends_12m: Dec;
  dividend_payments_12m: number;
  dividend_yield_12m: Dec;
  avg_volume_21d: Dec | null;
  avg_volume_252d: Dec | null;
  histogram: HistogramBin[];
};

export type Metrics = { ticker: string; metric: Metric | null };

export type RiskResult = {
  model_name: ModelName;
  model_category: "traditional" | "garch" | "ml";
  alpha: "0.0500" | "0.0100";
  hyperparameters: Record<string, unknown>;
  var_latest: Dec | null;
  var_mean: Dec | null;
  violations: number | null;
  expected_violations: Dec | null;
  kupiec_passed: boolean | null;
  kupiec_p_value: Dec | null;
  christoffersen_passed: boolean | null;
  christoffersen_p_value: Dec | null;
  dq_passed: boolean | null;
  dq_p_value: Dec | null;
  /** Chega e não é mostrada (RF-15). */
  basel_zone: string | null;
  adequate: boolean | null;
  error: string;
  reused_snapshots: number | null;
  trained_snapshots: number | null;
};

export type RiskRun = {
  id: number;
  calculated_at: string;
  finished_at: string | null;
  status: "ok" | "partial" | "failed";
  engine_version: string;
  seed: number;
  train_window_days: number;
  as_of_date: string;
  first_price_date: string;
  price_count: number;
  train_count: number;
  test_count: number;
  // `gold.risk_run.price_run` é chave estrangeira sem `null=True`: o serializer nunca o
  // manda nulo.
  price_run: {
    id: number;
    source: string;
    started_at: string;
    finished_at: string | null;
  };
  requested_models: string[];
  full_recompute: boolean;
  results: RiskResult[];
};

export type InProgress = {
  id: number;
  calculated_at: string;
  requested_models: string[];
  results_written: number;
  results_expected: number;
};

export type ComputeRequest = {
  id: number;
  status: "queued" | "running" | "done" | "failed" | "expired";
  requested_at: string;
  finished_at: string | null;
  reason: string;
  error: string;
  risk_run_id: number | null;
};

export type Risk = {
  ticker: string;
  covered: boolean;
  latest: RiskRun | null;
  in_progress: InProgress | null;
  request: ComputeRequest | null;
};

/** O plano de contas do balanço (`AccountPlan` em `backend/apps/fundamentals/models.py`). */
export type AccountPlan = "general" | "bank" | "insurance" | "unknown";

/**
 * A linha de `gold.fundamental_indicator` (M1.6c, RF-02), com os nomes das colunas.
 * `per_share_missing` e `market_cap_missing` são texto livre no banco (sem `choices`): um
 * valor fora das listas de `content/nulos.ts` cai na frase genérica (RF-07).
 */
export type Indicator = {
  calculated_at: string;
  statement: {
    reference_date: string;
    source: "itr" | "dfp";
    scope: "consolidated" | "individual";
  };
  account_plan: AccountPlan;
  scope: "consolidated" | "individual";
  revenue_ttm: Dec | null;
  ebit_ttm: Dec | null;
  net_income_ttm: Dec | null;
  equity_parent: Dec | null;
  total_assets: Dec | null;
  gross_debt: Dec | null;
  cash: Dec | null;
  net_debt: Dec | null;
  net_margin: Dec | null;
  ebit_margin: Dec | null;
  roe: Dec | null;
  net_debt_to_equity: Dec | null;
  price_date: string | null;
  close: Dec | null;
  shares_total: number | null;
  eps: Dec | null;
  bvps: Dec | null;
  pe: Dec | null;
  pb: Dec | null;
  per_share_missing: string | null;
  market_cap: Dec | null;
  market_cap_missing: string | null;
};

/** A posição de um indicador entre os pares: as três colunas `{ind}_*`, agrupadas. */
export type PeerIndicator = {
  median: Dec | null;
  percentile: Dec | null;
  count: number | null;
};

/** Os seis indicadores comparados com os pares (M3.2), na ordem de `PeersOut`. */
export const PEER_INDICATORS = [
  "roe",
  "net_margin",
  "ebit_margin",
  "net_debt_to_equity",
  "pe",
  "pb",
] as const;

export type PeerIndicatorName = (typeof PEER_INDICATORS)[number];

/** A comparação do próprio indicador com os pares (`gold.peer_comparison`). */
export type Peers = {
  peer_level: "segment" | "subsector" | "none";
  group_sector: string | null;
  group_subsector: string | null;
  group_segment: string | null;
} & Record<PeerIndicatorName, PeerIndicator>;

/** `GET /api/v1/assets/{ticker}/fundamentals`. */
export type Fundamentals = {
  ticker: string;
  indicator: Indicator | null;
  peers: Peers | null;
};

/** As três categorias de comunicado (`Disclosure.Category`), na ordem do filtro. */
export const DISCLOSURE_CATEGORIES = [
  "fato_relevante",
  "comunicado",
  "aviso_acionistas",
] as const;

export type DisclosureCategory = (typeof DISCLOSURE_CATEGORIES)[number];

/** Um documento de `silver.disclosure` (M1.6c, RF-03); `link` é a identidade (D-131). */
export type DisclosureItem = {
  delivered_on: string;
  reference_date: string | null;
  category: DisclosureCategory;
  kind: string;
  species: string;
  title: string;
  link: string;
};

/** `GET /api/v1/assets/{ticker}/disclosures`; `company` é nulo sem `code_cvm` no catálogo. */
export type Disclosures = {
  ticker: string;
  company: { code_cvm: string; name: string | null } | null;
  count: number;
  limit: number;
  offset: number;
  results: DisclosureItem[];
};
