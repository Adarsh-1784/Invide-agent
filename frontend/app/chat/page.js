'use client'
import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Lightbulb, CheckCircle, Map as MapIcon, BarChart2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

export default function AgentChat() {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hello! I'm the **EcoNITH Agent**, your AI assistant for NIT Hamirpur's environmental management.\n\nI can:\n- Query the database to show waste statistics\n- Generate charts for trends in severity or waste types\n- Create maps mapping campus hotspots\n- Analyze images of waste\n\nWhat would you like to know?"
        }
    ])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const suggestedQueries = [
        { icon: <BarChart2 size={16} />, text: "Show me a chart of waste types" },
        { icon: <MapIcon size={16} />, text: "Show me a map of campus hotspots" },
        { icon: <Lightbulb size={16} />, text: "What are the most severe issues right now?" }
    ]

    const handleSend = async (text = input) => {
        if (!text.trim() || isLoading) return

        const userMsg = { role: 'user', content: text }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setIsLoading(true)

        try {
            const chatHistory = messages.filter(m => m.role !== 'tool').map(m => ({
                role: m.role,
                content: m.content
            }))

            const res = await fetch(`/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, history: chatHistory })
            })

            const data = await res.json()

            if (!res.ok) {
                throw new Error(data.error || 'Server error connecting to AI Provider.');
            }

            setMessages(prev => [
                ...prev,
                {
                    role: 'assistant',
                    content: data.response,
                    mode: data.mode,
                    rounds: data.rounds
                }
            ])

        } catch (err) {
            console.error(err)
            setMessages(prev => [...prev, { role: 'assistant', content: `**Error:** ${err.message || 'Sorry, I encountered an error connecting to the server.'}` }])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="container animate-fade-in" style={{ height: 'calc(100vh - 12rem)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 style={{ fontSize: '2rem', marginBottom: '0.25rem' }}>EcoNITH <span className="gradient-text">AgentCore</span></h1>
                    <p style={{ color: 'var(--muted-foreground)' }}>Autonomous AI Agent with multi-tool calling</p>
                </div>
            </div>

            <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
                {/* Chat History */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {messages.map((msg, i) => (
                        <div key={i} style={{
                            display: 'flex',
                            gap: '1rem',
                            alignItems: 'flex-start',
                            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
                        }}>
                            {/* Avatar */}
                            <div style={{
                                width: '40px', height: '40px', borderRadius: '50%',
                                background: msg.role === 'user' ? 'var(--primary)' : 'var(--muted)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                flexShrink: 0
                            }}>
                                {msg.role === 'user' ? <User size={20} color="black" /> : <Bot size={20} color="var(--primary)" />}
                            </div>

                            {/* Message Content */}
                            <div style={{
                                background: msg.role === 'user' ? 'var(--primary)' : 'var(--muted)',
                                color: msg.role === 'user' ? 'black' : 'var(--foreground)',
                                padding: '1rem 1.25rem',
                                borderRadius: '12px',
                                borderTopRightRadius: msg.role === 'user' ? '2px' : '12px',
                                borderTopLeftRadius: msg.role === 'user' ? '12px' : '2px',
                                maxWidth: '80%',
                                fontSize: '0.95rem',
                                lineHeight: '1.5'
                            }}>
                                {msg.role === 'assistant' ? (
                                    <div className="markdown-body">
                                        <ReactMarkdown
                                            components={{
                                                img: ({ node, ...props }) => {
                                                    // Handle charts generated by the agent by fixing the path to point to backend URL
                                                    const src = props.src.startsWith('/') ? `${process.env.NEXT_PUBLIC_API_URL}${props.src}` : props.src
                                                    return <img {...props} src={src} style={{ maxWidth: '100%', borderRadius: '8px', margin: '1rem 0', border: '1px solid var(--border)' }} />
                                                },
                                                a: ({ node, ...props }) => {
                                                    if (props.href.includes('.html')) {
                                                        const href = props.href.startsWith('/') ? `${process.env.NEXT_PUBLIC_API_URL}${props.href}` : props.href
                                                        return (
                                                            <a href={href} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ display: 'inline-flex', margin: '1rem 0' }}>
                                                                <MapIcon size={16} /> Open Interactive Map
                                                            </a>
                                                        )
                                                    }
                                                    return <a {...props} style={{ color: 'var(--primary)' }} />
                                                }
                                            }}
                                        >
                                            {msg.content}
                                        </ReactMarkdown>
                                        {msg.rounds > 1 && (
                                            <div style={{ marginTop: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--border)', fontSize: '0.75rem', color: 'var(--muted-foreground)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <CheckCircle size={12} color="var(--success)" /> Agent completed task via {msg.rounds} autonomous tool-calling rounds.
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    msg.content
                                )}
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--muted)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <Bot size={20} color="var(--primary)" />
                            </div>
                            <div style={{ padding: '1rem', background: 'var(--muted)', borderRadius: '12px', borderTopLeftRadius: '2px', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <Loader2 className="animate-spin" size={18} color="var(--primary)" />
                                <span style={{ fontSize: '0.9rem', color: 'var(--muted-foreground)' }}>Agent is reasoning and calling tools...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Suggested Queries - Only show initially */}
                {messages.length === 1 && (
                    <div style={{ padding: '0 1.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                        {suggestedQueries.map((q, i) => (
                            <button
                                key={i}
                                className="badge"
                                style={{ background: 'var(--muted)', border: '1px solid var(--border)', color: 'var(--muted-foreground)', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', padding: '0.5rem 0.75rem' }}
                                onClick={() => handleSend(q.text)}
                                onMouseOver={e => e.currentTarget.style.borderColor = 'var(--primary)'}
                                onMouseOut={e => e.currentTarget.style.borderColor = 'var(--border)'}
                            >
                                {q.icon} {q.text}
                            </button>
                        ))}
                    </div>
                )}

                {/* Input Area */}
                <div style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border)' }}>
                    <form
                        onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                        style={{ display: 'flex', gap: '1rem' }}
                    >
                        <input
                            type="text"
                            className="input-field"
                            placeholder="Ask the agent to generate charts, maps, or statistics..."
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            disabled={isLoading}
                            style={{ background: 'var(--background)' }}
                        />
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={!input.trim() || isLoading}
                            style={{ padding: '0 1.5rem', borderRadius: '8px' }}
                        >
                            <Send size={20} />
                        </button>
                    </form>
                </div>
            </div>
        </div>
    )
}
