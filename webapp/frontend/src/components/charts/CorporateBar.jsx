import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useApi } from '../../hooks/useApi'

export default function CorporateBar() {
  const { data, isLoading, error } = useApi('/api/corporate-vs-individual')

  if (isLoading) return <div className="text-white/40 text-sm">Loading…</div>
  if (error) return <div className="text-red-400 text-sm">Error loading data</div>

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ left: 8, right: 16, top: 4, bottom: 60 }}>
        <XAxis
          dataKey="district"
          tick={{ fill: 'rgba(248,250,252,0.6)', fontSize: 10 }}
          angle={-35}
          textAnchor="end"
          axisLine={false}
          tickLine={false}
        />
        <YAxis tick={{ fill: 'rgba(248,250,252,0.5)', fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: 'rgba(15,12,41,0.9)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10 }}
          labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
        />
        <Legend wrapperStyle={{ color: 'rgba(248,250,252,0.7)', fontSize: 12, paddingTop: 8 }} />
        <Bar dataKey="multi_listing" stackId="a" fill="rgba(45,212,191,0.85)" radius={[0, 0, 0, 0]} name="Multi-listing" />
        <Bar dataKey="single_property" stackId="a" fill="rgba(167,139,250,0.85)" radius={[6, 6, 0, 0]} name="Single-property" />
      </BarChart>
    </ResponsiveContainer>
  )
}
