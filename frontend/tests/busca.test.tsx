/**
 * V-05 — a busca (RF-05): a pausa antes da consulta; o descarte da resposta atrasada de uma
 * consulta anterior; as três tags; o teclado (setas, Enter, Esc); "mostrar mais" pelo
 * `offset`; vazio, sem resultado e erro; e a lista suspensa da barra (RF-02), com 8.
 *
 * E V-09 do M1.7 (RF-10, RF-11, RF-13): a sugestão da caixa vazia vem de
 * `GET /api/v1/assets?has_risk=true&limit=8`, com os estados do mockup, **um** pedido por
 * montagem do `SearchBox` de página, e a resposta atrasada do primeiro efeito do `StrictMode`
 * descartada. O pedido da sugestão vai para `suggestionCalls`, à parte das consultas da busca
 * em `calls`.
 *
 * O `fetch` é um duplo que **ignora o `AbortSignal`** e só responde quando o teste manda:
 * assim a resposta da consulta antiga chega depois da nova, como na rede de verdade.
 * Só o `setTimeout` é falso — as promessas correm de verdade, e `flush` as esvazia.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { StrictMode } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { routes } from "../src/App";
import type { AssetItem, AssetPage } from "../src/api/types";
import { TEXTOS } from "../src/content/textos";

// A rota do ativo monta a tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` já
// no import, e o jsdom não o tem. Aqui nenhum gráfico chega a ser desenhado.
vi.mock("uplot", () => ({ default: class {} }));

type Call = {
  url: string;
  /** Responde 200 com o corpo. */
  respond: (body: AssetPage) => void;
  /** Responde com erro no formato da D-86. */
  fail: (status: number) => void;
};

let calls: Call[] = [];
/** Os pedidos da sugestão (RF-10), casados pelo endereço exato. */
let suggestionCalls: Call[] = [];

/** O pedido da sugestão, literal: o contrato do RF-10. */
const SUGGESTION_URL = "/api/v1/assets?has_risk=true&limit=8";

function fakeResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

/** O duplo de `fetch`: guarda cada pedido e **não olha o `signal`** do `init`. */
function stubFetch(): void {
  calls = [];
  suggestionCalls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string, _init?: RequestInit) =>
        new Promise<Response>((resolve) => {
          (url === SUGGESTION_URL ? suggestionCalls : calls).push({
            url,
            respond: (body) => resolve(fakeResponse(200, body)),
            fail: (status) =>
              resolve(
                fakeResponse(status, {
                  error: { code: "internal_error", message: "falhou", details: {} },
                }),
              ),
          });
        }),
    ),
  );
}

function asset(ticker: string, over: Partial<AssetItem> = {}): AssetItem {
  return {
    ticker,
    name: `${ticker} S.A.`,
    trading_name: `NOME ${ticker}`,
    kind: "stock",
    sector: "Setor de teste",
    status: "active",
    has_prices: true,
    has_risk: true,
    ...over,
  };
}

function page(results: AssetItem[], count = results.length, offset = 0): AssetPage {
  return { count, limit: 20, offset, results };
}

/** Esvazia as promessas pendentes — a cadeia fetch → json → estado — dentro do `act`. */
async function flush(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 20; i += 1) {
      await Promise.resolve();
    }
  });
}

/** Avança o relógio falso: a pausa de 200 ms antes da consulta. */
async function wait(ms: number): Promise<void> {
  await act(async () => {
    vi.advanceTimersByTime(ms);
  });
}

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

/** Como o `main.tsx`: dentro do `StrictMode`, que roda o efeito de montagem duas vezes. */
function renderStrictAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <StrictMode>
      <RouterProvider router={router} />
    </StrictMode>,
  );
  return router;
}

function pageInput(): HTMLInputElement {
  return screen.getByRole("combobox", {
    name: TEXTOS["busca.rotulo"],
  }) as HTMLInputElement;
}

function barInput(): HTMLInputElement {
  return screen.getByRole("combobox", {
    name: TEXTOS["casco.busca.rotulo"],
  }) as HTMLInputElement;
}

async function typeAndWait(input: HTMLElement, value: string): Promise<void> {
  fireEvent.change(input, { target: { value } });
  await wait(200);
}

function tickers(): string[] {
  return screen
    .queryAllByRole("option")
    .map((option) => option.querySelector(".ruvor-search__ticker")?.textContent ?? "");
}

function query(url: string): URLSearchParams {
  return new URL(url, "http://localhost").searchParams;
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] });
  stubFetch();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("a pausa antes da consulta", () => {
  it("não consulta antes de 200 ms, e consulta uma vez só com o último texto", async () => {
    renderAt("/");
    fireEvent.change(pageInput(), { target: { value: "p" } });
    await wait(150);
    fireEvent.change(pageInput(), { target: { value: "pe" } });
    await wait(150);
    fireEvent.change(pageInput(), { target: { value: "pet" } });
    await wait(199);
    expect(calls).toHaveLength(0);

    await wait(1);
    expect(calls).toHaveLength(1);
    const params = query(calls[0].url);
    expect(new URL(calls[0].url, "http://localhost").pathname).toBe("/api/v1/assets");
    expect(params.get("q")).toBe("pet");
    expect(params.get("limit")).toBe("20");
    expect(params.get("offset")).toBe("0");
  });

  it("mostra os resultados na ordem da API, cada um um link para o ativo", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "pet");
    calls[0].respond(page([asset("PETR4"), asset("PETR3"), asset("AUAU3")]));
    await flush();

    expect(tickers()).toEqual(["PETR4", "PETR3", "AUAU3"]);
    const link = within(screen.getAllByRole("option")[0]).getByRole("link");
    expect(link.getAttribute("href")).toBe("/ativos/PETR4");
    const list = screen.getByRole("listbox");
    expect(pageInput().getAttribute("aria-controls")).toBe(list.id);
    expect(pageInput().getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText(TEXTOS["busca.contagem"](3, "pet"))).toBeDefined();
  });
});

describe("a resposta atrasada de uma consulta anterior", () => {
  it("é descartada quando chega depois da resposta da consulta nova", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "pe");
    await typeAndWait(pageInput(), "pet");
    expect(calls.map((call) => query(call.url).get("q"))).toEqual(["pe", "pet"]);

    // A nova responde primeiro; a antiga, que o `fetch` não cancelou, chega depois.
    calls[1].respond(page([asset("PETR4")]));
    await flush();
    calls[0].respond(page([asset("PEAB3"), asset("PETR4"), asset("PETZ3")]));
    await flush();

    expect(tickers()).toEqual(["PETR4"]);
    expect(screen.getByText(TEXTOS["busca.contagem"](1, "pet"))).toBeDefined();
    expect(screen.queryByText(TEXTOS["busca.contagem"](3, "pe"))).toBeNull();
  });

  it("é descartada quando chega antes da nova: a tela segue carregando a nova", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "pe");
    await typeAndWait(pageInput(), "pet");

    calls[0].respond(page([asset("PEAB3")]));
    await flush();
    expect(tickers()).toEqual([]);
    expect(screen.getByText(TEXTOS["busca.buscando"])).toBeDefined();

    calls[1].respond(page([asset("PETR4")]));
    await flush();
    expect(tickers()).toEqual(["PETR4"]);
  });

  it("é descartada depois de limpar o campo, e o erro atrasado também", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "pet");
    fireEvent.keyDown(pageInput(), { key: "Escape" });
    calls[0].respond(page([asset("PETR4")]));
    await flush();
    expect(tickers()).toEqual([]);
    expect(screen.getByText(TEXTOS["busca.sugestaoTitulo"])).toBeDefined();

    await typeAndWait(pageInput(), "ib");
    fireEvent.keyDown(pageInput(), { key: "Escape" });
    calls[1].fail(500);
    await flush();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByText(TEXTOS["busca.sugestaoTitulo"])).toBeDefined();
  });
});

describe("as tags", () => {
  it("índice, inativo e sem dados ainda, cada uma só quando vale", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "x");
    calls[0].respond(
      page([
        asset("IBOV", { kind: "index", sector: null }),
        asset("OLD3", { status: "inactive" }),
        asset("NEW3", { has_prices: false }),
        asset("ALL3", { kind: "index", status: "inactive", has_prices: false }),
        asset("PETR4"),
      ]),
    );
    await flush();

    const tags = screen
      .getAllByRole("option")
      .map((option) =>
        [...option.querySelectorAll(".ruvor-search__tags > .ruvor-tag")].map(
          (tag) => `${tag.className}|${tag.textContent}`,
        ),
      );
    const indice = `ruvor-tag ruvor-tag--evidence|${TEXTOS["busca.tagIndice"]}`;
    const inativo = `ruvor-tag ruvor-tag--review|${TEXTOS["busca.tagInativo"]}`;
    const semDados = `ruvor-tag ruvor-tag--neutral|${TEXTOS["busca.tagSemDados"]}`;
    expect(tags).toEqual([
      [indice],
      [inativo],
      [semDados],
      [indice, inativo, semDados],
      [],
    ]);
  });

  it("o resultado mostra ticker, nome de pregão e setor; sem setor, só o nome", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "x");
    calls[0].respond(page([asset("PETR4"), asset("IBOV", { sector: null })]));
    await flush();
    const [withSector, withoutSector] = screen.getAllByRole("option");
    expect(withSector.querySelector(".ruvor-search__ticker")?.textContent).toBe(
      "PETR4",
    );
    expect(withSector.querySelector(".ruvor-search__name b")?.textContent).toBe(
      "NOME PETR4",
    );
    expect(withSector.querySelector(".ruvor-search__name span")?.textContent).toBe(
      "Setor de teste",
    );
    expect(withoutSector.querySelector(".ruvor-search__name span")).toBeNull();
  });
});

describe("o teclado", () => {
  async function withResults() {
    const router = renderAt("/");
    await typeAndWait(pageInput(), "pet");
    calls[0].respond(page([asset("PETR4"), asset("PETR3"), asset("AUAU3")]));
    await flush();
    return router;
  }

  function selected(): string[] {
    return screen
      .getAllByRole("option")
      .filter((option) => option.getAttribute("aria-selected") === "true")
      .map((option) => option.id);
  }

  it("as setas percorrem, com aria-selected, a classe do kit e aria-activedescendant", async () => {
    await withResults();
    const options = screen.getAllByRole("option");
    expect(selected()).toEqual([]);
    expect(pageInput().hasAttribute("aria-activedescendant")).toBe(false);

    fireEvent.keyDown(pageInput(), { key: "ArrowDown" });
    expect(selected()).toEqual([options[0].id]);
    expect(pageInput().getAttribute("aria-activedescendant")).toBe(options[0].id);
    expect(options[0].classList.contains("ruvor-search__option--active")).toBe(true);

    fireEvent.keyDown(pageInput(), { key: "ArrowDown" });
    fireEvent.keyDown(pageInput(), { key: "ArrowDown" });
    fireEvent.keyDown(pageInput(), { key: "ArrowDown" }); // para no último
    expect(selected()).toEqual([options[2].id]);

    fireEvent.keyDown(pageInput(), { key: "ArrowUp" });
    expect(selected()).toEqual([options[1].id]);
    expect(options[2].classList.contains("ruvor-search__option--active")).toBe(false);
  });

  it("Enter abre o destacado", async () => {
    const router = await withResults();
    fireEvent.keyDown(pageInput(), { key: "ArrowDown" });
    fireEvent.keyDown(pageInput(), { key: "ArrowDown" });
    fireEvent.keyDown(pageInput(), { key: "Enter" });
    await flush();
    expect(router.state.location.pathname).toBe("/ativos/PETR3");
  });

  it("Enter sem destaque abre o primeiro", async () => {
    const router = await withResults();
    fireEvent.keyDown(pageInput(), { key: "Enter" });
    await flush();
    expect(router.state.location.pathname).toBe("/ativos/PETR4");
  });

  it("Enter sem resultado não faz nada", async () => {
    const router = renderAt("/");
    await typeAndWait(pageInput(), "xyz");
    calls[0].respond(page([]));
    await flush();
    fireEvent.keyDown(pageInput(), { key: "Enter" });
    await flush();
    expect(router.state.location.pathname).toBe("/");
    expect(screen.getByText(TEXTOS["busca.semResultado"]("xyz"))).toBeDefined();
  });

  it("Esc limpa: o campo, a lista e o expandido", async () => {
    await withResults();
    fireEvent.keyDown(pageInput(), { key: "ArrowDown" });
    fireEvent.keyDown(pageInput(), { key: "Escape" });
    expect(pageInput().value).toBe("");
    expect(screen.queryAllByRole("option")).toHaveLength(0);
    expect(pageInput().getAttribute("aria-expanded")).toBe("false");
    expect(pageInput().hasAttribute("aria-activedescendant")).toBe(false);
    expect(screen.getByText(TEXTOS["busca.sugestaoTitulo"])).toBeDefined();
  });

  it("o botão de limpar faz o mesmo que o Esc", async () => {
    await withResults();
    fireEvent.click(screen.getByRole("button", { name: TEXTOS["busca.limpar"] }));
    expect(pageInput().value).toBe("");
    expect(screen.queryAllByRole("option")).toHaveLength(0);
  });
});

describe("mostrar mais", () => {
  it("pede a página seguinte pelo offset e soma os resultados", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "ener");
    const first = Array.from({ length: 20 }, (_, i) => asset(`AAA${i}`));
    calls[0].respond(page(first, 25));
    await flush();

    expect(screen.getAllByRole("option")).toHaveLength(20);
    expect(screen.getByText(TEXTOS["busca.mostrando"](20, 25))).toBeDefined();
    const more = screen.getByRole("button", { name: TEXTOS["busca.mostrarMais"] });
    fireEvent.click(more);
    expect(calls).toHaveLength(2);
    const params = query(calls[1].url);
    expect(params.get("q")).toBe("ener");
    expect(params.get("limit")).toBe("20");
    expect(params.get("offset")).toBe("20");
    expect(more.getAttribute("aria-busy")).toBe("true");

    const rest = Array.from({ length: 5 }, (_, i) => asset(`BBB${i}`));
    calls[1].respond(page(rest, 25, 20));
    await flush();
    expect(screen.getAllByRole("option")).toHaveLength(25);
    expect(tickers().slice(18)).toEqual([
      "AAA18",
      "AAA19",
      "BBB0",
      "BBB1",
      "BBB2",
      "BBB3",
      "BBB4",
    ]);
    expect(
      screen.queryByRole("button", { name: TEXTOS["busca.mostrarMais"] }),
    ).toBeNull();
  });
});

describe("os estados da página inicial", () => {
  it("vazio: a sugestão vinda da API, sem consultar a busca", async () => {
    renderAt("/");
    expect(suggestionCalls).toHaveLength(1);
    suggestionCalls[0].respond(page([asset("ITUB4"), asset("PETR4")]));
    await flush();
    expect(within(suggest()).getAllByRole("link")).toHaveLength(2);
    await wait(1000);
    expect(calls).toHaveLength(0);
  });

  it("carregando: a frase e o esqueleto", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "pet");
    expect(screen.getByText(TEXTOS["busca.buscando"])).toBeDefined();
    expect(document.querySelectorAll(".ruvor-search__skeleton")).toHaveLength(4);
  });

  it("sem resultado: nenhum ativo com o texto", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "xyz");
    calls[0].respond(page([]));
    await flush();
    expect(screen.getByText(TEXTOS["busca.semResultado"]("xyz"))).toBeDefined();
    expect(screen.getByText(TEXTOS["busca.semResultadoDica"])).toBeDefined();
    expect(pageInput().getAttribute("aria-expanded")).toBe("false");
  });

  it("erro: a mensagem, e tentar de novo consulta outra vez", async () => {
    renderAt("/");
    await typeAndWait(pageInput(), "pet");
    calls[0].fail(500);
    await flush();
    const alert = screen.getByRole("alert");
    expect(within(alert).getByText(TEXTOS["busca.erroTitulo"])).toBeDefined();
    expect(within(alert).getByText(TEXTOS["busca.erroTexto"])).toBeDefined();

    fireEvent.click(
      within(alert).getByRole("button", { name: TEXTOS["busca.tentarDeNovo"] }),
    );
    expect(calls).toHaveLength(2);
    expect(query(calls[1].url).get("q")).toBe("pet");
    calls[1].respond(page([asset("PETR4")]));
    await flush();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(tickers()).toEqual(["PETR4"]);
  });

  it("erro de rede também é o estado de erro", async () => {
    renderAt("/");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    await typeAndWait(pageInput(), "pet");
    await flush();
    expect(screen.getByRole("alert")).toBeDefined();
  });
});

/** A sugestão da caixa vazia: a região com o título. */
function suggest(): HTMLElement {
  return screen.getByRole("region", { name: TEXTOS["busca.sugestaoTitulo"] });
}

function chips(): string[] {
  return within(suggest())
    .queryAllByRole("link")
    .map((link) => link.textContent ?? "");
}

const SIX = ["AALR3", "BBDC4", "IBOV", "ITUB4", "PETR4", "VALE3"];
const ELEVEN_FIRST_PAGE = [
  "AALR3",
  "ABEV3",
  "B3SA3",
  "BBAS3",
  "BBDC4",
  "IBOV",
  "ITUB4",
  "PETR4",
];

function suggestionPage(tickers: string[], count = tickers.length): AssetPage {
  return { count, limit: 8, offset: 0, results: tickers.map((t) => asset(t)) };
}

describe("V-09 do M1.7 — a sugestão vinda da API (RF-10 a RF-13)", () => {
  it("a página inicial pede has_risk=true&limit=8 e mostra a resposta, na ordem, cada um um link", async () => {
    renderAt("/");
    expect(suggestionCalls.map((call) => call.url)).toEqual([SUGGESTION_URL]);
    suggestionCalls[0].respond(suggestionPage(SIX));
    await flush();

    expect(chips()).toEqual(SIX);
    expect(
      within(suggest())
        .getAllByRole("link")
        .map((link) => link.getAttribute("href")),
    ).toEqual(SIX.map((ticker) => `/ativos/${ticker}`));
    expect(within(suggest()).getByText(TEXTOS["busca.sugestaoNota"])).toBeDefined();
    expect(within(suggest()).queryByText(/e mais/)).toBeNull();
    expect(suggest().hasAttribute("aria-busy")).toBe(false);
  });

  it("carregando: o título, a frase fora da vista e os atalhos em esqueleto", () => {
    renderAt("/");
    const region = suggest();
    expect(region.getAttribute("aria-busy")).toBe("true");
    const phrase = within(region).getByText(TEXTOS["busca.sugestaoCarregando"]);
    expect(phrase.className).toBe("ruvor-sr-only");
    const skeletons = region.querySelectorAll(".ruvor-skeleton.ruvor-skeleton--chip");
    expect(skeletons).toHaveLength(6);
    expect(skeletons[0].closest("ul")?.getAttribute("aria-hidden")).toBe("true");
    expect(within(region).queryAllByRole("link")).toHaveLength(0);
    expect(within(region).queryByText(TEXTOS["busca.sugestaoNota"])).toBeNull();
  });

  it("erro: a frase e a dica no painel, sem botão nem alerta, e a caixa continua buscando", async () => {
    renderAt("/");
    suggestionCalls[0].fail(500);
    await flush();

    const region = suggest();
    const panel = within(region).getByText(TEXTOS["busca.sugestaoErro"]).parentElement;
    expect(panel?.className).toBe("ruvor-panel ruvor-search__empty");
    expect(
      within(panel as HTMLElement).getByText(TEXTOS["busca.sugestaoErroDica"]),
    ).toBeDefined();
    expect(within(region).queryAllByRole("button")).toHaveLength(0);
    expect(within(region).queryAllByRole("link")).toHaveLength(0);
    expect(screen.queryByRole("alert")).toBeNull();
    expect(region.querySelector("[aria-live]")).toBeNull();
    expect(region.hasAttribute("aria-busy")).toBe(false);

    await typeAndWait(pageInput(), "pet");
    expect(query(calls[0].url).get("q")).toBe("pet");
    calls[0].respond(page([asset("PETR4")]));
    await flush();
    expect(tickers()).toEqual(["PETR4"]);
  });

  it("erro de rede também é o erro da sugestão", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    renderAt("/");
    await flush();
    expect(within(suggest()).getByText(TEXTOS["busca.sugestaoErro"])).toBeDefined();
  });

  it("nenhum ativo com risco (count 0): a frase e a nota do mockup, sem atalho", async () => {
    renderAt("/");
    suggestionCalls[0].respond(suggestionPage([], 0));
    await flush();

    const region = suggest();
    const panel = within(region).getByText(
      TEXTOS["busca.sugestaoNenhum"],
    ).parentElement;
    expect(panel?.className).toBe("ruvor-panel ruvor-search__empty");
    expect(
      within(panel as HTMLElement).getByText(TEXTOS["busca.sugestaoNenhumNota"]),
    ).toBeDefined();
    expect(within(region).queryAllByRole("link")).toHaveLength(0);
    expect(within(region).queryByText(TEXTOS["busca.sugestaoNota"])).toBeNull();
  });

  it('count 11: os oito da página e o "e mais 3", sem link', async () => {
    renderAt("/");
    suggestionCalls[0].respond(suggestionPage(ELEVEN_FIRST_PAGE, 11));
    await flush();

    expect(chips()).toEqual(ELEVEN_FIRST_PAGE);
    const more = within(suggest()).getByText(TEXTOS["busca.sugestaoMais"](3));
    expect(more.textContent).toBe("e mais 3 ativos");
    // Os outros ramos, como na tabela de textos do mockup.
    expect(TEXTOS["busca.sugestaoMais"](1)).toBe("e mais 1 ativo");
    expect(TEXTOS["busca.sugestaoMais"](1234)).toBe("e mais 1.234 ativos");
    expect(more.className).toBe("ruvor-chips__more");
    expect(more.closest("a")).toBeNull();
    expect(more.closest("ul")?.className).toBe("ruvor-chips");
    expect(within(suggest()).getByText(TEXTOS["busca.sugestaoNota"])).toBeDefined();
  });

  it('count 8: os oito, sem o "e mais"', async () => {
    renderAt("/");
    suggestionCalls[0].respond(suggestionPage(ELEVEN_FIRST_PAGE, 8));
    await flush();
    expect(chips()).toEqual(ELEVEN_FIRST_PAGE);
    expect(within(suggest()).queryByText(/e mais/)).toBeNull();
    expect(suggest().querySelector(".ruvor-chips__more")).toBeNull();
  });

  it("um pedido por montagem: digitar, apagar e voltar ao vazio mostra a resposta guardada", async () => {
    renderAt("/");
    suggestionCalls[0].respond(suggestionPage(SIX));
    await flush();

    await typeAndWait(pageInput(), "pet");
    calls[0].respond(page([asset("PETR4")]));
    await flush();
    expect(
      screen.queryByRole("region", { name: TEXTOS["busca.sugestaoTitulo"] }),
    ).toBeNull();

    fireEvent.keyDown(pageInput(), { key: "Escape" });
    await flush();
    expect(chips()).toEqual(SIX);

    await typeAndWait(pageInput(), "vale");
    fireEvent.click(screen.getByRole("button", { name: TEXTOS["busca.limpar"] }));
    await wait(1000);
    await flush();
    expect(chips()).toEqual(SIX);
    expect(suggestionCalls).toHaveLength(1);
  });

  it.each([
    ["com erro", (call: Call) => call.fail(500)],
    ["com outra lista", (call: Call) => call.respond(suggestionPage(["WEGE3"]))],
  ])(
    "StrictMode: o pedido do primeiro efeito, resolvido depois %s, é descartado",
    async (_caso, late) => {
      renderStrictAt("/");
      // O StrictMode monta, desmonta e monta de novo: dois pedidos.
      expect(suggestionCalls).toHaveLength(2);

      // O segundo responde A; o primeiro, ainda pendente, resolve depois.
      suggestionCalls[1].respond(suggestionPage(SIX));
      await flush();
      expect(chips()).toEqual(SIX);

      late(suggestionCalls[0]);
      await flush();
      expect(chips()).toEqual(SIX);
      expect(within(suggest()).queryByText(TEXTOS["busca.sugestaoErro"])).toBeNull();
    },
  );

  it("a barra, fora da página inicial, não pede a sugestão", async () => {
    renderAt("/qualquer-coisa");
    await wait(1000);
    await flush();
    expect(suggestionCalls).toHaveLength(0);
    expect(calls).toHaveLength(0);
  });
});

describe("a lista suspensa da barra (RF-02)", () => {
  it("não existe na página de busca: o campo grande basta", () => {
    renderAt("/");
    expect(
      screen.queryByRole("combobox", { name: TEXTOS["casco.busca.rotulo"] }),
    ).toBeNull();
  });

  it("fora dela, consulta os 8 primeiros e mostra o rodapé da lista", async () => {
    renderAt("/qualquer-coisa");
    expect(barInput().getAttribute("placeholder")).toBe(
      TEXTOS["casco.busca.placeholder"],
    );
    await typeAndWait(barInput(), "ib");
    expect(query(calls[0].url).get("limit")).toBe("8");
    expect(query(calls[0].url).get("offset")).toBe("0");

    const eight = Array.from({ length: 8 }, (_, i) => asset(`IB${i}`));
    calls[0].respond({ count: 12, limit: 8, offset: 0, results: eight });
    await flush();
    expect(screen.getAllByRole("option")).toHaveLength(8);
    expect(screen.getByText(TEXTOS["busca.suspensaRodape"](8, 12))).toBeDefined();
    expect(
      screen.queryByRole("button", { name: TEXTOS["busca.mostrarMais"] }),
    ).toBeNull();
    expect(barInput().getAttribute("aria-expanded")).toBe("true");
  });

  it("fecha com o clique fora e volta ao focar o campo", async () => {
    renderAt("/qualquer-coisa");
    await typeAndWait(barInput(), "ib");
    calls[0].respond(page([asset("ITUB4")]));
    await flush();
    expect(screen.queryAllByRole("option")).toHaveLength(1);

    fireEvent.click(document.body);
    expect(screen.queryAllByRole("option")).toHaveLength(0);
    expect(barInput().getAttribute("aria-expanded")).toBe("false");

    fireEvent.focus(barInput());
    expect(screen.queryAllByRole("option")).toHaveLength(1);
  });

  it("Enter abre o ativo e fecha a lista", async () => {
    const router = renderAt("/qualquer-coisa");
    await typeAndWait(barInput(), "ib");
    calls[0].respond(page([asset("ITUB4"), asset("IBOV")]));
    await flush();
    fireEvent.keyDown(barInput(), { key: "ArrowDown" });
    fireEvent.keyDown(barInput(), { key: "ArrowDown" });
    fireEvent.keyDown(barInput(), { key: "Enter" });
    await flush();
    expect(router.state.location.pathname).toBe("/ativos/IBOV");
    expect(barInput().value).toBe("");
    expect(screen.queryAllByRole("option")).toHaveLength(0);
  });

  it("carregando, sem resultado e erro, na lista suspensa", async () => {
    renderAt("/qualquer-coisa");
    await typeAndWait(barInput(), "ib");
    expect(screen.getByText(TEXTOS["busca.buscando"])).toBeDefined();
    calls[0].fail(503);
    await flush();
    const alert = screen.getByRole("alert");
    expect(within(alert).getByText(TEXTOS["busca.erroTitulo"])).toBeDefined();

    await typeAndWait(barInput(), "xyz");
    calls[1].respond(page([]));
    await flush();
    expect(screen.getByText(TEXTOS["busca.semResultado"]("xyz"))).toBeDefined();
  });
});
