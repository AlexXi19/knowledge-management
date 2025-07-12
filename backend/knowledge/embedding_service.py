import os
import asyncio
from typing import List, Union, Optional
from abc import ABC, abstractmethod
import openai
from openai import AsyncOpenAI
from sentence_transformers import SentenceTransformer
import numpy as np

class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of the embeddings"""
        pass

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using their API"""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Model dimensions mapping
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI API"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating OpenAI embedding: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI API"""
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating OpenAI embeddings: {e}")
            raise
    
    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings"""
        return self._dimensions.get(self.model, 1536)

class SentenceTransformerProvider(EmbeddingProvider):
    """Local sentence transformer embedding provider"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text using sentence transformers"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, 
            lambda: self.model.encode(text, convert_to_tensor=False)
        )
        return embedding.tolist()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using sentence transformers"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self.model.encode(texts, convert_to_tensor=False)
        )
        return embeddings.tolist()
    
    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings"""
        return self.model.get_sentence_embedding_dimension()

class EmbeddingService:
    """Service that manages different embedding providers"""
    
    def __init__(self, provider_type: str = "sentence_transformer", **kwargs):
        self.provider_type = provider_type
        self.provider = self._create_provider(provider_type, **kwargs)
    
    def _create_provider(self, provider_type: str, **kwargs) -> EmbeddingProvider:
        """Create the appropriate embedding provider"""
        if provider_type == "openai":
            model = kwargs.get("model", "text-embedding-3-small")
            api_key = kwargs.get("api_key")
            return OpenAIEmbeddingProvider(model=model, api_key=api_key)
        
        elif provider_type == "sentence_transformer":
            model_name = kwargs.get("model_name", "all-MiniLM-L6-v2")
            return SentenceTransformerProvider(model_name=model_name)
        
        else:
            raise ValueError(f"Unknown embedding provider: {provider_type}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        return await self.provider.embed_text(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return await self.provider.embed_texts(texts)
    
    @property
    def dimension(self) -> int:
        """Return the dimension of the embeddings"""
        return self.provider.dimension
    
    def get_provider_info(self) -> dict:
        """Get information about the current provider"""
        if isinstance(self.provider, OpenAIEmbeddingProvider):
            return {
                "type": "openai",
                "model": self.provider.model,
                "dimension": self.provider.dimension
            }
        elif isinstance(self.provider, SentenceTransformerProvider):
            return {
                "type": "sentence_transformer", 
                "model": self.provider.model_name,
                "dimension": self.provider.dimension
            }
        else:
            return {"type": "unknown"}

def create_embedding_service() -> EmbeddingService:
    """Factory function to create embedding service based on environment variables"""
    provider_type = os.getenv("EMBEDDING_PROVIDER", "sentence_transformer").lower()
    
    if provider_type == "openai":
        model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("Warning: OPENAI_API_KEY not found, falling back to sentence transformers")
            provider_type = "sentence_transformer"
        else:
            return EmbeddingService(
                provider_type="openai",
                model=model,
                api_key=api_key
            )
    
    if provider_type == "sentence_transformer":
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        return EmbeddingService(
            provider_type="sentence_transformer",
            model_name=model_name
        )
    
    raise ValueError(f"Unknown embedding provider: {provider_type}")

# Test function
async def test_embedding_service():
    """Test function to verify embedding service works"""
    service = create_embedding_service()
    
    print(f"Provider info: {service.get_provider_info()}")
    
    # Test single embedding
    text = "This is a test sentence for embedding."
    embedding = await service.embed_text(text)
    print(f"Single embedding dimension: {len(embedding)}")
    
    # Test multiple embeddings
    texts = ["First sentence", "Second sentence", "Third sentence"]
    embeddings = await service.embed_texts(texts)
    print(f"Multiple embeddings count: {len(embeddings)}")
    print(f"Each embedding dimension: {len(embeddings[0])}")

if __name__ == "__main__":
    asyncio.run(test_embedding_service()) 