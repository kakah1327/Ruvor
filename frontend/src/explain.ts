/**
 * As explicações da tela do ativo: escondidas por padrão, mostradas pelo botão da barra de abas.
 *
 * A escolha é lembrada em `localStorage`, na chave `ruvor-explain`, lida e escrita dentro de
 * `try`, como `reading.ts` faz com o nível: sem armazenamento, a escolha vale só nesta página.
 * O texto não sai da página: a folha o esconde pela marca `data-explain="off"` no raiz da tela.
 */
import { useCallback, useState } from "react";

export const EXPLAIN_KEY = "ruvor-explain";

function readStored(): boolean {
  try {
    return window.localStorage.getItem(EXPLAIN_KEY) === "on";
  } catch {
    return false;
  }
}

function writeStored(on: boolean): void {
  try {
    window.localStorage.setItem(EXPLAIN_KEY, on ? "on" : "off");
  } catch {
    // Sem armazenamento, a escolha vale só nesta página.
  }
}

/** Se as explicações estão à vista, e a troca, que lembra a escolha. */
export function useExplain(): [boolean, () => void] {
  const [on, setOn] = useState(readStored);
  const toggle = useCallback(() => {
    setOn((value) => {
      writeStored(!value);
      return !value;
    });
  }, []);
  return [on, toggle];
}
