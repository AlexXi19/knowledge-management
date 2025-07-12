import networkx as nx
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
import uuid
import asyncio

from models.chat_models import SearchResult
from .embedding_service import create_embedding_service, EmbeddingService

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.chroma_client = None
        self.collection = None
        self.embedding_service = None
        self.knowledge_base_path = os.getenv("KNOWLEDGE_BASE_PATH", "./knowledge_base")
        self.initialized = False
        
    async def initialize(self):
        """Initialize the knowledge graph and vector database"""
        if self.initialized:
            return
            
        # Create knowledge base directory
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        
        # Initialize embedding service
        self.embedding_service = create_embedding_service()
        provider_info = self.embedding_service.get_provider_info()
        print(f"🧠 Initialized embedding service: {provider_info['type']} - {provider_info['model']}")
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=self.knowledge_base_path)
        
        # Create or get collection with custom embedding function
        collection_name = f"knowledge_base_{provider_info['type']}_{provider_info['model'].replace('/', '_').replace('-', '_')}"
        
        try:
            self.collection = self.chroma_client.get_collection(collection_name)
        except:
            # Create custom embedding function
            if provider_info['type'] == 'openai':
                # For OpenAI, we'll handle embeddings manually
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"embedding_provider": "openai", "model": provider_info['model']}
                )
            else:
                # For sentence transformers, use the built-in function
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=provider_info['model']
                    ),
                    metadata={"embedding_provider": "sentence_transformer", "model": provider_info['model']}
                )
        
        # Load existing graph
        await self._load_graph()
        
        self.initialized = True
        
    async def _load_graph(self):
        """Load existing graph from disk"""
        graph_path = os.path.join(self.knowledge_base_path, "graph.json")
        if os.path.exists(graph_path):
            try:
                with open(graph_path, 'r') as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except Exception as e:
                print(f"Error loading graph: {e}")
                self.graph = nx.MultiDiGraph()
                
    async def _save_graph(self):
        """Save graph to disk"""
        graph_path = os.path.join(self.knowledge_base_path, "graph.json")
        try:
            data = nx.node_link_data(self.graph)
            with open(graph_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving graph: {e}")
            
    async def add_node(self, content: str, category: str, metadata: Dict[str, Any] = None) -> str:
        """Add a new node to the knowledge graph"""
        node_id = str(uuid.uuid4())
        
        # Prepare metadata
        node_metadata = {
            "category": category,
            "created_at": datetime.now().isoformat(),
            "content": content,
            **(metadata or {})
        }
        
        # Add to NetworkX graph
        self.graph.add_node(node_id, **node_metadata)
        
        # Add to ChromaDB for semantic search
        try:
            # ChromaDB doesn't support list metadata, so convert lists to strings
            chroma_metadata = {}
            for key, value in node_metadata.items():
                if isinstance(value, list):
                    chroma_metadata[key] = ', '.join(str(item) for item in value)
                else:
                    chroma_metadata[key] = str(value) if value is not None else ""
            
            # Check if we need to generate embeddings manually (for OpenAI)
            provider_info = self.embedding_service.get_provider_info()
            if provider_info['type'] == 'openai':
                # Generate embedding using our service
                embedding = await self.embedding_service.embed_text(content)
                self.collection.add(
                    documents=[content],
                    metadatas=[chroma_metadata],
                    ids=[node_id],
                    embeddings=[embedding]
                )
            else:
                # Let ChromaDB handle embedding generation
                self.collection.add(
                    documents=[content],
                    metadatas=[chroma_metadata],
                    ids=[node_id]
                )
        except Exception as e:
            print(f"Error adding to ChromaDB: {e}")
        
        # Save graph
        await self._save_graph()
        
        return node_id
    
    async def add_edge(self, source_id: str, target_id: str, relationship: str, metadata: Dict[str, Any] = None):
        """Add a relationship between two nodes"""
        edge_metadata = {
            "relationship": relationship,
            "created_at": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        self.graph.add_edge(source_id, target_id, **edge_metadata)
        await self._save_graph()
        
    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search the knowledge base using semantic similarity"""
        if not self.collection:
            return []
            
        try:
            # Check if we need to generate query embedding manually (for OpenAI)
            provider_info = self.embedding_service.get_provider_info()
            if provider_info['type'] == 'openai':
                # Generate query embedding using our service
                query_embedding = await self.embedding_service.embed_text(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit
                )
            else:
                # Let ChromaDB handle query embedding generation
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
            
            search_results = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance  # Convert distance to similarity
                    
                    search_results.append(SearchResult(
                        content=doc,
                        category=metadata.get('category', 'Unknown'),
                        similarity=similarity,
                        node_id=results['ids'][0][i],
                        metadata=metadata
                    ))
            
            return search_results
            
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    async def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific node by ID"""
        if not self.graph.has_node(node_id):
            return None
            
        return dict(self.graph.nodes[node_id])
    
    async def get_neighbors(self, node_id: str) -> List[Dict[str, Any]]:
        """Get neighboring nodes and their relationships"""
        if not self.graph.has_node(node_id):
            return []
            
        neighbors = []
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.get_edge_data(node_id, neighbor)
            neighbors.append({
                "node_id": neighbor,
                "node_data": dict(self.graph.nodes[neighbor]),
                "relationships": edge_data
            })
            
        return neighbors
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories in the knowledge base"""
        categories = set()
        for node_id, node_data in self.graph.nodes(data=True):
            if 'category' in node_data:
                categories.add(node_data['category'])
        return sorted(list(categories))
    
    async def get_nodes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all nodes in a specific category"""
        nodes = []
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('category') == category:
                nodes.append({
                    "node_id": node_id,
                    "data": node_data
                })
        return nodes
    
    async def get_graph_data(self) -> Dict[str, Any]:
        """Get the complete graph data for visualization"""
        nodes = []
        edges = []
        
        # Get all nodes
        for node_id, node_data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": node_data.get('content', '')[:50] + "..." if len(node_data.get('content', '')) > 50 else node_data.get('content', ''),
                "category": node_data.get('category', 'Unknown'),
                "metadata": node_data
            })
        
        # Get all edges
        for source, target, edge_data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "relationship": edge_data.get('relationship', 'related'),
                "metadata": edge_data
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "categories": await self.get_categories()
            }
        }
    
    async def find_related_concepts(self, node_id: str, max_depth: int = 2) -> List[str]:
        """Find related concepts using graph traversal"""
        if not self.graph.has_node(node_id):
            return []
            
        related = set()
        
        # BFS to find related nodes
        queue = [(node_id, 0)]
        visited = {node_id}
        
        while queue:
            current_node, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
                
            for neighbor in self.graph.neighbors(current_node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    related.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        return list(related)
    
    async def get_node_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        total_nodes = self.graph.number_of_nodes()
        total_edges = self.graph.number_of_edges()
        categories = await self.get_categories()
        
        category_counts = {}
        for category in categories:
            nodes = await self.get_nodes_by_category(category)
            category_counts[category] = len(nodes)
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "total_categories": len(categories),
            "category_distribution": category_counts,
            "average_connections": total_edges / total_nodes if total_nodes > 0 else 0
        } 