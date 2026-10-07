import { type ReactNode, useEffect, useId, useRef } from "react";

import type { AssetItem } from "../api/types";
import { TEXTOS } from "../content/textos";
import { centsText, type EditorRow, liveSum, MAX_HOLDINGS } from "../portfolio/editor";
import { TOTAL_CENTS } from "../portfolio/weights";
import { AssetPicker } from "./AssetPicker";
import { Glyph } from "./Glyph";

type HoldingsEditorProps = {
  rows: readonly EditorRow[];
  /** As mensagens da linha da soma: a contagem e a soma, do cliente ou da API. */
  totalErrors: readonly string[];
  disabled: boolean;
  onAdd: (asset: AssetItem) => void;
  /** O texto do campo, como foi digitado: nunca reescrito. */
  onWeightChange: (index: number, text: string) => void;
  onWeightBlur: (index: number) => void;
  onRemove: (index: number) => void;
};

/**
 * O editor da composição (RF-06), como no `lista.html` aprovado: o seletor de ação e a tabela —
 * uma linha por ação, com o código, o nome, o peso (um campo de texto com `inputmode="decimal"`,
 * cujo valor é o texto digitado) e "remover" —, e no pé **a soma ao vivo** em centésimos
 * inteiros, com o quanto falta ou sobra para 100,00 e quantos pesos ainda não são número. Cada
 * mensagem fica na linha dela: a do peso embaixo do campo, a da ação embaixo do nome; a contagem
 * e a soma, na linha da soma. Ao acrescentar, a linha entra no fim e o foco vai ao peso dela.
 */
export function HoldingsEditor({
  rows,
  totalErrors,
  disabled,
  onAdd,
  onWeightChange,
  onWeightBlur,
  onRemove,
}: HoldingsEditorProps) {
  const id = useId();
  const tableRef = useRef<HTMLTableElement>(null);
  const focusLast = useRef(false);
  const taken = new Set(rows.map((row) => row.ticker));

  // A linha acrescentada pelo seletor recebe o foco no peso.
  // biome-ignore lint/correctness/useExhaustiveDependencies: `rows.length` não é lido; mudar de valor é o que dispara o foco na linha nova.
  useEffect(() => {
    if (!focusLast.current) return;
    focusLast.current = false;
    const inputs = tableRef.current?.querySelectorAll<HTMLInputElement>("input");
    inputs?.[inputs.length - 1]?.focus();
  }, [rows.length]);

  const { cents, outside } = liveSum(rows);
  let gap: ReactNode;
  if (cents === TOTAL_CENTS) {
    gap = (
      <span className="ruvor-weight-sum__gap ruvor-weight-sum__gap--exact">
        <Glyph name="check-circle" className="ruvor-glyph--sm" />{" "}
        {TEXTOS["carteiras.soma.exata"]}
      </span>
    );
  } else if (cents < TOTAL_CENTS) {
    gap = (
      <span className="ruvor-weight-sum__gap">
        {TEXTOS["carteiras.soma.abaixo"](centsText(TOTAL_CENTS - cents))}
      </span>
    );
  } else {
    gap = (
      <span className="ruvor-weight-sum__gap">
        {TEXTOS["carteiras.soma.acima"](centsText(cents - TOTAL_CENTS))}
      </span>
    );
  }

  return (
    <>
      <AssetPicker
        taken={taken}
        full={rows.length >= MAX_HOLDINGS}
        disabled={disabled}
        onPick={(asset) => {
          focusLast.current = true;
          onAdd(asset);
        }}
      />
      <table
        className="ruvor-table ruvor-holdings-editor"
        ref={tableRef}
        data-part="editor"
      >
        <colgroup>
          <col />
          <col className="ruvor-holdings-editor__weight" />
          <col className="ruvor-holdings-editor__remove" />
        </colgroup>
        <thead>
          <tr>
            <th scope="col">{TEXTOS["carteiras.col.acao"]}</th>
            <th scope="col" className="ruvor-holdings-editor__weight-head">
              {TEXTOS["carteiras.col.peso"]}
            </th>
            <th scope="col">
              <span className="ruvor-sr-only">{TEXTOS["carteiras.col.remover"]}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr className="ruvor-holdings-editor__empty">
              <td colSpan={3}>{TEXTOS["carteiras.editor.vazio"]}</td>
            </tr>
          ) : (
            rows.map((row, index) => {
              const weightMessage =
                row.error ??
                (row.apiError?.place === "weight" ? row.apiError.text : null);
              const tickerMessage =
                row.apiError?.place === "ticker" ? row.apiError.text : null;
              const weightErrorId = `${id}-r${row.key}-w`;
              const tickerErrorId = `${id}-r${row.key}-t`;
              return (
                <tr key={row.key} data-row={index} data-ticker={row.ticker}>
                  <td>
                    <span className="ruvor-holding-ticker">{row.ticker}</span>
                    <span className="ruvor-holding-name">{row.name}</span>
                    {tickerMessage !== null && (
                      <span className="ruvor-field__error" id={tickerErrorId}>
                        {tickerMessage}
                      </span>
                    )}
                  </td>
                  <td>
                    <input
                      className="ruvor-input"
                      type="text"
                      inputMode="decimal"
                      autoComplete="off"
                      value={row.text}
                      aria-label={TEXTOS["carteiras.peso.rotulo"](row.ticker)}
                      aria-invalid={weightMessage !== null ? true : undefined}
                      aria-describedby={
                        weightMessage !== null
                          ? weightErrorId
                          : tickerMessage !== null
                            ? tickerErrorId
                            : undefined
                      }
                      disabled={disabled}
                      onChange={(event) => onWeightChange(index, event.target.value)}
                      onBlur={() => onWeightBlur(index)}
                    />
                    {weightMessage !== null && (
                      <span className="ruvor-field__error" id={weightErrorId}>
                        {weightMessage}
                      </span>
                    )}
                  </td>
                  <td>
                    <button
                      className="ruvor-btn ruvor-btn--ghost ruvor-btn--icon"
                      type="button"
                      aria-label={TEXTOS["carteiras.remover"](row.ticker)}
                      disabled={disabled}
                      onClick={() => onRemove(index)}
                    >
                      <Glyph name="x" />
                    </button>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
        <tfoot>
          <tr>
            <td>
              <b>{TEXTOS["carteiras.soma.rotulo"]}</b>{" "}
              <span className="ruvor-muted">
                · {TEXTOS["carteiras.acoes"](rows.length)}
              </span>
            </td>
            <td colSpan={2}>
              <div className="ruvor-weight-sum" aria-live="polite" data-part="soma">
                <span className="ruvor-weight-sum__value">{centsText(cents)}%</span>
                {gap}
                {outside > 0 && (
                  <p className="ruvor-weight-sum__out">
                    {TEXTOS["carteiras.soma.foraDaSoma"](outside)}
                  </p>
                )}
              </div>
            </td>
          </tr>
          {totalErrors.length > 0 && (
            <tr>
              <td colSpan={3} data-part="soma-erros">
                {totalErrors.map((message) => (
                  <span key={message} className="ruvor-field__error" role="alert">
                    <Glyph name="warning" className="ruvor-glyph--sm" />
                    <span>{message}</span>
                  </span>
                ))}
              </td>
            </tr>
          )}
        </tfoot>
      </table>
    </>
  );
}
