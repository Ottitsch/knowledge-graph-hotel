import { useApi } from '../../hooks/useApi'

function Stat({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">{label}</div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </div>
  )
}

export default function EvolutionSummary() {
  const { data, error, isLoading } = useApi('/api/evolution/summary')

  if (isLoading) return <div className="text-sm text-white/45">Loading evolution summary...</div>
  if (error || !data) return <div className="text-sm text-red-200/80">Evolution summary unavailable.</div>
  if (data.status === 'insufficient_snapshots') {
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
            The latest two snapshots are currently identical, so the evolution diff is empty.
            This usually happens when snapshots were created back-to-back without a real data or pipeline change between them.
          </div>
        )}
      </div>
    </div>
  )
}
