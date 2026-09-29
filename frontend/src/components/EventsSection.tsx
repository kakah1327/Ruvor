import { useId, useState } from "react";

import type { Load } from "../api/resource";
import type { EventRow, Events } from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatCurrencyPrecise, formatDate, formatInteger } from "../format/numbers";
import { Glyph } from "./Glyph";
import { SectionError, SectionSkeleton } from "./SectionStatus";

type Props = {
  load: Load<Events>;
  /**
   * O fim da janela de 12 meses, `AAAA-MM-DD`: a data do último fechamento, como no
   * `ativo.html`. Nulo enquanto a identidade carrega — a seção espera por ela.
   */
  referenceDate: string | null;
  onRetry: () => void;
};

/** O início da janela: a mesma data, um ano antes (a janela exclui o início, como no mockup). */
function yearBefore(date: string): string {
  const [year, month, day] = date.split("-");
  return `${Number(year) - 1}-${month}-${day}`;
}

function EventLine({ event }: { event: EventRow }) {
  const value =
    event.kind === "dividend"
      ? event.amount === null
        ? "—"
        : TEXTOS["ativo.eventos.valor"](formatCurrencyPrecise(Number(event.amount)))
      : event.numerator === null || event.denominator === null
        ? "—"
        : TEXTOS["ativo.eventos.proporcao"](
            formatInteger(Number(event.numerator)),
            formatInteger(Number(event.denominator)),
          );
  return (
    <tr>
      <td className="ruvor-num">{formatDate(event.date)}</td>
      <td>{TEXTOS[`ativo.eventos.${event.kind}`]}</td>
      <td className="ruvor-num">{value}</td>
    </tr>
  );
}

/**
 * Proventos e desdobramentos (RF-09): os dos 12 meses até o último fechamento, do mais novo
 * ao mais antigo — data, tipo, valor ou proporção —, e "ver todos" para a série inteira. Sem
 * eventos no período, a frase.
 */
export function EventsSection({ load, referenceDate, onRetry }: Props) {
  const titleId = useId();
  const [showAll, setShowAll] = useState(false);
  const ready = load.state === "ok" && referenceDate !== null;

  let body: React.ReactNode;
  if (load.state === "error") {
    body = <SectionError onRetry={onRetry} />;
  } else if (load.state === "loading" || referenceDate === null) {
    body = <SectionSkeleton short />;
  } else {
    const start = yearBefore(referenceDate);
    const all = [...load.data.results].sort((a, b) => b.date.localeCompare(a.date));
    const recent = all.filter((e) => e.date > start && e.date <= referenceDate);
    const list = showAll ? all : recent;
    body = (
      <div className="ruvor-stack">
        {list.length === 0 ? (
          <p className="ruvor-muted">{TEXTOS["ativo.eventos.nenhum"]}</p>
        ) : (
          <table className="ruvor-table ruvor-table--end">
            <thead>
              <tr>
                <th scope="col">{TEXTOS["ativo.eventos.col.data"]}</th>
                <th scope="col">{TEXTOS["ativo.eventos.col.tipo"]}</th>
                <th scope="col">{TEXTOS["ativo.eventos.col.valor"]}</th>
              </tr>
            </thead>
            <tbody>
              {list.map((event) => (
                <EventLine key={`${event.date}-${event.kind}`} event={event} />
              ))}
            </tbody>
          </table>
        )}
        {all.length > recent.length && (
          <div>
            <button
              className="ruvor-btn ruvor-btn--ghost"
              type="button"
              aria-expanded={showAll}
              onClick={() => setShowAll((open) => !open)}
            >
              {showAll
                ? TEXTOS["ativo.eventos.verMenos"]
                : TEXTOS["ativo.eventos.verTodos"](formatInteger(all.length))}
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <section className="ruvor-panel" aria-labelledby={titleId}>
      <div className="ruvor-panel__head">
        <Glyph name="calendar-blank" />
        <h2 className="ruvor-h3" id={titleId}>
          {TEXTOS["ativo.eventos.titulo"]}
        </h2>
        {ready && (
          <span className="ruvor-push ruvor-muted">
            {TEXTOS["ativo.eventos.periodo"](formatDate(referenceDate))}
          </span>
        )}
      </div>
      <div
        className="ruvor-panel__body"
        aria-busy={
          load.state === "loading" || (load.state === "ok" && !ready) || undefined
        }
      >
        {body}
      </div>
    </section>
  );
}
