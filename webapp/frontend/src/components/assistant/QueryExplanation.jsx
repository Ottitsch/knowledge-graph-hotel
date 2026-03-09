export default function QueryExplanation({ result }) {
  if (!result?.matched) return null
  return (
    <div className="flex flex-col gap-3">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">Template</div>
        <div className="mt-2 text-sm font-medium text-white">{result.label}</div>
        <div className="mt-2 text-xs leading-relaxed text-white/55">{result.explanation}</div>
      </div>
      <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
        <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">Generated Cypher</div>
        <pre className="mt-3 overflow-x-auto text-[11px] leading-relaxed text-white/70">{result.cypher}</pre>
      </div>
    </div>
  )
}
