import json
from src.config import Settings
from src.db import initialize
from src.retrieval.retriever import index_documents


if __name__ == '__main__':
    settings = Settings()
    print(json.dumps(index_documents(settings, initialize(settings))))
