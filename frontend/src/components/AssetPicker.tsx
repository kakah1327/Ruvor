import {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import { apiGet } from "../api/client";
import type { AssetItem, AssetPage } from "../api/types";
import { TEXTOS } from "../content/textos";
import { Glyph } from "./Glyph";
import { PAGE_LIMIT, SEARCH_PAUSE_MS } from "./SearchBox";

/** O motivo de um item que não pode entrar na composição (RF-05, D-181), pela chave do texto. */
export type PickReason =
  | "carteiras.seletor.motivo.indice"
  | "carteiras.seletor.motivo.inativa"
  | "carteiras.seletor.motivo.naComposicao";

/**
 * Só ação ativa fora da composição é escolhível: `kind === "stock"`, `status === "active"` e o
 * código em nenhuma linha. O resto devolve o motivo, nesta ordem.
 */
export function pickReason(
  asset: AssetItem,
  taken: ReadonlySet<string>,
): PickReason | null {
  if (asset.kind !== "stock") return "carteiras.seletor.motivo.indice";
  if (asset.status !== "active") return "carteiras.seletor.motivo.inativa";
  if (taken.has(asset.ticker)) return "carteiras.seletor.motivo.naComposicao";
  return null;
}

type PickerState =
  | { kind: "empty" }
  | { kind: "loading"; q: string }
  | { kind: "results"; q: string; count: number; results: AssetItem[] }
  | { kind: "none"; q: string }
  | { kind: "error"; q: string };

const EMPTY: PickerState = { kind: "empty" };

type AssetPickerProps = {
  /** Os códigos já na composição: aparecem desabilitados, com o motivo. */
  taken: ReadonlySet<string>;
  /** A composição já tem 20 ações: o campo fica desabilitado, com a dica. */
  full: boolean;
  disabled: boolean;
  onPick: (asset: AssetItem) => void;
};

/**
 * O seletor de ação (RF-05, D-181), como no `lista.html` aprovado: a busca do catálogo
 * (`GET /api/v1/assets?q=&limit=20`, a pausa e o descarte da resposta atrasada do `SearchBox`),
 * com a lista suspensa do kit. **O filtro é no cliente** (`pickReason`): o que não serve aparece
 * com `aria-disabled="true"` e o motivo no lugar do setor; as setas passam também por ele, e o
 * Enter ou o clique nele não fazem nada. Escolher limpa o campo e fecha a lista. A página só com o
 * que não serve diz isso e pede um termo mais preciso. O clique fora fecha a lista, e o foco no
 * campo a reabre.
 */
export function AssetPicker({ taken, full, disabled, onPick }: AssetPickerProps) {
  const [value, setValue] = useState("");
  const [state, setState] = useState<PickerState>(EMPTY);
  const [active, setActive] = useState(-1);
  const [open, setOpen] = useState(true);
  const seq = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const id = useId();
  const listId = `${id}-lista`;
  const fullId = `${id}-limite`;
  const optionId = (index: number) => `${id}-opt-${index}`;

  const run = useCallback((text: string) => {
    clearTimeout(timer.current);
    seq.current += 1;
    const mine = seq.current;
    const q = text.trim();
    setActive(-1);
    if (q === "") {
      setState(EMPTY);
      return;
    }
    setState({ kind: "loading", q });
    apiGet<AssetPage>(
      `/api/v1/assets?q=${encodeURIComponent(q)}&limit=${PAGE_LIMIT}&offset=0`,
    ).then(
      (page) => {
        if (mine !== seq.current) return; // a resposta atrasada: descartada
        setState(
          page.count === 0 || page.results.length === 0
            ? { kind: "none", q }
            : { kind: "results", q, count: page.count, results: page.results },
        );
      },
      () => {
        if (mine !== seq.current) return;
        setState({ kind: "error", q });
      },
    );
  }, []);

  const clear = useCallback(() => {
    setValue("");
    run("");
  }, [run]);

  // Ao sair da tela, nada mais se aplica.
  useEffect(
    () => () => {
      clearTimeout(timer.current);
      seq.current += 1;
    },
    [],
  );

  // O clique fora fecha a lista.
  useEffect(() => {
    function onClick(event: MouseEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);

  const options = state.kind === "results" ? state.results : [];
  const expanded = open && state.kind === "results";

  function pick(asset: AssetItem) {
    if (pickReason(asset, taken) !== null) return; // desabilitado: nada
    clear();
    onPick(asset);
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown" && options.length > 0) {
      event.preventDefault();
      setOpen(true);
      setActive(Math.min(active + 1, options.length - 1));
    } else if (event.key === "ArrowUp" && options.length > 0) {
      event.preventDefault();
      setActive(Math.max(active - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault(); // nunca envia o formulário
      const asset = options[active >= 0 ? active : 0];
      if (expanded && asset !== undefined) pick(asset);
    } else if (event.key === "Escape") {
      event.preventDefault();
      clear();
    }
  }

  const noneFits =
    state.kind === "results" &&
    state.results.every((asset) => pickReason(asset, taken) !== null);

  let popover = null;
  if (open && state.kind !== "empty") {
    popover = (
      <div className="ruvor-search__popover">
        {state.kind === "loading" && (
          <div
            className="ruvor-search__msg ruvor-search__msg--loading"
            aria-live="polite"
          >
            <Glyph name="spinner-gap" className="ruvor-spin" />
            <span>{TEXTOS["busca.buscando"]}</span>
          </div>
        )}
        {state.kind === "none" && (
          <div className="ruvor-search__msg" aria-live="polite">
            <b>{TEXTOS["busca.semResultado"](state.q)}</b>
            <p>{TEXTOS["busca.semResultadoDica"]}</p>
          </div>
        )}
        {state.kind === "error" && (
          <div className="ruvor-search__msg ruvor-search__msg--error" role="alert">
            <b>{TEXTOS["busca.erroTitulo"]}</b>
            <p>{TEXTOS["busca.erroTexto"]}</p>
            <button className="ruvor-btn" type="button" onClick={() => run(state.q)}>
              <Glyph name="arrows-clockwise" />
              <span>{TEXTOS["busca.tentarDeNovo"]}</span>
            </button>
          </div>
        )}
        {state.kind === "results" && (
          <>
            {noneFits && (
              <div
                className="ruvor-search__msg"
                aria-live="polite"
                data-part="nenhuma-serve"
              >
                <b>{TEXTOS["carteiras.seletor.nenhumaServe"](state.q)}</b>
                <p>{TEXTOS["carteiras.seletor.nenhumaServeDica"]}</p>
              </div>
            )}
            <ul
              className="ruvor-search__list"
              id={listId}
              // biome-ignore lint/a11y/noNoninteractiveElementToInteractiveRole: a lista da caixa de combinação é a .ruvor-search__list do kit, um <ul role="listbox"> como no lista.html aprovado.
              role="listbox"
              aria-label={TEXTOS["carteiras.seletor.rotulo"]}
            >
              {state.results.map((asset, index) => (
                <PickOption
                  key={asset.ticker}
                  asset={asset}
                  id={optionId(index)}
                  active={index === active}
                  reason={pickReason(asset, taken)}
                  onPick={() => pick(asset)}
                />
              ))}
            </ul>
            <div className="ruvor-search__foot" aria-live="polite">
              {TEXTOS["busca.suspensaRodape"](state.results.length, state.count)}
            </div>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="ruvor-picker" ref={wrapperRef} data-part="seletor">
      <div className="ruvor-search">
        <Glyph name="magnifying-glass" />
        <input
          className="ruvor-input ruvor-search__input"
          type="search"
          autoComplete="off"
          spellCheck={false}
          role="combobox"
          aria-autocomplete="list"
          aria-controls={listId}
          aria-expanded={expanded}
          aria-activedescendant={expanded && active >= 0 ? optionId(active) : undefined}
          aria-label={TEXTOS["carteiras.seletor.rotulo"]}
          aria-describedby={full ? fullId : undefined}
          placeholder={TEXTOS["carteiras.seletor.placeholder"]}
          value={value}
          disabled={full || disabled}
          onChange={(event) => {
            setOpen(true);
            setValue(event.target.value);
            clearTimeout(timer.current);
            const text = event.target.value;
            timer.current = setTimeout(() => run(text), SEARCH_PAUSE_MS);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
      </div>
      {full ? (
        <p className="ruvor-hint" id={fullId}>
          {TEXTOS["carteiras.seletor.limite"]}
        </p>
      ) : (
        popover
      )}
    </div>
  );
}

type PickOptionProps = {
  asset: AssetItem;
  id: string;
  active: boolean;
  reason: PickReason | null;
  onPick: () => void;
};

/** Um item: o código, o nome de pregão, o setor (ou o motivo) e as tags do kit. */
function PickOption({ asset, id, active, reason, onPick }: PickOptionProps) {
  const classes = ["ruvor-search__option", "ruvor-pick"];
  if (reason !== null) classes.push("ruvor-pick--off");
  if (active) classes.push("ruvor-search__option--active");
  return (
    // biome-ignore lint/a11y/useFocusableInteractive: o foco fica no campo, e o item destacado é apontado por aria-activedescendant (padrão da caixa de combinação).
    // biome-ignore lint/a11y/useKeyWithClickEvents: o teclado é o do campo (setas e Enter), como na caixa de combinação.
    <li
      className={classes.join(" ")}
      id={id}
      // biome-ignore lint/a11y/noNoninteractiveElementToInteractiveRole: o item é um <li role="option"> da .ruvor-search__list, como no lista.html aprovado.
      role="option"
      aria-selected={active}
      aria-disabled={reason !== null ? true : undefined}
      data-ticker={asset.ticker}
      // O clique não tira o foco do campo.
      onMouseDown={(event) => event.preventDefault()}
      onClick={onPick}
    >
      <div className="ruvor-search__link">
        <span className="ruvor-search__ticker">{asset.ticker}</span>
        <span className="ruvor-search__name">
          <b>{asset.trading_name}</b>
          {reason !== null ? (
            <span className="ruvor-pick__why">{TEXTOS[reason]}</span>
          ) : (
            asset.sector !== null && <span>{asset.sector}</span>
          )}
        </span>
        <span className="ruvor-search__tags">
          {asset.kind === "index" && (
            <span className="ruvor-tag ruvor-tag--evidence">
              {TEXTOS["busca.tagIndice"]}
            </span>
          )}
          {asset.status === "inactive" && (
            <span className="ruvor-tag ruvor-tag--review">
              {TEXTOS["busca.tagInativo"]}
            </span>
          )}
        </span>
      </div>
    </li>
  );
}
