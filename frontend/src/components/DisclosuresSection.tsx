import { type ReactNode, useCallback, useEffect, useId, useRef, useState } from "react";

import { apiGet } from "../api/client";
import type { Load } from "../api/resource";
import {
  type AssetDetail,
  DISCLOSURE_CATEGORIES,
  type DisclosureCategory,
  type DisclosureItem,
  type Disclosures,
} from "../api/types";
import { TEXTOS } from "../content/textos";
import { formatDate, formatInteger } from "../format/numbers";
import { Glyph } from "./Glyph";
import { SectionError, SectionSkeleton } from "./SectionStatus";

/** Os dez mais recentes por página (RF-12); "mostrar mais" soma a seguinte (RF-13). */
export const DISCLOSURES_PAGE = 10;

/** O filtro: `""` é "todas" (o padrão). */
type Filter = DisclosureCategory | "";

const FILTERS: readonly Filter[] = ["", ...DISCLOSURE_CATEGORIES];

/**
 * A lista que chegou: a página pedida por último (`offset`, e quantos vieram nela), os itens
 * somados, e o que está em curso — a troca de filtro (`listLoading`) ou "mostrar mais".
 */
type Ready = {
  kind: "ready";
  body: Disclosures;
  items: DisclosureItem[];
  offset: number;
  pageLength: number;
  listLoading: boolean;
  more: "idle" | "loading" | "error";
};

type View = { kind: "loading" } | { kind: "error" } | Ready;

/**
 * Como um pedido começa: `fresh` apaga tudo (a primeira carga, outro ativo); `reset` volta ao
 * começo mostrando o carregando da lista (o filtro, "tentar de novo"); `reload` volta ao começo
 * sem apagar o que está na tela (a recarga do fim do acompanhamento, como o `reload()` de
 * `useResource`); `more` pede a página seguinte e soma.
 */
type Mode = "fresh" | "reset" | "reload" | "more";

function isCategory(value: string): value is DisclosureCategory {
  return (DISCLOSURE_CATEGORIES as readonly string[]).includes(value);
}

function disclosuresPath(ticker: string, filter: Filter, offset: number): string {
  const category = filter === "" ? "" : `&category=${filter}`;
  return `/api/v1/assets/${encodeURIComponent(ticker)}/disclosures?limit=${DISCLOSURES_PAGE}&offset=${offset}${category}`;
}

function begin(prev: View, mode: Mode): View {
  if (prev.kind !== "ready" || mode === "fresh") {
    return { kind: "loading" };
  }
  switch (mode) {
    case "reset":
      return { ...prev, listLoading: true, more: "idle" };
    case "reload":
      return { ...prev, more: "idle" };
    case "more":
      return { ...prev, more: "loading" };
  }
}

/** A página que chegou: no começo, substitui; em "mostrar mais", soma sem repetir o `link`. */
function arrive(prev: View, body: Disclosures, offset: number, append: boolean): View {
  let items = body.results;
  if (append && prev.kind === "ready") {
    const seen = new Set(prev.items.map((item) => item.link));
    items = [...prev.items, ...body.results.filter((item) => !seen.has(item.link))];
  }
  return {
    kind: "ready",
    body,
    items,
    offset,
    pageLength: body.results.length,
    listLoading: false,
    more: "idle",
  };
}

/**
 * Os pedidos a `/disclosures`, com o descarte da resposta atrasada (o molde da busca do
 * M1.6b): cada pedido leva um número de sequência, e a resposta só se aplica se o número
 * dela ainda for o do último disparado — a de um filtro anterior, a de um "mostrar mais"
 * que outro filtro atropelou, a que chega depois de a seção sair.
 */
function useDisclosures(ticker: string, reloadToken: number) {
  const [view, setView] = useState<View>({ kind: "loading" });
  const [filter, setFilterState] = useState<Filter>("");
  const filterRef = useRef<Filter>("");
  const seq = useRef(0);

  const request = useCallback(
    (category: Filter, offset: number, mode: Mode) => {
      seq.current += 1;
      const mine = seq.current;
      setView((prev) => begin(prev, mode));
      apiGet<Disclosures>(disclosuresPath(ticker, category, offset)).then(
        (body) => {
          // A resposta atrasada de um pedido anterior: descartada.
          if (mine !== seq.current) {
            return;
          }
          setView((prev) => arrive(prev, body, offset, mode === "more"));
        },
        () => {
          if (mine !== seq.current) {
            return;
          }
          setView((prev) =>
            mode === "more" && prev.kind === "ready"
              ? { ...prev, more: "error" }
              : { kind: "error" },
          );
        },
      );
    },
    [ticker],
  );

  // Outro ativo: tudo do começo, com "todas".
  useEffect(() => {
    filterRef.current = "";
    setFilterState("");
    request("", 0, "fresh");
    return () => {
      seq.current += 1;
    };
  }, [request]);

  // A recarga do fim do acompanhamento (RF-15): volta a `offset=0`, mantendo o filtro. O
  // primeiro valor é o da montagem, que o efeito acima já pediu.
  const lastToken = useRef(reloadToken);
  useEffect(() => {
    if (lastToken.current === reloadToken) {
      return;
    }
    lastToken.current = reloadToken;
    request(filterRef.current, 0, "reload");
  }, [reloadToken, request]);

  /** Trocar o filtro volta ao começo (RF-13). */
  const choose = useCallback(
    (next: Filter) => {
      filterRef.current = next;
      setFilterState(next);
      request(next, 0, "reset");
    },
    [request],
  );

  const retry = useCallback(() => request(filterRef.current, 0, "reset"), [request]);

  const more = useCallback(() => {
    if (view.kind === "ready") {
      request(filterRef.current, view.offset + DISCLOSURES_PAGE, "more");
    }
  }, [request, view]);

  return { view, filter, choose, retry, more };
}

/** Um aviso ou painel de estado, com o sinal duotone da evidência (D-93). */
function StatePanel({
  title,
  actions,
  notice = false,
}: {
  title: string;
  actions?: ReactNode;
  notice?: boolean;
}) {
  const inner = (
    <>
      <span className="ruvor-icon ruvor-icon--evidence">
        <Glyph name="info" weight="duotone" />
      </span>
      <div className="ruvor-state__body">
        <p className="ruvor-state__title">{title}</p>
        {actions !== undefined && <div className="ruvor-state__actions">{actions}</div>}
      </div>
    </>
  );
  return notice ? (
    <div className="ruvor-state ruvor-state--notice">{inner}</div>
  ) : (
    <div className="ruvor-panel">
      <div className="ruvor-panel__body ruvor-state">{inner}</div>
    </div>
  );
}

function Loading({ short = false }: { short?: boolean }) {
  return (
    <div role="status" aria-busy="true">
      <SectionSkeleton short={short} />
      <span className="ruvor-sr-only">{TEXTOS["comunicados.carregando"]}</span>
    </div>
  );
}

/** Um comunicado (RF-12): a data de entrega, a categoria em tag e o título como link para a CVM. */
function DisclosureRow({ item }: { item: DisclosureItem }) {
  const known = isCategory(item.category);
  return (
    <li className="ruvor-doc">
      <span className="ruvor-doc__date ruvor-num">
        <span className="ruvor-sr-only">{`${TEXTOS["comunicados.entregueEm"]} `}</span>
        {formatDate(item.delivered_on)}
      </span>
      <div className="ruvor-doc__main">
        {known && (
          <span
            className={
              item.category === "fato_relevante"
                ? "ruvor-tag ruvor-tag--evidence"
                : "ruvor-tag ruvor-tag--neutral"
            }
          >
            {TEXTOS[`comunicados.categoria.${item.category}`]}
          </span>
        )}
        <a
          className="ruvor-doc__link"
          href={item.link}
          target="_blank"
          rel="noopener noreferrer"
          data-disclosure-link=""
        >
          {item.title}
          <Glyph name="arrow-square-out" className="ruvor-glyph--sm" />
          <span className="ruvor-sr-only">{` (${TEXTOS["comunicados.linkSaida"]})`}</span>
        </a>
        {item.reference_date !== null && item.reference_date !== item.delivered_on && (
          <p className="ruvor-note">
            {TEXTOS["comunicados.referencia"](formatDate(item.reference_date))}
          </p>
        )}
      </div>
    </li>
  );
}

type Props = {
  ticker: string;
  /** A identidade (`/assets/{ticker}`): o `kind` diz por que `company` é nulo (RF-14). */
  asset: Load<AssetDetail>;
  /** Muda quando a tela recarrega tudo: a lista volta à primeira página, com o filtro. */
  reloadToken: number;
};

/**
 * Os comunicados da companhia à CVM (M1.6c, RF-11 a RF-14): os dez mais recentes, o filtro
 * pelas três categorias, "mostrar mais" sem repetir, e os estados. A seção faz os próprios
 * pedidos; `company: null` se explica pelo `kind` da identidade — enquanto ela carrega, a
 * seção segue carregando; se ela falhou, a frase não afirma se é índice.
 */
export function DisclosuresSection({ ticker, asset, reloadToken }: Props) {
  const titleId = useId();
  const { view, filter, choose, retry, more } = useDisclosures(ticker, reloadToken);

  let state: "loading" | "error" | "ready" | "empty";
  let company: string | undefined;
  let body: ReactNode;

  if (view.kind === "loading") {
    state = "loading";
    body = <Loading />;
  } else if (view.kind === "error") {
    state = "error";
    body = <SectionError onRetry={retry} />;
  } else if (view.body.company === null) {
    company = "unlinked";
    if (asset.state === "loading") {
      state = "loading";
      body = <Loading />;
    } else if (asset.state === "error") {
      state = "empty";
      body = <StatePanel title={TEXTOS["comunicados.semLigacao"]} />;
    } else if (asset.data.kind === "index") {
      state = "empty";
      company = "none-index";
      body = <StatePanel title={TEXTOS["comunicados.indice"]} />;
    } else {
      state = "empty";
      company = "none-stock";
      body = <StatePanel title={TEXTOS["comunicados.semCodigo"]} />;
    }
  } else if (filter === "" && !view.listLoading && view.items.length === 0) {
    state = "empty";
    company = view.body.company.code_cvm;
    body = <StatePanel title={TEXTOS["comunicados.vazio"]} />;
  } else {
    company = view.body.company.code_cvm;
    const who =
      view.body.company.name === null
        ? TEXTOS["comunicados.companhiaSemNome"](view.body.company.code_cvm)
        : TEXTOS["comunicados.companhia"](
            view.body.company.name,
            view.body.company.code_cvm,
          );

    let list: ReactNode;
    if (view.listLoading) {
      state = "loading";
      list = (
        <div className="ruvor-docs__state">
          <Loading short />
        </div>
      );
    } else if (view.items.length === 0 && filter !== "") {
      state = "empty";
      list = (
        <div className="ruvor-docs__state">
          <StatePanel
            notice
            title={TEXTOS["comunicados.filtroVazio"](
              TEXTOS[`comunicados.categoria.${filter}`],
            )}
            actions={
              <button className="ruvor-btn" type="button" onClick={() => choose("")}>
                {TEXTOS["comunicados.verTodas"]}
              </button>
            }
          />
        </div>
      );
    } else {
      state = "ready";
      const hasMore = view.offset + view.pageLength < view.body.count;
      let action: ReactNode = null;
      if (view.more === "loading") {
        action = (
          <button className="ruvor-btn" type="button" aria-busy="true" disabled>
            <Glyph name="spinner-gap" className="ruvor-spin" />
            <span>{TEXTOS["comunicados.carregandoMais"]}</span>
          </button>
        );
      } else if (view.more === "error") {
        action = (
          <div
            className="ruvor-callout ruvor-callout--critical ruvor-callout--row"
            role="alert"
          >
            <span>{TEXTOS["comunicados.erroMais"]}</span>
            <button className="ruvor-btn" type="button" onClick={more}>
              <Glyph name="arrows-clockwise" />
              <span>{TEXTOS["ativo.tentarDeNovo"]}</span>
            </button>
          </div>
        );
      } else if (hasMore) {
        action = (
          <button className="ruvor-btn" type="button" onClick={more}>
            {TEXTOS["comunicados.mostrarMais"]}
          </button>
        );
      }
      list = (
        <>
          <ul className="ruvor-docs">
            {view.items.map((item) => (
              <DisclosureRow key={item.link} item={item} />
            ))}
          </ul>
          <div className="ruvor-docs__foot">
            <span className="ruvor-muted" role="status">
              {TEXTOS["comunicados.mostrando"](
                formatInteger(view.items.length),
                formatInteger(view.body.count),
              )}
            </span>
            {action}
          </div>
        </>
      );
    }

    body = (
      <div className="ruvor-panel">
        <div className="ruvor-panel__head ruvor-docs__head">
          {/* biome-ignore lint/a11y/useSemanticElements: o filtro é a .ruvor-btn-group do kit, um div com role="group" como no ativo-fundamentos.html aprovado; um fieldset traria margem e largura mínima do navegador que a classe não zera. */}
          <div
            className="ruvor-btn-group ruvor-btn-group--wrap"
            role="group"
            aria-label={TEXTOS["comunicados.filtro.rotulo"]}
          >
            {FILTERS.map((option) => (
              <button
                key={option === "" ? "todas" : option}
                className="ruvor-btn"
                type="button"
                aria-pressed={filter === option}
                onClick={() => choose(option)}
              >
                {TEXTOS[`comunicados.filtro.${option === "" ? "todas" : option}`]}
              </button>
            ))}
          </div>
        </div>
        <div className="ruvor-panel__body">
          <p className="ruvor-note">{`${who} ${TEXTOS["comunicados.saida"]}`}</p>
          {list}
        </div>
      </div>
    );
  }

  return (
    <section
      className="ruvor-stack"
      data-section="disclosures"
      data-state={state}
      data-company={company}
      aria-labelledby={titleId}
    >
      <div className="ruvor-section-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["comunicados.sobrancelha"]}</p>
          <h2 className="ruvor-h2" id={titleId}>
            {TEXTOS["comunicados.titulo"]}
          </h2>
        </div>
      </div>
      <p className="ruvor-sub">{TEXTOS["comunicados.intro"]}</p>
      <div>{body}</div>
    </section>
  );
}
