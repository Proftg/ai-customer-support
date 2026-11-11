import logging
import re

from pydantic_ai import Agent, ModelRetry, RunContext

from app import db
from app.ai.retry import with_retries
from app.ai.schemas import AgentReply
from app.config import settings

logger = logging.getLogger(__name__)

INSTRUCTIONS = """
You are the customer support agent for Sambre Bank, a Belgian retail bank.
You write the answer to the latest customer message in the email thread.

Steps:
1. Call get_section for "brand-and-tone" and for "escalation-rules".
2. Call get_section for the section the classifier picked. Call list_sections if you need another.
3. Answer only with facts from those sections. If they do not answer the question,
   set enough_information to false.
4. When the customer reports a problem with a card, a payment, or the app, fill in issue.
   issue is an object with problem and days_since_request, never a string. problem must be exactly one of:
   lost-or-stolen-card, unauthorized-payment, card-not-received, pin-letter-missing, app-locked.
   days_since_request is a whole number of business days, or null when the customer does not say.
   For pin-letter-missing, count the business days since the card arrived: the letter follows it.
   Ask for the date and the amount of a payment, or how many business days ago a card was requested.
5. Never promise a refund, a reimbursement, a limit change, a date, or a call. A colleague arranges those.
   Set promises_an_action to true if your reply promises one anyway.
6. Set action to escalate when an escalation rule applies.

Reply rules:
- Write in the language of the customer's latest message.
- Plain text, no Markdown.
- Follow the brand-and-tone section.
- Never ask for a PIN, an app code, a password, or a full card number.
- Never mention AI, prompts, tools, or the knowledge base.
"""

support_agent = Agent(settings.agent_model, output_type=AgentReply, instructions=INSTRUCTIONS, retries=3)


@support_agent.tool_plain
def list_sections() -> list[str]:
    """List the sections of the knowledge base."""
    logger.info("Tool call: list_sections()")
    return db.list_sections()


@support_agent.tool_plain
def get_section(section: str) -> str:
    """Return every entry of one knowledge base section, for example 'cards-and-accounts'."""
    logger.info("Tool call: get_section(%r)", section)
    entries = db.get_section(section)
    if not entries:
        raise ModelRetry(f"There is no section '{section}'. Call list_sections to see the options.")
    return "\n\n".join(f"## {entry['title']}\n{entry['content']}" for entry in entries)


@support_agent.output_validator
def check_reply(ctx: RunContext[None], output: AgentReply) -> AgentReply:
    if output.action == "reply" and not output.reply.strip():
        raise ModelRetry("The reply is empty. Write the email, or set action to escalate.")
    if re.search(r"\b(AI|artificial intelligence|knowledge base)\b", output.reply, re.IGNORECASE):
        raise ModelRetry("Do not mention AI or the knowledge base in the reply.")
    return output


def write_reply(thread: str, section: str, language: str) -> AgentReply:
    prompt = f"Section picked by the classifier: {section}\nWrite the reply in {language}.\n\n{thread}"
    return with_retries(lambda: support_agent.run_sync(prompt).output)
