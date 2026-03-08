import { useRef, useCallback, useState, useEffect } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useApi } from '../../hooks/useApi'

const NODE_COLORS = {
  operator: '#2dd4bf',
  chain: '#a78bfa',
  district: '#60a5fa',
}

const FILTERS = [
  { label: 'All', value: 1 },
  { label: '2+', value: 2 },
  { label: '4+', value: 4 },
  { label: '10+', value: 10 },
]

export default function ForceGraph({ width = 500, height = 400, onOperatorClick }) {
  const [minUnits, setMinUnits] = useState(1)
  const { data, isLoading, error } = useApi(`/api/graph?min_units=${minUnits}`)
  const fgRef = useRef()
  const [selectedId, setSelectedId] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)

  useEffect(() => {
    if (!data?.nodes?.length || !fgRef.current) return
    const timer = setTimeout(() => {
      try {
        fgRef.current.zoomToFit(500, 40)
      } catch {
        // Ignore fit errors during early mount/layout churn.
      }
    }, 250)
    return () => clearTimeout(timer)
  }, [data, width, height])

  const nodeCanvasObject = useCallback((node, ctx, globalScale) => {
    const color = NODE_COLORS[node.type] ?? '#888'
    const r = node.type === 'chain' ? 7 : node.type === 'operator' ? 5 : 4
    const isSelected = node.id === selectedId

    ctx.beginPath()
    ctx.arc(node.x, node.y, r + (isSelected ? 2 : 0), 0, 2 * Math.PI)
    ctx.fillStyle = color + (isSelected ? 'ff' : 'cc')
    ctx.fill()
    ctx.strokeStyle = isSelected ? '#fff' : color
    ctx.lineWidth = isSelected ? 2 : 1.5
    ctx.stroke()

    if (globalScale >= 1.8 || isSelected) {
      const label = node.label
      ctx.font = `${10 / globalScale}px Inter`
      ctx.fillStyle = 'rgba(248,250,252,0.85)'
      ctx.textAlign = 'center'
      ctx.fillText(label, node.x, node.y + r + 8 / globalScale)
    }
  }, [selectedId])

  const handleNodeClick = useCallback((node) => {
    if (node.type === 'operator') {
      setSelectedId(node.id)
      onOperatorClick?.({ name: node.label, id: node.operator_id })
    }
  }, [onOperatorClick])

  const handleNodeHover = useCallback((node) => {
    setHoveredNode(node ?? null)
  }, [])

  const meta = data?.meta ?? {}
  const graphData = data ?? { nodes: [], links: [], meta: {} }

  return (
    <div className="w-full h-full overflow-hidden rounded-xl relative">
      <div className="absolute right-3 top-3 z-10 flex flex-wrap gap-2">
        {FILTERS.map((filter) => {
          const active = filter.value === minUnits
          return (
            <button
              key={filter.value}
              type="button"
              onClick={() => setMinUnits(filter.value)}
              className="rounded-full px-2.5 py-1 text-[11px] transition"
              style={{
                background: active ? 'rgba(45,212,191,0.18)' : 'rgba(15,17,23,0.78)',
                border: active ? '1px solid rgba(45,212,191,0.45)' : '1px solid rgba(255,255,255,0.12)',
                color: active ? '#ccfbf1' : 'rgba(255,255,255,0.72)',
              }}
            >
              {filter.label} units
            </button>
          )
        })}
      </div>

      {isLoading && (
        <div className="absolute left-3 top-3 z-10 rounded-xl border border-white/10 bg-black/45 px-3 py-2 text-sm text-white/65">
          Loading operator projection...
        </div>
      )}

      {error && (
        <div className="absolute left-3 top-3 z-10 rounded-xl border border-red-300/30 bg-red-950/50 px-3 py-2 text-sm text-red-200">
          Error loading graph data
        </div>
      )}

      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        width={width}
        height={height}
        backgroundColor="transparent"
        nodeCanvasObject={nodeCanvasObject}
        nodeCanvasObjectMode={() => 'replace'}
        linkColor={() => 'rgba(255,255,255,0.08)'}
        linkWidth={1}
        enableNodeDrag
        enableZoomInteraction
        cooldownTicks={180}
        nodeLabel={() => ''}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
      />

      {hoveredNode && (
        <div
          className="absolute left-3 top-14 pointer-events-none rounded-xl px-3 py-2 text-xs"
          style={{
            background: 'rgba(15,17,23,0.88)',
            border: '1px solid rgba(255,255,255,0.12)',
            backdropFilter: 'blur(8px)',
            maxWidth: 220,
          }}
        >
          <div className="font-semibold text-white/90 truncate">{hoveredNode.label}</div>
          <div className="mt-0.5 flex gap-2 text-white/50">
            <span
              className="font-medium"
              style={{ color: NODE_COLORS[hoveredNode.type] ?? '#888' }}
            >
              {hoveredNode.type}
            </span>
            {hoveredNode.count != null && (
              <span>{hoveredNode.count} unit{hoveredNode.count !== 1 ? 's' : ''}</span>
            )}
          </div>
          {hoveredNode.type === 'operator' && (
            <div className="mt-1 text-[10px] text-white/30">click to inspect units</div>
          )}
        </div>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-4 px-2">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5 text-xs text-white/60">
            <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: color }} />
            {type}
          </span>
        ))}
        <span className="text-xs text-white/45">
          {meta.operator_count || 0} operators, {meta.node_count || 0} nodes, {meta.link_count || 0} links
        </span>
        <span className="text-xs text-white/30">
          projection view: units are explored on click, not rendered all at once
        </span>
      </div>
    </div>
  )
}
