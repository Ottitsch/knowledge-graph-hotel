export default function SnapshotSelector({
  snapshots,
  previousSnapshot,
  currentSnapshot,
  onPreviousChange,
  onCurrentChange,
  isLoading,
  error,
}) {
  if (isLoading) return <div className="text-sm text-white/45">Loading snapshots...</div>
  if (error) return <div className="text-sm text-red-200/80">Snapshot list unavailable.</div>
  if (!snapshots.length) {
    return <div className="text-sm text-white/45">No snapshots available yet.</div>
  }

  const previousIndex = snapshots.indexOf(previousSnapshot)
  const currentIndex = snapshots.indexOf(currentSnapshot)

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <label className="flex flex-col gap-2">
        <span className="text-[10px] uppercase tracking-[0.22em] text-white/45">Previous snapshot</span>
        <select
          value={previousSnapshot}
          onChange={(event) => onPreviousChange(event.target.value)}
          className="rounded-2xl border border-white/10 bg-white px-4 py-3 text-sm text-black outline-none transition focus:border-[#2dd4bf]/60"
        >
          {snapshots.map((snapshot, index) => (
            <option
              key={snapshot}
              value={snapshot}
              disabled={currentIndex !== -1 && index >= currentIndex}
            >
              {snapshot}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-2">
        <span className="text-[10px] uppercase tracking-[0.22em] text-white/45">Current snapshot</span>
        <select
          value={currentSnapshot}
          onChange={(event) => onCurrentChange(event.target.value)}
          className="rounded-2xl border border-white/10 bg-white px-4 py-3 text-sm text-black outline-none transition focus:border-[#2dd4bf]/60"
        >
          {snapshots.map((snapshot, index) => (
            <option
              key={snapshot}
              value={snapshot}
              disabled={previousIndex !== -1 && index <= previousIndex}
            >
              {snapshot}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
