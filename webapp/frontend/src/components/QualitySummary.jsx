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
  const listingMatches = data.listing_matches || {}
  const linkedConfidence = listingMatches.linked_confidence || {}
  const strongLinks = linkedConfidence.high || 0
  const mediumLinks = linkedConfidence.medium || 0
  const linkedTotal = listingMatches.linked ?? (strongLinks + mediumLinks)
  const candidateOnly = listingMatches.candidate_only || 0
  const noCandidate = listingMatches.no_candidate || 0
  const unlinkedTotal = candidateOnly + noCandidate
  const operatorConfidence = data.operator_identity_confidence || {}
  const lowOperatorCount = operatorConfidence.low || 0
  const overlap = data.multi_source_establishments || {}
  const overlapPct = overlap.share_percent ? `${overlap.share_percent}%` : '0.0%'
  const totalRows = totals.rows ?? totals.total ?? 0

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Stat label="Rows" value={totalRows} hint={`${totals.listings || 0} listings`} />
        <Stat
          label="Strong Listing Links"
          value={linkedTotal}
          hint={`${strongLinks} high / ${mediumLinks} medium`}
        />
        <Stat
          label="Multi-source Establishments"
          value={overlap.rows || 0}
          hint={overlapPct}
        />
        <Stat
          label="Low-confidence Operators"
          value={lowOperatorCount}
          hint="Visible provenance, not hidden fallback"
        />
      </div>

      <div className="text-xs leading-relaxed text-white/45">
        The graph distinguishes evidence-backed listing links from weak proximity-only cases.
        Unlinked listings include both genuinely isolated listings and nearby candidates that were
        intentionally kept out of the graph because the textual evidence was too weak.
        Current unlinked listing count: {unlinkedTotal}.
      </div>
    </div>
  )
}
