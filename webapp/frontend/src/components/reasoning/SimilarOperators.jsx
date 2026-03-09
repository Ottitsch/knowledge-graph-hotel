export default function SimilarOperators({ payload, selectedOperatorName }) {
  const rows = payload?.rows || []

  if (!rows.length) {
    return <div className="text-sm text-white/35">No similarity suggestions available.</div>
  }

  if (payload?.mode === 'similar_to_operator') {
    return (
      <div className="flex flex-col gap-2">
        <div className="text-xs text-white/45">
          Similar operators to <span className="font-medium text-teal-300">{selectedOperatorName || payload.operator_id}</span>
        </div>
        {rows.map((row) => (
          <div key={row.operator_id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium text-white">{row.operator_name}</div>
                <div className="mt-1 text-xs text-white/45">{row.unit_count} units</div>
              </div>
              <div className="text-xs font-semibold text-teal-300">{row.similarity}</div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {rows.map((row) => (
        <div key={row.operator_id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="text-sm font-medium text-white">{row.operator_name}</div>
          <div className="mt-1 text-xs text-white/45">{row.unit_count} units</div>
          <div className="mt-3 flex flex-col gap-2">
            {(row.similar || []).map((similar) => (
              <div key={similar.operator_id} className="flex items-center justify-between text-xs text-white/65">
                <span>{similar.operator_name}</span>
                <span className="text-teal-300">{similar.similarity}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
