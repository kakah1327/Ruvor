/**
 * O tema (RF-03, D-88). Três escolhas: claro e escuro gravam `data-theme` em `<html>`;
 * sistema o remove, e a folha de tokens segue `prefers-color-scheme`.
 *
 * A escolha é lembrada em `localStorage`, na chave `ruvor-theme`, lida e escrita dentro de
 * `try`: sem armazenamento (bloqueado, cheio, modo privado), a escolha vale só nesta
 * página, e a tela funciona igual. O padrão é sistema.
 */

export type ThemeChoice = "light" | "dark" | "system";

export const THEME_KEY = "ruvor-theme";

const DARK_QUERY = "(prefers-color-scheme: dark)";

function isChoice(value: unknown): value is ThemeChoice {
  return value === "light" || value === "dark" || value === "system";
}

function readStored(): ThemeChoice {
  try {
    const value = window.localStorage.getItem(THEME_KEY);
    return isChoice(value) ? value : "system";
  } catch {
    return "system";
  }
}

function writeStored(choice: ThemeChoice): void {
  try {
    window.localStorage.setItem(THEME_KEY, choice);
  } catch {
    // Sem armazenamento, a escolha vale só nesta página.
  }
}

// A escolha corrente, em memória: continua valendo quando o armazenamento falha.
let current: ThemeChoice | null = null;

const listeners = new Set<(choice: ThemeChoice) => void>();

/** A escolha corrente — a lembrada, na primeira leitura. */
export function getTheme(): ThemeChoice {
  if (current === null) {
    current = readStored();
  }
  return current;
}

/** Grava ou remove `data-theme` em `<html>`, conforme a escolha. */
export function applyTheme(choice: ThemeChoice): void {
  const root = document.documentElement;
  if (choice === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", choice);
  }
}

/** Aplica o tema lembrado. `main.tsx` chama antes do primeiro desenho. */
export function initTheme(): ThemeChoice {
  const choice = getTheme();
  applyTheme(choice);
  return choice;
}

/** Troca a escolha: lembra, aplica e avisa quem assina. */
export function setTheme(choice: ThemeChoice): void {
  current = choice;
  writeStored(choice);
  applyTheme(choice);
  for (const listener of [...listeners]) {
    listener(choice);
  }
}

/**
 * Avisa quando a escolha muda e quando `prefers-color-scheme` muda com a escolha em
 * sistema — os gráficos releem as cores. Devolve a função que cancela a assinatura.
 */
export function onThemeChange(callback: (choice: ThemeChoice) => void): () => void {
  listeners.add(callback);
  const media =
    typeof window.matchMedia === "function" ? window.matchMedia(DARK_QUERY) : null;
  const onMedia = (): void => {
    if (getTheme() === "system") {
      callback("system");
    }
  };
  media?.addEventListener("change", onMedia);
  return () => {
    listeners.delete(callback);
    media?.removeEventListener("change", onMedia);
  };
}
