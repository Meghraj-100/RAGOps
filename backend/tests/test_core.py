"""Backend tests — unit tests that don't require external services or ML models."""

import sys
import pytest
from unittest.mock import MagicMock

# Mock heavy ML dependencies before importing app modules
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['openai'] = MagicMock()


class TestChunking:
    """Tests for the text chunking function."""

    def test_chunk_text_basic(self):
        from app.services.ingestion import chunk_text
        text = "word " * 200  # ~1000 chars
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 100

    def test_chunk_text_empty(self):
        from app.services.ingestion import chunk_text
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_chunk_text_short(self):
        from app.services.ingestion import chunk_text
        chunks = chunk_text("Hello world", chunk_size=100, overlap=10)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_chunk_text_overlap(self):
        from app.services.ingestion import chunk_text
        text = "A" * 100 + " " + "B" * 100
        chunks = chunk_text(text, chunk_size=110, overlap=20)
        assert len(chunks) >= 2

    def test_chunk_text_deterministic(self):
        from app.services.ingestion import chunk_text
        text = "The quick brown fox jumps over the lazy dog. " * 50
        c1 = chunk_text(text, chunk_size=100, overlap=10)
        c2 = chunk_text(text, chunk_size=100, overlap=10)
        assert c1 == c2


class TestFileExtension:
    def test_pdf(self):
        from app.services.ingestion import get_file_extension
        assert get_file_extension("document.pdf") == "pdf"

    def test_txt(self):
        from app.services.ingestion import get_file_extension
        assert get_file_extension("notes.txt") == "txt"

    def test_docx(self):
        from app.services.ingestion import get_file_extension
        assert get_file_extension("report.docx") == "docx"

    def test_uppercase(self):
        from app.services.ingestion import get_file_extension
        assert get_file_extension("File.PDF") == "pdf"


class TestExtractText:
    def test_extract_txt(self):
        from app.services.ingestion import extract_text
        content = b"Hello, this is a test document."
        text = extract_text(content, "txt")
        assert "Hello" in text
        assert "test document" in text

    def test_extract_unsupported(self):
        from app.services.ingestion import extract_text
        with pytest.raises(ValueError, match="Unsupported"):
            extract_text(b"data", "xyz")


class TestEvaluationMetrics:
    """Tests for evaluation metric calculations."""

    def test_hit_at_k(self):
        from app.evaluation.engine import calculate_hit_at_k
        assert calculate_hit_at_k(["a", "b", "c"], ["a"], 1) == 1.0
        assert calculate_hit_at_k(["a", "b", "c"], ["c"], 1) == 0.0
        assert calculate_hit_at_k(["a", "b", "c"], ["c"], 3) == 1.0
        assert calculate_hit_at_k(["a", "b", "c"], ["d"], 5) == 0.0

    def test_mrr(self):
        from app.evaluation.engine import calculate_mrr
        assert calculate_mrr(["a", "b", "c"], ["a"]) == 1.0
        assert calculate_mrr(["a", "b", "c"], ["b"]) == 0.5
        assert calculate_mrr(["a", "b", "c"], ["c"]) == pytest.approx(1/3)
        assert calculate_mrr(["a", "b", "c"], ["d"]) == 0.0

    def test_percentile(self):
        from app.evaluation.engine import percentile
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        assert percentile(values, 50) == pytest.approx(55.0)
        assert percentile(values, 95) == pytest.approx(95.5)
        assert percentile([], 50) == 0.0


class TestRetrieverFactory:
    def test_get_retriever_valid(self):
        from app.rag.retriever import get_retriever, VectorRetriever, HybridRetriever
        assert isinstance(get_retriever("vector-similarity"), VectorRetriever)
        assert isinstance(get_retriever("hybrid-search"), HybridRetriever)

    def test_get_retriever_invalid(self):
        from app.rag.retriever import get_retriever
        with pytest.raises(ValueError, match="Unknown"):
            get_retriever("invalid-strategy")


class TestPrompts:
    def test_system_prompt_exists(self):
        from app.rag.prompts import SYSTEM_PROMPT
        assert "context" in SYSTEM_PROMPT.lower()

    def test_user_prompt_template(self):
        from app.rag.prompts import USER_PROMPT_TEMPLATE
        formatted = USER_PROMPT_TEMPLATE.format(context="test context", question="test question")
        assert "test context" in formatted
        assert "test question" in formatted
