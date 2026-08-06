import { useSyncExternalStore } from 'react';
import { subscribe } from '../api/apiStatusStore';

let currentlyOffline = false;

function subscribeAndTrack(onStoreChange) {
  return subscribe((value) => {
    currentlyOffline = value;
    onStoreChange();
  });
}

export default function ApiOfflineBanner() {
  const offline = useSyncExternalStore(subscribeAndTrack, () => currentlyOffline);

  if (!offline) return null;

  return (
    <div className="api-offline-banner" role="alert">
      ⚠ não foi possível falar com a API — verifique se o Flask (<code>varlab web</code>) está rodando
    </div>
  );
}
