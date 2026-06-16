"""Tests for SelfAssessmentEngine edge cases — _parse_score fallthrough at line 353."""

from unittest.mock import MagicMock, patch

import pytest

from app.self_improvement.assessment import SelfAssessmentEngine


class TestParseScoreFallthrough:
    def test_parse_score_value_1_0_hits_line_353(self):
        """Text 'value=1.0' doesn't match 0.X pattern (starts with 1)."""
        result = SelfAssessmentEngine._parse_score(None, "value=1.0")
        assert result == 0.01  # 1.0 falls in 0-100 range → divided by 100

    def test_parse_score_value_0_5_fallback(self):
        """Text 'score 0.5' matches first try; '0.5' -> 0.5."""
        result = SelfAssessmentEngine._parse_score(None, "score 0.5")
        assert result == 0.5

    def test_parse_score_negative_in_fallback_then_positive(self):
        """First match is negative, second is 0.5 -> first try fails."""
        with patch("app.self_improvement.assessment.re.findall") as mock_findall:
            mock_findall.side_effect = [[], ["-1", "0.5"]]
            result = SelfAssessmentEngine._parse_score(None, "text")
            # num=-1, 0 <= num <= 100? No. 0 <= num <= 1? No. num > 100? No. num < 0? Yes -> return 0.0
            assert result == 0.0
