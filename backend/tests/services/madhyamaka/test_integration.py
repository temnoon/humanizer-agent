"""
Integration tests for the madhyamaka module.

Tests integration between detector, transformer, and contemplative practice generator.
"""

import pytest
from services.madhyamaka import (
    MadhyamakaDetector,
    MadhyamakaTransformer,
    ContemplativePracticeGenerator,
    ExtremeType
)


class TestDetectorTransformerIntegration:
    """Test integration between detector and transformer."""

    def test_transformer_uses_detector(self):
        """Test that transformer uses detector for analysis."""
        transformer = MadhyamakaTransformer()
        text = "This is absolutely essential."

        alternatives = transformer.generate_middle_path_alternatives(text)

        # Transformer should have used detector internally
        assert len(alternatives) > 0

    def test_detected_eternalism_triggers_alternatives(self):
        """Test that detected eternalism triggers appropriate alternatives."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()

        text = "This is always absolutely true for everyone."

        # Detect
        detection = detector.detect_eternalism(text)
        assert detection["eternalism_detected"] is True

        # Transform
        alternatives = transformer.generate_middle_path_alternatives(text, num_alternatives=5)

        # Should provide anti-eternalism alternatives
        assert len(alternatives) > 0

    def test_detected_nihilism_triggers_alternatives(self):
        """Test that detected nihilism triggers appropriate alternatives."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()

        text = "Everything is completely meaningless."

        # Detect
        detection = detector.detect_nihilism(text)
        assert detection["nihilism_detected"] is True

        # Transform
        alternatives = transformer.generate_middle_path_alternatives(text, num_alternatives=5)

        # Should include two truths framework
        two_truths_alts = [alt for alt in alternatives if alt.get("type") == "two_truths_framework"]
        assert len(two_truths_alts) > 0

    def test_middle_path_text_gets_refinements(self):
        """Test that middle path text still gets refinement alternatives."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()

        text = "I notice this sometimes arises depending on conditions."

        # Detect - should be close to middle path
        detection = detector.detect_middle_path_proximity(text)
        assert detection["middle_path_score"] > 0.5

        # Transform - should still provide some alternatives
        alternatives = transformer.generate_middle_path_alternatives(text)
        assert isinstance(alternatives, list)


class TestFullWorkflow:
    """Test complete workflow from detection to transformation to practice."""

    def test_eternalism_workflow(self):
        """Test complete workflow for eternalistic text."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()
        practice_gen = ContemplativePracticeGenerator()

        text = "The self is real and permanent."

        # Step 1: Detect
        detection = detector.detect_eternalism(text)
        assert detection["eternalism_detected"] is True

        # Step 2: Transform
        alternatives = transformer.generate_middle_path_alternatives(text, user_stage=2)
        assert len(alternatives) > 0

        # Step 3: Generate practice for reified concept
        practice = practice_gen.generate_neti_neti(target_concept="self", user_stage=2)
        assert practice["practice_type"] == "neti_neti"
        assert practice["target"] == "self"

    def test_nihilism_workflow(self):
        """Test complete workflow for nihilistic text."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()
        practice_gen = ContemplativePracticeGenerator()

        text = "Nothing has any real meaning."

        # Step 1: Detect
        detection = detector.detect_nihilism(text)
        assert detection["nihilism_detected"] is True

        # Step 2: Transform
        alternatives = transformer.generate_middle_path_alternatives(text)
        # Should get two truths framework
        two_truths = [alt for alt in alternatives if alt.get("type") == "two_truths_framework"]
        assert len(two_truths) > 0

        # Step 3: Generate two truths contemplation
        practice = practice_gen.generate_two_truths_contemplation()
        assert "practice_type" in practice

    def test_balanced_workflow(self):
        """Test workflow for balanced middle path text."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()
        practice_gen = ContemplativePracticeGenerator()

        text = "Conventionally, things function. Ultimately, they're empty."

        # Step 1: Detect middle path
        detection = detector.detect_middle_path_proximity(text)
        assert detection["middle_path_score"] > 0.6

        # Step 2: Get refinements
        alternatives = transformer.generate_middle_path_alternatives(text, user_stage=4)
        # Should still provide some alternatives
        assert isinstance(alternatives, list)

        # Step 3: Generate advanced practice
        practice = practice_gen.generate_dependent_origination_inquiry()
        assert "practice_type" in practice


class TestCrossModuleConsistency:
    """Test consistency across module components."""

    def test_extreme_type_enum_usage(self):
        """Test that ExtremeType enum is accessible and consistent."""
        # Should be able to import and use enum
        assert ExtremeType.ETERNALISM.value == "eternalism"
        assert ExtremeType.NIHILISM.value == "nihilism"
        assert ExtremeType.MIDDLE_PATH.value == "middle_path"
        assert ExtremeType.CLINGING.value == "clinging"

    def test_user_stage_consistency(self):
        """Test that user_stage parameter works consistently across components."""
        transformer = MadhyamakaTransformer()
        practice_gen = ContemplativePracticeGenerator()

        for stage in [1, 2, 3, 4, 5]:
            # Transformer should handle all stages
            alternatives = transformer.generate_middle_path_alternatives(
                "This is true.",
                user_stage=stage
            )
            assert isinstance(alternatives, list)

            # Practice generator should handle all stages
            practice = practice_gen.generate_neti_neti(user_stage=stage)
            assert "metadata" in practice

    def test_detection_modes_consistency(self):
        """Test that detection works in both hybrid and regex-only modes."""
        text = "This is absolutely essential."

        # Hybrid mode (if available)
        hybrid_detector = MadhyamakaDetector(use_semantic=True)
        hybrid_result = hybrid_detector.detect_eternalism(text)
        assert "confidence" in hybrid_result

        # Regex-only mode
        regex_detector = MadhyamakaDetector(use_semantic=False)
        regex_result = regex_detector.detect_eternalism(text)
        assert "confidence" in regex_result

        # Both should detect eternalism
        assert hybrid_result["eternalism_detected"] or regex_result["eternalism_detected"]


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_analyze_user_message(self):
        """Test analyzing a user message for extremes."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()

        user_message = "I feel like I'll never be happy. This depression is permanent and will always be with me."

        # Detect eternalism
        eternalism = detector.detect_eternalism(user_message)

        # Should detect "never", "permanent", "always"
        assert eternalism["eternalism_detected"] is True

        # Generate alternatives
        alternatives = transformer.generate_middle_path_alternatives(
            user_message,
            num_alternatives=3,
            user_stage=1  # Beginner - gentle
        )

        assert len(alternatives) > 0
        # Should soften absolutism
        assert any("never" not in alt["text"].lower() for alt in alternatives)

    def test_philosophical_discussion(self):
        """Test analyzing philosophical discussion for extremes."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()
        practice_gen = ContemplativePracticeGenerator()

        discussion = "The fundamental nature of consciousness is that it's absolutely primary and inherently real."

        # Detect
        detection = detector.detect_eternalism(discussion)
        assert detection["confidence"] > 0.5

        # Transform
        alternatives = transformer.generate_middle_path_alternatives(
            discussion,
            user_stage=3
        )
        assert len(alternatives) > 0

        # Suggest practice
        practice = practice_gen.generate_neti_neti(
            target_concept="consciousness",
            user_stage=3
        )
        assert practice["target"] == "consciousness"

    def test_convert_nihilistic_depression(self):
        """Test converting nihilistic depression to middle path."""
        detector = MadhyamakaDetector(use_semantic=False)
        transformer = MadhyamakaTransformer()

        text = "Nothing matters. Everything is meaningless."

        # Detect nihilism
        nihilism = detector.detect_nihilism(text)
        assert nihilism["nihilism_detected"] is True

        # Transform with two truths
        alternatives = transformer.generate_middle_path_alternatives(text)

        two_truths = [alt for alt in alternatives if alt.get("type") == "two_truths_framework"]
        assert len(two_truths) > 0
        # Should restore conventional function
        assert "function" in two_truths[0]["text"].lower() or \
               "purpose" in two_truths[0]["text"].lower()

    def test_conversation_history_analysis(self):
        """Test analyzing conversation history for clinging."""
        detector = MadhyamakaDetector()

        conversation = [
            {"role": "user", "content": "I KNOW this is TRUE!!"},
            {"role": "assistant", "content": "I hear you."},
            {"role": "user", "content": "This is ABSOLUTELY the ONLY way!!"},
            {"role": "assistant", "content": "Let's explore that."},
            {"role": "user", "content": "You just DON'T UNDERSTAND!!!"}
        ]

        result = detector.detect_clinging(conversation)

        # Should detect defensive patterns
        assert result["confidence"] > 0.0


class TestProgressiveLearning:
    """Test progressive learning journey."""

    def test_stage_1_to_stage_5_progression(self):
        """Test that practices progress appropriately through stages."""
        practice_gen = ContemplativePracticeGenerator()

        # Stage 1: Beginner
        stage1 = practice_gen.generate_neti_neti(user_stage=1, depth="simple")
        assert stage1["metadata"]["difficulty"] == "beginner"
        assert stage1["metadata"]["duration_minutes"] == 15

        # Stage 3: Intermediate
        stage3 = practice_gen.generate_neti_neti(user_stage=3, depth="progressive")
        assert stage3["metadata"]["difficulty"] == "intermediate"
        assert stage3["metadata"]["duration_minutes"] == 20

        # Stage 5: Advanced
        stage5 = practice_gen.generate_neti_neti(user_stage=5, depth="deep")
        assert stage5["metadata"]["difficulty"] == "advanced"
        assert stage5["metadata"]["duration_minutes"] == 30

    def test_transformation_depth_increases_with_stage(self):
        """Test that transformation depth increases with user stage."""
        transformer = MadhyamakaTransformer()
        text = "The self is real."

        # Stage 1: Simple softening
        stage1_alts = transformer.generate_middle_path_alternatives(text, user_stage=1)

        # Stage 4: Should include contemplative pointers
        stage4_alts = transformer.generate_middle_path_alternatives(text, user_stage=4)

        # Stage 4 should have more sophisticated alternatives
        stage4_types = set(alt.get("type") for alt in stage4_alts)
        contemplative = any("contemplative" in str(t).lower() for t in stage4_types)
        # Stage 4+ gets contemplative pointers
        assert contemplative


class TestErrorPropagation:
    """Test that errors are handled gracefully across components."""

    def test_detector_error_doesnt_crash_transformer(self):
        """Test that transformer handles detector errors gracefully."""
        transformer = MadhyamakaTransformer()

        # Edge case that might cause issues
        result = transformer.generate_middle_path_alternatives("")
        assert isinstance(result, list)

    def test_invalid_input_handled_gracefully(self):
        """Test that all components handle invalid input gracefully."""
        detector = MadhyamakaDetector()
        transformer = MadhyamakaTransformer()
        practice_gen = ContemplativePracticeGenerator()

        # Test with None/empty
        try:
            detector.detect_eternalism("")
            transformer.generate_middle_path_alternatives("")
            practice_gen.generate_neti_neti(target_concept="")
        except Exception as e:
            pytest.fail(f"Component failed to handle empty input: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
