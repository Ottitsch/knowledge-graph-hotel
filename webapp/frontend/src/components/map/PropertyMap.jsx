import { useEffect, useRef, useState, useCallback } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.markercluster'
import { useApi } from '../../hooks/useApi'

const TYPE_COLORS = {
  apartment: '#2dd4bf',
  hotel: '#a78bfa',
  house: '#60a5fa',
  room: '#f472b6',
  unknown: '#94a3b8',
}

const TILE_STYLES = [
  {
    id: 'voyager',
    label: 'Voyager',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  },
  {
    id: 'light',
    label: 'Light',
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  },
  {
    id: 'osm',
    label: 'OSM',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors',
  },
  {
    id: 'topo',
    label: 'Topo',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '&copy; OpenStreetMap contributors, SRTM | &copy; OpenTopoMap',
  },
  {
    id: 'satellite',
    label: 'Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri',
  },
  {
    id: 'dark',
    label: 'Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
  },
]

// Color ramp: teal → indigo → rose (no orange/yellow/green)
function clusterColor(count) {
  if (count < 15) return '#2dd4bf'   // teal
  if (count < 60) return '#6366f1'   // indigo
  return '#fb7185'                    // rose
}

// ── Cluster icon builders ─────────────────────────────────────────

function hexagonIcon(count) {
  const color = clusterColor(count)
  const size = count < 15 ? 32 : count < 60 ? 42 : 52
  const cx = size / 2, cy = size / 2, r = size / 2 - 2
  const pts = Array.from({ length: 6 }, (_, i) => {
    const a = (i * 60 - 90) * Math.PI / 180
    return `${cx + r * Math.cos(a)},${cy + r * Math.sin(a)}`
  }).join(' ')
  const fs = size < 42 ? 11 : 13
  return L.divIcon({
    html: `<svg width="${size}" height="${size}" style="filter:drop-shadow(0 2px 6px ${color}66)">
      <polygon points="${pts}" fill="${color}" fill-opacity="0.88" stroke="white" stroke-width="1" stroke-opacity="0.5"/>
      <text x="${cx}" y="${cy + fs * 0.38}" text-anchor="middle" fill="white"
        font-size="${fs}" font-family="Inter,sans-serif" font-weight="700">${count}</text>
    </svg>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

const CLUSTER_STYLES = [
  { id: 'hexagon', label: 'Hexagon', fn: hexagonIcon },
]

// ─────────────────────────────────────────────────────────────────

function colorFor(type) {
  return TYPE_COLORS[type] ?? TYPE_COLORS.unknown
}

function makeIcon(color, size = 8) {
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:1.5px solid rgba(255,255,255,0.5);box-shadow:0 0 6px ${color}88;"></div>`,
    className: '',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

export default function PropertyMap() {
  const { data, isLoading, error } = useApi('/api/map-points')
  const containerRef = useRef()
  const mapRef = useRef()
  const tileLayerRef = useRef()
  const allLayerRef = useRef()
  const focusLayerRef = useRef()
  const clusterStyleRef = useRef('hexagon')

  const [focusInfo, setFocusInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [tileStyle, setTileStyle] = useState('voyager')

  const iconCreateFunction = useCallback((cluster) => {
    const fn = CLUSTER_STYLES.find((s) => s.id === clusterStyleRef.current)?.fn ?? hexagonIcon
    return fn(cluster.getChildCount())
  }, [])

  // Init map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    mapRef.current = L.map(containerRef.current).setView([48.2082, 16.3738], 13)
    const style = TILE_STYLES.find((s) => s.id === 'voyager')
    tileLayerRef.current = L.tileLayer(style.url, {
      attribution: style.attribution,
      maxZoom: 19,
    }).addTo(mapRef.current)
    return () => { mapRef.current?.remove(); mapRef.current = null }
  }, [])

  // Swap tile layer
  useEffect(() => {
    if (!mapRef.current) return
    const style = TILE_STYLES.find((s) => s.id === tileStyle)
    if (!style) return
    if (tileLayerRef.current) mapRef.current.removeLayer(tileLayerRef.current)
    tileLayerRef.current = L.tileLayer(style.url, {
      attribution: style.attribution,
      maxZoom: 19,
    }).addTo(mapRef.current)
    tileLayerRef.current.bringToBack()
  }, [tileStyle])


  // Render all clustered markers once data arrives
  useEffect(() => {
    if (!data || !mapRef.current) return
    const map = mapRef.current

    // Canvas renderer — no DOM node per marker, handles 10k+ points smoothly
    const renderer = L.canvas({ padding: 0.5 })

    const clusters = L.markerClusterGroup({
      iconCreateFunction,
      maxClusterRadius: 40,
      spiderfyOnMaxZoom: true,
      chunkedLoading: true,
      chunkInterval: 100,
      chunkDelay: 30,
    })

    data.forEach((pt) => {
      const marker = L.circleMarker([pt.lat, pt.lon], {
        renderer,
        radius: 6,
        fillColor: colorFor(pt.type),
        fillOpacity: 0.85,
        color: 'rgba(255,255,255,0.55)',
        weight: 1.5,
      })
      marker.bindPopup(`<b>${pt.name ?? 'Property'}</b><br><small>${pt.type}</small>`)
      marker.on('click', () => handlePropertyClick(pt))
      clusters.addLayer(marker)
    })

    map.addLayer(clusters)
    allLayerRef.current = clusters
    return () => { map.removeLayer(clusters) }
  }, [data])

  function handlePropertyClick(pt) {
    setLoading(true)
    const params = new URLSearchParams({ name: pt.name, lat: pt.lat, lon: pt.lon })
    fetch(`/api/property-network?${params}`)
      .then((r) => r.json())
      .then((result) => {
        if (!mapRef.current) return
        const map = mapRef.current

        if (focusLayerRef.current) { map.removeLayer(focusLayerRef.current); focusLayerRef.current = null }

        if (!result.operator) {
          if (allLayerRef.current) map.addLayer(allLayerRef.current)
          setLoading(false)
          return
        }

        if (allLayerRef.current) map.removeLayer(allLayerRef.current)

        const origin = [pt.lat, pt.lon]
        const group = L.layerGroup()

        result.properties.forEach((p) => {
          const isSelf = Math.abs(p.lat - pt.lat) < 0.0001 && Math.abs(p.lon - pt.lon) < 0.0001
          if (!isSelf) {
            L.polyline([origin, [p.lat, p.lon]], {
              color: '#2dd4bf', weight: 1.5, opacity: 0.35, dashArray: '4 6',
            }).addTo(group)
          }
        })

        result.properties.forEach((p) => {
          const isSelf = Math.abs(p.lat - pt.lat) < 0.0001 && Math.abs(p.lon - pt.lon) < 0.0001
          const icon = isSelf ? makeIcon('#1e293b', 18) : makeIcon('#2dd4bf', 14)
          L.marker([p.lat, p.lon], { icon })
            .bindPopup(`<b>${p.name ?? 'Property'}</b><br><small>${p.type}</small>`)
            .addTo(group)
        })

        group.addTo(map)
        focusLayerRef.current = group

        const bounds = L.latLngBounds(result.properties.map((p) => [p.lat, p.lon]))
        if (bounds.isValid()) map.fitBounds(bounds, { padding: [48, 48] })

        setFocusInfo({ operator: result.operator, count: result.properties.length })
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  function clearFocus() {
    if (!mapRef.current) return
    if (focusLayerRef.current) { mapRef.current.removeLayer(focusLayerRef.current); focusLayerRef.current = null }
    if (allLayerRef.current) mapRef.current.addLayer(allLayerRef.current)
    setFocusInfo(null)
  }

  return (
    <div className="w-full flex flex-col gap-3">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="min-h-[28px] flex items-center">
          {focusInfo ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-white/70">
                Operated by{' '}
                <span className="font-semibold" style={{ color: '#2dd4bf' }}>{focusInfo.operator}</span>
                {' '}·{' '}
                <span className="text-white/50">{focusInfo.count} listing{focusInfo.count !== 1 ? 's' : ''}</span>
              </span>
              <button
                onClick={clearFocus}
                className="px-3 py-1 rounded-lg text-xs text-white/60 hover:text-white bg-white/10 hover:bg-white/15 transition-all"
              >
                ← Show all
              </button>
            </div>
          ) : (
            <span className="text-xs text-white/30">Click any listing to explore its operator network</span>
          )}
          {loading && <span className="text-xs text-white/40 ml-3">Loading…</span>}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Tile style picker */}
          <div className="flex gap-1 p-1 rounded-xl" style={{ background: 'rgba(255,255,255,0.06)' }}>
            {TILE_STYLES.map((s) => (
              <button
                key={s.id}
                onClick={() => setTileStyle(s.id)}
                className="px-3 py-1 rounded-lg text-xs font-medium transition-all duration-150"
                style={
                  tileStyle === s.id
                    ? { background: 'rgba(45,212,191,0.2)', color: '#2dd4bf', border: '1px solid rgba(45,212,191,0.35)' }
                    : { color: 'rgba(248,250,252,0.45)', border: '1px solid transparent' }
                }
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {isLoading && <div className="text-white/40 text-sm">Loading map data…</div>}
      {error && <div className="text-red-400 text-sm">Error loading map data</div>}

      <div ref={containerRef} style={{ height: '70vh', borderRadius: 12, overflow: 'hidden' }} />

      {!focusInfo && (
        <div className="flex gap-4 flex-wrap">
          {Object.entries(TYPE_COLORS).map(([type, color]) => (
            <span key={type} className="flex items-center gap-1.5 text-xs text-white/60">
              <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
              {type}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
