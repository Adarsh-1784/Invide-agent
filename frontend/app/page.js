'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { AlertTriangle, CheckCircle, Clock, MapPin, Activity, Flame } from 'lucide-react'

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(err => console.error("Error fetching stats:", err))
  }, [])

  if (!stats) return <div className="container" style={{ padding: '4rem 1.5rem', textAlign: 'center' }}>Loading dashboard...</div>

  return (
    <div className="container animate-fade-in">
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Campus Environment <span className="gradient-text">Overview</span></h1>
        <p style={{ color: 'var(--muted-foreground)' }}>NIT Hamirpur Waste Management Analytics</p>
      </div>

      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted-foreground)' }}>
            <Activity size={18} /><span>Total Reports</span>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{stats.total_reports}</div>
        </div>

        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', borderLeft: '4px solid var(--success)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--success)' }}>
            <CheckCircle size={18} /><span>Resolved</span>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{stats.resolved_reports}</div>
        </div>

        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', borderLeft: '4px solid var(--warning)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--warning)' }}>
            <Clock size={18} /><span>Pending</span>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{stats.pending_reports}</div>
        </div>

        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', borderLeft: '4px solid var(--danger)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--danger)' }}>
            <AlertTriangle size={18} /><span>Avg Severity</span>
          </div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{stats.avg_severity}<span style={{ fontSize: '1rem', color: 'var(--muted-foreground)' }}>/10</span></div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '2rem' }}>
        {/* Main Content Area */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.5rem' }}>Recent Reports</h2>
            <Link href="/reports" style={{ color: 'var(--primary)', fontSize: '0.9rem' }}>View All →</Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {stats.recent_reports?.map(report => (
              <div key={report.report_id} className="glass-panel" style={{ display: 'flex', gap: '1rem', padding: '1rem' }}>
                <div style={{
                  width: '80px', height: '80px', borderRadius: '8px',
                  background: report.image_url ? `url(${process.env.NEXT_PUBLIC_API_URL}${report.image_url}) center/cover` : 'var(--muted)',
                  flexShrink: 0
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="badge" style={{ background: 'var(--muted)', color: 'var(--foreground)' }}>
                        {report.waste_type || 'Unknown'}
                      </span>
                      {report.severity_score >= 7 && <span className="badge" style={{ background: 'var(--danger)', color: 'white' }}>High Severity</span>}
                    </div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)' }}>
                      {new Date(report.report_date).toLocaleDateString()}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: 'var(--foreground)' }}>
                    {report.description?.length > 100 ? report.description.substring(0, 100) + '...' : report.description}
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.8rem', color: 'var(--primary)' }}>
                    <MapPin size={12} /> {report.location_name}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          <div className="glass-panel">
            <h3 style={{ marginBottom: '1rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Flame color="var(--danger)" size={20} /> Top Waste Types
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              {stats.waste_breakdown?.slice(0, 5).map(item => (
                <div key={item.name}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                    <span>{item.name}</span>
                    <span style={{ color: 'var(--muted-foreground)' }}>{item.count}</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: 'var(--muted)', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${(item.count / stats.total_reports) * 100}%`, height: '100%', background: 'linear-gradient(90deg, var(--primary), var(--accent))' }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel" style={{ background: 'linear-gradient(145deg, rgba(22, 27, 34, 0.9), rgba(0, 201, 183, 0.1))' }}>
            <h3 style={{ marginBottom: '0.5rem', fontSize: '1.2rem' }}>Need specific insights?</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--muted-foreground)', marginBottom: '1.5rem' }}>
              Ask the EcoNITH AI Agent to generate custom charts, fetch data, or show hotspot maps.
            </p>
            <Link href="/chat" className="btn btn-primary" style={{ width: '100%' }}>
              Open Agent Chat
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
