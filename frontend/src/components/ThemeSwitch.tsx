import { useEffect, useState } from "react";

import { TEXTOS } from "../content/textos";
import { getTheme, onThemeChange, setTheme, type ThemeChoice } from "../theme";

/** A ordem e o rótulo de cada posição, como no `busca.html`: claro, escuro, sistema. */
const CHOICES = [
  { choice: "light", label: "casco.tema.claro" },
  { choice: "dark", label: "casco.tema.escuro" },
  { choice: "system", label: "casco.tema.sistema" },
] as const satisfies ReadonlyArray<{ choice: ThemeChoice; label: keyof typeof TEXTOS }>;

/**
 * A chave de tema (RF-03): três botões com rótulo e `aria-pressed`. Claro e escuro gravam
 * `data-theme` em `<html>`; sistema o remove — quem faz é `theme.ts`, que também lembra a
 * escolha.
 */
export function ThemeSwitch() {
  const [current, setCurrent] = useState<ThemeChoice>(getTheme);

  // Quem mais chamar `setTheme` na página também move a chave.
  useEffect(() => onThemeChange(setCurrent), []);

  return (
    // biome-ignore lint/a11y/useSemanticElements: a chave é a .ruvor-segmented do kit, um div com role="group" como no busca.html aprovado; um fieldset traria margem e largura mínima do navegador que a classe não zera.
    <div
      className="ruvor-segmented"
      role="group"
      aria-label={TEXTOS["casco.tema.rotulo"]}
    >
      {CHOICES.map(({ choice, label }) => (
        <button
          key={choice}
          className="ruvor-segmented__btn"
          type="button"
          aria-pressed={current === choice}
          onClick={() => {
            setTheme(choice);
            setCurrent(choice);
          }}
        >
          {TEXTOS[label]}
        </button>
      ))}
    </div>
  );
}
