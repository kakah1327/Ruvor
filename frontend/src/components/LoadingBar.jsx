import { useSyncExternalStore } from 'react';
import { subscribe } from '../api/loadingStore';

let currentlyActive = false;

function subscribeAndTrack(onStoreChange) {
  return subscribe((value) => {
    currentlyActive = value;
    onStoreChange();
  });
}

export default function LoadingBar() {
  const active = useSyncExternalStore(subscribeAndTrack, () => currentlyActive);

  if (!active) return null;

  return (
    <div className="loading-bar" role="status" aria-label="Carregando">
      <div className="loading-bar-fill" />
    </div>
  );
}
