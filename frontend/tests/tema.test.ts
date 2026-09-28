/**
 * V-03 (parte pura): o tema grava e remove `data-theme`, lembra a escolha em
 * `localStorage`, funciona com `localStorage` lançando exceção, e avisa quem assina —
 * na troca da escolha e na troca de `prefers-color-scheme` com a escolha em sistema.
 *
 * O módulo guarda a escolha em memória: cada teste o importa de novo.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

type ThemeModule = typeof import("../src/theme");

async function freshTheme(): Promise<ThemeModule> {
  vi.resetModules();
  return import("../src/theme");
}

function throwingStorage(): void {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
}

/** Um `matchMedia` falso, com o disparo da mudança à mão. */
function fakeMatchMedia(): { fire: () => void } {
  const handlers = new Set<() => void>();
  vi.stubGlobal(
    "matchMedia",
    vi.fn((query: string) => ({
      matches: false,
      media: query,
      addEventListener: (_type: string, handler: () => void) => handlers.add(handler),
      removeEventListener: (_type: string, handler: () => void) =>
        handlers.delete(handler),
    })),
  );
  return {
    fire: () => {
      for (const handler of handlers) {
        handler();
      }
    },
  };
}

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("tema", () => {
  it("o padrão é sistema, sem data-theme", async () => {
    const theme = await freshTheme();
    expect(theme.initTheme()).toBe("system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("claro e escuro gravam data-theme; sistema o remove", async () => {
    const theme = await freshTheme();
    theme.setTheme("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    theme.setTheme("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    theme.setTheme("system");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });

  it("lembra a escolha na chave ruvor-theme", async () => {
    const first = await freshTheme();
    first.setTheme("dark");
    expect(window.localStorage.getItem("ruvor-theme")).toBe("dark");

    document.documentElement.removeAttribute("data-theme");
    const second = await freshTheme();
    expect(second.initTheme()).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("valor lembrado inválido vale sistema", async () => {
    window.localStorage.setItem("ruvor-theme", "roxo");
    const theme = await freshTheme();
    expect(theme.initTheme()).toBe("system");
  });

  it("funciona com localStorage lançando exceção", async () => {
    throwingStorage();
    const theme = await freshTheme();
    expect(() => theme.initTheme()).not.toThrow();
    expect(theme.getTheme()).toBe("system");
    expect(() => theme.setTheme("dark")).not.toThrow();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    // A escolha vale nesta página, em memória.
    expect(theme.getTheme()).toBe("dark");
  });

  it("funciona sem matchMedia", async () => {
    vi.stubGlobal("matchMedia", undefined);
    const theme = await freshTheme();
    const callback = vi.fn();
    const off = theme.onThemeChange(callback);
    theme.setTheme("light");
    expect(callback).toHaveBeenCalledWith("light");
    off();
  });

  it("onThemeChange avisa na troca da escolha e para de avisar depois de cancelar", async () => {
    fakeMatchMedia();
    const theme = await freshTheme();
    const callback = vi.fn();
    const off = theme.onThemeChange(callback);
    theme.setTheme("dark");
    expect(callback).toHaveBeenLastCalledWith("dark");
    off();
    theme.setTheme("light");
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it("onThemeChange avisa na mudança de prefers-color-scheme só com a escolha em sistema", async () => {
    const media = fakeMatchMedia();
    const theme = await freshTheme();
    const callback = vi.fn();
    const off = theme.onThemeChange(callback);

    media.fire();
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenLastCalledWith("system");

    theme.setTheme("dark");
    callback.mockClear();
    media.fire();
    expect(callback).not.toHaveBeenCalled();

    off();
    theme.setTheme("system");
    callback.mockClear();
    media.fire();
    expect(callback).not.toHaveBeenCalled();
  });
});
