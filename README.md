# AgroPilot — Autonomous Sales Engineer (CPQ Agent Swarm) 🌾

**AgroPilot** is an advanced multi-agent artificial intelligence application engineered for Automated Agricultural Equipment Configuration, Pricing, and Quotation (CPQ). Built for the **AI Marathon 2026 (Problem Statement 1: The Autonomous Sales Engineer)**, AgroPilot ingests messy, unformatted, and unstructured inbound dealer or customer Request for Quote (RFQ) emails and orchestrates a stateful multi-agent swarm via **LangGraph** to construct an engineered, conflict-free Bill of Materials (BOM) and verified compliance audits in seconds.

---

## 🏗️ System Architecture & Workflow

AgroPilot operates as a deterministic state machine managed by a LangGraph workflow. The application features a 5-stage automated orchestration engine:

1. **RFQ Parser (Stage 1)**: Strips metadata, extraction properties, parameters, and constraints directly from raw unstructured texts.
2. **Configurator Agent (Stage 2)**: Engineers a matching Bill of Materials (BOM) by cross-referencing OEM specs, pricing models, and structural choices.
3. **Critic Agent (Stage 3 & 4)**: Reviews engineering compliance (e.g., checking for mechanical, engine, or hydraulic conflicts) and issues structural counter-recommendations to the Configurator in a correction feedback loop.
4. **Sentinel Agent (Stage 5)**: Scores deal health, financial risk parameters, gross margin baselines, historical conversion probabilities, and designs automated up-sell strategies.
5. **Human-In-The-Loop Approval**: Allows standard equipment dealers to inspect the workflow state, manually edit components, evaluate analytics metrics dashboards, and push downstream signals directly to client ecosystems.

---

## 💻 System Requirements & Dependencies

Ensure your execution environment matches the baseline operational specifications outlined below:

### 1. Environmental Thresholds
- **Operating System**: Cross-compatible across macOS (14+ Sonoma/Sequoia), Linux (Ubuntu 22.04 LTS+), or Windows 10/11.
- **Python Runtime Environment**: Version `3.10` or `3.11` (Strict Requirement).

### 2. Primary External Dependencies
The following core framework configurations are required and handled by your environment layer:
- `langgraph` (>=0.2.0) — Core multi-agent execution graphs
- `langchain-google-genai` (>=1.0.0) — LLM interface for the Gemini base engine
- `tavily-python` (>=0.3.0) — Dynamic compliance real-time verification engine
- `streamlit` (>=1.35.0) — High-end V3.0 Dark Dashboard UI panel interface
- `pandas` (>=2.0.0) — High-performance execution matrix dynamic visualization

---

## 🚀 Step-by-Step Installation & Local Setup

Execute the steps below in sequence within your local terminal environment to initialize and boot the application:

### Step 1: Clone the Repository
Clone your project repository down locally and change into the directory workspace root:

git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_LINK>
cd agropilot

### Step 2: Establish an Isolated Virtual Environment
Initialize a local runtime container to keep external package distributions clean and organized:

bash
# On macOS / Linux Systems:
python3 -m venv venv
source venv/bin/activate

# On Windows Systems (Command Prompt):
python -m venv venv
.\venv\Scripts\activate

# On Windows Systems (PowerShell):
python -m venv venv
.\venv\Scripts\Activate.ps1

### Step 3: Install Package Prerequisites
Leverage python's package manager dependency layout rules to bring down framework resources automatically:

Bash
pip install --upgrade pip
pip install -r requirements.txt
⚙️ Configuration & Token Isolation (.env)
AgroPilot securely decouples infrastructure execution codes from proprietary tokens using environment wrappers. The tracking layer enforces exclusion parameters through the project .gitignore file to ensure security tokens are never pushed to public version history nodes.

Generate a brand new environment token state configuration sheet directly within your project root root-path:

Bash
touch .env
Open your .env configuration text block using any text-editor workspace tool and structure it using this clear blueprint token format:

Code snippet
GOOGLE_API_KEY=YOUR_API_KEY_HERE
TAVILY_API_KEY=YOUR_TAVILY_API_KEY_HERE
⚠️ Evaluation Notice for Hackathon Judges: Replace the placeholders above with your personal GOOGLE_API_KEY obtained from Google AI Studio and an active TAVILY_API_KEY to run the agent search actions properly.

🖥️ Running the Application
AgroPilot can be verified through its terminal core emulation engine or natively within its premium V3.0 Dark Interactive Sales Dashboard.

Launching the Dashboard Panel (Recommended)
To start up the Streamlit-based dark UI dashboard overlay window, execute:

Bash
streamlit run app.py
Once tracking initialized, copy the generated local interface loopback address (typically http://localhost:8501) inside any standard web browser container.
