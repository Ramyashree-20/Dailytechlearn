"""Generates draft learning content by asking an LLM (via Groq) to explain a
topic in DailyTechLearn's structured format.

This is NOT the question-generation pipeline — see Phase 8 notes in
docs/architecture.md. Nothing produced here is saved to PostgreSQL. The
output is unreviewed AI text: structurally valid (enforced by
GeneratedLearningContent), but not verified for accuracy.

call_groq_json() is the shared low-level "talk to Groq, get back parsed
JSON" plumbing — reused by classification_service.py (Phase 10) so both
services share the same error handling instead of duplicating it.
"""

import json

import groq
from pydantic import ValidationError

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.schemas.ai import GeneratedLearningContent

REQUEST_TIMEOUT_SECONDS = 20.0

# Prompt engineering: wording the instructions precisely enough that the
# model reliably returns exactly the structure we need, not just "something
# roughly like it." Kept as one plain function/template — no framework.
SYSTEM_PROMPT = """You are a technical writer creating learning content for \
DailyTechLearn, an app that teaches AI/software engineers.

Given a topic or source material, produce a JSON object with EXACTLY these \
fields and no others:
- "question": a clear, natural question about the topic
- "answer": a correct, concise answer (2-4 sentences)
- "simple_explanation": an explanation a beginner could follow, avoiding \
unnecessary jargon
- "real_world_example": one concrete, realistic example of the concept in \
practice
- "business_relevance": why this matters to a business or product, in \
plain language
- "difficulty": exactly one of "beginner", "intermediate", or "advanced", \
judging how difficult this concept is for a software/AI engineer
- "keywords": a short comma-separated list of relevant keywords (e.g. \
"docker, container, deployment"), or an empty string if none apply

Rules:
- Return ONLY the JSON object. No markdown, no code fences, no text before \
or after it.
- Do not add fields beyond the seven listed.
- Do not invent specific statistics, company names, or version numbers you \
are not confident about.
- Keep each text field to a few sentences at most.
"""


class AIServiceError(Exception):
    """Raised when Groq can't be reached, is misconfigured, or returns
    something that can't be turned into valid structured data.

    Carries the HTTP status code the router should respond with, so the
    router doesn't need to guess based on the error message.
    """

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def call_groq_json(
    system_prompt: str, user_prompt: str, max_tokens: int | None = None
) -> dict:
    """Calls Groq in JSON mode and returns the parsed (but not yet
    schema-validated) dict. Raises AIServiceError on any failure — network,
    auth, rate limit, bad model, or invalid JSON.

    max_tokens caps the response length (and therefore cost) when a caller
    wants that bound — e.g. the Phase 15 learning assistant, which is
    triggered directly by user input rather than an admin action. Existing
    callers that omit it keep their current unbounded behavior."""
    if not GROQ_API_KEY:
        # Our own misconfiguration, not an upstream failure -> 500.
        raise AIServiceError("GROQ_API_KEY is not configured", status_code=500)

    client = groq.Groq(api_key=GROQ_API_KEY, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            **({"max_tokens": max_tokens} if max_tokens is not None else {}),
        )
    except groq.AuthenticationError as exc:
        raise AIServiceError("Groq rejected the API key (check GROQ_API_KEY)") from exc
    except groq.RateLimitError as exc:
        # 429: we're being throttled by Groq — a distinct, well-known signal
        # that the caller should slow down / try again shortly.
        raise AIServiceError("Groq rate limit exceeded — try again shortly", status_code=429) from exc
    except groq.NotFoundError as exc:
        raise AIServiceError(f"Groq model '{GROQ_MODEL}' was not found") from exc
    except groq.APITimeoutError as exc:
        raise AIServiceError("Groq request timed out") from exc
    except groq.APIConnectionError as exc:
        raise AIServiceError("Could not reach Groq (network error)") from exc
    except groq.APIStatusError as exc:
        raise AIServiceError(f"Groq returned an error status: {exc.status_code}") from exc

    raw_text = completion.choices[0].message.content

    try:
        return json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise AIServiceError("Groq returned invalid JSON") from exc


def _build_user_prompt(content: str) -> str:
    return f"Topic/content:\n{content}"


def generate_learning_content(content: str) -> GeneratedLearningContent:
    parsed = call_groq_json(SYSTEM_PROMPT, _build_user_prompt(content))
    try:
        return GeneratedLearningContent.model_validate(parsed)
    except ValidationError as exc:
        raise AIServiceError("Groq's response didn't match the expected structure") from exc
