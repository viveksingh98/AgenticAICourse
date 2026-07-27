"""Model routing and request configuration for the Riyaz grader.

Routing is by *rubric difficulty*, never by user tier — see BLUEPRINT.md section 9.
Giving paid users a different grader means two learners get different scores for the
same answer, which is indefensible the moment anyone notices.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GraderModel:
    """One grading tier: which model, how it is configured, what it costs."""

    tier: str
    model_id: str
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    min_cacheable_tokens: int
    supports_effort: bool
    thinking_off_requires_explicit_disable: bool
    max_tokens: int = 700

    def request_kwargs(self) -> dict:
        """Extra kwargs for messages.create() beyond model/system/messages.

        Two model-specific quirks are handled here rather than at the call site:

        * ``effort`` is rejected outright by Haiku 4.5, so it is only sent for tiers
          that support it.
        * Sonnet 5 runs adaptive thinking *by default*; grading is binary criterion
          checking, not a reasoning marathon, so we explicitly disable it. Haiku 4.5
          does not think unless asked, so it needs nothing.
        """
        output_config: dict = {
            "format": {
                "type": "json_schema",
                "schema": JUDGE_OUTPUT_SCHEMA,
            }
        }
        if self.supports_effort:
            output_config["effort"] = "low"

        kwargs: dict = {
            "max_tokens": self.max_tokens,
            "output_config": output_config,
        }
        if self.thinking_off_requires_explicit_disable:
            kwargs["thinking"] = {"type": "disabled"}
        return kwargs

    def cost_usd(self, usage) -> float:
        """Cost of one grade from a response ``usage`` object.

        Cache reads bill at ~0.1x base input; cache writes at ~1.25x (5-minute TTL).
        """
        fresh = getattr(usage, "input_tokens", 0) or 0
        cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
        cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
        out = getattr(usage, "output_tokens", 0) or 0

        effective_in = fresh + (cache_read * 0.1) + (cache_write * 1.25)
        return (
            effective_in * self.input_usd_per_mtok / 1_000_000
            + out * self.output_usd_per_mtok / 1_000_000
        )


# Pricing: Anthropic first-party API rates as of 2026-07-27.
# Sonnet 5 carries introductory pricing ($2/$10) through 2026-08-31; standard rates
# are used here so nothing silently changes on 1 September.
STANDARD = GraderModel(
    tier="standard",
    model_id="claude-haiku-4-5",
    input_usd_per_mtok=1.00,
    output_usd_per_mtok=5.00,
    # The number that shapes the whole cost model. A grading system prompt below this
    # length silently will not cache on Haiku — no error, just a ~2.25x bill.
    min_cacheable_tokens=4096,
    supports_effort=False,
    thinking_off_requires_explicit_disable=False,
)

HARD = GraderModel(
    tier="hard",
    model_id="claude-sonnet-5",
    input_usd_per_mtok=3.00,
    output_usd_per_mtok=15.00,
    min_cacheable_tokens=1024,
    supports_effort=True,
    thinking_off_requires_explicit_disable=True,
)

TIERS = {"standard": STANDARD, "hard": HARD}


def for_tier(tier: str) -> GraderModel:
    if tier not in TIERS:
        raise ValueError(f"unknown grader_tier {tier!r}; expected one of {sorted(TIERS)}")
    return TIERS[tier]


JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "met": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["id", "met", "evidence"],
                "additionalProperties": False,
            },
        },
        "strongest": {"type": "string"},
        "weakest": {"type": "string"},
    },
    "required": ["criteria", "strongest", "weakest"],
    "additionalProperties": False,
}
