// Contador global de requisicoes em voo, para o LoadingBar poder reagir a qualquer
// chamada feita via api/client.js sem cada pagina precisar gerenciar isso na mao.
let count = 0;
const listeners = new Set();

function notify() {
  const active = count > 0;
  listeners.forEach((fn) => fn(active));
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function beginRequest() {
  count += 1;
  notify();
}

export function endRequest() {
  count = Math.max(0, count - 1);
  notify();
}
