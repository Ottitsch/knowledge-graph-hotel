import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import 'leaflet.markercluster'

const MARKER_COLOR = '#2dd4bf'

export default function OperatorMap({ operatorName }) {
  const containerRef = useRef()
  const mapRef = useRef()
  const layerRef = useRef()

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

  // Load + render points whenever operatorName changes
  useEffect(() => {
    if (!operatorName || !mapRef.current) return

    if (layerRef.current) {
      mapRef.current.removeLayer(layerRef.current)
      layerRef.current = null
    }

    fetch(`/api/operator-map?name=${encodeURIComponent(operatorName)}`)
      .then((r) => r.json())
      .then((data) => {
        if (!mapRef.current) return

        const clusters = L.markerClusterGroup({ maxClusterRadius: 40 })
        const icon = L.divIcon({
          html: `<div style="width:10px;height:10px;border-radius:50%;background:${MARKER_COLOR};border:2px solid rgba(255,255,255,0.6);"></div>`,
          className: '',
          iconSize: [10, 10],
        })

        data.forEach((pt) => {
          const marker = L.marker([pt.lat, pt.lon], { icon })
          marker.bindPopup(`<b>${pt.name ?? 'Property'}</b><br><small>${pt.type}</small>`)
          clusters.addLayer(marker)
        })

        mapRef.current.addLayer(clusters)
        layerRef.current = clusters

        if (data.length > 0) {
          const bounds = clusters.getBounds()
          if (bounds.isValid()) mapRef.current.fitBounds(bounds, { padding: [32, 32] })
        }
      })
      .catch(console.error)
  }, [operatorName])

  return (
    <div className="w-full flex flex-col gap-2">
      {!operatorName ? (
        <div
          className="flex items-center justify-center text-white/30 text-sm"
          style={{ height: 420, borderRadius: 12, border: '1px dashed rgba(255,255,255,0.12)' }}
        >
          Click an operator node in the Force Graph to see their listings here
        </div>
      ) : (
        <>
          <p className="text-xs text-white/50">
            Listings by <span className="text-teal-400 font-medium" style={{ color: '#2dd4bf' }}>{operatorName}</span>
          </p>
          <div ref={containerRef} style={{ height: 420, borderRadius: 12, overflow: 'hidden' }} />
        </>
      )}
    </div>
  )
}
