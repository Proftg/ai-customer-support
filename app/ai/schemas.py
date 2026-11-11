from typing import Literal

from pydantic import BaseModel, Field

Section = Literal[
    "cards-and-accounts", "online-banking", "unauthorized-payments", "delays-and-channels", "other"
]


class Classification(BaseModel):
    section: Section
    language: str = Field(description="Language of the latest customer message, e.g. French")
    needs_human: bool = Field(description="True when an always-escalate rule applies")
    reason: str = Field(description="One sentence explaining the classification")
    acknowledgement: str = Field(
        description="Short note to the customer, in their language, that a colleague replies"
    )


class Issue(BaseModel):
    problem: Literal[
        "lost-or-stolen-card",
        "unauthorized-payment",
        "card-not-received",
        "pin-letter-missing",
        "app-locked",
    ]
    days_since_request: int | None = Field(
        default=None, description="Business days since the card or PIN letter was requested or sent"
    )


class AgentReply(BaseModel):
    action: Literal["reply", "escalate"]
    reply: str = Field(description="The email to the customer, plain text")
    reasoning: str = Field(description="Which knowledge base entries you used, and why")
    enough_information: bool = Field(description="True when the knowledge base answers the question")
    promises_an_action: bool = Field(
        description="True when the reply promises a refund, reimbursement, limit change, date, or call"
    )
    issue: Issue | None = Field(
        default=None, description="Fill in when the customer reports a problem with a card or the app"
    )


class Decision(BaseModel):
    action: Literal["reply", "escalate"]
    section: str
    reply: str
    reason: str
    proposed_action: str | None = None
