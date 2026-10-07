import { useEffect, useState } from "react";
import {
  createBrowserRouter,
  type RouteObject,
  RouterProvider,
  useNavigate,
  useParams,
} from "react-router";

import { assetTabPath, tabFromSlug } from "./components/AssetTabs";
import { Shell } from "./components/Shell";
import { AssetScreen } from "./screens/AssetScreen";
import { NotFoundScreen } from "./screens/NotFoundScreen";
import { PasswordScreen } from "./screens/PasswordScreen";
import { PortfolioScreen } from "./screens/PortfolioScreen";
import { PortfoliosScreen } from "./screens/PortfoliosScreen";
import { SearchScreen } from "./screens/SearchScreen";
import { SignInScreen } from "./screens/SignInScreen";
import { SignUpScreen } from "./screens/SignUpScreen";
import { UsersScreen } from "./screens/UsersScreen";
import { SessionProvider } from "./session/SessionProvider";

/**
 * A rota do ativo (RF-01), com a aba opcional depois do código: o ticker em minúsculas é aceito, e o endereço passa a mostrar
 * maiúsculas **sem entrada nova no histórico** — `replace`, não `push`. A tela só monta com
 * o código já em maiúsculas, e a chave pelo código a remonta do zero ao trocar de ativo.
 */
function AssetRoute() {
  const { ticker = "", aba } = useParams();
  const navigate = useNavigate();
  const upper = ticker.toUpperCase();
  const tab = tabFromSlug(aba);

  // O código em minúsculas vira maiúsculas, e a aba desconhecida vira a visão geral: os dois
  // com `replace`, sem entrada nova no histórico.
  useEffect(() => {
    if (ticker !== upper || tab === null) {
      void navigate(assetTabPath(upper, tab ?? ""), { replace: true });
    }
  }, [navigate, ticker, upper, tab]);

  // A chave é só o código: trocar de aba não remonta a tela nem pede as rotas de novo.
  return ticker === upper && tab !== null ? (
    <AssetScreen key={upper} ticker={upper} tab={tab} />
  ) : null;
}

/**
 * A rota da carteira (M2.2b, RF-02): a chave pelo `id` remonta a página do zero ao trocar de
 * carteira, sem levar o estado de uma para a outra.
 */
function PortfolioRoute() {
  const { id = "" } = useParams();
  return <PortfolioScreen key={id} portfolioId={id} />;
}

/**
 * As rotas (RF-01): a busca, o ativo e o resto, que é "página não encontrada", no casco. Na
 * raiz, a rota de layout do estado de sessão (M2.1b, RF-03), pai do casco e das telas fora
 * dele: quem monta `routes` recebe o provedor. A entrada e o cadastro (`/entrar`, `/cadastro`,
 * RF-04) ficam fora do casco, em tela cheia; vêm depois dele na lista, e o roteador os escolhe
 * pela especificidade — o caminho fixo ganha do `*` —, não pela ordem. A troca voluntária da
 * senha (`/conta/senha`) fica no casco; a obrigatória não tem rota (RF-05). A gestão de
 * usuários (`/organizacao/usuarios`, RF-11) também fica no casco. As carteiras (`/carteiras`, a
 * lista e a criação — M2.2b, RF-02) também, e a página de cada uma (`/carteiras/:id`).
 */
export const routes: RouteObject[] = [
  {
    element: <SessionProvider />,
    children: [
      {
        element: <Shell />,
        children: [
          { index: true, element: <SearchScreen /> },
          { path: "ativos/:ticker/:aba?", element: <AssetRoute /> },
          { path: "conta/senha", element: <PasswordScreen mode="voluntary" /> },
          { path: "organizacao/usuarios", element: <UsersScreen /> },
          { path: "carteiras", element: <PortfoliosScreen /> },
          { path: "carteiras/:id", element: <PortfolioRoute /> },
          { path: "*", element: <NotFoundScreen /> },
        ],
      },
      { path: "entrar", element: <SignInScreen /> },
      { path: "cadastro", element: <SignUpScreen /> },
    ],
  },
];

export function App() {
  const [router] = useState(() => createBrowserRouter(routes));
  return <RouterProvider router={router} />;
}
