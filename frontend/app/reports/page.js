'use client'
import { useState, useEffect } from 'react'
import { Search, Filter, Calendar, MapPin, Maximize2 } from 'lucide-react'

export default function Reports() {
    const [reports, setReports] = useState([])
    const [loading, setLoading] = useState(true)
    const [filter, setFilter] = useState('all')

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports?limit=50`)
            .then(res => res.json())
            .then(data => {
                setReports(data.reports || [])
                setLoading(false)
            })
            .catch(err => {
                console.error(err)
                setLoading(false)
            })
    }, [])

    const filteredReports = reports.filter(r => {
        if (filter === 'all') return true
        if (filter === 'pending') return ['submitted', 'analyzing', 'analyzed', 'verified'].includes(r.status)
        if (filter === 'resolved') return r.status === 'resolved'
        return true
    })

    const getStatusBadge = (status) => {
        switch (status) {
            case 'resolved': return <span className="badge" style={{ background: 'var(--success)', color: 'black' }}>Resolved</span>
            case 'verified': return <span className="badge" style={{ background: 'var(--primary)', color: 'black' }}>Verified</span>
            case 'analyzed': return <span className="badge" style={{ background: 'var(--accent)', color: 'black' }}>Analyzed</span>
            case 'rejected': return <span className="badge" style={{ background: 'var(--muted-foreground)', color: 'white' }}>Rejected</span>
            default: return <span className="badge" style={{ background: 'var(--warning)', color: 'black' }}>Submitted</span>
        }
    }

    const getSeverityBadge = (severity) => {
        if (!severity) return null
        if (severity >= 8) return <span className="badge" style={{ background: 'var(--danger)', color: 'white' }}>High ({severity}/10)</span>
        if (severity >= 5) return <span className="badge" style={{ background: 'var(--warning)', color: 'black' }}>Med ({severity}/10)</span>
        return <span className="badge" style={{ background: 'var(--success)', color: 'black' }}>Low ({severity}/10)</span>
    }

    return (
        <div className="container animate-fade-in">
            <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h1 style={{ fontSize: '2.5rem', marginBottom: '0.25rem' }}>Waste <span className="gradient-text">Reports</span></h1>
                    <p style={{ color: 'var(--muted-foreground)' }}>View all campus environmental reports</p>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={() => setFilter('all')} className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}>
                        All Reports
                    </button>
                    <button onClick={() => setFilter('pending')} className={`btn ${filter === 'pending' ? 'btn-primary' : 'btn-secondary'}`}>
                        Pending Action
                    </button>
                    <button onClick={() => setFilter('resolved')} className={`btn ${filter === 'resolved' ? 'btn-primary' : 'btn-secondary'}`}>
                        Resolved
                    </button>
                </div>
            </div>

            <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
                {loading ? (
                    <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted-foreground)' }}>Loading reports...</div>
                ) : (
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                            <thead>
                                <tr style={{ background: 'rgba(22, 27, 34, 0.9)', borderBottom: '1px solid var(--border)' }}>
                                    <th style={{ padding: '1rem', color: 'var(--muted-foreground)', fontWeight: 500 }}>Image / Details</th>
                                    <th style={{ padding: '1rem', color: 'var(--muted-foreground)', fontWeight: 500 }}>Location</th>
                                    <th style={{ padding: '1rem', color: 'var(--muted-foreground)', fontWeight: 500 }}>AI Classification</th>
                                    <th style={{ padding: '1rem', color: 'var(--muted-foreground)', fontWeight: 500 }}>Status</th>
                                    <th style={{ padding: '1rem', color: 'var(--muted-foreground)', fontWeight: 500 }}>Date</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredReports.map(report => (
                                    <tr key={report.report_id} style={{ borderBottom: '1px solid var(--border)' }}>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                                                <div style={{
                                                    width: '64px', height: '64px', borderRadius: '6px',
                                                    background: report.image_url ? `url(${process.env.NEXT_PUBLIC_API_URL}${report.image_url}) center/cover` : 'var(--muted)',
                                                    flexShrink: 0
                                                }} />
                                                <div style={{ maxWidth: '300px' }}>
                                                    <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--foreground)' }}>
                                                        {report.description?.length > 80 ? report.description.substring(0, 80) + '...' : report.description}
                                                    </p>
                                                </div>
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--primary)', fontSize: '0.9rem' }}>
                                                <MapPin size={16} />
                                                {report.location_name}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', alignItems: 'flex-start' }}>
                                                <span className="badge" style={{ background: 'var(--muted)', color: 'var(--foreground)' }}>
                                                    {report.waste_type_name || 'Unclassified'}
                                                </span>
                                                {getSeverityBadge(report.severity_score)}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>{getStatusBadge(report.status)}</td>
                                        <td style={{ padding: '1rem', color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
                                            {new Date(report.report_date).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                                {filteredReports.length === 0 && (
                                    <tr>
                                        <td colSpan={5} style={{ padding: '3rem', textAlign: 'center', color: 'var(--muted-foreground)' }}>
                                            No reports found for this filter.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    )
}
