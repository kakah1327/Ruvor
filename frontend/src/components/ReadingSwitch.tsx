import { TEXTOS } from "../content/textos";
import { type Reading, setReading, useReading } from "../reading";

/** A ordem e o rótulo de cada posição, como no `casco-e-preco.html`: iniciante, avançada. */
const CHOICES = [
  { reading: "beginner", label: "casco.leitura.iniciante" },
  { reading: "advanced", label: "casco.leitura.avancada" },
] as const satisfies ReadonlyArray<{ reading: Reading; label: keyof typeof TEXTOS }>;

/**
 * O alternador do nível de leitura (RF-01 a RF-03 do M2.3), no molde da chave de tema: dois
 * botões com rótulo e `aria-pressed`, num grupo com rótulo acessível. Quem guarda, lembra e
 * avisa é `reading.ts`.
 *
 * O nível vem de `useReading`, que lê o lembrado de forma síncrona: o primeiro desenho já sai
 * no nível certo, sem efeito (V-03), e a troca feita em outro ponto da página move o alternador.
 */
export function ReadingSwitch() {
  const current = useReading();

  return (
    // biome-ignore lint/a11y/useSemanticElements: o alternador é a .ruvor-segmented do kit, um div com role="group" como a chave de tema e o casco-e-preco.html aprovado; um fieldset traria margem e largura mínima do navegador que a classe não zera.
    <div
      className="ruvor-segmented"
      role="group"
      aria-label={TEXTOS["casco.leitura.rotulo"]}
    >
      {CHOICES.map(({ reading, label }) => (
        <button
          key={reading}
          className="ruvor-segmented__btn"
          type="button"
          aria-pressed={current === reading}
          onClick={() => setReading(reading)}
        >
          {TEXTOS[label]}
        </button>
      ))}
    </div>
  );
}
