import { useEffect, useRef, useState } from 'react'
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
  const allLayerRef = useRef()
  const focusLayerRef = useRef()   // L.LayerGroup for markers + lines together
  const [focusInfo, setFocusInfo] = useState(null)
  const [loading, setLoading] = useState(false)

  // Init map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    mapRef.current = L.map(containerRef.current).setView([48.2082, 16.3738], 13)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      maxZoom: 19,
    }).addTo(mapRef.current)

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [])

  // Render all clustered markers once data arrives
  useEffect(() => {
    if (!data || !mapRef.current) return
    const map = mapRef.current
    const clusters = L.markerClusterGroup({ maxClusterRadius: 40 })

    data.forEach((pt) => {
      const marker = L.marker([pt.lat, pt.lon], { icon: makeIcon(colorFor(pt.type)) })
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

        // Tear down previous focus layer
        if (focusLayerRef.current) { map.removeLayer(focusLayerRef.current); focusLayerRef.current = null }

        if (!result.operator) {
          if (allLayerRef.current) map.addLayer(allLayerRef.current)
          setLoading(false)
          return
        }

        // Hide clustered view
        if (allLayerRef.current) map.removeLayer(allLayerRef.current)

        const origin = [pt.lat, pt.lon]
        const group = L.layerGroup()

        // Lines first (drawn below markers)
        result.properties.forEach((p) => {
          const isSelf = Math.abs(p.lat - pt.lat) < 0.0001 && Math.abs(p.lon - pt.lon) < 0.0001
          if (!isSelf) {
            L.polyline([origin, [p.lat, p.lon]], {
              color: '#2dd4bf',
              weight: 1.5,
              opacity: 0.35,
              dashArray: '4 6',
            }).addTo(group)
          }
        })

        // Markers on top
        result.properties.forEach((p) => {
          const isSelf = Math.abs(p.lat - pt.lat) < 0.0001 && Math.abs(p.lon - pt.lon) < 0.0001
          const icon = isSelf ? makeIcon('#ffffff', 13) : makeIcon('#2dd4bf', 10)
          const marker = L.marker([p.lat, p.lon], { icon })
          marker.bindPopup(`<b>${p.name ?? 'Property'}</b><br><small>${p.type}</small>`)
          group.addLayer(marker)
        })

        group.addTo(map)
        focusLayerRef.current = group

        // Fit bounds to markers only
        const latlngs = result.properties.map((p) => [p.lat, p.lon])
        const bounds = L.latLngBounds(latlngs)
        if (bounds.isValid()) map.fitBounds(bounds, { padding: [48, 48] })

        setFocusInfo({ operator: result.operator, count: result.properties.length })
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }

  function clearFocus() {
    if (!mapRef.current) return
    const map = mapRef.current
    if (focusLayerRef.current) { map.removeLayer(focusLayerRef.current); focusLayerRef.current = null }
    if (allLayerRef.current) map.addLayer(allLayerRef.current)
    setFocusInfo(null)
  }

  return (
    <div className="w-full flex flex-col gap-3">
      <div className="flex items-center justify-between min-h-[28px]">
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
          <span className="text-xs text-white/30">Click any listing to see who operates it and all their other properties</span>
        )}
        {loading && <span className="text-xs text-white/40">Loading…</span>}
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
