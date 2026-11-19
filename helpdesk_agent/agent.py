import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TICKET_AGENT_URL = os.getenv("TICKET_AGENT_URL", "http://localhost:8001")


ticket_management_agent = RemoteA2aAgent(
    name="ticket_management_agent",
    description=(
        "IT ticket specialist: registers users, creates tickets, "
        "checks status, provides troubleshooting and records resolutions."
    ),
    agent_card=(
        f"{TICKET_AGENT_URL.rstrip('/')}"
        f"{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
    use_legacy=False,
)
knowledge_base_agent = RemoteA2aAgent(
    name="knowledgebase_agent",
    description=(
        "Searches IT troubleshooting Markdown documents "
        "and provides step-by-step resolutions for IT issues."
    ),
    agent_card=(
        "http://localhost:8002"
        f"{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
    use_legacy=False,
)

root_agent = Agent(
    name="helpdesk_agent",
    model=MODEL,
    description="User-facing IT helpdesk coordinator that delegates work over A2A.",
    instruction="""
You are the employee-facing IT Helpdesk Agent.
Understand the request, collect missing details, and delegate all database-backed
operations to ticket_management_agent.

For a new ticket, collect full name, work email, issue description, and department
(if unknown, use 'Not provided'). Ask for priority only when it matters; otherwise
use medium. Register the user before creating a ticket.
For status checks, use the ticket ID when available; otherwise ask for registered email.

- For IT troubleshooting questions, delegate to knowledge_base_agent.
- For ticket creation, status lookup, and ticket updates,
  delegate to ticket_management_agent.
- When troubleshooting information is returned, present it
  clearly to the user and ask whether the solution worked.
- Do not mark a ticket resolved unless the user confirms
  that the issue has been fixed.
Never invent a user, ticket ID, status, database result, or resolution.
Never mark a ticket resolved unless the employee explicitly asks and confirms the
resolution text. Explain results clearly and professionally.
""",
    sub_agents=[
    ticket_management_agent,
    knowledge_base_agent,
],
)
