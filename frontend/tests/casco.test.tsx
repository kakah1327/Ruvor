/**
 * V-03 completo, na tela: a chave de tema grava e remove `data-theme`, lembra a escolha, e a
 * tela funciona com `localStorage` lançando exceção. E o rodapé (RF-04): a ressalva e a
 * fonte em toda tela, e a proveniência só quando a tela a dá, só no endereço em que a deu.
 *
 * `theme.ts` guarda a escolha em memória: cada teste importa o casco de novo.
 *
 * V-03 do M2.3, na tela: o alternador do nível de leitura — dois botões com `aria-pressed`, o
 * padrão iniciante, a escolha lembrada, o valor desconhecido e o armazenamento que lança, a
 * troca feita em outro ponto da página — e o primeiro desenho no nível lembrado, provado por
 * `renderToString`, que não roda efeitos. `reading.ts` também guarda o nível em memória: o
 * `freshShell` o importa de novo junto com o casco.
 *
 * O lugar da conta (M2.1b, RF-09): por último na barra, depois da chave de tema. Sem o provedor
 * da sessão, o anônimo do padrão; nos casos logados e no carregando, o `SessionProvider` vem do
 * **mesmo grafo de módulos** que o casco, recarregado pelo `freshShell` — o de outro grafo teria
 * outro contexto, e o casco ficaria no anônimo do padrão.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { useEffect } from "react";
import { renderToString } from "react-dom/server";
import {
  createMemoryRouter,
  MemoryRouter,
  Route,
  RouterProvider,
  Routes,
} from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RESSALVA } from "../src/content/ressalva";
import { TEXTOS } from "../src/content/textos";

type ShellModule = typeof import("../src/components/Shell");

async function freshShell(): Promise<ShellModule> {
  vi.resetModules();
  return import("../src/components/Shell");
}

function throwingStorage(): void {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
}

async function renderShell(path = "/") {
  const { Shell } = await freshShell();
  const router = createMemoryRouter(
    [{ element: <Shell />, children: [{ path: "*", element: null }] }],
    { initialEntries: [path] },
  );
  render(<RouterProvider router={router} />);
  return router;
}

function themeButton(label: string): HTMLElement {
  const group = screen.getByRole("group", { name: TEXTOS["casco.tema.rotulo"] });
  return within(group).getByRole("button", { name: label });
}

function pressed(): string[] {
  const group = screen.getByRole("group", { name: TEXTOS["casco.tema.rotulo"] });
  return within(group)
    .getAllByRole("button")
    .filter((button) => button.getAttribute("aria-pressed") === "true")
    .map((button) => button.textContent ?? "");
}

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  document.documentElement.removeAttribute("data-reading");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("chave de tema", () => {
  it("tem três botões com rótulo, e o padrão é sistema, sem data-theme", async () => {
    await renderShell();
    expect(themeButton(TEXTOS["casco.tema.claro"])).toBeDefined();
    expect(themeButton(TEXTOS["casco.tema.escuro"])).toBeDefined();
    expect(themeButton(TEXTOS["casco.tema.sistema"])).toBeDefined();
    expect(pressed()).toEqual([TEXTOS["casco.tema.sistema"]]);
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("claro e escuro gravam data-theme; sistema o remove", async () => {
    await renderShell();
    fireEvent.click(themeButton(TEXTOS["casco.tema.escuro"]));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(pressed()).toEqual([TEXTOS["casco.tema.escuro"]]);

    fireEvent.click(themeButton(TEXTOS["casco.tema.claro"]));
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(pressed()).toEqual([TEXTOS["casco.tema.claro"]]);

    fireEvent.click(themeButton(TEXTOS["casco.tema.sistema"]));
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
    expect(pressed()).toEqual([TEXTOS["casco.tema.sistema"]]);
  });

  it("lembra a escolha: grava no localStorage e a próxima carga a mostra", async () => {
    await renderShell();
    fireEvent.click(themeButton(TEXTOS["casco.tema.escuro"]));
    expect(window.localStorage.getItem("ruvor-theme")).toBe("dark");
    cleanup();

    await renderShell();
    expect(pressed()).toEqual([TEXTOS["casco.tema.escuro"]]);
  });

  it("funciona com localStorage lançando exceção", async () => {
    throwingStorage();
    await renderShell();
    expect(pressed()).toEqual([TEXTOS["casco.tema.sistema"]]);

    fireEvent.click(themeButton(TEXTOS["casco.tema.escuro"]));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(pressed()).toEqual([TEXTOS["casco.tema.escuro"]]);

    fireEvent.click(themeButton(TEXTOS["casco.tema.sistema"]));
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });
});

function readingGroup(): HTMLElement {
  return screen.getByRole("group", { name: TEXTOS["casco.leitura.rotulo"] });
}

function readingButton(label: string): HTMLElement {
  return within(readingGroup()).getByRole("button", { name: label });
}

function readingPressed(): string[] {
  return within(readingGroup())
    .getAllByRole("button")
    .filter((button) => button.getAttribute("aria-pressed") === "true")
    .map((button) => button.textContent ?? "");
}

const INICIANTE = TEXTOS["casco.leitura.iniciante"];
const AVANCADA = TEXTOS["casco.leitura.avancada"];

describe("o alternador do nível de leitura (V-03 do M2.3)", () => {
  it("dois botões com rótulo e aria-pressed, num grupo com rótulo; o padrão é iniciante", async () => {
    await renderShell("/ativos/ITUB4");
    const buttons = within(readingGroup()).getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual([INICIANTE, AVANCADA]);
    expect(buttons.every((b) => b.hasAttribute("aria-pressed"))).toBe(true);
    expect(readingPressed()).toEqual([INICIANTE]);
    expect(document.documentElement.dataset.reading).toBe("beginner");
  });

  it("aparece na busca também, antes da chave de tema, e fora de região viva", async () => {
    await renderShell("/");
    const reading = readingGroup();
    const theme = screen.getByRole("group", { name: TEXTOS["casco.tema.rotulo"] });
    expect(
      reading.compareDocumentPosition(theme) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).not.toBe(0);
    expect(reading.parentElement).toBe(theme.parentElement);
    expect(reading.parentElement?.className).toBe("ruvor-topbar__prefs");
    // M2.1b (T10): até 840 px, o kit endereça o alternador como a .ruvor-segmented seguida de
    // outra e a chave de tema como a que segue outra — os dois vizinhos, nessa ordem.
    expect(reading.nextElementSibling).toBe(theme);
    expect(reading.classList.contains("ruvor-segmented")).toBe(true);
    expect(theme.classList.contains("ruvor-segmented")).toBe(true);
    expect(reading.closest("[aria-live]")).toBeNull();
  });

  it("trocar grava, aplica data-reading e move o alternador", async () => {
    await renderShell();
    fireEvent.click(readingButton(AVANCADA));
    expect(readingPressed()).toEqual([AVANCADA]);
    expect(window.localStorage.getItem("ruvor-reading")).toBe("advanced");
    expect(document.documentElement.dataset.reading).toBe("advanced");

    fireEvent.click(readingButton(INICIANTE));
    expect(readingPressed()).toEqual([INICIANTE]);
    expect(window.localStorage.getItem("ruvor-reading")).toBe("beginner");
    expect(document.documentElement.dataset.reading).toBe("beginner");
  });

  it("lembra a escolha: a próxima carga sai em avançada", async () => {
    await renderShell();
    fireEvent.click(readingButton(AVANCADA));
    cleanup();

    await renderShell();
    expect(readingPressed()).toEqual([AVANCADA]);
  });

  it.each(["expert", "Advanced", ""])(
    "valor guardado desconhecido %j sai em iniciante",
    async (valor) => {
      window.localStorage.setItem("ruvor-reading", valor);
      await renderShell();
      expect(readingPressed()).toEqual([INICIANTE]);
    },
  );

  it("funciona com localStorage lançando exceção", async () => {
    throwingStorage();
    await renderShell();
    expect(readingPressed()).toEqual([INICIANTE]);
    fireEvent.click(readingButton(AVANCADA));
    expect(readingPressed()).toEqual([AVANCADA]);
    expect(document.documentElement.dataset.reading).toBe("advanced");
  });

  it("RF-03: quem mais trocar o nível na página move o alternador", async () => {
    await renderShell();
    // O mesmo módulo que o casco importou: `freshShell` reiniciou o registro antes dele.
    const { setReading } = await import("../src/reading");
    act(() => setReading("advanced"));
    expect(readingPressed()).toEqual([AVANCADA]);
    act(() => setReading("beginner"));
    expect(readingPressed()).toEqual([INICIANTE]);
  });

  it("o primeiro desenho já sai no nível lembrado: renderToString, sem efeitos", async () => {
    window.localStorage.setItem("ruvor-reading", "advanced");
    const { Shell } = await freshShell();
    const html = renderToString(
      <MemoryRouter initialEntries={["/ativos/ITUB4"]}>
        <Routes>
          <Route element={<Shell />}>
            <Route path="*" element={null} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    const doc = new DOMParser().parseFromString(html, "text/html");
    const group = doc.querySelector(
      `[role="group"][aria-label="${TEXTOS["casco.leitura.rotulo"]}"]`,
    );
    expect(group).not.toBeNull();
    const pressedNow = [...(group as Element).querySelectorAll("button")]
      .filter((b) => b.getAttribute("aria-pressed") === "true")
      .map((b) => b.textContent);
    expect(pressedNow).toEqual([AVANCADA]);
  });

  it("o primeiro desenho sem nada guardado sai em iniciante", async () => {
    const { Shell } = await freshShell();
    const html = renderToString(
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route element={<Shell />}>
            <Route path="*" element={null} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(html).toContain(`aria-pressed="true">${INICIANTE}</button>`);
    expect(html).not.toContain(`aria-pressed="true">${AVANCADA}</button>`);
  });
});

describe("rodapé", () => {
  const PROVENANCE = {
    asOfDate: "2026-09-25",
    calculatedAt: "2026-09-28T14:04:02.000000-03:00",
  };

  function footer(): HTMLElement {
    return screen.getByRole("contentinfo");
  }

  it("sem proveniência: a ressalva e a fonte, e nada do cálculo", async () => {
    await renderShell("/qualquer");
    expect(within(footer()).getByText(RESSALVA)).toBeDefined();
    expect(within(footer()).getByText(TEXTOS["rodape.fonte"])).toBeDefined();
    expect(footer().querySelector("[data-provenance]")).toBeNull();
    expect(footer().textContent).not.toContain("Último pregão");
  });

  it("com proveniência: o último pregão e o instante do cálculo, e some ao sair do endereço", async () => {
    const { Shell, useShellContext } = await freshShell();

    function GivesProvenance() {
      const { setProvenance } = useShellContext();
      useEffect(() => {
        setProvenance(PROVENANCE);
      }, [setProvenance]);
      return null;
    }

    const router = createMemoryRouter(
      [
        {
          element: <Shell />,
          children: [
            { path: "ativos/:ticker", element: <GivesProvenance /> },
            { path: "*", element: null },
          ],
        },
      ],
      { initialEntries: ["/ativos/ITUB4"] },
    );
    render(<RouterProvider router={router} />);

    const asOf = await within(footer()).findByText(
      TEXTOS["rodape.ultimoPregao"]("25/09/2026"),
    );
    expect(asOf.getAttribute("data-provenance")).toBe("as-of-date");
    const calculated = within(footer()).getByText(
      TEXTOS["rodape.calculadoEm"]("28/09/2026", "14:04"),
    );
    expect(calculated.getAttribute("data-provenance")).toBe("calculated-at");
    expect(within(footer()).getByText(RESSALVA)).toBeDefined();

    await act(() => router.navigate("/outra"));
    expect(footer().querySelector("[data-provenance]")).toBeNull();
  });

  it("a tela pode limpar a proveniência", async () => {
    const { Shell, useShellContext } = await freshShell();
    let set: ((value: typeof PROVENANCE | null) => void) | null = null;

    function Holder() {
      set = useShellContext().setProvenance;
      return null;
    }

    const router = createMemoryRouter(
      [{ element: <Shell />, children: [{ path: "*", element: <Holder /> }] }],
      { initialEntries: ["/ativos/ITUB4"] },
    );
    render(<RouterProvider router={router} />);

    act(() => set?.(PROVENANCE));
    expect(footer().querySelector("[data-provenance]")).not.toBeNull();
    act(() => set?.(null));
    expect(footer().querySelector("[data-provenance]")).toBeNull();
  });
});

describe("o lugar da conta na barra (M2.1b, RF-09)", () => {
  const ME = {
    email: "ana.souza@exemplo.com",
    name: "Ana Beatriz Souza",
    role: "admin",
    must_change_password: false,
    is_staff: false,
    organization: { name: "Gestora Exemplo", slug: "gestora", is_personal: false },
  };

  const slot = () => document.querySelector(".ruvor-topbar__account") as HTMLElement;

  /** O casco sob o provedor da sessão do mesmo grafo; `me` nulo deixa o `auth/me` pendente. */
  async function renderWithSession(me: object | null, path = "/ativos/ITUB4") {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url !== "/api/v1/auth/me") return new Promise<Response>(() => {});
        if (me === null) return new Promise<Response>(() => {});
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => me,
        } as unknown as Response);
      }),
    );
    const { Shell } = await freshShell();
    const { SessionProvider } = await import("../src/session/SessionProvider");
    const router = createMemoryRouter(
      [
        {
          element: <SessionProvider />,
          children: [{ element: <Shell />, children: [{ path: "*", element: null }] }],
        },
      ],
      { initialEntries: [path] },
    );
    render(<RouterProvider router={router} />);
    await act(async () => {
      for (let i = 0; i < 20; i += 1) await Promise.resolve();
    });
  }

  it("sem o provedor: o anônimo do padrão, por último, depois da chave de tema", async () => {
    await renderShell("/ativos/ITUB4");
    const prefs = document.querySelector(".ruvor-topbar__prefs") as HTMLElement;
    const reading = readingGroup();
    const theme = screen.getByRole("group", { name: TEXTOS["casco.tema.rotulo"] });
    expect([...prefs.children]).toEqual([reading, theme, slot()]);
    expect(slot().getAttribute("data-account")).toBe("anonymous");
    expect(
      within(slot())
        .getByRole("link", { name: TEXTOS["conta.entrar"] })
        .getAttribute("href"),
    ).toBe("/entrar?next=%2Fativos%2FITUB4");
  });

  it("logado, com o provedor do mesmo grafo: o botão de conta, no mesmo lugar", async () => {
    await renderWithSession(ME);
    expect(slot().getAttribute("data-account")).toBe("authenticated");
    expect(
      within(slot()).getByRole("button", {
        name: TEXTOS["conta.menu.rotulo"](ME.name),
      }),
    ).toBeDefined();
    const prefs = document.querySelector(".ruvor-topbar__prefs") as HTMLElement;
    expect(prefs.lastElementChild).toBe(slot());
    // O alternador e a chave de tema seguem vizinhos, nessa ordem (o kit até 840 px).
    expect(readingGroup().nextElementSibling).toBe(
      screen.getByRole("group", { name: TEXTOS["casco.tema.rotulo"] }),
    );
  });

  it("carregando, com o provedor do mesmo grafo: o lugar vazio", async () => {
    await renderWithSession(null);
    expect(slot().getAttribute("data-account")).toBe("loading");
    expect(slot().childElementCount).toBe(0);
  });
});
