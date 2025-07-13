"""
File Watcher for Incremental Knowledge Graph Updates
Monitors markdown files for changes and updates the graph incrementally
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Set, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import time
from datetime import datetime
import threading

from .enhanced_knowledge_graph import get_enhanced_knowledge_graph
from .markdown_parser import get_markdown_parser

class MarkdownFileHandler(FileSystemEventHandler):
    """Handler for markdown file changes"""
    
    def __init__(self, callback: Callable[[str, str], None]):
        super().__init__()
        self.callback = callback
        self.debounce_time = 2.0  # Debounce file changes for 2 seconds
        self.pending_changes: Dict[str, float] = {}
        self.debounce_timer = None
        
    def on_modified(self, event: FileSystemEvent):
        """Handle file modifications"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        if file_path.endswith(('.md', '.markdown')):
            self._debounce_change(file_path, 'modified')
    
    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        if file_path.endswith(('.md', '.markdown')):
            self._debounce_change(file_path, 'created')
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        if file_path.endswith(('.md', '.markdown')):
            self._debounce_change(file_path, 'deleted')
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file moves/renames"""
        if event.is_directory:
            return
            
        if hasattr(event, 'dest_path'):
            # Handle rename
            old_path = event.src_path
            new_path = event.dest_path
            
            if old_path.endswith(('.md', '.markdown')):
                self._debounce_change(old_path, 'deleted')
            if new_path.endswith(('.md', '.markdown')):
                self._debounce_change(new_path, 'created')
    
    def _debounce_change(self, file_path: str, change_type: str):
        """Debounce file changes to avoid excessive updates"""
        current_time = time.time()
        self.pending_changes[file_path] = current_time
        
        # Cancel existing timer
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        # Start new timer
        self.debounce_timer = threading.Timer(
            self.debounce_time,
            self._process_pending_changes
        )
        self.debounce_timer.start()
    
    def _process_pending_changes(self):
        """Process all pending changes"""
        current_time = time.time()
        
        for file_path, change_time in list(self.pending_changes.items()):
            if current_time - change_time >= self.debounce_time:
                # Process the change
                self.callback(file_path, 'modified')  # Simplified to just 'modified'
                del self.pending_changes[file_path]

class KnowledgeGraphWatcher:
    """Monitors markdown files and updates the knowledge graph incrementally"""
    
    def __init__(self, notes_directory: str = None):
        self.notes_directory = Path(notes_directory or os.getenv("NOTES_DIRECTORY", "./notes"))
        self.observer = Observer()
        self.is_running = False
        self.graph = get_enhanced_knowledge_graph()
        self.parser = get_markdown_parser()
        
        # Statistics
        self.files_processed = 0
        self.last_update_time = None
        self.processing_queue = asyncio.Queue()
        
    async def start_watching(self):
        """Start monitoring the notes directory"""
        if not self.notes_directory.exists():
            print(f"⚠️  Notes directory does not exist: {self.notes_directory}")
            return
        
        print(f"👀 Starting file watcher for: {self.notes_directory}")
        
        # Create event handler
        handler = MarkdownFileHandler(self._on_file_change)
        
        # Set up observer
        self.observer.schedule(
            handler,
            str(self.notes_directory),
            recursive=True
        )
        
        # Start observer
        self.observer.start()
        self.is_running = True
        
        # Start processing queue
        asyncio.create_task(self._process_queue())
        
        print("✅ File watcher started successfully")
    
    def stop_watching(self):
        """Stop monitoring"""
        if self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            print("🛑 File watcher stopped")
    
    def _on_file_change(self, file_path: str, change_type: str):
        """Handle file change event"""
        # Add to processing queue
        try:
            self.processing_queue.put_nowait((file_path, change_type))
        except asyncio.QueueFull:
            print(f"⚠️  Processing queue full, skipping: {file_path}")
    
    async def _process_queue(self):
        """Process file changes from the queue"""
        while self.is_running:
            try:
                file_path, change_type = await asyncio.wait_for(
                    self.processing_queue.get(),
                    timeout=1.0
                )
                
                await self._process_file_change(file_path, change_type)
                self.files_processed += 1
                self.last_update_time = datetime.now()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing file change: {e}")
    
    async def _process_file_change(self, file_path: str, change_type: str):
        """Process a single file change"""
        try:
            path = Path(file_path)
            
            if change_type == 'deleted':
                await self._handle_file_deletion(path)
            else:
                await self._handle_file_update(path)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    async def _handle_file_deletion(self, file_path: Path):
        """Handle file deletion"""
        print(f"🗑️  File deleted: {file_path}")
        
        # Find node ID for this file
        node_id = None
        for node in self.graph.nodes_by_id.values():
            if node.file_path == str(file_path):
                node_id = node.id
                break
        
        if node_id:
            # Remove from graph
            await self._remove_node_from_graph(node_id)
            print(f"   ✅ Removed node: {node_id}")
        else:
            print(f"   ⚠️  No node found for deleted file")
    
    async def _handle_file_update(self, file_path: Path):
        """Handle file creation or modification"""
        if not file_path.exists():
            return
        
        print(f"📝 File updated: {file_path}")
        
        try:
            # Parse the file
            parsed_note = self.parser.parse_file(file_path)
            
            # Check if node already exists
            existing_node = None
            for node in self.graph.nodes_by_id.values():
                if node.file_path == str(file_path):
                    existing_node = node
                    break
            
            if existing_node:
                # Check if content actually changed
                if existing_node.content_hash != parsed_note.content_hash:
                    print(f"   🔄 Content changed, updating node: {existing_node.id}")
                    await self._update_existing_node(existing_node, parsed_note)
                else:
                    print(f"   ⚡ No content change, skipping: {existing_node.title}")
            else:
                # Create new node
                print(f"   ✨ Creating new node: {parsed_note.title}")
                await self._create_new_node(file_path, parsed_note)
                
        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
    
    async def _remove_node_from_graph(self, node_id: str):
        """Remove a node and all its edges from the graph"""
        # Remove from various indexes
        if node_id in self.graph.nodes_by_id:
            node = self.graph.nodes_by_id[node_id]
            
            # Remove from title mapping
            if node.title in self.graph.title_to_id:
                del self.graph.title_to_id[node.title]
            
            # Remove from category index
            if node.category in self.graph.category_index:
                self.graph.category_index[node.category].discard(node_id)
            
            # Remove from tag index
            for tag in node.tags:
                if tag in self.graph.tag_index:
                    self.graph.tag_index[tag].discard(node_id)
            
            # Remove from hierarchy index
            if node.parent_id in self.graph.hierarchy_index:
                self.graph.hierarchy_index[node.parent_id].discard(node_id)
            
            # Remove from nodes
            del self.graph.nodes_by_id[node_id]
        
        # Remove all edges involving this node
        edges_to_remove = []
        for edge_id, edge in self.graph.edges_by_id.items():
            if edge.source_id == node_id or edge.target_id == node_id:
                edges_to_remove.append(edge_id)
        
        for edge_id in edges_to_remove:
            del self.graph.edges_by_id[edge_id]
        
        # Remove from ChromaDB
        try:
            self.graph.collection.delete(ids=[node_id])
        except Exception as e:
            print(f"   ⚠️  Error removing from ChromaDB: {e}")
        
        # Save graph
        await self.graph._save_graph()
    
    async def _update_existing_node(self, existing_node, parsed_note):
        """Update an existing node with new content"""
        # Remove old node
        await self._remove_node_from_graph(existing_node.id)
        
        # Add updated node
        await self._create_new_node(Path(existing_node.file_path), parsed_note)
    
    async def _create_new_node(self, file_path: Path, parsed_note):
        """Create a new node from a parsed note"""
        # Add to graph using the enhanced knowledge graph method
        await self.graph._add_parsed_note(file_path, parsed_note)
        
        # Resolve wiki-links for this note
        await self.graph._resolve_wiki_links()
        
        # Save graph
        await self.graph._save_graph()
    
    def get_statistics(self) -> Dict:
        """Get file watcher statistics"""
        return {
            'is_running': self.is_running,
            'files_processed': self.files_processed,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'queue_size': self.processing_queue.qsize(),
            'notes_directory': str(self.notes_directory)
        }

# Global instance
_knowledge_graph_watcher = None

def get_knowledge_graph_watcher() -> KnowledgeGraphWatcher:
    """Get the global knowledge graph watcher instance"""
    global _knowledge_graph_watcher
    if _knowledge_graph_watcher is None:
        _knowledge_graph_watcher = KnowledgeGraphWatcher()
    return _knowledge_graph_watcher

async def start_file_watcher():
    """Convenience function to start the file watcher"""
    watcher = get_knowledge_graph_watcher()
    await watcher.start_watching()

def stop_file_watcher():
    """Convenience function to stop the file watcher"""
    watcher = get_knowledge_graph_watcher()
    watcher.stop_watching() 