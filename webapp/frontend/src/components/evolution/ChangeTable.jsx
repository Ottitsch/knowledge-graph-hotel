import { useApi } from '../../hooks/useApi'

function buildEvolutionPath(basePath, previousSnapshot, currentSnapshot) {
  const params = new URLSearchParams()
  if (previousSnapshot) params.set('previous', previousSnapshot)
  if (currentSnapshot) params.set('current', currentSnapshot)
  const query = params.toString()
  return query ? `${basePath}?${query}` : basePath
}

export default function ChangeTable({ previousSnapshot, currentSnapshot }) {
  const path = buildEvolutionPath('/api/evolution/changes', previousSnapshot, currentSnapshot)
  const { data, error, isLoading } = useApi(path)

  if (isLoading) return <div className="text-sm text-white/45">Loading change table...</div>
  if (error || !data) return <div className="text-sm text-red-200/80">Change data unavailable.</div>
  if (
    data.summary?.status === 'insufficient_snapshots' ||
    data.summary?.status === 'invalid_snapshot' ||
    data.summary?.status === 'invalid_order'
  ) {
    return <div className="text-sm text-white/45">{data.summary?.message || 'Snapshot comparison unavailable.'}</div>
  }

  const changes = data.operator_labels_changed || []
  const addedUnits = data.added_units || []
  const removedUnits = data.removed_units || []
  const addedLinks = data.listing_links_added || []
  const removedLinks = data.listing_links_removed || []
  const noVisibleChanges = (
    changes.length === 0 &&
    addedUnits.length === 0 &&
    removedUnits.length === 0 &&
    addedLinks.length === 0 &&
    removedLinks.length === 0
  )

  return (
    <div className="flex flex-col gap-3">
      <div className="text-sm font-semibold text-white">Recent operator label changes</div>
      {changes.length === 0 ? (
        <div className="text-sm text-white/35">No operator label changes detected in the latest diff.</div>
      ) : (
        changes.map((change) => (
          <div key={change.snapshot_key || change.canonical_id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
            <div className="text-sm font-medium text-white">{change.unit_name}</div>
            <div className="mt-1 text-xs text-white/45">
              {change.previous_operator || 'None'} {'->'} {change.current_operator || 'None'}
            </div>
          </div>
        ))
      )}
      <div className="mt-2 grid grid-cols-1 gap-3 xl:grid-cols-2">
        <ChangeList title="Added units" items={addedUnits} emptyText="No added units." />
        <ChangeList title="Removed units" items={removedUnits} emptyText="No removed units." />
        <LinkChangeList title="Listing links added" items={addedLinks} emptyText="No listing links added." />
        <LinkChangeList title="Listing links removed" items={removedLinks} emptyText="No listing links removed." />
      </div>
      {noVisibleChanges && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-relaxed text-white/45">
          There are currently no added units, removed units, added listing links, removed listing links, or operator-label changes between the selected snapshots.
          Choose a different snapshot pair if you want to inspect a larger change window.
        </div>
      )}
    </div>
  )
}

function ChangeList({ title, items, emptyText }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">{title}</div>
      {items.length === 0 ? (
        <div className="mt-2 text-xs text-white/35">{emptyText}</div>
      ) : (
        <div className="mt-2 flex flex-col gap-2">
          {items.slice(0, 6).map((item) => (
            <div key={item} className="break-all rounded-xl bg-black/15 px-3 py-2 text-xs text-white/65">
              {item}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function LinkChangeList({ title, items, emptyText }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-white/45">{title}</div>
      {items.length === 0 ? (
        <div className="mt-2 text-xs text-white/35">{emptyText}</div>
      ) : (
        <div className="mt-2 flex flex-col gap-2">
          {items.slice(0, 6).map((item) => (
            <div key={`${item.snapshot_key}-${item.linked_establishment_key}`} className="rounded-xl bg-black/15 px-3 py-2 text-xs text-white/65">
              <div className="break-all">{item.snapshot_key}</div>
              <div className="mt-1 break-all text-white/35">{'->'} {item.linked_establishment_key}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
