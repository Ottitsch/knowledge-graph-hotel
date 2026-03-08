import { useApi } from '../hooks/useApi'

function Stat({ label, value, hint }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
      {hint ? <div className="mt-1 text-xs text-white/45">{hint}</div> : null}
    </div>
  )
}

export default function QualitySummary() {
  const { data, error, isLoading } = useApi('/api/quality-summary')

  if (isLoading) {
    return <div className="text-sm text-white/50">Loading quality summary...</div>
  }

  if (error || !data) {
    return <div className="text-sm text-red-200/80">Quality summary unavailable.</div>
  }

  const totals = data.totals || {}
  const strongMatches = (data.listing_matches || []).find((row) => row.confidence === 'high')
  const mediumMatches = (data.listing_matches || []).find((row) => row.confidence === 'medium')
  const unlinked = (data.listing_matches || []).find((row) => row.confidence === 'unlinked')
  const lowOperator = (data.operator_confidence || []).find((row) => row.confidence === 'low')
  const overlap = data.source_overlap || {}
  const overlapPct = overlap.establishments
    ? `${((100 * overlap.multi_source_establishments) / overlap.establishments).toFixed(1)}%`
    : '0.0%'

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Stat label="Rows" value={totals.total || 0} hint={`${totals.listings || 0} listings`} />
        <Stat
          label="Strong Listing Links"
          value={(strongMatches?.count || 0) + (mediumMatches?.count || 0)}
          hint={`${strongMatches?.count || 0} high / ${mediumMatches?.count || 0} medium`}
        />
        <Stat
          label="Multi-source Establishments"
          value={overlap.multi_source_establishments || 0}
          hint={overlapPct}
        />
        <Stat
          label="Low-confidence Operators"
          value={lowOperator?.count || 0}
          hint="Visible provenance, not hidden fallback"
        />
      </div>

      <div className="text-xs leading-relaxed text-white/45">
        The graph distinguishes evidence-backed listing links from weak proximity-only cases.
        Unlinked listings include both genuinely isolated listings and nearby candidates that were
        intentionally kept out of the graph because the textual evidence was too weak.
        Current unlinked listing count: {unlinked?.count || 0}.
      </div>
    </div>
  )
}
