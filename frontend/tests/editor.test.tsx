/**
 * M2.2b (T7), V-03 e V-04 nas peças do editor, contra o `lista.html` aprovado: as funções puras
 * de `portfolio/editor.ts` (as conferências do cliente, a soma ao vivo, a leitura do
 * `400 invalid_holdings` pelo `index`), o `pickReason` do seletor, e o `HoldingsEditor` num
 * dono mínimo — **o campo guarda o texto como foi digitado**, ao digitar e ao sair dele, e o
 * seletor fica desabilitado com 20 ações.
 */
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it } from "vitest";

import { ApiError } from "../src/api/client";
import type { AssetItem } from "../src/api/types";
import { pickReason } from "../src/components/AssetPicker";
import { HoldingsEditor } from "../src/components/HoldingsEditor";
import { TEXTOS } from "../src/content/textos";
import {
  apiDecimalText,
  applyHoldingsError,
  blurRow,
  centsText,
  checkHoldings,
  type EditorRow,
  holdingsToApi,
  liveSum,
  newRow,
  weightError,
} from "../src/portfolio/editor";

afterEach(() => {
  cleanup();
});

const rowsOf = (...texts: string[]): EditorRow[] =>
  texts.map((text, i) => newRow(`ATV${i}3`, `ATIVO ${i}`, text));

function stock(ticker: string, over: Partial<AssetItem> = {}): AssetItem {
  return {
    ticker,
    name: ticker,
    trading_name: ticker,
    kind: "stock",
    sector: null,
    status: "active",
    has_prices: true,
    has_risk: false,
    ...over,
  };
}

describe("o seletor: pickReason (D-181)", () => {
  const taken = new Set(["ITUB4"]);
  it("só ação ativa fora da composição é escolhível", () => {
    expect(pickReason(stock("PETR4"), taken)).toBeNull();
  });
  it.each([
    [stock("IBOV", { kind: "index" }), "carteiras.seletor.motivo.indice"],
    [
      stock("IBOV", { kind: "index", status: "inactive" }),
      "carteiras.seletor.motivo.indice",
    ],
    [stock("BIDI4", { status: "inactive" }), "carteiras.seletor.motivo.inativa"],
    [stock("ITUB4"), "carteiras.seletor.motivo.naComposicao"],
  ])("%o → %s", (asset, reason) => {
    expect(pickReason(asset, taken)).toBe(reason);
  });
});

describe("as funções do editor", () => {
  it("weightError: o formato, depois de 0,01 a 100,00", () => {
    expect(weightError("12,345")).toBe(TEXTOS["carteiras.erro.pesoFormato"]);
    expect(weightError("")).toBe(TEXTOS["carteiras.erro.pesoFormato"]);
    expect(weightError("0")).toBe(TEXTOS["carteiras.erro.peso"]);
    expect(weightError("100,01")).toBe(TEXTOS["carteiras.erro.peso"]);
    expect(weightError("0,01")).toBeNull();
    expect(weightError("100")).toBeNull();
  });

  it("blurRow nunca reescreve o texto", () => {
    for (const text of ["5,", " 61,6 ", "33.4", "0,10", "abc", "007"]) {
      expect(blurRow(newRow("PETR4", "P", text)).text).toBe(text);
    }
  });

  it("blurRow: o formato aparece; a mensagem que já estava some quando o peso passa", () => {
    const bad = blurRow(newRow("PETR4", "P", "1,234"));
    expect(bad.error).toBe(TEXTOS["carteiras.erro.pesoFormato"]);
    expect(blurRow({ ...bad, text: "1,23" }).error).toBeNull();
    // Fora da faixa só aparece no envio, não ao sair do campo.
    expect(blurRow(newRow("PETR4", "P", "150")).error).toBeNull();
  });

  it("a soma ao vivo em centésimos inteiros: 0,01 + 65,40 + 34,59 = 10.000", () => {
    expect(liveSum(rowsOf("0,01", "65,40", "34,59"))).toEqual({
      cents: 10_000,
      outside: 0,
    });
    expect(liveSum(rowsOf("0,29", "1,15", "x"))).toEqual({ cents: 144, outside: 1 });
  });

  it("centsText e apiDecimalText: com vírgula e milhar, pelo texto", () => {
    expect(centsText(9999)).toBe("99,99");
    expect(centsText(1)).toBe("0,01");
    expect(centsText(1_999_980)).toBe("19.999,80");
    expect(apiDecimalText("99.99")).toBe("99,99");
    expect(apiDecimalText("100.5")).toBe("100,50");
    expect(apiDecimalText("1000")).toBe("1.000,00");
  });

  it("checkHoldings: as conferências na ordem da API; a soma só com todos os pesos números", () => {
    const one = checkHoldings(rowsOf("100"));
    expect(one.total).toEqual([TEXTOS["carteiras.erro.contagem"](1)]);
    expect(one.ok).toBe(false);

    const sumOff = checkHoldings(rowsOf("33,33", "33,33", "33,33"));
    expect(sumOff.total).toEqual([TEXTOS["carteiras.erro.soma"]("99,99")]);

    const notNumbers = checkHoldings(rowsOf("12,345", "0", "150", "40"));
    expect(notNumbers.total).toEqual([]);
    expect(notNumbers.rows.map((r) => r.error)).toEqual([
      TEXTOS["carteiras.erro.pesoFormato"],
      TEXTOS["carteiras.erro.peso"],
      TEXTOS["carteiras.erro.peso"],
      null,
    ]);

    const many = checkHoldings(rowsOf(...Array.from({ length: 21 }, () => "5")));
    expect(many.total[0]).toBe(TEXTOS["carteiras.erro.contagem"](21));

    const good = checkHoldings(rowsOf("0,01", "65,40", "34,59"));
    expect(good).toMatchObject({ total: [], ok: true });
    expect(good.rows.map((r) => r.text)).toEqual(["0,01", "65,40", "34,59"]);
  });

  it("holdingsToApi: o peso em texto com ponto, e a ordem do editor", () => {
    expect(holdingsToApi(rowsOf("5,", "33.4", " 61,6 "))).toEqual([
      { ticker: "ATV03", weight: "5.00" },
      { ticker: "ATV13", weight: "33.40" },
      { ticker: "ATV23", weight: "61.60" },
    ]);
  });

  it("applyHoldingsError: cada reason de items na linha do seu index, no lugar certo", () => {
    const rows = rowsOf("1", "2", "3", "4", "5", "85");
    const error = new ApiError(400, "invalid_holdings", "x", {
      reason: "items",
      items: [
        { index: 0, ticker: "ATV03", reason: "not_a_stock" },
        { index: 1, ticker: "ATV13", reason: "inactive" },
        { index: 2, ticker: "ATV23", reason: "unknown_ticker" },
        { index: 4, ticker: "ATV43", reason: "duplicate" },
        { index: 5, ticker: "ATV53", reason: "weight_out_of_range" },
      ],
    });
    const out = applyHoldingsError(error, rows);
    expect(out?.general).toBeNull();
    expect(out?.rows.map((r) => r.apiError)).toEqual([
      { place: "ticker", text: TEXTOS["carteiras.erro.naoAcao"] },
      { place: "ticker", text: TEXTOS["carteiras.erro.inativa"] },
      { place: "ticker", text: TEXTOS["carteiras.erro.desconhecida"] },
      null,
      { place: "ticker", text: TEXTOS["carteiras.erro.repetida"] },
      { place: "weight", text: TEXTOS["carteiras.erro.peso"] },
    ]);
  });

  it("applyHoldingsError: a soma e a contagem na linha da soma; a forma e o desconhecido no geral", () => {
    const rows = rowsOf("50", "50");
    const err = (code: string, details: Record<string, unknown>) =>
      new ApiError(400, code, "x", details);
    expect(
      applyHoldingsError(
        err("invalid_holdings", { reason: "weights_sum", sum: "100.01" }),
        rows,
      )?.total,
    ).toEqual([TEXTOS["carteiras.erro.soma"]("100,01")]);
    expect(
      applyHoldingsError(
        err("invalid_holdings", { reason: "count_out_of_range", count: 1 }),
        rows,
      )?.total,
    ).toEqual([TEXTOS["carteiras.erro.contagem"](1)]);
    for (const details of [
      { reason: "novo" },
      { reason: "items", items: [{ index: 0, reason: "novo" }] },
      { reason: "items", items: [{ index: 2, reason: "duplicate" }] },
      { reason: "count_out_of_range" },
    ]) {
      expect(applyHoldingsError(err("invalid_holdings", details), rows)?.general).toBe(
        TEXTOS["carteiras.erro.forma"],
      );
    }
    expect(
      applyHoldingsError(err("invalid_parameter", { fields: {} }), rows)?.general,
    ).toBe(TEXTOS["carteiras.erro.forma"]);
    expect(applyHoldingsError(new ApiError(0, "network_error", "x"), rows)).toBeNull();
  });
});

/** Um dono mínimo do editor, com as funções da tela: o texto entra como veio. */
function Owner({ initial }: { initial: EditorRow[] }) {
  const [rows, setRows] = useState(initial);
  return (
    <HoldingsEditor
      rows={rows}
      totalErrors={[]}
      disabled={false}
      onAdd={(asset) => setRows((c) => [...c, newRow(asset.ticker, asset.name)])}
      onWeightChange={(index, text) =>
        setRows((c) => c.map((row, i) => (i === index ? { ...row, text } : row)))
      }
      onWeightBlur={(index) =>
        setRows((c) => c.map((row, i) => (i === index ? blurRow(row) : row)))
      }
      onRemove={(index) => setRows((c) => c.filter((_, i) => i !== index))}
    />
  );
}

describe("o HoldingsEditor", () => {
  it("o campo guarda o texto como foi digitado, e a soma o lê por algarismos", async () => {
    render(<Owner initial={rowsOf("", "", "")} />);
    const inputs = screen.getAllByRole("textbox") as HTMLInputElement[];
    const typed = ["5,", "33.4", " 61,6 "];
    for (const [i, text] of typed.entries()) {
      await act(async () => {
        fireEvent.change(inputs[i], { target: { value: text } });
      });
      await act(async () => {
        fireEvent.blur(inputs[i]);
      });
    }
    expect(inputs.map((input) => input.value)).toEqual(typed);
    const soma = document.querySelector('[data-part="soma"]') as HTMLElement;
    expect(soma.querySelector(".ruvor-weight-sum__value")?.textContent).toBe("100,00%");
    expect(soma.textContent).toContain(TEXTOS["carteiras.soma.exata"]);
  });

  it("o peso é um campo de texto com inputmode decimal e rótulo com o código", () => {
    render(<Owner initial={rowsOf("10")} />);
    const input = screen.getByLabelText(TEXTOS["carteiras.peso.rotulo"]("ATV03"));
    expect(input.getAttribute("type")).toBe("text");
    expect(input.getAttribute("inputmode")).toBe("decimal");
  });

  it("sem linhas: a frase do vazio e a soma em 0,00", () => {
    render(<Owner initial={[]} />);
    expect(screen.getByText(TEXTOS["carteiras.editor.vazio"])).toBeDefined();
    expect(screen.getByText(TEXTOS["carteiras.soma.abaixo"]("100,00"))).toBeDefined();
  });

  it("com 20 ações, o seletor fica desabilitado, com a dica do máximo", () => {
    render(<Owner initial={rowsOf(...Array.from({ length: 20 }, () => "5"))} />);
    const picker = screen.getByRole("combobox", {
      name: TEXTOS["carteiras.seletor.rotulo"],
    }) as HTMLInputElement;
    expect(picker.disabled).toBe(true);
    const hint = document.getElementById(picker.getAttribute("aria-describedby") ?? "");
    expect(hint?.textContent).toBe(TEXTOS["carteiras.seletor.limite"]);
  });

  it("com 19, o seletor fica habilitado", () => {
    render(<Owner initial={rowsOf(...Array.from({ length: 19 }, () => "5"))} />);
    const picker = screen.getByRole("combobox", {
      name: TEXTOS["carteiras.seletor.rotulo"],
    }) as HTMLInputElement;
    expect(picker.disabled).toBe(false);
  });
});
