# DailyTechLearn

A personalized daily learning app for AI/software engineers: 5 new questions and
5 revision questions a day, with simple explanations, real-world examples, and
business relevance across AI/ML, software engineering, system design, DevOps,
cloud, databases, security, and business/SaaS concepts.

This project is **free-first** — no paid services unless explicitly agreed on.

> **Status: Phase 19 — Daily Fresh Learning Experience + Deployment
> Prep.** This phase is mostly an audit and polish pass, not a rebuild: it
> confirmed the existing daily-learning model (new vs. revision, Phase
> 12/18 adaptive repetition, the Phase 9 human-approval boundary) already
> matched the intended design, found and fixed one real gap (new-question
> selection wasn't excluding paused/inactive topics — it now does,
> consistently across `/api/learning/today`, the pipeline-status endpoint,
> and the dashboard), and rebuilt the Dashboard's "Today's Learning"
> section into two clear at-a-glance cards (New Learning / Today's
> Revision) with honest counts and accurate empty/completion states,
> instead of a content preview. The other major addition is **deployment
> preparation** for Vercel (frontend) + Render (backend) + a separate
> production PostgreSQL — [`render.yaml`](render.yaml) and
> [`frontend/vercel.json`](frontend/vercel.json), with nothing actually
> deployed and no production credentials created. See
> [`docs/architecture.md`](docs/architecture.md) for the full design.

## Architecture

```
Frontend (React + TypeScript)  →  Backend (FastAPI)  →  Database (PostgreSQL)  →  AI (future)
```

- `frontend/` — React + TypeScript app, built with Vite.
- `backend/` — Python 3.12 + FastAPI app, using SQLAlchemy to talk to PostgreSQL.
- `docs/` — project documentation.

## Prerequisites

- Python 3.12 (a `.venv` virtual environment already exists at the project root)
- Node.js + npm (for the frontend)
- PostgreSQL 15 running locally (see below)

## PostgreSQL: start the server and set up the database

PostgreSQL runs as a local Windows service, so it's usually already running.

```powershell
# Check whether it's running
Get-Service -Name postgresql-x64-15

# Start it if it isn't
Start-Service -Name postgresql-x64-15
```

If this is a fresh machine and the `dailytechlearn` database/role don't exist
yet, connect as the `postgres` superuser and create them:

```bash
psql -U postgres
```

```sql
CREATE USER dailytechlearn_app WITH PASSWORD 'choose-a-strong-password';
CREATE DATABASE dailytechlearn OWNER dailytechlearn_app;
```

Then set `DATABASE_URL` in your `.env` (copy from `.env.example`):

```
DATABASE_URL=postgresql://dailytechlearn_app:choose-a-strong-password@localhost:5432/dailytechlearn
```

Schema is managed by **Alembic migrations** (`backend/alembic/`), not
automatic table creation. Before starting the backend for the first time (or
after pulling schema changes), run:

```bash
cd backend
python -m alembic upgrade head
```

This creates/updates the `topics` and `questions` tables to match the latest
migration.

## Backend: activate the environment and run the server

From the project root:

```bash
# Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (Git Bash):
source .venv/Scripts/activate

# Install dependencies (first time only)
pip install -r backend/requirements.txt

# Apply database migrations (first time, and after pulling schema changes)
cd backend
python -m alembic upgrade head

# Run the API
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

> **If port 8000 refuses to bind** (`[WinError 10048] only one usage of
> each socket address...`) even after closing every terminal running
> uvicorn: on Windows this can be an orphaned socket that `netstat -ano`
> still shows as `LISTENING` under a PID that no longer corresponds to any
> real process (`Get-Process -Id <pid>` reports "cannot find a process").
> This isn't something to force-kill your way around — it usually clears
> after a machine restart. In the meantime, run the backend on a different
> port (`--port 8010`) and point the frontend at it via `frontend/.env`:
> `VITE_API_BASE_URL=http://localhost:8010` (Vite only reads this file at
> startup, so restart `npm run dev` after changing it).

## Frontend: install and run

In a separate terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## Testing the health API

With the backend running:

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{"status": "healthy"}
```

## Testing the database connection

With the backend running:

```bash
curl http://localhost:8000/api/db-health
```

Expected response:

```json
{"status": "healthy", "database": "connected"}
```

If PostgreSQL isn't reachable (wrong `DATABASE_URL`, service stopped, etc.),
this returns HTTP 503 with `{"status": "unhealthy", "database": "disconnected"}`.

## Verifying the `Topic` / `Question` schema

With migrations applied (`alembic upgrade head`), verify insert/read and the
relationship between `Topic` and `Question` end-to-end:

```bash
cd backend
python -m scripts.test_db_interaction
```

Expected output:

```
Inserted topic: id=1 name='Test Topic'
Inserted question: id=1 topic_id=1
Question -> Topic: 'Test Topic'
Topic -> Questions: ['What is Docker?']
Relationship verified in both directions.
Cleaned up test rows.
```

You can also inspect the tables directly:

```bash
psql -c "\d topics" "$DATABASE_URL"
psql -c "\d questions" "$DATABASE_URL"
```

## Seeding development data

To have realistic topics/questions — and a development user — to test the API
and frontend against:

```bash
cd backend
python -m scripts.seed_dev_data
```

Safe to re-run — it matches existing rows by name/text/username and only
inserts what's missing, so it never creates duplicates. This also creates a
seeded **admin** account so the content/AI pipeline endpoints are usable
right after setup:

- Email: `admin@dailytechlearn.dev`
- Password: `devpassword123`

**This account is for local development only.** Never reuse this
email/password combination anywhere real, and never seed a database like
this outside a single-developer local setup.

## Testing the Category / Topic taxonomy

With the backend running and dev data seeded (`python -m scripts.seed_dev_data`
— now creates 5 categories and 25 topics, backfilling the 8 original topics
with a category rather than touching their name/questions):

```bash
curl http://localhost:8000/api/categories
curl http://localhost:8000/api/categories/1
curl "http://localhost:8000/api/topics?category_id=1"
```

## Testing the Learning Content API

With the backend running and dev data seeded:

```bash
curl http://localhost:8000/api/topics
curl http://localhost:8000/api/topics/1
curl http://localhost:8000/api/questions
curl http://localhost:8000/api/questions/1
curl "http://localhost:8000/api/questions?topic_id=1"
curl "http://localhost:8000/api/questions?limit=5&offset=0"

# Create a question (admin-only as of Phase 14 — see "Authentication" above)
curl -X POST http://localhost:8000/api/questions \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"topic_id":1,"question_text":"What is a neural network?","answer":"...","difficulty":"beginner"}'
```

`GET /api/questions` and `GET /api/questions/{id}` stay public/read-only —
only creating a question requires an admin token.

A missing topic/question ID returns HTTP 404. An invalid request body (e.g. a
`difficulty` value that isn't `beginner`/`intermediate`/`advanced`, or a
missing required field) returns HTTP 422 with details about what's wrong.

## Authentication (Phase 14, username login added later)

Every learning/content endpoint now requires a JWT access token in an
`Authorization: Bearer <token>` header — the backend identifies you from
that token, never from anything else in the request. See
`docs/architecture.md` for what a JWT is and why this matters.

```bash
# Register a new (non-admin) learner — "username" is optional; set it if
# you want to be able to log in with it instead of your email later.
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"a-strong-password","username":"you"}'
# {"id":2,"email":"you@example.com","username":"you","is_admin":false,"created_at":"..."}

# Log in with EITHER the email or the username in "identifier"
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"you@example.com","password":"a-strong-password"}'
# ...or equivalently: -d '{"identifier":"you","password":"a-strong-password"}'
# {"access_token":"eyJ...", "token_type":"bearer"}

# Save it for the examples below
TOKEN="eyJ...the access_token value..."

# Confirm who you're logged in as
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer $TOKEN"
```

Duplicate-email registration returns `409` ("An account with this email
already exists"); a taken username returns its own `409` ("This username
is already taken") — checked independently since they're two different
unique columns. Wrong password or an unrecognized email/username both
return the same generic `401` — telling them apart would reveal which
accounts are registered. Missing/invalid/expired tokens return `401`.

For the content/AI pipeline endpoints below, log in as the seeded admin
account instead (see "Seeding development data" above) — either its email
or its legacy username (`dev_user`) works:

```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"admin@dailytechlearn.dev","password":"devpassword123"}' \
  | python -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
```

A normal (non-admin) learner's token gets `403 Forbidden` — not `401` — on
these endpoints, since they *are* authenticated, just not authorized for
admin actions (see "Authentication vs. authorization" in
`docs/architecture.md`).

## Testing the Learning Progress / Daily Learning API

With the backend running, dev data seeded, and `$TOKEN` set (see
"Authentication" above):

```bash
# Today's learning for the logged-in user
curl http://localhost:8000/api/learning/today -H "Authorization: Bearer $TOKEN"

# Mark a question learned ("result" is optional, defaults to "easy")
curl -X POST http://localhost:8000/api/learning/complete \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question_id":3}'
# {"question_id":3,...,"review_count":1,"next_review_at":"...+1 day..."}

# See your own progress, including next_review_at
curl http://localhost:8000/api/learning/progress -H "Authorization: Bearer $TOKEN"

# Visibility into pool health (approved questions, new/due counts, pending drafts)
curl http://localhost:8000/api/learning/pipeline-status -H "Authorization: Bearer $TOKEN"
```

After marking a question learned, it moves out of `new_questions` — but it
does **not** immediately appear in `revision_questions`, because it isn't
**due** yet (`next_review_at` is 1 day out). See "Testing spaced repetition"
below for how to actually see it become due. A nonexistent question returns
HTTP 404; a malformed request body returns HTTP 422; a missing/invalid token
returns HTTP 401. Two different users marking the *same* question learned
each get their own independent `LearningProgress` row — one user's progress
never affects or reveals another's.

## Testing adaptive spaced repetition (Phase 18)

Every question starts at `ease_factor = 2.5`. Reviewing it "easy" grows
the interval (bootstrap: 1 day, then 3 days, then `previous_interval *
ease_factor` from the third review on, capped at 180 days) and nudges
`ease_factor` up by `0.15`; "hard" resets the interval back to 1 day and
nudges `ease_factor` down by `0.2` (floored at `1.3`). Because the
multiplier is per-question, two questions with different histories end up
on genuinely different schedules — not the same fixed curve for everyone.

Since waiting real days isn't practical for testing, move a question's due
date into the past directly in Postgres:

```bash
# Make question 3 due right now (simulating time passing)
psql -c "UPDATE learning_progress SET next_review_at = now() - interval '1 hour' WHERE question_id = 3;" "$DATABASE_URL"

# Now it appears in revision_questions
curl http://localhost:8000/api/learning/today -H "Authorization: Bearer $TOKEN"

# Review it — the response includes the newly computed next_review_at
curl -X POST http://localhost:8000/api/learning/complete \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question_id":3,"result":"easy"}'

# Check the actual ease_factor/interval in the database
psql -c "SELECT review_count, ease_factor, next_review_at - last_reviewed_at AS interval FROM learning_progress WHERE question_id = 3;" "$DATABASE_URL"
```

Reviewing it again never creates a second `LearningProgress` row (the
existing unique constraint on `(user_id, question_id)` guarantees that —
unchanged since Phase 5). With multiple due questions, `/api/learning/today`
returns the **5 most overdue** first, and never more than 5 — also
unchanged; only how `next_review_at` gets computed is new this phase.

## Testing the external API integration

No API key needed — Dev.to's public articles API is free to read. This
endpoint is admin-only (it's part of the content pipeline, not something a
learner calls). With the backend running and `$ADMIN_TOKEN` set (see
"Authentication" above):

```bash
curl "http://localhost:8000/api/external/test?tag=devops&limit=3" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Returns a small JSON array of real, current Dev.to articles tagged `devops`
(title, url, description, tags, published_at). Nothing is saved to
PostgreSQL — this endpoint only proves the fetch works. If Dev.to is
unreachable (or `DEV_TO_API_BASE_URL` is misconfigured), this returns HTTP
`502 Bad Gateway` with a safe, non-sensitive error message instead of
crashing or leaking internal details.

## Testing content ingestion

Admin-only (content pipeline). With the backend running and `$ADMIN_TOKEN`
set:

```bash
AUTH=(-H "Authorization: Bearer $ADMIN_TOKEN")

# Fetch and store articles (safe to run repeatedly)
curl -X POST "http://localhost:8000/api/content/ingest?tag=devops&limit=5" "${AUTH[@]}"
# {"fetched":5,"created":5,"skipped_duplicates":0}

# Run it again immediately — no new rows are created
curl -X POST "http://localhost:8000/api/content/ingest?tag=devops&limit=5" "${AUTH[@]}"
# {"fetched":5,"created":0,"skipped_duplicates":5}

# List stored articles (supports ?source=, ?tag=, ?limit=, ?offset=)
curl http://localhost:8000/api/content/articles "${AUTH[@]}"

# Get one article by id
curl http://localhost:8000/api/content/articles/1 "${AUTH[@]}"
```

A nonexistent article id returns 404. If Dev.to is unreachable, `/api/content/ingest`
returns the same `502 Bad Gateway` behavior as `/api/external/test`. Nothing
here writes to the `questions` table — see `docs/architecture.md` for why
`SourceArticle` and `Question` are kept separate.

## Setting up Groq (AI layer)

This project uses [Groq](https://groq.com) — a cloud API for open-source
LLMs — **not** Ollama, even if Ollama happens to be installed on your
machine for something else.

1. Get a free API key at **https://console.groq.com/keys** (no credit card
   required).
2. Add it to your `.env` (never commit this):
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   GROQ_MODEL=openai/gpt-oss-20b
   ```

`GROQ_MODEL` defaults to `openai/gpt-oss-20b` if unset. Note: which models
are available can change over time / per account — if you hit a "model not
found" error, check your account's available models at
`https://console.groq.com/docs/models` or by listing them via the SDK.

## Testing the AI integration

Admin-only. With the backend running, `GROQ_API_KEY` set, and `$ADMIN_TOKEN`
set:

```bash
# Generate draft learning content for a bare topic
curl -X POST http://localhost:8000/api/ai/test \
  -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" \
  -d '{"topic":"What is Docker?"}'

# Generate draft learning content from a stored SourceArticle (id 1, e.g.)
curl -X POST http://localhost:8000/api/ai/test/article/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Both return a JSON object with `question`, `answer`, `simple_explanation`,
`real_world_example`, `business_relevance`, `difficulty`, `keywords` —
**nothing is saved to PostgreSQL**. A nonexistent article id returns 404. If
`GROQ_API_KEY` is missing, unset, or rejected, or Groq is unreachable, you'll
get a clean `500`/`502`/`429` response — never a stack trace, and never the
key itself.

## Testing the AI draft → Question pipeline

Admin-only. With the backend running, `GROQ_API_KEY` set, `$ADMIN_TOKEN`
set, and at least one article ingested (see above):

```bash
AUTH=(-H "Authorization: Bearer $ADMIN_TOKEN")

# 1. Generate a draft from a stored SourceArticle (id 1, e.g.)
curl -X POST http://localhost:8000/api/ai/drafts/article/1 "${AUTH[@]}"
# {"id":1,...,"status":"generated","reviewed_at":null}

# 2. List / inspect drafts
curl http://localhost:8000/api/ai/drafts "${AUTH[@]}"
curl http://localhost:8000/api/ai/drafts/1 "${AUTH[@]}"

# 3a. Approve — creates a real Question (pick a real topic id from /api/topics)
curl -X POST http://localhost:8000/api/ai/drafts/1/approve "${AUTH[@]}" \
  -H "Content-Type: application/json" -d '{"topic_id":8}'

# 3b. ...or reject instead — creates nothing
curl -X POST http://localhost:8000/api/ai/drafts/1/reject "${AUTH[@]}"
```

Notes:
- Generating again for the same article while an unreviewed draft is
  pending returns `409 Conflict` — review it first. Once a draft is
  approved or rejected, generating a new one for that article is allowed.
- Approving an already-approved (or rejected) draft returns `409`, not a
  silent success.
- A nonexistent draft, article, or topic returns `404`.
- The created `Question` has `source_draft_id` set, so you can always trace
  it back to the draft (and from there, the `SourceArticle`) it came from.

## Testing content classification

Admin-only. With the backend running, `GROQ_API_KEY` set, `$ADMIN_TOKEN`
set, and at least one article ingested:

```bash
curl -X POST http://localhost:8000/api/content/classify/1 \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Returns the AI's suggested `category`/`topic`/`difficulty`/`relevance_score`
(1–5) plus `matched_category_id`/`matched_topic_id` — `null` if the AI named
something that doesn't actually exist in our taxonomy. **As of Phase 11**,
when both match a real row, the classification is now persisted onto the
article (`classified_category_id`, `classified_topic_id`,
`classified_difficulty`, `relevance_score`, `classified_at`) — needed so
candidate selection doesn't have to re-call Groq for the same article. A
hallucinated (non-matching) name is never persisted. A nonexistent article
returns 404; Groq failures return the same clean 502/429/500 behavior as the
other AI endpoints.

## Testing candidate selection and batch draft generation

Admin-only. With the backend running, `$ADMIN_TOKEN` set, and at least one
article classified (see above):

```bash
AUTH=(-H "Authorization: Bearer $ADMIN_TOKEN")

# Inspect current candidates and their scoring breakdown
curl "http://localhost:8000/api/content/candidates?limit=10" "${AUTH[@]}"

# Generate up to 5 drafts from the best-ranked candidates
curl -X POST "http://localhost:8000/api/learning/generate-drafts?limit=5" "${AUTH[@]}"
# {"requested":5,"selected":4,"generated":4,"skipped":0,"errors":[]}

# Run it again immediately — no duplicate drafts for the same article
curl -X POST "http://localhost:8000/api/learning/generate-drafts?limit=5" "${AUTH[@]}"
# {"requested":5,"selected":0,"generated":0,"skipped":0,"errors":[]}
```

An article is excluded from candidates if it isn't classified, has
`relevance_score < 2`, its topic is inactive, or it already has an approved
or unreviewed (`generated`) draft. If Groq fails for one candidate mid-batch,
that one is recorded in `errors` (with `skipped` incremented) and the batch
continues — one bad article never corrupts the rest. **This only creates
`AIDraft`s** — approving one into a real `Question` still requires the
existing explicit `POST /api/ai/drafts/{id}/approve` call (Phase 9).

## Testing content pipeline management (Phase 13)

Admin-only. With the backend running and `$ADMIN_TOKEN` set:

```bash
AUTH=(-H "Authorization: Bearer $ADMIN_TOKEN")

# Global pipeline health
curl http://localhost:8000/api/content/pipeline-status "${AUTH[@]}"
# {"total_source_articles":5,...,"target_new_pool_size":35,
#  "pool_status":"needs_content","recommended_generation_count":17}

# Include one user's available-new / due-revision counts too
curl "http://localhost:8000/api/content/pipeline-status?user_id=1" "${AUTH[@]}"

# Generate drafts toward the target pool size (auto-calculates how many)
curl -X POST http://localhost:8000/api/content/replenish "${AUTH[@]}"
# {"requested":10,"max_batch_size":10,"candidates_considered":1,
#  "generated":1,"skipped":0,"failed":0,"errors":[]}

# You can also ask for a specific count (still capped at 10 per call)
curl -X POST "http://localhost:8000/api/content/replenish?count=3" "${AUTH[@]}"

# A count above the cap is rejected outright, not silently clamped away
curl -X POST "http://localhost:8000/api/content/replenish?count=10000" "${AUTH[@]}"
# HTTP 422 — "Input should be less than or equal to 10"
```

`recommended_generation_count = max(0, target_new_pool_size - approved_questions)`
— purely arithmetic, no Groq call involved in calculating it.
`MAX_BATCH_SIZE=10` is enforced twice: once by the API (`422` on an
out-of-range `count`) and again inside the service function itself, so the
limit holds even if something calls the service directly. Review drafts
awaiting a decision (now including the source article's title/topic/relevance)
via `GET /api/ai/drafts?status=generated` (also admin-only).

## Testing the AI Learning Assistant (Phase 15)

Any authenticated user (not just admin) can use this — it's a learner
feature. With the backend running, `GROQ_API_KEY` set, and `$TOKEN` set
(see "Authentication" above):

```bash
# General question, no specific DailyTechLearn question involved
curl -X POST http://localhost:8000/api/learning/assistant \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"What does idempotent mean in the context of APIs?"}'

# Grounded in a specific question (pick a real id from /api/questions)
curl -X POST http://localhost:8000/api/learning/assistant \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"Explain this like I'"'"'m a complete beginner.","question_id":3}'

# A follow-up — resend the conversation so far as "history" (the backend
# never stores this itself; the frontend keeps it in memory)
curl -X POST http://localhost:8000/api/learning/assistant \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"Can you give a business example of that?","question_id":3,
       "history":[{"role":"user","content":"Explain this like I'"'"'m a complete beginner."},
                  {"role":"assistant","content":"...the previous answer..."}]}'
```

Both return `{"answer": "...", "follow_up_suggestions": ["...", "..."]}`.
An empty or whitespace-only `message`, or one over 2000 characters, returns
`422`. A `question_id` that doesn't exist returns `404` — the backend
always loads the real `Question` from PostgreSQL itself; it never trusts
question content the client might try to send directly. Missing/invalid
tokens return `401`, same as every other protected endpoint. If Groq is
unreachable, misconfigured, or rejects the request, you get the same safe
`429`/`500`/`502` behavior as every other AI endpoint — never a leaked key
or stack trace. **Nothing here writes to `questions`, `ai_drafts`, or any
other table** — verified directly by comparing row counts before/after
testing.

Note: `POST /api/learning/assistant` (this section) still exists and still
works exactly as in Phase 15 — it's the stateless, no-history-saved path.
The frontend now uses the persistent chat endpoints below instead, but
nothing about this one changed except a bug fix (see "Groq's response
didn't match the expected structure" note in docs/architecture.md).

## Testing persistent AI chat (Phase 16)

Any authenticated user can use this. With the backend running,
`GROQ_API_KEY` set, and `$TOKEN` set:

```bash
# Create a session (question_id is optional — omit for a general chat)
curl -X POST http://localhost:8000/api/learning/chat/sessions \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question_id":3}'
# {"id":1,"title":"About: What is machine learning?","question_id":3,"messages":[],...}

# Send a message (SID = the id from above)
curl -X POST http://localhost:8000/api/learning/chat/sessions/1/messages \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"Explain this simply."}'
# {"message":{"id":1,"role":"assistant","content":"...","created_at":"..."},
#  "follow_up_suggestions":["...","..."]}

# Reload the session — messages persist across requests/page refreshes
curl http://localhost:8000/api/learning/chat/sessions/1 -H "Authorization: Bearer $TOKEN"

# List all your sessions (most recently active first)
curl http://localhost:8000/api/learning/chat/sessions -H "Authorization: Bearer $TOKEN"

# Delete a session (cascades to its messages)
curl -X DELETE http://localhost:8000/api/learning/chat/sessions/1 -H "Authorization: Bearer $TOKEN"
```

A session's title is set automatically from its first user message (or
from the linked question, before any message exists) — never a second Groq
call. Accessing, messaging, or deleting a session that belongs to another
user (or doesn't exist) returns `404` in both cases — deliberately
identical, so a caller can never tell "not yours" from "not real." If Groq
fails while sending a message, nothing is written: no fake assistant
reply, and the user's message isn't saved either (verified directly: after
an injected Groq failure, the session's message count was unchanged
afterward) — a retry can't create duplicates because the failed attempt
never touched the database.

## Testing the learning dashboard (Phase 16, extended Phase 17)

```bash
curl http://localhost:8000/api/learning/dashboard -H "Authorization: Bearer $TOKEN"
```

Returns counts (`learned_count`, `due_revision_count`, `new_available_count`,
`total_approved_questions`), `progress_percent`, `recent_activity` (last 5
reviewed questions), and `topics_in_progress` (topics with at least one
learned question, most-learned first, now including `total_questions` per
topic for a "3/8 learned" style display). Phase 17 added three more fields
to power the new `/dashboard/progress` page: `mastered_count` (questions at
`review_count >= 5`, i.e. reached the spaced-repetition schedule's top
interval), `total_reviews_completed` (sum of every `review_count`), and
`current_streak_days` (consecutive days with activity, ending today or
yesterday) — the last one is a **best-effort approximation**, not an exact
historical count, because `learning_progress` only ever stores each
question's most recent review date, not a full event history (see
docs/architecture.md for why). Entirely computed from the existing
`learning_progress`/`questions`/`topics` tables — still no new progress
table, same endpoint that powered Phase 16's dashboard.

## What you should see in the browser (Phase 17: multi-page app)

With both servers running (and dev data seeded), open `http://localhost:5173`.

**Routes (all client-side, via `react-router-dom`):**

| Route | Who can see it | What it shows |
|---|---|---|
| `/` | anyone | Landing page with "Get Started" / "Log In" — redirects to `/dashboard` if already logged in |
| `/login`, `/register` | anyone | Auth forms |
| `/dashboard` | any logged-in user | Home: stat cards (Learned/Due/New/Progress/**Streak**), a preview of Continue Learning + Today's Revision, topic chips, recent activity, an "Ask AI" card |
| `/dashboard/learn` | any logged-in user | All of today's new questions as full cards (topic, difficulty, answer, simple explanation, real-world example, keywords, Ask AI, Learned) |
| `/dashboard/revision` | any logged-in user | One due question at a time: Question → "Show Answer" → Answer + **Easy**/**Hard** → a brief success animation showing the actual next review date, then auto-advances to the next due question |
| `/dashboard/progress` | any logged-in user | Total learned, reviews completed, streak, mastered count, topic-wise progress bars, difficulty breakdown |
| `/ai` | any logged-in user | Conversation list (previous chats + "+ New Chat") |
| `/ai/chat/:id` | the session's owner only | The actual conversation — send a message, see the typing indicator, get an answer + follow-up suggestions |
| `/admin`, `/admin/content`, `/admin/candidates`, `/admin/drafts`, `/admin/taxonomy` | **admin only** | Pipeline health, source articles, candidates, draft review/approval, taxonomy browser |

Register a new account to see the normal-learner experience, or log in as
the seeded admin (`admin@dailytechlearn.dev` / `devpassword123`) to also
see the **Admin** section appear in the sidebar. A non-admin account never
sees admin links in the UI, and typing an admin URL directly redirects
them straight back to `/dashboard` — though the real enforcement is still
the backend's `get_current_admin_user` (every admin API call is `403` for
a non-admin regardless of what the frontend shows).

**Layout**: on desktop, a left sidebar (Dashboard/Learn/Revision/Progress/AI,
plus Admin links if applicable) and a top bar (your email, an "Admin" badge
if applicable, Log Out). Below ~860px width, the sidebar becomes a
slide-in drawer (opened via the ☰ button in the top bar) and a bottom
navigation bar (Home/Learn/Revise/AI/Progress) appears instead.

Clicking any question's **Ask AI 🤖** button navigates to `/ai/chat/:id` —
resuming a prior conversation about that exact question if one exists, or
starting a new one. Marking a question "Learned" (or rating a revision
Easy/Hard) shows a toast notification and refreshes the relevant page's
data immediately — every page is a live view over `learning_progress`, not
a cached snapshot.

**On storing the token in the browser:** the frontend keeps the JWT in
`localStorage` (key `dailytechlearn_token`), the simplest option available.
The real tradeoff: any JavaScript running on the page — including an
injected XSS payload — can read `localStorage`, so a real production app
would typically use an httpOnly cookie instead (invisible to JavaScript,
but requires CSRF protection and cookie/CORS setup). For this project's
scope, the simpler approach was the deliberate choice.

## Making a schema change (adding/editing a model)

1. Edit or add a model in `backend/app/models/`.
2. Generate a migration by diffing the models against the real database:
   ```bash
   cd backend
   python -m alembic revision --autogenerate -m "describe the change"
   ```
3. **Read the generated file** in `backend/alembic/versions/` — autogenerate
   is a helpful draft, not a guarantee (it can miss things like renames).
4. Apply it: `python -m alembic upgrade head`.

## Configuration

- `.env` at the project root (copy from [`.env.example`](.env.example)) —
  configures `CORS_ORIGINS`, `DATABASE_URL`, `GROQ_API_KEY`/`GROQ_MODEL`, and
  (as of Phase 14) `JWT_SECRET_KEY` — the secret that signs/verifies login
  tokens. Generate one with
  `python -c "import secrets; print(secrets.token_hex(32))"`. `python-dotenv`
  finds this file automatically when the backend starts. **Never commit this
  file** — it's gitignored, and it's where your real database password, Groq
  API key, and JWT secret all live. Whoever has `JWT_SECRET_KEY` can forge a
  valid login token, so treat it exactly like a password.
- `frontend/.env` (copy from [`frontend/.env.example`](frontend/.env.example)) —
  configures `VITE_API_BASE_URL`, where the frontend looks for the backend.
  The frontend never has access to `GROQ_API_KEY` — it only ever talks to
  our own backend.

## Deploying to production (Phase 19)

**Nothing has been deployed** — this section prepares the repo so a real
deployment is a small, safe, well-understood step whenever you're ready to
take it, not something done as part of this phase.

```
                    Internet
                       │
                       ▼
                  Vercel
                 Frontend (React, static build)
                       │  VITE_API_BASE_URL
                       ▼
                  Render
                 FastAPI Backend
                  /              \
                 /                \
                ▼                  ▼
        Production PostgreSQL     Groq API
        (separate from your        (same GROQ_API_KEY
         local dev database)        mechanism, just set
                                     in Render, not .env)
```

### Prerequisite: put the project in git (one-time, manual)

This project isn't a git repository yet (checked directly — `git status`
reports "not a git repository"). Vercel and Render both deploy by watching
a GitHub/GitLab/Bitbucket repo, so before any of the steps below apply,
you'd need to initialize git and push to a remote yourself:

```bash
cd DailyTechLearn
git init
git add .
git commit -m "Initial commit"
# then create a repo on GitHub and follow its "push an existing repo" instructions
```

This is left as a manual step deliberately — creating your version control
history and choosing where it's hosted (which GitHub account/org, public
vs. private) is your call, not something to decide on your behalf. Double
check `git status` before your first commit to confirm `.env` and
`frontend/.env` are excluded (they're already in `.gitignore`) — never
commit real secrets.

### 1. Provision a production database

Create a **separate** PostgreSQL database for production — a new Render
Postgres instance, or any hosted Postgres (Neon, Supabase, etc.). Never
point production at your local `dailytechlearn` database. Once created,
run the existing migrations against it once, from your machine, using its
connection string:

```bash
cd backend
DATABASE_URL="<production connection string>" python -m alembic upgrade head
```

(On Windows PowerShell: `$env:DATABASE_URL="..."; python -m alembic upgrade head`.)
This creates all tables fresh — safe to run against an empty production
database. From then on, every future migration should be applied the same
way as part of deploying a schema change (or via Render's start command,
see `render.yaml`, which runs `alembic upgrade head` automatically before
each deploy's server starts).

### 2. Deploy the backend to Render

[`render.yaml`](render.yaml) at the repo root describes the service:
Python runtime, `rootDir: backend`, build command
(`pip install -r requirements.txt`), start command (runs migrations, then
`uvicorn app.main:app --host 0.0.0.0 --port $PORT` — no `--reload`, and
`$PORT` comes from Render, never hardcoded), and a health check at
`/api/health` (already existed since Phase 1).

In the Render dashboard: **New +** → **Blueprint** → point it at your
pushed repo. Render reads `render.yaml` and prompts for the env vars
marked `sync: false`:

| Variable | Value |
|---|---|
| `DATABASE_URL` | your production Postgres connection string (step 1) |
| `GROQ_API_KEY` | your Groq key — same one from your local `.env` or a new one |
| `JWT_SECRET_KEY` | a **new**, production-only secret — generate with `python -c "import secrets; print(secrets.token_hex(32))"`; never reuse your local dev value |
| `CORS_ORIGINS` | your Vercel URL once you have it (step 3) — can be updated after |

`backend/runtime.txt` pins the Python version (3.12.10, matching this
project's local `.venv`) so Render provisions the same interpreter.

### 3. Deploy the frontend to Vercel

Vercel auto-detects a Vite project — no build configuration needed beyond
the environment variable. [`frontend/vercel.json`](frontend/vercel.json)
adds one required rewrite rule: without it, refreshing (or directly
opening) any client-side route like `/dashboard/learn` would `404`, since
Vercel's static file server doesn't otherwise know those URLs should all
serve `index.html` and let `react-router-dom` handle the path.

In the Vercel dashboard: **Add New** → **Project** → import the repo,
setting the project root to `frontend/`. Add one environment variable:

| Variable | Value |
|---|---|
| `VITE_API_BASE_URL` | your Render backend's URL, e.g. `https://dailytechlearn-backend.onrender.com` |

### 4. Close the loop

Once both are live, update the backend's `CORS_ORIGINS` on Render to your
real Vercel URL (multiple origins can be comma-separated, e.g. if you keep
a preview deployment too) and redeploy the backend so the new value takes
effect.

### Future workflow, once this is set up

```
Local development → test locally → git add → git commit → git push
   → Vercel rebuilds the frontend automatically
   → Render rebuilds the backend automatically (runs migrations, restarts)
   → Live application updated
```

Local development stays fully independent of production — your `.env`
keeps pointing at your local Postgres and local ports; nothing about
day-to-day development depends on Render or Vercel existing at all.

### What's intentionally NOT done here

No real deployment was performed, no Render/Vercel account was created or
touched, and no production credentials exist yet — this phase only
prepares the configuration so that work is safe and mechanical whenever
you choose to do it. `GROQ_API_KEY`/`DATABASE_URL`/`JWT_SECRET_KEY` are
never in any committed file, never sent to the frontend, and never
logged — the same discipline established since Phase 8/14, just now also
documented for a second (production) environment.
