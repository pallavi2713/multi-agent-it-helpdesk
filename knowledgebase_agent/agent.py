
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest

from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

load_dotenv()

MODEL = "gemini-2.5-flash"

KB_FILE = (
    Path(__file__).resolve().parent
    /"kb"
    /"troubleshoot.md"
)


def load_knowledge_base(callback_context: CallbackContext,
                        llm_request: LlmRequest):
    """
    Read the complete Markdown knowledge base and
    inject it into the LLM system instruction.
    """

    if not KB_FILE.exists():
        raise FileNotFoundError(
            f"Knowledge base file not found: {KB_FILE}"
        )

    knowledge_content = KB_FILE.read_text(encoding="utf-8")

    kb_instruction = f"""

    ORGANIZATION IT KNOWLEDGE BASE:

    Use the following knowledge base as your primary
    source for troubleshooting IT issues.

    ---------------- KNOWLEDGE BASE START ----------------

    {knowledge_content}

    ---------------- KNOWLEDGE BASE END ----------------

    Instructions:
    1. Understand the user's IT issue.
    2. Refer to the knowledge base before answering.
    3. Provide relevant, clear, numbered resolution steps.
    4. Do not invent procedures or claim that a solution
       exists in the knowledge base if it does not.
    5. If the issue is not covered, clearly inform the user.
    6. Ask the user whether the suggested resolution worked.
    """

    llm_request.append_instructions([kb_instruction])


root_agent = Agent(
    name="knowledge_base_agent",
    model=MODEL,
    description=(
        "IT troubleshooting specialist that uses the "
        "organization's Markdown knowledge base."
    ),
    instruction="""
    You are an IT Knowledge Base Specialist.

    Help employees troubleshoot their IT issues.

    Always use the injected knowledge base instructions
    when answering.

    Give practical, step-by-step resolutions.
    Never make up organization-specific procedures.
    Ask the user whether the solution worked.
    """,
    before_model_callback=load_knowledge_base,
)
# Expose Knowledge Base Agent through A2A
a2a_app = to_a2a(
    root_agent,
    host="localhost",
    port=8002
)