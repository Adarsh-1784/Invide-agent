"""
EcoNITH API Routes — REST endpoints for the campus environmental management system.
"""
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse

from database import get_db, CAMPUS_LOCATIONS, WASTE_TYPES
from agent import run_agent
from tools import analyze_report_image, execute_tool
from config import UPLOADS_DIR, DEMO_MODE

router = APIRouter(prefix="/api")


# ─── Reports ────────────────────────────────────────────

@router.post("/reports")
async def create_report(
    description: str = Form(...),
    location_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    image: Optional[UploadFile] = File(None),
):
    """Submit a new waste/environmental report."""
    report_id = str(uuid.uuid4())
    image_url = None

    # Save uploaded image
    if image and image.filename:
        ext = Path(image.filename).suffix or ".jpg"
        filename = f"{report_id}{ext}"
        filepath = UPLOADS_DIR / filename
        with open(filepath, "wb") as f:
            content = await image.read()
            f.write(content)
        image_url = f"/static/uploads/{filename}"

    # Find location name
    location = next((l for l in CAMPUS_LOCATIONS if l["id"] == location_id), None)
    address_text = f"{location['name']}, NIT Hamirpur Campus" if location else "NIT Hamirpur Campus"

    # Insert report
    conn = get_db()
    conn.execute(
        """INSERT INTO reports (report_id, location_id, latitude, longitude,
           description, image_url, status, report_date, address_text)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (report_id, location_id, latitude, longitude, description,
         image_url, "submitted", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address_text)
    )
    conn.commit()

    # Auto-analyze if image provided
    analysis = None
    if image_url:
        img_path = str(UPLOADS_DIR / f"{report_id}{ext}")
        analysis = analyze_report_image(img_path, context=f"Location: {address_text}. Description: {description}")

        if analysis and "error" not in analysis:
            # Save analysis
            waste_type_name = analysis.get("waste_type", "Mixed")
            wt = next((w for w in WASTE_TYPES if w["name"].lower() == waste_type_name.lower()), WASTE_TYPES[-1])

            conn.execute(
                """INSERT INTO analysis_results
                   (analysis_id, report_id, waste_type_id, confidence_score, severity_score,
                    priority_level, environmental_impact, safety_concerns, estimated_volume, full_description)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), report_id, wt["id"],
                    analysis.get("confidence_score", 80),
                    analysis.get("severity_score", 5),
                    analysis.get("priority_level", "medium"),
                    analysis.get("environmental_impact", ""),
                    analysis.get("safety_concerns", ""),
                    analysis.get("estimated_volume", ""),
                    analysis.get("full_description", "")
                )
            )
            conn.execute("UPDATE reports SET status='analyzed' WHERE report_id=?", (report_id,))
            conn.commit()

    conn.close()

    return {
        "report_id": report_id,
        "status": "analyzed" if analysis else "submitted",
        "image_url": image_url,
        "analysis": analysis,
        "message": "Report submitted successfully"
    }


@router.get("/reports")
async def list_reports(
    status: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
):
    """List waste reports with optional filters."""
    conn = get_db()
    query = """
        SELECT r.*, ar.waste_type_id, ar.severity_score, ar.priority_level,
               ar.confidence_score, ar.full_description as analysis_description,
               wt.name as waste_type_name, cl.name as location_name, cl.type as location_type
        FROM reports r
        LEFT JOIN analysis_results ar ON r.report_id = ar.report_id
        LEFT JOIN waste_types wt ON ar.waste_type_id = wt.waste_type_id
        LEFT JOIN campus_locations cl ON r.location_id = cl.location_id
    """
    conditions = []
    params = []

    if status:
        conditions.append("r.status = ?")
        params.append(status)
    if location_id:
        conditions.append("r.location_id = ?")
        params.append(location_id)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY r.report_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) FROM reports r" +
        (" WHERE " + " AND ".join(conditions) if conditions else ""),
        params[:-2] if conditions else []
    ).fetchone()[0]

    conn.close()
    return {
        "reports": [dict(r) for r in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a single report with full analysis details."""
    conn = get_db()
    row = conn.execute(
        """SELECT r.*, ar.waste_type_id, ar.severity_score, ar.priority_level,
                  ar.confidence_score, ar.environmental_impact, ar.safety_concerns,
                  ar.estimated_volume, ar.full_description as analysis_description,
                  ar.analyzed_date,
                  wt.name as waste_type_name, wt.hazard_level, wt.recyclable,
                  cl.name as location_name, cl.type as location_type
           FROM reports r
           LEFT JOIN analysis_results ar ON r.report_id = ar.report_id
           LEFT JOIN waste_types wt ON ar.waste_type_id = wt.waste_type_id
           LEFT JOIN campus_locations cl ON r.location_id = cl.location_id
           WHERE r.report_id = ?""",
        (report_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return dict(row)


# ─── Statistics ──────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    """Get aggregate campus waste statistics."""
    conn = get_db()

    # Core stats
    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM reports WHERE status='resolved'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM reports WHERE status IN ('submitted','analyzing','analyzed','verified')").fetchone()[0]
    avg_severity = conn.execute("SELECT COALESCE(AVG(severity_score),0) FROM analysis_results").fetchone()[0]

    # By waste type
    waste_breakdown = conn.execute(
        """SELECT wt.name, COUNT(*) as count
           FROM analysis_results ar
           JOIN waste_types wt ON ar.waste_type_id = wt.waste_type_id
           GROUP BY wt.name ORDER BY count DESC"""
    ).fetchall()

    # By status
    status_breakdown = conn.execute(
        "SELECT status, COUNT(*) as count FROM reports GROUP BY status"
    ).fetchall()

    # By location type
    location_breakdown = conn.execute(
        """SELECT cl.type, COUNT(*) as count FROM reports r
           JOIN campus_locations cl ON r.location_id = cl.location_id
           GROUP BY cl.type ORDER BY count DESC"""
    ).fetchall()

    # Recent reports
    recent = conn.execute(
        """SELECT r.report_id, r.description, r.status, r.report_date, r.image_url,
                  cl.name as location_name, wt.name as waste_type,
                  ar.severity_score
           FROM reports r
           LEFT JOIN campus_locations cl ON r.location_id = cl.location_id
           LEFT JOIN analysis_results ar ON r.report_id = ar.report_id
           LEFT JOIN waste_types wt ON ar.waste_type_id = wt.waste_type_id
           ORDER BY r.report_date DESC LIMIT 5"""
    ).fetchall()

    # Monthly trend
    monthly = conn.execute(
        """SELECT strftime('%Y-%m', report_date) as month, COUNT(*) as count
           FROM reports GROUP BY month ORDER BY month"""
    ).fetchall()

    conn.close()

    return {
        "total_reports": total,
        "resolved_reports": resolved,
        "pending_reports": pending,
        "avg_severity": round(avg_severity, 1),
        "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
        "waste_breakdown": [dict(r) for r in waste_breakdown],
        "status_breakdown": [dict(r) for r in status_breakdown],
        "location_breakdown": [dict(r) for r in location_breakdown],
        "recent_reports": [dict(r) for r in recent],
        "monthly_trend": [dict(r) for r in monthly],
    }


# ─── Hotspots ────────────────────────────────────────────

@router.get("/hotspots")
async def get_hotspots():
    """Get campus waste hotspot data."""
    conn = get_db()
    rows = conn.execute(
        """SELECT h.*, cl.name as location_name, cl.type as location_type
           FROM hotspots h
           JOIN campus_locations cl ON h.location_id = cl.location_id
           ORDER BY h.avg_severity DESC"""
    ).fetchall()
    conn.close()
    return {"hotspots": [dict(r) for r in rows]}


# ─── Locations ───────────────────────────────────────────

@router.get("/locations")
async def get_locations(location_type: Optional[str] = Query(None)):
    """Get NIT Hamirpur campus locations."""
    locations = CAMPUS_LOCATIONS
    if location_type:
        locations = [l for l in locations if l["type"] == location_type]
    return {"locations": locations}


# ─── Agent Chat ──────────────────────────────────────────

@router.post("/chat")
async def agent_chat(body: dict):
    """Send a message to the EcoNITH AI agent."""
    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    result = run_agent(message, history)
    return {
        "response": result.get("response", ""),
        "tool_calls": result.get("tool_calls", []),
        "rounds": result.get("rounds", 0),
        "charts": result.get("charts", []),
        "maps": result.get("maps", []),
        "mode": result.get("mode", "demo"),
    }


# ─── Image Analysis ─────────────────────────────────────

@router.post("/analyze-image")
async def analyze_image_endpoint(image: UploadFile = File(...)):
    """Analyze a waste image using AI."""
    # Save temp image
    temp_id = uuid.uuid4().hex[:8]
    ext = Path(image.filename).suffix or ".jpg"
    filename = f"temp_{temp_id}{ext}"
    filepath = UPLOADS_DIR / filename

    with open(filepath, "wb") as f:
        content = await image.read()
        f.write(content)

    result = analyze_report_image(str(filepath), context="NIT Hamirpur campus area")
    result["image_url"] = f"/static/uploads/{filename}"
    return result


# ─── Health ──────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    conn = get_db()
    report_count = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    conn.close()
    return {
        "status": "healthy",
        "service": "EcoNITH Backend",
        "demo_mode": DEMO_MODE,
        "database": f"{report_count} reports",
        "timestamp": datetime.now().isoformat(),
    }
