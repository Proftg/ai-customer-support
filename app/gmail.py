import base64
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
LABELS = ["ai-processed", "needs-human"]


def get_headers(message: dict) -> dict:
    return {h["name"].lower(): h["value"] for h in message["payload"]["headers"]}


def find_text(part: dict) -> str:
    """Return the first text/plain body found in a message part, searching nested parts."""
    if part.get("mimeType") == "text/plain" and part["body"].get("data"):
        return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", "replace")
    for child in part.get("parts", []):
        text = find_text(child)
        if text:
            return text
    return ""


def get_body(message: dict) -> str:
    return find_text(message["payload"]) or message.get("snippet", "")


def has_attachments(message: dict) -> bool:
    def walk(part: dict) -> bool:
        return bool(part.get("filename")) or any(walk(p) for p in part.get("parts", []))

    return walk(message["payload"])


def strip_quoted(text: str) -> str:
    """Drop the quoted earlier messages that mail clients add below a reply."""
    lines = []
    for line in text.splitlines():
        if line.startswith("On ") and line.rstrip().endswith("wrote:"):
            break
        if not line.startswith(">"):
            lines.append(line)
    return "\n".join(lines).strip()


def format_thread(thread: dict, own_address: str) -> str:
    """Render a Gmail thread as plain text, oldest message first."""
    first = get_headers(thread["messages"][0])
    parts = [f"Subject: {first.get('subject', '')}"]
    for message in thread["messages"]:
        sender = get_headers(message).get("from", "")
        role = "Harbor & Pine support" if own_address.lower() in sender.lower() else "Customer"
        parts.append(f"{role} ({sender}):\n{strip_quoted(get_body(message))}")
    return "\n\n".join(parts)


class Gmail:
    def __init__(self):
        # Only a refresh token: the library fetches a fresh access token before the first call.
        creds = Credentials(
            None,
            refresh_token=settings.google_refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=SCOPES,
        )
        self.api = build("gmail", "v1", credentials=creds, cache_discovery=False).users()
        self.address = self.api.getProfile(userId="me").execute()["emailAddress"]
        self.label_ids = self._ensure_labels()

    def _ensure_labels(self) -> dict:
        existing = {l["name"]: l["id"] for l in self.api.labels().list(userId="me").execute()["labels"]}
        for name in LABELS:
            if name not in existing:
                created = self.api.labels().create(userId="me", body={"name": name}).execute()
                existing[name] = created["id"]
        return {name: existing[name] for name in LABELS}

    def list_new_message_ids(self, max_results: int = 10) -> list[str]:
        # The ai-processed label is the state, so there is nothing else to track.
        result = self.api.messages().list(
            userId="me", q="in:inbox -label:ai-processed", maxResults=max_results
        ).execute()
        return [m["id"] for m in result.get("messages", [])]

    def get_message(self, message_id: str) -> dict:
        return self.api.messages().get(userId="me", id=message_id, format="full").execute()

    def get_thread(self, thread_id: str) -> dict:
        return self.api.threads().get(userId="me", id=thread_id, format="full").execute()

    def add_labels(self, message_id: str, names: list[str]) -> None:
        body = {"addLabelIds": [self.label_ids[n] for n in names]}
        self.api.messages().modify(userId="me", id=message_id, body=body).execute()

    def send_reply(self, message: dict, text: str) -> None:
        headers = get_headers(message)
        subject = headers.get("subject", "")
        reply = EmailMessage()
        reply["To"] = headers.get("reply-to") or headers["from"]
        reply["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
        # Gmail needs threadId, In-Reply-To and References plus a Re: subject to keep the thread.
        message_id = headers.get("message-id", "")
        reply["In-Reply-To"] = message_id
        reply["References"] = f"{headers.get('references', '')} {message_id}".strip()
        reply.set_content(text)
        raw = base64.urlsafe_b64encode(reply.as_bytes()).decode()
        self.api.messages().send(
            userId="me", body={"raw": raw, "threadId": message["threadId"]}
        ).execute()
