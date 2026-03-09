import ConfidenceBadge from '../explain/ConfidenceBadge'

export default function ReasoningLegend() {
  return (
    <div className="flex flex-wrap gap-2 text-xs text-white/55">
      <div className="flex items-center gap-2">
        <ConfidenceBadge value="asserted" />
        <span>asserted fact</span>
      </div>
      <div className="flex items-center gap-2">
        <ConfidenceBadge value="candidate_only" />
        <span>candidate link</span>
      </div>
      <div className="flex items-center gap-2">
        <ConfidenceBadge value="high" />
        <span>strong operator evidence</span>
      </div>
      <div className="flex items-center gap-2">
        <ConfidenceBadge value="low" />
        <span>fallback operator evidence</span>
      </div>
    </div>
  )
}
