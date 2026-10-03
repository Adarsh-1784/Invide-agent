# EcoNITH - AI-Powered Campus Environmental Management

EcoNITH is an autonomous AI agent system for the National Institute of Technology, Hamirpur (HP), inspired by the AWS Hackathon winning project **EcoLafaek**. It transforms campus waste management through intelligent community engagement and advanced AI reasoning.

## 🌟 Key Features

- **Intelligent Waste Reporting**: Submit reports with images and geospatial locations across NIT Hamirpur.
- **Multi-Modal AI Image Analysis**: Powered by Amazon Bedrock Nova-Pro to automatically classify waste, assess severity, and determine environmental impact.
- **Autonomous AI Agent**: Natural language chat interface with a ReAct-style agent that can autonomously execute 5 tools:
  - Query the database via SQL
  - Generate data visualization charts
  - Create interactive Folium maps
  - Analyze waste images
  - Retrieve campus specific information
- **Campus Hotspot Detection**: Interactive map visualizing waste accumulation clusters.
- **Hacktoberfest Aesthetic**: Beautiful dark theme UI combining modern glassmorphism with Hacktoberfest's teal/coral color palette and NIT Hamirpur branding.

## 🏗️ Architecture

```
frontend/        # Next.js 15, React, Lucide-React, Leaflet
backend/         # FastAPI, SQLite, Amazon Bedrock (boto3), Matplotlib
```

- **Frontend**: Next.js dashboard providing an intuitive web interface for reporting, stats, and agent chat.
- **Backend API**: Python FastAPI server managing REST endpoints and static files.
- **Agent System**: Custom ReAct agent loop replacing AgentCore for easier local deployment, utilizing Amazon Nova-Pro.
- **Database**: SQLite containing 6 tables and 60+ seeded synthetic data points representing NIT Hamirpur (hostels, academic blocks, messes, etc.).

## 🚀 Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configuration & AWS Settings

Copy the example environment file:
```bash
cp .env.example .env
```

**AWS Requirements** (To use real AI features):
1. Add your AWS IAM credentials to `.env` (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
2. Ensure you have access to `amazon.nova-pro-v1:0` in Amazon Bedrock (usually `us-east-1`).
3. Set `DEMO_MODE=false`.

**Demo Mode**: 
If you don't have AWS credentials, simply leave `DEMO_MODE=true` in your `.env`. The app will function perfectly using rule-based synthetic responses, allowing you to test the UI, tools, and database without AWS!

### 3. Running the Server

Start the backend (generates SQLite DB and synthetic data on first run):
```bash
python main.py
```
*API will be available at http://localhost:8000*

### 4. Frontend Setup

In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
*Dashboard will be available at http://localhost:3000*

## 🤖 Testing the Agent

Go to the **Agent Chat** tab in the dashboard and try these queries:
- *"Show me a chart of waste types on campus"*
- *"Where are the worst waste hotspots? Put them on a map."*
- *"What is the distribution of report severity?"*
- *"Tell me about the waste management policy at NIT Hamirpur."*

## 📝 Demo vs Production Mode

| Feature | Demo Mode (`DEMO_MODE=true`) | Production Mode (`DEMO_MODE=false`) |
|---------|------------------------------|--------------------------------------|
| **Database/SQL Tool** | Real SQLite database & queries | Real SQLite database & queries |
| **Charts Tool** | Real Matplotlib generation | Real Matplotlib generation |
| **Maps Tool** | Real Folium map generation | Real Folium map generation |
| **Agent Reasoning** | Rule-based exact match routing | Amazon Nova-Pro ReAct reasoning |
| **Image Analysis** | Mocked synthetic responses | Real Nova-Pro Multimodal Vision |

## 🎓 NIT Hamirpur Adaptation

This is specifically built for NIT Hamirpur, featuring real campus locations (e.g., Kailash Hostel, Mega Mess, Computer Science Dept) seeded into the test database.
