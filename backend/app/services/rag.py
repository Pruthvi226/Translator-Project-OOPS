import json
from pathlib import Path
import threading


class KnowledgeBase:
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None

    def retrieve(self, question):
        import faiss
        from sentence_transformers import SentenceTransformer
        with self.lock:
            if self.model is None:
                self.docs = json.loads((Path(__file__).parents[2] / 'knowledge' / 'grammar.json').read_text(encoding='utf-8'))
                self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
                vectors = self.model.encode([d['text'] for d in self.docs], normalize_embeddings=True).astype('float32')
                self.index = faiss.IndexFlatIP(vectors.shape[1])
                self.index.add(vectors)
            vector = self.model.encode([question], normalize_embeddings=True).astype('float32')
            scores, indices = self.index.search(vector, min(3, len(self.docs)))
        return [dict(self.docs[i], score=float(s)) for s, i in zip(scores[0], indices[0]) if i >= 0 and s >= 0.45]
