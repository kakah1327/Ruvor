/**
 * Os momentos de estresse (T6 do M3.3): o bloco da seção Comportamento.
 *
 * - V-09, a metade do frontend: as chaves de nome **contêm** `CODIGOS_GRAVADOS`, e a união
 *   `EpisodeCode` é a mesma lista (o `typecheck` reprova o `Record` se ela mudar);
 * - V-10 (RF-12): por episódio, os três números do ativo e os três do índice, cada um com a sua
 *   frase; cada estado com a sua — os quatro motivos com o índice mostrado, o índice nulo (no
 *   IBOV, a referência), a queda zero, a recuperação nula, `stress: []` —; as marcas;
 * - V-11: nenhuma palavra proibida no `textContent` do bloco, em nenhum caso, nos dois níveis —
 *   a expressão de `fundamentos.test.tsx`, com `pior` e `piores`;
 * - V-12: o bloco é o irmão seguinte de "Maior queda"; as datas de P0 e Pn só quando diferem do
 *   recorte de calendário.
 *
 * O dado é o do mockup aprovado (`docs/mockups/M3.3/ativo-estresse.html`, a foto do `/metrics`
 * do PETR4 e do IBOV de 2026-10-02); os estados são montados sobre ele, como no mockup.
 */
import { cleanup, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type {
  EpisodeCode,
  Metric,
  StressEpisode,
  StressMissing,
} from "../src/api/types";
import { BehaviorSection } from "../src/components/BehaviorSection";
import { TEXTOS_AVANCADOS } from "../src/content/avancado";
import { TEXTOS } from "../src/content/textos";
import { formatCurrency } from "../src/format/numbers";
import type { Reading } from "../src/reading";
import { comNivel, limparNivel } from "./nivel";

// A seção monta o histograma, que importa o uPlot; o uPlot pede `matchMedia` já na importação,
// e o jsdom não tem. O desenho do gráfico é dos testes dos gráficos.
vi.mock("uplot", () => ({ default: class {} }));

afterEach(() => {
  cleanup();
  limparNivel();
});

// ---------------------------------------------------------------- V-09: os códigos

/**
 * Os códigos já gravados em `gold.stress_episode`. Quando a D-147 for restringida, esta lista
 * guarda também os aposentados; a do backend (`test_stress.py`), só os vigentes.
 */
const CODIGOS_GRAVADOS = ["jbs_2017", "truckers_2018", "covid_2020", "rates_2021"];

// O `typecheck` reprova este objeto se a união ganhar ou perder um código.
const UNIAO: Record<EpisodeCode, true> = {
  jbs_2017: true,
  truckers_2018: true,
  covid_2020: true,
  rates_2021: true,
};

describe("V-09 — os códigos dos episódios", () => {
  it("as chaves de nome contêm os códigos gravados", () => {
    const prefixo = "comportamento.estresse.episodio.";
    const chaves = Object.keys(TEXTOS)
      .filter((k) => k.startsWith(prefixo))
      .map((k) => k.slice(prefixo.length));
    expect(chaves).toEqual(expect.arrayContaining(CODIGOS_GRAVADOS));
  });

  it("a união EpisodeCode é a lista dos códigos gravados", () => {
    expect(Object.keys(UNIAO)).toEqual(CODIGOS_GRAVADOS);
  });
});

// ---------------------------------------------------------------- o dado

/** O `stress` do PETR4, real (a foto do mockup). */
const PETR4: StressEpisode[] = [
  {
    episode: "jbs_2017",
    start_date: "2017-05-17",
    end_date: "2017-06-30",
    missing: null,
    window_start_date: "2017-05-17",
    window_end_date: "2017-06-30",
    period_return: "-0.2075592805",
    drawdown: "-0.2543241517",
    drawdown_peak_date: "2017-05-17",
    drawdown_trough_date: "2017-06-21",
    recovery_date: "2017-09-20",
    recovery_sessions: 65,
    benchmark_period_return: "-0.0687000296",
    benchmark_drawdown: "-0.1003553450",
    benchmark_recovery_sessions: 33,
  },
  {
    episode: "truckers_2018",
    start_date: "2018-05-18",
    end_date: "2018-06-29",
    missing: null,
    window_start_date: "2018-05-18",
    window_end_date: "2018-06-29",
    period_return: "-0.3284841417",
    drawdown: "-0.4335671323",
    drawdown_peak_date: "2018-05-18",
    drawdown_trough_date: "2018-06-18",
    recovery_date: "2018-10-08",
    recovery_sessions: 78,
    benchmark_period_return: "-0.1242025950",
    benchmark_drawdown: "-0.1596856118",
    benchmark_recovery_sessions: 75,
  },
  {
    episode: "covid_2020",
    start_date: "2020-02-21",
    end_date: "2020-03-31",
    missing: null,
    window_start_date: "2020-02-21",
    window_end_date: "2020-03-31",
    period_return: "-0.5199036628",
    drawdown: "-0.6125597977",
    drawdown_peak_date: "2020-02-21",
    drawdown_trough_date: "2020-03-18",
    recovery_date: "2021-01-05",
    recovery_sessions: 197,
    benchmark_period_return: "-0.3576763047",
    benchmark_drawdown: "-0.4408036523",
    benchmark_recovery_sessions: 176,
  },
  {
    episode: "rates_2021",
    start_date: "2021-06-07",
    end_date: "2022-07-14",
    missing: null,
    window_start_date: "2021-06-07",
    window_end_date: "2022-07-14",
    period_return: "0.4100493710",
    drawdown: "-0.1906911236",
    drawdown_peak_date: "2022-05-23",
    drawdown_trough_date: "2022-06-24",
    recovery_date: "2022-07-29",
    recovery_sessions: 25,
    benchmark_period_return: "-0.2649951061",
    benchmark_drawdown: "-0.2649951061",
    benchmark_recovery_sessions: 355,
  },
];

/** O `stress` do IBOV, real: o índice nulo nos quatro (a própria referência). */
const IBOV: StressEpisode[] = [
  [
    "jbs_2017",
    "-0.0687000296",
    "-0.1003553450",
    "2017-05-17",
    "2017-06-21",
    "2017-08-07",
    33,
  ],
  [
    "truckers_2018",
    "-0.1242025950",
    "-0.1596856118",
    "2018-05-18",
    "2018-06-18",
    "2018-10-03",
    75,
  ],
  [
    "covid_2020",
    "-0.3576763047",
    "-0.4408036523",
    "2020-02-21",
    "2020-03-23",
    "2020-12-04",
    176,
  ],
  [
    "rates_2021",
    "-0.2649951061",
    "-0.2649951061",
    "2021-06-07",
    "2022-07-14",
    "2023-12-14",
    355,
  ],
].map(([code, ret, dd, peak, trough, rec, n], i) => ({
  ...(PETR4[i] as StressEpisode),
  episode: code as EpisodeCode,
  period_return: ret as string,
  drawdown: dd as string,
  drawdown_peak_date: peak as string,
  drawdown_trough_date: trough as string,
  recovery_date: rec as string,
  recovery_sessions: n as number,
  benchmark_period_return: null,
  benchmark_drawdown: null,
  benchmark_recovery_sessions: null,
}));

const JBS = PETR4[0] as StressEpisode;

/** O ativo sem dado: os campos do ativo nulos, o índice mantido (RF-05). */
function semDado(e: StressEpisode, missing: StressMissing): StressEpisode {
  return {
    ...e,
    missing,
    window_start_date: null,
    window_end_date: null,
    period_return: null,
    drawdown: null,
    drawdown_peak_date: null,
    drawdown_trough_date: null,
    recovery_date: null,
    recovery_sessions: null,
  };
}

const SEM_INDICE: StressEpisode = {
  ...JBS,
  benchmark_period_return: null,
  benchmark_drawdown: null,
  benchmark_recovery_sessions: null,
};

const SEM_QUEDA: StressEpisode = {
  ...JBS,
  period_return: "0.0412000000",
  drawdown: "0E-10",
  drawdown_peak_date: "2017-05-17",
  drawdown_trough_date: "2017-05-17",
  recovery_date: null,
  recovery_sessions: null,
};

/** A recuperação nula, e P0 e Pn em outro pregão que o recorte de calendário. */
const JANELA_E_SEM_VOLTA: StressEpisode = {
  ...JBS,
  window_start_date: "2017-05-16",
  window_end_date: "2017-06-29",
  recovery_date: null,
  recovery_sessions: null,
};

const MOTIVOS: StressMissing[] = [
  "starts_after",
  "stale_start",
  "ends_before",
  "no_trading",
];

/** Uma linha de métrica com o mínimo da seção: o que o bloco "Maior queda" e os outros leem. */
function metric(stress: StressEpisode[]): Metric {
  return {
    calculated_at: "2026-10-02T13:07:52-03:00",
    as_of_date: "2026-09-29",
    first_price_date: "2016-09-27",
    price_count: 2492,
    return_1m: null,
    return_3m: null,
    return_6m: null,
    return_12m: null,
    return_36m: null,
    return_60m: null,
    return_120m: null,
    return_ytd: null,
    volatility_12m: null,
    volatility_60m: null,
    max_drawdown: "-0.6335604245",
    max_drawdown_peak_date: "2020-01-06",
    max_drawdown_trough_date: "2020-03-18",
    max_drawdown_recovery_date: "2021-01-07",
    max_drawdown_recovery_sessions: 199,
    beta_60m: null,
    correlation_60m: null,
    benchmark_observations: null,
    skewness: null,
    excess_kurtosis: null,
    statistical_observations: null,
    dividends_12m: "0",
    dividend_payments_12m: 0,
    dividend_yield_12m: "0",
    avg_volume_21d: null,
    avg_volume_252d: null,
    histogram: [],
    stress,
  };
}

function montar(
  stress: StressEpisode[],
  ticker = "PETR4",
  reading: Reading = "beginner",
) {
  comNivel(reading);
  render(
    <BehaviorSection
      load={{ state: "ok", data: { ticker, metric: metric(stress) } }}
      ticker={ticker}
      onRetry={() => {}}
    />,
  );
  const block = document.querySelector<HTMLElement>('[data-block="stress"]');
  if (block === null) throw new Error("sem o bloco de estresse");
  return block;
}

const episodios = (block: HTMLElement) =>
  [...block.querySelectorAll<HTMLElement>("[data-episode]")].map(
    (e) => e.dataset.episode,
  );

/** Rótulo, número e frase de uma célula do episódio, pela medida. */
function celula(article: HTMLElement, field: string) {
  const cell = article.querySelector<HTMLElement>(`[data-field="${field}"]`);
  if (cell === null) throw new Error(`sem a célula ${field}`);
  return {
    label: cell.querySelector(".ruvor-stat__label")?.textContent,
    value: cell.querySelector(".ruvor-stat__value")?.textContent,
    phrase: cell.querySelector(".ruvor-note")?.textContent,
    cell,
  };
}

const episodio = (block: HTMLElement, code: string) =>
  block.querySelector<HTMLElement>(`[data-episode="${code}"]`) as HTMLElement;

// ---------------------------------------------------------------- V-10: com dado

describe("V-10 — o ativo com dado (PETR4, real)", () => {
  it("os quatro episódios da D-147, em ordem de data, com o nome de cada um", () => {
    const block = montar(PETR4);
    expect(episodios(block)).toEqual(CODIGOS_GRAVADOS);
    for (const code of CODIGOS_GRAVADOS) {
      const nome = TEXTOS[`comportamento.estresse.episodio.${code as EpisodeCode}`];
      expect(
        within(episodio(block, code)).getByRole("heading", { name: nome }),
      ).toBeDefined();
    }
    expect(block.querySelector("[data-missing]")).toBeNull();
    expect(block.querySelector('[data-benchmark="none"]')).toBeNull();
  });

  it("a JBS: os três números do ativo e os três do índice, cada um com a frase", () => {
    const art = episodio(montar(PETR4), "jbs_2017");
    const esperado: Record<string, [string, string]> = {
      period_return: [
        "−20,8%",
        TEXTOS["comportamento.estresse.period_return"](
          formatCurrency(79.24),
          "17/05/2017",
          "30/06/2017",
        ),
      ],
      drawdown: [
        "−25,4%",
        TEXTOS["comportamento.estresse.drawdown"](
          "25,4%",
          "17/05/2017",
          "21/06/2017",
          false,
        ),
      ],
      recovery_sessions: [
        "65",
        TEXTOS["comportamento.estresse.recovery_sessions"]("20/09/2017"),
      ],
      benchmark_period_return: [
        "−6,9%",
        TEXTOS["comportamento.estresse.benchmark_period_return"](formatCurrency(93.13)),
      ],
      benchmark_drawdown: [
        "−10,0%",
        TEXTOS["comportamento.estresse.benchmark_drawdown"]("10,0%", false),
      ],
      benchmark_recovery_sessions: [
        "33",
        TEXTOS["comportamento.estresse.benchmark_recovery_sessions"](
          TEXTOS["comportamento.estresse.pregoes"]("33"),
        ),
      ],
    };
    for (const [field, [value, phrase]] of Object.entries(esperado)) {
      const c = celula(art, field);
      expect(c.label).toBe(
        TEXTOS[`comportamento.estresse.rotulo.${field as "drawdown"}`],
      );
      expect(c.value).toBe(value);
      expect(c.phrase).toBe(phrase);
    }
  });

  it("o ciclo de juros: retorno positivo, e o índice começa no topo e termina no fundo", () => {
    const art = episodio(montar(PETR4), "rates_2021");
    expect(celula(art, "period_return").value).toBe("+41,0%");
    expect(celula(art, "drawdown").phrase).toBe(
      TEXTOS["comportamento.estresse.drawdown"](
        "19,1%",
        "23/05/2022",
        "24/06/2022",
        false,
      ),
    );
    expect(celula(art, "benchmark_drawdown").phrase).toBe(
      TEXTOS["comportamento.estresse.benchmark_drawdown"]("26,5%", true),
    );
  });

  it("na grade, ativo e índice se alternam medida a medida", () => {
    const pair = episodio(montar(PETR4), "jbs_2017").querySelector(
      ".ruvor-pair",
    ) as HTMLElement;
    expect([...pair.children].map((c) => (c as HTMLElement).dataset.field)).toEqual([
      "period_return",
      "benchmark_period_return",
      "drawdown",
      "benchmark_drawdown",
      "recovery_sessions",
      "benchmark_recovery_sessions",
    ]);
  });

  it("a nota do bloco, com dado", () => {
    const block = montar(PETR4);
    expect(
      within(block).getByText(TEXTOS["comportamento.nota.estresse"]),
    ).toBeDefined();
  });
});

// ---------------------------------------------------------------- V-10: os estados

describe("V-10 — os estados do RF-12", () => {
  it("o IBOV: o índice nulo nos quatro, como a própria referência", () => {
    const block = montar(IBOV, "IBOV");
    expect(episodios(block)).toEqual(CODIGOS_GRAVADOS);
    const nulos = block.querySelectorAll<HTMLElement>('[data-benchmark="none"]');
    expect(nulos).toHaveLength(4);
    for (const nulo of nulos) {
      expect(nulo.querySelector(".ruvor-note")?.textContent).toBe(
        TEXTOS["comportamento.nulo.referencia"],
      );
      expect(nulo.classList.contains("ruvor-pair__span--bench")).toBe(true);
    }
    // No IBOV, o ciclo de juros vai do topo (P0) ao fundo (Pn): a queda é o retorno (D-147).
    expect(celula(episodio(block, "rates_2021"), "drawdown").phrase).toBe(
      TEXTOS["comportamento.estresse.drawdown"](
        "26,5%",
        "07/06/2021",
        "14/07/2022",
        true,
      ),
    );
  });

  it.each(MOTIVOS)("o ativo sem dado (%s): o motivo, e o índice mostrado", (motivo) => {
    const block = montar([semDado(JBS, motivo)]);
    const art = episodio(block, "jbs_2017");
    expect(art.dataset.missing).toBe(motivo);
    const span = art.querySelector<HTMLElement>(".ruvor-pair__span") as HTMLElement;
    expect(span.querySelector(".ruvor-stat__label")?.textContent).toBe(
      TEXTOS["comportamento.estresse.semDado.rotulo"],
    );
    expect(span.querySelector(".ruvor-note")?.textContent).toBe(
      TEXTOS[`comportamento.estresse.semDado.${motivo}`],
    );
    // O índice continua: os três números dele, com as frases.
    expect(celula(art, "benchmark_period_return").value).toBe("−6,9%");
    expect(celula(art, "benchmark_drawdown").value).toBe("−10,0%");
    expect(celula(art, "benchmark_recovery_sessions").value).toBe("33");
    expect(art.querySelector('[data-benchmark="none"]')).toBeNull();
  });

  it("o índice nulo fora do IBOV: sem o Ibovespa neste recorte", () => {
    const art = episodio(montar([SEM_INDICE]), "jbs_2017");
    const nulo = art.querySelector<HTMLElement>(
      '[data-benchmark="none"]',
    ) as HTMLElement;
    expect(nulo.querySelector(".ruvor-note")?.textContent).toBe(
      TEXTOS["comportamento.estresse.semIbov"],
    );
    expect(celula(art, "period_return").value).toBe("−20,8%");
  });

  it("a queda zero: sem queda e nada a recuperar", () => {
    const art = episodio(montar([SEM_QUEDA]), "jbs_2017");
    expect(celula(art, "drawdown").value).toBe("0,0%");
    expect(celula(art, "drawdown").phrase).toBe(
      TEXTOS["comportamento.estresse.semQueda"],
    );
    expect(celula(art, "recovery_sessions").value).toBe("—");
    expect(celula(art, "recovery_sessions").phrase).toBe(
      TEXTOS["comportamento.estresse.nadaARecuperar"],
    );
  });

  it("a recuperação nula: ainda não recuperou", () => {
    const art = episodio(montar([JANELA_E_SEM_VOLTA]), "jbs_2017");
    expect(celula(art, "recovery_sessions").value).toBe("—");
    expect(celula(art, "recovery_sessions").phrase).toBe(
      TEXTOS["comportamento.nulo.naoRecuperou"],
    );
  });

  it("stress: [] — ainda não calculado, sem nota e sem episódio", () => {
    const block = montar([]);
    expect(
      within(block).getByText(TEXTOS["comportamento.estresse.naoCalculado"]),
    ).toBeDefined();
    expect(within(block).queryByText(TEXTOS["comportamento.nota.estresse"])).toBeNull();
    expect(episodios(block)).toEqual([]);
  });
});

// ---------------------------------------------------------------- V-12: a posição e as datas

describe("V-12 — a posição e as datas", () => {
  it("o bloco abre os recolhidos, logo depois de Maior queda", () => {
    const block = montar(PETR4);
    const more = block.parentElement as HTMLElement;
    expect(more.classList.contains("ruvor-blocks__more")).toBe(true);
    expect(more.firstElementChild).toBe(block);
    const anterior = more.previousElementSibling as HTMLElement;
    expect(anterior.querySelector("h3")?.textContent).toBe(
      TEXTOS["comportamento.bloco.queda"],
    );
  });

  it("com P0 e Pn no recorte, só o recorte de calendário", () => {
    const art = episodio(montar(PETR4), "jbs_2017");
    expect(art.querySelector(".ruvor-episode__dates")?.textContent).toBe(
      TEXTOS["comportamento.estresse.recorte"]("17/05/2017", "30/06/2017"),
    );
  });

  it("com P0 e Pn em outro pregão, o recorte e as datas da janela", () => {
    const art = episodio(montar([JANELA_E_SEM_VOLTA]), "jbs_2017");
    expect(art.querySelector(".ruvor-episode__dates")?.textContent).toBe(
      `${TEXTOS["comportamento.estresse.recorte"]("17/05/2017", "30/06/2017")} · ${TEXTOS[
        "comportamento.estresse.janela"
      ]("16/05/2017", "29/06/2017")}`,
    );
    // E a frase do retorno usa as datas de P0 e Pn, não as do recorte.
    expect(celula(art, "period_return").phrase).toBe(
      TEXTOS["comportamento.estresse.period_return"](
        formatCurrency(79.24),
        "16/05/2017",
        "29/06/2017",
      ),
    );
  });
});

// ---------------------------------------------------------------- a leitura avançada

describe("D-152 — as seis frases de medida na leitura avançada", () => {
  it("a avançada substitui a iniciante, com os mesmos argumentos; o número não muda", () => {
    const art = episodio(montar(PETR4, "PETR4", "advanced"), "jbs_2017");
    expect(celula(art, "period_return").value).toBe("−20,8%");
    expect(celula(art, "period_return").phrase).toBe(
      TEXTOS_AVANCADOS["comportamento.estresse.period_return"](
        formatCurrency(79.24),
        "17/05/2017",
        "30/06/2017",
      ),
    );
    expect(celula(art, "benchmark_recovery_sessions").phrase).toBe(
      TEXTOS_AVANCADOS["comportamento.estresse.benchmark_recovery_sessions"](
        TEXTOS["comportamento.estresse.pregoes"]("33"),
      ),
    );
  });
});

// ---------------------------------------------------------------- V-11: o vocabulário

/** As palavras de `vocabulario.test.ts` mais `pior` e `piores` — a de `fundamentos.test.tsx`. */
const PROIBIDAS =
  /(?<![\p{L}\p{N}_])(melhor|melhores|pior|piores|recomendado|recomendada|recomendados|recomendadas|recomendamos|confiável|confiáveis)(?![\p{L}\p{N}_])/iu;

const CASOS: [string, StressEpisode[], string][] = [
  ["com dado", PETR4, "PETR4"],
  ["o IBOV", IBOV, "IBOV"],
  ...MOTIVOS.map((m): [string, StressEpisode[], string] => [
    m,
    [semDado(JBS, m)],
    "PETR4",
  ]),
  ["índice nulo", [SEM_INDICE], "PETR4"],
  ["sem queda", [SEM_QUEDA], "PETR4"],
  ["janela e sem volta", [JANELA_E_SEM_VOLTA], "PETR4"],
  ["stress: []", [], "PETR4"],
];

describe("V-11 — nenhuma palavra proibida no bloco, em nenhum caso", () => {
  for (const reading of ["beginner", "advanced"] as const) {
    it.each(CASOS)(`%s (${reading})`, (_nome, stress, ticker) => {
      const texto = montar(stress, ticker, reading).textContent ?? "";
      expect(texto.trim()).not.toBe("");
      expect(PROIBIDAS.exec(texto)?.[0] ?? null).toBeNull();
    });
  }
});
