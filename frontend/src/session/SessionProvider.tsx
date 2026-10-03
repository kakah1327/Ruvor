/**
 * O estado de sessão (RF-03), um só no aplicativo. Mora numa rota de layout na raiz de
 * `routes` (`App.tsx`): sem filhos, o provedor renderiza o `<Outlet>`, e todo teste que monta
 * `createMemoryRouter(routes)` o recebe sem montagem extra.
 *
 * Ao montar, **um** `GET /api/v1/auth/me`: 200 com a forma do `me` → logado; 200 com outra
 * forma, ou qualquer erro (401, outro erro da API, rede) → anônimo, sem tentar de novo sozinho.
 * Enquanto não volta, `loading`. A leitura é idempotente: o `StrictMode` a dobra em
 * desenvolvimento sem efeito.
 *
 * As ações (`setMe`, `reload`, `signOut`, `expired`) mudam o estado; uma leitura do `auth/me`
 * que volta **depois** de uma ação mais nova é descartada, para a resposta velha não desfazer
 * a entrada, a saída ou o fim de sessão.
 *
 * O bloqueio do RF-05: com `me.must_change_password`, o provedor renderiza a troca obrigatória
 * (`PasswordScreen` no modo `required`) **no lugar do `<Outlet>`**, na URL corrente, sem navegar
 * — exceto em `/entrar` e `/cadastro`, que montam a tela deles: a entrada bem-sucedida navega ao
 * `next`, e ele mostra a troca. Depois dela, o `reload()` tira a marca e o `<Outlet>` volta na
 * mesma URL. Fora de um roteador (o provedor com filhos), não há URL para isentar: o bloqueio
 * não se aplica.
 */
import {
  createContext,
  type JSX,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Outlet, useInRouterContext, useLocation } from "react-router";

import { ApiError, apiGet, apiPost } from "../api/client";
import { PasswordScreen } from "../screens/PasswordScreen";
import { isMe, type Me } from "./types";

export type Session =
  | { status: "loading" }
  | { status: "anonymous"; ended: boolean } // ended: 401 depois de estar logado (RF-16)
  | { status: "authenticated"; me: Me };

export type SessionApi = Session & {
  /** Login e signup: a resposta é o `me`. */
  setMe(me: Me): void;
  /** Relê `auth/me` — depois do `password`, de rebaixar a si mesma, do `password_change_required`. */
  reload(): Promise<void>;
  /** `POST auth/logout`; 204 ou 401 → anônimo, sem erro. Outro erro sobe, e o estado fica. */
  signOut(): Promise<void>;
  /** 401 de rota que exige conta → anônimo, com `ended: true`. */
  expired(): void;
};

const ME_PATH = "/api/v1/auth/me";
const LOGOUT_PATH = "/api/v1/auth/logout";

const ANONYMOUS: Session = { status: "anonymous", ended: false };

/** Fora do provedor: o anônimo do padrão, com as ações inertes. */
const OUTSIDE: SessionApi = {
  ...ANONYMOUS,
  setMe: () => {},
  reload: async () => {},
  signOut: async () => {},
  expired: () => {},
};

const SessionContext = createContext<SessionApi>(OUTSIDE);

/** O `auth/me` lido como sessão: o `me` com a forma certa, ou anônimo. */
async function readSession(): Promise<Session> {
  try {
    const body = await apiGet<unknown>(ME_PATH);
    return isMe(body) ? { status: "authenticated", me: body } : ANONYMOUS;
  } catch {
    return ANONYMOUS;
  }
}

/** As telas que a troca obrigatória não cobre (RF-04, RF-05): a entrada leva ao `next`. */
const EXEMPT = new Set(["/entrar", "/cadastro"]);

/**
 * O bloqueio do RF-05, dentro do roteador: a troca obrigatória no lugar do conteúdo, na URL
 * corrente, enquanto `must_change_password`. Sempre no mesmo lugar da árvore — o conteúdo não
 * remonta quando a sessão sai do carregando.
 */
function RequiredPasswordGate(props: { session: Session; children: ReactNode }) {
  const { pathname } = useLocation();
  const blocked =
    props.session.status === "authenticated" &&
    props.session.me.must_change_password &&
    !EXEMPT.has(pathname);
  return blocked ? <PasswordScreen mode="required" /> : props.children;
}

export function SessionProvider(props: { children?: ReactNode }): JSX.Element {
  const [session, setSession] = useState<Session>({ status: "loading" });
  // Sobe a cada mudança de estado pedida; a leitura que começou antes dela não vale mais.
  const version = useRef(0);

  const apply = useCallback((next: Session) => {
    version.current += 1;
    setSession(next);
  }, []);

  /** Lê o `auth/me` e aplica, se nenhuma mudança mais nova chegou enquanto isso. */
  const load = useCallback(
    async (isActive: () => boolean = () => true) => {
      const startedAt = version.current;
      const next = await readSession();
      if (isActive() && version.current === startedAt) {
        apply(next);
      }
    },
    [apply],
  );

  useEffect(() => {
    let active = true;
    void load(() => active);
    return () => {
      active = false;
    };
  }, [load]);

  const setMe = useCallback(
    (me: Me) => apply({ status: "authenticated", me }),
    [apply],
  );
  const reload = useCallback(() => load(), [load]);
  const expired = useCallback(
    () => apply({ status: "anonymous", ended: true }),
    [apply],
  );
  const signOut = useCallback(async () => {
    try {
      await apiPost<undefined>(LOGOUT_PATH);
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) {
        throw error;
      }
    }
    apply(ANONYMOUS);
  }, [apply]);

  const value = useMemo<SessionApi>(
    () => ({ ...session, setMe, reload, signOut, expired }),
    [session, setMe, reload, signOut, expired],
  );

  const inRouter = useInRouterContext();
  const content = props.children === undefined ? <Outlet /> : props.children;

  return (
    <SessionContext value={value}>
      {inRouter ? (
        <RequiredPasswordGate session={session}>{content}</RequiredPasswordGate>
      ) : (
        content
      )}
    </SessionContext>
  );
}

/** O estado de sessão; fora do provedor, o anônimo do padrão, e nada quebra. */
export function useSession(): SessionApi {
  return useContext(SessionContext);
}
