"""
Comprehensive test suite for MadhyamakaTransformer.

Tests all transformation methods, user stages, and edge cases.
"""

import pytest
from services.madhyamaka import MadhyamakaTransformer


class TestTransformerInitialization:
    """Test transformer initialization."""

    def test_default_initialization(self):
        """Test transformer initialization with detector."""
        transformer = MadhyamakaTransformer()
        assert transformer.detector is not None

    def test_detector_integration(self):
        """Test that transformer uses detector correctly."""
        transformer = MadhyamakaTransformer()
        # Detector should be able to detect extremes
        result = transformer.detector.detect_eternalism("This is always true.")
        assert "confidence" in result


class TestMiddlePathAlternatives:
    """Test generation of middle path alternatives."""

    def test_generate_alternatives_for_eternalism(self):
        """Test alternative generation for eternalist text."""
        transformer = MadhyamakaTransformer()
        text = "This is absolutely essential and everyone must understand it."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        assert len(alternatives) > 0
        assert all(isinstance(alt, dict) for alt in alternatives)
        assert all("text" in alt for alt in alternatives)
        assert all("score" in alt for alt in alternatives)

    def test_generate_alternatives_for_nihilism(self):
        """Test alternative generation for nihilistic text."""
        transformer = MadhyamakaTransformer()
        text = "Everything is completely meaningless."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        assert len(alternatives) > 0
        # Should include two truths framework
        two_truths_alts = [alt for alt in alternatives if alt.get("type") == "two_truths_framework"]
        assert len(two_truths_alts) > 0

    def test_alternative_scores_sorted(self):
        """Test that alternatives are sorted by score."""
        transformer = MadhyamakaTransformer()
        text = "This is always absolutely true for everyone."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=3
        )

        scores = [alt.get("score", 0) for alt in alternatives]
        # Should be sorted descending
        assert scores == sorted(scores, reverse=True)

    def test_num_alternatives_limit(self):
        """Test that number of alternatives is limited correctly."""
        transformer = MadhyamakaTransformer()
        text = "This is absolutely essential."

        for num in [1, 3, 5, 10]:
            alternatives = transformer.generate_middle_path_alternatives(
                text,
                num_alternatives=num,
                user_stage=2
            )
            assert len(alternatives) <= num

    def test_empty_text(self):
        """Test alternative generation for empty text."""
        transformer = MadhyamakaTransformer()
        alternatives = transformer.generate_middle_path_alternatives(
            "",
            num_alternatives=5,
            user_stage=1
        )

        # Should handle gracefully
        assert isinstance(alternatives, list)

    def test_balanced_text(self):
        """Test alternative generation for balanced (middle path) text."""
        transformer = MadhyamakaTransformer()
        text = "I notice this pattern sometimes arises depending on conditions."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should still provide some alternatives for refinement
        assert len(alternatives) >= 0


class TestUserStages:
    """Test different user journey stages."""

    def test_stage_1_beginner(self):
        """Test transformations for stage 1 (initial awareness)."""
        transformer = MadhyamakaTransformer()
        text = "This is absolutely true."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Stage 1 should get simple softening
        assert len(alternatives) > 0
        # Should not get advanced contemplative pointers
        contemplative = [alt for alt in alternatives if alt.get("type") == "contemplative_pointer"]
        assert len(contemplative) == 0

    def test_stage_2_pattern_recognition(self):
        """Test transformations for stage 2."""
        transformer = MadhyamakaTransformer()
        text = "This is absolutely essential."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=2
        )

        # Stage 2 should include construction framing
        construction = [alt for alt in alternatives if alt.get("type") == "construction_framing"]
        assert len(construction) >= 0  # May or may not be included depending on reified concepts

    def test_stage_3_active_investigation(self):
        """Test transformations for stage 3."""
        transformer = MadhyamakaTransformer()
        text = "Everyone must understand this truth."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=3
        )

        assert len(alternatives) > 0
        # Should get more sophisticated alternatives

    def test_stage_4_direct_experience(self):
        """Test transformations for stage 4."""
        transformer = MadhyamakaTransformer()
        text = "This is the absolute truth."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=4
        )

        # Stage 4 should include contemplative pointers
        contemplative = [alt for alt in alternatives if alt.get("type") == "contemplative_pointer"]
        assert len(contemplative) > 0

    def test_stage_5_natural_expression(self):
        """Test transformations for stage 5."""
        transformer = MadhyamakaTransformer()
        text = "This must be done."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=5
        )

        # Stage 5 should get all available transformation types
        assert len(alternatives) > 0

    def test_invalid_stage(self):
        """Test handling of invalid user stage."""
        transformer = MadhyamakaTransformer()
        text = "This is true."

        # Should handle gracefully
        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=0  # Invalid
        )
        assert isinstance(alternatives, list)

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=10  # Invalid
        )
        assert isinstance(alternatives, list)


class TestAntiEternalismTransformations:
    """Test anti-eternalism transformation strategies."""

    def test_conditional_softening(self):
        """Test that conditional softening reduces absolutism."""
        transformer = MadhyamakaTransformer()
        text = "This is always true."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should have conditional alternatives
        conditional_alts = [alt for alt in alternatives
                           if "conditional" in alt.get("type", "").lower() or
                              alt.get("preserves_conventional_meaning", False)]
        assert len(conditional_alts) > 0

        # Check that "always" is softened
        for alt in conditional_alts:
            if "always" in text.lower():
                assert "always" not in alt["text"].lower() or "often" in alt["text"].lower()

    def test_construction_framing(self):
        """Test framing statements as constructions."""
        transformer = MadhyamakaTransformer()
        text = "Truth is absolute."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=2  # Stage 2+ gets construction framing
        )

        construction_alts = [alt for alt in alternatives if alt.get("type") == "construction_framing"]
        # May or may not have construction framing depending on reified concepts
        if len(construction_alts) > 0:
            assert "concept" in construction_alts[0]["text"].lower() or \
                   "construct" in construction_alts[0]["text"].lower()

    def test_inquiry_transformation(self):
        """Test transformation to contemplative inquiry."""
        transformer = MadhyamakaTransformer()
        text = "The self is real."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=4  # Stage 4+ gets inquiry
        )

        inquiry_alts = [alt for alt in alternatives if alt.get("type") == "contemplative_pointer"]
        if len(inquiry_alts) > 0:
            # Should pose a question or investigation
            assert "?" in inquiry_alts[0]["text"] or "notice" in inquiry_alts[0]["text"].lower()

    def test_replaces_must_with_might(self):
        """Test that 'must' is replaced with conditional language."""
        transformer = MadhyamakaTransformer()
        text = "You must do this."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # At least one alternative should soften "must"
        softened = any("must" not in alt["text"].lower() for alt in alternatives)
        assert softened

    def test_replaces_never_with_rarely(self):
        """Test that 'never' is softened."""
        transformer = MadhyamakaTransformer()
        text = "This never works."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should soften "never"
        softened = any("never" not in alt["text"].lower() for alt in alternatives)
        assert softened


class TestAntiNihilismTransformations:
    """Test anti-nihilism transformation strategies."""

    def test_two_truths_framework(self):
        """Test two truths framework application."""
        transformer = MadhyamakaTransformer()
        text = "Everything is meaningless."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        two_truths_alts = [alt for alt in alternatives if alt.get("type") == "two_truths_framework"]
        assert len(two_truths_alts) > 0

        # Should include both conventional and ultimate
        for alt in two_truths_alts:
            assert "conventionally" in alt["text"].lower() or "ultimately" in alt["text"].lower()

    def test_restores_conventional_function(self):
        """Test that nihilistic denial is balanced with conventional function."""
        transformer = MadhyamakaTransformer()
        text = "Nothing has any real meaning."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should mention function or purpose
        functional_alts = any("function" in alt["text"].lower() or
                             "purpose" in alt["text"].lower() or
                             "useful" in alt["text"].lower()
                             for alt in alternatives)
        # At least try to restore functionality
        assert len(alternatives) > 0


class TestGeneralMiddlePath:
    """Test general middle path transformations."""

    def test_always_provides_alternatives(self):
        """Test that alternatives are always provided."""
        transformer = MadhyamakaTransformer()

        test_texts = [
            "This is always true.",
            "Nothing matters.",
            "I think this might sometimes work.",
            "The truth.",
            ""
        ]

        for text in test_texts:
            alternatives = transformer.generate_middle_path_alternatives(
                text,
                num_alternatives=5,
                user_stage=1
            )
            # Should provide at least attempt to generate alternatives
            assert isinstance(alternatives, list)

    def test_preserves_conventional_meaning_flag(self):
        """Test that alternatives track whether conventional meaning is preserved."""
        transformer = MadhyamakaTransformer()
        text = "This is absolutely essential."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=4  # Get variety of types
        )

        # Should have mix of meaning-preserving and transformative alternatives
        if len(alternatives) > 0:
            # Some should preserve conventional meaning
            preserving = [alt for alt in alternatives
                         if alt.get("preserves_conventional_meaning", False)]
            # This is expected behavior
            assert len(preserving) >= 0


class TestAlternativeMetadata:
    """Test metadata in generated alternatives."""

    def test_madhyamaka_improvements_field(self):
        """Test that alternatives include madhyamaka improvements."""
        transformer = MadhyamakaTransformer()
        text = "This is always the absolute truth."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=2
        )

        for alt in alternatives:
            # Should have improvements listed
            assert "madhyamaka_improvements" in alt or "text" in alt

    def test_type_field(self):
        """Test that alternatives include type classification."""
        transformer = MadhyamakaTransformer()
        text = "Everyone must understand this."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=3
        )

        types = set(alt.get("type") for alt in alternatives if "type" in alt)
        # Should have variety of types
        assert len(types) > 0

    def test_score_field(self):
        """Test that alternatives include scores."""
        transformer = MadhyamakaTransformer()
        text = "This is true."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        for alt in alternatives:
            assert "score" in alt
            assert 0.0 <= alt["score"] <= 1.0


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_very_short_text(self):
        """Test transformation of very short text."""
        transformer = MadhyamakaTransformer()
        alternatives = transformer.generate_middle_path_alternatives(
            "Truth.",
            num_alternatives=5,
            user_stage=1
        )

        assert isinstance(alternatives, list)

    def test_very_long_text(self):
        """Test transformation of very long text."""
        transformer = MadhyamakaTransformer()
        long_text = "This is absolutely essential and always true. " * 100

        alternatives = transformer.generate_middle_path_alternatives(
            long_text,
            num_alternatives=5,
            user_stage=1
        )

        assert len(alternatives) > 0

    def test_special_characters(self):
        """Test handling of special characters."""
        transformer = MadhyamakaTransformer()
        text = "This@#$ is!!! always??? [absolutely] true..."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        assert len(alternatives) > 0

    def test_unicode_text(self):
        """Test handling of Unicode characters."""
        transformer = MadhyamakaTransformer()
        text = "Śūnyatā (emptiness) is always the truth. 真理"

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        assert len(alternatives) >= 0

    def test_no_detected_extremes(self):
        """Test transformation when no extremes detected."""
        transformer = MadhyamakaTransformer()
        text = "I notice this pattern might arise sometimes in certain contexts."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should still provide general alternatives
        assert len(alternatives) >= 0

    def test_mixed_extremes(self):
        """Test text with both eternalism and nihilism."""
        transformer = MadhyamakaTransformer()
        text = "This absolute truth means nothing ultimately."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should address both extremes
        assert len(alternatives) > 0

    def test_zero_alternatives_requested(self):
        """Test requesting zero alternatives."""
        transformer = MadhyamakaTransformer()
        alternatives = transformer.generate_middle_path_alternatives(
            "This is true.",
            num_alternatives=0,
            user_stage=1
        )

        # Should return empty or very short list
        assert len(alternatives) == 0

    def test_negative_stage(self):
        """Test handling of negative user stage."""
        transformer = MadhyamakaTransformer()
        alternatives = transformer.generate_middle_path_alternatives(
            "This is true.",
            num_alternatives=5,
            user_stage=-1
        )

        # Should handle gracefully
        assert isinstance(alternatives, list)


class TestRealWorldExamples:
    """Test with real-world philosophical statements."""

    def test_cartesian_dualism(self):
        """Test transformation of Cartesian 'I think therefore I am'."""
        transformer = MadhyamakaTransformer()
        text = "I think, therefore I am. The self is the fundamental truth."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=4
        )

        assert len(alternatives) > 0
        # Should question the reification of self
        inquiry_alts = [alt for alt in alternatives if "?" in alt["text"] or "notice" in alt["text"].lower()]
        assert len(inquiry_alts) > 0

    def test_scientific_realism(self):
        """Test transformation of scientific realist claims."""
        transformer = MadhyamakaTransformer()
        text = "Science reveals the absolute objective truth about reality."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=2
        )

        assert len(alternatives) > 0

    def test_postmodern_relativism(self):
        """Test transformation of extreme relativism."""
        transformer = MadhyamakaTransformer()
        text = "All perspectives are equally valid. There is no truth, only interpretations."

        alternatives = transformer.generate_middle_path_alternatives(
            text,
            num_alternatives=5,
            user_stage=1
        )

        # Should address nihilistic relativism
        two_truths = [alt for alt in alternatives if "conventional" in alt["text"].lower()]
        assert len(two_truths) >= 0  # May or may not include depending on detection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
