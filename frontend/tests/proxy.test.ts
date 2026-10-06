// @vitest-environment node
import { describe, expect, it } from "vitest";

import config from "../vite.config";

// RF-19: a forma curta do proxy (so a string do alvo) liga o changeOrigin, e o Django
// recebe Host: web:8000 com Origin: localhost:<porta> -- a checagem de origem do CSRF
// recusa toda escrita de quem esta logado. As duas entradas tem de ser a forma longa.
describe("o proxy do Vite preserva o Host (RF-19)", () => {
  const proxy = config.server?.proxy ?? {};

  it.each(["/api", "/health"])("%s e objeto com changeOrigin false", (path) => {
    const entry = proxy[path];
    expect(typeof entry).toBe("object");
    expect(entry).not.toBeNull();
    expect(entry).toHaveProperty("changeOrigin", false);
  });

  it("as duas entradas apontam para o mesmo alvo", () => {
    const api = proxy["/api"];
    const health = proxy["/health"];
    if (typeof api !== "object" || typeof health !== "object") {
      throw new Error("entrada do proxy na forma curta");
    }
    expect(typeof api.target).toBe("string");
    expect(api.target).toBe(health.target);
  });
});
