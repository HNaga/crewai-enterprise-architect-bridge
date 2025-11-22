# CrewAI Enterprise Architect Bridge (ArchiCrew)

🚀 **An AI-powered automation suite that turns text requirements into Enterprise Architect (Sparx) models, Python code, and deployment scripts.**

This project demonstrates how to bridge the gap between modern LLM Agents (CrewAI) and locally installed Enterprise Architect (v15/v16) using the Windows COM Interface.

## 🌟 Features

*   **Text-to-UML:** Give an Agent a user story, and it draws Use Case, Class, and Sequence diagrams in EA.
*   **Multi-Agent Workflow:**
    *   🕵️ **Analyst:** Defines Requirements & User Stories.
    *   🏗️ **Architect:** Builds the EA Model & Database Schema.
    *   💻 **Developer:** Generates Flask/Python code from the EA Model.
    *   🚀 **DevOps:** Creates Dockerfiles for deployment.
*   **Local EA Control:** Works with local `.eapx` and `.qea` files (no Cloud required).
*   **Two-Pass Generation:** Solves the "Empty Diagram" bug by separating data creation from visual layout.
*   **Auto-Layout & Reporting:** Automatically arranges diagrams and generates RTF/PDF documentation.

## 🛠️ Tech Stack

*   **Orchestration:** [CrewAI](https://www.crewai.com/)
*   **Modeling:** [Sparx Enterprise Architect](https://sparxsystems.com/)
*   **Language:** Python 3.10+
*   **Interface:** `pywin32` (COM)

## 📋 Prerequisites

1.  **Enterprise Architect** (Professional/Corporate Edition) installed.
    *   *Note: The "Lite" or "Viewer" editions will not work as they block API write access.*
2.  **Python 3.x**
3.  **OpenAI API Key** (or any LLM supported by CrewAI/LangChain).

## 🚀 Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/crewai-ea-bridge.git
    cd crewai-ea-bridge
    ```

2.  Install dependencies:
    ```bash
    pip install crewai pywin32 pydantic
    ```

3.  **Important:** Register EA (if needed):
    If you get "Invalid Class String" errors, run this in Admin CMD:
    ```cmd
    "C:\Program Files (x86)\Sparx Systems\EA\EA.exe" /register
    ```

## 🏃 Usage

### 1. Define your Team
Open `ea_crew_multi_agent.py` and set your desired topic:
```python
USER_TOPIC = "A Hospital Management System"
