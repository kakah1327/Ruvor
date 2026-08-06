import { NavLink, Outlet, useLocation } from 'react-router-dom';
import ApiOfflineBanner from './ApiOfflineBanner';
import ErrorBoundary from './ErrorBoundary';
import LoadingBar from './LoadingBar';
import ThemeToggle from './ThemeToggle';

export default function Layout() {
  const location = useLocation();

  return (
    <>
      <LoadingBar />
      <ApiOfflineBanner />

      <header className="topbar">
        <div className="topbar-inner">
          <NavLink className="brand" to="/">
            <span className="brand-mark">VaR</span>Lab
          </NavLink>
          <nav>
            <NavLink to="/" end>Dashboard</NavLink>
            <NavLink to="/results">Resultados</NavLink>
            <ThemeToggle />
          </nav>
        </div>
        <div className="topbar-tagline">
          Plataforma de Modelagem e Backtesting de VaR com Machine Learning
        </div>
      </header>

      <main className="container">
        <div key={location.pathname} className="page-transition">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </div>
      </main>

      <footer>
        <p>VaR Lab &middot; TCC II &middot; Faculdade Impacta Tecnologia</p>
      </footer>
    </>
  );
}
