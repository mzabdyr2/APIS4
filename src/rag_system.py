from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence


@dataclass
class SourceDocument:
    """Text extracted from one source page or text block."""

    text: str
    source: str
    page: int | None = None


@dataclass
class DocumentChunk:
    """A chunk is the smallest text unit embedded and stored in the vector index."""

    id: str
    text: str
    source: str
    page: int | None = None


@dataclass
class RetrievedChunk:
    """Chunk returned by semantic search."""

    chunk: DocumentChunk
    score: float


@dataclass
class RagAnswer:
    """Complete answer object with retrieval evidence."""

    question: str
    answer: str
    prompt: str
    retrieved_chunks: list[RetrievedChunk]


class RAGSystem:
    """Educational RAG system for publications about 15-minute cities.

    The class intentionally keeps each RAG stage visible. This makes it useful for
    a notebook and a report: every method corresponds to one architecture block.
    """

    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 900,
        chunk_overlap: int = 150,
        top_k: int = 4,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        self.embedding_model_name = embedding_model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k

        self.documents: list[SourceDocument] = []
        self.chunks: list[DocumentChunk] = []
        self.index = None
        self._embedding_model = None

    # ---------------------------------------------------------------------
    # 1. Document loading
    # ---------------------------------------------------------------------
    def load_pdfs(self, pdf_directory: str | Path) -> list[SourceDocument]:
        """Load every PDF from a directory and extract text page by page."""

        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ImportError(
                "Install pypdf before loading PDFs: pip install pypdf"
            ) from exc

        pdf_directory = Path(pdf_directory)
        if not pdf_directory.exists():
            raise FileNotFoundError(f"PDF directory does not exist: {pdf_directory}")

        documents: list[SourceDocument] = []
        for pdf_path in sorted(pdf_directory.glob("*.pdf")):
            reader = PdfReader(str(pdf_path))
            for page_number, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                text = self._clean_text(text)
                if text:
                    documents.append(
                        SourceDocument(
                            text=text,
                            source=pdf_path.name,
                            page=page_number,
                        )
                    )

        self.documents = documents
        return documents

    def add_texts(
        self,
        texts: Iterable[str],
        source: str = "manual_input",
        start_page: int | None = None,
    ) -> list[SourceDocument]:
        """Add plain text manually.

        This is handy for smoke tests and for learning the pipeline before real
        scientific PDFs are added to data/papers.
        """

        added: list[SourceDocument] = []
        for offset, text in enumerate(texts):
            clean_text = self._clean_text(text)
            if not clean_text:
                continue
            page = None if start_page is None else start_page + offset
            added.append(SourceDocument(text=clean_text, source=source, page=page))

        self.documents.extend(added)
        return added

    # ---------------------------------------------------------------------
    # 2. Chunking
    # ---------------------------------------------------------------------
    def chunk_documents(
        self, documents: Sequence[SourceDocument] | None = None
    ) -> list[DocumentChunk]:
        """Split documents into overlapping chunks."""

        documents = list(documents or self.documents)
        chunks: list[DocumentChunk] = []

        for doc_index, document in enumerate(documents):
            text_chunks = self._split_text(document.text)
            for chunk_index, chunk_text in enumerate(text_chunks):
                chunks.append(
                    DocumentChunk(
                        id=f"doc{doc_index:04d}_chunk{chunk_index:04d}",
                        text=chunk_text,
                        source=document.source,
                        page=document.page,
                    )
                )

        self.chunks = chunks
        return chunks

    def _split_text(self, text: str) -> list[str]:
        """Paragraph-aware character splitter with overlap."""

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                    current = ""
                chunks.extend(self._split_long_paragraph(paragraph))
                continue

            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                current = paragraph

        if current:
            chunks.append(current.strip())

        return self._apply_overlap(chunks)

    def _split_long_paragraph(self, paragraph: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence[: self.chunk_size].strip()
                remainder = sentence[self.chunk_size :].strip()
                while remainder:
                    chunks.append(current)
                    current = remainder[: self.chunk_size].strip()
                    remainder = remainder[self.chunk_size :].strip()

        if current:
            chunks.append(current.strip())
        return chunks

    def _apply_overlap(self, chunks: list[str]) -> list[str]:
        if not chunks or self.chunk_overlap == 0:
            return chunks

        overlapped = [chunks[0]]
        for previous, current in zip(chunks, chunks[1:]):
            prefix = previous[-self.chunk_overlap :].strip()
            if prefix:
                overlapped.append(f"{prefix}\n\n{current}".strip())
            else:
                overlapped.append(current)
        return overlapped

    # ---------------------------------------------------------------------
    # 3. Embeddings and vector store
    # ---------------------------------------------------------------------
    def build_vector_store(
        self, chunks: Sequence[DocumentChunk] | None = None
    ) -> object:
        """Embed chunks and build a FAISS index using cosine-like similarity."""

        chunks = list(chunks or self.chunks)
        if not chunks:
            raise ValueError("No chunks available. Run chunk_documents() first.")

        try:
            import faiss
            import numpy as np
        except ImportError as exc:
            raise ImportError(
                "Install vector dependencies first: pip install faiss-cpu numpy"
            ) from exc

        model = self._get_embedding_model()
        embeddings = model.encode(
            [chunk.text for chunk in chunks],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).astype("float32")

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(np.asarray(embeddings))

        self.chunks = chunks
        self.index = index
        return index

    def save_vector_store(self, directory: str | Path) -> None:
        """Persist FAISS index and chunk metadata."""

        if self.index is None:
            raise ValueError("No FAISS index available. Run build_vector_store().")

        try:
            import faiss
        except ImportError as exc:
            raise ImportError("Install faiss-cpu before saving the index.") from exc

        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(directory / "index.faiss"))
        metadata = {
            "embedding_model_name": self.embedding_model_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }
        (directory / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load_vector_store(self, directory: str | Path) -> None:
        """Load a previously saved FAISS index and chunk metadata."""

        try:
            import faiss
        except ImportError as exc:
            raise ImportError("Install faiss-cpu before loading the index.") from exc

        directory = Path(directory)
        metadata_path = directory / "metadata.json"
        index_path = directory / "index.faiss"
        if not metadata_path.exists() or not index_path.exists():
            raise FileNotFoundError(
                "Vector store must contain metadata.json and index.faiss"
            )

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        self.embedding_model_name = metadata["embedding_model_name"]
        self.chunk_size = metadata["chunk_size"]
        self.chunk_overlap = metadata["chunk_overlap"]
        self.top_k = metadata["top_k"]
        self.chunks = [DocumentChunk(**chunk) for chunk in metadata["chunks"]]
        self.index = faiss.read_index(str(index_path))

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        """Return the most semantically similar chunks for a question."""

        if self.index is None:
            raise ValueError("No vector store available. Build or load one first.")
        if not self.chunks:
            raise ValueError("Chunk metadata is empty.")

        try:
            import numpy as np
        except ImportError as exc:
            raise ImportError("Install numpy before retrieval.") from exc

        top_k = top_k or self.top_k
        model = self._get_embedding_model()
        query_embedding = model.encode(
            [question],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(np.asarray(query_embedding), top_k)
        results: list[RetrievedChunk] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            results.append(
                RetrievedChunk(chunk=self.chunks[int(index)], score=float(score))
            )
        return results

    # ---------------------------------------------------------------------
    # 4. Prompting and answer generation
    # ---------------------------------------------------------------------
    def build_prompt(self, question: str, retrieved_chunks: Sequence[RetrievedChunk]) -> str:
        """Build a grounded prompt for an LLM."""

        context_blocks = []
        for number, result in enumerate(retrieved_chunks, start=1):
            page = f", page {result.chunk.page}" if result.chunk.page else ""
            context_blocks.append(
                f"[{number}] Source: {result.chunk.source}{page}\n"
                f"Similarity score: {result.score:.3f}\n"
                f"{result.chunk.text}"
            )

        context = "\n\n---\n\n".join(context_blocks)
        return (
            "You are an expert in geoinformatics, urban accessibility, and the "
            "15-minute city concept.\n"
            "Answer the user's question using only the provided context. "
            "If the context is insufficient, say that the documents do not provide "
            "enough evidence. Cite sources with bracket numbers such as [1].\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{question}\n\n"
            "Answer:"
        )

    def answer(
        self,
        question: str,
        top_k: int | None = None,
        generator: Callable[[str], str] | None = None,
    ) -> RagAnswer:
        """Retrieve context and generate an answer.

        Pass a generator callable to use an LLM, for example OpenAI, Ollama, or a
        Hugging Face pipeline. Without a generator, the method returns an
        extractive baseline answer built from the retrieved chunks.
        """

        retrieved = self.retrieve(question, top_k=top_k)
        prompt = self.build_prompt(question, retrieved)

        if generator is None:
            answer_text = self._extractive_answer(question, retrieved)
        else:
            answer_text = generator(prompt)

        return RagAnswer(
            question=question,
            answer=answer_text,
            prompt=prompt,
            retrieved_chunks=retrieved,
        )

    def _extractive_answer(
        self, question: str, retrieved_chunks: Sequence[RetrievedChunk]
    ) -> str:
        """Simple fallback when no LLM API or local model is configured."""

        if not retrieved_chunks:
            return "Nie znaleziono fragmentów dokumentów powiązanych z pytaniem."

        question_terms = {
            token
            for token in re.findall(r"[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{4,}", question.lower())
        }
        ranked_sentences: list[tuple[float, str, int]] = []
        for chunk_number, retrieved in enumerate(retrieved_chunks, start=1):
            sentences = re.split(r"(?<=[.!?])\s+", retrieved.chunk.text)
            for sentence in sentences:
                sentence_terms = set(
                    re.findall(
                        r"[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{4,}",
                        sentence.lower(),
                    )
                )
                overlap = len(question_terms & sentence_terms)
                length_penalty = 1 / math.sqrt(max(len(sentence_terms), 1))
                score = overlap + retrieved.score + length_penalty
                if len(sentence.strip()) > 40:
                    ranked_sentences.append((score, sentence.strip(), chunk_number))

        ranked_sentences.sort(reverse=True, key=lambda item: item[0])
        selected = ranked_sentences[:3]
        if not selected:
            selected = [
                (retrieved.score, retrieved.chunk.text[:500].strip(), number)
                for number, retrieved in enumerate(retrieved_chunks[:2], start=1)
            ]

        bullet_points = "\n".join(
            f"- {sentence} [{source_number}]" for _, sentence, source_number in selected
        )
        return (
            "Poniżej znajduje się odpowiedź ekstrakcyjna oparta na najbardziej "
            "podobnych fragmentach. W finalnej wersji projektu można w tym miejscu "
            "podłączyć model generatywny LLM.\n\n"
            f"{bullet_points}"
        )

    # ---------------------------------------------------------------------
    # 5. Evaluation helpers
    # ---------------------------------------------------------------------
    def evaluate_keyword_coverage(
        self,
        answer: str,
        expected_keywords: Sequence[str],
    ) -> dict[str, object]:
        """Measure how many expected concepts appear in the answer."""

        answer_lower = answer.lower()
        matched = [
            keyword for keyword in expected_keywords if keyword.lower() in answer_lower
        ]
        coverage = len(matched) / len(expected_keywords) if expected_keywords else 0.0
        return {
            "coverage": coverage,
            "matched_keywords": matched,
            "missing_keywords": [
                keyword for keyword in expected_keywords if keyword not in matched
            ],
        }

    def evaluate_context_relevance(
        self,
        retrieved_chunks: Sequence[RetrievedChunk],
        expected_keywords: Sequence[str],
    ) -> dict[str, object]:
        """Estimate whether retrieved chunks contain expected concepts."""

        context = " ".join(item.chunk.text for item in retrieved_chunks).lower()
        matched = [
            keyword for keyword in expected_keywords if keyword.lower() in context
        ]
        relevance = len(matched) / len(expected_keywords) if expected_keywords else 0.0
        return {
            "context_relevance": relevance,
            "matched_keywords": matched,
            "missing_keywords": [
                keyword for keyword in expected_keywords if keyword not in matched
            ],
        }

    def evaluate_rouge_l(self, answer: str, reference_answer: str) -> dict[str, float]:
        """Compute ROUGE-L if rouge-score is installed."""

        try:
            from rouge_score import rouge_scorer
        except ImportError as exc:
            raise ImportError(
                "Install rouge-score before using ROUGE: pip install rouge-score"
            ) from exc

        scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
        score = scorer.score(reference_answer, answer)["rougeL"]
        return {
            "precision": score.precision,
            "recall": score.recall,
            "fmeasure": score.fmeasure,
        }

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _get_embedding_model(self):
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "Install sentence-transformers before embedding text: "
                    "pip install sentence-transformers"
                ) from exc
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
        return self._embedding_model

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\x00", " ")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
