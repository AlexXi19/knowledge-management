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

@dataclass
class Note:
    """Represents a single note"""
    path: str
    title: str
    content: str
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

class NotesManager:
    """Manages note files and directory structure"""
    
    def __init__(self, notes_directory: str = None):
        self.notes_directory = Path(notes_directory or os.getenv("NOTES_DIRECTORY", "./notes"))
        self.notes_index: Dict[str, Note] = {}
        self.categories = {
            "Ideas to Develop": "ideas",
            "Personal": "personal", 
            "Research": "research",
            "Reading List": "reading-list",
            "Projects": "projects",
            "Learning": "learning",
            "Quick Notes": "quick-notes"
        }
        self.initialized = False
    
    async def initialize(self):
        """Initialize the notes manager"""
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
        
        # Scan existing notes
        await self._scan_existing_notes()
        
        self.initialized = True
        print(f"📁 Notes Manager initialized with {len(self.notes_index)} existing notes")
    
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
        """Scan existing notes directory and build index"""
        for root, dirs, files in os.walk(self.notes_directory):
            for file in files:
                if file.endswith(('.md', '.txt', '.markdown')):
                    file_path = Path(root) / file
                    try:
                        note = await self._parse_note_file(file_path)
                        if note:
                            self.notes_index[str(file_path)] = note
                    except Exception as e:
                        print(f"Error parsing note {file_path}: {e}")
    
    async def _parse_note_file(self, file_path: Path) -> Optional[Note]:
        """Parse a note file and extract metadata"""
        try:
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
        """Create a new note"""
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
        )
        
        # Add to index
        self.notes_index[str(file_path)] = note
        
        print(f"📝 Created note: {title} in {category}")
        return note
    
    async def update_note(self, note_path: str, additional_content: str) -> Note:
        """Update an existing note with additional content"""
        if note_path not in self.notes_index:
            raise ValueError(f"Note not found: {note_path}")
        
        note = self.notes_index[note_path]
        file_path = Path(note_path)
        
        # Read current content
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            current_content = await f.read()
        
        # Add new content
        updated_content = current_content + f"\n\n## Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{additional_content}"
        
        # Update frontmatter
        if current_content.startswith('---'):
            parts = current_content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    metadata['updated'] = datetime.now().isoformat()
                    updated_content = f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n\n{parts[2].strip()}\n\n## Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{additional_content}"
                except:
                    pass
        
        # Write updated content
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(updated_content)
        
        # Update note object
        note.content = note.content + f"\n\n## Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{additional_content}"
        note.updated_at = datetime.now()
        
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
    
    async def decide_note_action(self, content: str, category: str) -> Tuple[str, Optional[Note]]:
        """Decide whether to create a new note or update an existing one"""
        # Find related notes
        related_notes = await self.find_related_notes(content, category, limit=3)
        
        if not related_notes:
            return "create", None
        
        # Check if content is very similar to an existing note
        for note in related_notes:
            content_similarity = self._calculate_similarity(content, note.content)
            if content_similarity > 0.7:  # High similarity threshold
                return "update", note
        
        # Check if it's a brief addition that could extend an existing note
        if len(content.split()) < 50:  # Short content
            return "update", related_notes[0]
        
        return "create", None
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0 