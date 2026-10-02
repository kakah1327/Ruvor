/**
 * O `App` é o casco nas rotas (RF-01 a RF-04): a barra com a marca e a chave de tema, e o
 * rodapé. Ele deixou de consultar `/health` — a tela de verificação saiu.
 */
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { RESSALVA } from "../src/content/ressalva";
import { TEXTOS } from "../src/content/textos";

// A rota do ativo monta a tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` já
// no import, e o jsdom não o tem. Aqui nenhum gráfico chega a ser desenhado.
vi.mock("uplot", () => ({ default: class {} }));

afterEach(() => {
  cleanup(); // sem globals: true no Vitest, a Testing Library nao limpa o DOM sozinha
  vi.unstubAllGlobals();
  window.history.replaceState(null, "", "/");
});

describe("App", () => {
  it("renderiza o casco: a marca que leva à busca, a chave de tema e o rodapé", () => {
    render(<App />);
    const banner = screen.getByRole("banner");
    const brand = within(banner).getByRole("link", {
      name: TEXTOS["casco.marca.rotulo"],
    });
    expect(brand.getAttribute("href")).toBe("/");
    expect(within(brand).getByText(TEXTOS["casco.marca"])).toBeDefined();
    expect(brand.querySelector("img")?.getAttribute("alt")).toBe("");
    expect(
      within(banner).getByRole("group", { name: TEXTOS["casco.tema.rotulo"] }),
    ).toBeDefined();
    expect(within(screen.getByRole("contentinfo")).getByText(RESSALVA)).toBeDefined();
    expect(screen.getByRole("main")).toBeDefined();
  });

  it("em /, o único pedido é o da sugestão: nem /health nem outra rota (M1.7, RF-10)", () => {
    const fetchSpy = vi.fn((_url: string) => new Promise<Response>(() => {}));
    vi.stubGlobal("fetch", fetchSpy);
    render(<App />);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(fetchSpy.mock.calls[0]?.[0]).toBe("/api/v1/assets?has_risk=true&limit=8");
  });

  it("endereço desconhecido mostra a página não encontrada dentro do casco", () => {
    window.history.replaceState(null, "", "/qualquer-coisa");
    render(<App />);
    expect(
      screen.getByRole("heading", { name: TEXTOS["casco.naoEncontrada.titulo"] }),
    ).toBeDefined();
    expect(screen.getByRole("banner")).toBeDefined();
    expect(screen.getByRole("contentinfo")).toBeDefined();
  });
});
