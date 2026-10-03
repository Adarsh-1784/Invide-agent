import './globals.css'
import Link from 'next/link'
import { Leaf, LayoutDashboard, Map as MapIcon, MessageSquare, List } from 'lucide-react'

export const metadata = {
  title: 'EcoNITH | AI Campus Environmental Management',
  description: 'AI-Powered Campus Environmental Management for NIT Hamirpur',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <nav style={{
          position: 'sticky',
          top: 0,
          zIndex: 50,
          background: 'rgba(13, 17, 23, 0.8)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--border)'
        }}>
          <div className="container" style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: '4rem'
          }}>
            <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold', fontSize: '1.25rem' }}>
              <Leaf color="var(--primary)" size={24} />
              <span className="gradient-text">EcoNITH</span>
            </Link>

            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
              <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
                <LayoutDashboard size={18} />
                <span className="nav-label">Dashboard</span>
              </Link>
              <Link href="/reports" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
                <List size={18} />
                <span className="nav-label">Reports</span>
              </Link>
              <Link href="/map" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
                <MapIcon size={18} />
                <span className="nav-label">Campus Map</span>
              </Link>
              <Link href="/chat" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--muted-foreground)', fontSize: '0.9rem' }}>
                <MessageSquare size={18} />
                <span className="nav-label">Agent Chat</span>
              </Link>
              <Link href="/report" className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.9rem' }}>
                Report Issue
              </Link>
            </div>
          </div>
        </nav>

        <main style={{ flex: 1, padding: '2rem 0' }}>
          {children}
        </main>

        <footer style={{
          borderTop: '1px solid var(--border)',
          padding: '2rem 0',
          marginTop: 'auto',
          color: 'var(--muted-foreground)',
          fontSize: '0.9rem',
          textAlign: 'center'
        }}>
          <div className="container">
            <p>EcoNITH - AI-Powered Campus Environmental Management for NIT Hamirpur.</p>
            <p style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>Inspired by EcoLafaek | Demo Version</p>
          </div>
        </footer>
      </body>
    </html>
  )
}
