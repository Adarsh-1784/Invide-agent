"""
EcoNITH Database - SQLite schema, seeding, and access functions.
Synthetic NIT Hamirpur campus data for waste/environmental reports.
"""
import sqlite3
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from config import DATABASE_PATH

# ─── NIT Hamirpur Campus Locations ──────────────────────────────────────
CAMPUS_LOCATIONS = [
    {"id": "hostel-kailash", "name": "Kailash Boys Hostel", "type": "hostel", "lat": 31.7095, "lng": 76.5268},
    {"id": "hostel-himadri", "name": "Himadri Boys Hostel", "type": "hostel", "lat": 31.7090, "lng": 76.5275},
    {"id": "hostel-dhauladhar", "name": "Dhauladhar Boys Hostel", "type": "hostel", "lat": 31.7088, "lng": 76.5260},
    {"id": "hostel-shivalik", "name": "Shivalik Boys Hostel", "type": "hostel", "lat": 31.7085, "lng": 76.5280},
    {"id": "hostel-pir-panjal", "name": "Pir Panjal Boys Hostel", "type": "hostel", "lat": 31.7078, "lng": 76.5272},
    {"id": "hostel-udaigiri", "name": "Udaigiri Boys Hostel", "type": "hostel", "lat": 31.7098, "lng": 76.5285},
    {"id": "hostel-satpura", "name": "Satpura Boys Hostel", "type": "hostel", "lat": 31.7082, "lng": 76.5290},
    {"id": "hostel-ambika", "name": "Ambika Girls Hostel", "type": "hostel", "lat": 31.7075, "lng": 76.5265},
    {"id": "hostel-manimahesh", "name": "Manimahesh Girls Hostel", "type": "hostel", "lat": 31.7072, "lng": 76.5258},
    {"id": "academic-main", "name": "Main Academic Block", "type": "academic", "lat": 31.7080, "lng": 76.5270},
    {"id": "academic-cse", "name": "CSE Department", "type": "academic", "lat": 31.7083, "lng": 76.5265},
    {"id": "academic-ece", "name": "ECE Department", "type": "academic", "lat": 31.7081, "lng": 76.5262},
    {"id": "academic-eee", "name": "EEE Department", "type": "academic", "lat": 31.7079, "lng": 76.5258},
    {"id": "academic-me", "name": "Mechanical Engg. Department", "type": "academic", "lat": 31.7077, "lng": 76.5275},
    {"id": "academic-ce", "name": "Civil Engg. Department", "type": "academic", "lat": 31.7076, "lng": 76.5282},
    {"id": "library", "name": "Central Library", "type": "academic", "lat": 31.7084, "lng": 76.5278},
    {"id": "mess-mega", "name": "Mega Mess", "type": "mess", "lat": 31.7092, "lng": 76.5270},
    {"id": "mess-old", "name": "Old Mess", "type": "mess", "lat": 31.7087, "lng": 76.5267},
    {"id": "canteen-main", "name": "Main Canteen (Maggi Point)", "type": "canteen", "lat": 31.7086, "lng": 76.5273},
    {"id": "sports-ground", "name": "Sports Ground", "type": "facility", "lat": 31.7070, "lng": 76.5270},
    {"id": "gym-fitness", "name": "Gymnasium & Fitness Center", "type": "facility", "lat": 31.7068, "lng": 76.5275},
    {"id": "admin-block", "name": "Administrative Block", "type": "admin", "lat": 31.7082, "lng": 76.5255},
    {"id": "workshop", "name": "Central Workshop", "type": "facility", "lat": 31.7074, "lng": 76.5288},
    {"id": "road-main", "name": "Main Campus Road", "type": "road", "lat": 31.7080, "lng": 76.5272},
    {"id": "road-hostel", "name": "Hostel Road", "type": "road", "lat": 31.7090, "lng": 76.5278},
    {"id": "parking-main", "name": "Main Parking Area", "type": "facility", "lat": 31.7078, "lng": 76.5250},
    {"id": "garden-central", "name": "Central Garden", "type": "facility", "lat": 31.7082, "lng": 76.5270},
    {"id": "waste-collection-1", "name": "Waste Collection Point - Hostel Zone", "type": "waste_point", "lat": 31.7093, "lng": 76.5272},
    {"id": "waste-collection-2", "name": "Waste Collection Point - Academic Zone", "type": "waste_point", "lat": 31.7079, "lng": 76.5265},
    {"id": "waste-collection-3", "name": "Waste Collection Point - Mess Area", "type": "waste_point", "lat": 31.7089, "lng": 76.5268},
]

WASTE_TYPES = [
    {"id": 1, "name": "Plastic", "description": "Plastic bottles, bags, wrappers, packaging", "hazard_level": "medium", "recyclable": True},
    {"id": 2, "name": "Paper", "description": "Notebooks, printouts, packaging, cardboard", "hazard_level": "low", "recyclable": True},
    {"id": 3, "name": "Organic", "description": "Food waste, mess leftovers, garden waste", "hazard_level": "low", "recyclable": False},
    {"id": 4, "name": "Electronic", "description": "E-waste, batteries, cables, old devices", "hazard_level": "high", "recyclable": True},
    {"id": 5, "name": "Metal", "description": "Cans, foil, broken equipment parts", "hazard_level": "medium", "recyclable": True},
    {"id": 6, "name": "Glass", "description": "Bottles, broken lab glass, window panes", "hazard_level": "high", "recyclable": True},
    {"id": 7, "name": "Construction", "description": "Debris, bricks, cement, renovation waste", "hazard_level": "medium", "recyclable": False},
    {"id": 8, "name": "Hazardous", "description": "Lab chemicals, paint, solvents", "hazard_level": "high", "recyclable": False},
    {"id": 9, "name": "Mixed", "description": "Mixed unsorted waste", "hazard_level": "medium", "recyclable": False},
]

REPORT_DESCRIPTIONS = [
    "Overflowing dustbin near {location}. Mostly plastic wrappers and bottles.",
    "Large pile of mess food waste dumped behind {location}. Attracting stray animals.",
    "Broken glass and e-waste found near {location}. Safety hazard for students.",
    "Paper and cardboard waste scattered around {location} after fest event cleanup.",
    "Construction debris left unattended near {location}. Blocking the pathway.",
    "Plastic bottles and Maggi cups littered around {location}. Needs cleanup.",
    "Old furniture and electronic items dumped near {location}.",
    "Mixed waste accumulation near {location}. No segregation done.",
    "Food waste from mess kitchen dumped in open area near {location}.",
    "Chemical waste containers found near {location}. Lab disposal issue.",
    "Plastic bags and food packaging piled up near {location} dustbin.",
    "Scattered paper waste from recent examination near {location}.",
    "Overflowing garbage bin at {location}. Not collected for 3 days.",
    "Electronic components and batteries found discarded near {location}.",
    "Garden waste and tree branches blocking path near {location}.",
]

STUDENT_NAMES = [
    "Aarav Sharma", "Priya Thakur", "Rohit Verma", "Sneha Chauhan", "Amit Kumar",
    "Neha Singh", "Vikram Rajput", "Anjali Devi", "Karan Mehta", "Pooja Negi",
    "Ravi Pathania", "Divya Kaundal", "Saurabh Rana", "Megha Pandit", "Arjun Dhiman",
    "Sakshi Gupta", "Deepak Thakur", "Ritika Bhardwaj", "Manish Katoch", "Tanvi Sharma",
]


def get_db():
    """Get database connection. Creates DB if not exists."""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS waste_types (
        waste_type_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        hazard_level TEXT CHECK(hazard_level IN ('low','medium','high')) DEFAULT 'low',
        recyclable BOOLEAN DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS campus_locations (
        location_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        full_name TEXT,
        email TEXT,
        role TEXT CHECK(role IN ('student','staff','admin')) DEFAULT 'student',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        user_id TEXT REFERENCES users(user_id),
        location_id TEXT REFERENCES campus_locations(location_id),
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        description TEXT,
        image_url TEXT,
        status TEXT CHECK(status IN ('submitted','analyzing','analyzed','verified','resolved','rejected')) DEFAULT 'submitted',
        report_date TEXT DEFAULT (datetime('now')),
        address_text TEXT
    );

    CREATE TABLE IF NOT EXISTS analysis_results (
        analysis_id TEXT PRIMARY KEY,
        report_id TEXT REFERENCES reports(report_id) ON DELETE CASCADE,
        waste_type_id INTEGER REFERENCES waste_types(waste_type_id),
        confidence_score REAL,
        severity_score INTEGER CHECK(severity_score BETWEEN 1 AND 10),
        priority_level TEXT CHECK(priority_level IN ('low','medium','high','critical')),
        environmental_impact TEXT,
        safety_concerns TEXT,
        estimated_volume TEXT,
        full_description TEXT,
        analyzed_date TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS hotspots (
        hotspot_id TEXT PRIMARY KEY,
        location_id TEXT REFERENCES campus_locations(location_id),
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        report_count INTEGER DEFAULT 0,
        avg_severity REAL DEFAULT 0,
        predominant_waste TEXT,
        last_updated TEXT DEFAULT (datetime('now')),
        status TEXT CHECK(status IN ('active','monitored','resolved')) DEFAULT 'active'
    );

    CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
    CREATE INDEX IF NOT EXISTS idx_reports_location ON reports(location_id);
    CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(report_date);
    CREATE INDEX IF NOT EXISTS idx_analysis_waste_type ON analysis_results(waste_type_id);
    CREATE INDEX IF NOT EXISTS idx_analysis_severity ON analysis_results(severity_score);
    """)

    conn.commit()
    conn.close()
    print("[DB] Schema initialized.")


def seed_data():
    """Seed database with synthetic NIT Hamirpur data."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if already seeded
    row = cursor.execute("SELECT COUNT(*) FROM reports").fetchone()
    if row[0] > 0:
        print(f"[DB] Already seeded ({row[0]} reports). Skipping.")
        conn.close()
        return

    # Seed waste types
    for wt in WASTE_TYPES:
        cursor.execute(
            "INSERT OR IGNORE INTO waste_types (waste_type_id, name, description, hazard_level, recyclable) VALUES (?,?,?,?,?)",
            (wt["id"], wt["name"], wt["description"], wt["hazard_level"], wt["recyclable"])
        )

    # Seed campus locations
    for loc in CAMPUS_LOCATIONS:
        cursor.execute(
            "INSERT OR IGNORE INTO campus_locations (location_id, name, type, latitude, longitude) VALUES (?,?,?,?,?)",
            (loc["id"], loc["name"], loc["type"], loc["lat"], loc["lng"])
        )

    # Seed users
    user_ids = []
    for i, name in enumerate(STUDENT_NAMES):
        uid = str(uuid.uuid4())
        user_ids.append(uid)
        username = name.lower().replace(" ", ".") + str(random.randint(10, 99))
        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name, email, role) VALUES (?,?,?,?,?)",
            (uid, username, name, f"{username}@nith.ac.in", "student")
        )

    # Seed reports (60 reports over last 90 days)
    now = datetime.now()
    report_ids = []
    for i in range(60):
        rid = str(uuid.uuid4())
        report_ids.append(rid)
        loc = random.choice(CAMPUS_LOCATIONS)
        user_id = random.choice(user_ids)
        days_ago = random.randint(0, 90)
        report_date = (now - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
        desc_template = random.choice(REPORT_DESCRIPTIONS)
        description = desc_template.format(location=loc["name"])

        # Add slight coordinate jitter
        lat = loc["lat"] + random.uniform(-0.0005, 0.0005)
        lng = loc["lng"] + random.uniform(-0.0005, 0.0005)

        status = random.choices(
            ["submitted", "analyzed", "verified", "resolved", "rejected"],
            weights=[15, 25, 30, 25, 5],
            k=1
        )[0]

        cursor.execute(
            """INSERT INTO reports (report_id, user_id, location_id, latitude, longitude,
               description, status, report_date, address_text)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (rid, user_id, loc["id"], lat, lng, description, status,
             report_date, f"{loc['name']}, NIT Hamirpur Campus")
        )

    # Seed analysis results for analyzed/verified/resolved reports
    for rid in report_ids:
        row = cursor.execute("SELECT status, location_id FROM reports WHERE report_id=?", (rid,)).fetchone()
        if row and row[0] in ("analyzed", "verified", "resolved"):
            wt = random.choice(WASTE_TYPES)
            severity = random.randint(1, 10)
            priority_map = {range(1, 4): "low", range(4, 7): "medium", range(7, 9): "high", range(9, 11): "critical"}
            priority = "medium"
            for r, p in priority_map.items():
                if severity in r:
                    priority = p
                    break

            impacts = [
                "Soil contamination risk. May attract pests.",
                "Water drainage blockage potential. Breeding ground for mosquitoes.",
                "Air quality concern due to decomposition. Unpleasant odor.",
                "Chemical leaching risk to groundwater. Safety hazard.",
                "Aesthetic degradation of campus environment. Student wellbeing impact.",
                "Fire hazard from dry waste accumulation near buildings.",
            ]

            cursor.execute(
                """INSERT INTO analysis_results
                   (analysis_id, report_id, waste_type_id, confidence_score, severity_score,
                    priority_level, environmental_impact, safety_concerns, estimated_volume, full_description)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), rid, wt["id"],
                    round(random.uniform(70, 98), 1), severity, priority,
                    random.choice(impacts),
                    random.choice(["Sharp objects present", "Chemical exposure risk", "Tripping hazard", "None significant", "Pest infestation risk"]),
                    random.choice(["~5 kg", "~10 kg", "~20 kg", "~50 kg", "~1 bag", "~2-3 bags", "Large pile"]),
                    f"AI analysis detected {wt['name'].lower()} waste with severity {severity}/10. "
                    f"Location: {row[1]}. Priority: {priority}."
                )
            )

    # Seed hotspots (computed from report density)
    hotspot_locations = ["hostel-kailash", "mess-mega", "canteen-main", "road-main",
                         "hostel-himadri", "academic-main", "waste-collection-1"]
    for loc_id in hotspot_locations:
        loc = next((l for l in CAMPUS_LOCATIONS if l["id"] == loc_id), None)
        if loc:
            count = cursor.execute(
                "SELECT COUNT(*) FROM reports WHERE location_id=?", (loc_id,)
            ).fetchone()[0]
            avg_sev = cursor.execute(
                """SELECT COALESCE(AVG(ar.severity_score), 5) FROM reports r
                   JOIN analysis_results ar ON r.report_id = ar.report_id
                   WHERE r.location_id=?""", (loc_id,)
            ).fetchone()[0]

            if count == 0:
                count = random.randint(3, 12)
                avg_sev = random.uniform(4, 8)

            cursor.execute(
                """INSERT OR IGNORE INTO hotspots
                   (hotspot_id, location_id, latitude, longitude, report_count, avg_severity, predominant_waste, status)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), loc_id, loc["lat"], loc["lng"],
                 count, round(avg_sev, 1),
                 random.choice(["Plastic", "Organic", "Mixed", "Paper"]),
                 random.choice(["active", "monitored"]))
            )

    conn.commit()
    conn.close()
    print("[DB] Seeded 60 synthetic reports across NIT Hamirpur campus.")


if __name__ == "__main__":
    init_db()
    seed_data()
