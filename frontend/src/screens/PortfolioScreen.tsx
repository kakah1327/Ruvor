import {
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";
import { Link, useNavigate } from "react-router";

import { ApiError, apiDelete, apiGet, apiPatch, apiPut } from "../api/client";
import type { Portfolio } from "../api/types";
import { Glyph } from "../components/Glyph";
import { HoldingsEditor } from "../components/HoldingsEditor";
import { PortfolioRiskSection } from "../components/PortfolioRiskSection";
import { SignInNotice } from "../components/SignInNotice";
import { TEXTOS } from "../content/textos";
import { formatInstant } from "../format/numbers";
import {
  apiDecimalText,
  applyHoldingsError,
  blurRow,
  centsText,
  checkHoldings,
  type EditorRow,
  holdingsToApi,
  newRow,
} from "../portfolio/editor";
import { formatBrlText, notionalToApi, parseNotional } from "../portfolio/notional";
import { parseWeight, sumCents } from "../portfolio/weights";
import { useSession } from "../session/SessionProvider";
import {
  isPortfolio,
  PORTFOLIOS_PATH,
  type PortfoliosLocationState,
} from "./PortfoliosScreen";

/** "Composição mudou em": o instante no fuso da B3, como as outras telas. */
const TIME_ZONE = "America/Sao_Paulo";
/** O nome tem até 100 caracteres (`PortfolioUpdateIn`). */
const NAME_MAX = 100;
/** O "Entrar" do aviso de sessão terminada: recebe o foco depois de um 401. */
const NOTICE_LINK = "[data-signin-notice] a";
/** O primeiro controle do diálogo, que recebe o foco quando ele abre. */
const FIRST_CONTROL = "button:not([disabled]), a[href]";

/**
 * Onde o 401 chegou: o aviso de sessão terminada entra no lugar dessa ação. `risk` é o pedido de
 * cálculo ou uma leitura do risco (a seção chama `expired()`; a página o vê pela sessão).
 */
type Ended = "name" | "value" | "unset" | "comp" | "archive" | "risk";

type Page =
  | { kind: "loading" }
  | { kind: "error" }
  | { kind: "notfound" }
  | { kind: "ended" } // o 401 ao carregar
  | { kind: "ok"; portfolio: Portfolio };

/** O nome ou o valor no lugar: o texto digitado, a mensagem do campo e a falha do pedido. */
type Inline = {
  text: string;
  error: string | null;
  sending: boolean;
  fail: string | null;
};

/** A composição em edição: as linhas do editor, as mensagens da soma e a falha do pedido. */
type Comp = {
  rows: EditorRow[];
  total: string[];
  sending: boolean;
  fail: string | null;
};

/**
 * A resposta do `PUT` na leitura: "salva", "nada mudou" ou "outra pessoa mudou" (RF-07); com um
 * cálculo em curso da versão anterior, a frase dele junto (`extra`, ou no lugar de "salva").
 */
type Reply = { text: string; review: boolean; extra: string | null };

type Archive = { sending: boolean; error: string | null; ended: boolean };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** O que um erro diz além da própria ação: a conta de quem pede, ou a carteira que sumiu. */
function outcomeOf(caught: unknown): "ended" | "password" | "notfound" | null {
  if (!(caught instanceof ApiError)) return null;
  switch (caught.code) {
    case "not_authenticated":
      return "ended";
    case "password_change_required":
      return "password";
    case "portfolio_not_found":
      return "notfound";
    default:
      return null;
  }
}

/**
 * A falha de uma escrita (RF-08), pelo `code` — nunca a mensagem da API —, seguida de que nada
 * mudou: rede, resposta fora da forma e 5xx são "falar com o servidor"; o 429, com ou sem
 * `wait_seconds`; o `csrf_failed` que sobrou da repetição do cliente; e qualquer outro `code`.
 */
function writeFailure(caught: unknown): string {
  let text: string = TEXTOS["carteira.erro.outro"];
  if (!(caught instanceof ApiError)) {
    text = TEXTOS["carteira.erro.rede"];
  } else if (caught.code === "too_many_requests") {
    const wait = caught.details.wait_seconds;
    text =
      typeof wait === "number"
        ? TEXTOS["carteira.erro.muitos"](wait)
        : TEXTOS["carteira.erro.muitosSemTempo"];
  } else if (caught.code === "csrf_failed") {
    text = TEXTOS["carteira.erro.csrf"];
  } else if (
    caught.status === 0 ||
    caught.status >= 500 ||
    caught.code === "network_error" ||
    caught.code === "unexpected_response"
  ) {
    text = TEXTOS["carteira.erro.rede"];
  }
  return `${text} ${TEXTOS["carteira.erro.mantido"]}`;
}

/** A mensagem que a API manda para um campo no `invalid_parameter` (`details.fields`), como chega. */
function fieldMessage(caught: unknown, field: "name" | "notional"): string | null {
  if (!(caught instanceof ApiError) || caught.code !== "invalid_parameter") return null;
  const { fields } = caught.details;
  if (!isRecord(fields)) return null;
  const messages = fields[field];
  if (!Array.isArray(messages)) return null;
  const first = messages[0];
  return typeof first === "string" && first !== "" ? first : null;
}

/** O corpo `{portfolio}` de `GET`, `PATCH` e `PUT`; fora da forma é erro, como no cliente. */
function portfolioOf(body: unknown, status: number): Portfolio {
  if (!isRecord(body) || !isPortfolio(body.portfolio)) {
    throw new ApiError(status, "unexpected_response", "portfolio fora da forma");
  }
  return body.portfolio;
}

/** O decimal da API no campo, na abertura: só o ponto vira vírgula ("40.00" → "40,00"). */
function apiToField(value: string): string {
  return value.replace(".", ",");
}

function Failure({ text }: { text: string }) {
  return (
    <div
      className="ruvor-callout ruvor-callout--critical"
      role="alert"
      data-part="falha"
    >
      <Glyph name="warning" />
      <span>{text}</span>
    </div>
  );
}

function Sending({ label }: { label: string }) {
  return (
    <button
      className="ruvor-btn ruvor-btn--primary"
      type="button"
      aria-busy="true"
      disabled
    >
      <Glyph name="spinner-gap" className="ruvor-spin" />
      <span>{label}</span>
    </button>
  );
}

/**
 * A página da carteira (`/carteiras/:id`, RF-02, RF-07, RF-08), no casco, como o `carteira.html`
 * aprovado, só com classes do kit.
 *
 * **A sessão** (o plano, "A sessão nas telas da carteira"): só pede à API com a sessão logada;
 * carregando, o esqueleto, sem pedido; anônimo, o aviso "para quem entrou", sem `ended`.
 *
 * **A leitura** (`GET portfolios/{id}`): o nome, o valor, a versão, quando a composição mudou e
 * quem criou; a composição na ordem da API, por código. Estados: carregando, erro com "Tentar de
 * novo", não encontrada (o 404, ao abrir ou no meio do uso), e o 401 ao abrir, com o aviso de
 * sessão terminada no lugar da página.
 *
 * **As escritas**: o nome e o valor no lugar (`PATCH`, com `notional: null` para tirar o valor),
 * a composição no lugar (`PUT .../holdings`, com o editor da criação) e o arquivamento com
 * confirmação no diálogo (`DELETE`, que volta à lista com o nome da carteira arquivada). A
 * resposta do `PUT` se lê pela `version` contra a que a tela conhecia: a mesma, "nada mudou"; a
 * seguinte, "salva"; maior, "outra pessoa mudou". A falha de uma escrita mostra a mensagem no
 * lugar da ação e mantém o que estava, com o que foi digitado; o 404 leva a "não encontrada".
 *
 * **O 401 numa escrita** chama `expired()`: a página fica à vista, só leitura, com o que foi
 * digitado; todas as ações de escrita somem, e um aviso só entra no lugar da que falhou — Esc e
 * "Cancelar" não as trazem de volta; no diálogo, o outro botão vira "Fechar".
 *
 * **O risco** (T9) é a seção de `PortfolioRiskSection`, depois da composição, montada só com a
 * carteira aberta; ela diz à página se há cálculo em curso, para as frases da composição (RF-07):
 * o aviso no editor e a resposta do `PUT` que muda a versão.
 */
export function PortfolioScreen({ portfolioId }: { portfolioId: string }) {
  const session = useSession();
  const { expired, reload } = session;
  const navigate = useNavigate();
  const signedIn = session.status === "authenticated";
  const path = `${PORTFOLIOS_PATH}/${encodeURIComponent(portfolioId)}`;

  const [page, setPage] = useState<Page>({ kind: "loading" });
  const [ended, setEnded] = useState<Ended | null>(null);
  const [name, setName] = useState<Inline | null>(null);
  const [value, setValue] = useState<Inline | null>(null);
  const [unsetSending, setUnsetSending] = useState(false);
  const [valueFail, setValueFail] = useState<string | null>(null);
  const [comp, setComp] = useState<Comp | null>(null);
  const [compReply, setCompReply] = useState<Reply | null>(null);
  const [archive, setArchive] = useState<Archive | null>(null);
  const [riskRunning, setRiskRunning] = useState(false);

  const rootRef = useRef<HTMLDivElement>(null);
  const focusNext = useRef<string | null>(null);
  const loadSeq = useRef(0);

  // O diálogo, como na gestão de usuários do M2.1b.
  const dialogRef = useRef<HTMLDialogElement>(null);
  const shownIn = useRef<HTMLDialogElement | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  const focusDialog = useRef<string | null>(null);
  const restore = useRef(false);

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const id = useId();
  const ids = {
    name: `${id}-nome`,
    value: `${id}-valor`,
    comp: `${id}-composicao`,
    dialog: `${id}-arquivar`,
  };

  const load = useCallback(async () => {
    loadSeq.current += 1;
    const seq = loadSeq.current;
    setPage({ kind: "loading" });
    try {
      const portfolio = portfolioOf(await apiGet<unknown>(path), 200);
      if (!mounted.current || seq !== loadSeq.current) return;
      setPage({ kind: "ok", portfolio });
    } catch (caught) {
      if (!mounted.current || seq !== loadSeq.current) return;
      const outcome = outcomeOf(caught);
      if (outcome === "notfound") {
        setPage({ kind: "notfound" });
      } else if (outcome === "ended") {
        setPage({ kind: "ended" });
        expired();
      } else {
        setPage({ kind: "error" });
        if (outcome === "password") void reload();
      }
    }
  }, [path, expired, reload]);

  // Só com a sessão logada: nunca um pedido antes de ela resolver, nem do anônimo.
  useEffect(() => {
    if (signedIn) void load();
  }, [signedIn, load]);

  // O foco, depois de desenhar; e o diálogo, aberto uma vez por arquivamento.
  useEffect(() => {
    const element = dialogRef.current;
    if (archive === null) shownIn.current = null;
    if (archive !== null && element !== null) {
      if (shownIn.current !== element) {
        shownIn.current = element;
        if (!element.open) element.showModal();
      }
      if (focusDialog.current !== null) {
        element.querySelector<HTMLElement>(focusDialog.current)?.focus();
        focusDialog.current = null;
      }
    }
    if (archive === null && restore.current) {
      restore.current = false;
      const from = opener.current;
      opener.current = null;
      const target = from?.isConnected
        ? from
        : rootRef.current?.querySelector<HTMLElement>(NOTICE_LINK);
      target?.focus();
    }
    if (focusNext.current !== null) {
      rootRef.current?.querySelector<HTMLElement>(focusNext.current)?.focus();
      focusNext.current = null;
    }
  });

  /** A carteira que a resposta de uma escrita devolveu, no lugar da que estava. */
  function show(portfolio: Portfolio) {
    setPage({ kind: "ok", portfolio });
  }

  /** O 404 numa escrita: a página inteira vai a "não encontrada", e o que estava aberto fecha. */
  const gone = useCallback(() => {
    setName(null);
    setValue(null);
    setComp(null);
    setArchive(null);
    setPage({ kind: "notfound" });
  }, []);

  /** Os erros que valem para qualquer escrita; devolve se tratou. */
  function handleWrite(caught: unknown, where: Ended): boolean {
    const outcome = outcomeOf(caught);
    if (outcome === "notfound") {
      gone();
      return true;
    }
    if (outcome === "ended") {
      setEnded(where);
      expired();
      focusNext.current = NOTICE_LINK;
      return true;
    }
    if (outcome === "password") {
      void reload();
      return true;
    }
    return false;
  }

  async function patch(changes: Record<string, string | null>): Promise<Portfolio> {
    return portfolioOf(await apiPatch<unknown>(path, changes), 200);
  }

  // --- o nome ------------------------------------------------------------------------

  function openName(portfolio: Portfolio) {
    setName({ text: portfolio.name, error: null, sending: false, fail: null });
    focusNext.current = `[id="${ids.name}"]`;
  }

  function cancelName() {
    setName(null);
    focusNext.current = '[data-part="mudar-nome"]';
  }

  async function saveName(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (name === null || name.sending || ended !== null) return;
    const { text } = name;
    const trimmed = text.trim();
    if (trimmed === "") {
      setName({
        text,
        error: TEXTOS["carteiras.erro.nome"],
        sending: false,
        fail: null,
      });
      focusNext.current = `[id="${ids.name}"]`;
      return;
    }
    setName({ text, error: null, sending: true, fail: null });
    try {
      const portfolio = await patch({ name: trimmed });
      if (!mounted.current) return;
      show(portfolio);
      setName(null);
      focusNext.current = '[data-part="mudar-nome"]';
    } catch (caught) {
      if (!mounted.current) return;
      setName({ text, error: null, sending: false, fail: null });
      if (handleWrite(caught, "name")) return;
      const message = fieldMessage(caught, "name");
      setName({
        text,
        error: message,
        sending: false,
        fail: message === null ? writeFailure(caught) : null,
      });
      if (message !== null) focusNext.current = `[id="${ids.name}"]`;
    }
  }

  // --- o valor -----------------------------------------------------------------------

  function openValue(portfolio: Portfolio) {
    setValue({
      text: portfolio.notional === null ? "" : apiToField(portfolio.notional),
      error: null,
      sending: false,
      fail: null,
    });
    setValueFail(null);
    focusNext.current = `[id="${ids.value}"]`;
  }

  function cancelValue() {
    setValue(null);
    focusNext.current = '[data-part="mudar-valor"]';
  }

  async function saveValue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (value === null || value.sending || ended !== null) return;
    const { text } = value;
    const notional = parseNotional(text);
    if (notional === null) {
      setValue({
        text,
        error: TEXTOS["carteiras.erro.valor"],
        sending: false,
        fail: null,
      });
      focusNext.current = `[id="${ids.value}"]`;
      return;
    }
    setValue({ text, error: null, sending: true, fail: null });
    try {
      const portfolio = await patch({ notional: notionalToApi(notional) });
      if (!mounted.current) return;
      show(portfolio);
      setValue(null);
      focusNext.current = '[data-part="mudar-valor"]';
    } catch (caught) {
      if (!mounted.current) return;
      setValue({ text, error: null, sending: false, fail: null });
      if (handleWrite(caught, "value")) return;
      const message = fieldMessage(caught, "notional");
      setValue({
        text,
        error: message,
        sending: false,
        fail: message === null ? writeFailure(caught) : null,
      });
      if (message !== null) focusNext.current = `[id="${ids.value}"]`;
    }
  }

  /** "Tirar o valor": `{"notional": null}` direto, sem confirmação (barato de desfazer). */
  async function unsetValue() {
    if (unsetSending || ended !== null) return;
    setUnsetSending(true);
    setValueFail(null);
    try {
      const portfolio = await patch({ notional: null });
      if (!mounted.current) return;
      setUnsetSending(false);
      show(portfolio);
      focusNext.current = '[data-part="mudar-valor"]';
    } catch (caught) {
      if (!mounted.current) return;
      setUnsetSending(false);
      if (handleWrite(caught, "unset")) return;
      setValueFail(writeFailure(caught));
    }
  }

  // --- a composição ------------------------------------------------------------------

  function openComp(portfolio: Portfolio) {
    setComp({
      rows: portfolio.holdings.map((h) =>
        newRow(h.ticker, h.name, apiToField(h.weight)),
      ),
      total: [],
      sending: false,
      fail: null,
    });
    setCompReply(null);
    focusNext.current = '[data-part="editor"] input';
  }

  function cancelComp() {
    setComp(null);
    focusNext.current = '[data-part="editar-composicao"]';
  }

  function setRowsOf(change: (rows: EditorRow[]) => EditorRow[]) {
    setComp((current) =>
      current === null ? current : { ...current, rows: change(current.rows) },
    );
  }

  async function saveComp(event: FormEvent<HTMLFormElement>, known: number) {
    event.preventDefault();
    if (comp === null || comp.sending || ended !== null) return;
    const checked = checkHoldings(comp.rows);
    if (!checked.ok) {
      setComp({ rows: checked.rows, total: checked.total, sending: false, fail: null });
      focusNext.current = "[aria-invalid='true']";
      return;
    }
    const { rows } = checked;
    const running = riskRunning;
    setComp({ rows, total: [], sending: true, fail: null });
    try {
      const portfolio = portfolioOf(
        await apiPut<unknown>(`${path}/holdings`, { holdings: holdingsToApi(rows) }),
        200,
      );
      if (!mounted.current) return;
      // A resposta pela `version` contra a conhecida (RF-07): a API não cria versão quando a
      // composição é a mesma, e não tem controle de edição simultânea (a última escrita vence).
      // O cálculo em curso, quando havia, é da versão conhecida: o risco passa à nova.
      const version = portfolio.version;
      let next: Reply;
      if (version === known) {
        next = {
          text: TEXTOS["carteira.composicao.nadaMudou"](known),
          review: false,
          extra: null,
        };
      } else if (version > known + 1) {
        next = {
          text: TEXTOS["carteira.composicao.outraPessoa"](version),
          review: true,
          extra: running
            ? TEXTOS["carteira.composicao.riscoEmCurso"](known, version)
            : null,
        };
      } else {
        next = {
          text: running
            ? TEXTOS["carteira.composicao.salvaEmCurso"](version, known)
            : TEXTOS["carteira.composicao.salva"](version),
          review: false,
          extra: null,
        };
      }
      setCompReply(next);
      show(portfolio);
      setComp(null);
      focusNext.current = '[data-part="editar-composicao"]';
    } catch (caught) {
      if (!mounted.current) return;
      setComp({ rows, total: [], sending: false, fail: null });
      if (handleWrite(caught, "comp")) return;
      const mapped = applyHoldingsError(caught, rows);
      if (mapped === null) {
        setComp({ rows, total: [], sending: false, fail: writeFailure(caught) });
        return;
      }
      setComp({
        rows: mapped.rows,
        total: mapped.total,
        sending: false,
        fail:
          mapped.general === null
            ? null
            : `${TEXTOS["carteira.erro.forma"]} ${TEXTOS["carteira.erro.mantido"]}`,
      });
      focusNext.current = "[aria-invalid='true']";
    }
  }

  // --- o arquivamento ----------------------------------------------------------------

  function openArchive(from: HTMLElement) {
    opener.current = from;
    focusDialog.current = FIRST_CONTROL;
    setArchive({ sending: false, error: null, ended: false });
  }

  function closeDialog() {
    dialogRef.current?.close();
  }

  /** O `close` do `<dialog>` — "Cancelar", "Fechar" ou o `Esc`: o foco volta a quem abriu. */
  function onDialogClose() {
    restore.current = true;
    setArchive(null);
  }

  async function confirmArchive(portfolioName: string) {
    if (archive === null || archive.sending || archive.ended) return;
    setArchive({ sending: true, error: null, ended: false });
    try {
      await apiDelete(path);
      if (!mounted.current) return;
      const state: PortfoliosLocationState = { archived: portfolioName };
      void navigate("/carteiras", { state });
    } catch (caught) {
      if (!mounted.current) return;
      const outcome = outcomeOf(caught);
      if (outcome === "notfound") {
        opener.current = null;
        gone();
        return;
      }
      if (outcome === "ended") {
        setEnded("archive");
        expired();
        focusDialog.current = NOTICE_LINK;
        setArchive({ sending: false, error: null, ended: true });
        return;
      }
      if (outcome === "password") {
        closeDialog();
        void reload();
        return;
      }
      focusDialog.current = '[data-part="confirmar-arquivar"]';
      setArchive({ sending: false, error: writeFailure(caught), ended: false });
    }
  }

  // --- o desenho ---------------------------------------------------------------------

  const back = (
    <Link className="ruvor-back" to="/carteiras" data-part="voltar">
      <Glyph name="arrow-left" />
      <span>{TEXTOS["carteira.voltar"]}</span>
    </Link>
  );

  if (session.status === "loading" || (signedIn && page.kind === "loading")) {
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteira">
        <div className="ruvor-stack" role="status" aria-busy="true">
          <span className="ruvor-sr-only">{TEXTOS["carteira.carregando"]}</span>
          <div className="ruvor-skeleton ruvor-skeleton--short" aria-hidden="true" />
          <div className="ruvor-skeleton ruvor-skeleton--block" aria-hidden="true" />
          <div className="ruvor-skeleton ruvor-skeleton--block" aria-hidden="true" />
        </div>
      </div>
    );
  }

  if (page.kind === "ended") {
    // O 401 ao abrir, de quem tinha entrado: o aviso de sessão terminada no lugar da página.
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteira">
        <div className="ruvor-page-notice">
          <SignInNotice ended />
        </div>
      </div>
    );
  }

  // A sessão terminada com a página aberta, sem uma escrita que a tenha visto: o 401 veio do risco.
  const sessionEnded = session.status === "anonymous" && session.ended;
  const endedAt: Ended | null =
    ended ?? (sessionEnded && page.kind === "ok" ? "risk" : null);

  if (!signedIn && (endedAt === null || page.kind !== "ok")) {
    // Quem não entrou: o aviso "para quem entrou" no lugar da página, sem pedido.
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteira">
        <div className="ruvor-page-notice">
          <SignInNotice ended={false} />
        </div>
      </div>
    );
  }

  if (page.kind === "notfound") {
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteira">
        <section
          className="ruvor-notfound"
          aria-labelledby={`${id}-nao-encontrada`}
          data-part="nao-encontrada"
        >
          <p className="ruvor-eyebrow">{TEXTOS["carteira.sobrancelha"]}</p>
          <h1 className="ruvor-display" id={`${id}-nao-encontrada`}>
            {TEXTOS["carteira.naoEncontrada.titulo"]}
          </h1>
          <p className="ruvor-sub">{TEXTOS["carteira.naoEncontrada.texto"]}</p>
          <Link className="ruvor-btn ruvor-btn--primary" to="/carteiras">
            <Glyph name="briefcase" />
            <span>{TEXTOS["carteira.naoEncontrada.voltar"]}</span>
          </Link>
        </section>
      </div>
    );
  }

  if (page.kind !== "ok") {
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="carteira">
        <div className="ruvor-stack">
          {back}
          <div className="ruvor-panel" data-part="erro">
            <div className="ruvor-panel__body ruvor-state">
              <span className="ruvor-icon ruvor-icon--review">
                <Glyph name="warning" weight="duotone" />
              </span>
              <div className="ruvor-state__body">
                <p className="ruvor-state__title">{TEXTOS["carteira.erro.titulo"]}</p>
                <p className="ruvor-state__text">{TEXTOS["carteira.erro.texto"]}</p>
                <div className="ruvor-state__actions">
                  <button
                    className="ruvor-btn"
                    type="button"
                    onClick={() => void load()}
                  >
                    <Glyph name="arrows-clockwise" />
                    <span>{TEXTOS["carteiras.tentarDeNovo"]}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const { portfolio } = page;
  const readOnly = endedAt !== null;
  const notice = <SignInNotice ended />;

  /** O `Esc` no campo aberto cancela — salvo depois do 401 ou enviando. */
  function cancelOnEscape(
    event: KeyboardEvent<HTMLFormElement>,
    open: Inline,
    cancel: () => void,
  ) {
    if (event.key === "Escape" && !readOnly && !open.sending) {
      event.preventDefault();
      cancel();
    }
  }

  // A cabeça: o nome (ou o campo dele) e as ações da página.
  let title: ReactNode;
  if (name !== null) {
    const errorId = `${ids.name}-erro`;
    const hintId = `${ids.name}-dica`;
    title = (
      <form
        className="ruvor-inline-edit ruvor-inline-edit--name"
        noValidate
        data-part="form-nome"
        onSubmit={(event) => void saveName(event)}
        onKeyDown={(event) => cancelOnEscape(event, name, cancelName)}
      >
        <label className="ruvor-label" htmlFor={ids.name}>
          {TEXTOS["carteira.nome.campo"]}
        </label>
        <div className="ruvor-inline-edit__row">
          <input
            className="ruvor-input"
            id={ids.name}
            type="text"
            maxLength={NAME_MAX}
            autoComplete="off"
            value={name.text}
            aria-invalid={name.error !== null ? true : undefined}
            aria-describedby={name.error !== null ? errorId : hintId}
            disabled={name.sending}
            readOnly={readOnly}
            onChange={(event) => setName({ ...name, text: event.target.value })}
          />
          {readOnly ? null : name.sending ? (
            <Sending label={TEXTOS["carteira.salvando"]} />
          ) : (
            <>
              <button className="ruvor-btn ruvor-btn--primary" type="submit">
                {TEXTOS["carteira.salvar"]}
              </button>
              <button className="ruvor-btn" type="button" onClick={cancelName}>
                {TEXTOS["carteiras.cancelar"]}
              </button>
            </>
          )}
        </div>
        {name.error !== null ? (
          <span className="ruvor-field__error" id={errorId}>
            {name.error}
          </span>
        ) : (
          <span className="ruvor-hint" id={hintId}>
            {TEXTOS["carteiras.campo.nomeDica"]}
          </span>
        )}
        {name.fail !== null && <Failure text={name.fail} />}
        {ended === "name" && notice}
      </form>
    );
  } else {
    title = (
      <h1 className="ruvor-display" data-part="nome">
        {portfolio.name}
      </h1>
    );
  }

  let actions: ReactNode = null;
  if (ended === "archive") {
    actions = <div className="ruvor-portfolio-top__actions">{notice}</div>;
  } else if (name === null && !readOnly) {
    actions = (
      <div className="ruvor-portfolio-top__actions">
        <button
          className="ruvor-btn ruvor-btn--ghost"
          type="button"
          data-part="mudar-nome"
          onClick={() => openName(portfolio)}
        >
          {TEXTOS["carteira.nome.mudar"]}
        </button>
        <button
          className="ruvor-btn"
          type="button"
          data-part="arquivar"
          onClick={(event) => openArchive(event.currentTarget)}
        >
          {TEXTOS["carteira.arquivar"]}
        </button>
      </div>
    );
  }

  // O valor: o fato, ou o campo dele.
  const has = portfolio.notional !== null;
  let valueFact: ReactNode;
  if (value !== null) {
    const errorId = `${ids.value}-erro`;
    const hintId = `${ids.value}-dica`;
    valueFact = (
      <form
        className="ruvor-inline-edit"
        noValidate
        data-part="form-valor"
        onSubmit={(event) => void saveValue(event)}
        onKeyDown={(event) => cancelOnEscape(event, value, cancelValue)}
      >
        <label className="ruvor-sr-only" htmlFor={ids.value}>
          {TEXTOS["carteira.valor.campo"]}
        </label>
        <div className="ruvor-inline-edit__row">
          <input
            className="ruvor-input ruvor-num"
            id={ids.value}
            type="text"
            inputMode="decimal"
            autoComplete="off"
            value={value.text}
            aria-invalid={value.error !== null ? true : undefined}
            aria-describedby={value.error !== null ? errorId : hintId}
            disabled={value.sending}
            readOnly={readOnly}
            onChange={(event) => setValue({ ...value, text: event.target.value })}
          />
          {readOnly ? null : value.sending ? (
            <Sending label={TEXTOS["carteira.salvando"]} />
          ) : (
            <>
              <button className="ruvor-btn ruvor-btn--primary" type="submit">
                {TEXTOS["carteira.salvar"]}
              </button>
              <button className="ruvor-btn" type="button" onClick={cancelValue}>
                {TEXTOS["carteiras.cancelar"]}
              </button>
            </>
          )}
        </div>
        {value.error !== null ? (
          <span className="ruvor-field__error" id={errorId}>
            {value.error}
          </span>
        ) : (
          <span className="ruvor-hint" id={hintId}>
            {TEXTOS["carteiras.campo.valorDica"]}
          </span>
        )}
        {value.fail !== null && <Failure text={value.fail} />}
        {ended === "value" && notice}
      </form>
    );
  } else {
    valueFact = (
      <>
        <span
          className={has ? "ruvor-facts__value ruvor-num" : "ruvor-facts__muted"}
          data-part="valor"
        >
          {portfolio.notional !== null
            ? formatBrlText(portfolio.notional)
            : TEXTOS["carteiras.semValor"]}
        </span>
        <span className="ruvor-note">
          {has ? TEXTOS["carteira.valor.nota.com"] : TEXTOS["carteira.valor.nota.sem"]}
        </span>
        {readOnly ? (
          ended === "unset" || ended === "value" ? (
            notice
          ) : null
        ) : (
          <span className="ruvor-facts__acts">
            {unsetSending ? (
              <Sending label={TEXTOS["carteira.salvando"]} />
            ) : (
              <>
                <button
                  className="ruvor-btn ruvor-btn--ghost"
                  type="button"
                  data-part="mudar-valor"
                  onClick={() => openValue(portfolio)}
                >
                  {has
                    ? TEXTOS["carteira.valor.mudar"]
                    : TEXTOS["carteira.valor.informar"]}
                </button>
                {has && (
                  <button
                    className="ruvor-btn ruvor-btn--ghost"
                    type="button"
                    data-part="tirar-valor"
                    onClick={() => void unsetValue()}
                  >
                    {TEXTOS["carteira.valor.tirar"]}
                  </button>
                )}
              </>
            )}
          </span>
        )}
        {valueFail !== null && <Failure text={valueFail} />}
      </>
    );
  }

  const [changedDate = "", changedTime = ""] = formatInstant(
    portfolio.version_created_at,
    TIME_ZONE,
  ).split(" ");

  // A composição: em leitura, na ordem da API (por código); ou no editor da criação.
  const total = sumCents(portfolio.holdings.map((h) => parseWeight(h.weight) ?? 0));
  let compBody: ReactNode;
  if (comp === null) {
    compBody = (
      <div className="ruvor-panel__body ruvor-stack">
        {compReply !== null && (
          <div
            className="ruvor-callout"
            role={compReply.review ? "alert" : "status"}
            data-part="resposta"
          >
            <span
              className={
                compReply.review
                  ? "ruvor-icon ruvor-icon--review"
                  : "ruvor-icon ruvor-icon--evidence"
              }
            >
              <Glyph name={compReply.review ? "warning" : "info"} weight="duotone" />
            </span>
            <p className="ruvor-reply">{compReply.text}</p>
          </div>
        )}
        {compReply?.extra != null && (
          <div className="ruvor-callout" role="status" data-part="resposta-em-curso">
            <span className="ruvor-icon ruvor-icon--evidence">
              <Glyph name="info" weight="duotone" />
            </span>
            <p className="ruvor-reply">{compReply.extra}</p>
          </div>
        )}
        <table className="ruvor-table ruvor-holdings" data-part="composicao">
          <thead>
            <tr>
              <th scope="col">{TEXTOS["carteiras.col.acao"]}</th>
              <th scope="col">{TEXTOS["carteiras.col.peso"]}</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.holdings.map((h) => (
              <tr key={h.ticker} data-ticker={h.ticker}>
                <td>
                  <span className="ruvor-holding-ticker">{h.ticker}</span>
                  <span className="ruvor-holding-name">{h.name}</span>
                </td>
                <td className="ruvor-num">{`${apiDecimalText(h.weight)}%`}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td>{TEXTOS["carteira.composicao.total"]}</td>
              <td className="ruvor-num">{`${centsText(total)}%`}</td>
            </tr>
          </tfoot>
        </table>
        <p className="ruvor-note">{TEXTOS["carteira.composicao.ordem"]}</p>
      </div>
    );
  } else {
    compBody = (
      <form
        className="ruvor-panel__body ruvor-stack"
        noValidate
        data-part="form-composicao"
        aria-busy={comp.sending ? true : undefined}
        onSubmit={(event) => void saveComp(event, portfolio.version)}
      >
        <p className="ruvor-note">
          {`${TEXTOS["carteiras.composicao.dica"]} ${TEXTOS["carteira.composicao.nota"]}`}
        </p>
        {riskRunning && (
          <div className="ruvor-callout" role="status" data-part="em-curso">
            <span className="ruvor-icon ruvor-icon--evidence">
              <Glyph name="info" weight="duotone" />
            </span>
            <p className="ruvor-reply">
              {TEXTOS["carteira.composicao.emCurso"](portfolio.version)}
            </p>
          </div>
        )}
        <HoldingsEditor
          rows={comp.rows}
          totalErrors={comp.total}
          disabled={comp.sending || readOnly}
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
        {comp.fail !== null && <Failure text={comp.fail} />}
        {readOnly ? (
          ended === "comp" ? (
            notice
          ) : null
        ) : (
          <div className="ruvor-edit-actions">
            <button
              className="ruvor-btn"
              type="button"
              disabled={comp.sending}
              onClick={cancelComp}
            >
              {TEXTOS["carteiras.cancelar"]}
            </button>
            {comp.sending ? (
              <Sending label={TEXTOS["carteira.salvando"]} />
            ) : (
              <button
                className="ruvor-btn ruvor-btn--primary"
                type="submit"
                data-part="salvar-composicao"
              >
                {TEXTOS["carteira.composicao.salvar"]}
              </button>
            )}
          </div>
        )}
      </form>
    );
  }

  return (
    <div
      className="ruvor-stack ruvor-stack--loose"
      data-screen="carteira"
      ref={rootRef}
    >
      <div className="ruvor-stack">
        {back}
        <div className="ruvor-portfolio-top">
          <div className="ruvor-portfolio-top__id">
            <p className="ruvor-eyebrow">{TEXTOS["carteira.sobrancelha"]}</p>
            {title}
          </div>
          {actions}
        </div>
        <section className="ruvor-panel" aria-label={TEXTOS["carteira.fatos.rotulo"]}>
          <div className="ruvor-panel__body">
            <dl className="ruvor-facts">
              <div
                className={value !== null ? "ruvor-facts__wide" : "ruvor-facts__lead"}
              >
                <dt>{TEXTOS["carteira.valor.rotulo"]}</dt>
                <dd>{valueFact}</dd>
              </div>
              <div>
                <dt>{TEXTOS["carteira.versao.rotulo"]}</dt>
                <dd className="ruvor-facts__value ruvor-num" data-part="versao">
                  {portfolio.version}
                </dd>
              </div>
              <div>
                <dt>{TEXTOS["carteira.mudouEm.rotulo"]}</dt>
                <dd className="ruvor-num" data-part="mudou-em">
                  {TEXTOS["carteira.mudouEm"](changedDate, changedTime)}
                </dd>
              </div>
              <div>
                <dt>{TEXTOS["carteira.criadaPor.rotulo"]}</dt>
                <dd title={portfolio.created_by.email}>{portfolio.created_by.name}</dd>
              </div>
            </dl>
          </div>
        </section>
      </div>

      <section
        className="ruvor-panel"
        aria-labelledby={ids.comp}
        data-part="painel-composicao"
      >
        <div className="ruvor-panel__head ruvor-panel__head--wrap">
          <Glyph name="briefcase" />
          <h2 className="ruvor-h3" id={ids.comp}>
            {TEXTOS["carteiras.composicao.titulo"]}
          </h2>
          <span className="ruvor-tag ruvor-tag--neutral">
            {TEXTOS["carteiras.acoes"](
              comp !== null ? comp.rows.length : portfolio.holdings.length,
            )}
          </span>
          {comp === null && !readOnly && (
            <button
              className="ruvor-btn ruvor-push"
              type="button"
              data-part="editar-composicao"
              onClick={() => openComp(portfolio)}
            >
              {TEXTOS["carteira.composicao.editar"]}
            </button>
          )}
        </div>
        {compBody}
      </section>

      <PortfolioRiskSection
        portfolio={portfolio}
        readOnly={readOnly}
        endedHere={endedAt === "risk"}
        onNotFound={gone}
        onRunning={setRiskRunning}
      />

      <dialog
        ref={dialogRef}
        className="ruvor-dialog"
        aria-labelledby={ids.dialog}
        data-dialog={archive !== null ? "arquivar" : undefined}
        onClose={onDialogClose}
        onCancel={(event) => {
          // Enviando, o `Esc` não fecha: o "Cancelar" também está travado.
          if (archive?.sending) event.preventDefault();
        }}
      >
        {archive !== null && (
          <>
            <div className="ruvor-dialog__body">
              <h2 className="ruvor-h3" id={ids.dialog}>
                {TEXTOS["carteira.arquivar.titulo"](portfolio.name)}
              </h2>
              {!archive.ended && (
                <>
                  <p>{TEXTOS["carteira.arquivar.texto"]}</p>
                  <p className="ruvor-note">{TEXTOS["carteira.arquivar.semVolta"]}</p>
                </>
              )}
              {archive.error !== null && <Failure text={archive.error} />}
              {archive.ended && <SignInNotice ended />}
            </div>
            <div className="ruvor-dialog__actions">
              <button
                className="ruvor-btn"
                type="button"
                disabled={archive.sending}
                onClick={closeDialog}
              >
                {archive.ended
                  ? TEXTOS["usuarios.confirmar.fechar"]
                  : TEXTOS["carteiras.cancelar"]}
              </button>
              {archive.ended ? null : archive.sending ? (
                <Sending label={TEXTOS["carteira.arquivar.enviando"]} />
              ) : (
                <button
                  className="ruvor-btn ruvor-btn--primary"
                  type="button"
                  data-part="confirmar-arquivar"
                  onClick={() => void confirmArchive(portfolio.name)}
                >
                  {TEXTOS["carteira.arquivar.confirmar"]}
                </button>
              )}
            </div>
          </>
        )}
      </dialog>
    </div>
  );
}
