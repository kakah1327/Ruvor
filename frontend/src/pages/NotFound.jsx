import { Link } from 'react-router-dom';
import Card from '../components/Card';

export default function NotFound() {
  return (
    <Card>
      <h2>404 — página não encontrada</h2>
      <p className="meta">Essa rota não existe no VaR Lab.</p>
      <p style={{ marginTop: '1rem' }}>
        <Link to="/">&larr; voltar para o dashboard</Link>
      </p>
    </Card>
  );
}
