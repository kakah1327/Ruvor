import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { downloadCsvUrl, downloadJsonUrl, getResult } from '../api/client';
import Card from '../components/Card';
import ResultsTable from '../components/ResultsTable';
import Skeleton from '../components/Skeleton';

export default function ResultDetail() {
  const { runId } = useParams();
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setPayload(null);
    setError(null);
    getResult(runId).then(setPayload).catch((err) => setError(err.message));
  }, [runId]);

  if (error) {
    return <p className="empty-state">Não foi possível carregar o experimento #{runId}: {error}</p>;
  }

  if (!payload) {
    return (
      <Card>
        <Skeleton width="60%" height="1.6rem" />
        <div style={{ marginTop: '0.75rem' }}><Skeleton width="40%" height="1rem" /></div>
        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.6rem' }}>
          <Skeleton width="8rem" height="2.4rem" />
          <Skeleton width="8rem" height="2.4rem" />
        </div>
        <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <Skeleton height="2rem" />
          <Skeleton height="2rem" />
        </div>
      </Card>
    );
  }

  const { config, ranking } = payload;

  return (
    <>
      <Card>
        <h2>Experimento #{runId} — {config.ticker}</h2>
        <p className="meta">
          Período: {config.start} a {config.end} &middot; alphas={config.alphas.join(', ')} &middot; horizonte={config.horizon}
        </p>

        <div className="actions">
          <a className="btn btn-primary" href={downloadCsvUrl(runId)}>&#8595; Baixar CSV</a>
          <a className="btn" href={downloadJsonUrl(runId)}>&#8595; Baixar JSON</a>
        </div>

        <h3>Ranking dos modelos</h3>
        <ResultsTable rows={ranking} />
      </Card>

      <Link className="back-link" to="/results">&larr; voltar para todos os resultados</Link>
    </>
  );
}
