function Stat({ label, value, hint }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
      {hint ? <div className="mt-1 text-xs text-white/45">{hint}</div> : null}
    </div>
  )
}

export default function EmbeddingSummary({ summary }) {
  const metrics = summary?.embeddings || {}
  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <Stat label="Rule Facts" value={summary?.rules?.fact_count || 0} hint={`${summary?.rules?.rule_count || 0} rules`} />
      <Stat label="Candidate Links" value={summary?.candidate_count || 0} hint={`${summary?.strong_review_count || 0} strong review`} />
      <Stat label="Embedding Model" value={metrics.model || 'n/a'} hint={`${metrics.embedding_dim || 0} dimensions`} />
      <Stat label="Training Epochs" value={metrics.epochs || 0} hint={`${metrics.triple_count || 0} triples`} />
    </div>
  )
}
