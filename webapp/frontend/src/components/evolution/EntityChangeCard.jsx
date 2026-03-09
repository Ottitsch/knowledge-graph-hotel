import { useApi } from '../../hooks/useApi'

export default function EntityChangeCard({ entityId }) {
  const path = entityId ? `/api/evolution/entity?id=${encodeURIComponent(entityId)}` : null
  const { data, error, isLoading } = useApi(path)

  if (!path) return <div className="text-sm text-white/35">Select a changed entity to compare snapshots.</div>
  if (isLoading) return <div className="text-sm text-white/45">Loading entity diff...</div>
  if (error || !data) return <div className="text-sm text-red-200/80">Entity diff unavailable.</div>

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
      <div className="text-sm font-semibold text-white">Entity snapshot diff</div>
      <div className="mt-2 text-xs text-white/45">Current snapshot: {data.current_snapshot || 'n/a'}</div>
      <div className="mt-3 grid grid-cols-1 gap-3 xl:grid-cols-2">
        <div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-white/35">Previous</div>
          <pre className="mt-2 overflow-x-auto rounded-xl bg-black/20 p-3 text-[11px] text-white/65">
            {JSON.stringify(data.previous || {}, null, 2)}
          </pre>
        </div>
        <div>
          <div className="text-[10px] uppercase tracking-[0.22em] text-white/35">Current</div>
          <pre className="mt-2 overflow-x-auto rounded-xl bg-black/20 p-3 text-[11px] text-white/65">
            {JSON.stringify(data.current || {}, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
