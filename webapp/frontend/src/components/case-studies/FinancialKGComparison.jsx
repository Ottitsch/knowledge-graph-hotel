import { useApi } from '../../hooks/useApi'

export default function FinancialKGComparison() {
  const { data, error, isLoading } = useApi('/api/financial-kg-comparison')

  if (isLoading) return <div className="text-sm text-white/45">Loading comparison...</div>
  if (error || !data) return <div className="text-sm text-red-200/80">Comparison unavailable.</div>

  const lines = (data.markdown || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .filter((line) => !line.startsWith('#'))

  return (
    <div className="flex flex-col gap-3">
      {lines.map((line, index) => (
        <div key={index} className="text-xs leading-relaxed text-white/50">
          {line.startsWith('- ') ? line.slice(2) : line}
        </div>
      ))}
    </div>
  )
}
