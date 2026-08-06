import { useEffect, useState } from 'react';
import { getConfig, getModels } from '../api/client';
import Card from '../components/Card';
import ChipList from '../components/Chip';
import Skeleton from '../components/Skeleton';

export default function Dashboard() {
  const [tickers, setTickers] = useState(null);
  const [models, setModels] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([getConfig(), getModels()])
      .then(([config, modelList]) => {
        setTickers(config.tickers);
        setModels(modelList);
      })
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return <p className="empty-state">Não foi possível carregar a API: {error}</p>;
  }

  return (
    <>
      <Card title="Ativos disponíveis">
        {tickers === null ? (
          <Skeleton height="1.8rem" width="14rem" />
        ) : (
          <ChipList items={tickers} emptyMessage="Nenhum ativo configurado." />
        )}
      </Card>

      <Card title="Modelos registrados">
        {models === null ? (
          <Skeleton height="1.8rem" width="10rem" />
        ) : (
          <ChipList
            items={models}
            emptyMessage={
              'Nenhum modelo registrado ainda — implemente as Etapas 1-3 do cronograma ' +
              '(varlab/models/traditional, garch, ml) para que apareçam aqui automaticamente.'
            }
          />
        )}
      </Card>
    </>
  );
}
