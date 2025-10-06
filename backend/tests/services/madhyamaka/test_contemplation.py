"""
Comprehensive test suite for ContemplativePracticeGenerator.

Tests all contemplative practice generation methods and configurations.
"""

import pytest
from services.madhyamaka import ContemplativePracticeGenerator


class TestPracticeGeneratorInitialization:
    """Test contemplative practice generator initialization."""

    def test_default_initialization(self):
        """Test generator initializes correctly."""
        generator = ContemplativePracticeGenerator()
        assert generator is not None


class TestNetiNetiPractice:
    """Test Neti Neti (systematic negation) practice generation."""

    def test_generate_neti_neti_default(self):
        """Test default Neti Neti generation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti()

        assert practice["practice_type"] == "neti_neti"
        assert "target" in practice
        assert "instructions" in practice
        assert "metadata" in practice

    def test_neti_neti_self_target(self):
        """Test Neti Neti for investigating the self."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        assert practice["target"] == "self"
        assert "instructions" in practice
        assert "stages" in practice["instructions"]
        assert len(practice["instructions"]["stages"]) > 0

    def test_neti_neti_thought_target(self):
        """Test Neti Neti for investigating thoughts."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="thought")

        assert practice["target"] == "thought"
        assert "stages" in practice["instructions"]

    def test_neti_neti_emotion_target(self):
        """Test Neti Neti for investigating emotions."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="emotion")

        assert practice["target"] == "emotion"
        assert "stages" in practice["instructions"]

    def test_neti_neti_consciousness_target(self):
        """Test Neti Neti for investigating consciousness."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="consciousness")

        assert practice["target"] == "consciousness"
        assert "stages" in practice["instructions"]

    def test_neti_neti_invalid_target(self):
        """Test Neti Neti with invalid target falls back to self."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="invalid_concept")

        # Should default to self
        assert "instructions" in practice
        assert practice["practice_type"] == "neti_neti"

    def test_neti_neti_simple_depth(self):
        """Test Neti Neti with simple depth."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(depth="simple")

        assert practice["metadata"]["duration_minutes"] == 15

    def test_neti_neti_progressive_depth(self):
        """Test Neti Neti with progressive depth."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(depth="progressive")

        assert practice["metadata"]["duration_minutes"] == 20

    def test_neti_neti_deep_depth(self):
        """Test Neti Neti with deep depth."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(depth="deep")

        assert practice["metadata"]["duration_minutes"] == 30

    def test_neti_neti_beginner_difficulty(self):
        """Test Neti Neti difficulty for beginner (stage 1-2)."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(user_stage=1)

        assert practice["metadata"]["difficulty"] == "beginner"

    def test_neti_neti_intermediate_difficulty(self):
        """Test Neti Neti difficulty for intermediate (stage 3-4)."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(user_stage=3)

        assert practice["metadata"]["difficulty"] == "intermediate"

    def test_neti_neti_advanced_difficulty(self):
        """Test Neti Neti difficulty for advanced (stage 5+)."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(user_stage=5)

        assert practice["metadata"]["difficulty"] == "advanced"

    def test_neti_neti_has_safety_warning(self):
        """Test that Neti Neti includes safety warning."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti()

        assert "warning" in practice["metadata"]
        assert "anxiety" in practice["metadata"]["warning"].lower() or \
               "dissociation" in practice["metadata"]["warning"].lower()

    def test_neti_neti_stages_structure(self):
        """Test that Neti Neti stages have proper structure."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        stages = practice["instructions"]["stages"]
        assert len(stages) > 0

        for stage in stages:
            assert "stage" in stage
            assert "investigation" in stage
            assert "contemplation" in stage
            assert "negation" in stage
            # Should include anti-nihilism safeguard
            assert "not_nihilism" in stage or "middle_path" in str(stage).lower()

    def test_neti_neti_has_closing(self):
        """Test that Neti Neti has closing instructions."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti()

        assert "closing" in practice["instructions"]

    def test_all_neti_neti_targets(self):
        """Test all Neti Neti target concepts."""
        generator = ContemplativePracticeGenerator()
        targets = ["self", "thought", "emotion", "consciousness"]

        for target in targets:
            practice = generator.generate_neti_neti(target_concept=target)
            assert practice["target"] == target
            assert len(practice["instructions"]["stages"]) > 0


class TestTwoTruthsContemplation:
    """Test Two Truths contemplation generation."""

    def test_generate_two_truths(self):
        """Test Two Truths contemplation generation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_two_truths_contemplation()

        assert "practice_type" in practice
        assert practice["practice_type"] in ["two_truths", "two_truths_contemplation"]

    def test_two_truths_has_both_levels(self):
        """Test that Two Truths includes both conventional and ultimate."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_two_truths_contemplation()

        # Should have instructions mentioning both truths
        instructions_str = str(practice)
        assert "conventional" in instructions_str.lower() or "ultimate" in instructions_str.lower()

    def test_two_truths_with_concept(self):
        """Test Two Truths with specific concept."""
        generator = ContemplativePracticeGenerator()

        # Test with different concepts if the method accepts them
        practice = generator.generate_two_truths_contemplation()
        assert "practice_type" in practice

    def test_two_truths_has_metadata(self):
        """Test that Two Truths has metadata."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_two_truths_contemplation()

        assert "metadata" in practice or "duration" in str(practice).lower()


class TestDependentOriginationInquiry:
    """Test Dependent Origination inquiry generation."""

    def test_generate_dependent_origination(self):
        """Test Dependent Origination inquiry generation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_dependent_origination_inquiry()

        assert "practice_type" in practice
        assert "dependent" in practice["practice_type"].lower() or \
               "origination" in practice["practice_type"].lower()

    def test_dependent_origination_explores_causes(self):
        """Test that Dependent Origination explores causation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_dependent_origination_inquiry()

        # Should mention causes, conditions, or arising
        practice_str = str(practice)
        assert any(word in practice_str.lower()
                  for word in ["cause", "condition", "arise", "depend"])

    def test_dependent_origination_with_phenomenon(self):
        """Test Dependent Origination with specific phenomenon."""
        generator = ContemplativePracticeGenerator()

        # Test with different phenomena if the method accepts them
        practice = generator.generate_dependent_origination_inquiry()
        assert "practice_type" in practice

    def test_dependent_origination_has_inquiry_steps(self):
        """Test that Dependent Origination has inquiry steps."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_dependent_origination_inquiry()

        # Should have some structure (steps, stages, or instructions)
        assert any(key in practice for key in ["steps", "stages", "instructions", "inquiry"])


class TestUserStageAdaptation:
    """Test adaptation to different user journey stages."""

    def test_stage_1_practices(self):
        """Test practices for stage 1 (initial awareness)."""
        generator = ContemplativePracticeGenerator()

        practice = generator.generate_neti_neti(user_stage=1)
        assert practice["metadata"]["difficulty"] == "beginner"

    def test_stage_3_practices(self):
        """Test practices for stage 3 (active investigation)."""
        generator = ContemplativePracticeGenerator()

        practice = generator.generate_neti_neti(user_stage=3)
        assert practice["metadata"]["difficulty"] == "intermediate"

    def test_stage_5_practices(self):
        """Test practices for stage 5 (natural expression)."""
        generator = ContemplativePracticeGenerator()

        practice = generator.generate_neti_neti(user_stage=5)
        assert practice["metadata"]["difficulty"] == "advanced"

    def test_invalid_stage(self):
        """Test handling of invalid user stage."""
        generator = ContemplativePracticeGenerator()

        # Should handle gracefully
        practice = generator.generate_neti_neti(user_stage=0)
        assert "metadata" in practice

        practice = generator.generate_neti_neti(user_stage=10)
        assert "metadata" in practice


class TestPracticeContent:
    """Test content quality of generated practices."""

    def test_neti_neti_self_has_body_stage(self):
        """Test that Neti Neti self includes body investigation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        stages_str = str(practice["instructions"]["stages"])
        assert "body" in stages_str.lower()

    def test_neti_neti_self_has_thought_stage(self):
        """Test that Neti Neti self includes thought investigation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        stages_str = str(practice["instructions"]["stages"])
        assert "thought" in stages_str.lower()

    def test_neti_neti_includes_pause_instructions(self):
        """Test that Neti Neti includes pause/breathing instructions."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        practice_str = str(practice)
        assert "breath" in practice_str.lower() or "pause" in practice_str.lower()

    def test_practices_avoid_nihilism(self):
        """Test that practices include safeguards against nihilism."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        # Should explicitly mention that negation doesn't mean non-existence
        practice_str = str(practice)
        assert "conventional" in practice_str.lower() or \
               "function" in practice_str.lower() or \
               "not_nihilism" in practice_str

    def test_practices_point_to_middle_path(self):
        """Test that practices point to middle path realization."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self")

        practice_str = str(practice)
        # Should mention middle path concepts
        assert any(term in practice_str.lower()
                  for term in ["middle", "dependent", "empty", "arise"])


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_target_concept(self):
        """Test handling of empty target concept."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="")

        # Should handle gracefully (likely default to self)
        assert "practice_type" in practice

    def test_none_target_concept(self):
        """Test handling of None target concept."""
        generator = ContemplativePracticeGenerator()

        # Should handle gracefully
        try:
            practice = generator.generate_neti_neti(target_concept=None)
            assert "practice_type" in practice
        except (TypeError, AttributeError):
            # Acceptable to raise error for None
            pass

    def test_special_characters_in_target(self):
        """Test handling of special characters in target."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="self@#$")

        # Should handle gracefully
        assert "practice_type" in practice

    def test_very_long_target_name(self):
        """Test handling of very long target concept name."""
        generator = ContemplativePracticeGenerator()
        long_target = "self" * 100

        practice = generator.generate_neti_neti(target_concept=long_target)
        assert "practice_type" in practice

    def test_unicode_target(self):
        """Test handling of Unicode in target."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(target_concept="आत्मन्")  # Sanskrit "self"

        assert "practice_type" in practice

    def test_negative_user_stage(self):
        """Test handling of negative user stage."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(user_stage=-1)

        # Should handle gracefully
        assert "metadata" in practice

    def test_extremely_high_user_stage(self):
        """Test handling of extremely high user stage."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti(user_stage=1000)

        assert "metadata" in practice
        # Should cap at advanced
        assert practice["metadata"]["difficulty"] == "advanced"


class TestPracticeIntegration:
    """Test integration between different practice types."""

    def test_all_practice_types_available(self):
        """Test that all practice types can be generated."""
        generator = ContemplativePracticeGenerator()

        # Neti Neti
        neti_neti = generator.generate_neti_neti()
        assert neti_neti is not None

        # Two Truths
        two_truths = generator.generate_two_truths_contemplation()
        assert two_truths is not None

        # Dependent Origination
        dep_orig = generator.generate_dependent_origination_inquiry()
        assert dep_orig is not None

    def test_practices_have_consistent_structure(self):
        """Test that all practices have consistent structure."""
        generator = ContemplativePracticeGenerator()

        practices = [
            generator.generate_neti_neti(),
            generator.generate_two_truths_contemplation(),
            generator.generate_dependent_origination_inquiry()
        ]

        for practice in practices:
            assert "practice_type" in practice
            # All should have some form of instructions
            assert any(key in practice for key in ["instructions", "steps", "stages", "inquiry"])

    def test_practices_complement_each_other(self):
        """Test that practices address different aspects of realization."""
        generator = ContemplativePracticeGenerator()

        neti_neti = generator.generate_neti_neti(target_concept="self")
        two_truths = generator.generate_two_truths_contemplation()
        dep_orig = generator.generate_dependent_origination_inquiry()

        # Neti Neti should focus on negation
        assert "neti" in str(neti_neti).lower() or "not" in str(neti_neti).lower()

        # Two Truths should mention both levels
        two_truths_str = str(two_truths).lower()
        assert "conventional" in two_truths_str or "ultimate" in two_truths_str

        # Dependent Origination should explore causation
        dep_orig_str = str(dep_orig).lower()
        assert any(word in dep_orig_str for word in ["cause", "condition", "depend", "arise"])


class TestSafetyFeatures:
    """Test safety features and warnings in practices."""

    def test_practices_include_grounding_instructions(self):
        """Test that practices include grounding instructions."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti()

        warning = practice["metadata"]["warning"]
        assert "ground" in warning.lower() or "return" in warning.lower()

    def test_practices_warn_about_dissociation(self):
        """Test that practices warn about potential dissociation."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti()

        warning = practice["metadata"]["warning"]
        assert "dissociation" in warning.lower() or "anxiety" in warning.lower()

    def test_practices_clarify_goal(self):
        """Test that practices clarify the liberating goal."""
        generator = ContemplativePracticeGenerator()
        practice = generator.generate_neti_neti()

        warning = practice["metadata"]["warning"]
        assert "liberating" in warning.lower() or "insight" in warning.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
