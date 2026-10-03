/**
 * O `App` é o casco nas rotas (RF-01 a RF-04): a barra com a marca e a chave de tema, e o
 * rodapé. Ele deixou de consultar `/health` — a tela de verificação saiu. Desde o M2.1b, a
 * rota de layout da sessão pede o `auth/me` ao montar (RF-03): o duplo do `fetch` responde
 * 401 (anônimo) por padrão, e deixa o resto pendente.
 */
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";
import { RESSALVA } from "../src/content/ressalva";
import { TEXTOS } from "../src/content/textos";

// A rota do ativo monta a tela do ativo, que importa o uPlot; o uPlot pede `matchMedia` já
// no import, e o jsdom não o tem. Aqui nenhum gráfico chega a ser desenhado.
vi.mock("uplot", () => ({ default: class {} }));

const ME_URL = "/api/v1/auth/me";
const SUGGESTION_URL = "/api/v1/assets?has_risk=true&limit=8";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) =>
      url === ME_URL
        ? Promise.resolve({
            ok: false,
            status: 401,
            json: async () => ({
              error: { code: "not_authenticated", message: "falhou", details: {} },
            }),
          } as unknown as Response)
        : new Promise<Response>(() => {}),
    ),
  );
});

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

  it("em /, ao montar, só o auth/me e a sugestão: nem /health nem outra rota (M2.1b RF-03, M1.7 RF-10)", () => {
    const fetchSpy = vi.fn((_url: string) => new Promise<Response>(() => {}));
    vi.stubGlobal("fetch", fetchSpy);
    render(<App />);
    expect(fetchSpy).toHaveBeenCalledTimes(2);
    expect(fetchSpy.mock.calls.map(([url]) => url).sort()).toEqual(
      [ME_URL, SUGGESTION_URL].sort(),
    );
  });

  it("fora de /, ao montar, o único pedido do App é o auth/me (M2.1b, RF-03)", () => {
    const fetchSpy = vi.fn((_url: string) => new Promise<Response>(() => {}));
    vi.stubGlobal("fetch", fetchSpy);
    window.history.replaceState(null, "", "/qualquer-coisa");
    render(<App />);
    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(fetchSpy.mock.calls[0]?.[0]).toBe(ME_URL);
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
