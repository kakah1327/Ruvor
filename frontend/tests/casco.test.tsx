/**
 * V-03 completo, na tela: a chave de tema grava e remove `data-theme`, lembra a escolha, e a
 * tela funciona com `localStorage` lançando exceção. E o rodapé (RF-04): a ressalva e a
 * fonte em toda tela, e a proveniência só quando a tela a dá, só no endereço em que a deu.
 *
 * `theme.ts` guarda a escolha em memória: cada teste importa o casco de novo.
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
import { createMemoryRouter, RouterProvider } from "react-router";
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
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
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
