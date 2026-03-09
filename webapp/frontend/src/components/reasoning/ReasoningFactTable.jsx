export default function ReasoningFactTable({ facts = [] }) {
  if (!facts.length) {
    return <div className="text-sm text-white/35">No inferred facts available yet.</div>
  }

  return (
    <div className="flex flex-col gap-2">
      {facts.map((fact) => (
        <div key={fact.fact_id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-medium text-white">{fact.entity_label}</div>
              <div className="mt-1 text-xs text-white/45">{fact.inferred_type}</div>
            </div>
            <span className="text-[10px] uppercase tracking-[0.2em] text-teal-300/80">
              {fact.rule_label}
            </span>
          </div>
          <div className="mt-2 text-xs leading-relaxed text-white/55">{fact.description}</div>
        </div>
      ))}
    </div>
  )
}
