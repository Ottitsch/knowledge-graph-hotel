import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const MARKER_COLOR = '#2dd4bf'

function buildPopup(pt) {
  const name = pt.name ?? 'Property'
  const img = pt.picture_url ? `<img src="${pt.picture_url}" alt="" style="width:100%;height:120px;object-fit:cover;border-radius:6px;margin-bottom:6px;display:block;">` : ''
  const link = pt.website ? `<a href="${pt.website}" target="_blank" rel="noopener noreferrer" style="color:#2dd4bf;font-size:11px;">View listing ↗</a>` : ''
  return `<div style="font-family:Inter,sans-serif;min-width:160px;">${img}<b style="font-size:13px;">${name}</b><br><span style="font-size:11px;color:#64748b;">${pt.type}</span>${link ? '<br>' + link : ''}</div>`
}

export default function OperatorMap({ operatorName, operatorType = 'operator' }) {
  const containerRef = useRef()
  const mapRef = useRef()
  const layerRef = useRef()

  // Init map once the container div is in the DOM (always rendered)
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    mapRef.current = L.map(containerRef.current).setView([48.2082, 16.3738], 13)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      maxZoom: 19,
    }).addTo(mapRef.current)

    return () => {
      mapRef.current?.remove()
      mapRef.current = null
    }
  }, [])

  // Load markers whenever operatorName changes
  useEffect(() => {
    if (!mapRef.current) return

    if (layerRef.current) {
      mapRef.current.removeLayer(layerRef.current)
      layerRef.current = null
    }

    if (!operatorName) return

    // Invalidate size in case the container was hidden before
    setTimeout(() => mapRef.current?.invalidateSize(), 50)

    const endpoint = operatorType === 'chain' ? '/api/chain-map' : '/api/operator-map'
    fetch(`${endpoint}?name=${encodeURIComponent(operatorName)}`)
      .then((r) => r.json())
      .then((data) => {
        if (!mapRef.current) return

        const icon = L.divIcon({
          html: `<div style="width:14px;height:14px;border-radius:50%;background:${MARKER_COLOR};border:2px solid rgba(255,255,255,0.6);box-shadow:0 0 6px ${MARKER_COLOR}88;"></div>`,
          className: '',
          iconSize: [14, 14],
          iconAnchor: [7, 7],
        })

        const group = L.layerGroup()
        const latlngs = []

        data.forEach((pt) => {
          const marker = L.marker([pt.lat, pt.lon], { icon })
          marker.bindPopup(buildPopup(pt), { maxWidth: 260 })
          group.addLayer(marker)
          latlngs.push([pt.lat, pt.lon])
        })

        mapRef.current.addLayer(group)
        layerRef.current = group

        if (latlngs.length > 0) {
          const bounds = L.latLngBounds(latlngs)
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
        <p className="text-xs text-white/50">
          {operatorType === 'chain' ? 'Chain' : 'Operator'}: <span className="font-medium" style={{ color: '#2dd4bf' }}>{operatorName}</span>
        </p>
      )}
      {/* Always in DOM so Leaflet can init; hidden when no operator selected */}
      <div
        ref={containerRef}
        style={{
          height: 420,
          borderRadius: 12,
          overflow: 'hidden',
          display: operatorName ? 'block' : 'none',
        }}
      />
    </div>
  )
}
