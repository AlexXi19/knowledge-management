# Sync Endpoint Usage Guide

The `/sync` endpoint allows you to synchronize your knowledge base with the current state of your vault directory. It's perfect for situations where you've manually added, modified, or deleted files and want to update the knowledge graph accordingly.

## 🚀 Basic Usage

### Regular Sync

```bash
curl -X POST http://localhost:8000/sync
```

### Force Rebuild (Complete Cleanup)

```bash
curl -X POST "http://localhost:8000/sync?force_rebuild=true"
```

## 📊 Response Format

The sync endpoint returns a detailed JSON response:

```json
{
  "sync_completed": true,
  "processing_time_seconds": 2.45,
  "timestamp": "2024-01-15T10:30:00",
  "vault_files_found": 25,
  "graph_nodes_before": 20,
  "changes_detected": {
    "new_files": ["./notes/new-idea.md"],
    "deleted_files": ["./notes/old-note.md"],
    "modified_files": ["./notes/updated-note.md"],
    "unchanged_files": ["./notes/stable-note.md"],
    "total_changes": 3,
    "force_rebuild": false
  },
  "actions_taken": [
    "Added new file: ./notes/new-idea.md",
    "Removed deleted file: ./notes/old-note.md",
    "Updated modified file: ./notes/updated-note.md",
    "Resolved wiki-links",
    "Saved updated graph",
    "Cleaned up hash cache",
    "Cleaned 2 orphaned vector entries"
  ],
  "graph_nodes_after": 21,
  "graph_edges_after": 15,
  "errors": [],
  "warnings": [],
  "cleanup_results": {
    "actions_taken": [
      "Removed 20 entries from ChromaDB",
      "Cleared 20 nodes and 15 edges from graph indexes",
      "Cleared hash cache (15 items, 20 mappings)",
      "Removed saved graph file",
      "Cleared NetworkX graph"
    ],
    "errors": [],
    "warnings": []
  }
}
```

## 🔧 How It Works

### 1. **Comprehensive Cleanup (Force Rebuild)**

When `force_rebuild=true`, the system performs a complete cleanup:

- **ChromaDB Vector Database**: Removes all embeddings and vector entries
- **Graph Indexes**: Clears all nodes, edges, and relationship mappings
- **Hash Cache**: Removes all cached content hashes and file mappings
- **Saved Files**: Deletes saved graph state files
- **NetworkX Graph**: Clears the in-memory graph structure
- **Category/Tag/Hierarchy Indexes**: Resets all organizational structures

### 2. **File Scanning**

- Scans the vault directory for all `.md` files
- Calculates content hashes for change detection
- Compares with cached hashes to identify changes

### 3. **Change Detection**

- **New files**: Present in vault but not in knowledge graph
- **Deleted files**: Present in knowledge graph but not in vault
- **Modified files**: Content hash differs from cached hash
- **Unchanged files**: Content hash matches cached hash

### 4. **Processing Changes**

- **New files**: Parse and add to knowledge graph + vector database
- **Deleted files**: Remove from knowledge graph, vector database, and all indexes
- **Modified files**: Remove old version, add updated version to all systems
- **Wiki-links**: Resolve all wiki-links after changes
- **Orphaned cleanup**: Remove any orphaned entries from vector database

### 5. **Vector Database Cleanup**

- **Individual file removal**: ChromaDB entries are removed when files are deleted
- **Orphaned entry detection**: Finds and removes vector entries without corresponding graph nodes
- **Force rebuild**: Completely clears and rebuilds the vector database

### 6. **Hash-Based Efficiency**

- Uses SHA-256 hashes to detect content changes
- Skips processing for unchanged files
- Maintains a persistent hash cache for performance

## 🎯 Use Cases

### Manual File Operations

```bash
# After manually creating new notes
curl -X POST http://localhost:8000/sync

# After deleting notes outside the system
curl -X POST http://localhost:8000/sync

# After editing notes directly
curl -X POST http://localhost:8000/sync
```

### System Recovery & Cleanup

```bash
# Force complete rebuild if something goes wrong
curl -X POST "http://localhost:8000/sync?force_rebuild=true"

# Clean up after corruption or inconsistencies
curl -X POST "http://localhost:8000/sync?force_rebuild=true"
```

### Integration with External Tools

```bash
# Sync after external note-taking apps modify files
curl -X POST http://localhost:8000/sync
```

## 🔄 Force Rebuild vs Regular Sync

### Regular Sync (Default)

- Only processes files that have actually changed
- Uses hash comparison for efficiency
- Cleans up orphaned vector entries
- Maintains existing graph structure
- Faster for large vaults with few changes

### Force Rebuild

- **Complete cleanup**: Removes ALL data from vector database, indexes, and caches
- **Full rebuild**: Processes ALL files regardless of hash status
- **Fresh start**: Rebuilds the entire knowledge graph from scratch
- **Consistency guarantee**: Ensures complete consistency across all systems
- **Slower but thorough**: Takes longer but ensures no stale data remains

## 📈 Performance

- **Hash-based detection**: Only processes changed files in regular sync
- **Incremental updates**: Maintains existing graph structure when possible
- **Vector database optimization**: Cleans orphaned entries automatically
- **Efficient caching**: Persistent hash cache for fast comparisons
- **Parallel processing**: Handles multiple files efficiently

## 🛠️ Testing

Run the test script to verify functionality:

```bash
cd backend
python test_sync_endpoint.py
```

## 💡 Best Practices

1. **Regular syncing**: Run sync after manual file operations
2. **Force rebuild for issues**: Use `force_rebuild=true` when experiencing:
   - Inconsistent search results
   - Missing or stale data
   - Vector database corruption
   - Performance degradation
3. **Monitor cleanup results**: Check the response for cleanup actions and errors
4. **Performance optimization**: Regular sync is faster for large vaults
5. **Integration**: Integrate with file watchers or external tools
6. **Backup consideration**: Force rebuild removes all cached data

## 🔗 Related Endpoints

- `GET /knowledge/graph`: View current knowledge graph
- `GET /cache/stats`: Check hash cache statistics
- `POST /cache/clear`: Clear hash cache (use with caution)
- `POST /cache/rebuild`: Rebuild cache using agent tools

## 📝 Example Workflow

```bash
# 1. Check current state
curl http://localhost:8000/knowledge/graph

# 2. Manually add some notes to your vault
echo "# New Idea\nThis is a new idea" > notes/new-idea.md

# 3. Sync to update knowledge graph
curl -X POST http://localhost:8000/sync

# 4. If something seems wrong, force rebuild
curl -X POST "http://localhost:8000/sync?force_rebuild=true"

# 5. Verify the new note was added
curl http://localhost:8000/knowledge/graph
```

## 🧹 Cleanup Details

The enhanced sync endpoint now performs comprehensive cleanup of:

### Vector Database (ChromaDB)

- Removes deleted note embeddings
- Cleans orphaned vector entries
- Force rebuild clears entire collection

### Graph Indexes

- Node mappings (ID, title, category, tags)
- Edge relationships
- Hierarchy structures
- NetworkX graph representation

### Cache Systems

- Content hash cache
- File-to-node mappings
- Stale entry removal

### File System

- Saved graph state files
- Temporary processing files

This comprehensive approach ensures your knowledge base remains consistent, performant, and free of stale data!

## ⚠️ Important Notes

- **Force rebuild is destructive**: It removes ALL cached data and rebuilds from scratch
- **Backup your vault**: Always ensure your markdown files are backed up
- **Check results**: Monitor the response for any errors or warnings
- **Performance impact**: Force rebuild takes longer but ensures complete consistency

This sync endpoint provides powerful vault management capabilities while maintaining the performance and consistency of your knowledge base!
