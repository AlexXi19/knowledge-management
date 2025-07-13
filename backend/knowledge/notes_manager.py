import os
import yaml
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import asyncio
import aiofiles
import re
from dataclasses import dataclass

from knowledge.hash_utils import calculate_content_hash, get_hash_tracker, HashTracker

@dataclass
class Note:
    """Represents a single note with hash tracking"""
    path: str
    title: str
    content: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict
    content_hash: str = ""  # Add content hash field
    
    def __post_init__(self):
        """Calculate content hash after initialization"""
        if not self.content_hash:
            self.content_hash = calculate_content_hash(self.content)
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "content_hash": self.content_hash
        }
    
    def has_content_changed(self, new_content: str) -> bool:
        """Check if content has changed by comparing hashes"""
        new_hash = calculate_content_hash(new_content)
        return self.content_hash != new_hash
    
    def update_content_hash(self):
        """Update the content hash based on current content"""
        self.content_hash = calculate_content_hash(self.content)
        
    def get_obsidian_wiki_link(self, notes_directory: Path) -> str:
        """Get the proper Obsidian wiki-link path for this note"""
        try:
            # Get relative path from notes directory to this note (without .md extension)
            note_path = Path(self.path)
            relative_path = note_path.relative_to(notes_directory)
            # Remove .md extension for wiki-link
            wiki_path = str(relative_path).replace('.md', '')
            return f"[[{wiki_path}]]"
        except Exception:
            # Fallback to title if path calculation fails
            return f"[[{self.title}]]"

class NotesManager:
    """Manages note files and directory structure with hash-based caching"""
    
    def __init__(self, notes_directory: str = None):
        self.notes_directory = Path(notes_directory or os.getenv("NOTES_DIRECTORY", "./notes"))
        self.notes_index: Dict[str, Note] = {}
        self.hash_tracker = get_hash_tracker()
        self.categories = {
            "Ideas to Develop": "ideas",
            "Personal": "personal", 
            "Research": "research",
            "Reading List": "reading-list",
            "Projects": "projects",
            "Learning": "learning",
            "Quick Notes": "quick-notes",
            "Web Content": "web-content"  # Add web content category
        }
        self.initialized = False
    
    def get_obsidian_wiki_link_for_note(self, note_title: str, note_category: str = None) -> str:
        """
        Generate the proper Obsidian wiki-link path for a note title and category.
        This ensures Obsidian can resolve the link correctly.
        
        Args:
            note_title: The title of the note
            note_category: The category/folder the note is in
            
        Returns:
            Properly formatted wiki-link with path, e.g., [[ideas/My Note]]
        """
        try:
            # Find the note in our index first
            for note in self.notes_index.values():
                if note.title == note_title:
                    return note.get_obsidian_wiki_link(self.notes_directory)
            
            # If not found in index, generate based on category
            if note_category and note_category in self.categories:
                folder_name = self.categories[note_category]
                # Sanitize title for filename
                safe_title = re.sub(r'[^\w\s-]', '', note_title).strip()
                safe_title = re.sub(r'[-\s]+', '-', safe_title)
                return f"[[{folder_name}/{safe_title}]]"
            
            # Fallback to bare title
            return f"[[{note_title}]]"
            
        except Exception as e:
            print(f"Error generating wiki-link for {note_title}: {e}")
            return f"[[{note_title}]]"
    
    def _fix_wiki_links_in_content(self, content: str) -> str:
        """
        Fix bare wiki-links in content to use proper paths for Obsidian compatibility.
        Converts [[Note Title]] to [[category/note-title]] where appropriate.
        """
        import re
        
        def replace_wiki_link(match):
            link_content = match.group(1).strip()
            
            # Skip if already has a path (contains '/')
            if '/' in link_content:
                return match.group(0)
            
            # Skip if it's a display link with |
            if '|' in link_content:
                target, display = link_content.split('|', 1)
                target = target.strip()
                display = display.strip()
                
                # Try to resolve the target
                proper_link = self.get_obsidian_wiki_link_for_note(target)
                if proper_link != f"[[{target}]]":
                    # Extract path from proper link
                    path_match = re.match(r'\[\[([^\]]+)\]\]', proper_link)
                    if path_match:
                        return f"[[{path_match.group(1)}|{display}]]"
                
                return match.group(0)
            
            # Try to resolve bare link
            proper_link = self.get_obsidian_wiki_link_for_note(link_content)
            return proper_link
        
        # Pattern to match wiki-links
        wiki_link_pattern = r'\[\[([^\]]+)\]\]'
        return re.sub(wiki_link_pattern, replace_wiki_link, content)
    
    async def initialize(self):
        """Initialize the notes manager with hash tracking"""
        if self.initialized:
            return
            
        # Create notes directory if it doesn't exist
        self.notes_directory.mkdir(parents=True, exist_ok=True)
        
        # Create category subdirectories
        for category, folder_name in self.categories.items():
            category_path = self.notes_directory / folder_name
            category_path.mkdir(exist_ok=True)
            
            # Create a README for each category if it doesn't exist
            readme_path = category_path / "README.md"
            if not readme_path.exists():
                await self._create_category_readme(category, folder_name)
        
        # Scan existing notes with hash checking
        await self._scan_existing_notes()
        
        # Cleanup stale cache entries
        valid_note_paths = set(self.notes_index.keys())
        self.hash_tracker.cleanup_stale_entries(valid_note_paths)
        
        self.initialized = True
        print(f"📁 Notes Manager initialized with {len(self.notes_index)} existing notes")
        
        # Print cache stats
        cache_stats = self.hash_tracker.get_cache_stats()
        print(f"💾 Cache stats: {cache_stats['total_cached_items']} items, {cache_stats['total_mapped_notes']} mappings")
    
    async def _create_category_readme(self, category: str, folder_name: str):
        """Create a README file for a category"""
        readme_content = f"""# {category}

This folder contains notes categorized as "{category}".

## About This Category

"""
        
        # Add category-specific descriptions
        descriptions = {
            "Ideas to Develop": "Incomplete thoughts, concepts, and ideas that need further development and exploration.",
            "Personal": "Personal reflections, experiences, and private thoughts.",
            "Research": "Academic or professional research content, studies, and findings.",
            "Reading List": "Articles, books, and content to read later, along with summaries and notes.",
            "Projects": "Project-related notes, planning documents, and progress updates.",
            "Learning": "Educational content, course notes, and learning materials.",
            "Quick Notes": "Brief thoughts, reminders, and quick captures."
        }
        
        readme_content += descriptions.get(category, "Notes in this category.")
        readme_content += f"\n\n## Notes in this folder\n\n*Notes will be automatically listed here*\n\n---\n*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        readme_path = self.notes_directory / folder_name / "README.md"
        async with aiofiles.open(readme_path, 'w') as f:
            await f.write(readme_content)
    
    async def _scan_existing_notes(self):
        """Scan existing notes directory with hash-based change detection"""
        processed_count = 0
        cached_count = 0
        
        for root, dirs, files in os.walk(self.notes_directory):
            for file in files:
                if file.endswith(('.md', '.txt', '.markdown')):
                    file_path = Path(root) / file
                    try:
                        # Read file content to check if it changed
                        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                            current_content = await f.read()
                        
                        # Check if content has changed using hash
                        if not self.hash_tracker.has_content_changed(str(file_path), current_content):
                            # Content hasn't changed, try to load from cache
                            cached_note = self._load_note_from_cache(file_path, current_content)
                            if cached_note:
                                self.notes_index[str(file_path)] = cached_note
                                cached_count += 1
                                continue
                        
                        # Content has changed or no cache, parse the file
                        note = await self._parse_note_file(file_path, current_content)
                        if note:
                            self.notes_index[str(file_path)] = note
                            # Update hash cache
                            self.hash_tracker.update_hash(
                                str(file_path), 
                                note.content_hash,
                                {
                                    "title": note.title,
                                    "category": note.category,
                                    "updated_at": note.updated_at.isoformat()
                                }
                            )
                            processed_count += 1
                    except Exception as e:
                        print(f"Error processing note {file_path}: {e}")
        
        if cached_count > 0:
            print(f"⚡ Used cache for {cached_count} unchanged notes, processed {processed_count} new/modified notes")
    
    def _load_note_from_cache(self, file_path: Path, content: str) -> Optional[Note]:
        """Load note from cached hash data if available"""
        try:
            cached_hash = self.hash_tracker.get_cached_hash(str(file_path))
            if not cached_hash:
                return None
            
            # Get file timestamps
            stat = file_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            updated_at = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to get metadata from cache
            cache_entry = self.hash_tracker.hash_cache.get(str(file_path), {})
            cached_metadata = cache_entry.get('metadata', {})
            
            # Create note with cached information
            # Extract title and basic info from content quickly
            title = cached_metadata.get('title', file_path.stem)
            category = self._determine_category_from_path(file_path)
            
            # Create note object
            note = Note(
                path=str(file_path),
                title=title,
                content=content,
                category=category,
                tags=[],  # Will be parsed if needed
                created_at=created_at,
                updated_at=updated_at,
                metadata=cached_metadata,
                content_hash=cached_hash
            )
            
            return note
            
        except Exception as e:
            print(f"Error loading cached note {file_path}: {e}")
            return None
    
    async def _parse_note_file(self, file_path: Path, content: str = None) -> Optional[Note]:
        """Parse a note file and extract metadata"""
        try:
            if content is None:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
            
            # Extract frontmatter if present
            metadata = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    try:
                        metadata = yaml.safe_load(parts[1])
                        content = parts[2].strip()
                    except:
                        pass
            
            # Extract title (first # heading or filename)
            title = metadata.get('title', '')
            if not title:
                title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
                if title_match:
                    title = title_match.group(1).strip()
                else:
                    title = file_path.stem
            
            # Determine category from folder structure
            category = self._determine_category_from_path(file_path)
            
            # Extract tags
            tags = metadata.get('tags', [])
            if isinstance(tags, str):
                tags = [tag.strip() for tag in tags.split(',')]
            
            # Get file timestamps
            stat = file_path.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime)
            updated_at = datetime.fromtimestamp(stat.st_mtime)
            
            return Note(
                path=str(file_path),
                title=title,
                content=content,
                category=category,
                tags=tags,
                created_at=created_at,
                updated_at=updated_at,
                metadata=metadata
                # content_hash will be calculated automatically in __post_init__
            )
            
        except Exception as e:
            print(f"Error parsing note {file_path}: {e}")
            return None
    
    def _determine_category_from_path(self, file_path: Path) -> str:
        """Determine category based on file path"""
        relative_path = file_path.relative_to(self.notes_directory)
        
        # Check if it's in a category subfolder
        for category, folder_name in self.categories.items():
            if str(relative_path).startswith(folder_name + "/"):
                return category
        
        # Default category
        return "Quick Notes"
    
    async def create_note(self, title: str, content: str, category: str, tags: List[str] = None) -> Note:
        """Create a new note with hash tracking"""
        if tags is None:
            tags = []
        
        # Get category folder
        folder_name = self.categories.get(category, "quick-notes")
        category_path = self.notes_directory / folder_name
        
        # Generate filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{safe_title}.md"
        
        # Ensure unique filename
        counter = 1
        file_path = category_path / filename
        while file_path.exists():
            name_part = safe_title
            file_path = category_path / f"{name_part}-{counter}.md"
            counter += 1
        
        # Create frontmatter
        now = datetime.now()
        frontmatter = {
            'title': title,
            'category': category,
            'tags': tags,
            'created': now.isoformat(),
            'updated': now.isoformat()
        }
        
        # Create note content with frontmatter
        note_content = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n# {title}\n\n{content}"
        
        # Fix wiki-links in content
        note_content = self._fix_wiki_links_in_content(note_content)
        
        # Write file
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(note_content)
        
        # Create note object
        note = Note(
            path=str(file_path),
            title=title,
            content=content,
            category=category,
            tags=tags,
            created_at=now,
            updated_at=now,
            metadata=frontmatter
            # content_hash will be calculated automatically
        )
        
        # Add to index
        self.notes_index[str(file_path)] = note
        
        # Update hash cache
        self.hash_tracker.update_hash(
            str(file_path),
            note.content_hash,
            {
                "title": title,
                "category": category,
                "updated_at": now.isoformat()
            }
        )
        
        print(f"📝 Created note: {title} in {category}")
        return note
    
    async def update_note(self, note_path: str, additional_content: str) -> Note:
        """Update an existing note with additional content and hash tracking"""
        if note_path not in self.notes_index:
            raise ValueError(f"Note not found: {note_path}")
        
        note = self.notes_index[note_path]
        file_path = Path(note_path)
        
        # Read current content
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            current_content = await f.read()
        
        # Check if we actually need to update (avoid unnecessary writes)
        new_content_section = f"\n\n## Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{additional_content}"
        if new_content_section.strip() in current_content:
            print(f"⚠️  Content already exists in note: {note.title}")
            return note
        
        # Add new content
        updated_content = current_content + new_content_section
        
        # Update frontmatter
        if current_content.startswith('---'):
            parts = current_content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    metadata['updated'] = datetime.now().isoformat()
                    updated_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n\n{parts[2].strip()}{new_content_section}"
                except:
                    pass
        
        # Fix wiki-links in content
        updated_content = self._fix_wiki_links_in_content(updated_content)
        
        # Write updated content
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(updated_content)
        
        # Update note object
        note.content = note.content + new_content_section
        note.updated_at = datetime.now()
        note.update_content_hash()  # Recalculate hash
        
        # Update hash cache
        self.hash_tracker.update_hash(
            str(file_path),
            note.content_hash,
            {
                "title": note.title,
                "category": note.category,
                "updated_at": note.updated_at.isoformat()
            }
        )
        
        print(f"✏️  Updated note: {note.title}")
        return note
    
    async def find_related_notes(self, content: str, category: str = None, limit: int = 5) -> List[Note]:
        """Find notes related to the given content"""
        # Simple keyword matching for now - could be enhanced with embeddings
        content_lower = content.lower()
        keywords = set(re.findall(r'\b\w+\b', content_lower))
        
        scored_notes = []
        for note in self.notes_index.values():
            if category and note.category != category:
                continue
            
            # Score based on keyword overlap
            note_keywords = set(re.findall(r'\b\w+\b', note.content.lower()))
            overlap = len(keywords.intersection(note_keywords))
            
            if overlap > 0:
                scored_notes.append((note, overlap))
        
        # Sort by score and return top matches
        scored_notes.sort(key=lambda x: x[1], reverse=True)
        return [note for note, score in scored_notes[:limit]]
    
    async def get_notes_by_category(self, category: str) -> List[Note]:
        """Get all notes in a specific category"""
        return [note for note in self.notes_index.values() if note.category == category]
    
    async def get_all_notes(self) -> List[Note]:
        """Get all notes"""
        return list(self.notes_index.values())
    
    async def search_notes(self, query: str, limit: int = 10) -> List[Note]:
        """Search notes by content"""
        query_lower = query.lower()
        matching_notes = []
        
        for note in self.notes_index.values():
            if (query_lower in note.title.lower() or 
                query_lower in note.content.lower() or
                any(query_lower in tag.lower() for tag in note.tags)):
                matching_notes.append(note)
        
        return matching_notes[:limit]
    
    def get_notes_structure(self) -> Dict:
        """Get the notes directory structure"""
        structure = {}
        for category, folder_name in self.categories.items():
            notes_in_category = [note for note in self.notes_index.values() if note.category == category]
            structure[category] = {
                "folder": folder_name,
                "count": len(notes_in_category),
                "notes": [{"title": note.title, "path": note.path} for note in notes_in_category]
            }
        return structure

