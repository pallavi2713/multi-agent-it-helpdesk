import os
from dotenv import load_dotenv
load_dotenv()

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from .database import (
    register_user as db_register_user,
    create_ticket as db_create_ticket,
    get_ticket_status as db_get_ticket_status,
    update_ticket as db_update_ticket,
    get_history as db_get_history,
)

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def register_user(name: str, email: str, department: str = "Not provided") -> dict:
    """Create or update an employee record using name, email, and department."""
    if "@" not in email:
        return {"ok": False, "error": "A valid email address is required."}
    return {"ok": True, "user": db_register_user(name, email, department)}

def create_support_ticket(email: str, issue: str, priority: str = "medium") -> dict:
    """Create a ticket for a registered employee. Priority: low, medium, high, critical."""
    if not issue.strip():
        return {"ok": False, "error": "Issue description cannot be empty."}
    return db_create_ticket(email, issue, priority)

def check_ticket_status(ticket_id: str = "", email: str = "") -> dict:
    """Check a ticket by ID or list the latest tickets for an employee email."""
    return db_get_ticket_status(ticket_id, email)

def get_troubleshooting_guidance(issue: str) -> dict:
    """Get first-line troubleshooting suggestions for common IT issues."""
    text = issue.lower()
    rules = [
        (("vpn",), ["Check internet connectivity.", "Disconnect and reconnect the VPN.",
         "Restart the VPN client and verify device date/time.",
         "If it persists, capture the exact error and escalate to network support."]),
        (("password","locked","login","sign in"), ["Check keyboard layout and Caps Lock.",
         "Use the organization's approved password-reset process.",
         "Never share passwords or one-time codes.",
         "If the account remains locked, contact identity/access support."]),
        (("slow","performance","hang","freez"), ["Restart the device if work is saved.",
         "Check disk space and close unnecessary applications.",
         "Install approved pending updates.",
         "If it continues, record when it happens and contact desktop support."]),
        (("printer","printing"), ["Check power, paper, and connectivity.",
         "Confirm the correct printer is selected.",
         "Clear stuck print jobs and retry.",
         "If it persists, share the printer name and error with support."]),
        (("email","outlook","mailbox"), ["Check network connectivity.",
         "Restart the mail client and verify mailbox storage.",
         "Try the approved webmail client to isolate a desktop issue.",
         "If it persists, capture the error and contact messaging support."]),
    ]
    for keys, steps in rules:
        if any(k in text for k in keys):
            return {"issue": issue, "suggestions": steps,
                    "notice": "First-line suggestions; not a confirmed fix."}
    return {"issue": issue, "suggestions": [
        "Record the exact error and when the issue started.",
        "Restart the affected application if safe.",
        "Check whether the issue affects one application or the whole device.",
        "Create a support ticket if the issue continues."
    ], "notice": "No issue-specific runbook matched; escalate if it persists."}

def update_ticket_status(ticket_id: str, resolution: str,
                         new_status: str = "resolved") -> dict:
    """Update ticket status and save a resolution or progress note."""
    if not resolution.strip():
        return {"ok": False, "error": "A resolution or progress note is required."}
    return db_update_ticket(ticket_id, resolution, new_status)

def get_ticket_audit_history(ticket_id: str) -> dict:
    """Retrieve the event history for a ticket."""
    return db_get_history(ticket_id)

root_agent = Agent(
    name="ticket_management_agent",
    model=MODEL,
    description="IT ticket specialist with SQLite-backed user and ticket operations.",
    instruction="""
You are the Ticket Management Specialist Agent, called by another agent over A2A.
Use tools for every database operation. Never fabricate records or claim a write
succeeded unless a tool confirms it. Register users before creating tickets.
Return concise facts, ticket IDs, statuses, and errors. Provide troubleshooting
guidance when requested. Do not resolve tickets unless explicitly instructed by
the calling agent.
""",
    tools=[
        register_user,
        create_support_ticket,
        check_ticket_status,
        get_troubleshooting_guidance,
        update_ticket_status,
        get_ticket_audit_history,
    ],
)

# Expose the specialist as an A2A service; Uvicorn serves this ASGI app.
a2a_app = to_a2a(root_agent, host="localhost", port=8001)
