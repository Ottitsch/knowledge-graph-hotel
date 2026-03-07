import { useEffect, useRef } from 'react'
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

export default function PropertyMap() {
  const { data, isLoading, error } = useApi('/api/map-points')
  const containerRef = useRef()
  const mapRef = useRef()

  useEffect(() => {
    if (!data || !containerRef.current) return

    // Init map once
    if (!mapRef.current) {
      mapRef.current = L.map(containerRef.current).setView([48.2082, 16.3738], 13)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
        maxZoom: 19,
      }).addTo(mapRef.current)
    }

    const map = mapRef.current
    const clusters = L.markerClusterGroup({ maxClusterRadius: 40 })

    data.forEach((pt) => {
      const color = colorFor(pt.type)
      const icon = L.divIcon({
        html: `<div style="width:8px;height:8px;border-radius:50%;background:${color};border:1px solid rgba(255,255,255,0.4);"></div>`,
        className: '',
        iconSize: [8, 8],
      })
      const marker = L.marker([pt.lat, pt.lon], { icon })
      marker.bindPopup(`<b>${pt.name ?? 'Property'}</b><br><small>${pt.type}</small>`)
      clusters.addLayer(marker)
    })

    map.addLayer(clusters)

    return () => {
      map.removeLayer(clusters)
    }
  }, [data])

  // Cleanup map on unmount
  useEffect(() => {
    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [])

  return (
    <div className="w-full flex flex-col gap-3">
      {isLoading && <div className="text-white/40 text-sm">Loading map data…</div>}
      {error && <div className="text-red-400 text-sm">Error loading map data</div>}
      <div ref={containerRef} style={{ height: 520, borderRadius: 12, overflow: 'hidden' }} />
      <div className="flex gap-4 flex-wrap">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1.5 text-xs text-white/60">
            <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: color }} />
            {type}
          </span>
        ))}
      </div>
    </div>
  )
}
