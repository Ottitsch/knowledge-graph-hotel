import { useApi } from '../../hooks/useApi'
import CandidateRankingTable from './CandidateRankingTable'
import EmbeddingSummary from './EmbeddingSummary'
import ReasoningFactTable from './ReasoningFactTable'
import ReasoningLegend from './ReasoningLegend'
import SimilarOperators from './SimilarOperators'

export default function ReasoningLab({ selectedOperatorId, selectedOperatorName, onInspectLink }) {
  const { data: summary, isLoading, error } = useApi('/api/reasoning/summary')
  const { data: facts } = useApi('/api/reasoning/facts?limit=8')
  const { data: candidates } = useApi('/api/embeddings/candidates?limit=10')
  const similarityPath = selectedOperatorId
    ? `/api/embeddings/similar-operators?operator_id=${encodeURIComponent(selectedOperatorId)}&limit=6`
    : '/api/embeddings/similar-operators?limit=4'
  const { data: similarity } = useApi(similarityPath)

  if (isLoading) {
    return <div className="text-sm text-white/45">Loading reasoning outputs...</div>
  }

  if (error || !summary) {
    return <div className="text-sm text-red-200/80">Reasoning outputs unavailable.</div>
  }

  return (
    <div className="flex flex-col gap-5">
      <EmbeddingSummary summary={summary} />
      <ReasoningLegend />

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <div className="flex flex-col gap-3">
          <div className="text-sm font-semibold text-white">Rule-derived facts</div>
          <ReasoningFactTable facts={facts || []} />
        </div>
        <div className="flex flex-col gap-3">
          <div className="text-sm font-semibold text-white">Operator similarity</div>
          <SimilarOperators payload={similarity} selectedOperatorName={selectedOperatorName} />
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div className="text-sm font-semibold text-white">Embedding-ranked candidate links</div>
        <CandidateRankingTable rows={candidates || []} onInspect={onInspectLink} />
      </div>
    </div>
  )
}
