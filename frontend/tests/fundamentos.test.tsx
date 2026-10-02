/**
 * A seção Fundamentos (M1.6c, T4): RF-05 a RF-10 na tela.
 *
 * - V-07: cada campo do RF-06 com a sua frase; as frações em percentual; o preço de
 *   `price_date` no P/L; o que entra na dívida; o banco com os nulos do `account_plan`; cada
 *   motivo de nulo; `indicator: null`; os valores em reais abreviados, com a forma inteira para
 *   leitor de tela;
 * - V-08: a frase "acima de k das outras n−1" com `k` inteiro (`percentile` 0,6667 e `n` 4 dão
 *   2 de 3); a mediana; o nível subsetor e `none`; indicador sem comparação; `peers: null`;
 *   nenhuma palavra proibida;
 * - as marcas da execução real: `data-section`, `data-state`, `data-null-reason`,
 *   `data-peer-k` e `data-peer-n`.
 *
 * A seção recebe os `Load` por prop: o teste a monta direto, sem rede.
 */
import { cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../src/api/client";
import type { Load } from "../src/api/resource";
import type {
  AssetDetail,
  Fundamentals,
  Indicator,
  PeerIndicator,
  Peers,
} from "../src/api/types";
import { FundamentalsSection } from "../src/components/FundamentalsSection";
import { REASON_NULLS } from "../src/content/nulos";
import { TEXTOS } from "../src/content/textos";
import { formatCompactCurrency } from "../src/format/numbers";

afterEach(cleanup);

// ---------------------------------------------------------------- os dados

// O corpo real de /api/v1/assets/PETR4/fundamentals (2026-09-29).
const PETR4: Indicator = {
  calculated_at: "2026-09-28T08:02:59.205615-03:00",
  statement: { reference_date: "2026-06-30", source: "itr", scope: "consolidated" },
  account_plan: "general",
  scope: "consolidated",
  revenue_ttm: "548493000000.00",
  ebit_ttm: "185746000000.00",
  net_income_ttm: "133376000000.00",
  equity_parent: "480950000000.00",
  total_assets: "1279019000000.00",
  gross_debt: "366533000000.00",
  cash: "53764000000.00",
  net_debt: "312769000000.00",
  net_margin: "0.2431680988",
  ebit_margin: "0.3386478952",
  roe: "0.2773178085",
  net_debt_to_equity: "0.6503150016",
  price_date: "2026-09-25",
  close: "48.070000",
  shares_total: 12888732761,
  eps: "10.348263",
  bvps: "37.315538",
  pe: "4.645224",
  pb: "1.288203",
  per_share_missing: null,
  market_cap: null,
  market_cap_missing: "missing_class_price",
};

const NO_PEER: PeerIndicator = { median: null, percentile: null, count: null };

const PETR4_PEERS: Peers = {
  peer_level: "segment",
  group_sector: "Petróleo, Gás e Biocombustíveis",
  group_subsector: "Petróleo, Gás e Biocombustíveis",
  group_segment: "Exploração, Refino e Distribuição",
  roe: { median: "0.1125889984", percentile: "1.0000", count: 7 },
  net_margin: { median: "0.0134853183", percentile: "1.0000", count: 8 },
  ebit_margin: { median: "0.1343001814", percentile: "1.0000", count: 8 },
  net_debt_to_equity: { median: "0.6503150016", percentile: "0.5000", count: 7 },
  pe: NO_PEER,
  pb: NO_PEER,
};

// O corpo real do ITUB4: banco, com os campos do plano nulos.
const ITUB4: Indicator = {
  ...PETR4,
  account_plan: "bank",
  revenue_ttm: null,
  ebit_ttm: null,
  net_income_ttm: "46828000000.00",
  equity_parent: "217779000000.00",
  total_assets: "3202125000000.00",
  gross_debt: null,
  cash: null,
  net_debt: null,
  net_margin: null,
  ebit_margin: null,
  roe: "0.2150253238",
  net_debt_to_equity: null,
  close: "42.130001",
  shares_total: 11021872000,
  eps: "4.248643",
  bvps: "19.758803",
  pe: "9.916107",
  pb: "2.132214",
};

const ASSET: AssetDetail = {
  ticker: "PETR4",
  name: "PETROLEO BRASILEIRO S.A. PETROBRAS",
  trading_name: "PETROBRAS",
  kind: "stock",
  sector: "Petróleo, Gás e Biocombustíveis",
  status: "active",
  has_prices: true,
  subsector: "Petróleo, Gás e Biocombustíveis",
  segment: "Exploração, Refino e Distribuição",
  listing_segment: "N2",
  last_price: { date: "2026-09-28", close: "48.720001", adj_close: "48.720001" },
};

const IBOV: AssetDetail = {
  ...ASSET,
  ticker: "IBOV",
  name: "IBOVESPA",
  trading_name: "IBOVESPA",
  kind: "index",
  sector: null,
  subsector: null,
  segment: null,
  listing_segment: null,
};

const ok = <T,>(data: T): Load<T> => ({ state: "ok", data });
const LOADING = { state: "loading" } as const;
const ERROR = {
  state: "error",
  error: new ApiError(500, "internal_error", "Erro interno."),
} as const;

function body(
  indicator: Partial<Indicator> | null,
  peers: Peers | null = PETR4_PEERS,
): Fundamentals {
  return {
    ticker: "PETR4",
    indicator: indicator === null ? null : { ...PETR4, ...indicator },
    peers,
  };
}

function mount(
  load: Load<Fundamentals>,
  asset: Load<AssetDetail> = ok(ASSET),
  onRetry: () => void = () => {},
) {
  const { container } = render(
    <FundamentalsSection load={load} asset={asset} onRetry={onRetry} />,
  );
  const section = container.querySelector<HTMLElement>('[data-section="fundamentals"]');
  if (section === null) throw new Error("a seção não tem data-section");
  return section;
}

function stat(section: HTMLElement, field: string): HTMLElement {
  const el = section.querySelector<HTMLElement>(`.ruvor-stat[data-field="${field}"]`);
  if (el === null) throw new Error(`sem o número ${field}`);
  return el;
}

/** A frase do número: a primeira nota dele, fora da posição entre os pares. */
function phraseOf(section: HTMLElement, field: string): string {
  const note = stat(section, field).querySelector(":scope > .ruvor-note");
  return note?.textContent ?? "";
}

/** O que aparece na tela, sem o texto só para leitor de tela. */
function visibleValue(section: HTMLElement, field: string): string {
  const value = stat(section, field).querySelector(".ruvor-stat__value");
  if (value === null) return "";
  const hidden = value.querySelector('[aria-hidden="true"]');
  return (hidden ?? value).textContent ?? "";
}

function srValue(section: HTMLElement, field: string): string | null {
  return (
    stat(section, field).querySelector(".ruvor-stat__value .ruvor-sr-only")
      ?.textContent ?? null
  );
}

function nullMark(section: HTMLElement, field: string): string | null {
  return stat(section, field)
    .querySelector(".ruvor-stat__value")
    ?.getAttribute("data-null-reason") as string | null;
}

function peerOf(section: HTMLElement, field: string): HTMLElement | null {
  return stat(section, field).querySelector<HTMLElement>(".ruvor-peer");
}

// O Intl separa o símbolo da moeda por espaço não separável.
const normalize = (s: string): string => s.replace(/ /g, " ");

// ---------------------------------------------------------------- V-07

describe("V-07 — a seção com o dado real da PETR4", () => {
  const section = () => mount(ok(body({})));

  it("as marcas: data-section e data-state ready", () => {
    expect(section().getAttribute("data-state")).toBe("ready");
  });

  it("a proveniência no cabeçalho (RF-05)", () => {
    const tag = section().querySelector(".ruvor-section-head .ruvor-tag");
    expect(tag?.textContent).toBe(
      "balanço de 30/06/2026 (ITR), calculado em 28/09/2026 às 08:02",
    );
  });

  it("os cinco blocos, na ordem, com os dezoito números do RF-06", () => {
    const s = section();
    const titulos = [...s.querySelectorAll("h3")].map((h) => h.textContent);
    expect(titulos).toEqual([
      TEXTOS["fundamentos.bloco.resultado"],
      TEXTOS["fundamentos.bloco.rentabilidade"],
      TEXTOS["fundamentos.bloco.endividamento"],
      TEXTOS["fundamentos.bloco.porAcao"],
      TEXTOS["fundamentos.bloco.tamanho"],
    ]);
    const campos = [...s.querySelectorAll(".ruvor-stat")].map((e) =>
      e.getAttribute("data-field"),
    );
    expect(campos).toEqual([
      "revenue_ttm",
      "ebit_ttm",
      "net_income_ttm",
      "net_margin",
      "ebit_margin",
      "roe",
      "gross_debt",
      "cash",
      "net_debt",
      "net_debt_to_equity",
      "close",
      "eps",
      "bvps",
      "pe",
      "pb",
      "equity_parent",
      "total_assets",
      "market_cap",
    ]);
  });

  it("cada número presente com o seu rótulo e a sua frase", () => {
    const s = section();
    const esperado: Record<string, string> = {
      revenue_ttm: TEXTOS["fundamentos.revenue_ttm"],
      ebit_ttm: TEXTOS["fundamentos.ebit_ttm"](false),
      net_income_ttm: TEXTOS["fundamentos.net_income_ttm"](false),
      net_margin: TEXTOS["fundamentos.net_margin"]("R$ 24,32", false),
      ebit_margin: TEXTOS["fundamentos.ebit_margin"]("R$ 33,86", false),
      roe: TEXTOS["fundamentos.roe"]("R$ 27,73", false),
      gross_debt: TEXTOS["fundamentos.gross_debt"],
      cash: TEXTOS["fundamentos.cash"],
      net_debt: TEXTOS["fundamentos.net_debt"](false),
      net_debt_to_equity: TEXTOS["fundamentos.net_debt_to_equity"]("R$ 65,03", false),
      eps: TEXTOS["fundamentos.eps"]("12.888.732.761", false),
      bvps: TEXTOS["fundamentos.bvps"]("12.888.732.761"),
      pe: TEXTOS["fundamentos.pe"]("25/09/2026", "R$ 48,07", "4,6", false),
      pb: TEXTOS["fundamentos.pb"]("25/09/2026", "R$ 48,07", "1,29"),
      equity_parent: TEXTOS["fundamentos.equity_parent"](false),
      total_assets: TEXTOS["fundamentos.total_assets"],
    };
    for (const [campo, frase] of Object.entries(esperado)) {
      expect(stat(s, campo).querySelector(".ruvor-stat__label")?.textContent).toBe(
        (TEXTOS as Record<string, unknown>)[`fundamentos.rotulo.${campo}`],
      );
      expect(normalize(phraseOf(s, campo))).toBe(normalize(frase));
    }
  });

  it("as frações em percentual, o P/L e o P/VP em vezes, o preço inteiro", () => {
    const s = section();
    expect(visibleValue(s, "net_margin")).toBe("24,3%");
    expect(visibleValue(s, "ebit_margin")).toBe("33,9%");
    expect(visibleValue(s, "roe")).toBe("27,7%");
    expect(visibleValue(s, "net_debt_to_equity")).toBe("65,0%");
    expect(visibleValue(s, "pe")).toBe("4,65 vezes");
    expect(visibleValue(s, "pb")).toBe("1,29 vezes");
    expect(normalize(visibleValue(s, "close"))).toBe("R$ 48,07");
    expect(normalize(visibleValue(s, "eps"))).toBe("R$ 10,35");
  });

  it("os valores em reais abreviados, com a forma inteira só para leitor de tela", () => {
    const s = section();
    expect(visibleValue(s, "revenue_ttm")).toBe("R$ 548,5 bi");
    expect(visibleValue(s, "total_assets")).toBe("R$ 1,3 tri");
    expect(visibleValue(s, "cash")).toBe("R$ 53,8 bi");
    expect(normalize(srValue(s, "revenue_ttm") ?? "")).toBe("R$ 548.493.000.000,00");
    expect(normalize(srValue(s, "total_assets") ?? "")).toBe("R$ 1.279.019.000.000,00");
    // A razão não tem forma inteira: a visível já é a lida.
    expect(srValue(s, "net_margin")).toBeNull();
  });

  it("o P/L diz o preço usado: o fechamento de price_date", () => {
    const frase = normalize(phraseOf(section(), "pe"));
    expect(frase).toContain("com o fechamento de 25/09/2026, R$ 48,07");
  });

  it("o preço de outra data: price_date antes do último pregão da identidade", () => {
    expect(phraseOf(section(), "close")).toBe(
      TEXTOS["fundamentos.closeOutraData"]("25/09/2026", "28/09/2026"),
    );
    const mesmoDia = mount(
      ok(body({})),
      ok({
        ...ASSET,
        last_price: { date: "2026-09-25", close: "48.07", adj_close: "48.07" },
      }),
    );
    expect(phraseOf(mesmoDia, "close")).toBe(TEXTOS["fundamentos.close"]("25/09/2026"));
  });

  it("sem a identidade, a frase do preço não compara datas", () => {
    expect(phraseOf(mount(ok(body({})), ERROR), "close")).toBe(
      TEXTOS["fundamentos.close"]("25/09/2026"),
    );
  });

  it("o bloco de endividamento diz o que entra: o arrendamento e as aplicações", () => {
    const s = section();
    const notas = [...s.querySelectorAll(".ruvor-panel__note")].map(
      (n) => n.textContent,
    );
    expect(notas).toContain(TEXTOS["fundamentos.nota.endividamento"]);
    expect(TEXTOS["fundamentos.nota.endividamento"]).toMatch(/arrendamento/);
    expect(TEXTOS["fundamentos.nota.endividamento"]).toMatch(/aplicações financeiras/);
    expect(phraseOf(s, "gross_debt")).toMatch(/arrendamento/);
  });

  it("o valor de mercado nulo com o motivo real (missing_class_price)", () => {
    const s = section();
    expect(nullMark(s, "market_cap")).toBe("market_cap:missing_class_price");
    expect(phraseOf(s, "market_cap")).toBe(
      TEXTOS["fundamentos.nulo.valorMercado.missing_class_price"],
    );
    expect(visibleValue(s, "market_cap")).toBe("—");
    expect(srValue(s, "market_cap")).toBe(TEXTOS["fundamentos.semValor"]);
  });

  it("nulo não é zero: nenhum número presente leva data-null-reason", () => {
    const s = section();
    const marcados = [...s.querySelectorAll("[data-null-reason]")].map((e) =>
      e.closest(".ruvor-stat")?.getAttribute("data-field"),
    );
    expect(marcados).toEqual(["market_cap"]);
  });

  it("a nota da fonte ao pé", () => {
    expect(section().textContent).toContain(TEXTOS["fundamentos.fonteNota"]);
  });
});

describe("V-07 — o banco (ITUB4): os nulos do account_plan", () => {
  const PLANO = [
    "revenue_ttm",
    "ebit_ttm",
    "net_margin",
    "ebit_margin",
    "gross_debt",
    "cash",
    "net_debt",
    "net_debt_to_equity",
  ];

  it.each(PLANO)("%s: a frase de bancos e seguradoras", (campo) => {
    const s = mount(ok({ ticker: "ITUB4", indicator: ITUB4, peers: PETR4_PEERS }));
    expect(nullMark(s, campo)).toBe("plan:bank");
    expect(phraseOf(s, campo)).toBe(TEXTOS["fundamentos.nulo.planoFinanceiro"]);
  });

  it("o que o banco calcula aparece", () => {
    const s = mount(ok({ ticker: "ITUB4", indicator: ITUB4, peers: PETR4_PEERS }));
    expect(visibleValue(s, "roe")).toBe("21,5%");
    expect(visibleValue(s, "total_assets")).toBe("R$ 3,2 tri");
    expect(nullMark(s, "roe")).toBeNull();
  });

  it("insurance divide a frase; unknown tem a sua", () => {
    const seguradora = mount(ok(body({ ...ITUB4, account_plan: "insurance" })));
    expect(nullMark(seguradora, "revenue_ttm")).toBe("plan:insurance");
    expect(phraseOf(seguradora, "revenue_ttm")).toBe(
      TEXTOS["fundamentos.nulo.planoFinanceiro"],
    );
    cleanup();
    const desconhecido = mount(ok(body({ ...ITUB4, account_plan: "unknown" })));
    expect(nullMark(desconhecido, "revenue_ttm")).toBe("plan:unknown");
    expect(phraseOf(desconhecido, "revenue_ttm")).toBe(
      TEXTOS["fundamentos.nulo.planoDesconhecido"],
    );
  });
});

describe("V-07 — cada motivo de nulo", () => {
  const nulos = (campos: readonly string[]) =>
    Object.fromEntries(campos.map((c) => [c, null])) as Partial<Indicator>;

  it.each(Object.keys(REASON_NULLS) as Array<keyof typeof REASON_NULLS>)(
    "per_share_missing %s: a frase do motivo só no conjunto dele",
    (motivo) => {
      const conjunto = REASON_NULLS[motivo] as readonly string[];
      const s = mount(ok(body({ ...nulos(conjunto), per_share_missing: motivo })));
      for (const campo of ["close", "eps", "bvps", "pe", "pb"]) {
        if (conjunto.includes(campo)) {
          expect(nullMark(s, campo)).toBe(`per_share:${motivo}`);
          expect(phraseOf(s, campo)).toBe(
            (TEXTOS as Record<string, unknown>)[`fundamentos.nulo.porAcao.${motivo}`],
          );
        } else {
          expect(nullMark(s, campo)).toBeNull();
        }
      }
    },
  );

  it("no_price com o LPA nulo: o LPA leva a genérica, não a do motivo", () => {
    const s = mount(
      ok(
        body({
          ...nulos(REASON_NULLS.no_price),
          per_share_missing: "no_price",
          eps: null,
        }),
      ),
    );
    expect(nullMark(s, "eps")).toBe("generic");
    expect(phraseOf(s, "eps")).toBe(TEXTOS["fundamentos.nulo.generico"]);
    expect(nullMark(s, "pe")).toBe("per_share:no_price");
  });

  it.each([
    "stale_statement",
    "no_share_count",
    "share_scale_unknown",
    "ambiguous_class",
    "no_price",
    "missing_class_price",
  ])("market_cap_missing %s: só o valor de mercado recebe a frase", (motivo) => {
    const s = mount(
      ok(body({ market_cap: null, market_cap_missing: motivo, total_assets: null })),
    );
    expect(nullMark(s, "market_cap")).toBe(`market_cap:${motivo}`);
    expect(phraseOf(s, "market_cap")).toBe(
      (TEXTOS as Record<string, unknown>)[`fundamentos.nulo.valorMercado.${motivo}`],
    );
    expect(nullMark(s, "total_assets")).toBe("generic");
  });

  it("o valor de mercado presente: o número e a frase", () => {
    const s = mount(
      ok(body({ market_cap: "626283512000.00", market_cap_missing: null })),
    );
    expect(visibleValue(s, "market_cap")).toBe("R$ 626,3 bi");
    expect(phraseOf(s, "market_cap")).toBe(TEXTOS["fundamentos.market_cap"]);
  });

  it("os nulos sem motivo gravado (12 meses incompletos): a genérica", () => {
    const s = mount(ok(body({ revenue_ttm: null, net_margin: null, roe: null })));
    for (const campo of ["revenue_ttm", "net_margin", "roe"]) {
      expect(nullMark(s, campo)).toBe("generic");
      expect(phraseOf(s, campo)).toBe(TEXTOS["fundamentos.nulo.generico"]);
    }
  });
});

describe("V-07 — os negativos", () => {
  const NEG: Partial<Indicator> = {
    net_income_ttm: "-2104000000.00",
    ebit_ttm: "-310000000.00",
    net_margin: "-0.0421000000",
    ebit_margin: "-0.0062000000",
    roe: "-0.0612000000",
    eps: "-0.422500",
    pe: "-28.757396",
    close: "12.150000",
    pb: "1.050000",
    bvps: "11.571429",
    net_debt: "-8200000000.00",
    net_debt_to_equity: "-0.2400000000",
    gross_debt: "5100000000.00",
    cash: "13300000000.00",
    equity_parent: "34380000000.00",
    shares_total: 4980000000,
  };

  it("P/L negativo é mostrado, e a frase diz o que ele quer dizer", () => {
    const s = mount(ok(body(NEG)));
    expect(visibleValue(s, "pe")).toBe("−28,76 vezes");
    expect(normalize(phraseOf(s, "pe"))).toBe(
      normalize(TEXTOS["fundamentos.pe"]("25/09/2026", "R$ 12,15", "−28,8", true)),
    );
    expect(phraseOf(s, "eps")).toBe(TEXTOS["fundamentos.eps"]("4.980.000.000", true));
  });

  it("dívida líquida negativa com o menos tipográfico", () => {
    const s = mount(ok(body(NEG)));
    expect(visibleValue(s, "net_debt")).toBe("−R$ 8,2 bi");
    expect(normalize(srValue(s, "net_debt") ?? "")).toBe("−R$ 8.200.000.000,00");
    expect(phraseOf(s, "net_debt")).toBe(TEXTOS["fundamentos.net_debt"](true));
    expect(visibleValue(s, "net_debt_to_equity")).toBe("−24,0%");
    expect(phraseOf(s, "net_debt_to_equity")).toBe(
      TEXTOS["fundamentos.net_debt_to_equity"]("R$ 24,00", true),
    );
    expect(normalize(phraseOf(s, "net_margin"))).toBe(
      normalize(TEXTOS["fundamentos.net_margin"]("R$ 4,21", true)),
    );
  });
});

describe("V-07 — indicator: null, carregando e erro", () => {
  const vazio = ok<Fundamentals>({ ticker: "IBOV", indicator: null, peers: null });

  it("o índice: não calculado, e por quê", () => {
    const s = mount(vazio, ok(IBOV));
    expect(s.getAttribute("data-state")).toBe("empty");
    expect(s.textContent).toContain(TEXTOS["fundamentos.naoCalculado.titulo"]);
    expect(s.textContent).toContain(TEXTOS["fundamentos.naoCalculado.indice"]);
    expect(s.querySelector(".ruvor-stat")).toBeNull();
    expect(s.querySelector(".ruvor-section-head .ruvor-tag")).toBeNull();
  });

  it("a ação sem indicador: não calculado, sem falar de índice", () => {
    const s = mount(vazio, ok(ASSET));
    expect(s.getAttribute("data-state")).toBe("empty");
    expect(s.textContent).toContain(TEXTOS["fundamentos.naoCalculado.nota"]);
    expect(s.textContent).not.toContain(TEXTOS["fundamentos.naoCalculado.indice"]);
  });

  it("a identidade carregando: a seção segue carregando, sem afirmar nada", () => {
    const s = mount(vazio, LOADING);
    expect(s.getAttribute("data-state")).toBe("loading");
    expect(s.textContent).not.toContain(TEXTOS["fundamentos.naoCalculado.titulo"]);
  });

  it("a identidade falhou: a frase genérica, sem dizer se é índice", () => {
    const s = mount(vazio, ERROR);
    expect(s.getAttribute("data-state")).toBe("empty");
    expect(s.textContent).toContain(TEXTOS["fundamentos.naoCalculado.nota"]);
    expect(s.textContent).not.toContain(TEXTOS["fundamentos.naoCalculado.indice"]);
  });

  it("a marca data-empty-reason: index, unlinked e not-calculated", () => {
    expect(mount(vazio, ok(IBOV)).getAttribute("data-empty-reason")).toBe("index");
    cleanup();
    expect(mount(vazio, ERROR).getAttribute("data-empty-reason")).toBe("unlinked");
    cleanup();
    expect(mount(vazio, ok(ASSET)).getAttribute("data-empty-reason")).toBe(
      "not-calculated",
    );
    cleanup();
    // Fora do vazio, a marca não sai.
    expect(mount(vazio, LOADING).hasAttribute("data-empty-reason")).toBe(false);
    cleanup();
    expect(mount(ok(body({}))).hasAttribute("data-empty-reason")).toBe(false);
  });

  it("carregando: o esqueleto e o texto só para leitor de tela", () => {
    const s = mount(LOADING);
    expect(s.getAttribute("data-state")).toBe("loading");
    expect(s.querySelector('[role="status"][aria-busy="true"]')).not.toBeNull();
    expect(s.querySelector(".ruvor-sr-only")?.textContent).toBe(
      TEXTOS["fundamentos.carregando"],
    );
  });

  it("erro: o erro da seção, com tentar de novo", () => {
    const onRetry = vi.fn();
    const s = mount(ERROR, ok(ASSET), onRetry);
    expect(s.getAttribute("data-state")).toBe("error");
    expect(s.querySelector('[role="alert"]')?.textContent).toContain(
      TEXTOS["ativo.erroSecao"],
    );
    const retry = s.querySelector<HTMLButtonElement>('[role="alert"] button');
    if (retry === null) throw new Error("sem o tentar de novo");
    fireEvent.click(retry);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});

describe("V-07 — os valores em reais (formatCompactCurrency)", () => {
  it.each([
    [0, "R$ 0"],
    [950, "R$ 950"],
    [999.4, "R$ 999"],
    [999.6, "R$ 1,0 mil"],
    [12_300, "R$ 12,3 mil"],
    [46_800_000, "R$ 46,8 mi"],
    [999_940_000, "R$ 999,9 mi"],
    [999_960_000, "R$ 1,0 bi"],
    [217_800_000_000, "R$ 217,8 bi"],
    [999_960_000_000, "R$ 1,0 tri"],
    [2_700_000_000_000, "R$ 2,7 tri"],
    [1_234_500_000_000_000, "R$ 1.234,5 tri"],
    [-8_200_000_000, "−R$ 8,2 bi"],
    [-500, "−R$ 500"],
  ])("%d → %s", (valor, esperado) => {
    expect(normalize(formatCompactCurrency(valor))).toBe(esperado);
  });

  it("999,96 mi não sai 1.000,0 mi", () => {
    expect(formatCompactCurrency(999_960_000)).not.toContain("1.000,0");
  });
});

// ---------------------------------------------------------------- V-08

describe("V-08 — os pares", () => {
  it("o segmento, uma vez, no topo, com a leitura que não julga", () => {
    const s = mount(ok(body({})));
    const aviso = s.querySelector(".ruvor-state--notice");
    expect(aviso?.querySelector(".ruvor-state__title")?.textContent).toBe(
      TEXTOS["fundamentos.pares.segmento"]("Exploração, Refino e Distribuição"),
    );
    expect(aviso?.querySelector(".ruvor-state__text")?.textContent).toBe(
      TEXTOS["fundamentos.pares.leitura"],
    );
    expect(s.querySelectorAll(".ruvor-state--notice")).toHaveLength(1);
  });

  it("o sinal do aviso é duotone, dentro de .ruvor-icon (D-93)", () => {
    const s = mount(ok(body({})));
    const icone = s.querySelector(".ruvor-state--notice .ruvor-icon svg");
    // O duotone tem dois caminhos, o de fundo com opacidade.
    expect(icone?.querySelectorAll("path")).toHaveLength(2);
    expect(icone?.querySelector("path[opacity]")).not.toBeNull();
  });

  it("a posição em contagem exata, com a mediana, só nos seis indicadores", () => {
    const s = mount(ok(body({})));
    const roe = peerOf(s, "roe");
    expect(roe?.getAttribute("data-peer-k")).toBe("6");
    expect(roe?.getAttribute("data-peer-n")).toBe("6");
    expect(roe?.querySelector(".ruvor-note")?.textContent).toBe(
      `${TEXTOS["fundamentos.pares.posicao"]("6", "6")} ${TEXTOS["fundamentos.pares.mediana"]("11,3%")}`,
    );
    const divida = peerOf(s, "net_debt_to_equity");
    expect(divida?.getAttribute("data-peer-k")).toBe("3");
    expect(divida?.getAttribute("data-peer-n")).toBe("6");
    expect(divida?.textContent).toContain(TEXTOS["fundamentos.pares.mediana"]("65,0%"));
    for (const campo of ["revenue_ttm", "gross_debt", "eps", "close", "market_cap"]) {
      expect(peerOf(s, campo)).toBeNull();
    }
  });

  it("percentile 0,6667 com count 4 dá 2 de 3 — k inteiro", () => {
    const sub: Peers = {
      ...PETR4_PEERS,
      peer_level: "subsector",
      roe: { median: "0.1510000000", percentile: "0.6667", count: 4 },
    };
    const s = mount(ok(body({}, sub)));
    const roe = peerOf(s, "roe");
    expect(roe?.getAttribute("data-peer-k")).toBe("2");
    expect(roe?.getAttribute("data-peer-n")).toBe("3");
    expect(roe?.querySelector(".ruvor-note")?.textContent).toContain(
      TEXTOS["fundamentos.pares.posicao"]("2", "3"),
    );
  });

  it("k = 0: abaixo de todas as outras", () => {
    const k0: Peers = {
      ...PETR4_PEERS,
      roe: { median: "0.1125889984", percentile: "0.0000", count: 8 },
    };
    const s = mount(ok(body({ roe: "0.0310000000" }, k0)));
    const roe = peerOf(s, "roe");
    expect(roe?.getAttribute("data-peer-k")).toBe("0");
    expect(roe?.getAttribute("data-peer-n")).toBe("7");
    expect(roe?.querySelector(".ruvor-note")?.textContent).toBe(
      `${TEXTOS["fundamentos.pares.abaixoDeTodas"]("7")} ${TEXTOS["fundamentos.pares.mediana"]("11,3%")}`,
    );
    expect(roe?.textContent).not.toContain("Acima de 0");
  });

  it("a mediana do P/L em vezes", () => {
    const comPl: Peers = {
      ...PETR4_PEERS,
      pe: { median: "7.200000", percentile: "0.2500", count: 5 },
    };
    const s = mount(ok(body({}, comPl)));
    const pe = peerOf(s, "pe");
    expect(pe?.getAttribute("data-peer-k")).toBe("1");
    expect(pe?.textContent).toContain(
      TEXTOS["fundamentos.pares.mediana"]("7,20 vezes"),
    );
  });

  it("a barra: a do kit, na cor neutra, com a largura do percentil", () => {
    const s = mount(ok(body({})));
    const barra = peerOf(s, "net_debt_to_equity")?.querySelector(".ruvor-bar");
    expect(barra?.classList.contains("ruvor-bar--evidence")).toBe(true);
    expect(barra?.className).not.toMatch(/validated|review|critical/);
    expect(barra?.getAttribute("aria-hidden")).toBe("true");
    // O jsdom normaliza "50.0%" para "50%": compara o número.
    const largura =
      barra?.querySelector<HTMLElement>(".ruvor-bar__fill")?.style.width ?? "";
    expect(largura.endsWith("%")).toBe(true);
    expect(Number.parseFloat(largura)).toBe(50);
  });

  it("as três colunas nulas: sem comparação, e nenhuma posição", () => {
    const s = mount(ok(body({})));
    for (const campo of ["pe", "pb"]) {
      const peer = peerOf(s, campo);
      expect(peer?.textContent).toContain(TEXTOS["fundamentos.pares.semComparacao"]);
      expect(peer?.hasAttribute("data-peer-k")).toBe(false);
      expect(peer?.querySelector(".ruvor-bar")).toBeNull();
    }
  });

  it("menos de três no grupo: sem comparação", () => {
    const dois: Peers = {
      ...PETR4_PEERS,
      roe: { median: "0.1125889984", percentile: "1.0000", count: 2 },
    };
    const peer = peerOf(mount(ok(body({}, dois))), "roe");
    expect(peer?.textContent).toContain(TEXTOS["fundamentos.pares.semComparacao"]);
    expect(peer?.hasAttribute("data-peer-k")).toBe(false);
  });

  it("o nível subsetor: a frase de que o segmento não formou grupo", () => {
    const sub: Peers = { ...PETR4_PEERS, peer_level: "subsector" };
    const s = mount(ok(body({}, sub)));
    expect(
      s.querySelector(".ruvor-state--notice .ruvor-state__title")?.textContent,
    ).toBe(TEXTOS["fundamentos.pares.subsetor"]("Petróleo, Gás e Biocombustíveis"));
  });

  it("o nível none: a frase no topo, e cada indicador sem comparação", () => {
    const none: Peers = {
      ...PETR4_PEERS,
      peer_level: "none",
      roe: NO_PEER,
      net_margin: NO_PEER,
      ebit_margin: NO_PEER,
      net_debt_to_equity: NO_PEER,
    };
    const s = mount(ok(body({}, none)));
    expect(
      s.querySelector(".ruvor-state--notice .ruvor-state__title")?.textContent,
    ).toBe(TEXTOS["fundamentos.pares.nenhum"]);
    expect(s.querySelectorAll("[data-peer-k]")).toHaveLength(0);
    expect(s.querySelectorAll(".ruvor-peer")).toHaveLength(6);
  });

  it("peers: null com o indicador presente: a frase no topo e nenhuma posição", () => {
    const s = mount(ok(body({}, null)));
    expect(
      s.querySelector(".ruvor-state--notice .ruvor-state__title")?.textContent,
    ).toBe(TEXTOS["fundamentos.pares.indisponivel"]);
    expect(s.querySelectorAll(".ruvor-peer")).toHaveLength(0);
    expect(s.getAttribute("data-state")).toBe("ready");
  });

  it("nenhuma palavra proibida na seção, em nenhum caso", () => {
    const PROIBIDAS =
      /(?<![\p{L}\p{N}_])(melhor|melhores|pior|piores|recomendado|recomendada|recomendados|recomendadas|recomendamos|confiável|confiáveis)(?![\p{L}\p{N}_])/iu;
    const k0: Peers = {
      ...PETR4_PEERS,
      roe: { median: "0.1125889984", percentile: "0.0000", count: 8 },
    };
    const casos = [
      mount(ok(body({}))),
      mount(ok(body({}, k0))),
      mount(ok(body({}, { ...PETR4_PEERS, peer_level: "subsector" }))),
      mount(ok(body({}, null))),
      mount(ok({ ticker: "ITUB4", indicator: ITUB4, peers: PETR4_PEERS })),
    ];
    for (const s of casos) expect(s.textContent ?? "").not.toMatch(PROIBIDAS);
  });
});

// ---------------------------------------------------------------- V-02 do M1.6d

describe("V-02 do M1.6d — nenhuma região viva embrulha o corpo", () => {
  // A seção não tem andamento: o carregando é `role="status"`, e o corpo não fica dentro de
  // `aria-live`, que reanunciaria a seção inteira a cada troca de estado (RF-02).
  it.each([
    ["carregando", LOADING as Load<Fundamentals>, "loading"],
    ["pronto", ok(body({})), "ready"],
  ])("%s: nenhum elemento com aria-live", (_nome, load, estado) => {
    const s = mount(load);
    expect(s.getAttribute("data-state")).toBe(estado);
    const vivas = s.querySelectorAll("[aria-live]");
    expect(vivas).toHaveLength(0);
  });

  it("carregando: segue com role=status", () => {
    const s = mount(LOADING);
    expect(within(s).getByRole("status").textContent).toContain(
      TEXTOS["fundamentos.carregando"],
    );
  });
});
