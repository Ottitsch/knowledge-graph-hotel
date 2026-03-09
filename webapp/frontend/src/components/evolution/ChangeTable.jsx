import { useApi } from '../../hooks/useApi'

export default function ChangeTable() {
  const { data, error, isLoading } = useApi('/api/evolution/changes')

  if (isLoading) return <div className="text-sm text-white/45">Loading change table...</div>
  if (error || !data) return <div className="text-sm text-red-200/80">Change data unavailable.</div>
  if (data.summary?.status === 'insufficient_snapshots') {
    return <div className="text-sm text-white/45">Run the pipeline twice to see snapshot changes here.</div>
  }

  const changes = data.operator_labels_changed || []
  const noVisibleChanges = (
    changes.length === 0 &&
    (data.added_units || []).length === 0 &&
    (data.removed_units || []).length === 0 &&
    (data.listing_links_added || []).length === 0 &&
    (data.listing_links_removed || []).length === 0
  )

  return (
    <div className="flex flex-col gap-3">
      <div className="text-sm font-semibold text-white">Recent operator label changes</div>
      {changes.length === 0 ? (
        <div className="text-sm text-white/35">No operator label changes detected in the latest diff.</div>
      ) : (
        changes.map((change) => (
          <div key={change.canonical_id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="text-sm font-medium text-white">{change.unit_name}</div>
            <div className="mt-1 text-xs text-white/45">
              {change.previous_operator || 'None'} {'->'} {change.current_operator || 'None'}
            </div>
          </div>
        ))
      )}
      {noVisibleChanges && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-relaxed text-white/45">
          There are currently no added units, removed units, added listing links, removed listing links, or operator-label changes between the latest two snapshots.
          Run the pipeline again after a real data change or after adjusting the matching logic to produce a more informative evolution view.
        </div>
      )}
    </div>
  )
}
