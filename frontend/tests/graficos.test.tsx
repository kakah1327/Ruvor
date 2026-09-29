/**
 * V-15 — os gráficos (RF-08, RF-11, RF-22).
 *
 * O uPlot é substituído por um duplo (`vi.mock("uplot")`): o jsdom não tem `<canvas>`, e o
 * que se confere é o que o invólucro **passa** ao uPlot. Cada token recebe no
 * `documentElement` um valor distinto, e cada opção da tabela do plano (O mapa de cor do
 * uPlot) tem de chegar com o valor do seu token — pelo nome, não por posição nem por cor
 * fixa. A troca de tema destrói o gráfico e o recria com as cores relidas.
 *
 * E os seletores do `app.css` que cobrem as três regras de cor fixa da folha do uPlot: a
 * árvore que o uPlot 1.6.32 gera é montada no jsdom, e cada seletor tem de casar com o seu
 * elemento — `.uplot.u-hz` é composto, porque o uPlot põe as duas classes no mesmo raiz.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type uPlot from "uplot";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { HistogramBin, PriceRow } from "../src/api/types";
import { PriceChart } from "../src/components/PriceChart";
import { binRange, ReturnsHistogram } from "../src/components/ReturnsHistogram";
import { TEXTOS } from "../src/content/textos";
import {
  formatCurrency,
  formatCurrencyWhole,
  formatSignedPercent,
  typographicMinus,
} from "../src/format/numbers";
import { setTheme } from "../src/theme";

// ---------------------------------------------------------------- o duplo do uPlot

type Hook = (self: FakeChart) => void;

type FakeChart = {
  opts: uPlot.Options;
  data: uPlot.AlignedData;
  target: HTMLElement;
  root: HTMLDivElement;
  over: HTMLDivElement;
  destroyed: boolean;
  cursor: { idx: number | null; left: number };
  select: { left: number; top: number; width: number; height: number };
  scales: { x: { min?: number; max?: number } };
  setScale: ReturnType<typeof vi.fn>;
  setSize: ReturnType<typeof vi.fn>;
  valToPos: (value: number) => number;
  posToVal: (pos: number) => number;
  destroy: () => void;
};

const mock = vi.hoisted(() => {
  const instances: FakeChart[] = [];
  const bars = { kind: "bars" };
  class FakeUPlot {
    static paths = { bars: () => bars };
    static tzDate = (date: Date) => date;
    opts: uPlot.Options;
    data: uPlot.AlignedData;
    target: HTMLElement;
    root: HTMLDivElement;
    over: HTMLDivElement;
    destroyed = false;
    cursor = { idx: null as number | null, left: -1 };
    select = { left: 0, top: 0, width: 0, height: 0 };
    scales = { x: {} };
    setScale = vi.fn();
    setSize = vi.fn();
    constructor(opts: uPlot.Options, data: uPlot.AlignedData, target: HTMLElement) {
      this.opts = opts;
      this.data = data;
      this.target = target;
      this.root = document.createElement("div");
      this.over = document.createElement("div");
      this.root.appendChild(this.over);
      target.appendChild(this.root);
      instances.push(this as unknown as FakeChart);
    }
    valToPos = (value: number) => value * 10;
    posToVal = (pos: number) => pos * 1000;
    destroy() {
      this.destroyed = true;
      this.root.remove();
    }
  }
  return { instances, bars, FakeUPlot };
});

vi.mock("uplot", () => ({ default: mock.FakeUPlot }));

// ---------------------------------------------------------------- os tokens

// Um valor distinto por token: a opção que ler o token errado cai no valor errado.
const TOKENS = {
  evidence: "tok-evidence",
  critical: "tok-critical",
  surface: "tok-surface",
  ink: "tok-ink",
  "text-muted": "tok-text-muted",
  "table-rule": "tok-table-rule",
  "font-sans": "tok-font-sans",
  "type-micro-size": "tok-micro",
} as const;

function setTokens(prefix: string): void {
  for (const [name, value] of Object.entries(TOKENS)) {
    document.documentElement.style.setProperty(`--ruvor-${name}`, `${prefix}${value}`);
  }
}

function clearTokens(): void {
  for (const name of Object.keys(TOKENS)) {
    document.documentElement.style.removeProperty(`--ruvor-${name}`);
  }
}

beforeEach(() => {
  mock.instances.length = 0;
  setTokens("");
});

afterEach(() => {
  cleanup();
  clearTokens();
  act(() => setTheme("system"));
  window.localStorage.clear();
});

// ---------------------------------------------------------------- os dados

function priceRows(n: number): PriceRow[] {
  const start = Date.UTC(2016, 0, 4);
  return Array.from({ length: n }, (_, i) => {
    const date = new Date(start + i * 86400000).toISOString().slice(0, 10);
    const close = (20 + (i % 7) + i / 100).toFixed(4);
    return {
      date,
      open: close,
      high: close,
      low: close,
      close,
      adj_close: close,
      volume: 1000,
    };
  });
}

// Os 42 baldes do backend: a ponta de baixo, 40 faixas de 0,5 ponto, a ponta de cima.
function bins(): HistogramBin[] {
  return Array.from({ length: 42 }, (_, i) => {
    const lower = i === 0 ? null : (-0.1 + (i - 1) * 0.005).toFixed(4);
    const upper = i === 41 ? null : (-0.1 + i * 0.005).toFixed(4);
    return {
      bin_index: i,
      lower_bound: lower,
      upper_bound: upper,
      count: i === 22 ? 90 : i,
    };
  });
}

function hookOf(c: FakeChart, name: "setCursor" | "setSelect"): Hook {
  const found = c.opts.hooks?.[name]?.[0];
  if (found === undefined) throw new Error(`sem o gancho ${name}`);
  return found as unknown as Hook;
}

function chart(index = 0): FakeChart {
  const found = mock.instances[index];
  if (found === undefined) throw new Error(`sem o gráfico ${index}`);
  return found;
}

type AnySeries = uPlot.Series & { points?: { stroke?: unknown; fill?: unknown } };

function series(c: FakeChart, i: number): AnySeries {
  return c.opts.series[i] as AnySeries;
}

// ---------------------------------------------------------------- o mapa de cor

function expectAxesAndCursor(c: FakeChart, prefix = ""): void {
  const axes = c.opts.axes ?? [];
  expect(axes).toHaveLength(2);
  for (const axis of axes) {
    expect(axis.stroke).toBe(`${prefix}tok-text-muted`);
    expect(axis.grid?.stroke).toBe(`${prefix}tok-table-rule`);
    expect(axis.ticks?.stroke).toBe(`${prefix}tok-table-rule`);
    expect(axis.font).toBe(`${prefix}tok-micro ${prefix}tok-font-sans`);
  }
  const points = c.opts.cursor?.points;
  expect(points?.stroke).toBe(`${prefix}tok-ink`);
  expect(points?.fill).toBe(`${prefix}tok-surface`);
  for (let i = 1; i < c.opts.series.length; i += 1) {
    expect(series(c, i).points?.fill).toBe(`${prefix}tok-surface`);
  }
}

describe("V-15 — o mapa de cor do uPlot: cada opção pelo nome do token", () => {
  it("o preço: série, pontos, eixos, cursor e fonte", () => {
    render(<PriceChart rows={priceRows(30)} />);
    const c = chart();
    const price = series(c, 1);
    expect(price.stroke).toBe("tok-evidence");
    expect(price.points?.stroke).toBe("tok-evidence");
    // Sem preenchimento, e a opção passada explicitamente.
    expect(Object.hasOwn(price, "fill")).toBe(true);
    expect(price.fill).toBeUndefined();
    expectAxesAndCursor(c);
  });

  it("o histograma: queda em critical, alta em evidence, eixos, cursor e fonte", () => {
    render(<ReturnsHistogram bins={bins()} observations={1200} />);
    const c = chart();
    const [neg, pos] = [series(c, 1), series(c, 2)];
    expect([neg.fill, neg.stroke, neg.points?.stroke]).toEqual([
      "tok-critical",
      "tok-critical",
      "tok-critical",
    ]);
    expect([pos.fill, pos.stroke, pos.points?.stroke]).toEqual([
      "tok-evidence",
      "tok-evidence",
      "tok-evidence",
    ]);
    expect(neg.paths).toBe(mock.bars);
    expect(pos.paths).toBe(mock.bars);
    expectAxesAndCursor(c);
  });

  it("a troca de tema destrói o gráfico e o recria com as cores relidas", () => {
    render(
      <>
        <PriceChart rows={priceRows(30)} />
        <ReturnsHistogram bins={bins()} observations={1200} />
      </>,
    );
    expect(mock.instances).toHaveLength(2);
    setTokens("escuro-");
    act(() => setTheme("dark"));
    expect(mock.instances).toHaveLength(4);
    expect(chart(0).destroyed).toBe(true);
    expect(chart(1).destroyed).toBe(true);
    expect(chart(0).root.isConnected).toBe(false);
    const [price, hist] = [chart(2), chart(3)];
    expect(price.destroyed || hist.destroyed).toBe(false);
    expect(series(price, 1).stroke).toBe("escuro-tok-evidence");
    expect(series(hist, 1).fill).toBe("escuro-tok-critical");
    expectAxesAndCursor(price, "escuro-");
    expectAxesAndCursor(hist, "escuro-");
  });

  it("desmontado, destrói e deixa de ouvir o tema", () => {
    const { unmount } = render(<PriceChart rows={priceRows(30)} />);
    unmount();
    expect(chart(0).destroyed).toBe(true);
    act(() => setTheme("dark"));
    expect(mock.instances).toHaveLength(1);
  });

  it("a largura acompanha o contêiner pelo ResizeObserver", () => {
    const observers: Array<() => void> = [];
    vi.stubGlobal(
      "ResizeObserver",
      class {
        constructor(cb: () => void) {
          observers.push(cb);
        }
        observe() {}
        disconnect() {}
      },
    );
    try {
      render(<PriceChart rows={priceRows(30)} />);
      expect(observers).toHaveLength(1);
      observers[0]();
      expect(chart().setSize).toHaveBeenCalledWith({ width: 0, height: 260 });
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

// ---------------------------------------------------------------- o preço (RF-08)

describe("RF-08 — o gráfico do preço", () => {
  const rows = priceRows(3000);
  const xs = rows.map((r) => Date.parse(`${r.date}T00:00:00Z`) / 1000);
  const last = xs.length - 1;

  const pressed = (): string[] =>
    screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-pressed") === "true")
      .map((b) => b.textContent ?? "");

  it("o resumo é a alternativa em texto, e a leitura começa no último pregão", () => {
    render(<PriceChart rows={priceRows(3)} />);
    const img = screen.getByRole("img");
    expect(img.className).toBe("ruvor-chart");
    // Os três pregões: 20, 21,01 e 22,02 — o mínimo no primeiro, o máximo no último.
    const resumo = TEXTOS["grafico.resumoPreco"](
      "04/01/2016",
      "06/01/2016",
      formatCurrency(20),
      "04/01/2016",
      formatCurrency(22.02),
      "06/01/2016",
      formatCurrency(22.02),
    );
    expect(img.getAttribute("aria-label")).toBe(resumo);
    expect(document.querySelector(".ruvor-chart__summary")?.textContent).toBe(resumo);
    expect(document.querySelector(".ruvor-chart__readout")?.textContent).toBe(
      TEXTOS["grafico.dicaPreco"]("06/01/2016", formatCurrency(22.02)),
    );
  });

  it("os atalhos 1 ano, 5 anos e tudo mudam a escala e o marcado", () => {
    render(<PriceChart rows={rows} />);
    const c = chart();
    expect(pressed()).toEqual([TEXTOS["grafico.atalho.tudo"]]);
    fireEvent.click(screen.getByRole("button", { name: TEXTOS["grafico.atalho.1a"] }));
    expect(c.setScale).toHaveBeenLastCalledWith("x", {
      min: xs[last] - 365.25 * 86400,
      max: xs[last],
    });
    expect(pressed()).toEqual([TEXTOS["grafico.atalho.1a"]]);
    fireEvent.click(screen.getByRole("button", { name: TEXTOS["grafico.atalho.5a"] }));
    expect(c.setScale).toHaveBeenLastCalledWith("x", {
      min: xs[last] - 5 * 365.25 * 86400,
      max: xs[last],
    });
    fireEvent.click(
      screen.getByRole("button", { name: TEXTOS["grafico.atalho.tudo"] }),
    );
    expect(c.setScale).toHaveBeenLastCalledWith("x", { min: xs[0], max: xs[last] });
    expect(screen.getByRole("group").getAttribute("aria-label")).toBe(
      TEXTOS["grafico.atalhos"],
    );
  });

  it("o arrasto desmarca os atalhos, e o duplo clique volta a tudo", () => {
    render(<PriceChart rows={rows} />);
    const c = chart();
    c.select = { left: 2, top: 0, width: 3, height: 100 };
    act(() => hookOf(c, "setSelect")(c));
    expect(pressed()).toEqual([]);
    // Recriado pelo tema, o gráfico volta à janela arrastada.
    act(() => setTheme("dark"));
    expect(chart(1).setScale).toHaveBeenLastCalledWith("x", { min: 2000, max: 5000 });
    fireEvent.doubleClick(chart(1).over);
    expect(pressed()).toEqual([TEXTOS["grafico.atalho.tudo"]]);
  });

  it("a leitura de data e preço segue o cursor", () => {
    render(<PriceChart rows={priceRows(3)} />);
    const c = chart();
    c.cursor = { idx: 0, left: 5 };
    act(() => hookOf(c, "setCursor")(c));
    expect(document.querySelector(".ruvor-chart__readout")?.textContent).toBe(
      TEXTOS["grafico.dicaPreco"]("04/01/2016", formatCurrency(20)),
    );
  });

  it("os rótulos do eixo do preço, em reais sem centavos", () => {
    render(<PriceChart rows={priceRows(3)} />);
    const axis = chart().opts.axes?.[1];
    const values = axis?.values as (self: unknown, splits: number[]) => string[];
    expect(values(null, [20, 1234.5]).map((s) => s.replace(/\s/g, " "))).toEqual([
      "R$ 20",
      "R$ 1.235",
    ]);
  });

  it("sem preço, a área vazia com a frase, e nenhum gráfico", () => {
    render(<PriceChart rows={[]} />);
    expect(mock.instances).toHaveLength(0);
    expect(document.querySelector(".ruvor-chart__empty")?.textContent).toBe(
      `${TEXTOS["ativo.preco.vazio"]}${TEXTOS["ativo.preco.vazio.nota"]}`,
    );
  });
});

// ---------------------------------------------------------------- o histograma (RF-11)

describe("RF-11 — o histograma dos retornos", () => {
  it("as duas séries: a queda só nos baldes até zero, a alta no resto", () => {
    render(<ReturnsHistogram bins={bins()} observations={1200} />);
    const [xs, neg, pos] = chart().data as [
      number[],
      (number | null)[],
      (number | null)[],
    ];
    expect(xs).toHaveLength(42);
    // Baldes 0 a 20 terminam em até 0 (o 20 é de −0,5% a 0%): queda.
    expect(neg.slice(0, 21).every((v) => v !== null)).toBe(true);
    expect(neg.slice(21).every((v) => v === null)).toBe(true);
    expect(pos.slice(0, 21).every((v) => v === null)).toBe(true);
    expect(pos.slice(21).every((v) => v !== null)).toBe(true);
  });

  it("a dica por barra tem a faixa e a contagem; a ponta aberta, pelo nome", () => {
    render(<ReturnsHistogram bins={bins()} observations={1200} />);
    const c = chart();
    const tip = c.over.querySelector(".ruvor-chart__tip") as HTMLElement;
    expect(tip.hidden).toBe(true);
    expect(tip.getAttribute("aria-hidden")).toBe("true");
    const hook = hookOf(c, "setCursor");

    c.cursor = { idx: 1, left: 10 };
    hook(c);
    expect(tip.hidden).toBe(false);
    expect(tip.textContent).toBe(TEXTOS["grafico.dicaBarra"]("de −10,0% a −9,5%", 1));

    c.cursor = { idx: 0, left: 10 };
    hook(c);
    expect(tip.textContent).toBe(
      TEXTOS["grafico.dicaBarra"](TEXTOS["grafico.pontaInferior"], 0),
    );

    c.cursor = { idx: 41, left: 10 };
    hook(c);
    expect(tip.textContent).toBe(
      TEXTOS["grafico.dicaBarra"](TEXTOS["grafico.pontaSuperior"], 41),
    );

    c.cursor = { idx: null, left: -10 };
    hook(c);
    expect(tip.hidden).toBe(true);
  });

  it("o resumo, a legenda, as pontas e os rótulos do eixo", () => {
    render(<ReturnsHistogram bins={bins()} observations={1200} />);
    const resumo = TEXTOS["grafico.resumoHistograma"]("de 0,5% a 1,0%", "90", 0, 41);
    expect(screen.getByRole("img").getAttribute("aria-label")).toBe(resumo);
    expect(document.querySelector(".ruvor-chart__summary")?.textContent).toBe(resumo);
    expect(document.querySelector(".ruvor-legend")?.textContent).toBe(
      `${TEXTOS["grafico.legendaQueda"]}${TEXTOS["grafico.legendaAlta"]}`,
    );
    expect(document.querySelector(".ruvor-chart__ends")?.textContent).toBe(
      `← ${TEXTOS["grafico.pontaInferior"]}${TEXTOS["grafico.pontaSuperior"]} →`,
    );
    const values = chart().opts.axes?.[0].values as () => string[];
    expect(values()).toEqual(["−10%", "−5%", "0%", "+5%", "+10%"]);
  });

  it("a série curta mostra a frase no lugar do gráfico", () => {
    render(<ReturnsHistogram bins={bins()} observations={null} />);
    expect(mock.instances).toHaveLength(0);
    expect(screen.getByText(TEXTOS["comportamento.histogramaCurto"])).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
  });

  it("binRange usa o menos tipográfico", () => {
    expect(binRange(bins()[20])).toBe(TEXTOS["grafico.faixa"]("−0,5%", "0,0%"));
  });
});

describe("os formatos dos gráficos", () => {
  it("menos tipográfico, percentual com sinal e reais sem centavos", () => {
    expect(typographicMinus("-0,5%")).toBe("−0,5%");
    expect(typographicMinus("0,5%")).toBe("0,5%");
    expect(formatSignedPercent(0.05, 0)).toBe("+5%");
    expect(formatSignedPercent(-0.05, 0)).toBe("−5%");
    expect(formatSignedPercent(0, 0)).toBe("0%");
    expect(formatCurrencyWhole(19.6).replace(/\s/g, " ")).toBe("R$ 20");
  });
});

// ---------------------------------------------------------------- os seletores do app.css

const APP_CSS = join(process.cwd(), "src", "app.css");

type Rule = { selectors: string[]; declarations: Array<[string, string]> };

// As regras do app.css que tocam o uPlot, com os seletores e as declarações.
function uplotRules(): Rule[] {
  const css = readFileSync(APP_CSS, "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const rules: Rule[] = [];
  for (const match of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const selectors = match[1]
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!selectors.some((s) => s.includes(".uplot"))) continue;
    const declarations = match[2]
      .split(";")
      .map((d) => d.trim())
      .filter(Boolean)
      .map((d) => {
        const at = d.indexOf(":");
        return [d.slice(0, at).trim(), d.slice(at + 1).trim()] as [string, string];
      });
    rules.push({ selectors, declarations });
  }
  return rules;
}

// A árvore do uPlot 1.6.32: o raiz com `uplot` e a orientação no mesmo elemento
// (`placeDiv(UPLOT)` e `addClass(root, ORI_HZ)`), `.u-wrap`, `.u-over`, e dentro dele as
// linhas do cursor e a seleção.
function uplotTree(orientation: "u-hz" | "u-vt"): HTMLElement {
  const root = document.createElement("div");
  root.className = `uplot ${orientation}`;
  const wrap = document.createElement("div");
  wrap.className = "u-wrap";
  const over = document.createElement("div");
  over.className = "u-over";
  for (const cls of ["u-cursor-x", "u-cursor-y", "u-select"]) {
    const el = document.createElement("div");
    el.className = cls;
    over.appendChild(el);
  }
  wrap.appendChild(over);
  root.appendChild(wrap);
  document.body.appendChild(root);
  return root;
}

function target(tree: HTMLElement, cls: string): Element {
  const el = tree.querySelector(`.${cls}`);
  if (el === null) throw new Error(`sem .${cls}`);
  return el;
}

// Os elementos que um seletor alcança, nas duas árvores: "u-hz u-cursor-x" e assim por diante.
function reach(selector: string): string[] {
  const out: string[] = [];
  for (const orientation of ["u-hz", "u-vt"] as const) {
    const tree = uplotTree(orientation);
    for (const cls of ["u-cursor-x", "u-cursor-y", "u-select"]) {
      if (target(tree, cls).matches(selector)) out.push(`${orientation} ${cls}`);
    }
    tree.remove();
  }
  return out;
}

describe("V-15 — os seletores do app.css casam na árvore do uPlot", () => {
  afterEach(() => {
    document.body.replaceChildren();
  });

  it("as três regras, só com token", () => {
    const rules = uplotRules();
    expect(rules).toHaveLength(3);
    for (const rule of rules) {
      expect(rule.declarations).toHaveLength(1);
      expect(rule.declarations[0][1]).toMatch(/^var\(--ruvor-[a-z-]+\)$/);
    }
  });

  it("todo seletor das três regras alcança algum elemento", () => {
    for (const rule of uplotRules()) {
      for (const selector of rule.selectors) {
        expect(reach(selector), `o seletor ${selector} não casa com nada`).not.toEqual(
          [],
        );
      }
    }
  });

  it("cada elemento que a folha do uPlot pinta com cor fixa ganha a propriedade certa", () => {
    // O que a folha do uPlot 1.6.32 pinta (`.u-select`; `.u-hz .u-cursor-x, .u-vt
    // .u-cursor-y` à direita; `.u-hz .u-cursor-y, .u-vt .u-cursor-x` embaixo) e o que o
    // app.css tem de sobrepor, elemento a elemento.
    const covered: Record<string, string[]> = {};
    for (const rule of uplotRules()) {
      for (const selector of rule.selectors) {
        for (const hit of reach(selector)) {
          covered[hit] = [
            ...(covered[hit] ?? []),
            ...rule.declarations.map(([p]) => p),
          ];
        }
      }
    }
    expect(covered).toEqual({
      "u-hz u-select": ["background"],
      "u-vt u-select": ["background"],
      "u-hz u-cursor-x": ["border-right-color"],
      "u-vt u-cursor-y": ["border-right-color"],
      "u-hz u-cursor-y": ["border-bottom-color"],
      "u-vt u-cursor-x": ["border-bottom-color"],
    });
  });
});
