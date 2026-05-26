# AgriQuote — Autonomous Sales Engineer (CPQ Swarm) 🌾

AgriQuote is an autonomous, multi-agent sales engineering platform designed for Agricultural Equipment & Precision Farming CPQ (Configure, Price, Quote). Built using **LangGraph** and powered by **Gemini**, the system acts as an expert full-stack sales operator that ingests unstructured, messy dealer RFQ emails and generates validated, conflict-free commercial quotes in seconds.

---

## 🛠️ System Requirements & Dependencies

Ensure you have the following prerequisites installed on your local machine:

- **Operating System**: Windows 11, macOS (14+), or Linux (Ubuntu 22.04+)
- **Python**: version `3.10` or `3.11` (Recommended)
- **Package Manager**: `pip` (included with Python)

### Core Framework Dependencies
- `streamlit` (Premium Dark UI layout engine)
- `langgraph` (Multi-agent stateful orchestration graph)
- `langchain-google-genai` (Gemini model integrations)
- `pandas` (Dynamic UI table generation)
- `python-dotenv` (Secure local environment state handling)
- `tavily-python` (Real-time live web verification engines)

---

## 🚀 Installation & Local Setup Instructions

Follow these step-by-step instructions to get the platform running locally on your machine.

### 1. Clone the Repository
```bash
git clone <YOUR_PUBLIC_GITHUB_REPOSITORY_LINK>
cd AgriQuote
2. Set Up a Virtual Environment (Recommended)
Create an isolated environment to prevent dependency conflicts:

Bash
# MacOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
.\venv\Scripts\activate
3. Install Dependencies
Install all required libraries using the provided environment requirements checklist:

Bash
pip install -r requirements.txt
(If a requirements.txt file isn't present in your root, run: pip install streamlit langgraph langchain-google-genai pandas python-dotenv tavily-python)

⚙️ Configuration (.env Setup)
The application relies on secure environment variables to communicate with LLM foundations and search networks.

Create a file named .env in the root directory of the project:

Bash
touch .env
Open the .env file and populate it with your personal API credentials:

Code snippet
GOOGLE_API_KEY=AIzaSyYourActualSecureGeminiKeyHere
TAVILY_API_KEY=tvly-YourOptionalTavilyKeyHere
⚠️ Security Notice: The .env configuration file is strictly ignored by local tracking rules (.gitignore) and must never be committed to shared code hosts. Each judge or user spinning up this project must supply their own standalone keys using this template format.

🖥️ Running the Application
The architecture can be launched as a standalone backend simulation or via its high-end interactive Sales Dashboard panel interface.

Launch the Production UI (Streamlit Layout)
To run the autonomous agent system with its V3.0 Dark Dashboard panel interface, execute:

Bash
streamlit run app.py
Once launched, your terminal will provide a local tracking URL (typically http://localhost:8501). Open this address in any modern web browser to interact with the platform.

Running Pre-Configured Test Matrices
Use the Scenario Selection Matrix dropdown at the top of the app interface to select an evaluation track (e.g., Malaysia Paddy Field - Kubota or Iowa Row-Crop - John Deere).

Click ▶️ RUN PIPELINE.

Watch the multi-agent graph stream logs live as Configurator, Critic, and Sentinel agents negotiate configurations, intercept engineering constraints, and render optimized Bills of Materials (BOM) and compliance records dynamically.
