import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { useApi } from '../../hooks/useApi'

export default function DistrictBar() {
  const { data, isLoading, error } = useApi('/api/districts')

  if (isLoading) return <div className="text-white/40 text-sm">Loading…</div>
  if (error) return <div className="text-red-400 text-sm">Error loading data</div>

  return (
    <ResponsiveContainer width="100%" height={280}>
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
          itemStyle={{ color: '#60a5fa' }}
        />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data?.map((_, i) => (
            <Cell key={i} fill={`rgba(96,165,250,${0.9 - i * 0.04})`} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
