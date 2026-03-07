import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useApi } from '../../hooks/useApi'

const COLORS = [
  '#2dd4bf', '#a78bfa', '#60a5fa', '#f472b6', '#fb923c',
  '#34d399', '#818cf8', '#e879f9', '#fbbf24', '#f87171',
]

export default function TypePie() {
  const { data, isLoading, error } = useApi('/api/property-types')

  if (isLoading) return <div className="text-white/40 text-sm">Loading…</div>
  if (error) return <div className="text-red-400 text-sm">Error loading data</div>

  const top = data?.slice(0, 10) ?? []

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={top}
          dataKey="count"
          nameKey="type"
          cx="50%"
          cy="45%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={3}
        >
          {top.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: 'rgba(15,12,41,0.9)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10 }}
          labelStyle={{ color: '#f8fafc' }}
          itemStyle={{ color: '#f8fafc' }}
        />
        <Legend
          wrapperStyle={{ color: 'rgba(248,250,252,0.7)', fontSize: 11 }}
          formatter={(value) => value}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}
