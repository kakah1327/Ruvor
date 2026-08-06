// Rastreia se a ultima tentativa de falar com a API falhou por causa de rede (fetch
// rejeitado: servidor fora do ar, CORS, DNS etc.) — nao confundir com um 404/500 HTTP,
// que e uma resposta valida da API e nao significa "API offline".
let offline = false;
const listeners = new Set();

function notify() {
  listeners.forEach((fn) => fn(offline));
}

export function subscribe(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function markOnline() {
  if (offline) {
    offline = false;
    notify();
  }
}

export function markOffline() {
  if (!offline) {
    offline = true;
    notify();
  }
}
