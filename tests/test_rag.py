import sys
from types import SimpleNamespace
import numpy as np
from backend.app.services.rag import KnowledgeBase


def test_knowledge_loading_threshold_and_cached_index(monkeypatch):
    class Encoder:
        def __init__(self, model):
            self.model = model
        def encode(self, texts, **kwargs):
            if len(texts) > 1:
                return np.eye(len(texts), dtype='float32')
            return np.array([[0, 0, 0] if texts[0] == 'unrelated' else [1, 0, 0]], dtype='float32')
    class Index:
        def __init__(self, dimensions):
            self.dimensions = dimensions
        def add(self, vectors):
            self.vectors = vectors
        def search(self, vector, count):
            scores = vector @ self.vectors.T
            indices = np.argsort(-scores, axis=1)[:, :count]
            return np.take_along_axis(scores, indices, axis=1), indices
    monkeypatch.setitem(sys.modules, 'sentence_transformers', SimpleNamespace(SentenceTransformer=Encoder))
    monkeypatch.setitem(sys.modules, 'faiss', SimpleNamespace(IndexFlatIP=Index))
    knowledge = KnowledgeBase()
    assert knowledge.model is None
    sources = knowledge.retrieve('articles')
    assert len(sources) == 1 and sources[0]['id'] == 'en-articles'
    assert sources[0]['url'].startswith('https://learnenglish.britishcouncil.org/')
    encoder = knowledge.model
    assert knowledge.retrieve('unrelated') == []
    assert knowledge.model is encoder
