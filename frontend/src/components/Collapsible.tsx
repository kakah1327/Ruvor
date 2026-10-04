import { type ReactNode, useId, useState } from "react";

import { type Reading, useReading } from "../reading";
import { Glyph } from "./Glyph";

type Props = {
  /** Vira `data-collapsible`: a marca que a execução real confere. */
  name: "moments" | "models" | "trail" | "lab-tests" | "lab-trail";
  /** O texto do botão, de `textos.ts` — um só, nos dois estados. */
  label: string;
  children: ReactNode;
};

/** O padrão de cada nível (RF-07 do M2.3): iniciante fecha, avançada abre. */
function openFor(reading: Reading): boolean {
  return reading === "advanced";
}

/**
 * O recolhimento (RF-06, RF-07 do M2.3; o controle do `comportamento.html` aprovado): um botão
 * com rótulo, `aria-expanded` e `aria-controls`, e o conteúdo logo abaixo dele.
 *
 * Aberto por padrão na leitura avançada, fechado na iniciante; trocar o nível reaplica o padrão
 * — o estado guarda o nível em que foi decidido, e o nível novo o reinicia ainda no desenho, sem
 * efeito e sem remontar o conteúdo —; abrir não é lembrado. O conteúdo fechado **não é
 * desenhado** (fora da árvore acessível e do fluxo): o `aria-controls` aponta para o id que só
 * existe aberto, escolha registrada no plano. Nunca dentro de elemento com `aria-live` (V-05).
 */
export function Collapsible({ name, label, children }: Props) {
  const reading = useReading();
  const contentId = useId();
  const [state, setState] = useState(() => ({ reading, open: openFor(reading) }));

  let open = state.open;
  if (state.reading !== reading) {
    // O nível mudou: o padrão dele vale de novo (o molde do React para estado que depende de
    // um valor anterior — atualizar durante o desenho, não num efeito).
    open = openFor(reading);
    setState({ reading, open });
  }

  return (
    <div className="ruvor-collapsible" data-collapsible={name} data-open={open}>
      <button
        className="ruvor-collapsible__toggle"
        type="button"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setState({ reading, open: !open })}
      >
        <Glyph name="caret-right" />
        <span>{label}</span>
      </button>
      {open && <div id={contentId}>{children}</div>}
    </div>
  );
}
