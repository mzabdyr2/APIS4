from src.rag_system import RAGSystem


def test_add_texts_and_chunk_documents():
    rag = RAGSystem(chunk_size=120, chunk_overlap=20)
    rag.add_texts(
        [
            (
                "The 15-minute city is an urban planning concept. "
                "It focuses on access to daily services by walking or cycling. "
                "GIS accessibility analysis can use street networks and isochrones."
            )
        ],
        source="sample.txt",
    )

    chunks = rag.chunk_documents()

    assert chunks
    assert chunks[0].source == "sample.txt"
    assert "15-minute city" in chunks[0].text


def test_keyword_coverage():
    rag = RAGSystem()
    result = rag.evaluate_keyword_coverage(
        answer="Accessibility can be measured with isochrones and network analysis.",
        expected_keywords=["accessibility", "isochrones", "walkability"],
    )

    assert result["coverage"] == 2 / 3
    assert result["matched_keywords"] == ["accessibility", "isochrones"]
