import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { getResults } from '../api/client';
import Card from '../components/Card';
import Skeleton from '../components/Skeleton';
import { formatDateTime } from '../utils/formatDate';

const COLUMNS = [
  { key: 'id', label: 'ID' },
  { key: 'ticker', label: 'Ativo' },
  { key: 'created_at', label: 'Rodado em' },
];

export default function ResultsList() {
  const [runs, setRuns] = useState(null);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState('');
  const [sortKey, setSortKey] = useState('id');
  const [sortDir, setSortDir] = useState('desc');

  useEffect(() => {
    getResults().then(setRuns).catch((err) => setError(err.message));
  }, []);

  const visibleRuns = useMemo(() => {
    if (!runs) return [];
    const q = query.trim().toLowerCase();
    const filtered = q ? runs.filter((run) => run.ticker.toLowerCase().includes(q)) : runs;

    const sorted = [...filtered].sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (va < vb) return -1;
      if (va > vb) return 1;
      return 0;
    });
    if (sortDir === 'desc') sorted.reverse();
    return sorted;
  }, [runs, query, sortKey, sortDir]);

  function toggleSort(key) {
    if (key === sortKey) {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  }

  return (
    <Card>
      <h2>Resultados de experimentos</h2>
      <p className="meta">Explore os experimentos já executados e baixe os resultados de cada um.</p>

      {error && <p className="empty-state">Não foi possível carregar a API: {error}</p>}

      {runs === null && !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', marginTop: '1rem' }}>
          <Skeleton height="2.2rem" />
          <Skeleton height="2.2rem" />
        </div>
      )}

      {runs && runs.length > 0 && (
        <>
          <div className="list-toolbar">
            <input
              type="text"
              className="search-input"
              placeholder="buscar por ativo (ex: PETR4)…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <p className="meta" style={{ margin: 0 }}>
              {visibleRuns.length} de {runs.length}
            </p>
          </div>

          {visibleRuns.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    {COLUMNS.map((col) => (
                      <th key={col.key} className="sortable" onClick={() => toggleSort(col.key)}>
                        {col.label}
                        {sortKey === col.key && (
                          <span className="sort-indicator">{sortDir === 'asc' ? '▲' : '▼'}</span>
                        )}
                      </th>
                    ))}
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {visibleRuns.map((run) => (
                    <tr key={run.id}>
                      <td>#{run.id}</td>
                      <td>{run.ticker}</td>
                      <td>{formatDateTime(run.created_at)}</td>
                      <td><Link to={`/results/${run.id}`}>ver resultado &rarr;</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="empty-state">Nenhum experimento bate com "{query}".</p>
          )}
        </>
      )}

      {runs && runs.length === 0 && (
        <p className="empty-state">
          Nenhum experimento rodado ainda. Rode um com{' '}
          <code>varlab run --ticker ... --model ... --backtest ... --save</code>{' '}
          para que apareça aqui, disponível para download.
        </p>
      )}
    </Card>
  );
}
