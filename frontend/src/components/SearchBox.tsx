import {
  type KeyboardEvent,
  type MouseEvent,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { Link, useNavigate } from "react-router";

import { ApiError, apiGet } from "../api/client";
import type { Load } from "../api/resource";
import type { AssetItem, AssetPage } from "../api/types";
import { TEXTOS } from "../content/textos";
import { Glyph } from "./Glyph";

/** A pausa na digitação antes da consulta (RF-05: entre 150 e 300 ms). */
export const SEARCH_PAUSE_MS = 200;
/** Quantos resultados por consulta: a página inicial, com "mostrar mais"; a barra, só estes. */
export const PAGE_LIMIT = 20;
export const BAR_LIMIT = 8;
/** Quantos ativos a sugestão mostra (M1.7, RF-10: fixo); o resto vira "e mais N". */
export const SUGGESTION_LIMIT = 8;
/** O pedido da sugestão: os ativos com risco calculado, a primeira página (RF-10). */
export const SUGGESTION_PATH = `/api/v1/assets?has_risk=true&limit=${SUGGESTION_LIMIT}`;
/** Quantos atalhos o esqueleto da sugestão desenha enquanto carrega (o do mockup). */
const SUGGESTION_SKELETONS = [0, 1, 2, 3, 4, 5];

type SearchState =
  | { kind: "empty" }
  | { kind: "loading"; q: string }
  | {
      kind: "results";
      q: string;
      count: number;
      results: AssetItem[];
      loadingMore: boolean;
    }
  | { kind: "none"; q: string }
  | { kind: "error"; q: string };

const EMPTY: SearchState = { kind: "empty" };

function assetPath(ticker: string): string {
  return `/ativos/${encodeURIComponent(ticker)}`;
}

/** O clique que abre o link na mesma aba: o do meio e o com tecla abrem outra. */
function isPlainClick(event: MouseEvent): boolean {
  return (
    event.button === 0 &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.shiftKey &&
    !event.altKey
  );
}

/**
 * A consulta a `GET /api/v1/assets?q=`, com a pausa e o descarte da resposta atrasada.
 *
 * Cada consulta disparada leva um número de sequência; a resposta só se aplica se o número
 * dela ainda for o da última disparada. Limpar o campo também conta como disparo: a
 * resposta que chegar depois de limpar é descartada.
 */
function useAssetSearch(limit: number) {
  const [value, setValue] = useState("");
  const [state, setState] = useState<SearchState>(EMPTY);
  const [active, setActive] = useState(-1);
  const seq = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const run = useCallback(
    (text: string, offset = 0) => {
      clearTimeout(timer.current);
      seq.current += 1;
      const mine = seq.current;
      const q = text.trim();
      setActive(-1);

      if (q === "") {
        setState(EMPTY);
        return;
      }
      const append = offset > 0;
      if (append) {
        setState((prev) =>
          prev.kind === "results" ? { ...prev, loadingMore: true } : prev,
        );
      } else {
        setState({ kind: "loading", q });
      }

      apiGet<AssetPage>(
        `/api/v1/assets?q=${encodeURIComponent(q)}&limit=${limit}&offset=${offset}`,
      ).then(
        (page) => {
          // A resposta atrasada de uma consulta anterior: descartada.
          if (mine !== seq.current) {
            return;
          }
          setActive(-1);
          setState((prev) => {
            if (page.count === 0) {
              return { kind: "none", q };
            }
            const results =
              append && prev.kind === "results"
                ? [...prev.results, ...page.results]
                : page.results;
            return {
              kind: "results",
              q,
              count: page.count,
              results,
              loadingMore: false,
            };
          });
        },
        () => {
          if (mine !== seq.current) {
            return;
          }
          setActive(-1);
          setState({ kind: "error", q });
        },
      );
    },
    [limit],
  );

  const type = useCallback(
    (text: string) => {
      setValue(text);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => run(text), SEARCH_PAUSE_MS);
    },
    [run],
  );

  const clear = useCallback(() => {
    setValue("");
    run("");
  }, [run]);

  // Ao sair da tela, nada mais se aplica: nem a consulta que esperava a pausa, nem a que
  // estava no ar.
  useEffect(
    () => () => {
      clearTimeout(timer.current);
      seq.current += 1;
    },
    [],
  );

  return { value, state, active, setActive, run, type, clear };
}

/**
 * A sugestão da caixa vazia (M1.7, RF-10 e RF-11): **um** pedido por montagem do `SearchBox`
 * de página, guardado aqui — voltar ao vazio mostra a mesma resposta, sem pedido novo. Com
 * `enabled` falso (a busca da barra), não pede nada.
 *
 * O descarte segue o molde da busca: cada pedido leva um número de sequência, e a resposta só
 * se aplica se o número dela ainda for o último. Desmontar também conta — é o que descarta o
 * pedido do primeiro efeito do `StrictMode`, que monta, desmonta e monta de novo.
 */
function useSuggestion(enabled: boolean): Load<AssetPage> {
  const [load, setLoad] = useState<Load<AssetPage>>({ state: "loading" });
  const seq = useRef(0);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    seq.current += 1;
    const mine = seq.current;
    apiGet<AssetPage>(SUGGESTION_PATH).then(
      (data) => {
        if (mine === seq.current) {
          setLoad({ state: "ok", data });
        }
      },
      (error: unknown) => {
        if (mine === seq.current) {
          setLoad({
            state: "error",
            error:
              error instanceof ApiError
                ? error
                : new ApiError(0, "unexpected_response", String(error)),
          });
        }
      },
    );
    return () => {
      seq.current += 1;
    };
  }, [enabled]);

  return load;
}

type SearchBoxProps = {
  /** `page`: o campo grande da página inicial; `bar`: o da barra, com a lista suspensa. */
  variant: "page" | "bar";
};

/**
 * A busca (RF-05), caixa de combinação com lista: `role="combobox"` no campo,
 * `aria-controls` na lista, `role="option"` em cada item, e o item é um link de verdade.
 * Setas percorrem, Enter abre o destacado — sem destaque, o primeiro; sem resultado, nada —,
 * Esc limpa.
 */
export function SearchBox({ variant }: SearchBoxProps) {
  const isBar = variant === "bar";
  const { value, state, active, setActive, run, type, clear } = useAssetSearch(
    isBar ? BAR_LIMIT : PAGE_LIMIT,
  );
  // Só a caixa de página pede a sugestão; a da barra não pede nada (RF-10).
  const suggestion = useSuggestion(!isBar);
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(true);
  const listId = useId();
  const optionId = useCallback((index: number) => `${listId}-opt-${index}`, [listId]);

  const options = state.kind === "results" ? state.results : [];
  const visible = !isBar || open;
  const expanded = visible && state.kind === "results";

  // A lista suspensa fecha com o clique fora dela; volta ao focar o campo.
  useEffect(() => {
    if (!isBar) {
      return;
    }
    function onClick(event: globalThis.MouseEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, [isBar]);

  // O destacado fica à vista quando a lista rola.
  useEffect(() => {
    if (active >= 0) {
      document.getElementById(optionId(active))?.scrollIntoView?.({ block: "nearest" });
    }
  }, [active, optionId]);

  function choose(ticker: string) {
    clear();
    void navigate(assetPath(ticker));
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "ArrowDown" && options.length > 0) {
      event.preventDefault();
      if (!visible) {
        setOpen(true);
        return;
      }
      setActive(Math.min(active + 1, options.length - 1));
    } else if (event.key === "ArrowUp" && options.length > 0 && visible) {
      event.preventDefault();
      setActive(Math.max(active - 1, 0));
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (options.length === 0 || !visible) {
        return; // sem resultado, nada
      }
      choose(options[active >= 0 ? active : 0].ticker);
    } else if (event.key === "Escape") {
      event.preventDefault();
      clear();
    }
  }

  const list =
    state.kind === "results" ? (
      <ul
        className="ruvor-search__list"
        id={listId}
        // biome-ignore lint/a11y/noNoninteractiveElementToInteractiveRole: a lista da caixa de combinação é a .ruvor-search__list do kit, um <ul role="listbox"> como no busca.html aprovado; o plano fixa role="option" em cada item, com o link dentro.
        role="listbox"
        aria-label={TEXTOS["busca.contagem"](state.count, state.q)}
      >
        {state.results.map((asset, index) => (
          <SearchOption
            key={asset.ticker}
            asset={asset}
            id={optionId(index)}
            active={index === active}
            onPick={(event) => {
              if (isPlainClick(event)) {
                clear();
              }
            }}
          />
        ))}
      </ul>
    ) : null;

  const field = (
    <div className={`ruvor-search ${isBar ? "ruvor-search--bar" : "ruvor-search--lg"}`}>
      <Glyph
        name="magnifying-glass"
        className={isBar ? undefined : "ruvor-glyph--lg"}
      />
      <input
        ref={inputRef}
        className="ruvor-input ruvor-search__input"
        type="search"
        autoComplete="off"
        spellCheck={false}
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={expanded}
        aria-controls={listId}
        aria-activedescendant={expanded && active >= 0 ? optionId(active) : undefined}
        aria-label={isBar ? TEXTOS["casco.busca.rotulo"] : TEXTOS["busca.rotulo"]}
        placeholder={
          isBar ? TEXTOS["casco.busca.placeholder"] : TEXTOS["busca.placeholder"]
        }
        value={value}
        onChange={(event) => {
          setOpen(true);
          type(event.target.value);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
      />
      <button
        className="ruvor-search__clear"
        type="button"
        aria-label={TEXTOS["busca.limpar"]}
        hidden={value === ""}
        onClick={() => {
          clear();
          inputRef.current?.focus();
        }}
      >
        <Glyph name="x" className={isBar ? "ruvor-glyph--sm" : undefined} />
      </button>
    </div>
  );

  const retry = (
    <button
      className="ruvor-btn"
      type="button"
      onClick={() => {
        if (state.kind === "error") {
          run(state.q);
        }
        if (isBar) {
          inputRef.current?.focus();
        }
      }}
    >
      <Glyph name="arrows-clockwise" />
      <span>{TEXTOS["busca.tentarDeNovo"]}</span>
    </button>
  );

  if (isBar) {
    return (
      <div className="ruvor-topbar__search" ref={wrapperRef}>
        {field}
        <div className="ruvor-search__popover" hidden={state.kind === "empty" || !open}>
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
              {retry}
            </div>
          )}
          {state.kind === "results" && (
            <>
              {list}
              <div className="ruvor-search__foot" aria-live="polite">
                {TEXTOS["busca.suspensaRodape"](state.results.length, state.count)}
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <>
      {field}
      {state.kind === "empty" ? (
        <Suggestions load={suggestion} />
      ) : (
        <div className="ruvor-search__results">
          <p className="ruvor-search__count" aria-live="polite">
            {state.kind === "loading" && <span>{TEXTOS["busca.buscando"]}</span>}
            {state.kind === "results" && (
              <b>{TEXTOS["busca.contagem"](state.count, state.q)}</b>
            )}
          </p>

          {state.kind === "loading" && (
            <div className="ruvor-panel" aria-busy="true">
              {[0, 1, 2, 3].map((row) => (
                <div key={row} className="ruvor-search__skeleton" aria-hidden="true">
                  <span className="ruvor-skeleton" />
                  <span className="ruvor-skeleton" />
                  <span className="ruvor-skeleton" />
                </div>
              ))}
            </div>
          )}

          {state.kind === "none" && (
            <div className="ruvor-panel ruvor-search__empty">
              <b>{TEXTOS["busca.semResultado"](state.q)}</b>
              <p>{TEXTOS["busca.semResultadoDica"]}</p>
            </div>
          )}

          {state.kind === "error" && (
            <div
              className="ruvor-callout ruvor-callout--critical ruvor-search__error"
              role="alert"
            >
              <span className="ruvor-icon ruvor-icon--critical">
                <Glyph name="x-circle" weight="duotone" />
              </span>
              <div>
                <b>{TEXTOS["busca.erroTitulo"]}</b>
                <p>{TEXTOS["busca.erroTexto"]}</p>
                {retry}
              </div>
            </div>
          )}

          {state.kind === "results" && (
            <>
              <div className="ruvor-panel">{list}</div>
              {state.count > state.results.length && (
                <div className="ruvor-search__more">
                  <button
                    className="ruvor-btn"
                    type="button"
                    aria-busy={state.loadingMore || undefined}
                    disabled={state.loadingMore}
                    onClick={() => run(state.q, state.results.length)}
                  >
                    {TEXTOS["busca.mostrarMais"]}
                  </button>
                  <span>
                    {TEXTOS["busca.mostrando"](state.results.length, state.count)}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </>
  );
}

type SearchOptionProps = {
  asset: AssetItem;
  id: string;
  active: boolean;
  onPick: (event: MouseEvent) => void;
};

/** Um resultado: ticker, nome de pregão, setor e as tags; um link para a tela do ativo. */
function SearchOption({ asset, id, active, onPick }: SearchOptionProps) {
  return (
    // biome-ignore lint/a11y/useFocusableInteractive: o foco fica no campo, e o item destacado é apontado por aria-activedescendant (padrão da caixa de combinação); o link dentro do item é o alvo do clique.
    <li
      className={
        active
          ? "ruvor-search__option ruvor-search__option--active"
          : "ruvor-search__option"
      }
      id={id}
      // biome-ignore lint/a11y/noNoninteractiveElementToInteractiveRole: o item é um <li role="option"> da .ruvor-search__list, como no busca.html aprovado.
      role="option"
      aria-selected={active}
    >
      <Link
        className="ruvor-search__link"
        to={assetPath(asset.ticker)}
        tabIndex={-1}
        onClick={onPick}
      >
        <span className="ruvor-search__ticker">{asset.ticker}</span>
        <span className="ruvor-search__name">
          <b>{asset.trading_name}</b>
          {asset.sector !== null && <span>{asset.sector}</span>}
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
          {!asset.has_prices && (
            <span className="ruvor-tag ruvor-tag--neutral">
              {TEXTOS["busca.tagSemDados"]}
            </span>
          )}
        </span>
        <Glyph name="caret-right" className="ruvor-glyph--sm ruvor-search__go" />
      </Link>
    </li>
  );
}

/**
 * O estado vazio da caixa de página: os ativos com risco calculado, vindos da API (M1.7,
 * RF-10 e RF-11). Recebe o estado do `SearchBox` e não pede nada — ela desmonta a cada busca.
 * Sem região viva e sem `role="alert"`: a sugestão é auxiliar, e o erro dela não bloqueia a
 * caixa, que continua aceitando o que se digita.
 */
function Suggestions({ load }: { load: Load<AssetPage> }) {
  const titleId = useId();
  return (
    <section
      className="ruvor-search__suggest"
      aria-labelledby={titleId}
      aria-busy={load.state === "loading" || undefined}
    >
      <h2 className="ruvor-eyebrow" id={titleId}>
        {TEXTOS["busca.sugestaoTitulo"]}
      </h2>
      {load.state === "loading" && (
        <>
          <p className="ruvor-sr-only">{TEXTOS["busca.sugestaoCarregando"]}</p>
          <ul className="ruvor-chips" aria-hidden="true">
            {SUGGESTION_SKELETONS.map((slot) => (
              <li key={slot}>
                <span className="ruvor-skeleton ruvor-skeleton--chip" />
              </li>
            ))}
          </ul>
        </>
      )}
      {load.state === "error" && (
        <div className="ruvor-panel ruvor-search__empty">
          <b>{TEXTOS["busca.sugestaoErro"]}</b>
          <p>{TEXTOS["busca.sugestaoErroDica"]}</p>
        </div>
      )}
      {load.state === "ok" && load.data.count === 0 && (
        <div className="ruvor-panel ruvor-search__empty">
          <b>{TEXTOS["busca.sugestaoNenhum"]}</b>
          <p>{TEXTOS["busca.sugestaoNenhumNota"]}</p>
        </div>
      )}
      {load.state === "ok" && load.data.count > 0 && (
        <>
          <ul className="ruvor-chips">
            {load.data.results.map((asset) => (
              <li key={asset.ticker}>
                <Link className="ruvor-chip" to={assetPath(asset.ticker)}>
                  {asset.ticker}
                </Link>
              </li>
            ))}
            {load.data.count > SUGGESTION_LIMIT && (
              <li>
                <span className="ruvor-chips__more">
                  {TEXTOS["busca.sugestaoMais"](load.data.count - SUGGESTION_LIMIT)}
                </span>
              </li>
            )}
          </ul>
          <p>{TEXTOS["busca.sugestaoNota"]}</p>
        </>
      )}
    </section>
  );
}
