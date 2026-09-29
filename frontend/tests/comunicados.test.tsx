/**
 * A seção Comunicados (M1.6c, T5): RF-11 a RF-14 na tela.
 *
 * - V-09: o título "Comunicados da companhia à CVM"; os dois casos de `company: null`, cada um
 *   com a sua frase, pelo `kind` da identidade — e o `unlinked` enquanto ela carrega ou se
 *   falhou; a tag de categoria com texto; o link com `target`, `rel` e o aviso de saída para
 *   leitor de tela; o filtro volta ao começo; "mostrar mais" soma sem repetir o `link`; a
 *   resposta atrasada de outro filtro é descartada; a recarga pelo `reloadToken` volta ao
 *   começo mantendo o filtro; os estados do RF-14. A varredura do radical da imprensa está em
 *   `vocabulario.test.ts`.
 * - V-06, a lista `category`: a mesma de `backend/tests/api/test_valores_fundamentos.py`, e cada
 *   valor com a sua tag e o seu botão de filtro.
 * - As marcas da execução real: `data-section`, `data-state`, `data-company`,
 *   `data-disclosure-link`.
 *
 * O `fetch` é um duplo que só responde quando o teste manda: assim a resposta de um pedido
 * antigo chega depois da do novo, como na rede de verdade (o molde de `busca.test.tsx`).
 */
import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../src/api/client";
import type { Load } from "../src/api/resource";
import {
  type AssetDetail,
  DISCLOSURE_CATEGORIES,
  type DisclosureItem,
  type Disclosures,
} from "../src/api/types";
import { DisclosuresSection } from "../src/components/DisclosuresSection";
import { TEXTOS } from "../src/content/textos";

// ---------------------------------------------------------------- o duplo de fetch

type Call = {
  url: URL;
  respond: (body: Disclosures) => void;
  fail: (status: number) => void;
};

let calls: Call[] = [];

function fakeResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as unknown as Response;
}

beforeEach(() => {
  calls = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(
      (url: string) =>
        new Promise<Response>((resolve) => {
          calls.push({
            url: new URL(url, "http://ruvor.test"),
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
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

/** Esvazia as promessas pendentes — a cadeia fetch → json → estado — dentro do `act`. */
async function flush(): Promise<void> {
  await act(async () => {
    for (let i = 0; i < 20; i += 1) {
      await Promise.resolve();
    }
  });
}

function last(): Call {
  const call = calls.at(-1);
  if (call === undefined) throw new Error("nenhum pedido");
  return call;
}

async function respond(call: Call, body: Disclosures): Promise<void> {
  call.respond(body);
  await flush();
}

// ---------------------------------------------------------------- os dados

const ASSET_STOCK: AssetDetail = {
  ticker: "PETR4",
  name: "PETROLEO BRASILEIRO S.A. PETROBRAS",
  trading_name: "PETROBRAS",
  kind: "stock",
  sector: "Petróleo. Gás e Biocombustíveis",
  status: "active",
  has_prices: true,
  subsector: "Petróleo. Gás e Biocombustíveis",
  segment: "Exploração. Refino e Distribuição",
  listing_segment: "N2",
  last_price: { date: "2026-09-28", close: "48.070000", adj_close: "48.070000" },
};

const ASSET_INDEX: AssetDetail = {
  ...ASSET_STOCK,
  ticker: "IBOV",
  name: "IBOVESPA",
  trading_name: "IBOVESPA",
  kind: "index",
  sector: null,
  subsector: null,
  segment: null,
};

const OK_STOCK: Load<AssetDetail> = { state: "ok", data: ASSET_STOCK };
const OK_INDEX: Load<AssetDetail> = { state: "ok", data: ASSET_INDEX };
const LOADING: Load<AssetDetail> = { state: "loading" };
const FAILED: Load<AssetDetail> = {
  state: "error",
  error: new ApiError(500, "internal_error", "falhou"),
};

const COMPANY = { code_cvm: "9512", name: "PETROLEO BRASILEIRO S.A. PETROBRAS" };

/** Um comunicado; o `link` é a identidade (D-131). */
function doc(n: number, over: Partial<DisclosureItem> = {}): DisclosureItem {
  return {
    delivered_on: "2026-09-25",
    reference_date: "2026-09-25",
    category: "comunicado",
    kind: "Outros Comunicados Não Considerados Fatos Relevantes",
    species: "",
    title: `Título do comunicado ${n}`,
    link: `https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo=${n}`,
    ...over,
  };
}

function docs(from: number, to: number, over: Partial<DisclosureItem> = {}) {
  const out: DisclosureItem[] = [];
  for (let n = from; n < to; n += 1) out.push(doc(n, over));
  return out;
}

function page(
  results: DisclosureItem[],
  count: number,
  offset = 0,
  company: Disclosures["company"] = COMPANY,
): Disclosures {
  return { ticker: "PETR4", company, count, limit: 10, offset, results };
}

function mount(asset: Load<AssetDetail> = OK_STOCK, reloadToken = 0) {
  const view = render(
    <DisclosuresSection ticker="PETR4" asset={asset} reloadToken={reloadToken} />,
  );
  const section = () =>
    view.container.querySelector('[data-section="disclosures"]') as HTMLElement;
  return { ...view, section };
}

function links(root: HTMLElement): string[] {
  return [...root.querySelectorAll("[data-disclosure-link]")].map(
    (a) => a.getAttribute("href") ?? "",
  );
}

function filterButton(root: HTMLElement, label: string): HTMLElement {
  const group = within(root).getByRole("group", {
    name: TEXTOS["comunicados.filtro.rotulo"],
  });
  return within(group).getByRole("button", { name: label });
}

function params(call: Call) {
  return {
    path: call.url.pathname,
    limit: call.url.searchParams.get("limit"),
    offset: call.url.searchParams.get("offset"),
    category: call.url.searchParams.get("category"),
  };
}

// ---------------------------------------------------------------- V-06: a lista category

describe("V-06 — a lista category é a do contrato", () => {
  const CATEGORY = ["fato_relevante", "comunicado", "aviso_acionistas"];

  it("DISCLOSURE_CATEGORIES, na ordem de Disclosure.Category", () => {
    expect([...DISCLOSURE_CATEGORIES]).toEqual(CATEGORY);
  });

  it.each(CATEGORY)("%s tem tag e botão de filtro", (categoria) => {
    const textos = TEXTOS as Record<string, unknown>;
    for (const chave of [
      `comunicados.categoria.${categoria}`,
      `comunicados.filtro.${categoria}`,
    ]) {
      expect(typeof textos[chave]).toBe("string");
      expect((textos[chave] as string).trim()).not.toBe("");
    }
  });
});

// ---------------------------------------------------------------- V-09

describe("V-09 — o título e a frase", () => {
  it("o título é 'Comunicados da companhia à CVM', com a frase do que são", async () => {
    const { section } = mount();
    const heading = within(section()).getByRole("heading", { level: 2 });
    expect(heading.textContent).toBe("Comunicados da companhia à CVM");
    expect(section().getAttribute("aria-labelledby")).toBe(heading.id);
    expect(section().textContent).toContain(TEXTOS["comunicados.intro"]);
    expect(TEXTOS["comunicados.intro"]).toContain("uma vez por dia");
  });
});

describe("V-09 — o primeiro pedido e a lista", () => {
  it("pede os dez mais recentes, com todas as categorias", () => {
    mount();
    expect(calls).toHaveLength(1);
    expect(params(last())).toEqual({
      path: "/api/v1/assets/PETR4/disclosures",
      limit: "10",
      offset: "0",
      category: null,
    });
  });

  it("carregando: data-state loading, sem data-company", () => {
    const { section } = mount();
    expect(section().dataset.state).toBe("loading");
    expect(section().hasAttribute("data-company")).toBe(false);
    expect(section().textContent).toContain(TEXTOS["comunicados.carregando"]);
  });

  it("cada comunicado: a data, a tag com texto e o link que sai do Ruvor", async () => {
    const { section } = mount();
    await respond(
      last(),
      page(
        [
          doc(1, { category: "fato_relevante", delivered_on: "2026-09-25" }),
          doc(2, {
            category: "comunicado",
            delivered_on: "2026-09-22",
            reference_date: "2026-09-11",
          }),
          doc(3, { category: "aviso_acionistas", reference_date: null }),
        ],
        3,
      ),
    );
    const root = section();
    expect(root.dataset.state).toBe("ready");
    expect(root.dataset.company).toBe("9512");

    const rows = root.querySelectorAll("li.ruvor-doc");
    expect(rows).toHaveLength(3);

    // A tag de categoria com texto.
    expect(rows[0].querySelector(".ruvor-tag")?.textContent).toBe("fato relevante");
    expect(rows[1].querySelector(".ruvor-tag")?.textContent).toBe(
      "comunicado ao mercado",
    );
    expect(rows[2].querySelector(".ruvor-tag")?.textContent).toBe(
      "aviso aos acionistas",
    );

    // A data de entrega; a de referência só quando difere.
    expect(rows[0].querySelector(".ruvor-doc__date")?.textContent).toBe(
      `${TEXTOS["comunicados.entregueEm"]} 25/09/2026`,
    );
    expect(rows[0].textContent).not.toContain("Referente a");
    expect(rows[1].textContent).toContain(
      TEXTOS["comunicados.referencia"]("11/09/2026"),
    );
    expect(rows[2].textContent).not.toContain("Referente a");

    // O link: para a CVM, em aba nova, com rel e o aviso de saída para leitor de tela.
    const link = rows[0].querySelector("a") as HTMLAnchorElement;
    expect(link.getAttribute("href")).toBe(doc(1).link);
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
    expect(link.hasAttribute("data-disclosure-link")).toBe(true);
    const aviso = link.querySelector(".ruvor-sr-only");
    expect(aviso?.textContent).toBe(` (${TEXTOS["comunicados.linkSaida"]})`);
    expect(link.textContent).toBe(
      `${doc(1).title} (${TEXTOS["comunicados.linkSaida"]})`,
    );

    // Quem entregou, e o aviso de que o título sai do Ruvor.
    expect(root.textContent).toContain(
      `${TEXTOS["comunicados.companhia"](COMPANY.name, "9512")} ${TEXTOS["comunicados.saida"]}`,
    );
    expect(root.textContent).toContain(TEXTOS["comunicados.mostrando"]("3", "3"));
    expect(
      within(root).queryByRole("button", { name: TEXTOS["comunicados.mostrarMais"] }),
    ).toBeNull();
  });

  it("company sem nome: a frase só com o código", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 2), 2, 0, { code_cvm: "9512", name: null }));
    expect(section().textContent).toContain(
      TEXTOS["comunicados.companhiaSemNome"]("9512"),
    );
  });

  it("uma categoria fora da lista não quebra a linha: ela sai sem tag", async () => {
    const { section } = mount();
    const estranho = { ...doc(1), category: "outra" } as unknown as DisclosureItem;
    await respond(last(), page([estranho], 1));
    const row = section().querySelector("li.ruvor-doc") as HTMLElement;
    expect(row.querySelector(".ruvor-tag")).toBeNull();
    expect(links(section())).toEqual([doc(1).link]);
  });
});

describe("V-09 — o filtro", () => {
  it("os quatro botões com aria-pressed; 'todas' é o padrão", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    const group = within(section()).getByRole("group", {
      name: TEXTOS["comunicados.filtro.rotulo"],
    });
    const buttons = within(group).getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual([
      TEXTOS["comunicados.filtro.todas"],
      TEXTOS["comunicados.filtro.fato_relevante"],
      TEXTOS["comunicados.filtro.comunicado"],
      TEXTOS["comunicados.filtro.aviso_acionistas"],
    ]);
    expect(buttons.map((b) => b.getAttribute("aria-pressed"))).toEqual([
      "true",
      "false",
      "false",
      "false",
    ]);
  });

  it("trocar o filtro, depois de 'mostrar mais', volta ao começo e substitui a lista", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(
      within(section()).getByRole("button", {
        name: TEXTOS["comunicados.mostrarMais"],
      }),
    );
    expect(params(last()).offset).toBe("10");
    await respond(last(), page(docs(10, 20), 25, 10));
    expect(links(section())).toHaveLength(20);

    fireEvent.click(
      filterButton(section(), TEXTOS["comunicados.filtro.fato_relevante"]),
    );
    expect(params(last())).toMatchObject({
      offset: "0",
      category: "fato_relevante",
      limit: "10",
    });
    // Volta a carregando, com o filtro já marcado.
    expect(section().dataset.state).toBe("loading");
    expect(
      filterButton(section(), TEXTOS["comunicados.filtro.fato_relevante"]).getAttribute(
        "aria-pressed",
      ),
    ).toBe("true");
    expect(
      filterButton(section(), TEXTOS["comunicados.filtro.todas"]).getAttribute(
        "aria-pressed",
      ),
    ).toBe("false");

    const fatos = docs(100, 104, { category: "fato_relevante" });
    await respond(last(), page(fatos, 4));
    expect(section().dataset.state).toBe("ready");
    expect(links(section())).toEqual(fatos.map((d) => d.link));
    expect(section().textContent).toContain(TEXTOS["comunicados.mostrando"]("4", "4"));
  });

  it("filtro sem resultado: a frase da categoria e 'ver todas', que volta a todas", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(
      filterButton(section(), TEXTOS["comunicados.filtro.aviso_acionistas"]),
    );
    await respond(last(), page([], 0));
    expect(section().dataset.state).toBe("empty");
    expect(section().textContent).toContain(
      TEXTOS["comunicados.filtroVazio"]("aviso aos acionistas"),
    );
    // O filtro continua à vista, para sair do vazio.
    expect(
      filterButton(
        section(),
        TEXTOS["comunicados.filtro.aviso_acionistas"],
      ).getAttribute("aria-pressed"),
    ).toBe("true");

    fireEvent.click(
      within(section()).getByRole("button", { name: TEXTOS["comunicados.verTodas"] }),
    );
    expect(params(last())).toMatchObject({ offset: "0", category: null });
    await respond(last(), page(docs(0, 10), 25));
    expect(links(section())).toHaveLength(10);
    expect(
      filterButton(section(), TEXTOS["comunicados.filtro.todas"]).getAttribute(
        "aria-pressed",
      ),
    ).toBe("true");
  });
});

describe("V-09 — mostrar mais", () => {
  it("pede offset += 10 e soma, sem repetir o link, enquanto count passar do mostrado", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    expect(section().textContent).toContain(
      TEXTOS["comunicados.mostrando"]("10", "25"),
    );

    const mais = () =>
      within(section()).queryByRole("button", {
        name: TEXTOS["comunicados.mostrarMais"],
      });
    fireEvent.click(mais() as HTMLElement);
    expect(params(last())).toMatchObject({ offset: "10", limit: "10", category: null });

    // Carregando mais: a lista fica, o botão espera.
    expect(links(section())).toHaveLength(10);
    const ocupado = within(section()).getByRole("button", {
      name: TEXTOS["comunicados.carregandoMais"],
    });
    expect(ocupado.getAttribute("aria-busy")).toBe("true");
    expect(ocupado.hasAttribute("disabled")).toBe(true);

    // A coleta diária inseriu um no topo: a segunda página começa pelo último da primeira.
    const segunda = [doc(9), ...docs(10, 19)];
    await respond(last(), page(segunda, 26, 10));
    const vistos = links(section());
    expect(vistos).toHaveLength(19);
    expect(new Set(vistos).size).toBe(19);
    expect(vistos).toEqual(docs(0, 19).map((d) => d.link));
    expect(section().textContent).toContain(
      TEXTOS["comunicados.mostrando"]("19", "26"),
    );

    // 10 + 10 < 26: ainda há mais.
    fireEvent.click(mais() as HTMLElement);
    expect(params(last()).offset).toBe("20");
    await respond(last(), page(docs(19, 25), 26, 20));
    expect(links(section())).toHaveLength(25);
    // 20 + 6 = 26: acabou.
    expect(mais()).toBeNull();
  });

  it("erro no mostrar mais: a lista fica, e o erro vai junto do botão", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(
      within(section()).getByRole("button", {
        name: TEXTOS["comunicados.mostrarMais"],
      }),
    );
    last().fail(500);
    await flush();
    expect(links(section())).toHaveLength(10);
    const alerta = within(section()).getByRole("alert");
    expect(alerta.textContent).toContain(TEXTOS["comunicados.erroMais"]);
    fireEvent.click(
      within(alerta).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
    );
    expect(params(last()).offset).toBe("10");
    await respond(last(), page(docs(10, 20), 25, 10));
    expect(links(section())).toHaveLength(20);
    expect(within(section()).queryByRole("alert")).toBeNull();
  });
});

describe("V-09 — a resposta atrasada é descartada", () => {
  it("a de um filtro anterior, que chega depois da do novo", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));

    fireEvent.click(
      filterButton(section(), TEXTOS["comunicados.filtro.fato_relevante"]),
    );
    const antigo = last();
    fireEvent.click(filterButton(section(), TEXTOS["comunicados.filtro.comunicado"]));
    const novo = last();
    expect(params(antigo).category).toBe("fato_relevante");
    expect(params(novo).category).toBe("comunicado");

    const comunicados = docs(200, 203, { category: "comunicado" });
    await respond(novo, page(comunicados, 3));
    await respond(antigo, page(docs(300, 305, { category: "fato_relevante" }), 5));

    expect(links(section())).toEqual(comunicados.map((d) => d.link));
    expect(section().textContent).toContain(TEXTOS["comunicados.mostrando"]("3", "3"));
    expect(
      filterButton(section(), TEXTOS["comunicados.filtro.comunicado"]).getAttribute(
        "aria-pressed",
      ),
    ).toBe("true");
  });

  it("a de um 'mostrar mais' que a troca de filtro atropelou", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(
      within(section()).getByRole("button", {
        name: TEXTOS["comunicados.mostrarMais"],
      }),
    );
    const mais = last();
    fireEvent.click(
      filterButton(section(), TEXTOS["comunicados.filtro.fato_relevante"]),
    );
    const fatos = docs(100, 102, { category: "fato_relevante" });
    await respond(last(), page(fatos, 2));
    await respond(mais, page(docs(10, 20), 25, 10));
    expect(links(section())).toEqual(fatos.map((d) => d.link));
  });

  it("o erro atrasado também", async () => {
    const { section } = mount();
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(
      filterButton(section(), TEXTOS["comunicados.filtro.fato_relevante"]),
    );
    const antigo = last();
    fireEvent.click(filterButton(section(), TEXTOS["comunicados.filtro.comunicado"]));
    await respond(last(), page(docs(200, 203), 3));
    antigo.fail(500);
    await flush();
    expect(section().dataset.state).toBe("ready");
    expect(within(section()).queryByRole("alert")).toBeNull();
  });
});

describe("V-09 — a recarga pelo reloadToken", () => {
  it("volta a offset=0, mantendo o filtro, e substitui a lista somada", async () => {
    const view = mount(OK_STOCK, 0);
    const { section } = view;
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(filterButton(section(), TEXTOS["comunicados.filtro.comunicado"]));
    await respond(last(), page(docs(0, 10), 25));
    fireEvent.click(
      within(section()).getByRole("button", {
        name: TEXTOS["comunicados.mostrarMais"],
      }),
    );
    await respond(last(), page(docs(10, 20), 25, 10));
    expect(links(section())).toHaveLength(20);
    const antes = calls.length;

    view.rerender(
      <DisclosuresSection ticker="PETR4" asset={OK_STOCK} reloadToken={1} />,
    );
    expect(calls).toHaveLength(antes + 1);
    expect(params(last())).toMatchObject({
      offset: "0",
      limit: "10",
      category: "comunicado",
    });
    // Sem piscar: a lista fica até a resposta nova.
    expect(links(section())).toHaveLength(20);

    const nova = [doc(500), ...docs(0, 9)];
    await respond(last(), page(nova, 26));
    expect(links(section())).toEqual(nova.map((d) => d.link));
    expect(section().textContent).toContain(
      TEXTOS["comunicados.mostrando"]("10", "26"),
    );
    expect(
      filterButton(section(), TEXTOS["comunicados.filtro.comunicado"]).getAttribute(
        "aria-pressed",
      ),
    ).toBe("true");
  });

  it("o mesmo reloadToken não pede de novo", async () => {
    const view = mount(OK_STOCK, 3);
    await respond(last(), page(docs(0, 10), 25));
    view.rerender(
      <DisclosuresSection ticker="PETR4" asset={OK_STOCK} reloadToken={3} />,
    );
    expect(calls).toHaveLength(1);
  });
});

describe("V-09 — os estados do RF-14", () => {
  it("erro da seção, com 'tentar de novo'", async () => {
    const { section } = mount();
    last().fail(500);
    await flush();
    expect(section().dataset.state).toBe("error");
    const alerta = within(section()).getByRole("alert");
    expect(alerta.textContent).toContain(TEXTOS["ativo.erroSecao"]);
    fireEvent.click(
      within(alerta).getByRole("button", { name: TEXTOS["ativo.tentarDeNovo"] }),
    );
    expect(params(last())).toMatchObject({ offset: "0", category: null });
    expect(section().dataset.state).toBe("loading");
    await respond(last(), page(docs(0, 3), 3));
    expect(section().dataset.state).toBe("ready");
  });

  it("nenhum comunicado: a frase, sem o filtro", async () => {
    const { section } = mount();
    await respond(last(), page([], 0));
    expect(section().dataset.state).toBe("empty");
    expect(section().dataset.company).toBe("9512");
    expect(section().textContent).toContain(TEXTOS["comunicados.vazio"]);
    expect(within(section()).queryByRole("group")).toBeNull();
  });

  it.each([
    ["índice", OK_INDEX, "none-index", TEXTOS["comunicados.indice"], "empty"],
    [
      "ação sem código",
      OK_STOCK,
      "none-stock",
      TEXTOS["comunicados.semCodigo"],
      "empty",
    ],
    [
      "identidade em erro",
      FAILED,
      "unlinked",
      TEXTOS["comunicados.semLigacao"],
      "empty",
    ],
    [
      "identidade carregando",
      LOADING,
      "unlinked",
      TEXTOS["comunicados.carregando"],
      "loading",
    ],
  ] as const)("company nulo, %s", async (_caso, identidade, marca, frase, estado) => {
    const { section } = mount(identidade);
    await respond(last(), page([], 0, 0, null));
    expect(section().dataset.company).toBe(marca);
    expect(section().dataset.state).toBe(estado);
    expect(section().textContent).toContain(frase);
    expect(within(section()).queryByRole("group")).toBeNull();
  });

  it("company nulo: a frase do índice e a do código não se confundem", async () => {
    const indice = mount(OK_INDEX);
    await respond(last(), page([], 0, 0, null));
    expect(indice.section().textContent).not.toContain(TEXTOS["comunicados.semCodigo"]);
    cleanup();
    const acao = mount(OK_STOCK);
    await respond(last(), page([], 0, 0, null));
    expect(acao.section().textContent).not.toContain(TEXTOS["comunicados.indice"]);
  });

  it("a identidade chega depois: sai do carregando para a frase do kind", async () => {
    const view = mount(LOADING);
    await respond(last(), page([], 0, 0, null));
    expect(view.section().dataset.state).toBe("loading");
    view.rerender(
      <DisclosuresSection ticker="PETR4" asset={OK_INDEX} reloadToken={0} />,
    );
    expect(view.section().dataset.company).toBe("none-index");
    expect(view.section().textContent).toContain(TEXTOS["comunicados.indice"]);
    expect(calls).toHaveLength(1);
  });
});
