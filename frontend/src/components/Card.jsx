export default function Card({ title, children }) {
  return (
    <section>
      {title && <h3>{title}</h3>}
      {children}
    </section>
  );
}
