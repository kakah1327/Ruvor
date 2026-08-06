import { useEffect, useState } from 'react';

const STORAGE_KEY = 'varlab-theme';

function readStoredTheme() {
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === 'light' || stored === 'dark' ? stored : null;
}

export default function ThemeToggle() {
  // null = segue o tema do sistema operacional; 'light'/'dark' = escolha manual do usuario
  const [override, setOverride] = useState(readStoredTheme);

  useEffect(() => {
    if (override) {
      document.documentElement.dataset.theme = override;
      localStorage.setItem(STORAGE_KEY, override);
    } else {
      delete document.documentElement.dataset.theme;
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [override]);

  const systemPrefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
  const effective = override ?? (systemPrefersLight ? 'light' : 'dark');

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setOverride(effective === 'light' ? 'dark' : 'light')}
      aria-label="Alternar tema claro/escuro"
      title={effective === 'light' ? 'Mudar para escuro' : 'Mudar para claro'}
    >
      {effective === 'light' ? '☾' : '☀'}
    </button>
  );
}
