"""
Advanced Markdown Parser for PKM Systems
Supports wiki-links, YAML front-matter, and typed relationships
Following best practices for "second brain" / PKM systems
"""

import re
import yaml
from typing import Dict, List, Set, Optional, Tuple, NamedTuple
from pathlib import Path
from datetime import datetime
import hashlib
from dataclasses import dataclass, field
from enum import Enum

class RelationType(Enum):
    """Typed relationship enum for semantic clarity"""
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    RELATED_TO = "related_to"
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    EXAMPLE_OF = "example_of"

@dataclass
class WikiLink:
    """Represents a wiki-style link [[target|display]]"""
    target: str
    display: str = ""
    line_number: int = 0
    context: str = ""
    
    def __post_init__(self):
        if not self.display:
            self.display = self.target

@dataclass
class Relationship:
    """Represents a typed relationship between notes"""
    source_id: str
    target_id: str
    relation_type: RelationType
    metadata: Dict = field(default_factory=dict)
    
    @property
    def inverse_relation(self) -> RelationType:
        """Get the inverse relationship type"""
        inverse_map = {
            RelationType.PARENT_OF: RelationType.CHILD_OF,
            RelationType.CHILD_OF: RelationType.PARENT_OF,
            RelationType.SUPPORTS: RelationType.CONTRADICTS,
            RelationType.CONTRADICTS: RelationType.SUPPORTS,
            RelationType.DEPENDS_ON: RelationType.REFERENCES,  # Approximate
            RelationType.REFERENCES: RelationType.DEPENDS_ON,  # Approximate
            RelationType.EXTENDS: RelationType.RELATED_TO,      # Approximate
            RelationType.IMPLEMENTS: RelationType.RELATED_TO,   # Approximate
            RelationType.EXAMPLE_OF: RelationType.RELATED_TO,   # Approximate
        }
        return inverse_map.get(self.relation_type, RelationType.RELATED_TO)

@dataclass
class ParsedNote:
    """Comprehensive note representation with relationships"""
    content: str
    metadata: Dict
    wiki_links: List[WikiLink] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    title: str = ""
    category: str = ""
    parent: str = ""
    children: List[str] = field(default_factory=list)
    content_hash: str = ""
    id: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = self._calculate_content_hash()
        if not self.id:
            self.id = self._generate_deterministic_id()
    
    def _calculate_content_hash(self) -> str:
        """Calculate deterministic hash of content"""
        content_for_hash = f"{self.title}|{self.content}|{self.category}|{sorted(self.tags)}"
        return hashlib.sha256(content_for_hash.encode()).hexdigest()[:16]
    
    def _generate_deterministic_id(self) -> str:
        """Generate stable ID based on content hash"""
        return f"note_{self.content_hash}"

class LinkCache:
    """Fast O(1) backlink queries following PKM best practices"""
    
    def __init__(self):
        self.outgoing_links: Dict[str, Set[str]] = {}  # note_id -> set of target_ids
        self.incoming_links: Dict[str, Set[str]] = {}  # note_id -> set of source_ids
        self.link_metadata: Dict[Tuple[str, str], Dict] = {}  # (source, target) -> metadata
    
    def add_link(self, source_id: str, target_id: str, metadata: Dict = None):
        """Add a link to the cache"""
        # Outgoing links
        if source_id not in self.outgoing_links:
            self.outgoing_links[source_id] = set()
        self.outgoing_links[source_id].add(target_id)
        
        # Incoming links (backlinks)
        if target_id not in self.incoming_links:
            self.incoming_links[target_id] = set()
        self.incoming_links[target_id].add(source_id)
        
        # Link metadata
        if metadata:
            self.link_metadata[(source_id, target_id)] = metadata
    
    def get_outgoing_links(self, note_id: str) -> Set[str]:
        """Get all outgoing links from a note"""
        return self.outgoing_links.get(note_id, set())
    
    def get_incoming_links(self, note_id: str) -> Set[str]:
        """Get all incoming links to a note (backlinks)"""
        return self.incoming_links.get(note_id, set())
    
    def get_link_metadata(self, source_id: str, target_id: str) -> Dict:
        """Get metadata for a specific link"""
        return self.link_metadata.get((source_id, target_id), {})
    
    def remove_note(self, note_id: str):
        """Remove all links for a note"""
        # Remove outgoing links
        if note_id in self.outgoing_links:
            for target in self.outgoing_links[note_id]:
                if target in self.incoming_links:
                    self.incoming_links[target].discard(note_id)
                # Remove metadata
                self.link_metadata.pop((note_id, target), None)
            del self.outgoing_links[note_id]
        
        # Remove incoming links
        if note_id in self.incoming_links:
            for source in self.incoming_links[note_id]:
                if source in self.outgoing_links:
                    self.outgoing_links[source].discard(note_id)
                # Remove metadata
                self.link_metadata.pop((source, note_id), None)
            del self.incoming_links[note_id]
    
    def find_orphans(self) -> Set[str]:
        """Find notes with no incoming links"""
        all_notes = set(self.outgoing_links.keys()) | set(self.incoming_links.keys())
        return all_notes - set(self.incoming_links.keys())
    
    def find_broken_links(self, valid_note_ids: Set[str]) -> List[Tuple[str, str]]:
        """Find links to non-existent notes"""
        broken = []
        for source_id, targets in self.outgoing_links.items():
            for target in targets:
                if target not in valid_note_ids:
                    broken.append((source_id, target))
        return broken

class MarkdownParser:
    """Advanced markdown parser with PKM features"""
    
    def __init__(self):
        self.link_cache = LinkCache()
        self.note_id_mapping: Dict[str, str] = {}  # title/path -> note_id
        self.wiki_link_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        self.tag_pattern = re.compile(r'#([a-zA-Z0-9_-]+)')
        
        # Typed relationship patterns
        self.relationship_patterns = {
            RelationType.PARENT_OF: re.compile(r'parent::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.CHILD_OF: re.compile(r'child::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.SUPPORTS: re.compile(r'supports::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.CONTRADICTS: re.compile(r'contradicts::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.DEPENDS_ON: re.compile(r'depends::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.REFERENCES: re.compile(r'references::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.EXTENDS: re.compile(r'extends::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.IMPLEMENTS: re.compile(r'implements::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
            RelationType.EXAMPLE_OF: re.compile(r'example::\s*\[\[([^\]]+)\]\]', re.IGNORECASE),
        }
    
    def parse_file(self, file_path: Path, content: str = None) -> ParsedNote:
        """Parse a markdown file with all PKM features"""
        if content is None:
            content = file_path.read_text(encoding='utf-8')
        
        # Parse YAML front-matter
        metadata, body_content = self._parse_frontmatter(content)
        
        # Extract basic information
        title = self._extract_title(body_content, metadata, file_path)
        category = self._extract_category(metadata, file_path)
        tags = self._extract_tags(body_content, metadata)
        
        # Parse wiki-links
        wiki_links = self._parse_wiki_links(body_content)
        
        # Parse typed relationships
        relationships = self._parse_relationships(body_content, title)
        
        # Extract hierarchy information
        parent, children = self._extract_hierarchy(metadata, relationships)
        
        # Create parsed note
        parsed_note = ParsedNote(
            content=body_content,
            metadata=metadata,
            wiki_links=wiki_links,
            relationships=relationships,
            tags=tags,
            title=title,
            category=category,
            parent=parent,
            children=children
        )
        
        # Update link cache
        self._update_link_cache(parsed_note)
        
        # Update note ID mapping
        self.note_id_mapping[title] = parsed_note.id
        self.note_id_mapping[str(file_path)] = parsed_note.id
        
        return parsed_note
    
    def _parse_frontmatter(self, content: str) -> Tuple[Dict, str]:
        """Parse YAML front-matter"""
        if not content.startswith('---'):
            return {}, content
        
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1]) or {}
                body_content = parts[2].strip()
                return metadata, body_content
        except yaml.YAMLError as e:
            print(f"Warning: Invalid YAML front-matter: {e}")
        
        return {}, content
    
    def _extract_title(self, content: str, metadata: Dict, file_path: Path) -> str:
        """Extract title from various sources"""
        # 1. From YAML front-matter
        if 'title' in metadata:
            return metadata['title']
        
        # 2. From first H1 heading
        heading_match = self.heading_pattern.search(content)
        if heading_match and heading_match.group(1) == '#':
            return heading_match.group(2).strip()
        
        # 3. From filename
        return file_path.stem
    
    def _extract_category(self, metadata: Dict, file_path: Path) -> str:
        """Extract category from metadata or file path"""
        if 'category' in metadata:
            return metadata['category']
        
        # Determine from folder structure
        categories = {
            'ideas': 'Ideas to Develop',
            'personal': 'Personal',
            'research': 'Research',
            'reading-list': 'Reading List',
            'projects': 'Projects',
            'learning': 'Learning',
            'quick-notes': 'Quick Notes'
        }
        
        for folder, category in categories.items():
            if folder in str(file_path):
                return category
        
        return 'Quick Notes'
    
    def _extract_tags(self, content: str, metadata: Dict) -> List[str]:
        """Extract tags from content and metadata"""
        tags = set()
        
        # From YAML front-matter
        if 'tags' in metadata:
            meta_tags = metadata['tags']
            if isinstance(meta_tags, list):
                tags.update(meta_tags)
            elif isinstance(meta_tags, str):
                tags.update(tag.strip() for tag in meta_tags.split(','))
        
        # From hashtags in content
        hashtag_matches = self.tag_pattern.findall(content)
        tags.update(hashtag_matches)
        
        return sorted(list(tags))
    
    def _parse_wiki_links(self, content: str) -> List[WikiLink]:
        """Parse wiki-style links [[target|display]]"""
        wiki_links = []
        
        for match in self.wiki_link_pattern.finditer(content):
            link_text = match.group(1)
            
            # Handle pipe notation [[target|display]]
            if '|' in link_text:
                target, display = link_text.split('|', 1)
                target = target.strip()
                display = display.strip()
            else:
                target = link_text.strip()
                display = target
            
            # Find line number
            line_number = content[:match.start()].count('\n') + 1
            
            # Extract context (surrounding text)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end].replace('\n', ' ')
            
            wiki_links.append(WikiLink(
                target=target,
                display=display,
                line_number=line_number,
                context=context
            ))
        
        return wiki_links
    
    def _parse_relationships(self, content: str, source_title: str) -> List[Relationship]:
        """Parse typed relationships from content"""
        relationships = []
        
        for relation_type, pattern in self.relationship_patterns.items():
            matches = pattern.findall(content)
            for target_title in matches:
                target_id = self.note_id_mapping.get(target_title, f"note_{target_title}")
                source_id = self.note_id_mapping.get(source_title, f"note_{source_title}")
                
                relationships.append(Relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=relation_type,
                    metadata={
                        'source_title': source_title,
                        'target_title': target_title,
                        'discovered_at': datetime.now().isoformat()
                    }
                ))
        
        return relationships
    
    def _extract_hierarchy(self, metadata: Dict, relationships: List[Relationship]) -> Tuple[str, List[str]]:
        """Extract parent-child hierarchy"""
        parent = ""
        children = []
        
        # From YAML front-matter
        if 'parent' in metadata:
            parent = metadata['parent']
        
        if 'children' in metadata:
            if isinstance(metadata['children'], list):
                children = metadata['children']
            elif isinstance(metadata['children'], str):
                children = [child.strip() for child in metadata['children'].split(',')]
        
        # From typed relationships
        for rel in relationships:
            if rel.relation_type == RelationType.PARENT_OF:
                children.append(rel.target_id)
            elif rel.relation_type == RelationType.CHILD_OF:
                parent = rel.target_id
        
        return parent, children
    
    def _update_link_cache(self, note: ParsedNote):
        """Update the link cache with note's links"""
        # Add wiki-links to cache
        for link in note.wiki_links:
            target_id = self.note_id_mapping.get(link.target, f"note_{link.target}")
            self.link_cache.add_link(
                source_id=note.id,
                target_id=target_id,
                metadata={
                    'type': 'wiki_link',
                    'display': link.display,
                    'line_number': link.line_number,
                    'context': link.context
                }
            )
        
        # Add typed relationships to cache
        for rel in note.relationships:
            self.link_cache.add_link(
                source_id=rel.source_id,
                target_id=rel.target_id,
                metadata={
                    'type': 'typed_relationship',
                    'relation_type': rel.relation_type.value,
                    **rel.metadata
                }
            )
    
    def get_backlinks(self, note_id: str) -> Set[str]:
        """Get all notes that link to this note (O(1) lookup)"""
        return self.link_cache.get_incoming_links(note_id)
    
    def get_outgoing_links(self, note_id: str) -> Set[str]:
        """Get all notes that this note links to (O(1) lookup)"""
        return self.link_cache.get_outgoing_links(note_id)
    
    def find_orphans(self) -> Set[str]:
        """Find notes with no incoming links"""
        return self.link_cache.find_orphans()
    
    def find_broken_links(self, valid_note_ids: Set[str]) -> List[Tuple[str, str]]:
        """Find links to non-existent notes"""
        return self.link_cache.find_broken_links(valid_note_ids)
    
    def resolve_note_id(self, title_or_path: str) -> Optional[str]:
        """Resolve a title or path to a note ID"""
        return self.note_id_mapping.get(title_or_path)
    
    def get_relationship_graph(self) -> Dict[str, List[Dict]]:
        """Get the full relationship graph for visualization"""
        graph = {}
        
        for source_id, targets in self.link_cache.outgoing_links.items():
            graph[source_id] = []
            for target_id in targets:
                metadata = self.link_cache.get_link_metadata(source_id, target_id)
                graph[source_id].append({
                    'target': target_id,
                    'metadata': metadata
                })
        
        return graph
    
    def write_relationships_to_note(self, note_path: Path, relationships: List[Relationship]):
        """Write relationships back to markdown file (round-tripping)"""
        try:
            content = note_path.read_text(encoding='utf-8')
            
            # Parse existing front-matter
            metadata, body_content = self._parse_frontmatter(content)
            
            # Update relationships in metadata
            for rel in relationships:
                if rel.relation_type == RelationType.PARENT_OF:
                    if 'children' not in metadata:
                        metadata['children'] = []
                    target_title = rel.metadata.get('target_title', rel.target_id)
                    if target_title not in metadata['children']:
                        metadata['children'].append(target_title)
                
                elif rel.relation_type == RelationType.CHILD_OF:
                    metadata['parent'] = rel.metadata.get('target_title', rel.target_id)
            
            # Write back to file
            new_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n\n{body_content}"
            note_path.write_text(new_content, encoding='utf-8')
            
        except Exception as e:
            print(f"Error writing relationships to {note_path}: {e}")

# Global parser instance
_markdown_parser = None

def get_markdown_parser() -> MarkdownParser:
    """Get the global markdown parser instance"""
    global _markdown_parser
    if _markdown_parser is None:
        _markdown_parser = MarkdownParser()
    return _markdown_parser 