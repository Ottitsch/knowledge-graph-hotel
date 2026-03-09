export default function ProvenanceList({ title, items = [] }) {
  if (!items || items.length === 0) return null
  return (
    <div className="flex flex-col gap-2">
      <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">{title}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className="rounded-full border border-white/10 bg-white/5 px-2 py-1 text-[11px] text-white/65"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}
