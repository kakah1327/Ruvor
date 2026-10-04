import {
  type FormEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import { ApiError, apiGet, apiPatch, apiPost } from "../api/client";
import { Glyph } from "../components/Glyph";
import { SectionSkeleton } from "../components/SectionStatus";
import { SignInNotice } from "../components/SignInNotice";
import { TEXTOS } from "../content/textos";
import { formatInstant } from "../format/numbers";
import { useSession } from "../session/SessionProvider";
import type { Me, OrgUser } from "../session/types";
import { apiFieldLists, FieldErrorList } from "./SignUpScreen";

const USERS_PATH = "/api/v1/organization/users";
const PAGE_SIZE = 50;
/** O último acesso no fuso da B3, como as outras datas e horas do Ruvor. */
const LAST_LOGIN_TIME_ZONE = "America/Sao_Paulo";

/** As ações da linha (RF-14); `rebaixarSi` é "Mudar para membro" na própria linha. */
type Action = "admin" | "member" | "rebaixarSi" | "desativar" | "reativar" | "senha";

/** O `data-dialog` de cada diálogo aberto, a marca que o roteiro da execução real lê. */
const DIALOG_MARK: Record<Action, string> = {
  admin: "confirmar-admin",
  member: "confirmar-member",
  rebaixarSi: "confirmar-rebaixar-si",
  desativar: "confirmar-desativar",
  reativar: "confirmar-reativar",
  senha: "confirmar-senha",
};

type Dialog =
  | {
      kind: "confirm";
      action: Action;
      user: OrgUser;
      sending: boolean;
      error: string | null;
      /** `user_not_found`: só o título, o erro e "Fechar". */
      gone: boolean;
      /** 401: o aviso de sessão terminada no lugar da ação, e "Fechar". */
      ended: boolean;
    }
  | {
      kind: "password";
      variant: "criado" | "nova";
      user: OrgUser;
      /** A senha provisória: só na memória da tela enquanto o diálogo está aberto. */
      password: string;
      copy: "ok" | "falhou" | null;
    };

/** Onde o botão que abriu o diálogo estava: a linha (pelo e-mail) e a posição nela. */
type Spot = { email: string; index: number };

type Field = "name" | "email";
type FieldErrors = Partial<Record<Field, string[]>>;

/** O que um erro da API diz sobre a conta de quem pede, para qualquer pedido da tela. */
type AccountOutcome = "ended" | "member" | "personal" | "password" | null;

function accountOutcome(caught: unknown): AccountOutcome {
  if (!(caught instanceof ApiError)) return null;
  switch (caught.code) {
    case "not_authenticated":
      return "ended";
    case "permission_denied":
      return "member";
    case "personal_organization":
      return "personal";
    case "password_change_required":
      return "password";
    default:
      return null;
  }
}

/** O texto do erro geral, pelo `code` — nunca a mensagem da API. */
function generalError(caught: unknown): string {
  if (!(caught instanceof ApiError)) return TEXTOS["usuarios.erro.rede"];
  switch (caught.code) {
    case "too_many_requests": {
      const wait = caught.details.wait_seconds;
      return typeof wait === "number"
        ? TEXTOS["usuarios.erro.muitos"](wait)
        : TEXTOS["usuarios.erro.muitosSemTempo"];
    }
    case "csrf_failed":
      return TEXTOS["usuarios.erro.csrf"];
    case "network_error":
    case "unexpected_response":
      return TEXTOS["usuarios.erro.rede"];
    default:
      return TEXTOS["usuarios.erro.outro"];
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Confere a forma do `user` da gestão (`services.user_body`), com o instante legível. */
function isOrgUser(value: unknown): value is OrgUser {
  return (
    isRecord(value) &&
    typeof value.email === "string" &&
    typeof value.name === "string" &&
    (value.role === "admin" || value.role === "member") &&
    typeof value.is_active === "boolean" &&
    typeof value.must_change_password === "boolean" &&
    typeof value.created_at === "string" &&
    (value.last_login === null ||
      (typeof value.last_login === "string" &&
        !Number.isNaN(new Date(value.last_login).getTime())))
  );
}

/** O corpo da criação e da senha nova: o `user` e a `temporary_password`. */
function isWithPassword(
  value: unknown,
): value is { user: OrgUser; temporary_password: string } {
  return (
    isRecord(value) &&
    isOrgUser(value.user) &&
    typeof value.temporary_password === "string"
  );
}

type Page = { count: number; results: OrgUser[] };

function isPage(value: unknown): value is Page {
  return (
    isRecord(value) &&
    typeof value.count === "number" &&
    Array.isArray(value.results) &&
    value.results.every(isOrgUser)
  );
}

/** Uma página da lista; corpo fora da forma é erro, como no cliente. */
async function fetchPage(offset: number): Promise<Page> {
  const body = await apiGet<unknown>(
    `${USERS_PATH}?limit=${PAGE_SIZE}&offset=${offset}`,
  );
  if (!isPage(body)) {
    throw new ApiError(200, "unexpected_response", "organization/users fora da forma");
  }
  return body;
}

/** A página seguinte depois das linhas que já estão na tela, sem repetir e-mail. */
function appendUnique(rows: OrgUser[], more: OrgUser[]): OrgUser[] {
  const seen = new Set(rows.map((u) => u.email));
  return [...rows, ...more.filter((u) => !seen.has(u.email))];
}

/** O último acesso, "dd/mm/aaaa às hh:mm" no fuso da B3, ou "nunca entrou". */
function lastAccess(value: string | null): string | null {
  if (value === null) return null;
  const [date, time] = formatInstant(value, LAST_LOGIN_TIME_ZONE).split(" ");
  return TEXTOS["usuarios.ultimoAcesso"](date ?? "", time ?? "");
}

/** O papel como a tela o mostra: `admin` é "Administração" (o portão da T9). */
const ROLE_LABEL: Record<OrgUser["role"], string> = {
  member: TEXTOS["usuarios.papel.member"],
  admin: TEXTOS["usuarios.papel.admin"],
};

/** O primeiro controle do diálogo, que recebe o foco quando o conteúdo dele aparece. */
const FIRST_CONTROL = "input, button:not([disabled]), a[href]";

/**
 * A gestão de usuários (`/organizacao/usuarios`, RF-11 a RF-14), no casco, como o
 * `usuarios.html` aprovado, só com classes do kit. O papel `admin` se mostra "Administração".
 *
 * **Quem não pode gerir vê o porquê** (RF-12), pelo `me` antes de qualquer pedido — membro,
 * organização pessoal —, e pelo `code` depois (`permission_denied`, `personal_organization`);
 * quem não entrou vê o aviso "para quem entrou"; `password_change_required` relê a conta, e o
 * bloqueio do RF-05 assume. Com a sessão carregando, o esqueleto, sem pedido.
 *
 * **A lista** (RF-11): `GET organization/users`, 50 por página, ordenada pela API; "Mostrar
 * mais" pede a seguinte e não repete e-mail. A própria linha leva "você" e só a mudança de papel:
 * nem "Desativar" nem "Nova senha provisória".
 *
 * **Criar** (RF-13): nome, e-mail e papel ("Membro" de padrão); o vazio não manda pedido. O 201
 * abre o diálogo com a senha provisória, que se copia por `navigator.clipboard.writeText`; ao
 * fechar, a senha sai da memória da tela, e a lista é **relida da primeira página** — nunca se
 * insere a linha à mão.
 *
 * **As ações** (RF-14), cada uma com confirmação num diálogo que diz o efeito; o e-mail vai no
 * caminho por `encodeURIComponent`, e a linha mostra o `user` que a API devolve. Rebaixar o
 * próprio papel relê a conta (`reload()`), e a tela passa ao caso "membro", com o foco nele.
 *
 * **O 401** (RF-16) chama `expired()` e mostra o aviso de sessão terminada **no lugar da ação**
 * — na lista, no formulário, no diálogo —; o resto da página fica.
 *
 * **O diálogo** (`<dialog>` com `showModal()`) devolve o foco explicitamente a quem o abriu, ao
 * fechar; se aquele botão deixou de existir, ao da mesma posição na mesma linha. Quando o
 * conteúdo do diálogo aberto é trocado, o foco vai ao primeiro controle dele. O foco preso e o
 * `Esc` são do navegador.
 */
export function UsersScreen() {
  const session = useSession();
  const { expired, reload } = session;

  const [lastMe, setLastMe] = useState<Me | null>(null);
  const [ended, setEnded] = useState(false);
  const [blocked, setBlocked] = useState<"member" | "personal" | null>(null);

  // A lista.
  const [rows, setRows] = useState<OrgUser[] | null>(null);
  const [count, setCount] = useState(0);
  const [nextOffset, setNextOffset] = useState(0);
  const [exhausted, setExhausted] = useState(false);
  const [listStatus, setListStatus] = useState<"loading" | "ok" | "error" | "ended">(
    "loading",
  );
  const [moreStatus, setMoreStatus] = useState<"idle" | "loading" | "error">("idle");
  const listSeq = useRef(0);
  const listRef = useRef<HTMLDivElement>(null);

  // A criação.
  const [values, setValues] = useState<Record<Field, string>>({ name: "", email: "" });
  const [role, setRole] = useState<"member" | "admin">("member");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [formEnded, setFormEnded] = useState(false);
  const nameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const submitRef = useRef<HTMLButtonElement>(null);
  const focusAfter = useRef<Field | "submit" | null>(null);

  // O diálogo.
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const openerSpot = useRef<Spot | null>(null);
  const focusFirst = useRef(false);
  // O elemento em que o `showModal()` já foi chamado para o diálogo corrente. O `close()` tira o
  // `open` na hora, mas o evento `close` chega numa tarefa: a renderização que vem antes dele
  // (a linha trocada, por exemplo) não pode reabrir o `<dialog>`. Zera quando o diálogo é nulo.
  const shownIn = useRef<HTMLDialogElement | null>(null);
  const skipRestore = useRef(false);
  const restore = useRef<{ opener: HTMLElement | null; spot: Spot | null } | null>(
    null,
  );

  // O caso do RF-12 que aparece no meio do uso recebe o foco.
  const caseRef = useRef<HTMLDivElement>(null);
  const focusCase = useRef(false);

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const id = useId();
  const ids = {
    form: `${id}-criar`,
    list: `${id}-lista`,
    dialogTitle: `${id}-dialogo`,
    password: `${id}-senha`,
    role: `${id}-papel`,
    roleHint: `${id}-papel-dica`,
    input: (field: Field) => `${id}-${field}`,
    errors: (field: Field) => `${id}-${field}-erro`,
  };

  useEffect(() => {
    if (session.status === "authenticated") setLastMe(session.me);
  }, [session]);

  // Depois de um 401 a sessão vira anônima, e a página fica com a conta que tinha.
  const me: Me | null =
    session.status === "authenticated" ? session.me : ended ? lastMe : null;
  const manages =
    me !== null &&
    blocked === null &&
    me.role === "admin" &&
    !me.organization.is_personal;

  /** Os erros de conta que valem para qualquer pedido; devolve se tratou. */
  const handleAccount = useCallback(
    (outcome: AccountOutcome): boolean => {
      if (outcome === "member" || outcome === "personal") {
        focusCase.current = true;
        setBlocked(outcome);
        return true;
      }
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
    setListStatus((current) => (current === "ok" ? "ok" : "loading"));
    try {
      const page = await fetchPage(0);
      if (!mounted.current || seq !== listSeq.current) return;
      setRows(appendUnique([], page.results));
      setCount(page.count);
      setNextOffset(page.results.length);
      setExhausted(page.results.length === 0);
      setListStatus("ok");
    } catch (caught) {
      if (!mounted.current || seq !== listSeq.current) return;
      const outcome = accountOutcome(caught);
      if (outcome === "ended") setListStatus("ended");
      else if (outcome === null) setListStatus("error");
      handleAccount(outcome);
    }
  }, [handleAccount]);

  useEffect(() => {
    if (manages) void loadFirst();
  }, [manages, loadFirst]);

  async function loadMore() {
    if (moreStatus === "loading") return;
    const seq = listSeq.current;
    setMoreStatus("loading");
    try {
      const page = await fetchPage(nextOffset);
      if (!mounted.current || seq !== listSeq.current) return;
      setRows((current) => appendUnique(current ?? [], page.results));
      setCount(page.count);
      setNextOffset((current) => current + page.results.length);
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

  /** A linha com o estado que a API devolveu (RF-14). */
  function replaceRow(user: OrgUser) {
    setRows((current) =>
      current === null
        ? current
        : current.map((u) => (u.email === user.email ? user : u)),
    );
  }

  // --- o diálogo ---------------------------------------------------------------------

  function spotOf(element: HTMLElement | null): Spot | null {
    const row = element?.closest<HTMLElement>("tr[data-email]");
    if (row == null || element == null) return null;
    const buttons = [...row.querySelectorAll<HTMLElement>("[data-act]")];
    return { email: row.dataset.email ?? "", index: buttons.indexOf(element) };
  }

  function fromSpot(spot: Spot | null): HTMLElement | null {
    if (spot === null || listRef.current === null) return null;
    const row = [
      ...listRef.current.querySelectorAll<HTMLElement>("tr[data-email]"),
    ].find((tr) => tr.dataset.email === spot.email);
    const buttons = [...(row?.querySelectorAll<HTMLElement>("[data-act]") ?? [])];
    if (buttons.length === 0) return null;
    return buttons[Math.min(Math.max(spot.index, 0), buttons.length - 1)] ?? null;
  }

  function openDialog(next: Dialog, from: HTMLElement | null) {
    opener.current = from;
    openerSpot.current = spotOf(from);
    focusFirst.current = true;
    setDialog(next);
  }

  /** Troca o conteúdo do diálogo aberto: o foco vai ao primeiro controle do novo. */
  function swapDialog(next: Dialog) {
    focusFirst.current = true;
    setDialog(next);
  }

  function closeDialog() {
    dialogRef.current?.close();
  }

  /** Fecha sem devolver o foco: a tela vai mudar de caso, e o foco vai ao caso. */
  function dismissDialog() {
    const element = dialogRef.current;
    if (element?.open) {
      skipRestore.current = true;
      element.close();
    } else {
      setDialog(null);
    }
  }

  /** O `close` do `<dialog>` — "Cancelar", "Fechar", o fim da ação ou o `Esc`. */
  function onDialogClose() {
    restore.current = skipRestore.current
      ? null
      : { opener: opener.current, spot: openerSpot.current };
    skipRestore.current = false;
    opener.current = null;
    openerSpot.current = null;
    // A senha provisória sai da memória da tela aqui.
    setDialog(null);
  }

  useEffect(() => {
    const element = dialogRef.current;
    if (dialog === null) shownIn.current = null;
    if (dialog !== null && element !== null) {
      if (shownIn.current !== element) {
        shownIn.current = element;
        if (!element.open) element.showModal();
      }
      if (focusFirst.current) {
        focusFirst.current = false;
        element.querySelector<HTMLElement>(FIRST_CONTROL)?.focus();
      }
    }
    if (dialog === null && restore.current !== null) {
      const { opener: from, spot } = restore.current;
      restore.current = null;
      const target = from?.isConnected ? from : fromSpot(spot);
      // O foco volta explicitamente a quem abriu (o contrato da T14): não depende do navegador.
      target?.focus();
    }
    if (focusCase.current && caseRef.current !== null) {
      focusCase.current = false;
      caseRef.current.focus();
    }
    if (!busy && focusAfter.current !== null) {
      const field = focusAfter.current;
      focusAfter.current = null;
      (field === "name"
        ? nameRef
        : field === "email"
          ? emailRef
          : submitRef
      ).current?.focus();
    }
  });

  function openConfirm(action: Action, user: OrgUser, from: HTMLElement) {
    openDialog(
      {
        kind: "confirm",
        action,
        user,
        sending: false,
        error: null,
        gone: false,
        ended: false,
      },
      from,
    );
  }

  async function onConfirm() {
    const current = dialog;
    if (current?.kind !== "confirm" || current.sending) return;
    setDialog({ ...current, sending: true, error: null });
    const path = `${USERS_PATH}/${encodeURIComponent(current.user.email)}`;
    try {
      if (current.action === "senha") {
        const body = await apiPost<unknown>(`${path}/temporary-password`);
        if (!isWithPassword(body)) {
          throw new ApiError(
            200,
            "unexpected_response",
            "temporary-password fora da forma",
          );
        }
        if (!mounted.current) return;
        replaceRow(body.user);
        swapDialog({
          kind: "password",
          variant: "nova",
          user: body.user,
          password: body.temporary_password,
          copy: null,
        });
        return;
      }
      const changes =
        current.action === "desativar"
          ? { is_active: false }
          : current.action === "reativar"
            ? { is_active: true }
            : { role: current.action === "admin" ? "admin" : "member" };
      const body = await apiPatch<unknown>(path, changes);
      if (!isOrgUser(body)) {
        throw new ApiError(
          200,
          "unexpected_response",
          "organization/users fora da forma",
        );
      }
      if (!mounted.current) return;
      replaceRow(body);
      if (current.action === "rebaixarSi") {
        // A tela relê a conta e passa ao caso "membro", com o foco nele.
        focusCase.current = true;
        dismissDialog();
        void reload();
        return;
      }
      closeDialog();
    } catch (caught) {
      if (!mounted.current) return;
      const outcome = accountOutcome(caught);
      if (outcome === "ended") {
        handleAccount(outcome);
        swapDialog({ ...current, sending: false, error: null, ended: true });
        return;
      }
      if (outcome !== null) {
        dismissDialog();
        handleAccount(outcome);
        return;
      }
      if (caught instanceof ApiError && caught.code === "user_not_found") {
        swapDialog({
          ...current,
          sending: false,
          gone: true,
          error: TEXTOS["usuarios.erro.naoEncontrado"],
        });
        void loadFirst();
        return;
      }
      const error =
        caught instanceof ApiError && caught.code === "last_admin"
          ? TEXTOS["usuarios.erro.lastAdmin"]
          : generalError(caught);
      swapDialog({ ...current, sending: false, error });
    }
  }

  async function onCopy() {
    if (dialog?.kind !== "password") return;
    const { password } = dialog;
    let copied = false;
    try {
      await navigator.clipboard.writeText(password);
      copied = true;
    } catch {
      copied = false;
    }
    if (!mounted.current) return;
    setDialog((current) =>
      current?.kind === "password" && current.password === password
        ? { ...current, copy: copied ? "ok" : "falhou" }
        : current,
    );
    // A cópia negada deixa a senha selecionada, para o teclado.
    if (!copied) passwordRef.current?.select();
  }

  // --- a criação ---------------------------------------------------------------------

  function change(field: Field, value: string) {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => {
      if (current[field] === undefined) return current;
      const { [field]: _gone, ...rest } = current;
      return rest;
    });
  }

  async function onCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const name = values.name.trim();
    const email = values.email.trim();
    const found: FieldErrors = {};
    if (name === "") found.name = [TEXTOS["usuarios.erro.nomeVazio"]];
    if (email === "") found.email = [TEXTOS["usuarios.erro.emailVazio"]];
    setFormError(null);
    setErrors(found);
    if (found.name !== undefined) {
      nameRef.current?.focus();
      return;
    }
    if (found.email !== undefined) {
      emailRef.current?.focus();
      return;
    }

    setBusy(true);
    try {
      const body = await apiPost<unknown>(USERS_PATH, { email, name, role });
      if (!isWithPassword(body)) {
        throw new ApiError(
          201,
          "unexpected_response",
          "organization/users fora da forma",
        );
      }
      if (!mounted.current) return;
      setBusy(false);
      setValues({ name: "", email: "" });
      setRole("member");
      openDialog(
        {
          kind: "password",
          variant: "criado",
          user: body.user,
          password: body.temporary_password,
          copy: null,
        },
        submitRef.current,
      );
      // A lista relida da primeira página: a ordem e o `count` são os da API (RF-13).
      void loadFirst();
    } catch (caught) {
      if (!mounted.current) return;
      setBusy(false);
      const outcome = accountOutcome(caught);
      if (outcome === "ended") setFormEnded(true);
      if (handleAccount(outcome)) return;
      if (caught instanceof ApiError && caught.code === "email_taken") {
        setErrors({ email: [TEXTOS["usuarios.erro.emailTaken"]] });
        focusAfter.current = "email";
        return;
      }
      const lists =
        caught instanceof ApiError && caught.code === "invalid_parameter"
          ? apiFieldLists(caught.details, ["name", "email"] as const)
          : null;
      if (lists !== null) {
        setErrors(lists);
        focusAfter.current = lists.name !== undefined ? "name" : "email";
        return;
      }
      setFormError(generalError(caught));
      focusAfter.current = "submit";
    }
  }

  // --- o desenho ---------------------------------------------------------------------

  function head(org: string | null) {
    return (
      <div className="ruvor-page-head">
        <div>
          <p className="ruvor-eyebrow">{TEXTOS["usuarios.eyebrow"]}</p>
          <h1 className="ruvor-display">{TEXTOS["usuarios.titulo"]}</h1>
          {org !== null && <p className="ruvor-sub">{TEXTOS["usuarios.sub"](org)}</p>}
        </div>
      </div>
    );
  }

  if (session.status === "loading") {
    return (
      <div className="ruvor-stack" data-screen="usuarios" aria-busy="true">
        <SectionSkeleton />
      </div>
    );
  }

  if (me === null) {
    // Quem não entrou (anônimo desde a carga): o aviso "para quem entrou" no lugar da tela.
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="usuarios">
        {head(null)}
        <div className="ruvor-page-notice">
          <SignInNotice ended={false} />
        </div>
      </div>
    );
  }

  const memberCase = blocked === "member" || (blocked === null && me.role !== "admin");
  if (memberCase || blocked === "personal" || me.organization.is_personal) {
    const member = memberCase;
    return (
      <div className="ruvor-stack ruvor-stack--loose" data-screen="usuarios">
        {head(null)}
        <div className="ruvor-panel">
          <div className="ruvor-panel__body">
            <div className="ruvor-state" ref={caseRef} tabIndex={-1}>
              <span
                className={
                  member
                    ? "ruvor-icon ruvor-icon--review"
                    : "ruvor-icon ruvor-icon--evidence"
                }
              >
                <Glyph name={member ? "shield-warning" : "buildings"} />
              </span>
              <div className="ruvor-state__body">
                <p className="ruvor-state__title">
                  {member
                    ? TEXTOS["usuarios.membro.titulo"]
                    : TEXTOS["usuarios.pessoal.titulo"]}
                </p>
                <p className="ruvor-state__text">
                  {member
                    ? TEXTOS["usuarios.membro.texto"](me.organization.name)
                    : TEXTOS["usuarios.pessoal.texto"]}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function described(field: Field) {
    const lines = errors[field] ?? [];
    return {
      "aria-invalid": lines.length > 0 ? true : undefined,
      "aria-describedby": lines.length > 0 ? ids.errors(field) : undefined,
    };
  }

  const form = formEnded ? (
    <SignInNotice ended />
  ) : (
    <form
      className="ruvor-form-section"
      noValidate
      aria-labelledby={ids.form}
      aria-busy={busy ? true : undefined}
      data-part="form-criar"
      onSubmit={(event) => void onCreate(event)}
    >
      <div className="ruvor-form-section__intro">
        <h2 className="ruvor-h3" id={ids.form}>
          {TEXTOS["usuarios.criar.titulo"]}
        </h2>
        <p>{TEXTOS["usuarios.criar.texto"]}</p>
      </div>
      <div className="ruvor-form-section__fields">
        {formError !== null && (
          <div className="ruvor-callout ruvor-callout--critical" role="alert">
            <Glyph name="warning" />
            <span>{formError}</span>
          </div>
        )}
        <div className="ruvor-form-grid">
          <div className="ruvor-field">
            <label className="ruvor-label" htmlFor={ids.input("name")}>
              {TEXTOS["usuarios.campo.nome"]}
            </label>
            <input
              ref={nameRef}
              className="ruvor-input"
              id={ids.input("name")}
              name="name"
              type="text"
              autoComplete="off"
              disabled={busy}
              value={values.name}
              onChange={(event) => change("name", event.target.value)}
              {...described("name")}
            />
            <FieldErrorList id={ids.errors("name")} lines={errors.name ?? []} />
          </div>
          <div className="ruvor-field">
            <label className="ruvor-label" htmlFor={ids.input("email")}>
              {TEXTOS["usuarios.campo.email"]}
            </label>
            <input
              ref={emailRef}
              className="ruvor-input"
              id={ids.input("email")}
              name="email"
              type="email"
              autoComplete="off"
              spellCheck={false}
              placeholder={TEXTOS["usuarios.campo.email.exemplo"]}
              disabled={busy}
              value={values.email}
              onChange={(event) => change("email", event.target.value)}
              {...described("email")}
            />
            <FieldErrorList id={ids.errors("email")} lines={errors.email ?? []} />
          </div>
        </div>
        <div className="ruvor-field">
          <span className="ruvor-label" id={ids.role}>
            {TEXTOS["usuarios.campo.papel"]}
          </span>
          {/* biome-ignore lint/a11y/useSemanticElements: o grupo de botões do kit, como a chave de tema. */}
          <div
            className="ruvor-segmented ruvor-segmented--surface"
            role="group"
            aria-labelledby={ids.role}
            aria-describedby={ids.roleHint}
          >
            {(["member", "admin"] as const).map((value) => (
              <button
                key={value}
                className="ruvor-segmented__btn"
                type="button"
                aria-pressed={role === value}
                disabled={busy}
                onClick={() => setRole(value)}
              >
                {ROLE_LABEL[value]}
              </button>
            ))}
          </div>
          <span className="ruvor-hint" id={ids.roleHint}>
            {TEXTOS["usuarios.campo.papel.dica"]}
          </span>
        </div>
        <div className="ruvor-form-section__actions">
          <button
            ref={submitRef}
            className="ruvor-btn ruvor-btn--primary"
            type="submit"
            disabled={busy}
            aria-busy={busy ? true : undefined}
            data-part="botao-criar"
          >
            {busy && <Glyph name="spinner-gap" className="ruvor-spin" />}
            <span>
              {busy
                ? TEXTOS["usuarios.criar.enviando"]
                : TEXTOS["usuarios.criar.botao"]}
            </span>
          </button>
        </div>
      </div>
    </form>
  );

  function actionsOf(user: OrgUser, self: boolean): Action[] {
    const out: Action[] = [
      user.role === "admin" ? (self ? "rebaixarSi" : "member") : "admin",
    ];
    // A própria linha só muda o papel (RF-14): a própria senha se troca pelo menu de conta.
    if (!self) {
      out.push(user.is_active ? "desativar" : "reativar", "senha");
    }
    return out;
  }

  const ACTION_LABEL: Record<Action, string> = {
    admin: TEXTOS["usuarios.acao.admin"],
    member: TEXTOS["usuarios.acao.member"],
    rebaixarSi: TEXTOS["usuarios.acao.member"],
    desativar: TEXTOS["usuarios.acao.desativar"],
    reativar: TEXTOS["usuarios.acao.reativar"],
    senha: TEXTOS["usuarios.acao.senha"],
  };

  const selfEmail = me.email;
  const firstOther = rows?.find((u) => u.email !== selfEmail)?.email ?? null;

  function row(user: OrgUser) {
    const self = user.email === selfEmail;
    const part = self ? "linha-voce" : user.email === firstOther ? "linha" : undefined;
    const access = lastAccess(user.last_login);
    return (
      <tr key={user.email} data-email={user.email} data-part={part}>
        <td>
          <span className="ruvor-users__name">
            {user.name}
            {self && (
              <>
                {" "}
                <span className="ruvor-tag ruvor-tag--neutral">
                  {TEXTOS["usuarios.voce"]}
                </span>
              </>
            )}
          </span>
        </td>
        <td className="ruvor-users__email">{user.email}</td>
        <td data-label={TEXTOS["usuarios.col.papel"]}>{ROLE_LABEL[user.role]}</td>
        <td data-label={TEXTOS["usuarios.col.situacao"]}>
          <ul className="ruvor-tag-list">
            <li>
              {user.is_active ? (
                <span className="ruvor-tag ruvor-tag--validated">
                  {TEXTOS["usuarios.situacao.ativa"]}
                </span>
              ) : (
                <span className="ruvor-tag ruvor-tag--neutral">
                  {TEXTOS["usuarios.situacao.desativada"]}
                </span>
              )}
            </li>
            {user.must_change_password && (
              <li>
                <span className="ruvor-tag ruvor-tag--review">
                  {TEXTOS["usuarios.provisoria"]}
                </span>
              </li>
            )}
          </ul>
        </td>
        <td
          data-label={TEXTOS["usuarios.col.ultimoAcesso"]}
          className={access === null ? "ruvor-users__muted" : "ruvor-num"}
        >
          {access ?? TEXTOS["usuarios.nuncaEntrou"]}
        </td>
        <td>
          {/* biome-ignore lint/a11y/useSemanticElements: o grupo de botões do kit, rotulado pela pessoa. */}
          <div
            className="ruvor-btn-group ruvor-btn-group--wrap"
            role="group"
            aria-label={TEXTOS["usuarios.acoes.rotulo"](user.name)}
          >
            {actionsOf(user, self).map((action, index) => (
              <button
                // A posição, e não a ação: "Desativar" que vira "Reativar" é o mesmo botão.
                // biome-ignore lint/suspicious/noArrayIndexKey: a posição é a identidade do botão.
                key={index}
                className="ruvor-btn ruvor-btn--ghost"
                type="button"
                data-act={action}
                onClick={(event) => openConfirm(action, user, event.currentTarget)}
              >
                {ACTION_LABEL[action]}
              </button>
            ))}
          </div>
        </td>
      </tr>
    );
  }

  let listBody: ReactNode;
  if (listStatus === "ended") {
    listBody = <SignInNotice ended />;
  } else if (listStatus === "error") {
    listBody = (
      <div
        className="ruvor-callout ruvor-callout--critical ruvor-callout--row"
        role="alert"
      >
        <span>{TEXTOS["usuarios.erroLista"]}</span>
        <button className="ruvor-btn" type="button" onClick={() => void loadFirst()}>
          <Glyph name="arrows-clockwise" />
          <span>{TEXTOS["usuarios.tentarDeNovo"]}</span>
        </button>
      </div>
    );
  } else if (listStatus === "loading" || rows === null) {
    listBody = <SectionSkeleton />;
  } else {
    const more = nextOffset < count && !exhausted;
    listBody = (
      <>
        <table className="ruvor-table ruvor-users">
          <thead>
            <tr>
              <th scope="col">{TEXTOS["usuarios.col.nome"]}</th>
              <th scope="col">{TEXTOS["usuarios.col.email"]}</th>
              <th scope="col">{TEXTOS["usuarios.col.papel"]}</th>
              <th scope="col">{TEXTOS["usuarios.col.situacao"]}</th>
              <th scope="col">{TEXTOS["usuarios.col.ultimoAcesso"]}</th>
              <th scope="col">
                <span className="ruvor-sr-only">{TEXTOS["usuarios.col.acoes"]}</span>
              </th>
            </tr>
          </thead>
          <tbody>{rows.map(row)}</tbody>
        </table>
        <div className="ruvor-docs__foot">
          <span className="ruvor-muted">
            {TEXTOS["usuarios.mostrando"](rows.length, count)}
          </span>
          {moreStatus === "error" ? (
            <div
              className="ruvor-callout ruvor-callout--critical ruvor-callout--row"
              role="alert"
            >
              <span>{TEXTOS["usuarios.erroMais"]}</span>
              <button
                className="ruvor-btn"
                type="button"
                onClick={() => void loadMore()}
              >
                <Glyph name="arrows-clockwise" />
                <span>{TEXTOS["usuarios.tentarDeNovo"]}</span>
              </button>
            </div>
          ) : (
            more && (
              <button
                className="ruvor-btn"
                type="button"
                disabled={moreStatus === "loading"}
                aria-busy={moreStatus === "loading" ? true : undefined}
                onClick={() => void loadMore()}
              >
                {TEXTOS["usuarios.mostrarMais"]}
              </button>
            )
          )}
        </div>
      </>
    );
  }

  function confirmText(current: Extract<Dialog, { kind: "confirm" }>) {
    const { user } = current;
    switch (current.action) {
      case "admin":
        return {
          title: TEXTOS["usuarios.confirmar.admin.titulo"](user.name),
          text: TEXTOS["usuarios.confirmar.admin.texto"],
        };
      case "member":
        return {
          title: TEXTOS["usuarios.confirmar.member.titulo"](user.name),
          text: TEXTOS["usuarios.confirmar.member.texto"],
        };
      case "rebaixarSi":
        return {
          title: TEXTOS["usuarios.confirmar.rebaixarSi.titulo"],
          text: TEXTOS["usuarios.confirmar.rebaixarSi.texto"],
        };
      case "desativar":
        return {
          title: TEXTOS["usuarios.confirmar.desativar.titulo"](user.name),
          text: TEXTOS["usuarios.confirmar.desativar.texto"],
        };
      case "reativar":
        return {
          title: TEXTOS["usuarios.confirmar.reativar.titulo"](user.name),
          text: TEXTOS["usuarios.confirmar.reativar.texto"],
        };
      case "senha":
        return {
          title: TEXTOS["usuarios.confirmar.senha.titulo"](user.name),
          text: TEXTOS["usuarios.confirmar.senha.texto"],
        };
    }
  }

  let dialogContent: ReactNode = null;
  if (dialog?.kind === "confirm") {
    const { title, text } = confirmText(dialog);
    const bare = dialog.gone || dialog.ended;
    // Na linha desativada, a mudança de papel diz quando vale.
    const note =
      (dialog.action === "admin" || dialog.action === "member") &&
      !dialog.user.is_active
        ? TEXTOS["usuarios.confirmar.desativada"]
        : null;
    dialogContent = (
      <>
        <div className="ruvor-dialog__body">
          <h2 className="ruvor-h3" id={ids.dialogTitle}>
            {title}
          </h2>
          {!bare && <p>{text}</p>}
          {!bare && note !== null && <p className="ruvor-note">{note}</p>}
          {dialog.error !== null && (
            <div className="ruvor-callout ruvor-callout--critical" role="alert">
              <Glyph name="warning" />
              <span>{dialog.error}</span>
            </div>
          )}
          {dialog.ended && <SignInNotice ended />}
        </div>
        <div className="ruvor-dialog__actions">
          <button
            className="ruvor-btn"
            type="button"
            disabled={dialog.sending}
            onClick={closeDialog}
          >
            {bare
              ? TEXTOS["usuarios.confirmar.fechar"]
              : TEXTOS["usuarios.confirmar.cancelar"]}
          </button>
          {!bare && (
            <button
              className="ruvor-btn ruvor-btn--primary"
              type="button"
              disabled={dialog.sending}
              aria-busy={dialog.sending ? true : undefined}
              onClick={() => void onConfirm()}
            >
              {dialog.sending && <Glyph name="spinner-gap" className="ruvor-spin" />}
              <span>
                {dialog.sending
                  ? TEXTOS["usuarios.confirmar.enviando"]
                  : ACTION_LABEL[dialog.action]}
              </span>
            </button>
          )}
        </div>
      </>
    );
  } else if (dialog?.kind === "password") {
    const { user, variant, copy } = dialog;
    dialogContent = (
      <>
        <div className="ruvor-dialog__body">
          <h2 className="ruvor-h3" id={ids.dialogTitle}>
            {variant === "criado"
              ? TEXTOS["usuarios.senha.criado.titulo"]
              : TEXTOS["usuarios.senha.nova.titulo"]}
          </h2>
          <p>
            {variant === "criado"
              ? TEXTOS["usuarios.senha.criado.texto"](user.name, user.email)
              : TEXTOS["usuarios.senha.nova.texto"](user.name, user.email)}
          </p>
          <div className="ruvor-field">
            <label className="ruvor-label" htmlFor={ids.password}>
              {TEXTOS["usuarios.senha.campo"]}
            </label>
            <div className="ruvor-copy">
              <input
                ref={passwordRef}
                className="ruvor-input"
                id={ids.password}
                type="text"
                readOnly
                value={dialog.password}
                spellCheck={false}
                autoComplete="off"
              />
              <button className="ruvor-btn" type="button" onClick={() => void onCopy()}>
                {copy === "ok" ? (
                  <>
                    <Glyph name="check-circle" />
                    <span>{TEXTOS["usuarios.senha.copiada"]}</span>
                  </>
                ) : (
                  TEXTOS["usuarios.senha.copiar"]
                )}
              </button>
            </div>
            <p
              className={
                copy === "falhou"
                  ? "ruvor-copy__reply ruvor-copy__reply--critical"
                  : "ruvor-copy__reply"
              }
              role="status"
            >
              {copy === "ok" && (
                <>
                  <Glyph name="check-circle" />
                  <span>{TEXTOS["usuarios.senha.copiadaAviso"]}</span>
                </>
              )}
              {copy === "falhou" && (
                <>
                  <Glyph name="warning" />
                  <span>{TEXTOS["usuarios.senha.copiaFalhou"]}</span>
                </>
              )}
            </p>
          </div>
          <ul className="ruvor-dialog__list">
            <li>{TEXTOS["usuarios.senha.umaVez"]}</li>
            <li>{TEXTOS["usuarios.senha.trocar"]}</li>
            <li>{TEXTOS["usuarios.senha.entrega"]}</li>
          </ul>
        </div>
        <div className="ruvor-dialog__actions">
          <button
            className="ruvor-btn ruvor-btn--primary"
            type="button"
            onClick={closeDialog}
          >
            {TEXTOS["usuarios.senha.fechar"]}
          </button>
        </div>
      </>
    );
  }

  const dialogMark =
    dialog === null
      ? undefined
      : dialog.kind === "password"
        ? "senha-provisoria"
        : DIALOG_MARK[dialog.action];

  return (
    <div className="ruvor-stack ruvor-stack--loose" data-screen="usuarios">
      {head(me.organization.name)}

      <section className="ruvor-panel">
        <div className="ruvor-panel__body">{form}</div>
      </section>

      <section className="ruvor-panel" aria-labelledby={ids.list} data-part="lista">
        <div className="ruvor-panel__head">
          <Glyph name="user" />
          <h2 className="ruvor-h3" id={ids.list}>
            {TEXTOS["usuarios.lista.titulo"]}
          </h2>
          {listStatus === "ok" && rows !== null && (
            <span className="ruvor-tag ruvor-tag--neutral ruvor-push">
              {TEXTOS["usuarios.lista.contagem"](count)}
            </span>
          )}
        </div>
        <div
          className="ruvor-panel__body"
          ref={listRef}
          aria-busy={listStatus === "loading" ? true : undefined}
        >
          {listBody}
        </div>
      </section>

      <dialog
        ref={dialogRef}
        className="ruvor-dialog"
        aria-labelledby={ids.dialogTitle}
        data-dialog={dialogMark}
        onClose={onDialogClose}
        onCancel={(event) => {
          // Enviando, o `Esc` não fecha: o "Cancelar" também está travado.
          if (dialog?.kind === "confirm" && dialog.sending) event.preventDefault();
        }}
      >
        {dialogContent}
      </dialog>
    </div>
  );
}
