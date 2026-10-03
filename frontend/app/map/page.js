'use client'
import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { AlertCircle, Flame, Filter } from 'lucide-react'
import 'leaflet/dist/leaflet.css'

// Import Leaflet dynamically since it needs window at runtime
const MapContainer = dynamic(
    () => import('react-leaflet').then(mod => mod.MapContainer),
    { ssr: false }
)
const TileLayer = dynamic(
    () => import('react-leaflet').then(mod => mod.TileLayer),
    { ssr: false }
)
const Marker = dynamic(
    () => import('react-leaflet').then(mod => mod.Marker),
    { ssr: false }
)
const Popup = dynamic(
    () => import('react-leaflet').then(mod => mod.Popup),
    { ssr: false }
)

export default function CampusMap() {
    const [reports, setReports] = useState([])
    const [hotspots, setHotspots] = useState([])
    const [filter, setFilter] = useState('all') // all, hotspots, reports
    const [isClient, setIsClient] = useState(false)

    // NIT Hamirpur coordinates
    const center = [31.7082, 76.5274]

    useEffect(() => {
        setIsClient(true)

        // Fix Leaflet's default icon paths by replacing them with foolproof CSS markers
        import('leaflet').then(L => {
            const customIcon = L.divIcon({
                className: 'custom-leaflet-marker',
                html: '<div style="background-color: var(--primary, #00C9B7); width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 6px rgba(0,0,0,0.8);"></div>',
                iconSize: [14, 14],
                iconAnchor: [7, 7],
                popupAnchor: [0, -10]
            });
            L.Marker.prototype.options.icon = customIcon;
        })

        // Fetch reports
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports?limit=50`)
            .then(res => res.json())
            .then(data => setReports(data.reports || []))

        // Fetch hotspots
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/hotspots`)
            .then(res => res.json())
            .then(data => setHotspots(data.hotspots || []))
    }, [])

    if (!isClient) return <div className="container" style={{ padding: '2rem 0' }}>Loading map...</div>

    return (
        <div className="container animate-fade-in" style={{ height: 'calc(100vh - 12rem)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.25rem' }}>Campus <span className="gradient-text">Map</span></h1>
                    <p style={{ color: 'var(--muted-foreground)' }}>Interactive visualization of waste locations and hotspots</p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem', background: 'var(--card)', padding: '0.5rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <button
                        className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.25rem 0.75rem' }}
                        onClick={() => setFilter('all')}
                    >
                        All View
                    </button>
                    <button
                        className={`btn ${filter === 'hotspots' ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.25rem 0.75rem' }}
                        onClick={() => setFilter('hotspots')}
                    >
                        Hotspots
                    </button>
                    <button
                        className={`btn ${filter === 'reports' ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '0.25rem 0.75rem' }}
                        onClick={() => setFilter('reports')}
                    >
                        Recent Reports
                    </button>
                </div>
            </div>

            <div className="glass-panel" style={{ flex: 1, padding: 0, overflow: 'hidden', position: 'relative' }}>
                <MapContainer
                    center={center}
                    zoom={16}
                    style={{ height: '100%', width: '100%', background: '#0D1117' }}
                    className="dark-map"
                >
                    {/* Using Standard OSM, and we'll apply a CSS filter via global styles to make it dark */}
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />

                    {/* Render Hotspots */}
                    {(filter === 'all' || filter === 'hotspots') && hotspots.map(h => (
                        <Marker key={h.hotspot_id} position={[h.latitude, h.longitude]}>
                            <Popup className="dark-popup">
                                <div style={{ padding: '0.5rem', color: 'black' }}>
                                    <h3 style={{ margin: '0 0 0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <Flame color={h.avg_severity > 7 ? 'red' : 'orange'} size={18} />
                                        {h.location_name}
                                    </h3>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem' }}>
                                        <div><strong>Reports:</strong> {h.report_count}</div>
                                        <div><strong>Severity:</strong> {h.avg_severity}/10</div>
                                        <div style={{ gridColumn: 'span 2' }}>
                                            <strong>Main Type:</strong> {h.predominant_waste}
                                        </div>
                                    </div>
                                </div>
                            </Popup>
                        </Marker>
                    ))}

                    {/* Render Reports */}
                    {(filter === 'all' || filter === 'reports') && reports.filter(r => r.status !== 'resolved').map(r => (
                        <Marker key={r.report_id} position={[r.latitude, r.longitude]}>
                            <Popup>
                                <div style={{ padding: '0.5rem', color: 'black', maxWidth: '200px' }}>
                                    <h4 style={{ margin: '0 0 0.2rem' }}>{r.waste_type_name || 'Report'}</h4>
                                    <p style={{ fontSize: '0.8rem', color: '#666', margin: '0 0 0.5rem' }}>{new Date(r.report_date).toLocaleDateString()}</p>
                                    <p style={{ fontSize: '0.9rem', margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical' }}>
                                        {r.description}
                                    </p>
                                </div>
                            </Popup>
                        </Marker>
                    ))}
                </MapContainer>

                {/* Legend */}
                <div style={{ position: 'absolute', bottom: '20px', right: '20px', zIndex: 1000, background: 'rgba(22, 27, 34, 0.9)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>Legend</h4>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--muted-foreground)' }}>
                        <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', background: '#3388ff' }}></span>
                        Location Marker
                    </div>
                </div>
            </div>

            <style jsx global>{`
                /* Invert OSM colors to create a beautiful dark map that matches the UI perfectly */
                .leaflet-layer,
                .leaflet-control-zoom-in,
                .leaflet-control-zoom-out,
                .leaflet-control-attribution {
                    filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
                }
            `}</style>
        </div>
    )
}
