'use client'
import { useState, useEffect } from 'react'
import dynamic from 'next/dynamic'
import { AlertCircle, Flame, Filter } from 'lucide-react'

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

        // Fetch reports
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports?limit=50`)
            .then(res => res.json())
            .then(data => setReports(data.reports || []))

        // Fetch hotspots
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/hotspots`)
            .then(res => res.json())
            .then(data => setHotspots(data.hotspots || []))

        // Import leaflet css
        import('leaflet/dist/leaflet.css')
    }, [])

    if (!isClient) return <div className="container" style={{ padding: '2rem 0' }}>Loading map...</div>

    // We need to fix the default Leaflet icons in a Next.js environment
    const getIcon = (type, severity = 0) => {
        if (typeof window === 'undefined') return null
        import('leaflet').then(L => {
            // Setup custom icons
            delete L.Icon.Default.prototype._getIconUrl;
            L.Icon.Default.mergeOptions({
                iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
                iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
            });
        })

        // Returning null here and using the global custom icons defined later if we need different colors
        return null
    }

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
                {/* We use a key to force re-render if needed, but normally not required */}
                <MapContainer
                    center={center}
                    zoom={16}
                    style={{ height: '100%', width: '100%', background: '#0D1117' }}
                    className="dark-map"
                >
                    {/* CartoDB Dark Matter for dark theme map */}
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
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
        </div>
    )
}
