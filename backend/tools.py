"""
EcoNITH Agent Tools — 5 tools the AI agent can invoke autonomously.
Each tool performs a real operation (SQL, chart generation, map, image analysis, campus info).
"""
import json
import sqlite3
import uuid
import base64
import io
import re
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster

from config import (
    DATABASE_PATH, CHARTS_DIR, MAPS_DIR,
    CAMPUS_CENTER_LAT, CAMPUS_CENTER_LNG, DEMO_MODE,
    get_bedrock_client, BEDROCK_MODEL_ID,
)
from database import CAMPUS_LOCATIONS, WASTE_TYPES, get_db

# ──────────────────────────────────────────────────────
# Tool definitions (JSON schema for agent system prompt)
# ──────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "execute_sql_query",
        "description": (
            "Execute a read-only SQL query against the NIT Hamirpur waste reports database. "
            "Tables: reports (report_id, user_id, location_id, latitude, longitude, description, image_url, status, report_date, address_text), "
            "analysis_results (analysis_id, report_id, waste_type_id, confidence_score, severity_score, priority_level, environmental_impact, safety_concerns, estimated_volume, full_description, analyzed_date), "
            "waste_types (waste_type_id, name, description, hazard_level, recyclable), "
            "campus_locations (location_id, name, type, latitude, longitude), "
            "hotspots (hotspot_id, location_id, latitude, longitude, report_count, avg_severity, predominant_waste, status), "
            "users (user_id, username, full_name, email, role). "
            "Only SELECT queries are allowed. Use JOINs to combine tables as needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The SQL SELECT query to execute."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_chart",
        "description": (
            "Generate a data visualization chart (bar, pie, line, heatmap) using matplotlib. "
            "Provide structured data and chart configuration. Returns the URL path to the generated chart image. "
            "Use this after fetching data with execute_sql_query."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "pie", "line", "horizontal_bar", "stacked_bar"],
                    "description": "Type of chart to generate."
                },
                "title": {
                    "type": "string",
                    "description": "Chart title."
                },
                "labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Category labels for the data."
                },
                "values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Numeric values corresponding to labels."
                },
                "xlabel": {"type": "string", "description": "X-axis label."},
                "ylabel": {"type": "string", "description": "Y-axis label."},
                "colors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of color hex codes."
                }
            },
            "required": ["chart_type", "title", "labels", "values"]
        }
    },
    {
        "name": "generate_campus_map",
        "description": (
            "Generate an interactive HTML map of the NIT Hamirpur campus showing waste report locations, "
            "hotspots, or specific points. Returns a URL path to the generated map HTML file. "
            "Use this for spatial visualization of campus waste data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "markers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number"},
                            "lng": {"type": "number"},
                            "label": {"type": "string"},
                            "severity": {"type": "number", "description": "1-10 severity score for color coding"},
                            "info": {"type": "string", "description": "Popup info text"}
                        },
                        "required": ["lat", "lng", "label"]
                    },
                    "description": "List of markers to place on the map."
                },
                "title": {"type": "string", "description": "Map title."},
                "show_heatmap": {"type": "boolean", "description": "Whether to show a heat map overlay."},
                "zoom": {"type": "integer", "description": "Map zoom level (default 16)."}
            },
            "required": ["markers", "title"]
        }
    },
    {
        "name": "analyze_report_image",
        "description": (
            "Analyze a waste/environmental report image using AI multimodal vision. "
            "Returns waste type classification, severity score, environmental impact, and recommendations. "
            "Use this when the user provides an image or asks about a specific report's image."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path or URL to the image to analyze."
                },
                "context": {
                    "type": "string",
                    "description": "Additional context about where the image was taken."
                }
            },
            "required": ["image_path"]
        }
    },
    {
        "name": "get_campus_info",
        "description": (
            "Get information about NIT Hamirpur campus locations, waste management policies, facilities, "
            "and general campus data. Use this for answering questions about the campus itself."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "enum": ["locations", "waste_policy", "facilities", "statistics_summary", "about"],
                    "description": "Type of campus information to retrieve."
                },
                "location_type": {
                    "type": "string",
                    "enum": ["hostel", "academic", "mess", "canteen", "facility", "road", "waste_point", "admin", "all"],
                    "description": "Filter locations by type (only used when query_type is 'locations')."
                }
            },
            "required": ["query_type"]
        }
    },
]


# ──────────────────────────────────────────────────────
# Tool Implementations
# ──────────────────────────────────────────────────────

def execute_sql_query(query: str) -> dict:
    """Execute a read-only SQL query on the database."""
    # Safety: only allow SELECT
    clean = query.strip().upper()
    if not clean.startswith("SELECT"):
        return {"error": "Only SELECT queries are allowed.", "rows": [], "count": 0}

    # Block dangerous patterns
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC", "ATTACH"]
    for kw in dangerous:
        if re.search(rf'\b{kw}\b', clean):
            return {"error": f"Query contains forbidden keyword: {kw}", "rows": [], "count": 0}

    try:
        conn = get_db()
        cursor = conn.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return {
            "columns": columns,
            "rows": rows[:100],  # Limit to 100 rows
            "count": len(rows),
            "query": query
        }
    except Exception as e:
        return {"error": str(e), "rows": [], "count": 0}


def generate_chart(chart_type: str, title: str, labels: list, values: list,
                   xlabel: str = "", ylabel: str = "", colors: list = None) -> dict:
    """Generate a matplotlib chart and save as PNG."""
    try:
        # Hacktoberfest-inspired dark theme
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor("#0D1117")
        ax.set_facecolor("#0D1117")

        if not colors:
            colors = ["#00C9B7", "#FF6B6B", "#4ECDC4", "#FFD93D", "#6BCB77",
                       "#4D96FF", "#FF8B94", "#A8D8EA", "#AA96DA", "#FCBAD3"]

        if chart_type == "bar":
            bars = ax.bar(labels, values, color=colors[:len(labels)], edgecolor="white", linewidth=0.5)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                        str(int(val)), ha="center", va="bottom", color="white", fontsize=10)
        elif chart_type == "horizontal_bar":
            bars = ax.barh(labels, values, color=colors[:len(labels)], edgecolor="white", linewidth=0.5)
        elif chart_type == "pie":
            ax.pie(values, labels=labels, colors=colors[:len(labels)], autopct="%1.1f%%",
                   startangle=90, textprops={"color": "white", "fontsize": 10})
        elif chart_type == "line":
            ax.plot(labels, values, color="#00C9B7", marker="o", linewidth=2, markersize=6)
            ax.fill_between(range(len(labels)), values, alpha=0.15, color="#00C9B7")
        elif chart_type == "stacked_bar":
            ax.bar(labels, values, color=colors[:len(labels)], edgecolor="white", linewidth=0.5)

        ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=15)
        if xlabel:
            ax.set_xlabel(xlabel, color="white", fontsize=11)
        if ylabel:
            ax.set_ylabel(ylabel, color="white", fontsize=11)

        ax.tick_params(colors="white", labelsize=9)
        if chart_type != "pie":
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#333")
            ax.spines["bottom"].set_color("#333")
            plt.xticks(rotation=45 if len(labels) > 5 else 0, ha="right" if len(labels) > 5 else "center")

        plt.tight_layout()

        filename = f"chart_{uuid.uuid4().hex[:8]}.png"
        filepath = CHARTS_DIR / filename
        fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#0D1117")
        plt.close(fig)

        return {
            "chart_url": f"/static/charts/{filename}",
            "chart_type": chart_type,
            "title": title,
            "data_points": len(labels)
        }
    except Exception as e:
        return {"error": f"Chart generation failed: {str(e)}"}


def generate_campus_map(markers: list, title: str = "NIT Hamirpur Campus",
                        show_heatmap: bool = False, zoom: int = 16) -> dict:
    """Generate an interactive Folium map of campus."""
    try:
        m = folium.Map(
            location=[CAMPUS_CENTER_LAT, CAMPUS_CENTER_LNG],
            zoom_start=zoom,
            tiles="CartoDB dark_matter",
            attr="EcoNITH Campus Map"
        )

        # Title
        title_html = f"""
        <div style="position:fixed; top:10px; left:50%; transform:translateX(-50%);
                     z-index:1000; background:rgba(13,17,23,0.9); color:white;
                     padding:10px 20px; border-radius:8px; font-size:16px; font-weight:bold;
                     border:1px solid #00C9B7;">
            🌿 {title}
        </div>
        """
        m.get_root().html.add_child(folium.Element(title_html))

        # Marker cluster
        cluster = MarkerCluster(name="Reports").add_to(m)

        heat_data = []
        for marker in markers:
            lat = marker.get("lat", CAMPUS_CENTER_LAT)
            lng = marker.get("lng", CAMPUS_CENTER_LNG)
            label = marker.get("label", "Report")
            severity = marker.get("severity", 5)
            info = marker.get("info", "")

            # Color based on severity
            if severity >= 8:
                color = "red"
                icon = "exclamation-triangle"
            elif severity >= 5:
                color = "orange"
                icon = "warning"
            else:
                color = "green"
                icon = "info-sign"

            popup_html = f"""
            <div style="font-family:sans-serif; min-width:200px;">
                <h4 style="margin:0 0 5px; color:#333;">{label}</h4>
                <p style="margin:2px 0;"><b>Severity:</b> {severity}/10</p>
                <p style="margin:2px 0;">{info}</p>
            </div>
            """

            folium.Marker(
                [lat, lng],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{label} (Severity: {severity})",
                icon=folium.Icon(color=color, icon=icon, prefix="glyphicon")
            ).add_to(cluster)

            heat_data.append([lat, lng, severity / 10])

        if show_heatmap and heat_data:
            HeatMap(
                heat_data,
                radius=25,
                blur=15,
                gradient={0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1: "red"}
            ).add_to(m)

        folium.LayerControl().add_to(m)

        filename = f"map_{uuid.uuid4().hex[:8]}.html"
        filepath = MAPS_DIR / filename
        m.save(str(filepath))

        return {
            "map_url": f"/static/maps/{filename}",
            "title": title,
            "marker_count": len(markers),
            "has_heatmap": show_heatmap
        }
    except Exception as e:
        return {"error": f"Map generation failed: {str(e)}"}


def analyze_report_image(image_path: str, context: str = "") -> dict:
    """Analyze a waste image using Amazon Bedrock Nova-Pro multimodal."""
    client = get_bedrock_client()

    if not client or DEMO_MODE:
        # Demo mode: return synthetic analysis
        import random
        wt = random.choice(WASTE_TYPES)
        severity = random.randint(3, 9)
        return {
            "waste_type": wt["name"],
            "severity_score": severity,
            "confidence_score": round(random.uniform(75, 96), 1),
            "priority_level": "high" if severity >= 7 else "medium" if severity >= 4 else "low",
            "environmental_impact": f"Potential {wt['hazard_level']} environmental impact. {wt['description']}.",
            "safety_concerns": "Sharp objects may be present" if wt["hazard_level"] == "high" else "No immediate safety concerns",
            "estimated_volume": random.choice(["~5 kg", "~10 kg", "~20 kg", "~1 bag"]),
            "full_description": f"[DEMO] Image analysis detected {wt['name'].lower()} waste. {context or 'No additional context.'}",
            "recommendations": [
                f"Deploy cleanup crew to remove {wt['name'].lower()} waste",
                "Install additional waste bins in this area",
                "Schedule regular waste collection",
            ],
            "mode": "demo"
        }

    # Real Bedrock Nova-Pro analysis
    try:
        # Read image
        img_path = Path(image_path)
        if img_path.exists():
            with open(img_path, "rb") as f:
                image_bytes = f.read()
            image_b64 = base64.b64encode(image_bytes).decode()
        else:
            return {"error": f"Image not found: {image_path}"}

        prompt = """Analyze this waste/environmental image from NIT Hamirpur campus.
Provide a JSON response with these fields:
- waste_type: primary type of waste (Plastic, Paper, Organic, Electronic, Metal, Glass, Construction, Hazardous, Mixed)
- severity_score: 1-10 rating of severity
- confidence_score: 0-100 confidence in your classification
- priority_level: low/medium/high/critical
- environmental_impact: brief description of environmental risks
- safety_concerns: any safety issues
- estimated_volume: rough estimate of waste volume
- full_description: detailed description of what you see
- recommendations: list of 3 recommended actions

Context: """ + (context or "NIT Hamirpur campus area")

        body = json.dumps({
            "messages": [{
                "role": "user",
                "content": [
                    {"text": prompt},
                    {"image": {"format": "jpeg", "source": {"bytes": image_b64}}}
                ]
            }],
            "inferenceConfig": {"temperature": 0.2, "maxTokens": 2048}
        })

        response = client.invoke_model(modelId=BEDROCK_MODEL_ID, body=body)
        result = json.loads(response["body"].read())
        text = result["output"]["message"]["content"][0]["text"]

        # Try to parse as JSON
        try:
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        return {
            "waste_type": "Mixed",
            "severity_score": 5,
            "full_description": text,
            "mode": "real"
        }

    except Exception as e:
        return {"error": f"Image analysis failed: {str(e)}", "mode": "error"}


def get_campus_info(query_type: str, location_type: str = "all") -> dict:
    """Get NIT Hamirpur campus information."""
    if query_type == "locations":
        locations = CAMPUS_LOCATIONS
        if location_type != "all":
            locations = [l for l in locations if l["type"] == location_type]
        return {
            "locations": locations,
            "count": len(locations),
            "campus": "NIT Hamirpur, Himachal Pradesh"
        }

    elif query_type == "waste_policy":
        return {
            "policy": {
                "name": "NIT Hamirpur Campus Waste Management Policy",
                "waste_segregation": "3-bin system: Wet (Green), Dry (Blue), Hazardous (Red)",
                "collection_schedule": "Daily collection at 7 AM and 4 PM from all hostel zones",
                "waste_points": "3 main collection points across campus",
                "e_waste": "Dedicated e-waste collection drive every semester",
                "lab_waste": "Chemical waste handled by dedicated lab safety team",
                "composting": "Organic waste composting facility at campus garden",
                "awareness": "Monthly cleanliness drives organized by NSS and eco clubs",
                "penalties": "Fine of ₹500 for littering in campus premises",
                "reporting": "Report waste issues via EcoNITH portal for swift action",
            }
        }

    elif query_type == "facilities":
        return {
            "facilities": {
                "hostels": "9 hostels (7 boys, 2 girls) housing ~3000 students",
                "academic_blocks": "6 department buildings + Central Library",
                "messes": "2 messes (Mega Mess, Old Mess) serving 3000+ meals daily",
                "canteens": "Main Canteen (Maggi Point) + departmental canteens",
                "sports": "Cricket ground, basketball court, gym, football field",
                "waste_management": "3 collection points, 1 composting facility, designated e-waste storage",
                "green_cover": "40% campus area is green cover, includes Central Garden",
                "total_area": "320 acres campus in lower Himalayan region",
                "altitude": "900m above sea level",
            }
        }

    elif query_type == "statistics_summary":
        conn = get_db()
        stats = {
            "total_reports": conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
            "resolved_reports": conn.execute("SELECT COUNT(*) FROM reports WHERE status='resolved'").fetchone()[0],
            "pending_reports": conn.execute("SELECT COUNT(*) FROM reports WHERE status IN ('submitted','analyzing','analyzed','verified')").fetchone()[0],
            "active_hotspots": conn.execute("SELECT COUNT(*) FROM hotspots WHERE status='active'").fetchone()[0],
            "avg_severity": round(conn.execute("SELECT COALESCE(AVG(severity_score),0) FROM analysis_results").fetchone()[0], 1),
            "total_users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "waste_types_found": conn.execute("SELECT COUNT(DISTINCT waste_type_id) FROM analysis_results").fetchone()[0],
        }
        conn.close()
        return {"statistics": stats}

    elif query_type == "about":
        return {
            "about": {
                "name": "EcoNITH - AI-Powered Campus Environmental Management",
                "institution": "National Institute of Technology, Hamirpur (HP)",
                "established": "1986",
                "location": "Hamirpur, Himachal Pradesh, India (31.7082°N, 76.5274°E)",
                "mission": "Empower NIT Hamirpur students and administration to monitor, report, and resolve campus environmental issues using AI-driven insights.",
                "tech_stack": "FastAPI + Amazon Bedrock Nova-Pro + Next.js + SQLite + Folium",
                "features": [
                    "AI-powered waste image analysis",
                    "Autonomous agent chat with multi-tool orchestration",
                    "Campus hotspot detection and mapping",
                    "Trend analysis and data-driven recommendations",
                    "Student report submission with location tracking",
                ],
            }
        }

    return {"error": f"Unknown query type: {query_type}"}


# ──────────────────────────────────────────────────────
# Tool executor (maps tool name → function)
# ──────────────────────────────────────────────────────

TOOL_REGISTRY = {
    "execute_sql_query": execute_sql_query,
    "generate_chart": generate_chart,
    "generate_campus_map": generate_campus_map,
    "analyze_report_image": analyze_report_image,
    "get_campus_info": get_campus_info,
}


def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute a tool by name with given input."""
    func = TOOL_REGISTRY.get(tool_name)
    if not func:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return func(**tool_input)
    except TypeError as e:
        return {"error": f"Invalid arguments for {tool_name}: {str(e)}"}
    except Exception as e:
        return {"error": f"Tool execution error ({tool_name}): {str(e)}"}
