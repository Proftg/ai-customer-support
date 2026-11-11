# AI customer support

An email support agent: it polls a Gmail inbox, classifies each message, and drafts an answer with an LLM agent.
## Stack

Python 3.13, uv, FastAPI, Pydantic AI (Groq), Postgres, Gmail API.

## Run

```bash
uv sync
cp .env.example .env   # fill in the values
uv run fastapi dev app/main.py
```

Check `http://localhost:8000/health`, it returns `{"status": "ok"}`.

## Status

- [x] Project setup
- [ ] Gmail access
- [ ] Database
- [ ] Classifier and agent
- [ ] Dashboard
- [ ] Deployment
