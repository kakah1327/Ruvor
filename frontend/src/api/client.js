import { markOffline, markOnline } from './apiStatusStore';
import { beginRequest, endRequest } from './loadingStore';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

async function getJSON(path) {
  beginRequest();
  try {
    let res;
    try {
      res = await fetch(`${BASE_URL}${path}`);
    } catch (networkError) {
      // fetch so rejeita por falha de rede/CORS/servidor inalcancavel — nunca por
      // causa de um status HTTP de erro, que cai no bloco abaixo em vez deste.
      markOffline();
      throw new Error(`Não foi possível falar com a API (${BASE_URL || 'origem atual'})`);
    }
    markOnline();
    if (!res.ok) {
      throw new Error(`${path} respondeu ${res.status}`);
    }
    return await res.json();
  } finally {
    endRequest();
  }
}

export const getConfig = () => getJSON('/api/config');
export const getModels = () => getJSON('/api/models');
export const getBacktests = () => getJSON('/api/backtests');
export const getResults = () => getJSON('/api/results');
export const getResult = (runId) => getJSON(`/api/results/${runId}`);

export const downloadCsvUrl = (runId) => `${BASE_URL}/api/results/${runId}/download.csv`;
export const downloadJsonUrl = (runId) => `${BASE_URL}/api/results/${runId}/download.json`;
