/**
 * RF-02 e RF-03, a parte pura do nível de leitura: o padrão é iniciante; a escolha é lembrada
 * em `localStorage`, na chave `ruvor-reading`, lida dentro de `try`; valor desconhecido vale
 * iniciante; `data-reading` em `<html>` existe desde a primeira leitura; a troca grava, aplica e
 * avisa quem assina.
 *
 * O módulo guarda o nível em memória: cada teste o importa de novo (o molde de `tema.test.ts`).
 */
import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TEXTOS } from "../src/content/textos";

type ReadingModule = typeof import("../src/reading");

async function freshReading(): Promise<ReadingModule> {
  vi.resetModules();
  return import("../src/reading");
}

function throwingStorage(): void {
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
  vi.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
    throw new DOMException("bloqueado", "SecurityError");
  });
}

const marca = (): string | undefined => document.documentElement.dataset.reading;

beforeEach(() => {
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-reading");
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("o nível de leitura", () => {
  it("sem nada guardado, a primeira leitura é iniciante, e data-reading também", async () => {
    const reading = await freshReading();
    expect(marca()).toBeUndefined();
    expect(reading.getReading()).toBe("beginner");
    expect(marca()).toBe("beginner");
  });

  it("com advanced guardado, a primeira leitura é avançada, e data-reading também", async () => {
    window.localStorage.setItem("ruvor-reading", "advanced");
    const reading = await freshReading();
    expect(reading.getReading()).toBe("advanced");
    expect(marca()).toBe("advanced");
  });

  it("com beginner guardado, iniciante", async () => {
    window.localStorage.setItem("ruvor-reading", "beginner");
    const reading = await freshReading();
    expect(reading.getReading()).toBe("beginner");
    expect(marca()).toBe("beginner");
  });

  it.each(["expert", "Advanced", "", "true"])(
    "valor guardado desconhecido %j vale iniciante",
    async (valor) => {
      window.localStorage.setItem("ruvor-reading", valor);
      const reading = await freshReading();
      expect(reading.getReading()).toBe("beginner");
      expect(marca()).toBe("beginner");
    },
  );

  it("funciona com localStorage lançando exceção", async () => {
    throwingStorage();
    const reading = await freshReading();
    expect(() => reading.getReading()).not.toThrow();
    expect(reading.getReading()).toBe("beginner");
    expect(marca()).toBe("beginner");
    expect(() => reading.setReading("advanced")).not.toThrow();
    // A escolha vale nesta página, em memória.
    expect(reading.getReading()).toBe("advanced");
    expect(marca()).toBe("advanced");
    expect(() => reading.resetReadingForTests()).not.toThrow();
  });

  it("setReading grava, avisa o assinante e troca data-reading", async () => {
    const reading = await freshReading();
    expect(reading.getReading()).toBe("beginner");
    const callback = vi.fn();
    const off = reading.onReadingChange(callback);

    reading.setReading("advanced");
    expect(window.localStorage.getItem("ruvor-reading")).toBe("advanced");
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenLastCalledWith("advanced");
    expect(marca()).toBe("advanced");
    expect(reading.getReading()).toBe("advanced");

    reading.setReading("beginner");
    expect(window.localStorage.getItem("ruvor-reading")).toBe("beginner");
    expect(callback).toHaveBeenLastCalledWith("beginner");
    expect(marca()).toBe("beginner");

    off();
    reading.setReading("advanced");
    expect(callback).toHaveBeenCalledTimes(2);
  });

  it("a escolha gravada vale na próxima carga", async () => {
    const first = await freshReading();
    first.setReading("advanced");

    document.documentElement.removeAttribute("data-reading");
    const second = await freshReading();
    expect(second.getReading()).toBe("advanced");
    expect(marca()).toBe("advanced");
  });

  it("useReading sai no nível lembrado e acompanha a troca feita em outro ponto", async () => {
    window.localStorage.setItem("ruvor-reading", "advanced");
    const reading = await freshReading();
    const { result } = renderHook(() => reading.useReading());
    expect(result.current).toBe("advanced");
    act(() => reading.setReading("beginner"));
    expect(result.current).toBe("beginner");
  });

  it("resetReadingForTests volta a iniciante, limpa o armazenamento e tira data-reading", async () => {
    const reading = await freshReading();
    reading.setReading("advanced");
    reading.resetReadingForTests();
    expect(reading.getReading()).toBe("beginner");
    expect(window.localStorage.getItem("ruvor-reading")).toBeNull();
    expect(document.documentElement.hasAttribute("data-reading")).toBe(false);
  });

  it("textFor devolve a iniciante no nível iniciante", async () => {
    const reading = await freshReading();
    expect(reading.textFor("ativo.precoAjustado", "beginner")).toBe(
      TEXTOS["ativo.precoAjustado"],
    );
    // Função: compara a saída (o `vi.resetModules` deu a `reading` outra instância de textos).
    expect(reading.textFor("ativo.ultimoFechamento", "beginner")("26/09/2026")).toBe(
      TEXTOS["ativo.ultimoFechamento"]("26/09/2026"),
    );
  });

  it("textFor devolve a avançada no nível avançado", async () => {
    const reading = await freshReading();
    const { TEXTOS_AVANCADOS } = await import("../src/content/avancado");
    expect(reading.textFor("ativo.precoAjustado", "advanced")).toBe(
      TEXTOS_AVANCADOS["ativo.precoAjustado"],
    );
    expect(reading.textFor("ativo.ultimoFechamento", "advanced")("26/09/2026")).toBe(
      TEXTOS_AVANCADOS["ativo.ultimoFechamento"]("26/09/2026"),
    );
    expect(reading.textFor("ativo.precoAjustado", "advanced")).not.toBe(
      TEXTOS["ativo.precoAjustado"],
    );
  });
});
