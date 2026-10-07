import {
  type FormEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { ApiError, apiGet, apiPost } from "../api/client";
import type { Portfolio, PortfolioPage } from "../api/types";
import { Glyph } from "../components/Glyph";
import { HoldingsEditor } from "../components/HoldingsEditor";
import { SignInNotice } from "../components/SignInNotice";
import { TEXTOS } from "../content/textos";
import { formatInstant } from "../format/numbers";
import {
  applyHoldingsError,
  blurRow,
  checkHoldings,
  type EditorRow,
  holdingsToApi,
  newRow,
} from "../portfolio/editor";
import { formatBrlText, notionalToApi, parseNotional } from "../portfolio/notional";
import { useSession } from "../session/SessionProvider";
import type { Me } from "../session/types";

export const PORTFOLIOS_PATH = "/api/v1/portfolios";
/** A página da lista: o `limit` padrão da API (RF-03). */
export const PORTFOLIOS_PAGE = 50;
/** O nome tem até 100 caracteres (`PortfolioCreateIn`). */
const NAME_MAX = 100;

/**
 * O estado de navegação que a lista lê ao chegar: `archived`, o nome da carteira que acabou de
 * ser arquivada (RF-08) — quem arquiva navega a `/carteiras` com ele.
 */
export type PortfoliosLocationState = { archived?: string };

/** O caminho da página de uma carteira. */
export function portfolioPath(id: string): string {
  return `/carteiras/${encodeURIComponent(id)}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** A forma de `PortfolioOut` que a tela lê, com o instante legível. */
export function isPortfolio(value: unknown): value is Portfolio {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.name === "string" &&
    (value.notional === null || typeof value.notional === "string") &&
    typeof value.version === "number" &&
    Array.isArray(value.holdings) &&
    typeof value.version_created_at === "string" &&
    !Number.isNaN(new Date(value.version_created_at).getTime())
  );
}

function isPage(value: unknown): value is PortfolioPage {
  return (
    isRecord(value) &&
    typeof value.count === "number" &&
    Array.isArray(value.results) &&
    value.results.every(isPortfolio)
  );
}

/** Uma página da lista; corpo fora da forma é erro, como no cliente. */
async function fetchPage(offset: number): Promise<PortfolioPage> {
  const body = await apiGet<unknown>(
    `${PORTFOLIOS_PATH}?limit=${PORTFOLIOS_PAGE}&offset=${offset}`,
  );
  if (!isPage(body)) {
    throw new ApiError(200, "unexpected_response", "portfolios fora da forma");
  }
  return body;
}

/** A página seguinte depois das que já estão na tela, sem repetir carteira. */
function appendUnique(rows: Portfolio[], more: Portfolio[]): Portfolio[] {
  const seen = new Set(rows.map((p) => p.id));
  return [...rows, ...more.filter((p) => !seen.has(p.id))];
}

/** O que um erro da API diz sobre a conta de quem pede. */
function accountOutcome(caught: unknown): "ended" | "password" | null {
  if (!(caught instanceof ApiError)) return null;
  if (caught.code === "not_authenticated") return "ended";
  if (caught.code === "password_change_required") return "password";
  return null;
}

type Form = {
  name: string;
  notional: string;
  rows: EditorRow[];
  nameError: string | null;
  notionalError: string | null;
  total: string[];
  general: string | null;
};

const BLANK: Form = {
  name: "",
  notional: "",
  rows: [],
  nameError: null,
  notionalError: null,
  total: [],
  general: null,
};

/**
 * As carteiras (`/carteiras`, RF-02 a RF-06), no casco, como no `lista.html` aprovado, só com
 * classes do kit.
 *
 * **A sessão** (o plano, "A sessão nas telas da carteira"): só pede à API com a sessão logada;
 * carregando, o esqueleto, sem pedido; anônimo, o aviso "para quem entrou", sem `ended`, com o
 * `next` para esta página — nunca um pedido que volte 401 a quem nunca entrou.
 *
 * **A lista** (RF-03): `GET portfolios`, 50 por página, na ordem da API; "Mostrar mais" pede o
 * `offset` seguinte, e a falha dele deixa as já carregadas.
 *
 * **A criação** (RF-04 a RF-06): o nome, o valor e o editor da composição. "Criar carteira"
 * confere primeiro o que a API confere, na ordem dela, e põe o foco no primeiro campo com erro;
 * passando, `POST portfolios`, e o 201 vai à página da carteira nova. A falha mostra a mensagem
 * no lugar e mantém tudo o que foi digitado; o 401 chama `expired()` e põe o aviso de sessão
 * terminada no lugar dos botões.
 */
export function PortfoliosScreen() {
  const session = useSession();
  const { expired, reload } = session;
  const location = useLocation();
  const navigate = useNavigate();
  const archived = (location.state as PortfoliosLocationState | null)?.archived;

  const [lastMe, setLastMe] = useState<Me | null>(null);
  const [ended, setEnded] = useState(false);

  // A lista.
  const [rows, setRows] = useState<Portfolio[] | null>(null);
  const [count, setCount] = useState(0);
  const [listStatus, setListStatus] = useState<"loading" | "ok" | "error" | "ended">(
    "loading",
  );
  const [moreStatus, setMoreStatus] = useState<"idle" | "loading" | "error">("idle");
  // Uma página vazia antes do `count`: não há mais o que pedir.
  const [exhausted, setExhausted] = useState(false);
  const listSeq = useRef(0);

  // A criação.
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<Form>(BLANK);
  const [sending, setSending] = useState(false);
  const [formEnded, setFormEnded] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const focusInvalid = useRef(false);
  const focusName = useRef(false);

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const id = useId();
  const ids = {
    title: `${id}-criar`,
    name: `${id}-nome`,
    notional: `${id}-valor`,
  };

  useEffect(() => {
    if (session.status === "authenticated") setLastMe(session.me);
  }, [session]);

  // Depois de um 401 a sessão vira anônima, e a página fica com a conta que tinha.
  const me: Me | null =
    session.status === "authenticated" ? session.me : ended ? lastMe : null;
  const signedIn = session.status === "authenticated";

  const handleAccount = useCallback(
    (outcome: "ended" | "password" | null): boolean => {
      if (outcome === "password") {
        void reload();
        return true;
      }
      if (outcome === "ended") {
        setEnded(true);
        expired();
        return true;
      }
      return false;
    },
    [expired, reload],
  );

  const loadFirst = useCallback(async () => {
    listSeq.current += 1;
    const seq = listSeq.current;
    setMoreStatus("idle");
    setListStatus("loading");
    try {
      const page = await fetchPage(0);
      if (!mounted.current || seq !== listSeq.current) return;
      setRows(appendUnique([], page.results));
      setCount(page.count);
      setExhausted(page.results.length === 0);
      setListStatus("ok");
    } catch (caught) {
      if (!mounted.current || seq !== listSeq.current) return;
      const outcome = accountOutcome(caught);
      setListStatus(outcome === "ended" ? "ended" : "error");
      handleAccount(outcome);
    }
  }, [handleAccount]);

  // Só com a sessão logada: nunca um pedido antes de ela resolver, nem do anônimo.
  useEffect(() => {
    if (signedIn) void loadFirst();
  }, [signedIn, loadFirst]);

  async function loadMore() {
    if (moreStatus === "loading" || rows === null) return;
    const seq = listSeq.current;
    setMoreStatus("loading");
    try {
      const page = await fetchPage(rows.length);
      if (!mounted.current || seq !== listSeq.current) return;
      setRows((current) => appendUnique(current ?? [], page.results));
      setCount(page.count);
      setExhausted(page.results.length === 0);
      setMoreStatus("idle");
    } catch (caught) {
      if (!mounted.current || seq !== listSeq.current) return;
      const outcome = accountOutcome(caught);
      setMoreStatus(outcome === null ? "error" : "idle");
      if (outcome === "ended") setListStatus("ended");
      handleAccount(outcome);
    }
  }

  // O foco, depois de desenhar: o nome ao abrir a criação; o primeiro campo com erro depois de
  // conferir ou de a API responder.
  useEffect(() => {
    if (focusName.current) {
      focusName.current = false;
      nameRef.current?.focus();
    }
    if (focusInvalid.current) {
      focusInvalid.current = false;
      formRef.current?.querySelector<HTMLElement>("[aria-invalid='true']")?.focus();
    }
  });

  function openForm() {
    setForm(BLANK);
    setOpen(true);
    focusName.current = true;
  }

  function cancelForm() {
    setForm(BLANK);
    setOpen(false);
  }

  function setRowsOf(change: (rows: EditorRow[]) => EditorRow[]) {
    setForm((current) => ({ ...current, rows: change(current.rows) }));
  }

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending) return;
    const nameError = form.name.trim() === "" ? TEXTOS["carteiras.erro.nome"] : null;
    const notional = form.notional.trim() === "" ? null : parseNotional(form.notional);
    const notionalError =
      form.notional.trim() !== "" && notional === null
        ? TEXTOS["carteiras.erro.valor"]
        : null;
    const holdings = checkHoldings(form.rows);
    const next: Form = {
      ...form,
      rows: holdings.rows,
      nameError,
      notionalError,
      total: holdings.total,
      general: null,
    };
    setForm(next);
    if (nameError !== null || notionalError !== null || !holdings.ok) {
      focusInvalid.current = true;
      return;
    }

    setSending(true);
    try {
      const body = await apiPost<unknown>(PORTFOLIOS_PATH, {
        name: form.name.trim(),
        notional: notional === null ? null : notionalToApi(notional),
        holdings: holdingsToApi(form.rows),
      });
      if (!isRecord(body) || !isPortfolio(body.portfolio)) {
        throw new ApiError(201, "unexpected_response", "portfolios fora da forma");
      }
      if (!mounted.current) return;
      void navigate(portfolioPath(body.portfolio.id));
    } catch (caught) {
      if (!mounted.current) return;
      setSending(false);
      const outcome = accountOutcome(caught);
      if (outcome === "ended") setFormEnded(true);
      if (handleAccount(outcome)) return;
      const mapped = applyHoldingsError(caught, next.rows);
      setForm({
        ...next,
        rows: mapped?.rows ?? next.rows,
        total: mapped?.total ?? [],
        general: mapped === null ? TEXTOS["carteiras.erro.envio"] : mapped.general,
      });
      focusInvalid.current = true;
    }
  }

  // --- o desenho ---------------------------------------------------------------------

  const listEmpty = listStatus === "ok" && rows !== null && rows.length === 0;
  // "Nova carteira" na cabeça: não enquanto a lista carrega, nem com a lista vazia (que tem o
  // convite dela), nem com a criação aberta, nem depois da sessão terminada.
  const showNew =
    me !== null && !ended && !open && listStatus !== "loading" && !listEmpty;

  const head = (
    <div className="ruvor-page-head ruvor-portfolios-head">
      <div>
        <p className="ruvor-eyebrow">{TEXTOS["carteiras.eyebrow"]}</p>
        <h1 className="ruvor-display">{TEXTOS["carteiras.titulo"]}</h1>
        <p className="ruvor-sub">{TEXTOS["carteiras.sub"]}</p>
        {me !== null && !me.organization.is_personal && (
          <p className="ruvor-portfolios-head__org">
            {TEXTOS["carteiras.sub.organizacao"](me.organization.name)}
          </p>
        )}
      </div>
      {showNew && (
        <button
          className="ruvor-btn ruvor-btn--primary ruvor-push"
          type="button"
          data-part="nova"
          onClick={openForm}
        >
          <Glyph name="briefcase" />
          <span>{TEXTOS["carteiras.nova"]}</span>
        </button>
      )}
    </div>
  );

  if (session.status === "loading") {
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteiras">
        {head}
        <section className="ruvor-panel" aria-busy="true">
          <p className="ruvor-sr-only">{TEXTOS["carteiras.lista.carregando"]}</p>
          <div className="ruvor-panel__body ruvor-stack" aria-hidden="true">
            <span className="ruvor-skeleton ruvor-skeleton--short" />
            <span className="ruvor-skeleton ruvor-skeleton--short" />
            <span className="ruvor-skeleton ruvor-skeleton--short" />
          </div>
        </section>
      </div>
    );
  }

  if (me === null) {
    // Quem não entrou: o aviso "para quem entrou" no lugar da tela, sem pedido.
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteiras">
        {head}
        <div className="ruvor-page-notice">
          <SignInNotice ended={false} />
        </div>
      </div>
    );
  }

  const listHead = (shown: number | null) => (
    <div className="ruvor-panel__head">
      <Glyph name="briefcase" />
      <h2 className="ruvor-h3">{TEXTOS["carteiras.lista.titulo"]}</h2>
      {shown !== null && (
        <span className="ruvor-push ruvor-muted">
          {TEXTOS["carteiras.lista.contagem"](shown)}
        </span>
      )}
    </div>
  );

  const thead = (
    <thead>
      <tr>
        <th scope="col">{TEXTOS["carteiras.col.nome"]}</th>
        <th scope="col">{TEXTOS["carteiras.col.acoes"]}</th>
        <th scope="col">{TEXTOS["carteiras.col.versao"]}</th>
        <th scope="col">{TEXTOS["carteiras.col.valor"]}</th>
        <th scope="col">{TEXTOS["carteiras.col.mudou"]}</th>
      </tr>
    </thead>
  );

  let list: ReactNode;
  if (listStatus === "ended") {
    list = <SignInNotice ended />;
  } else if (listStatus === "error") {
    list = (
      <div
        className="ruvor-callout ruvor-callout--critical"
        role="alert"
        data-part="lista-erro"
      >
        <span className="ruvor-icon ruvor-icon--critical">
          <Glyph name="x-circle" weight="duotone" />
        </span>
        <div className="ruvor-stack">
          <div>
            <b>{TEXTOS["carteiras.lista.erro.titulo"]}</b>
            <p className="ruvor-note">{TEXTOS["carteiras.lista.erro.texto"]}</p>
          </div>
          <div>
            <button
              className="ruvor-btn"
              type="button"
              onClick={() => void loadFirst()}
            >
              <Glyph name="arrows-clockwise" />
              <span>{TEXTOS["carteiras.tentarDeNovo"]}</span>
            </button>
          </div>
        </div>
      </div>
    );
  } else if (listStatus === "loading" || rows === null) {
    list = (
      <section className="ruvor-panel" aria-busy="true" data-part="lista">
        {listHead(null)}
        <p className="ruvor-sr-only">{TEXTOS["carteiras.lista.carregando"]}</p>
        <table className="ruvor-table ruvor-portfolios" aria-hidden="true">
          {thead}
          <tbody>
            {[0, 1, 2].map((line) => (
              <tr key={line} className="ruvor-portfolios__skel">
                {[0, 1, 2, 3, 4].map((cell) => (
                  <td key={cell}>
                    <span className="ruvor-skeleton" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    );
  } else if (rows.length === 0) {
    list = (
      <section className="ruvor-panel" data-part="lista">
        {listHead(0)}
        <div className="ruvor-panel__body ruvor-state">
          <span className="ruvor-icon ruvor-icon--evidence">
            <Glyph name="info" weight="duotone" />
          </span>
          <div className="ruvor-state__body">
            <p className="ruvor-state__title">
              {TEXTOS["carteiras.lista.vazia.titulo"]}
            </p>
            <p className="ruvor-state__text">{TEXTOS["carteiras.lista.vazia.texto"]}</p>
            {!open && !ended && (
              <div className="ruvor-state__actions">
                <button
                  className="ruvor-btn ruvor-btn--primary"
                  type="button"
                  data-part="criar-primeira"
                  onClick={openForm}
                >
                  <Glyph name="briefcase" />
                  <span>{TEXTOS["carteiras.lista.vazia.criar"]}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </section>
    );
  } else {
    const more = count > rows.length && !exhausted;
    list = (
      <section className="ruvor-panel" data-part="lista">
        {listHead(count)}
        <table className="ruvor-table ruvor-portfolios">
          {thead}
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} data-id={p.id}>
                <td>
                  <Link className="ruvor-portfolios__name" to={portfolioPath(p.id)}>
                    {p.name}
                  </Link>
                </td>
                <td data-label={TEXTOS["carteiras.col.acoes"]}>
                  {TEXTOS["carteiras.acoes"](p.holdings.length)}
                </td>
                <td data-label={TEXTOS["carteiras.col.versao"]} className="ruvor-num">
                  {p.version}
                </td>
                <td
                  data-label={TEXTOS["carteiras.col.valor"]}
                  className={
                    p.notional !== null ? "ruvor-num" : "ruvor-portfolios__muted"
                  }
                >
                  {p.notional !== null
                    ? formatBrlText(p.notional)
                    : TEXTOS["carteiras.semValor"]}
                </td>
                <td data-label={TEXTOS["carteiras.col.mudou"]} className="ruvor-num">
                  {formatInstant(p.version_created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {more && (
          <div className="ruvor-portfolios-more" data-part="mais">
            <button
              className="ruvor-btn"
              type="button"
              aria-busy={moreStatus === "loading" ? true : undefined}
              disabled={moreStatus === "loading"}
              onClick={() => void loadMore()}
            >
              {moreStatus === "error" ? (
                <>
                  <Glyph name="arrows-clockwise" />
                  <span>{TEXTOS["carteiras.tentarDeNovo"]}</span>
                </>
              ) : (
                TEXTOS["carteiras.mostrarMais"]
              )}
            </button>
            <span aria-live="polite">
              {moreStatus === "loading"
                ? TEXTOS["carteiras.carregandoMais"]
                : TEXTOS["carteiras.mostrando"](rows.length, count)}
            </span>
            {moreStatus === "error" && (
              <p className="ruvor-portfolios-more__error" role="alert">
                {TEXTOS["carteiras.maisErro"]}
              </p>
            )}
          </div>
        )}
      </section>
    );
  }

  function field(
    fieldId: string,
    label: string,
    hint: string,
    value: string,
    error: string | null,
    onChange: (text: string) => void,
    extra: { maxLength?: number; inputMode?: "decimal"; ref?: typeof nameRef },
  ) {
    return (
      <div className="ruvor-field">
        <label className="ruvor-label" htmlFor={fieldId}>
          {label}
        </label>
        <input
          ref={extra.ref}
          className="ruvor-input"
          id={fieldId}
          type="text"
          autoComplete="off"
          maxLength={extra.maxLength}
          inputMode={extra.inputMode}
          value={value}
          aria-describedby={
            error !== null ? `${fieldId}-dica ${fieldId}-erro` : `${fieldId}-dica`
          }
          aria-invalid={error !== null ? true : undefined}
          disabled={sending}
          onChange={(event) => onChange(event.target.value)}
        />
        <span className="ruvor-hint" id={`${fieldId}-dica`}>
          {hint}
        </span>
        {error !== null && (
          <span className="ruvor-field__error" id={`${fieldId}-erro`}>
            {error}
          </span>
        )}
      </div>
    );
  }

  const creation = open && (
    <section className="ruvor-panel" aria-labelledby={ids.title} data-part="criacao">
      <div className="ruvor-panel__head">
        <Glyph name="briefcase" />
        <h2 className="ruvor-h3" id={ids.title}>
          {TEXTOS["carteiras.criar.titulo"]}
        </h2>
      </div>
      <div className="ruvor-panel__body ruvor-portfolio-form-body">
        <form
          ref={formRef}
          className="ruvor-portfolio-form"
          noValidate
          aria-busy={sending ? true : undefined}
          onSubmit={(event) => void onCreate(event)}
        >
          <div className="ruvor-form-grid ruvor-portfolio-form__fields">
            {field(
              ids.name,
              TEXTOS["carteiras.campo.nome"],
              TEXTOS["carteiras.campo.nomeDica"],
              form.name,
              form.nameError,
              (text) => setForm((current) => ({ ...current, name: text })),
              { maxLength: NAME_MAX, ref: nameRef },
            )}
            {field(
              ids.notional,
              TEXTOS["carteiras.campo.valor"],
              TEXTOS["carteiras.campo.valorDica"],
              form.notional,
              form.notionalError,
              (text) => setForm((current) => ({ ...current, notional: text })),
              { inputMode: "decimal" },
            )}
          </div>
          <fieldset className="ruvor-fieldset">
            <legend className="ruvor-fieldset__title">
              {TEXTOS["carteiras.composicao.titulo"]}
            </legend>
            {/* Um <span>, item do flex do .ruvor-fieldset: sem a margem do <p> (o mockup a zerava
                com estilo na linha). */}
            <span className="ruvor-hint">{TEXTOS["carteiras.composicao.dica"]}</span>
            <HoldingsEditor
              rows={form.rows}
              totalErrors={form.total}
              disabled={sending}
              onAdd={(asset) =>
                setRowsOf((current) => [...current, newRow(asset.ticker, asset.name)])
              }
              onWeightChange={(index, text) =>
                setRowsOf((current) =>
                  current.map((row, i) => (i === index ? { ...row, text } : row)),
                )
              }
              onWeightBlur={(index) =>
                setRowsOf((current) =>
                  current.map((row, i) => (i === index ? blurRow(row) : row)),
                )
              }
              onRemove={(index) =>
                setRowsOf((current) => current.filter((_, i) => i !== index))
              }
            />
          </fieldset>
          {form.general !== null && (
            <div
              className="ruvor-callout ruvor-callout--critical ruvor-portfolio-form__general"
              role="alert"
            >
              <Glyph name="warning" />
              <span>{form.general}</span>
            </div>
          )}
          {formEnded ? (
            <SignInNotice ended />
          ) : (
            <div className="ruvor-portfolio-form__actions">
              <button
                className="ruvor-btn ruvor-btn--primary"
                type="submit"
                disabled={sending}
                aria-busy={sending ? true : undefined}
                data-part="criar"
              >
                {sending && <Glyph name="spinner-gap" className="ruvor-spin" />}
                <span>
                  {sending ? TEXTOS["carteiras.criando"] : TEXTOS["carteiras.criar"]}
                </span>
              </button>
              <button
                className="ruvor-btn ruvor-btn--ghost"
                type="button"
                disabled={sending}
                onClick={cancelForm}
              >
                {TEXTOS["carteiras.cancelar"]}
              </button>
            </div>
          )}
        </form>
      </div>
    </section>
  );

  return (
    <div className="ruvor-stack ruvor-stack--loose" data-screen="carteiras">
      {head}
      {archived !== undefined && (
        <div className="ruvor-callout" role="status" data-part="arquivada">
          <span className="ruvor-icon ruvor-icon--validated">
            <Glyph name="check-circle" weight="duotone" />
          </span>
          <div>{TEXTOS["carteiras.arquivada"](archived)}</div>
        </div>
      )}
      {creation}
      {list}
    </div>
  );
}
