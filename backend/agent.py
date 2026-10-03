"""
EcoNITH Agent — ReAct-style autonomous agent with multi-round tool calling.
Uses Amazon Bedrock Nova-Pro for reasoning. Falls back to demo mode.

Agent Workflow:
1. Receive user message + conversation history
2. Build system prompt with tool definitions
3. Send to LLM → get response (text or tool_use)
4. If tool_use → execute tool → feed result back → loop
5. Continue until final text answer (max 8 rounds)
"""
import json
import re
import random
from datetime import datetime

from config import get_bedrock_client, BEDROCK_MODEL_ID, DEMO_MODE
from tools import TOOL_DEFINITIONS, execute_tool

MAX_ROUNDS = 8

SYSTEM_PROMPT = """You are EcoNITH Agent, an AI assistant for the NIT Hamirpur Campus Environmental Management System.

Your job is to help students and administrators with waste management queries about NIT Hamirpur campus.

You have access to the following tools:

{tool_descriptions}

## How to use tools
When you need data, generate a chart, create a map, or analyze an image, call the appropriate tool.
You can chain multiple tools in sequence. For example:
1. First use execute_sql_query to get data
2. Then use generate_chart to visualize it
3. Then use generate_campus_map to show locations

## Important rules
- Always use execute_sql_query to get REAL data before making claims about statistics
- When generating charts, first query the data, then pass the results to generate_chart
- For maps, query location data first, then pass to generate_campus_map
- Provide clear, helpful answers with data-backed insights
- Always mention the source of your data (e.g., "Based on our database of 60 reports...")
- Be specific about NIT Hamirpur locations (hostels, departments, messes, etc.)
- When showing charts or maps, include the URL so the frontend can render them
- Format responses in clean markdown

## Database Schema
Tables: reports, analysis_results, waste_types, campus_locations, hotspots, users
Key columns:
- reports: report_id, location_id, status, description, report_date, latitude, longitude
- analysis_results: waste_type_id, severity_score, priority_level, confidence_score
- waste_types: name, hazard_level, recyclable
- campus_locations: name, type (hostel/academic/mess/canteen/facility/road/waste_point)
- hotspots: report_count, avg_severity, predominant_waste, status

Current date: {current_date}
"""


def build_system_prompt() -> str:
    """Build the system prompt with tool descriptions."""
    tool_desc = json.dumps(TOOL_DEFINITIONS, indent=2)
    return SYSTEM_PROMPT.format(
        tool_descriptions=tool_desc,
        current_date=datetime.now().strftime("%Y-%m-%d")
    )


def run_agent_bedrock(user_message: str, conversation_history: list = None) -> dict:
    """Run the agent using Amazon Bedrock Nova-Pro."""
    client = get_bedrock_client()
    if not client:
        return run_agent_demo(user_message)

    system_prompt = build_system_prompt()
    messages = []

    # Add conversation history
    if conversation_history:
        for msg in conversation_history[-6:]:  # Keep last 6 messages
            messages.append({
                "role": msg.get("role", "user"),
                "content": [{"text": msg.get("content", "")}]
            })

    # Add current user message
    messages.append({
        "role": "user",
        "content": [{"text": user_message}]
    })

    tool_calls_made = []
    final_response = ""

    for round_num in range(1, MAX_ROUNDS + 1):
        try:
            # Build Bedrock request with tool config
            bedrock_tools = []
            for tool_def in TOOL_DEFINITIONS:
                bedrock_tools.append({
                    "toolSpec": {
                        "name": tool_def["name"],
                        "description": tool_def["description"],
                        "inputSchema": {
                            "json": tool_def["input_schema"]
                        }
                    }
                })

            body = {
                "system": [{"text": system_prompt}],
                "messages": messages,
                "inferenceConfig": {
                    "temperature": 0.3,
                    "maxTokens": 4096,
                },
                "toolConfig": {
                    "tools": bedrock_tools
                }
            }

            response = client.converse(
                modelId=BEDROCK_MODEL_ID,
                **body
            )

            output = response.get("output", {}).get("message", {})
            stop_reason = response.get("stopReason", "")
            content_blocks = output.get("content", [])

            # Add assistant message to conversation
            messages.append({"role": "assistant", "content": content_blocks})

            # Check if the model wants to use a tool
            if stop_reason == "tool_use":
                tool_results = []
                for block in content_blocks:
                    if "toolUse" in block:
                        tool_use = block["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use.get("input", {})
                        tool_id = tool_use.get("toolUseId", f"tool_{round_num}")

                        print(f"  [Agent Round {round_num}] Calling tool: {tool_name}")
                        print(f"    Input: {json.dumps(tool_input)[:200]}")

                        # Execute the tool
                        result = execute_tool(tool_name, tool_input)
                        tool_calls_made.append({
                            "round": round_num,
                            "tool": tool_name,
                            "input": tool_input,
                            "output_summary": str(result)[:200]
                        })

                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_id,
                                "content": [{"json": result}]
                            }
                        })

                # Add tool results back
                messages.append({"role": "user", "content": tool_results})
                continue

            # Final text response
            for block in content_blocks:
                if "text" in block:
                    final_response += block["text"]

            break

        except Exception as e:
            print(f"  [Agent Error] Round {round_num}: {str(e)}")
            if round_num == 1:
                # If first round fails, fallback to demo
                return run_agent_demo(user_message)
            break

    return {
        "response": final_response or "I apologize, I couldn't generate a response. Please try again.",
        "tool_calls": tool_calls_made,
        "rounds": len(tool_calls_made) + 1,
        "mode": "bedrock"
    }


def run_agent_demo(user_message: str) -> dict:
    """Demo mode agent — uses rule-based tool routing with real tool execution."""
    msg_lower = user_message.lower()
    tool_calls_made = []
    response_parts = []
    charts = []
    maps = []

    # ── Detect intent and route to tools ──

    # Statistics / trends queries
    if any(kw in msg_lower for kw in ["statistic", "stats", "summary", "overview", "how many", "total", "count"]):
        # Tool 1: Get stats from DB
        result = execute_tool("get_campus_info", {"query_type": "statistics_summary"})
        tool_calls_made.append({"round": 1, "tool": "get_campus_info", "input": {"query_type": "statistics_summary"}})
        stats = result.get("statistics", {})

        # Tool 2: Get waste type breakdown
        sql_result = execute_tool("execute_sql_query", {
            "query": """SELECT wt.name, COUNT(*) as count FROM analysis_results ar
                        JOIN waste_types wt ON ar.waste_type_id = wt.waste_type_id
                        GROUP BY wt.name ORDER BY count DESC"""
        })
        tool_calls_made.append({"round": 2, "tool": "execute_sql_query"})

        # Tool 3: Generate chart
        if sql_result.get("rows"):
            labels = [r["name"] for r in sql_result["rows"]]
            values = [r["count"] for r in sql_result["rows"]]
            chart_result = execute_tool("generate_chart", {
                "chart_type": "bar",
                "title": "Waste Type Distribution at NIT Hamirpur",
                "labels": labels,
                "values": values,
                "xlabel": "Waste Type",
                "ylabel": "Number of Reports"
            })
            tool_calls_made.append({"round": 3, "tool": "generate_chart"})
            if "chart_url" in chart_result:
                charts.append(chart_result["chart_url"])

        response_parts.append(f"""## 📊 NIT Hamirpur Campus Environmental Statistics

| Metric | Value |
|--------|-------|
| Total Reports | {stats.get('total_reports', 0)} |
| Resolved | {stats.get('resolved_reports', 0)} |
| Pending | {stats.get('pending_reports', 0)} |
| Active Hotspots | {stats.get('active_hotspots', 0)} |
| Average Severity | {stats.get('avg_severity', 0)}/10 |
| Contributing Users | {stats.get('total_users', 0)} |

### Waste Type Breakdown""")
        if charts:
            response_parts.append(f"![Waste Type Chart]({charts[0]})")

    # Map / hotspot queries
    elif any(kw in msg_lower for kw in ["map", "hotspot", "location", "where", "spatial", "area", "zone"]):
        # Tool 1: Get hotspot data
        sql_result = execute_tool("execute_sql_query", {
            "query": """SELECT h.latitude, h.longitude, cl.name, h.report_count,
                        h.avg_severity, h.predominant_waste, h.status
                        FROM hotspots h
                        JOIN campus_locations cl ON h.location_id = cl.location_id
                        ORDER BY h.avg_severity DESC"""
        })
        tool_calls_made.append({"round": 1, "tool": "execute_sql_query"})

        markers = []
        if sql_result.get("rows"):
            for row in sql_result["rows"]:
                markers.append({
                    "lat": row["latitude"],
                    "lng": row["longitude"],
                    "label": row["name"],
                    "severity": round(row["avg_severity"]),
                    "info": f"Reports: {row['report_count']} | Waste: {row['predominant_waste']} | Status: {row['status']}"
                })

        # Tool 2: Generate map
        if markers:
            map_result = execute_tool("generate_campus_map", {
                "markers": markers,
                "title": "NIT Hamirpur Waste Hotspots",
                "show_heatmap": True
            })
            tool_calls_made.append({"round": 2, "tool": "generate_campus_map"})
            if "map_url" in map_result:
                maps.append(map_result["map_url"])

        response_parts.append("## 🗺️ Campus Waste Hotspot Map\n")
        if maps:
            response_parts.append(f"[View Interactive Map]({maps[0]})\n")
        response_parts.append("### Top Hotspots\n")
        if sql_result.get("rows"):
            for i, row in enumerate(sql_result["rows"][:5], 1):
                severity_emoji = "🔴" if row["avg_severity"] >= 7 else "🟡" if row["avg_severity"] >= 4 else "🟢"
                response_parts.append(
                    f"{i}. {severity_emoji} **{row['name']}** — Severity: {row['avg_severity']:.1f}/10, "
                    f"Reports: {row['report_count']}, Type: {row['predominant_waste']}"
                )

    # Chart / visualization queries
    elif any(kw in msg_lower for kw in ["chart", "graph", "visualiz", "trend", "breakdown", "plot"]):
        # Determine what to chart
        if "severity" in msg_lower:
            sql_result = execute_tool("execute_sql_query", {
                "query": """SELECT
                    CASE WHEN severity_score <= 3 THEN 'Low (1-3)'
                         WHEN severity_score <= 6 THEN 'Medium (4-6)'
                         WHEN severity_score <= 8 THEN 'High (7-8)'
                         ELSE 'Critical (9-10)' END as level,
                    COUNT(*) as count
                    FROM analysis_results GROUP BY level ORDER BY MIN(severity_score)"""
            })
            chart_title = "Report Severity Distribution"
        elif "location" in msg_lower or "hostel" in msg_lower or "area" in msg_lower:
            sql_result = execute_tool("execute_sql_query", {
                "query": """SELECT cl.name, COUNT(*) as count FROM reports r
                            JOIN campus_locations cl ON r.location_id = cl.location_id
                            GROUP BY cl.name ORDER BY count DESC LIMIT 10"""
            })
            chart_title = "Reports by Campus Location (Top 10)"
        elif "status" in msg_lower:
            sql_result = execute_tool("execute_sql_query", {
                "query": "SELECT status, COUNT(*) as count FROM reports GROUP BY status ORDER BY count DESC"
            })
            chart_title = "Report Status Distribution"
        elif "month" in msg_lower or "time" in msg_lower or "trend" in msg_lower:
            sql_result = execute_tool("execute_sql_query", {
                "query": """SELECT strftime('%Y-%m', report_date) as month, COUNT(*) as count
                            FROM reports GROUP BY month ORDER BY month"""
            })
            chart_title = "Monthly Report Trends"
        else:
            sql_result = execute_tool("execute_sql_query", {
                "query": """SELECT wt.name, COUNT(*) as count FROM analysis_results ar
                            JOIN waste_types wt ON ar.waste_type_id = wt.waste_type_id
                            GROUP BY wt.name ORDER BY count DESC"""
            })
            chart_title = "Waste Type Distribution"

        tool_calls_made.append({"round": 1, "tool": "execute_sql_query"})

        if sql_result.get("rows"):
            cols = sql_result["columns"]
            label_col = cols[0]
            value_col = cols[1]
            labels = [str(r[label_col]) for r in sql_result["rows"]]
            values = [r[value_col] for r in sql_result["rows"]]

            chart_type = "pie" if "pie" in msg_lower else "line" if "trend" in msg_lower or "month" in msg_lower else "bar"
            chart_result = execute_tool("generate_chart", {
                "chart_type": chart_type,
                "title": chart_title,
                "labels": labels,
                "values": values,
            })
            tool_calls_made.append({"round": 2, "tool": "generate_chart"})
            if "chart_url" in chart_result:
                charts.append(chart_result["chart_url"])

        response_parts.append(f"## 📈 {chart_title}\n")
        if charts:
            response_parts.append(f"![Chart]({charts[0]})\n")
        if sql_result.get("rows"):
            response_parts.append("### Data\n| Category | Count |\n|----------|-------|\n")
            for r in sql_result["rows"]:
                vals = list(r.values())
                response_parts.append(f"| {vals[0]} | {vals[1]} |")

    # Waste type queries
    elif any(kw in msg_lower for kw in ["waste type", "plastic", "organic", "electronic", "hazardous", "recycle"]):
        sql_result = execute_tool("execute_sql_query", {
            "query": """SELECT wt.name, wt.description, wt.hazard_level, wt.recyclable,
                        COUNT(ar.analysis_id) as report_count,
                        COALESCE(AVG(ar.severity_score), 0) as avg_severity
                        FROM waste_types wt
                        LEFT JOIN analysis_results ar ON wt.waste_type_id = ar.waste_type_id
                        GROUP BY wt.waste_type_id ORDER BY report_count DESC"""
        })
        tool_calls_made.append({"round": 1, "tool": "execute_sql_query"})

        response_parts.append("## ♻️ Waste Types at NIT Hamirpur\n")
        if sql_result.get("rows"):
            response_parts.append("| Type | Hazard | Recyclable | Reports | Avg Severity |\n|------|--------|------------|---------|-------------|")
            for r in sql_result["rows"]:
                recycle = "✅" if r["recyclable"] else "❌"
                response_parts.append(
                    f"| {r['name']} | {r['hazard_level']} | {recycle} | {r['report_count']} | {r['avg_severity']:.1f} |"
                )

    # Campus info queries
    elif any(kw in msg_lower for kw in ["campus", "nith", "nit hamirpur", "about", "policy", "facili"]):
        query_type = "about"
        if "policy" in msg_lower or "rule" in msg_lower:
            query_type = "waste_policy"
        elif "facili" in msg_lower or "infrastr" in msg_lower:
            query_type = "facilities"

        result = execute_tool("get_campus_info", {"query_type": query_type})
        tool_calls_made.append({"round": 1, "tool": "get_campus_info", "input": {"query_type": query_type}})

        data = result.get(query_type, result.get("about", result.get("policy", result.get("facilities", {}))))
        response_parts.append(f"## 🏫 NIT Hamirpur — {query_type.replace('_', ' ').title()}\n")
        if isinstance(data, dict):
            for key, val in data.items():
                if isinstance(val, list):
                    response_parts.append(f"**{key.replace('_', ' ').title()}:**")
                    for item in val:
                        response_parts.append(f"- {item}")
                else:
                    response_parts.append(f"**{key.replace('_', ' ').title()}:** {val}")

    # Default / general query
    else:
        # Try to be helpful with stats
        result = execute_tool("get_campus_info", {"query_type": "statistics_summary"})
        tool_calls_made.append({"round": 1, "tool": "get_campus_info"})
        stats = result.get("statistics", {})

        response_parts.append(f"""## 🌿 EcoNITH — Campus Environmental Assistant

I'm your AI assistant for NIT Hamirpur's campus environmental management. Here's what I can help with:

- 📊 **Statistics**: "Show me campus waste statistics"
- 📈 **Charts**: "Generate a chart of waste types" or "Show severity trends"
- 🗺️ **Maps**: "Show campus waste hotspots on a map"
- ♻️ **Waste Info**: "What waste types are most common?"
- 🏫 **Campus**: "Tell me about NIT Hamirpur waste policy"
- 📸 **Analysis**: Submit a report with an image for AI analysis

### Quick Stats
- **{stats.get('total_reports', 0)}** total reports filed
- **{stats.get('resolved_reports', 0)}** issues resolved
- **{stats.get('active_hotspots', 0)}** active hotspots

Ask me anything about campus waste management!""")

    return {
        "response": "\n".join(response_parts),
        "tool_calls": tool_calls_made,
        "rounds": len(tool_calls_made),
        "charts": charts,
        "maps": maps,
        "mode": "demo"
    }


def run_agent(user_message: str, conversation_history: list = None) -> dict:
    """Main agent entry point. Uses Bedrock if configured, else demo mode."""
    print(f"\n[Agent] Query: {user_message[:100]}")

    if DEMO_MODE or not get_bedrock_client():
        print("[Agent] Running in DEMO mode")
        return run_agent_demo(user_message)
    else:
        print("[Agent] Running with Amazon Bedrock")
        return run_agent_bedrock(user_message, conversation_history)
