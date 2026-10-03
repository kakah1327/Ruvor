import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { TEXTOS } from "../content/textos";
import { signInHref } from "../session/next";
import { useSession } from "../session/SessionProvider";
import type { Me } from "../session/types";
import { Glyph } from "./Glyph";

/**
 * As iniciais do avatar, como no `conta.html` aprovado: a primeira letra da primeira e da
 * última palavra do nome, em maiúscula ("Ana Beatriz Souza" → "AS"); nome de uma palavra, uma
 * letra; nome só de espaço (o `createsuperuser` o aceita), a primeira letra do e-mail.
 */
export function initials(name: string, email: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return email.trim().charAt(0).toUpperCase();
  const first = words[0].charAt(0);
  const last = words.length === 1 ? "" : words[words.length - 1].charAt(0);
  return (first + last).toUpperCase();
}

/** "Usuários da organização" (RF-09): só quem administra uma organização que não é pessoal. */
export function canManageUsers(me: Me): boolean {
  return me.role === "admin" && !me.organization.is_personal;
}

/** As páginas que exigem conta (RF-10): quem sai delas vai a `/`. */
function requiresAccount(pathname: string): boolean {
  return pathname.startsWith("/conta/") || pathname.startsWith("/organizacao/");
}

/**
 * O lugar da conta na barra (RF-09, RF-10), por último em `.ruvor-topbar__prefs`, como no
 * `conta.html` aprovado — com a largura fixa do kit nos três estados, sem salto:
 *
 * - **carregando**: o lugar vazio;
 * - **anônimo**: o link "Entrar", para `/entrar?next=<página atual>`;
 * - **logado**: o botão de conta (o nome, as iniciais e a seta; abaixo de 1024 px, o kit deixa
 *   só as iniciais), com `aria-expanded` e `aria-controls`, que abre o menu: o nome e o
 *   e-mail, a organização (ou "Conta pessoal"), "Trocar a senha" (com o `next` na página
 *   atual), "Usuários da organização" (só `canManageUsers`) e "Sair".
 *
 * O menu fecha no clique num item, no `Tab` que sai dele, no clique fora e no `Esc` — que
 * devolve o foco ao botão. "Sair" chama `signOut()` e, numa página que exige conta, navega a
 * `/`; se ele falha, a sessão fica, o menu continua aberto e só ganha a linha de alerta — o
 * resto do menu não remonta, e o `focusout` de um elemento já desmontado não o fecha.
 */
export function AccountMenu() {
  const session = useSession();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const leaving = useRef(false);
  const slotRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = `${useId()}-menu`;

  const here = location.pathname + location.search;
  const signedIn = session.status === "authenticated";

  // Fora do menu aberto: o `Esc` o fecha e devolve o foco ao botão; o clique fora o fecha.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    };
    const onClick = (event: MouseEvent) => {
      const slot = slotRef.current;
      if (
        slot !== null &&
        event.target instanceof Node &&
        slot.contains(event.target)
      ) {
        return;
      }
      setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("click", onClick);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("click", onClick);
    };
  }, [open]);

  // A sessão que deixa de estar logada leva o menu junto.
  useEffect(() => {
    if (!signedIn) setOpen(false);
  }, [signedIn]);

  // O `Tab` que sai do menu o fecha (o `focusout` dele, com o foco indo para fora do lugar da
  // conta). O elemento já desmontado não fecha nada: o `focusout` dele chega com
  // `relatedTarget` nulo e fecharia o menu que continua aberto.
  useEffect(() => {
    const menu = menuRef.current;
    if (!signedIn || menu === null) return;
    const onFocusOut = (event: FocusEvent) => {
      if (!menu.isConnected) return;
      if (event.target instanceof Node && !event.target.isConnected) return;
      const next = event.relatedTarget;
      if (next instanceof Node && slotRef.current?.contains(next)) return;
      setOpen(false);
    };
    menu.addEventListener("focusout", onFocusOut);
    return () => menu.removeEventListener("focusout", onFocusOut);
  }, [signedIn]);

  function toggle() {
    if (!open) setFailed(false);
    setOpen(!open);
  }

  async function signOut() {
    if (leaving.current) return;
    leaving.current = true;
    setFailed(false);
    try {
      await session.signOut();
      setOpen(false);
      if (requiresAccount(location.pathname)) void navigate("/");
    } catch {
      setFailed(true);
    } finally {
      leaving.current = false;
    }
  }

  let content: ReactNode = null;
  if (session.status === "anonymous") {
    content = (
      <Link className="ruvor-topbar__signin" data-part="entrar" to={signInHref(here)}>
        {TEXTOS["conta.entrar"]}
      </Link>
    );
  } else if (session.status === "authenticated") {
    const { me } = session;
    content = (
      <>
        <button
          ref={buttonRef}
          className="ruvor-account ruvor-account--button"
          type="button"
          data-part="conta"
          aria-expanded={open}
          aria-controls={menuId}
          aria-label={TEXTOS["conta.menu.rotulo"](me.name)}
          onClick={toggle}
        >
          <span className="ruvor-account__name">{me.name}</span>
          <span className="ruvor-avatar" data-part="avatar" aria-hidden="true">
            {initials(me.name, me.email)}
          </span>
          <Glyph name="caret-down" />
        </button>
        <div
          className="ruvor-menu"
          id={menuId}
          data-part="menu"
          hidden={!open}
          ref={menuRef}
        >
          <div className="ruvor-menu__who">
            <p className="ruvor-menu__name" data-part="menu-nome">
              {me.name}
            </p>
            <p className="ruvor-menu__email">{me.email}</p>
          </div>
          <div className="ruvor-menu__org" data-part="menu-organizacao">
            <p className="ruvor-eyebrow">{TEXTOS["conta.menu.organizacao"]}</p>
            <p>
              {me.organization.is_personal
                ? TEXTOS["conta.menu.pessoal"]
                : me.organization.name}
            </p>
          </div>
          <ul className="ruvor-menu__list">
            <li>
              <Link
                className="ruvor-menu__item"
                to={`/conta/senha?next=${encodeURIComponent(here)}`}
                onClick={() => setOpen(false)}
              >
                <Glyph name="shield-check" />
                <span>{TEXTOS["conta.menu.senha"]}</span>
              </Link>
            </li>
            {canManageUsers(me) && (
              <li>
                <Link
                  className="ruvor-menu__item"
                  to="/organizacao/usuarios"
                  onClick={() => setOpen(false)}
                >
                  <Glyph name="buildings" />
                  <span>{TEXTOS["conta.menu.usuarios"]}</span>
                </Link>
              </li>
            )}
            <li className="ruvor-menu__sep" role="presentation" />
            <li>
              <button
                className="ruvor-menu__item"
                type="button"
                data-part="menu-sair"
                onClick={() => void signOut()}
              >
                <Glyph name="sign-out" />
                <span>{TEXTOS["conta.menu.sair"]}</span>
              </button>
            </li>
          </ul>
          {failed && (
            <p className="ruvor-menu__error" role="alert">
              {TEXTOS["conta.menu.sairFalhou"]}
            </p>
          )}
        </div>
      </>
    );
  }

  return (
    <div className="ruvor-topbar__account" data-account={session.status} ref={slotRef}>
      {content}
    </div>
  );
}
