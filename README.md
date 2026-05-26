# AgroPilot — Autonomous Sales Engineer (CPQ Agent Swarm) 🌾

**AgroPilot** is an advanced multi-agent artificial intelligence platform engineered for automated Agricultural Equipment Configuration, Pricing, and Quotation (CPQ).

Built for the **AI Marathon 2026** *(Problem Statement 1: The Autonomous Sales Engineer)*, AgroPilot ingests messy, unformatted, and unstructured inbound dealer or customer Request for Quote (RFQ) emails and orchestrates a stateful multi-agent swarm using **LangGraph** to construct an engineered, conflict-free Bill of Materials (BOM) and verified compliance audits within seconds. 

---

# 🏗️ System Architecture & Workflow

AgroPilot operates as a deterministic state machine managed through a LangGraph workflow. The platform features a 5-stage automated orchestration engine:

## 1️⃣ RFQ Parser (Stage 1)

* Cleans and strips metadata from raw RFQ emails
* Extracts properties, parameters, constraints, and customer requirements
* Converts unstructured text into structured machine-readable data

## 2️⃣ Configurator Agent (Stage 2)

* Engineers a matching Bill of Materials (BOM)
* Cross-references OEM specifications and pricing models
* Generates optimized equipment configurations

## 3️⃣ Critic Agent (Stages 3 & 4)

* Reviews engineering compliance and mechanical compatibility
* Detects hydraulic, engine, or structural conflicts
* Provides correction feedback loops to the Configurator Agent

## 4️⃣ Sentinel Agent (Stage 5)

* Evaluates deal health and financial risk
* Scores gross margin baselines
* Predicts historical conversion probabilities
* Generates intelligent automated up-sell strategies

## 5️⃣ Human-In-The-Loop Approval

* Allows equipment dealers to inspect workflow states
* Supports manual editing and overrides
* Provides analytics dashboards and workflow visibility
* Enables downstream integrations with client ecosystems

---

# 💻 System Requirements

## 🖥️ Supported Operating Systems

* macOS 14+ (Sonoma / Sequoia)
* Ubuntu 22.04 LTS+
* Windows 10 / 11

## 🐍 Python Version

* Python `3.10` or `3.11` (**strict requirement**)

---

# 📦 Dependencies

The following core frameworks are required and managed through `requirements.txt`:

```txt
langgraph>=0.2.0
langchain-google-genai>=1.0.0
langchain-core>=0.2.0
tavily-python>=0.3.0
python-dotenv>=1.0.0
streamlit>=1.35.0
pandas>=2.0.0
```

### Dependency Overview

| Package                  | Purpose                                |
| ------------------------ | -------------------------------------- |
| `langgraph`              | Multi-agent execution orchestration    |
| `langchain-google-genai` | Gemini LLM integration                 |
| `langchain-core`         | Message and state abstraction          |
| `tavily-python`          | Real-time compliance verification      |
| `python-dotenv`          | Secure environment variable management |
| `streamlit`              | Interactive dashboard UI               |
| `pandas`                 | Data processing and visualization      |

---

# 🚀 Installation & Local Setup

Follow the steps below to initialize AgroPilot locally.

---

## Step 1 — Clone the Repository

```bash
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_LINK>
cd AgroPilot
```

---

## Step 2 — Create a Virtual Environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows (Command Prompt)

```bash
python -m venv venv
.\venv\Scripts\activate
```

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

---

## Step 3 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

# ⚙️ Environment Configuration

AgroPilot uses environment variables to securely isolate API credentials and infrastructure tokens.

Create a `.env` file inside the project root:

```bash
touch .env
```

Add the following configuration:

```env
GOOGLE_API_KEY=YOUR_API_KEY_HERE
TAVILY_API_KEY=YOUR_TAVILY_API_KEY_HERE
```

> ⚠️ **Hackathon Evaluation Notice**
> Replace the placeholders above with:
>
> * A valid `GOOGLE_API_KEY` from Google AI Studio
> * An active `TAVILY_API_KEY`
>
> These keys are required for agent orchestration and real-time search verification.

---

# 🖥️ Running the Application

AgroPilot supports both:

* Terminal-based execution
* Interactive Streamlit dashboard mode

---

## 🌟 Launch the Dashboard (Recommended)

Start the Streamlit dashboard:

```bash
streamlit run app.py
```

Once initialized, open the generated local URL in your browser:

```txt
http://localhost:8501
```

---

# ✨ Key Features

* 🤖 Multi-agent CPQ automation
* 🌾 Agricultural equipment configuration engine
* 📧 Unstructured RFQ parsing
* 🧠 Engineering compliance verification
* 📊 Deal risk and margin analysis
* 🔄 Stateful LangGraph orchestration
* 🖥️ Interactive Streamlit dashboard
* 👨‍💻 Human-in-the-loop validation workflow

---

# 🧩 Tech Stack

| Layer               | Technology |
| ------------------- | ---------- |
| Agent Orchestration | LangGraph  |
| LLM Engine          | Gemini     |
| Backend Framework   | LangChain  |
| Search Verification | Tavily     |
| Dashboard UI        | Streamlit  |
| Data Processing     | Pandas     |

---

# 📌 Project Context

AgroPilot was developed for:

**AI Marathon 2026 — Problem Statement 1: The Autonomous Sales Engineer**

The project focuses on automating complex agricultural equipment sales engineering workflows through intelligent multi-agent systems.

---

# 📄 License

This project is intended for educational, research, and hackathon demonstration purposes.

