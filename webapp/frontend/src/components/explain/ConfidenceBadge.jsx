const COLOR_BY_VALUE = {
  high: 'rgba(34,197,94,0.18)',
  medium: 'rgba(245,158,11,0.18)',
  low: 'rgba(248,113,113,0.18)',
  asserted: 'rgba(45,212,191,0.18)',
  candidate_only: 'rgba(250,204,21,0.18)',
  none: 'rgba(148,163,184,0.18)',
}

const BORDER_BY_VALUE = {
  high: 'rgba(34,197,94,0.35)',
  medium: 'rgba(245,158,11,0.35)',
  low: 'rgba(248,113,113,0.35)',
  asserted: 'rgba(45,212,191,0.35)',
  candidate_only: 'rgba(250,204,21,0.35)',
  none: 'rgba(148,163,184,0.35)',
}

export default function ConfidenceBadge({ value }) {
  if (!value) return null
  return (
    <span
      className="inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] text-white/80"
      style={{
        background: COLOR_BY_VALUE[value] ?? 'rgba(148,163,184,0.18)',
        borderColor: BORDER_BY_VALUE[value] ?? 'rgba(148,163,184,0.35)',
      }}
    >
      {value.replaceAll('_', ' ')}
    </span>
  )
}
