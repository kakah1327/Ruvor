/**
 * V-06, a metade do `next` (RF-04): só caminho interno, conferido pelo `URL` e não por prefixo
 * de texto; o destino é `pathname + search` normalizado. E o link para a entrada, que leva o
 * caminho e a busca codificados.
 */
import { describe, expect, it } from "vitest";

import { safeNext, signInHref } from "../src/session/next";

const ORIGIN = "http://localhost:5173";

describe("safeNext", () => {
  it("aceita o caminho interno com a busca", () => {
    expect(safeNext("/ativos/ITUB4?x=1", ORIGIN)).toBe("/ativos/ITUB4?x=1");
  });

  it("o destino é o normalizado pelo URL, não a cadeia recebida", () => {
    expect(safeNext("/ativos/../ativos/ITUB4?x=1#topo", ORIGIN)).toBe(
      "/ativos/ITUB4?x=1",
    );
    expect(safeNext(`${ORIGIN}/ativos/PETR4`, ORIGIN)).toBe("/ativos/PETR4");
  });

  it.each([
    ["//evil.com", "//evil.com"],
    ["/\\evil.com", "/\\evil.com"],
    ["/\\t/evil.com, com tabulação real", "/\t/evil.com"],
    ["https://evil.com", "https://evil.com"],
    ["/entrar", "/entrar"],
    ["/cadastro?next=/x", "/cadastro?next=/x"],
  ])("recusa %s → /", (_nome, next) => {
    expect(safeNext(next, ORIGIN)).toBe("/");
  });

  it("o caso da tabulação leva mesmo um caractere de tabulação", () => {
    expect("/\t/evil.com".charCodeAt(1)).toBe(9);
  });

  it("null e a cadeia vazia → /", () => {
    expect(safeNext(null, ORIGIN)).toBe("/");
    expect(safeNext("", ORIGIN)).toBe("/");
  });

  it("sem origem, usa a da janela", () => {
    expect(safeNext("/ativos/ITUB4?x=1")).toBe("/ativos/ITUB4?x=1");
    expect(safeNext("//evil.com")).toBe("/");
  });
});

describe("signInHref", () => {
  it("leva o caminho e a busca codificados no next", () => {
    expect(signInHref("/ativos/ITUB4?x=1&y=2")).toBe(
      "/entrar?next=%2Fativos%2FITUB4%3Fx%3D1%26y%3D2",
    );
  });

  it("o next do link volta inteiro pelo safeNext", () => {
    const next = new URL(signInHref("/ativos/ITUB4?x=1&y=2"), ORIGIN).searchParams.get(
      "next",
    );
    expect(safeNext(next, ORIGIN)).toBe("/ativos/ITUB4?x=1&y=2");
  });
});
