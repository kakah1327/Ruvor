import { useEffect, useState } from "react";
import {
  createBrowserRouter,
  type RouteObject,
  RouterProvider,
  useNavigate,
  useParams,
} from "react-router";

import { Shell } from "./components/Shell";
import { AssetScreen } from "./screens/AssetScreen";
import { NotFoundScreen } from "./screens/NotFoundScreen";
import { PasswordScreen } from "./screens/PasswordScreen";
import { SearchScreen } from "./screens/SearchScreen";
import { SignInScreen } from "./screens/SignInScreen";
import { SignUpScreen } from "./screens/SignUpScreen";
import { SessionProvider } from "./session/SessionProvider";

/**
 * A rota do ativo (RF-01): o ticker em minúsculas é aceito, e o endereço passa a mostrar
 * maiúsculas **sem entrada nova no histórico** — `replace`, não `push`. A tela só monta com
 * o código já em maiúsculas, e a chave pelo código a remonta do zero ao trocar de ativo.
 */
function AssetRoute() {
  const { ticker = "" } = useParams();
  const navigate = useNavigate();
  const upper = ticker.toUpperCase();

  useEffect(() => {
    if (ticker !== upper) {
      void navigate(`/ativos/${encodeURIComponent(upper)}`, { replace: true });
    }
  }, [navigate, ticker, upper]);

  return ticker === upper ? <AssetScreen key={upper} ticker={upper} /> : null;
}

/**
 * As rotas (RF-01): a busca, o ativo e o resto, que é "página não encontrada", no casco. Na
 * raiz, a rota de layout do estado de sessão (M2.1b, RF-03), pai do casco e das telas fora
 * dele: quem monta `routes` recebe o provedor. A entrada e o cadastro (`/entrar`, `/cadastro`,
 * RF-04) ficam fora do casco, em tela cheia; vêm depois dele na lista, e o roteador os escolhe
 * pela especificidade — o caminho fixo ganha do `*` —, não pela ordem. A troca voluntária da
 * senha (`/conta/senha`) fica no casco; a obrigatória não tem rota (RF-05).
 */
export const routes: RouteObject[] = [
  {
    element: <SessionProvider />,
    children: [
      {
        element: <Shell />,
        children: [
          { index: true, element: <SearchScreen /> },
          { path: "ativos/:ticker", element: <AssetRoute /> },
          { path: "conta/senha", element: <PasswordScreen mode="voluntary" /> },
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
