import { Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import NotFound from './pages/NotFound';
import ResultDetail from './pages/ResultDetail';
import ResultsList from './pages/ResultsList';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="results" element={<ResultsList />} />
        <Route path="results/:runId" element={<ResultDetail />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
