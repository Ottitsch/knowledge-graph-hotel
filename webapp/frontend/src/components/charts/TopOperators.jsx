import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LabelList } from 'recharts'
import { useApi } from '../../hooks/useApi'

const TEAL = '#2dd4bf'

export default function TopOperators({ onSelect }) {
  const { data, isLoading, error } = useApi('/api/top-operators')

  if (isLoading) return <div className="text-white/40 text-sm">Loading…</div>
  if (error) return <div className="text-red-400 text-sm">Error loading data</div>

  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16, top: 4, bottom: 4 }}>
        <XAxis type="number" tick={{ fill: 'rgba(248,250,252,0.5)', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis
          type="category"
          dataKey="operator"
          width={130}
          tick={false}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{ background: 'rgba(15,12,41,0.9)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10 }}
          labelStyle={{ color: '#f8fafc', fontWeight: 600 }}
          itemStyle={{ color: TEAL }}
        />
        <Bar dataKey="count" radius={[0, 6, 6, 0]} style={{ cursor: 'pointer' }} onClick={(d) => onSelect?.(d.operator)}>
          {data?.map((_, i) => (
            <Cell key={i} fill={`rgba(45,212,191,${0.9 - i * 0.03})`} />
          ))}
          <LabelList
            dataKey="operator"
            position="left"
            style={{ fill: 'rgba(248,250,252,0.7)', fontSize: 11, fontFamily: 'Inter,sans-serif', fontWeight: 500 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
