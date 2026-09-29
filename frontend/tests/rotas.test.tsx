/**
 * V-02 (menos o carregamento direto no navegador, que é da execução real): as rotas do
 * RF-01 — `/`, `/ativos/ITUB4`, `/ativos/itub4` vira `ITUB4` sem entrada nova no
 * histórico, endereço desconhecido dá "página não encontrada", e o voltar funciona.
 */
import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App, routes } from "../src/App";
import { TEXTOS } from "../src/content/textos";

// A rota do ativo monta a tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` já
// no import, e o jsdom não o tem. Aqui nenhum gráfico chega a ser desenhado.
vi.mock("uplot", () => ({ default: class {} }));

afterEach(() => {
  cleanup(); // sem globals: true no Vitest, a Testing Library nao limpa o DOM sozinha
  window.history.replaceState(null, "", "/");
});

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(<RouterProvider router={router} />);
  return router;
}

function notFoundHeading(): HTMLElement | null {
  return screen.queryByRole("heading", { name: TEXTOS["casco.naoEncontrada.titulo"] });
}

describe("rotas", () => {
  it("/ abre no casco, sem a página não encontrada", () => {
    const router = renderAt("/");
    expect(router.state.location.pathname).toBe("/");
    expect(screen.getByRole("banner")).toBeDefined();
    expect(notFoundHeading()).toBeNull();
  });

  it("/ativos/ITUB4 abre sem trocar o endereço", () => {
    const router = renderAt("/ativos/ITUB4");
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    expect(router.state.historyAction).toBe("POP");
    expect(notFoundHeading()).toBeNull();
  });

  it("/ativos/itub4 vira /ativos/ITUB4 por substituição", async () => {
    const router = renderAt("/ativos/itub4");
    await waitFor(() => expect(router.state.location.pathname).toBe("/ativos/ITUB4"));
    expect(router.state.historyAction).toBe("REPLACE");
  });

  it("/ativos/itub4 vira /ativos/ITUB4 sem entrada nova no histórico do navegador", async () => {
    window.history.replaceState(null, "", "/ativos/itub4");
    const before = window.history.length;
    render(<App />);
    await waitFor(() => expect(window.location.pathname).toBe("/ativos/ITUB4"));
    expect(window.history.length).toBe(before);
  });

  it("endereço desconhecido mostra a página não encontrada, com o endereço e o caminho para a busca", () => {
    renderAt("/ativo/itub4");
    expect(notFoundHeading()).not.toBeNull();
    expect(screen.getByText("/ativo/itub4").className).toBe("ruvor-path");
    const back = screen.getByRole("link", { name: TEXTOS["casco.irParaBusca"] });
    expect(back.getAttribute("href")).toBe("/");
  });

  it("o voltar funciona entre a busca e o ativo", async () => {
    const router = renderAt("/");
    await act(() => router.navigate("/ativos/ITUB4"));
    expect(router.state.location.pathname).toBe("/ativos/ITUB4");
    await act(() => router.navigate(-1));
    expect(router.state.location.pathname).toBe("/");
  });

  it("a marca leva à busca", () => {
    renderAt("/ativo/itub4");
    const brand = screen.getByRole("link", { name: TEXTOS["casco.marca.rotulo"] });
    expect(brand.getAttribute("href")).toBe("/");
  });
});
