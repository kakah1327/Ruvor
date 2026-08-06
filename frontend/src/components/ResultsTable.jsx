import Badge from './Badge';

export default function ResultsTable({ rows }) {
  if (!rows || rows.length === 0) {
    return (
      <p className="empty-state">
        Este experimento não produziu resultados (verifique erros por modelo no JSON).
      </p>
    );
  }

  const columns = Object.keys(rows[0]).sort((a, b) => {
    if (a === 'model') return -1;
    if (b === 'model') return 1;
    return 0;
  });

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col}>
                  {col.endsWith('_passed') ? (
                    <Badge passed={row[col]} />
                  ) : (
                    row[col] ?? '—'
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
