import { useState } from 'react'
import { useApi } from '../../hooks/useApi'
import QueryExplanation from './QueryExplanation'
import QueryResultTable from './QueryResultTable'

const STARTER_QUESTIONS = [
  'Which operators manage more than 5 units in Leopoldstadt?',
  'Show chain-affiliated establishments with nearby Airbnb listings.',
  'Which operators have low-confidence identities?',
  'Show multi-source confirmed establishments.',
]

export default function QueryAssistant() {
  const { data: templates } = useApi('/api/query-templates')
  const [question, setQuestion] = useState(STARTER_QUESTIONS[0])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function runQuestion(nextQuestion) {
    const q = nextQuestion ?? question
    setLoading(true)
    try {
      const response = await fetch(`/api/query-assistant?q=${encodeURIComponent(q)}`)
      const payload = await response.json()
      setResult(payload)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
        <div className="text-sm font-semibold text-white">Query assistant</div>
        <div className="mt-2 text-xs leading-relaxed text-white/45">
          This assistant maps supported natural-language questions to safe Cypher templates instead of using an ungrounded chatbot.
        </div>
        <div className="mt-4 flex flex-col gap-3 xl:flex-row">
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            className="flex-1 rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none"
          />
          <button
            onClick={() => runQuestion()}
            className="rounded-xl border border-teal-500/25 bg-teal-500/10 px-4 py-3 text-sm font-medium text-teal-300 transition hover:bg-teal-500/15"
          >
            {loading ? 'Running...' : 'Run query'}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {STARTER_QUESTIONS.map((item) => (
            <button
              key={item}
              onClick={() => {
                setQuestion(item)
                runQuestion(item)
              }}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] text-white/60 transition hover:bg-white/10 hover:text-white"
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <div className="flex flex-col gap-3">
          <div className="text-sm font-semibold text-white">Supported templates</div>
          <div className="flex flex-col gap-2">
            {(templates || []).map((template) => (
              <div key={template.id} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                <div className="text-sm font-medium text-white">{template.label}</div>
                <div className="mt-1 text-xs text-white/45">{template.description}</div>
              </div>
            ))}
          </div>
        </div>
        <QueryExplanation result={result} />
      </div>

      {result && !result.matched && (
        <div className="rounded-2xl border border-amber-400/15 bg-amber-400/10 p-4 text-sm text-amber-100/85">
          {result.message}
        </div>
      )}

      {result?.matched && (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="mb-3 text-sm font-semibold text-white">
            Query results ({result.row_count})
          </div>
          <QueryResultTable rows={result.rows || []} />
        </div>
      )}
    </div>
  )
}
