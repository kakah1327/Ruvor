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
import { SearchScreen } from "./screens/SearchScreen";

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

/** As rotas (RF-01): a busca, o ativo e o resto, que é "página não encontrada", no casco. */
export const routes: RouteObject[] = [
  {
    element: <Shell />,
    children: [
      { index: true, element: <SearchScreen /> },
      { path: "ativos/:ticker", element: <AssetRoute /> },
      { path: "*", element: <NotFoundScreen /> },
    ],
  },
];

export function App() {
  const [router] = useState(() => createBrowserRouter(routes));
  return <RouterProvider router={router} />;
}
