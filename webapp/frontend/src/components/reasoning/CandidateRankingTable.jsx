export default function CandidateRankingTable({ rows = [], onInspect }) {
  if (!rows.length) {
    return <div className="text-sm text-white/35">No embedding-scored candidates available yet.</div>
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-xs text-white/70">
        <thead className="text-[10px] uppercase tracking-[0.2em] text-white/35">
          <tr>
            <th className="pb-3 pr-4">Listing</th>
            <th className="pb-3 pr-4">Candidate</th>
            <th className="pb-3 pr-4">Distance</th>
            <th className="pb-3 pr-4">Score</th>
            <th className="pb-3 pr-4">Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.canonical_id} className="border-t border-white/5">
              <td className="py-3 pr-4">
                <div className="font-medium text-white">{row.name}</div>
                <div className="text-white/40">{row.operator_name || 'Unknown operator'}</div>
              </td>
              <td className="py-3 pr-4">{row.candidate_establishment_id}</td>
              <td className="py-3 pr-4">{row.candidate_establishment_distance_m || '-'} m</td>
              <td className="py-3 pr-4">
                {row.embedding_score ? Number(row.embedding_score).toFixed(3) : '-'}
              </td>
              <td className="py-3 pr-4">
                <button
                  onClick={() => onInspect?.(row)}
                  className="rounded-lg border border-teal-500/20 bg-teal-500/10 px-3 py-1 text-[11px] font-medium text-teal-300 transition hover:bg-teal-500/15"
                >
                  Inspect evidence
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
