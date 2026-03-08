import { useRef, useCallback, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { useApi } from '../../hooks/useApi'

const NODE_COLORS = {
  operator: '#2dd4bf',
  chain: '#a78bfa',
  district: '#60a5fa',
}

export default function ForceGraph({ width = 500, height = 400, onOperatorClick }) {
  const { data, isLoading, error } = useApi('/api/graph')
  const fgRef = useRef()
  const [selectedId, setSelectedId] = useState(null)
  const [hoveredNode, setHoveredNode] = useState(null)

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

  if (isLoading) return <div className="text-white/40 text-sm p-4">Loading graph…</div>
  if (error) return <div className="text-red-400 text-sm p-4">Error loading graph data</div>

  return (
    <div className="w-full h-full overflow-hidden rounded-xl relative">
      <ForceGraph2D
        ref={fgRef}
        graphData={data ?? { nodes: [], links: [] }}
        width={width}
        height={height}
        backgroundColor="transparent"
        nodeCanvasObject={nodeCanvasObject}
        nodeCanvasObjectMode={() => 'replace'}
        linkColor={() => 'rgba(255,255,255,0.08)'}
        linkWidth={1}
        enableNodeDrag={true}
        enableZoomInteraction={true}
        cooldownTicks={120}
        nodeLabel={() => ''}
        onNodeClick={handleNodeClick}
        onNodeHover={handleNodeHover}
      />

      {/* Hover info box */}
      {hoveredNode && (
        <div
          className="absolute top-3 left-3 pointer-events-none rounded-xl px-3 py-2 text-xs"
          style={{
            background: 'rgba(15,17,23,0.88)',
            border: '1px solid rgba(255,255,255,0.12)',
            backdropFilter: 'blur(8px)',
            maxWidth: 220,
          }}
        >
          <div className="font-semibold text-white/90 truncate">{hoveredNode.label}</div>
          <div className="flex gap-2 mt-0.5 text-white/50">
            <span
              className="font-medium"
              style={{ color: NODE_COLORS[hoveredNode.type] ?? '#888' }}
            >
              {hoveredNode.type}
            </span>
            {hoveredNode.count != null && (
              <span>· {hoveredNode.count} unit{hoveredNode.count !== 1 ? 's' : ''}</span>
            )}
          </div>
          {hoveredNode.type === 'operator' && (
            <div className="mt-1 text-white/30 text-[10px]">click to explore</div>
          )}
        </div>
      )}

      <div className="flex gap-4 mt-2 px-2 items-center">
        {Object.entries(NODE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5 text-xs text-white/60">
            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
            {type}
          </span>
        ))}
        <span className="text-xs text-white/30 ml-2">· click an operator to explore</span>
      </div>
    </div>
  )
}
