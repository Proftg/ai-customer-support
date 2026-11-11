from app.ai.schemas import Issue

# Steps where the reply goes to the customer, because the knowledge base already covers them.
CUSTOMER_STEPS = {"wait", "ask-details", "self-service"}


def resolve_issue(issue: Issue) -> str:
    """Decide the next step for a reported problem. The model reports, Python decides."""
    step = next_step(issue)
    # A shop would check an order number here before any action. A bank has no such field:
    # customers never email a card number, so there is nothing to check.
    return step


def next_step(issue: Issue) -> str:
    days = issue.days_since_request  # business days, limits in cards-and-accounts
    if issue.problem == "app-locked":
        return "self-service"
    if issue.problem == "card-not-received":
        if days is None:
            return "ask-details"
        return "wait" if days <= 7 else "reissue-card"
    if issue.problem == "pin-letter-missing":
        if days is None:
            return "ask-details"
        return "wait" if days <= 2 else "resend-pin-letter"
    if issue.problem == "unauthorized-payment":
        return "review-unauthorized-payment"
    if issue.problem == "lost-or-stolen-card":
        return "block-and-replace-card"
    # Anything unexpected goes to a person.
    return "escalate"


if __name__ == "__main__":
    assert resolve_issue(Issue(problem="app-locked")) == "self-service"
    assert resolve_issue(Issue(problem="card-not-received")) == "ask-details"
    assert resolve_issue(Issue(problem="card-not-received", days_since_request=3)) == "wait"
    assert resolve_issue(Issue(problem="card-not-received", days_since_request=12)) == "reissue-card"
    assert resolve_issue(Issue(problem="pin-letter-missing")) == "ask-details"
    assert resolve_issue(Issue(problem="pin-letter-missing", days_since_request=2)) == "wait"
    assert resolve_issue(Issue(problem="pin-letter-missing", days_since_request=5)) == "resend-pin-letter"
    assert resolve_issue(Issue(problem="unauthorized-payment")) == "review-unauthorized-payment"
    assert resolve_issue(Issue(problem="lost-or-stolen-card")) == "block-and-replace-card"
    print("rules ok")
