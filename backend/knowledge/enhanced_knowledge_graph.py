"""
Enhanced Knowledge Graph System following PKM best practices
Implements the hybrid approach: declarative links + compiled index
"""

import networkx as nx
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional, Set, Tuple
import json
import os
from datetime import datetime
import uuid
import asyncio
from pathlib import Path
import pickle
from dataclasses import dataclass, asdict
import re

from models.chat_models import SearchResult
from .embedding_service import create_embedding_service, EmbeddingService
from .hash_utils import calculate_content_hash, get_hash_tracker, HashTracker
from .markdown_parser import (
    get_markdown_parser, 
    MarkdownParser, 
    ParsedNote, 
    RelationType, 
    Relationship,
    WikiLink
)

@dataclass
class GraphNode:
    """Enhanced node representation with PKM metadata"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    metadata: Dict[str, Any]
    content_hash: str
    created_at: str
    updated_at: str
    file_path: str = ""
    parent_id: str = ""
    children_ids: List[str] = None
    
    def __post_init__(self):
        if self.children_ids is None:
            self.children_ids = []

@dataclass
class GraphEdge:
    """Enhanced edge representation with typed relationships"""
    source_id: str
    target_id: str
    relation_type: str
    metadata: Dict[str, Any]
    weight: float = 1.0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class UnifiedSearchResult:
    """Unified search result format for all search types"""
    content: str
    title: str
    category: str
    source_type: str  # 'semantic', 'grep', 'title', 'tag'
    relevance_score: float
    node_id: str
    file_path: str = ""
    line_number: int = 0
    context: str = ""
    snippet: str = ""
    metadata: Dict[str, Any] = None
    chunk_index: int = 0
    total_chunks: int = 1
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TextChunk:
    """Text chunk for semantic search"""
    content: str
    start_index: int
    end_index: int
    chunk_index: int
    total_chunks: int
    node_id: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class EnhancedKnowledgeGraph:
    """Enhanced knowledge graph with PKM features"""
    
    def __init__(self, knowledge_base_path: str = None):
        self.knowledge_base_path = knowledge_base_path or os.getenv("KNOWLEDGE_BASE_PATH", "./.knowledge_base")
        self.notes_directory = os.getenv("NOTES_DIRECTORY", "./notes")
        
        # Core components
        self.graph = nx.MultiDiGraph()
        self.chroma_client = None
        self.collection = None
        self.embedding_service = None
        self.hash_tracker = get_hash_tracker()
        self.markdown_parser = get_markdown_parser()
        
        # PKM-specific indexes
        self.nodes_by_id: Dict[str, GraphNode] = {}
        self.edges_by_id: Dict[str, GraphEdge] = {}
        self.title_to_id: Dict[str, str] = {}
        self.category_index: Dict[str, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self.hierarchy_index: Dict[str, Set[str]] = {}  # parent_id -> children_ids
        
        self.initialized = False
        
    async def initialize(self):
        """Initialize the enhanced knowledge graph"""
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
        
        # Create or get collection
        collection_name = f"enhanced_knowledge_base_{provider_info['type']}_{provider_info['model'].replace('/', '_').replace('-', '_')}"
        
        try:
            self.collection = self.chroma_client.get_collection(collection_name)
        except:
            if provider_info['type'] == 'openai':
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"embedding_provider": "openai", "model": provider_info['model']}
                )
            else:
                self.collection = self.chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name=provider_info['model']
                    ),
                    metadata={"embedding_provider": "sentence_transformer", "model": provider_info['model']}
                )
        
        # Load existing graph
        await self._load_graph()
        
        # Scan notes directory for wiki-links and relationships
        await self._scan_notes_directory()
        
        self.initialized = True
        print(f"📊 Enhanced Knowledge Graph initialized with {len(self.nodes_by_id)} nodes and {len(self.edges_by_id)} edges")
        
    async def _load_graph(self):
        """Load existing graph from disk"""
        graph_path = os.path.join(self.knowledge_base_path, "enhanced_graph.json")
        if os.path.exists(graph_path):
            try:
                with open(graph_path, 'r') as f:
                    data = json.load(f)
                    
                # Load nodes
                for node_data in data.get('nodes', []):
                    node = GraphNode(**node_data)
                    self.nodes_by_id[node.id] = node
                    self.title_to_id[node.title] = node.id
                    self._update_indexes(node)
                
                # Load edges
                for edge_data in data.get('edges', []):
                    edge = GraphEdge(**edge_data)
                    self.edges_by_id[f"{edge.source_id}-{edge.target_id}-{edge.relation_type}"] = edge
                
                # Rebuild NetworkX graph
                self._rebuild_networkx_graph()
                
            except Exception as e:
                print(f"Error loading enhanced graph: {e}")
                self.graph = nx.MultiDiGraph()
                
    async def _save_graph(self):
        """Save graph to disk"""
        graph_path = os.path.join(self.knowledge_base_path, "enhanced_graph.json")
        try:
            data = {
                'nodes': [asdict(node) for node in self.nodes_by_id.values()],
                'edges': [asdict(edge) for edge in self.edges_by_id.values()],
                'metadata': {
                    'saved_at': datetime.now().isoformat(),
                    'total_nodes': len(self.nodes_by_id),
                    'total_edges': len(self.edges_by_id)
                }
            }
            
            with open(graph_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving enhanced graph: {e}")
            
    def _rebuild_networkx_graph(self):
        """Rebuild the NetworkX graph from our indexes (without content for efficiency)"""
        self.graph.clear()
        
        # Add nodes (excluding content for memory efficiency)
        for node in self.nodes_by_id.values():
            self.graph.add_node(node.id, **{
                'title': node.title,
                'category': node.category,
                'tags': node.tags,
                'file_path': node.file_path,
                'content_hash': node.content_hash,
                'created_at': node.created_at,
                'updated_at': node.updated_at,
                'metadata': node.metadata
            })
        
        # Add edges
        for edge in self.edges_by_id.values():
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                relation_type=edge.relation_type,
                weight=edge.weight,
                metadata=edge.metadata,
                created_at=edge.created_at
            )
    
    def _update_indexes(self, node: GraphNode):
        """Update various indexes for fast lookups"""
        # Category index
        if node.category not in self.category_index:
            self.category_index[node.category] = set()
        self.category_index[node.category].add(node.id)
        
        # Tag index
        for tag in node.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(node.id)
        
        # Hierarchy index
        if node.parent_id:
            if node.parent_id not in self.hierarchy_index:
                self.hierarchy_index[node.parent_id] = set()
            self.hierarchy_index[node.parent_id].add(node.id)
    
    async def _scan_notes_directory(self):
        """Scan notes directory for wiki-links and relationships"""
        notes_path = Path(self.notes_directory)
        if not notes_path.exists():
            return
        
        print(f"🔍 Scanning notes directory: {notes_path}")
        
        # First pass: parse all notes
        parsed_notes = []
        for md_file in notes_path.rglob("*.md"):
            try:
                parsed_note = self.markdown_parser.parse_file(md_file)
                parsed_notes.append((md_file, parsed_note))
                print(f"   📄 Parsed: {parsed_note.title}")
            except Exception as e:
                print(f"   ❌ Error parsing {md_file}: {e}")
        
        # Second pass: add nodes and relationships
        for md_file, parsed_note in parsed_notes:
            await self._add_parsed_note(md_file, parsed_note)
        
        # Third pass: resolve wiki-links to actual node IDs
        await self._resolve_wiki_links()
        
        # Save the updated graph
        await self._save_graph()
        
        print(f"✅ Scanned {len(parsed_notes)} notes")
    
    async def _add_parsed_note(self, file_path: Path, parsed_note: ParsedNote):
        """Add a parsed note to the graph"""
        try:
            # Create graph node
            node = GraphNode(
                id=parsed_note.id,
                title=parsed_note.title,
                content=parsed_note.content,
                category=parsed_note.category,
                tags=parsed_note.tags,
                metadata=parsed_note.metadata,
                content_hash=parsed_note.content_hash,
                created_at=parsed_note.metadata.get('created', datetime.now().isoformat()),
                updated_at=parsed_note.metadata.get('updated', datetime.now().isoformat()),
                file_path=str(file_path),
                parent_id=parsed_note.parent,
                children_ids=parsed_note.children
            )
            
            # Add to indexes
            self.nodes_by_id[node.id] = node
            self.title_to_id[node.title] = node.id
            self._update_indexes(node)
            
            # Add to ChromaDB for semantic search
            await self._add_to_chroma(node)
            
            # Add relationships as edges
            for relationship in parsed_note.relationships:
                await self._add_relationship(relationship)
                
        except Exception as e:
            print(f"Error adding parsed note {parsed_note.title}: {e}")
    
    async def _add_to_chroma(self, node: GraphNode):
        """Add node to ChromaDB for semantic search"""
        try:
            # Prepare metadata for ChromaDB
            chroma_metadata = {
                'title': node.title,
                'category': node.category,
                'tags': ', '.join(node.tags),
                'content_hash': node.content_hash,
                'created_at': node.created_at,
                'updated_at': node.updated_at,
                'file_path': node.file_path
            }
            
            # Check if we need to generate embeddings manually
            provider_info = self.embedding_service.get_provider_info()
            if provider_info['type'] == 'openai':
                embedding = await self.embedding_service.embed_text(node.content)
                self.collection.add(
                    documents=[node.content],
                    metadatas=[chroma_metadata],
                    ids=[node.id],
                    embeddings=[embedding]
                )
            else:
                self.collection.add(
                    documents=[node.content],
                    metadatas=[chroma_metadata],
                    ids=[node.id]
                )
                
        except Exception as e:
            print(f"Error adding to ChromaDB: {e}")
    
    async def _add_relationship(self, relationship: Relationship):
        """Add a relationship as an edge"""
        edge_id = f"{relationship.source_id}-{relationship.target_id}-{relationship.relation_type.value}"
        
        edge = GraphEdge(
            source_id=relationship.source_id,
            target_id=relationship.target_id,
            relation_type=relationship.relation_type.value,
            metadata=relationship.metadata,
            weight=1.0
        )
        
        self.edges_by_id[edge_id] = edge
    
    async def _resolve_wiki_links(self):
        """Resolve wiki-links to actual node IDs and create edges"""
        print(f"🔗 Starting wiki-link resolution for {len(self.nodes_by_id)} nodes")
        print(f"   Available titles: {list(self.title_to_id.keys())}")
        
        resolved_count = 0
        broken_count = 0
        
        for node in self.nodes_by_id.values():
            # Get the original parsed note to access wiki-links
            file_path = Path(node.file_path)
            if file_path.exists():
                try:
                    parsed_note = self.markdown_parser.parse_file(file_path)
                    
                    for wiki_link in parsed_note.wiki_links:
                        # Try multiple resolution strategies
                        target_id = self._resolve_wiki_link_target(wiki_link.target)
                        
                        if target_id:
                            # Create edge for wiki-link
                            edge_id = f"{node.id}-{target_id}-wiki_link"
                            edge = GraphEdge(
                                source_id=node.id,
                                target_id=target_id,
                                relation_type="wiki_link",
                                metadata={
                                    'type': 'wiki_link',
                                    'display': wiki_link.display,
                                    'line_number': wiki_link.line_number,
                                    'context': wiki_link.context
                                }
                            )
                            self.edges_by_id[edge_id] = edge
                            resolved_count += 1
                            print(f"   ✅ Resolved: {wiki_link.target} -> {target_id}")
                        else:
                            broken_count += 1
                            print(f"   ⚠️  Broken wiki-link: '{wiki_link.target}' in {node.title}")
                            
                except Exception as e:
                    print(f"Error resolving wiki-links for {node.title}: {e}")
        
        print(f"🔗 Wiki-link resolution complete: {resolved_count} resolved, {broken_count} broken")
    
    def _resolve_wiki_link_target(self, target: str) -> Optional[str]:
        """Resolve a wiki-link target to a node ID using multiple strategies including path-based resolution"""
        # Strategy 1: Exact match
        if target in self.title_to_id:
            return self.title_to_id[target]
        
        # Strategy 2: Path-based resolution (for links like "ideas/note-title")
        if '/' in target:
            # This is a path-based link, try to find by file path
            for node in self.nodes_by_id.values():
                if node.file_path:
                    try:
                        # Get relative path from notes directory
                        notes_path = Path(os.getenv("NOTES_DIRECTORY", "./notes"))
                        file_path = Path(node.file_path)
                        relative_path = file_path.relative_to(notes_path)
                        # Remove .md extension for comparison
                        wiki_path = str(relative_path).replace('.md', '')
                        
                        if wiki_path == target or wiki_path.lower() == target.lower():
                            return node.id
                    except:
                        continue
        
        # Strategy 3: Case-insensitive match
        target_lower = target.lower()
        for title, node_id in self.title_to_id.items():
            if title.lower() == target_lower:
                return node_id
        
        # Strategy 4: Partial match (contains)
        for title, node_id in self.title_to_id.items():
            if target_lower in title.lower() or title.lower() in target_lower:
                return node_id
        
        # Strategy 5: Remove common separators and try again
        cleaned_target = target.replace('-', ' ').replace('_', ' ').strip()
        for title, node_id in self.title_to_id.items():
            cleaned_title = title.replace('-', ' ').replace('_', ' ').strip()
            if cleaned_target.lower() == cleaned_title.lower():
                return node_id
        
        # Strategy 6: Try to match just the filename part of a path-based link
        if '/' in target:
            filename_part = target.split('/')[-1]
            return self._resolve_wiki_link_target(filename_part)  # Recursive call with just filename
        
        return None
    
    def generate_obsidian_wiki_link(self, node_id: str) -> str:
        """
        Generate a proper Obsidian wiki-link for a node that will resolve correctly.
        Returns the link in format [[category/note-title]] or [[note-title]] for root notes.
        """
        if node_id not in self.nodes_by_id:
            return f"[[{node_id}]]"
        
        node = self.nodes_by_id[node_id]
        
        try:
            if node.file_path:
                # Get relative path from notes directory
                notes_path = Path(self.notes_directory)
                file_path = Path(node.file_path)
                relative_path = file_path.relative_to(notes_path)
                # Remove .md extension for wiki-link
                wiki_path = str(relative_path).replace('.md', '')
                return f"[[{wiki_path}]]"
        except Exception as e:
            print(f"Error generating wiki-link for {node.title}: {e}")
        
        # Fallback to title
        return f"[[{node.title}]]"
    
    async def add_note_from_content(self, title: str, content: str, category: str, tags: List[str] = None, file_path: str = None) -> str:
        """Add a note from content (for agent-generated notes)"""
        if tags is None:
            tags = []
        
        # Create a temporary parsed note
        metadata = {
            'title': title,
            'category': category,
            'tags': tags,
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        }
        
        parsed_note = ParsedNote(
            content=content,
            metadata=metadata,
            tags=tags,
            title=title,
            category=category
        )
        
        # Add to graph
        await self._add_parsed_note(Path(file_path) if file_path else Path(f"{title}.md"), parsed_note)
        
        # Save graph
        await self._save_graph()
        
        return parsed_note.id
    
    async def search_semantic(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Semantic search using ChromaDB"""
        if not self.collection:
            return []
            
        try:
            provider_info = self.embedding_service.get_provider_info()
            
            if provider_info['type'] == 'openai':
                query_embedding = await self.embedding_service.embed_text(query)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
            
            search_results = []
            
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance
                    
                    search_results.append(SearchResult(
                        content=doc,
                        category=metadata.get('category', 'Unknown'),
                        similarity=similarity,
                        node_id=results['ids'][0][i],
                        metadata=metadata
                    ))
            
            return search_results
            
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    async def search_content_in_files(self, query: str, case_sensitive: bool = False, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for content in actual files using grep-like functionality"""
        import re
        import asyncio
        
        search_results = []
        notes_path = Path(self.notes_directory)
        
        if not notes_path.exists():
            return search_results
        
        # Prepare regex pattern
        pattern_flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(query, pattern_flags)
        except re.error:
            # If regex fails, escape the query and search as literal text
            pattern = re.compile(re.escape(query), pattern_flags)
        
        try:
            for md_file in notes_path.rglob("*.md"):
                try:
                    # Get corresponding node for metadata
                    node = None
                    for n in self.nodes_by_id.values():
                        if n.file_path == str(md_file):
                            node = n
                            break
                    
                    if not node:
                        continue
                    
                    # Read file content
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Search for matches
                    matches = []
                    for line_num, line in enumerate(content.split('\n'), 1):
                        if pattern.search(line):
                            matches.append({
                                'line_number': line_num,
                                'line_content': line.strip(),
                                'context': self._get_line_context(content.split('\n'), line_num - 1, context_lines=2)
                            })
                            
                            if len(matches) >= 5:  # Limit matches per file
                                break
                    
                    if matches:
                        search_results.append({
                            'node_id': node.id,
                            'title': node.title,
                            'category': node.category,
                            'file_path': node.file_path,
                            'content_hash': node.content_hash,
                            'matches': matches,
                            'total_matches': len(matches),
                            'tags': node.tags,
                            'updated_at': node.updated_at
                        })
                    
                    if len(search_results) >= limit:
                        break
                        
                except Exception as e:
                    print(f"Error searching in file {md_file}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error in content search: {e}")
        
        # Sort by number of matches (descending)
        search_results.sort(key=lambda x: x['total_matches'], reverse=True)
        
        return search_results
    
    def _get_line_context(self, lines: List[str], line_index: int, context_lines: int = 2) -> str:
        """Get context around a specific line"""
        start = max(0, line_index - context_lines)
        end = min(len(lines), line_index + context_lines + 1)
        
        context_with_numbers = []
        for i in range(start, end):
            prefix = ">>> " if i == line_index else "    "
            context_with_numbers.append(f"{prefix}{i+1}: {lines[i]}")
        
        return '\n'.join(context_with_numbers)
    
    async def get_backlinks(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all nodes that link to this node"""
        backlinks = []
        
        for edge in self.edges_by_id.values():
            if edge.target_id == node_id:
                source_node = self.nodes_by_id.get(edge.source_id)
                if source_node:
                    backlinks.append({
                        'node_id': edge.source_id,
                        'title': source_node.title,
                        'relation_type': edge.relation_type,
                        'metadata': edge.metadata
                    })
        
        return backlinks
    
    async def get_outgoing_links(self, node_id: str) -> List[Dict[str, Any]]:
        """Get all nodes that this node links to"""
        outgoing_links = []
        
        for edge in self.edges_by_id.values():
            if edge.source_id == node_id:
                target_node = self.nodes_by_id.get(edge.target_id)
                if target_node:
                    outgoing_links.append({
                        'node_id': edge.target_id,
                        'title': target_node.title,
                        'relation_type': edge.relation_type,
                        'metadata': edge.metadata
                    })
        
        return outgoing_links
    
    async def get_nodes_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all nodes in a category"""
        node_ids = self.category_index.get(category, set())
        return [asdict(self.nodes_by_id[node_id]) for node_id in node_ids if node_id in self.nodes_by_id]
    
    async def get_nodes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all nodes with a specific tag"""
        node_ids = self.tag_index.get(tag, set())
        return [asdict(self.nodes_by_id[node_id]) for node_id in node_ids if node_id in self.nodes_by_id]
    
    async def get_hierarchy(self, parent_id: str) -> Dict[str, Any]:
        """Get hierarchical structure starting from a parent"""
        if parent_id not in self.nodes_by_id:
            return {}
        
        parent_node = self.nodes_by_id[parent_id]
        children_ids = self.hierarchy_index.get(parent_id, set())
        
        children = []
        for child_id in children_ids:
            if child_id in self.nodes_by_id:
                child_hierarchy = await self.get_hierarchy(child_id)
                children.append(child_hierarchy)
        
        return {
            'id': parent_id,
            'title': parent_node.title,
            'category': parent_node.category,
            'children': children
        }
    
    async def find_orphans(self) -> List[Dict[str, Any]]:
        """Find notes with no incoming links"""
        orphans = []
        
        nodes_with_incoming = set()
        for edge in self.edges_by_id.values():
            nodes_with_incoming.add(edge.target_id)
        
        for node_id, node in self.nodes_by_id.items():
            if node_id not in nodes_with_incoming:
                orphans.append(asdict(node))
        
        return orphans
    
    async def find_broken_links(self) -> List[Dict[str, Any]]:
        """Find links to non-existent nodes"""
        broken_links = []
        
        for edge in self.edges_by_id.values():
            if edge.target_id not in self.nodes_by_id:
                source_node = self.nodes_by_id.get(edge.source_id)
                broken_links.append({
                    'source_id': edge.source_id,
                    'source_title': source_node.title if source_node else "Unknown",
                    'target_id': edge.target_id,
                    'relation_type': edge.relation_type,
                    'metadata': edge.metadata
                })
        
        return broken_links
    
    async def get_graph_data(self) -> Dict[str, Any]:
        """Get complete graph data for visualization"""
        nodes = []
        edges = []
        
        # Convert nodes for visualization (excluding content for efficiency)
        for node in self.nodes_by_id.values():
            nodes.append({
                'id': node.id,
                'title': node.title,
                'category': node.category,
                'tags': node.tags,
                'file_path': node.file_path,
                'content_hash': node.content_hash,
                'created_at': node.created_at,
                'updated_at': node.updated_at,
                'metadata': {
                    **node.metadata
                }
            })
        
        # Convert edges for visualization
        for edge in self.edges_by_id.values():
            edges.append({
                'source': edge.source_id,
                'target': edge.target_id,
                'weight': edge.weight,
                'relation_type': edge.relation_type,
                'metadata': edge.metadata
            })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'categories': list(self.category_index.keys()),
                'tags': list(self.tag_index.keys())
            }
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive graph statistics"""
        return {
            'total_nodes': len(self.nodes_by_id),
            'total_edges': len(self.edges_by_id),
            'categories': {cat: len(nodes) for cat, nodes in self.category_index.items()},
            'tags': {tag: len(nodes) for tag, nodes in self.tag_index.items()},
            'relationship_types': self._get_relationship_type_stats(),
            'orphans': len(await self.find_orphans()),
            'broken_links': len(await self.find_broken_links()),
            'hierarchy_depth': self._calculate_hierarchy_depth()
        }
    
    def _get_relationship_type_stats(self) -> Dict[str, int]:
        """Get statistics on relationship types"""
        stats = {}
        for edge in self.edges_by_id.values():
            stats[edge.relation_type] = stats.get(edge.relation_type, 0) + 1
        return stats
    
    def _calculate_hierarchy_depth(self) -> int:
        """Calculate the maximum depth of the hierarchy"""
        def depth(node_id: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
            
            if node_id in visited:
                return 0
            
            visited.add(node_id)
            children_ids = self.hierarchy_index.get(node_id, set())
            
            if not children_ids:
                return 1
            
            return 1 + max(depth(child_id, visited.copy()) for child_id in children_ids)
        
        # Find root nodes (nodes with no parents)
        root_nodes = []
        for node_id, node in self.nodes_by_id.items():
            if not node.parent_id:
                root_nodes.append(node_id)
        
        if not root_nodes:
            return 0
        
        return max(depth(root_id) for root_id in root_nodes)

    async def get_pkm_insights(self) -> Dict[str, Any]:
        """Get PKM insights and analytics"""
        insights = {}
        
        # Top connected nodes
        if self.nodes_by_id:
            node_connections = {}
            for edge in self.edges_by_id.values():
                node_connections[edge.source_id] = node_connections.get(edge.source_id, 0) + 1
                node_connections[edge.target_id] = node_connections.get(edge.target_id, 0) + 1
            
            if node_connections:
                top_connected = sorted(node_connections.items(), key=lambda x: x[1], reverse=True)[:5]
                insights["top_connected_nodes"] = [
                    {
                        "title": self.nodes_by_id[node_id].title,
                        "connections": count
                    } for node_id, count in top_connected if node_id in self.nodes_by_id
                ]
        
        # Orphan nodes (no connections)
        connected_nodes = set()
        for edge in self.edges_by_id.values():
            connected_nodes.add(edge.source_id)
            connected_nodes.add(edge.target_id)
        
        orphan_nodes = []
        for node_id, node in self.nodes_by_id.items():
            if node_id not in connected_nodes:
                orphan_nodes.append({
                    "title": node.title,
                    "category": node.category
                })
        
        insights["orphan_nodes"] = orphan_nodes[:10]  # Limit to 10
        
        # Category distribution
        insights["category_distribution"] = {}
        for category, node_ids in self.category_index.items():
            insights["category_distribution"][category] = len(node_ids)
        
        # Recent activity
        recent_nodes = sorted(
            self.nodes_by_id.values(),
            key=lambda x: x.updated_at,
            reverse=True
        )[:5]
        
        insights["recent_activity"] = [
            {
                "title": node.title,
                "category": node.category,
                "updated_at": node.updated_at
            } for node in recent_nodes
        ]
        
        return insights
    
    def _chunk_text(self, text: str, node_id: str, chunk_size: int = 500, overlap: int = 50) -> List[TextChunk]:
        """
        Split text into overlapping chunks for better semantic search
        
        Args:
            text: Text to chunk
            node_id: ID of the node this text belongs to
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of TextChunk objects
        """
        if len(text) <= chunk_size:
            return [TextChunk(
                content=text,
                start_index=0,
                end_index=len(text),
                chunk_index=0,
                total_chunks=1,
                node_id=node_id
            )]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        # Try to split on sentence boundaries first
        sentences = re.split(r'[.!?]+\s+', text)
        current_chunk = ""
        current_start = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would exceed chunk_size, save current chunk
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(TextChunk(
                    content=current_chunk.strip(),
                    start_index=current_start,
                    end_index=current_start + len(current_chunk),
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will be updated later
                    node_id=node_id
                ))
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                current_start = current_start + len(current_chunk) - len(overlap_text) - len(sentence) - 1
                chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    current_start = start
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append(TextChunk(
                content=current_chunk.strip(),
                start_index=current_start,
                end_index=current_start + len(current_chunk),
                chunk_index=chunk_index,
                total_chunks=0,  # Will be updated later
                node_id=node_id
            ))
        
        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.total_chunks = total_chunks
        
        return chunks
    
    async def unified_search(
        self, 
        query: str, 
        limit: int = 20,
        include_semantic: bool = True,
        include_grep: bool = True,
        include_title: bool = True,
        include_tag: bool = True,
        chunk_size: int = 500,
        semantic_threshold: float = 0.3
    ) -> List[UnifiedSearchResult]:
        """
        Unified search function that combines multiple search methods
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            include_semantic: Include semantic search results
            include_grep: Include grep/content search results
            include_title: Include title matching results
            include_tag: Include tag matching results
            chunk_size: Size for text chunking in semantic search
            semantic_threshold: Minimum similarity score for semantic results
            
        Returns:
            List of UnifiedSearchResult objects sorted by relevance
        """
        all_results = []
        
        # 1. Semantic Search with Chunking
        if include_semantic and self.collection:
            try:
                # Create chunks for all nodes if not already done
                chunked_content = []
                chunk_to_node = {}
                
                for node in self.nodes_by_id.values():
                    chunks = self._chunk_text(node.content, node.id, chunk_size)
                    for chunk in chunks:
                        chunk_id = f"{node.id}_chunk_{chunk.chunk_index}"
                        chunked_content.append(chunk.content)
                        chunk_to_node[len(chunked_content) - 1] = {
                            'node': node,
                            'chunk': chunk
                        }
                
                # Perform semantic search on chunks
                provider_info = self.embedding_service.get_provider_info()
                
                if provider_info['type'] == 'openai':
                    query_embedding = await self.embedding_service.embed_text(query)
                    # For chunked search, we need to search against our chunk embeddings
                    # For now, fall back to node-level search
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=min(limit, len(self.nodes_by_id))
                    )
                else:
                    results = self.collection.query(
                        query_texts=[query],
                        n_results=min(limit, len(self.nodes_by_id))
                    )
                
                if results['documents'] and results['documents'][0]:
                    for i, doc in enumerate(results['documents'][0]):
                        metadata = results['metadatas'][0][i]
                        distance = results['distances'][0][i] if results['distances'] else 0
                        similarity = 1 - distance
                        
                        if similarity >= semantic_threshold:
                            node_id = results['ids'][0][i]
                            node = self.nodes_by_id.get(node_id)
                            
                            if node:
                                # Create snippet from the most relevant part
                                snippet = self._create_semantic_snippet(doc, query, max_length=200)
                                
                                all_results.append(UnifiedSearchResult(
                                    content=doc,
                                    title=node.title,
                                    category=node.category,
                                    source_type="semantic",
                                    relevance_score=similarity,
                                    node_id=node_id,
                                    file_path=node.file_path,
                                    snippet=snippet,
                                    metadata={"similarity": similarity, "search_type": "semantic"}
                                ))
                
            except Exception as e:
                print(f"Error in semantic search: {e}")
        
        # 2. Grep/Content Search
        if include_grep:
            try:
                grep_results = await self.search_content_in_files(query, limit=limit//2)
                
                for result in grep_results:
                    node = self.nodes_by_id.get(result['node_id'])
                    if node:
                        for match in result['matches']:
                            snippet = self._create_grep_snippet(
                                match['line_content'], 
                                query, 
                                max_length=200
                            )
                            
                            # Calculate relevance based on number of matches and position
                            relevance = min(1.0, result['total_matches'] * 0.1 + 0.5)
                            
                            all_results.append(UnifiedSearchResult(
                                content=match['context'],
                                title=node.title,
                                category=node.category,
                                source_type="grep",
                                relevance_score=relevance,
                                node_id=result['node_id'],
                                file_path=result['file_path'],
                                line_number=match['line_number'],
                                context=match['context'],
                                snippet=snippet,
                                metadata={
                                    "total_matches": result['total_matches'],
                                    "line_number": match['line_number'],
                                    "search_type": "grep"
                                }
                            ))
                
            except Exception as e:
                print(f"Error in grep search: {e}")
        
        # 3. Title Search
        if include_title:
            query_lower = query.lower()
            for node in self.nodes_by_id.values():
                if query_lower in node.title.lower():
                    # Calculate relevance based on how much of title matches
                    title_lower = node.title.lower()
                    if title_lower == query_lower:
                        relevance = 1.0
                    elif title_lower.startswith(query_lower):
                        relevance = 0.9
                    else:
                        relevance = 0.7
                    
                    snippet = self._create_title_snippet(node.title, query, max_length=200)
                    
                    all_results.append(UnifiedSearchResult(
                        content=node.content[:300] + "..." if len(node.content) > 300 else node.content,
                        title=node.title,
                        category=node.category,
                        source_type="title",
                        relevance_score=relevance,
                        node_id=node.id,
                        file_path=node.file_path,
                        snippet=snippet,
                        metadata={"search_type": "title"}
                    ))
        
        # 4. Tag Search
        if include_tag:
            query_lower = query.lower()
            # Remove # if present in query
            clean_query = query_lower.replace('#', '')
            
            for tag, node_ids in self.tag_index.items():
                if clean_query in tag.lower():
                    relevance = 1.0 if tag.lower() == clean_query else 0.8
                    
                    for node_id in node_ids:
                        node = self.nodes_by_id.get(node_id)
                        if node:
                            snippet = f"Tagged with: #{tag}"
                            
                            all_results.append(UnifiedSearchResult(
                                content=node.content[:300] + "..." if len(node.content) > 300 else node.content,
                                title=node.title,
                                category=node.category,
                                source_type="tag",
                                relevance_score=relevance,
                                node_id=node_id,
                                file_path=node.file_path,
                                snippet=snippet,
                                metadata={"tag": tag, "search_type": "tag"}
                            ))
        
        # 5. Remove duplicates and sort by relevance
        unique_results = {}
        for result in all_results:
            # Use node_id + source_type as key to allow same node from different search types
            key = f"{result.node_id}_{result.source_type}"
            if key not in unique_results or result.relevance_score > unique_results[key].relevance_score:
                unique_results[key] = result
        
        # Sort by relevance score (descending) and return top results
        sorted_results = sorted(unique_results.values(), key=lambda x: x.relevance_score, reverse=True)
        return sorted_results[:limit]
    
    def _create_semantic_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """Create a snippet highlighting the most relevant part for semantic search"""
        # Find the part of content that best matches the query
        query_words = query.lower().split()
        sentences = re.split(r'[.!?]+', content)
        
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            sentence_lower = sentence.lower()
            score = sum(1 for word in query_words if word in sentence_lower)
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        if best_sentence:
            if len(best_sentence) > max_length:
                return best_sentence[:max_length-3] + "..."
            return best_sentence
        
        # Fallback to beginning of content
        if len(content) > max_length:
            return content[:max_length-3] + "..."
        return content
    
    def _create_grep_snippet(self, line_content: str, query: str, max_length: int = 200) -> str:
        """Create a snippet highlighting the search term in grep results"""
        # Find the position of the query in the line
        query_lower = query.lower()
        line_lower = line_content.lower()
        
        try:
            # Try regex search first
            pattern = re.compile(re.escape(query_lower), re.IGNORECASE)
            match = pattern.search(line_content)
            
            if match:
                start_pos = match.start()
                end_pos = match.end()
                
                # Create snippet centered around the match
                snippet_start = max(0, start_pos - max_length // 3)
                snippet_end = min(len(line_content), end_pos + max_length // 3)
                
                snippet = line_content[snippet_start:snippet_end]
                
                # Add ellipsis if we truncated
                if snippet_start > 0:
                    snippet = "..." + snippet
                if snippet_end < len(line_content):
                    snippet = snippet + "..."
                
                return snippet
        except:
            pass
        
        # Fallback to simple truncation
        if len(line_content) > max_length:
            return line_content[:max_length-3] + "..."
        return line_content
    
    def _create_title_snippet(self, title: str, query: str, max_length: int = 200) -> str:
        """Create a snippet for title matches"""
        if len(title) > max_length:
            return title[:max_length-3] + "..."
        return title


# Global instance
_enhanced_knowledge_graph = None

def get_enhanced_knowledge_graph() -> EnhancedKnowledgeGraph:
    """Get the global enhanced knowledge graph instance"""
    global _enhanced_knowledge_graph
    if _enhanced_knowledge_graph is None:
        _enhanced_knowledge_graph = EnhancedKnowledgeGraph()
    return _enhanced_knowledge_graph 