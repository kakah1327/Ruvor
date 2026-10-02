/**
 * O nível de leitura (RF-02, RF-03): iniciante ou avançada. O padrão é iniciante.
 *
 * A escolha é lembrada em `localStorage`, na chave `ruvor-reading`, lida e escrita dentro de
 * `try`, como `theme.ts` faz com o tema: sem armazenamento, a escolha vale só nesta página, e
 * a tela funciona igual; valor desconhecido lido vale iniciante.
 *
 * `getReading` aplica `data-reading` em `<html>` já na primeira leitura, e `useReading` usa
 * `getReading` como leitura síncrona: o primeiro desenho sai no nível lembrado, sem efeito.
 */
import { useSyncExternalStore } from "react";

import { type Leitura, type LeituraKey, TEXTOS_AVANCADOS } from "./content/avancado";
import { TEXTOS } from "./content/textos";

export type Reading = "beginner" | "advanced";

export const READING_KEY = "ruvor-reading";

function isReading(value: unknown): value is Reading {
  return value === "beginner" || value === "advanced";
}

function readStored(): Reading {
  try {
    const value = window.localStorage.getItem(READING_KEY);
    return isReading(value) ? value : "beginner";
  } catch {
    return "beginner";
  }
}

function writeStored(reading: Reading): void {
  try {
    window.localStorage.setItem(READING_KEY, reading);
  } catch {
    // Sem armazenamento, a escolha vale só nesta página.
  }
}

/** Grava `data-reading` em `<html>` — a marca que a execução real confere. */
function applyReading(reading: Reading): void {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-reading", reading);
  }
}

// O nível corrente, em memória: continua valendo quando o armazenamento falha.
let current: Reading | null = null;

const listeners = new Set<(reading: Reading) => void>();

/** O nível corrente — o lembrado, na primeira leitura, que também aplica `data-reading`. */
export function getReading(): Reading {
  if (current === null) {
    current = readStored();
    applyReading(current);
  }
  return current;
}

/** Troca o nível: lembra, aplica `data-reading` e avisa quem assina. */
export function setReading(reading: Reading): void {
  current = reading;
  writeStored(reading);
  applyReading(reading);
  for (const listener of [...listeners]) {
    listener(reading);
  }
}

/** Avisa quando o nível muda. Devolve a função que cancela a assinatura. */
export function onReadingChange(callback: (reading: Reading) => void): () => void {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

/** O nível corrente num componente, já no primeiro desenho, e a troca feita em outro ponto. */
export function useReading(): Reading {
  return useSyncExternalStore(onReadingChange, getReading, getReading);
}

/**
 * Só para `tests/`: volta o nível em memória a iniciante, limpa o armazenamento e tira
 * `data-reading` de `<html>`.
 */
export function resetReadingForTests(): void {
  current = "beginner";
  try {
    window.localStorage.removeItem(READING_KEY);
  } catch {
    // Sem armazenamento, não há o que limpar.
  }
  if (typeof document !== "undefined") {
    document.documentElement.removeAttribute("data-reading");
  }
}

/** A frase de uma chave da lista fechada no nível pedido: a avançada ou a iniciante. */
export function textFor<K extends LeituraKey>(
  key: K,
  reading: Reading,
): Leitura<(typeof TEXTOS)[K]> {
  return reading === "advanced"
    ? TEXTOS_AVANCADOS[key]
    : (TEXTOS[key] as Leitura<(typeof TEXTOS)[K]>);
}
