import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "../src/App";

function stubFetch(body: unknown, ok = true): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({ ok, json: async () => body })),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("tela de verificação", () => {
  it("renderiza a marca e o estado ok do backend", async () => {
    stubFetch({ status: "ok" });
    render(<App />);
    expect(screen.getByRole("heading", { name: "Ruvor" })).toBeDefined();
    expect(screen.getByAltText("Símbolo Ruvor")).toBeDefined();
    expect(await screen.findByText("Backend: ok")).toBeDefined();
  });

  it("mostra indisponível quando o backend não responde", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new Error("rede");
      }),
    );
    render(<App />);
    expect(await screen.findByText("Backend: indisponível")).toBeDefined();
  });
});
