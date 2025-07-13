"""
Hash utilities for content tracking and caching in the knowledge management system
"""
import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime
import os


def calculate_content_hash(content: str) -> str:
    """
    Calculate SHA-256 hash of content for tracking changes
    
    Args:
        content: The content to hash
        
    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def calculate_file_hash(file_path: str) -> Optional[str]:
    """
    Calculate hash of a file's content
    
    Args:
        file_path: Path to the file
        
    Returns:
        File content hash or None if file doesn't exist
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return calculate_content_hash(content)
    except (FileNotFoundError, IOError):
        return None


def calculate_metadata_hash(metadata: Dict[str, Any]) -> str:
    """
    Calculate hash of metadata for tracking changes
    
    Args:
        metadata: Dictionary of metadata
        
    Returns:
        Metadata hash string
    """
    # Sort keys for consistent hashing
    metadata_str = json.dumps(metadata, sort_keys=True, default=str)
    return hashlib.sha256(metadata_str.encode('utf-8')).hexdigest()


def calculate_combined_hash(content: str, metadata: Dict[str, Any] = None) -> str:
    """
    Calculate combined hash of content and metadata
    
    Args:
        content: The main content
        metadata: Optional metadata dictionary
        
    Returns:
        Combined hash string
    """
    content_hash = calculate_content_hash(content)
    
    if metadata:
        metadata_hash = calculate_metadata_hash(metadata)
        combined = f"{content_hash}:{metadata_hash}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    return content_hash


class HashTracker:
    """
    Manages hash tracking for content and files
    """
    
    def __init__(self, cache_file: str = ".knowledge_base/hash_cache.json"):
        self.cache_file = cache_file
        self.hash_cache = self._load_cache()
        self.note_to_node_mapping = self._load_mapping()
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """Load hash cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}
    
    def _save_cache(self):
        """Save hash cache to file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.hash_cache, f, indent=2, default=str)
        except IOError as e:
            print(f"Warning: Could not save hash cache: {e}")
    
    def _load_mapping(self) -> Dict[str, str]:
        """Load note to knowledge node mapping"""
        mapping_file = self.cache_file.replace('hash_cache.json', 'note_mapping.json')
        try:
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return {}
    
    def _save_mapping(self):
        """Save note to knowledge node mapping"""
        mapping_file = self.cache_file.replace('hash_cache.json', 'note_mapping.json')
        try:
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            with open(mapping_file, 'w') as f:
                json.dump(self.note_to_node_mapping, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save note mapping: {e}")
    
    def get_cached_hash(self, identifier: str) -> Optional[str]:
        """
        Get cached hash for an identifier
        
        Args:
            identifier: Unique identifier (file path, note id, etc.)
            
        Returns:
            Cached hash or None if not found
        """
        cache_entry = self.hash_cache.get(identifier)
        if cache_entry:
            return cache_entry.get('hash')
        return None
    
    def update_hash(self, identifier: str, content_hash: str, metadata: Dict[str, Any] = None):
        """
        Update hash cache for an identifier
        
        Args:
            identifier: Unique identifier
            content_hash: Content hash
            metadata: Optional metadata
        """
        self.hash_cache[identifier] = {
            'hash': content_hash,
            'updated_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self._save_cache()
    
    def has_content_changed(self, identifier: str, current_content: str) -> bool:
        """
        Check if content has changed since last processing
        
        Args:
            identifier: Unique identifier
            current_content: Current content to check
            
        Returns:
            True if content has changed, False if unchanged
        """
        cached_hash = self.get_cached_hash(identifier)
        if not cached_hash:
            return True  # No cache entry means it's new/changed
        
        current_hash = calculate_content_hash(current_content)
        return cached_hash != current_hash
    
    def get_knowledge_node_id(self, note_path: str) -> Optional[str]:
        """
        Get knowledge node ID for a note
        
        Args:
            note_path: Path to the note
            
        Returns:
            Knowledge node ID or None if not mapped
        """
        return self.note_to_node_mapping.get(note_path)
    
    def set_note_mapping(self, note_path: str, node_id: str):
        """
        Set mapping between note and knowledge node
        
        Args:
            note_path: Path to the note
            node_id: Knowledge node ID
        """
        self.note_to_node_mapping[note_path] = node_id
        self._save_mapping()
    
    def remove_note_mapping(self, note_path: str):
        """
        Remove mapping for a note
        
        Args:
            note_path: Path to the note
        """
        if note_path in self.note_to_node_mapping:
            del self.note_to_node_mapping[note_path]
            self._save_mapping()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'total_cached_items': len(self.hash_cache),
            'total_mapped_notes': len(self.note_to_node_mapping),
            'cache_file': self.cache_file,
            'last_updated': max(
                (entry.get('updated_at', '') for entry in self.hash_cache.values()),
                default='Never'
            )
        }
    
    def clear_cache(self):
        """Clear all cache data"""
        self.hash_cache.clear()
        self.note_to_node_mapping.clear()
        self._save_cache()
        self._save_mapping()
    
    def cleanup_stale_entries(self, valid_identifiers: set):
        """
        Remove cache entries for identifiers that no longer exist
        
        Args:
            valid_identifiers: Set of currently valid identifiers
        """
        stale_keys = set(self.hash_cache.keys()) - valid_identifiers
        for key in stale_keys:
            del self.hash_cache[key]
        
        stale_mappings = set(self.note_to_node_mapping.keys()) - valid_identifiers
        for key in stale_mappings:
            del self.note_to_node_mapping[key]
        
        if stale_keys or stale_mappings:
            self._save_cache()
            self._save_mapping()
            print(f"Cleaned up {len(stale_keys)} stale cache entries and {len(stale_mappings)} stale mappings")


# Global hash tracker instance
_hash_tracker = None


def get_hash_tracker() -> HashTracker:
    """Get global hash tracker instance"""
    global _hash_tracker
    if _hash_tracker is None:
        _hash_tracker = HashTracker()
    return _hash_tracker 