import { useApi } from '../../hooks/useApi'
import ConfidenceBadge from './ConfidenceBadge'
import ProvenanceList from './ProvenanceList'

function StatRow({ label, value }) {
  if (value === undefined || value === null || value === '') return null
  return (
    <div className="flex items-start justify-between gap-3 border-b border-white/5 py-2 text-xs">
      <span className="text-white/40">{label}</span>
      <span className="text-right text-white/75">{String(value)}</span>
    </div>
  )
}

export default function EvidencePanel({ operatorId, unitId, link }) {
  const path = link
    ? `/api/link-evidence?listing_id=${encodeURIComponent(link.listingId)}&establishment_id=${encodeURIComponent(link.establishmentId || '')}`
    : operatorId
      ? `/api/entity-evidence?operator_id=${encodeURIComponent(operatorId)}`
      : unitId
        ? `/api/entity-evidence?unit_id=${encodeURIComponent(unitId)}`
        : null

  const { data, error, isLoading } = useApi(path)

  if (!path) {
    return (
      <div className="text-sm text-white/35">
        Select an operator or inspect a suggested link to see evidence here.
      </div>
    )
  }

  if (isLoading) {
    return <div className="text-sm text-white/45">Loading evidence...</div>
  }

  if (error || !data || data.found === false) {
    return <div className="text-sm text-red-200/80">Evidence unavailable.</div>
  }

  if (link) {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-white">{data.listing?.name || 'Listing'}</div>
            <div className="text-xs text-white/45">
              {data.target?.name ? `Candidate establishment: ${data.target.name}` : 'No target establishment'}
            </div>
          </div>
          <ConfidenceBadge value={data.status} />
        </div>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          <StatRow label="Distance" value={data.distance_m ? `${data.distance_m} m` : ''} />
          <StatRow label="Linked confidence" value={data.linked_confidence} />
        </div>
        <StatRow label="Linked evidence" value={data.linked_evidence} />
        <StatRow label="Candidate evidence" value={data.candidate_evidence} />
      </div>
    )
  }

  if (data.kind === 'operator') {
    return (
      <div className="flex flex-col gap-4">
        <div>
          <div className="text-sm font-semibold text-white">{data.operator_name}</div>
          <div className="mt-1 text-xs text-white/45">
            {data.unit_count} unit{data.unit_count !== 1 ? 's' : ''} in this graph
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {Object.entries(data.confidence_counts || {}).map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-white/70">
              <div className="flex items-center gap-2">
                <ConfidenceBadge value={key} />
                <span>{value}</span>
              </div>
            </div>
          ))}
        </div>
        <ProvenanceList title="Districts" items={data.districts || []} />
        <ProvenanceList title="Chains" items={data.chains || []} />
        <div className="flex flex-col gap-2">
          <div className="text-[10px] uppercase tracking-[0.22em] text-white/45">Rule facts</div>
          {(data.rule_facts || []).length === 0 ? (
            <div className="text-xs text-white/45">No inferred facts for this operator.</div>
          ) : (
            data.rule_facts.map((fact) => (
              <div key={fact.fact_id} className="rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-white/70">
                <div className="font-medium text-white">{fact.inferred_type}</div>
                <div className="mt-1 text-white/45">{fact.description}</div>
              </div>
            ))
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="text-sm font-semibold text-white">{data.entity?.name || data.entity?.canonical_id}</div>
        <div className="mt-1 flex items-center gap-2 text-xs text-white/45">
          <span>{data.entity?.granularity}</span>
          <ConfidenceBadge value={data.entity?.operator_identity_confidence} />
        </div>
      </div>
      <ProvenanceList title="Sources" items={data.sources || []} />
      <ProvenanceList title="Source record ids" items={data.source_record_ids || []} />
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
        <StatRow label="Operator" value={data.entity?.operator_name} />
        <StatRow label="Operator source" value={data.entity?.operator_name_source} />
        <StatRow label="Merge confidence" value={data.entity?.merge_confidence} />
        <StatRow label="Linked establishment confidence" value={data.entity?.linked_establishment_confidence} />
      </div>
    </div>
  )
}
