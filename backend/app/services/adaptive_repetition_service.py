"""Adaptive spaced repetition (Phase 18) — replaces Phase 12's fixed
1 -> 3 -> 7 -> 14 -> 30 day lookup table (the same schedule for every
question, forever) with an ease-factor-driven schedule, so two questions
with different review histories end up on genuinely different schedules.

Pure interval/ease-factor math — no database access, no FastAPI, and no
Groq/AI involvement (see Phase 18 constraints: the backend alone owns
revision timing). Timezone-safe: the one datetime this module produces is
timezone-aware UTC, matching every other datetime in this app (Phase 12
established why mixing naive/aware datetimes here would be a silent
correctness bug, not a style nitpick).

Algorithm: a simplified SM-2 (SuperMemo-2), adapted for this app's binary
Easy/Hard input instead of SM-2's 0-5 quality scale.

- Every question starts at DEFAULT_EASE_FACTOR (2.5 — SM-2's traditional
  starting point): no review history yet, so no reason to assume it's
  easier or harder than average.
- The first two successful ("easy") reviews use fixed bootstrap intervals
  (1 day, then 3 days) — there is no prior interval to multiply yet, and
  inventing one would just be an arbitrary number in a different disguise.
  Classic SM-2 does the same thing (fixed I(1)/I(2), formula from I(3) on).
- From the third successful review on:
      next_interval = previous_interval * ease_factor
  capped at MAX_INTERVAL_DAYS. This is the actually adaptive part — a
  question with a higher ease_factor (consistently remembered easily)
  grows faster than one with a lower ease_factor (previously marked
  hard), even though both use the same formula.
- Each "easy" nudges ease_factor up by EASY_EASE_DELTA; each "hard" nudges
  it down by HARD_EASE_DELTA, floored at MIN_EASE_FACTOR so a rough patch
  never makes the interval collapse to (or below) zero.
- "Hard" also resets the bootstrap: review_count goes back to 0 and the
  interval drops back to FIRST_INTERVAL_DAYS — the same visible "back to
  reviewing it again soon" behavior Phase 12 had — but now combined with a
  lowered ease_factor, so the *next* run of easy reviews after a hard one
  grows more slowly than an unbroken streak of easy reviews would have.
  That's what makes two questions with different histories diverge over
  time (see docs/architecture.md for a worked example).
"""

from datetime import datetime, timedelta, timezone
from typing import Literal

ReviewResult = Literal["easy", "hard"]

DEFAULT_EASE_FACTOR = 2.5
MIN_EASE_FACTOR = 1.3
EASY_EASE_DELTA = 0.15
HARD_EASE_DELTA = -0.2

FIRST_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 3
# A cap, not a claim that anything is "fully learned forever" — without
# one, a long enough streak of easy reviews would push the interval out
# indefinitely. ~6 months is a reasonable product ceiling for this app.
MAX_INTERVAL_DAYS = 180

# A question that's had this many consecutive successful reviews (without
# an intervening "hard" reset) is considered well-consolidated in memory —
# reused by learning_service.get_dashboard() for "questions mastered"
# rather than that page inventing its own independent threshold.
MASTERED_REVIEW_COUNT_THRESHOLD = 5


def calculate_next_review(
    current_review_count: int,
    ease_factor: float,
    previous_interval_days: float,
    result: ReviewResult,
) -> tuple[int, float, datetime]:
    """Given the review state as it was BEFORE this review, returns the
    (new_review_count, new_ease_factor, next_review_at) to store.

    current_review_count: consecutive successful reviews so far, 0 for a
        brand-new question (never reviewed) or immediately after a "hard".
    ease_factor: the question's ease factor going into this review
        (DEFAULT_EASE_FACTOR for a brand-new question).
    previous_interval_days: the interval that was scheduled at the last
        review. Ignored when current_review_count is 0 or 1 (the fixed
        bootstrap stage doesn't multiply anything yet).
    """
    if result == "hard":
        new_ease_factor = max(MIN_EASE_FACTOR, ease_factor + HARD_EASE_DELTA)
        new_review_count = 0
        interval_days = FIRST_INTERVAL_DAYS
    else:
        new_ease_factor = max(MIN_EASE_FACTOR, ease_factor + EASY_EASE_DELTA)
        new_review_count = current_review_count + 1

        if current_review_count == 0:
            interval_days = FIRST_INTERVAL_DAYS
        elif current_review_count == 1:
            interval_days = SECOND_INTERVAL_DAYS
        else:
            # Floor of 1: two reviews landing on the same calendar day
            # (e.g. rapid manual testing) would otherwise multiply zero by
            # ease_factor forever and never grow.
            grown = round(max(1, previous_interval_days) * new_ease_factor)
            interval_days = min(MAX_INTERVAL_DAYS, max(1, grown))

    next_review_at = datetime.now(timezone.utc) + timedelta(days=interval_days)
    return new_review_count, new_ease_factor, next_review_at
