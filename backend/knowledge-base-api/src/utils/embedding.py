from typing import List, Dict, Any
import requests

class EmbeddingService:
    def __init__(self, embedding_url: str):
        self.embedding_url = embedding_url

    def get_embedding(self, text: str) -> List[float]:
        response = requests.post(self.embedding_url, json={"text": text})
        response.raise_for_status()
        return response.json().get("embedding", [])

def create_embedding(texts: List[str], embedding_service: EmbeddingService) -> List[Dict[str, Any]]:
    embeddings = []
    for text in texts:
        embedding = embedding_service.get_embedding(text)
        embeddings.append({
            "text": text,
            "embedding": embedding
        })
    return embeddings