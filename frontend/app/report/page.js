'use client'
import { useState, useEffect } from 'react'
import { Upload, MapPin, Loader2, CheckCircle } from 'lucide-react'

export default function SubmitReport() {
    const [locations, setLocations] = useState([])
    const [formData, setFormData] = useState({
        description: '',
        location_id: '',
        latitude: 31.7082,
        longitude: 76.5274,
    })
    const [imageFile, setImageFile] = useState(null)
    const [imagePreview, setImagePreview] = useState(null)

    const [isSubmitting, setIsSubmitting] = useState(false)
    const [success, setSuccess] = useState(null)

    useEffect(() => {
        fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/locations`)
            .then(res => res.json())
            .then(data => setLocations(data.locations || []))
            .catch(err => console.error(err))
    }, [])

    const handleImageChange = (e) => {
        const file = e.target.files[0]
        if (file) {
            setImageFile(file)
            const reader = new FileReader()
            reader.onloadend = () => setImagePreview(reader.result)
            reader.readAsDataURL(file)
        }
    }

    const handleLocationChange = (e) => {
        const locId = e.target.value
        const loc = locations.find(l => l.id === locId)
        if (loc) {
            setFormData(prev => ({
                ...prev,
                location_id: loc.id,
                latitude: loc.lat,
                longitude: loc.lng
            }))
        }
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (!formData.location_id) return alert("Please select a location")

        setIsSubmitting(true)
        try {
            const data = new FormData()
            data.append("description", formData.description)
            data.append("location_id", formData.location_id)
            data.append("latitude", formData.latitude)
            data.append("longitude", formData.longitude)
            if (imageFile) data.append("image", imageFile)

            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/reports`, {
                method: 'POST',
                body: data,
            })

            const result = await res.json()
            if (res.ok) {
                setSuccess(result)
                // Reset form
                setFormData({ description: '', location_id: '', latitude: 31.7082, longitude: 76.5274 })
                setImageFile(null)
                setImagePreview(null)
            } else {
                alert(result.detail || "Error submitting report")
            }
        } catch (err) {
            console.error(err)
            alert("Error connecting to server")
        } finally {
            setIsSubmitting(false)
        }
    }

    if (success) {
        return (
            <div className="container animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '4rem' }}>
                <CheckCircle size={64} color="var(--success)" style={{ marginBottom: '1.5rem' }} />
                <h1 style={{ fontSize: '2rem', marginBottom: '1rem' }}>Report Submitted!</h1>
                <p style={{ color: 'var(--muted-foreground)', marginBottom: '2rem', textAlign: 'center', maxWidth: '500px' }}>
                    Thank you for helping keep NIT Hamirpur clean. {success.status === 'analyzed' && "Our AI has already analyzed your image and categorized the issue."}
                </p>

                {success.analysis && (
                    <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', marginBottom: '2rem', borderLeft: '4px solid var(--primary)' }}>
                        <h3 style={{ marginBottom: '1rem', color: 'var(--primary)' }}>AI Analysis Results</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)' }}>Waste Type</div>
                                <div style={{ fontWeight: 'bold' }}>{success.analysis.waste_type}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)' }}>Severity</div>
                                <div style={{ fontWeight: 'bold' }}>{success.analysis.severity_score}/10</div>
                            </div>
                            <div style={{ gridColumn: 'span 2' }}>
                                <div style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)' }}>Impact</div>
                                <div style={{ fontSize: '0.9rem' }}>{success.analysis.environmental_impact}</div>
                            </div>
                        </div>
                    </div>
                )}

                <button className="btn btn-secondary" onClick={() => setSuccess(null)}>
                    Submit Another Report
                </button>
            </div>
        )
    }

    return (
        <div className="container animate-fade-in" style={{ maxWidth: '800px' }}>
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Report an Issue</h1>
                <p style={{ color: 'var(--muted-foreground)' }}>Help keep NIT Hamirpur campus clean by reporting environmental issues.</p>
            </div>

            <div className="glass-panel">
                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

                    {/* Image Upload */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Photo (Required for AI Analysis)</label>
                        <div
                            style={{
                                border: '2px dashed var(--border)',
                                borderRadius: '8px',
                                padding: '2rem',
                                textAlign: 'center',
                                background: imagePreview ? `url(${imagePreview}) center/cover` : 'var(--background)',
                                position: 'relative',
                                cursor: 'pointer',
                                transition: 'border-color 0.2s',
                                minHeight: '200px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexDirection: 'column'
                            }}
                            onClick={() => document.getElementById('image-upload').click()}
                            onMouseOver={(e) => !imagePreview && (e.currentTarget.style.borderColor = 'var(--primary)')}
                            onMouseOut={(e) => (e.currentTarget.style.borderColor = 'var(--border)')}
                        >
                            {!imagePreview && (
                                <>
                                    <Upload size={32} color="var(--primary)" style={{ marginBottom: '1rem' }} />
                                    <p style={{ color: 'var(--muted-foreground)' }}>Click to upload a photo of the waste</p>
                                    <p style={{ fontSize: '0.8rem', color: 'var(--muted-foreground)', marginTop: '0.5rem' }}>JPEG or PNG, max 5MB</p>
                                </>
                            )}
                            {imagePreview && (
                                <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0, transition: 'opacity 0.2s' }}
                                    onMouseOver={e => e.currentTarget.style.opacity = 1}
                                    onMouseOut={e => e.currentTarget.style.opacity = 0}>
                                    <p style={{ color: 'white', fontWeight: 'bold' }}>Change Image</p>
                                </div>
                            )}
                            <input
                                id="image-upload"
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                                style={{ display: 'none' }}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        {/* Location */}
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: '500' }}>
                                <MapPin size={18} color="var(--primary)" /> Campus Location *
                            </label>
                            <select
                                className="input-field"
                                value={formData.location_id}
                                onChange={handleLocationChange}
                                required
                                style={{ backgroundColor: 'var(--background)' }}
                            >
                                <option value="">Select a location...</option>
                                {/* Group by type */}
                                {['hostel', 'academic', 'mess', 'facility'].map(type => (
                                    <optgroup label={type.charAt(0).toUpperCase() + type.slice(1) + 's'} key={type}>
                                        {locations.filter(l => l.type === type).map(loc => (
                                            <option key={loc.id} value={loc.id}>{loc.name}</option>
                                        ))}
                                    </optgroup>
                                ))}
                            </select>
                        </div>

                        {/* Description */}
                        <div style={{ gridColumn: 'span 2' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>Description</label>
                            <textarea
                                className="input-field"
                                placeholder="Briefly describe the issue..."
                                rows={4}
                                value={formData.description}
                                onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary"
                        style={{ width: '100%', padding: '1rem', fontSize: '1.1rem', marginTop: '1rem' }}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? (
                            <><Loader2 className="animate-spin" size={20} /> Submitting & Analyzing...</>
                        ) : "Submit Report"}
                    </button>
                </form>
            </div>
        </div>
    )
}
