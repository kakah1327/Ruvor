export default function ChipList({ items, emptyMessage }) {
  if (!items || items.length === 0) {
    return <p className="empty-state">{emptyMessage}</p>;
  }
  return (
    <ul className="chip-list">
      {items.map((item) => (
        <li className="chip" key={item}>{item}</li>
      ))}
    </ul>
  );
}
