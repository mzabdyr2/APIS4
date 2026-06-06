"""RAG project package for APIS task 4."""

from .ollama_generator import ollama_generate
from .rag_system import RAGSystem

__all__ = ["RAGSystem", "ollama_generate"]
