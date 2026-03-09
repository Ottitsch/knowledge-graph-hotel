export default function QueryResultTable({ rows = [] }) {
  if (!rows.length) {
    return <div className="text-sm text-white/35">No rows returned.</div>
  }

  const columns = Object.keys(rows[0])
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-xs text-white/70">
        <thead className="text-[10px] uppercase tracking-[0.2em] text-white/35">
          <tr>
            {columns.map((column) => (
              <th key={column} className="pb-3 pr-4">{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-t border-white/5">
              {columns.map((column) => (
                <td key={column} className="py-3 pr-4">{Array.isArray(row[column]) ? row[column].join(', ') : String(row[column] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
