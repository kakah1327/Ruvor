import { useEffect, useState } from "react";

type BackendState = "pending" | "ok" | "unavailable";

const LABEL: Record<BackendState, string> = {
  pending: "verificando…",
  ok: "ok",
  unavailable: "indisponível",
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

/** F2b-10: ok so quando a resposta e 2xx e o corpo JSON tem status === "ok". */
async function checkBackend(): Promise<BackendState> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      return "unavailable";
    }
    const body: unknown = await response.json();
    const status =
      typeof body === "object" && body !== null && "status" in body
        ? (body as { status: unknown }).status
        : undefined;
    return status === "ok" ? "ok" : "unavailable";
  } catch {
    return "unavailable";
  }
}

export function App() {
  const [backend, setBackend] = useState<BackendState>("pending");

  useEffect(() => {
    let cancelled = false;
    void checkBackend().then((state) => {
      if (!cancelled) {
        setBackend(state);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="shell">
      <img className="shell__mark" alt="Símbolo Ruvor" src="/ruvor-mark.svg" />
      <h1>Ruvor</h1>
      <p role="status" className={`status status--${backend}`}>
        Backend: {LABEL[backend]}
      </p>
    </main>
  );
}
