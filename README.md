# Multi-Agent IT Helpdesk System

An AI-powered IT Helpdesk application built using **Google Agent Development Kit (ADK)**, **Agent-to-Agent (A2A) protocol**, and **SQLite**.

The system uses multiple specialized AI agents to handle employee IT support requests, provide troubleshooting guidance from Markdown-based documentation, manage support tickets, and track ticket resolution.

## Architecture

The application consists of three collaborating agents:

### 1. Helpdesk Coordinator Agent
- Acts as the primary interface for employees.
- Understands incoming IT support requests.
- Delegates tasks to the appropriate specialist agent.
- Coordinates the end-to-end support workflow.

### 2. Ticket Management Agent
- Registers employee information.
- Creates support tickets with priority levels.
- Retrieves ticket details and current status.
- Updates ticket information and resolution details.
- Maintains ticket activity history using SQLite.

### 3. Knowledge Base Agent
- Reads the organization's IT troubleshooting documentation from Markdown files.
- Injects the complete knowledge base into the LLM request context.
- Generates relevant, step-by-step troubleshooting instructions.
- Avoids inventing organization-specific solutions when documentation does not cover an issue.

## Technology Stack

- **Language:** Python
- **Agent Framework:** Google ADK
- **Agent Communication:** Google A2A Protocol
- **LLM:** Google Gemini
- **Database:** SQLite
- **Knowledge Source:** Markdown (`.md`) documentation
- **API Server:** Uvicorn

## Architecture Overview

```text
                    Employee
                       |
                       v
             Helpdesk Coordinator
                       |
              A2A Agent Delegation
                 /           \
                /             \
               v               v
       Ticket Management    Knowledge Base
             Agent              Agent
               |                  |
               v                  v
            SQLite          Markdown Files
          (Tickets, Users,  (IT Troubleshooting
           History)          Documentation)
```

## Project Structure

```text
adk_a2a_helpdesk/
│
├── helpdesk_agent/
│   ├── __init__.py
│   └── agent.py
│
├── ticket_agent/
│   ├── __init__.py
│   ├── agent.py
│   └── database.py
│
├── knowledgebase_agent/
│   ├── __init__.py
│   ├── agent.py
│   └── knowledge_base/
│       └── it_troubleshooting.md
│
├── data/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Google Gemini API key
- Git

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/multi-agent-it-helpdesk.git

cd multi-agent-it-helpdesk
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

```env
GOOGLE_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
DATABASE_PATH=./data/helpdesk.db
TICKET_AGENT_URL=http://localhost:8001
```

Get a Gemini API key from:

https://aistudio.google.com/apikey

Never commit your actual `.env` file or API key.

### 5. Initialize the database

Run this command from the project root:

```bash
python -c "from ticket_agent.database import init_db; init_db(); print('Database initialized successfully!')"
```

The SQLite database and required tables are initialized automatically.

### 6. Start the Ticket Management Agent

Open a terminal and run:

```bash
uvicorn ticket_agent.agent:a2a_app --host 127.0.0.1 --port 8001
```

### 7. Start the Knowledge Base Agent

Open a second terminal:

```bash
uvicorn knowledge_base_agent.agent:a2a_app --host 127.0.0.1 --port 8002
```

### 8. Start the Helpdesk Coordinator

Open a third terminal:

```bash
adk web .
```

Open the local ADK Web interface and select `helpdesk_agent`.

The specialist agents expose their A2A Agent Cards at:

- Ticket Agent: `http://localhost:8001/.well-known/agent-card.json`
- Knowledge Base Agent: `http://localhost:8002/.well-known/agent-card.json`

## Example Workflow

A typical support interaction follows this sequence:

1. An employee reports an IT issue, such as VPN connectivity failure.
2. The Helpdesk Coordinator delegates troubleshooting to the Knowledge Base Agent.
3. The Knowledge Base Agent reads the Markdown documentation and provides resolution steps.
4. If the issue persists, the Ticket Management Agent registers the employee and creates a support ticket.
5. The employee confirms when the issue is resolved.
6. The Ticket Management Agent updates the ticket status and resolution details.
7. The employee can retrieve the final ticket status and activity history.

## Current Implementation

- Multi-agent orchestration using Google ADK.
- Inter-agent communication using A2A.
- Separate agents for ticket management and IT knowledge assistance.
- Markdown-based full-context knowledge injection.
- SQLite-based ticket and user persistence.
- Ticket status updates and activity history.

## Future Enhancements

- Deploy agents as independently hosted services.
- Add a web-based employee support portal.
- Integrate authentication and role-based access control.
- Expand the IT knowledge base.
- Introduce advanced document retrieval when the knowledge base grows.
- Add monitoring, logging, and evaluation for agent interactions.

## Note

This repository currently represents a local working prototype. It is intended for learning and demonstrating multi-agent orchestration and IT support automation. It is not yet a production-ready enterprise helpdesk system.
