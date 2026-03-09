import { useApi } from '../../hooks/useApi'

function Stat({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </div>
  )
}

function buildEvolutionPath(basePath, previousSnapshot, currentSnapshot) {
  const params = new URLSearchParams()
  if (previousSnapshot) params.set('previous', previousSnapshot)
  if (currentSnapshot) params.set('current', currentSnapshot)
  const query = params.toString()
  return query ? `${basePath}?${query}` : basePath
}

export default function EvolutionSummary({ previousSnapshot, currentSnapshot }) {
  const path = buildEvolutionPath('/api/evolution/summary', previousSnapshot, currentSnapshot)
  const { data, error, isLoading } = useApi(path)

  if (isLoading) return <div className="text-sm text-white/45">Loading evolution summary...</div>
  if (error || !data) return <div className="text-sm text-red-200/80">Evolution summary unavailable.</div>
  if (data.status === 'insufficient_snapshots' || data.status === 'invalid_snapshot' || data.status === 'invalid_order') {
    return <div className="text-sm text-white/45">{data.message}</div>
  }

  const isZeroDiff = (
    (data.added_units || 0) === 0 &&
    (data.removed_units || 0) === 0 &&
    (data.listing_links_added || 0) === 0 &&
    (data.listing_links_removed || 0) === 0 &&
    (data.operator_labels_changed || 0) === 0 &&
    (data.rule_fact_delta || 0) === 0 &&
    (data.linked_listing_delta || 0) === 0
  )

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Stat label="Added Units" value={data.added_units || 0} />
        <Stat label="Removed Units" value={data.removed_units || 0} />
        <Stat label="Links Added" value={data.listing_links_added || 0} />
        <Stat label="Rule Delta" value={data.rule_fact_delta || 0} />
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">Compared snapshots</div>
        <div className="mt-2 text-xs leading-relaxed text-white/60">
          <span className="font-medium text-white/80">{data.previous_snapshot || 'n/a'}</span>
          {' -> '}
          <span className="font-medium text-white/80">{data.current_snapshot || 'n/a'}</span>
        </div>
        {isZeroDiff && (
          <div className="mt-3 text-xs leading-relaxed text-white/45">
            The selected snapshots currently produce an empty evolution diff.
            Choose a wider time gap or compare two runs with different matching or reasoning settings.
          </div>
        )}
      </div>
    </div>
  )
}
