import { useEffect, useState } from "react";
import {
  createBrowserRouter,
  type RouteObject,
  RouterProvider,
  useNavigate,
  useParams,
} from "react-router";

import { Shell } from "./components/Shell";
import { NotFoundScreen } from "./screens/NotFoundScreen";

/**
 * A rota do ativo (RF-01): o ticker em minúsculas é aceito, e o endereço passa a mostrar
 * maiúsculas **sem entrada nova no histórico** — `replace`, não `push`. A tela do ativo
 * entra aqui na T10.
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

  return null;
}

/** As rotas (RF-01): a busca, o ativo e o resto, que é "página não encontrada", no casco. */
export const routes: RouteObject[] = [
  {
    element: <Shell />,
    children: [
      // A busca entra aqui na T7.
      { index: true, element: null },
      { path: "ativos/:ticker", element: <AssetRoute /> },
      { path: "*", element: <NotFoundScreen /> },
    ],
  },
];

export function App() {
  const [router] = useState(() => createBrowserRouter(routes));
  return <RouterProvider router={router} />;
}
