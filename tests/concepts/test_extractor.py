"""Tests for ConceptExtractor."""

from agent.concepts.extractor import ConceptExtractor


class TestConceptExtractor:
    def test_extract_from_headings(self) -> None:
        ce = ConceptExtractor()
        content = (
            "## Machine Learning\n\nSome text about ML.\n\n### Deep Learning\n\nMore about DL."
        )
        concepts = ce.extract(content)
        names = [c.name for c in concepts]
        assert "Machine Learning" in names
        assert "Deep Learning" in names

    def test_extract_chinese_bigrams(self) -> None:
        ce = ConceptExtractor()
        content = "深度学习是人工智能的一个重要分支，深度学习在图像处理中有广泛应用"
        concepts = ce.extract(content)
        assert len(concepts) >= 1

    def test_extract_english_terms(self) -> None:
        ce = ConceptExtractor()
        content = "We use PyTorch and TensorFlow for MachineLearning tasks."
        concepts = ce.extract(content)
        names = [c.name for c in concepts]
        assert any("PyTorch" in n for n in names) or any("TensorFlow" in n for n in names)

    def test_max_6_concepts(self) -> None:
        ce = ConceptExtractor()
        content = "\n".join(f"## Topic {i}\n\nContent about topic {i}." for i in range(20))
        concepts = ce.extract(content)
        assert len(concepts) <= 6

    def test_deduplicate_similar(self) -> None:
        ce = ConceptExtractor()
        content = "Machine Learning is great. Machine Learning is powerful."
        concepts = ce.extract(content)
        names = [c.name for c in concepts]
        assert names.count("Machine Learning") <= 1

    def test_match_existing_boost(self) -> None:
        ce = ConceptExtractor()
        content = "## Machine Learning\n\nDeep learning is part of ML."
        concepts = ce.extract(content, existing_concepts=["machine-learning"])
        ml = next((c for c in concepts if c.name == "Machine Learning"), None)
        if ml:
            assert ml.confidence >= 0.35

    def test_structural_labels_filtered(self) -> None:
        ce = ConceptExtractor()
        content = "## Introduction\n\n## Methods\n\n## Real Topic\n\nContent."
        concepts = ce.extract(content)
        names = [c.name for c in concepts]
        assert "Introduction" not in names
        assert "Methods" not in names
