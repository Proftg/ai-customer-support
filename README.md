# AI customer support

An email support agent for a fictional Belgian bank (Sambre Bank). It polls a Gmail inbox, drops robot mail, classifies each message, writes a reply with an LLM agent that reads a knowledge base, and hands anything doubtful to a human.

The model proposes, the code decides: business rules and the final reply-or-escalate choice live in plain Python, not in prompts.

## How an email is handled

1. `app/poller.py` lists new messages every 30 seconds.
2. `db.start_event` claims the message in Postgres, so it is never handled twice.
3. `app/guards.py` skips our own mail, auto-replies and mailing lists, with no model call.
4. `app/ai/classifier.py` picks a section and flags cases that need a human.
5. `app/ai/agent.py` reads the knowledge base through tools and writes the reply.
6. `app/ai/rules.py` turns a reported problem into a next step.
7. `app/ai/decide.py` replies only if no escalation rule fires. Otherwise the customer gets an acknowledgement and the thread is labelled `needs-human`.
8. The reply and the ticket are saved in Postgres.

## Stack

Python 3.13, uv, FastAPI, Pydantic AI with Groq (`gpt-oss-20b`), Postgres on Supabase, Gmail API, pydantic-evals, Docker Compose.

## Layout

```
app/          poller, pipeline, Gmail client, database, guards
app/ai/       schemas, classifier, agent, rules, decide, retry
evals/        golden emails and the evaluation runner
knowledge_base/  the texts the agent can read, by section
playground/   run the AI pipeline on a question without sending mail
scripts/      Gmail token, Gmail check, knowledge base seed
supabase/     SQL migrations
```

## Set up

```bash
uv sync
cp .env.example .env
```

Fill in `.env`:

| Variable | What it is |
|---|---|
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` | Gmail access, see below |
| `DATABASE_URL` | Supabase session pooler connection string |
| `GROQ_API_KEY` | Groq key (or `ANTHROPIC_API_KEY` with other model names) |
| `CLASSIFIER_MODEL`, `AGENT_MODEL` | Model names such as `groq:openai/gpt-oss-20b` |
| `POLL_INTERVAL_SECONDS` | Seconds between two reads of the inbox |

Gmail: create an OAuth desktop client in Google Cloud with the `gmail.modify` scope, save it as `credentials.json`, then run `uv run python scripts/get_refresh_token.py` and copy the three printed values into `.env`. A Google app in test mode gives a token that expires after 7 days.

Database and knowledge base:

```bash
supabase db push
uv run python -m scripts.seed_knowledge_base
```

## Run

```bash
uv run python -m app.poller          # the loop
uv run fastapi dev app/main.py       # health endpoint at /health
uv run python playground/try_pipeline.py   # no Gmail, no reply sent
```

With Docker, `docker compose up -d --build` starts the API and the poller. The API listens on `127.0.0.1` only.

## Evaluations

```bash
uv run python -m evals.run_evals
```

24 golden emails (13 expected replies, 11 expected escalations), each checked for the section and the action. The last run scored 100 % with no errors. Model outputs vary between runs, so run it twice after any prompt change.

## Known limits

- The evaluation does not judge the text of the replies.
- Re-running the knowledge base seed overwrites existing entries.
- The free Groq tier limits tokens per minute, so evaluations run one case at a time.

## Status

- [x] Project setup
- [x] Gmail access
- [x] Database and poller
- [x] Classifier, agent, rules and decision
- [x] Evaluations
- [x] Docker files
- [ ] Server deployment
- [ ] Admin dashboard
