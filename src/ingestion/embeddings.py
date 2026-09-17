"""Optional local semantic embeddings; no transaction data goes to this encoder."""
MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
DIMENSIONS = 384


class SemanticEncoder:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(MODEL)

    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()
