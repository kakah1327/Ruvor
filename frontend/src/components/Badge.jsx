export default function Badge({ passed }) {
  return (
    <span className={`badge ${passed ? 'badge-pass' : 'badge-fail'}`}>
      {passed ? 'passou' : 'falhou'}
    </span>
  );
}
