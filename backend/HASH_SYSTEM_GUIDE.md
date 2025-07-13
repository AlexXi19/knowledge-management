# Hash-Based Caching System Documentation

## Overview

This guide documents the advanced hash-based caching system implemented in the knowledge management agent. The system provides intelligent content change detection and performance optimization through SHA-256 hashing.

## Key Features

### 🔍 Content Change Detection

- **SHA-256 Hashing**: Uses cryptographic hashing to detect content changes
- **Intelligent Caching**: Avoids reprocessing unchanged content
- **File & Content Tracking**: Monitors both file-based and runtime content

### 🔗 Note-to-Knowledge Mapping

- **Persistent Mappings**: Maintains relationships between notes and knowledge graph nodes
- **Automatic Cleanup**: Removes stale mappings when files are deleted
- **Bidirectional Tracking**: Efficiently maps notes to knowledge nodes and vice versa

### ⚡ Performance Optimization

- **30%+ Performance Improvement**: Demonstrated in testing
- **Cache Hit Detection**: Tracks cache effectiveness
- **Lazy Loading**: Processes content only when changes are detected

## Architecture

### Core Components

#### 1. Hash Utilities (`knowledge/hash_utils.py`)

```python
# Content hashing
calculate_content_hash(content: str) -> str
calculate_file_hash(file_path: str) -> Optional[str]
calculate_combined_hash(content: str, metadata: Dict) -> str

# Global tracker
get_hash_tracker() -> HashTracker
```

#### 2. HashTracker Class

- **Persistent Storage**: Saves cache to `knowledge_base/hash_cache.json`
- **Note Mapping**: Stores mappings in `knowledge_base/note_mapping.json`
- **Cache Statistics**: Provides detailed performance metrics

#### 3. Enhanced Note Model

```python
@dataclass
class Note:
    # ... existing fields ...
    content_hash: str = ""  # SHA-256 hash of content

    def has_content_changed(self, new_content: str) -> bool
    def update_content_hash(self)
```

### Integration Points

#### Notes Manager

- **Startup Optimization**: Uses cached data for unchanged files
- **Change Detection**: Only parses modified files during initialization
- **Hash Updates**: Automatically updates hashes when content changes

#### Knowledge Graph

- **Node Caching**: Reuses existing knowledge nodes for unchanged content
- **Mapping Maintenance**: Tracks note-to-node relationships
- **Intelligent Updates**: Updates only when content actually changes

#### Agent Tools

- **Content Processing**: Caches categorization results
- **Note Operations**: Detects duplicate content before processing
- **Performance Tracking**: Reports cache hits and performance gains

## Usage Examples

### Basic Content Hashing

```python
from knowledge.hash_utils import calculate_content_hash, get_hash_tracker

# Calculate hash
content = "This is my content"
hash_value = calculate_content_hash(content)

# Track changes
tracker = get_hash_tracker()
tracker.update_hash("my_content_id", hash_value)

# Check for changes
has_changed = tracker.has_content_changed("my_content_id", new_content)
```

### Note-to-Knowledge Mapping

```python
# Set mapping
tracker.set_note_mapping("/path/to/note.md", "knowledge_node_123")

# Retrieve mapping
node_id = tracker.get_knowledge_node_id("/path/to/note.md")

# Remove mapping
tracker.remove_note_mapping("/path/to/note.md")
```

### Cache Management via API

```bash
# Get cache statistics
curl http://localhost:8000/cache/stats

# Clear cache (dangerous!)
curl -X POST http://localhost:8000/cache/clear?confirm=true

# Rebuild cache
curl -X POST http://localhost:8000/cache/rebuild
```

### Agent Tools

```python
# The agent automatically uses caching
response = await agent.process_message("Process this content: Machine learning basics")
# If content was processed before, it uses cached results

# Manual cache operations
await agent.process_message("Get cache statistics")
await agent.process_message("Rebuild the cache")
```

## Cache Files

### Hash Cache (`knowledge_base/hash_cache.json`)

```json
{
  "content_id": {
    "hash": "sha256_hash_value",
    "updated_at": "2025-07-12T16:45:00.000000",
    "metadata": {
      "title": "Content Title",
      "category": "Ideas to Develop"
    }
  }
}
```

### Note Mapping (`knowledge_base/note_mapping.json`)

```json
{
  "/path/to/note.md": "knowledge_node_uuid",
  "/another/note.md": "another_node_uuid"
}
```

## Performance Metrics

### Test Results

- **Average Uncached Processing**: 12.51 seconds
- **Average Cached Processing**: 8.75 seconds
- **Performance Improvement**: 30.1%
- **Cache Hit Rate**: High for repeated content

### Cache Statistics

```json
{
  "total_cached_items": 15,
  "total_mapped_notes": 8,
  "cache_hit_rate_percent": 45.2,
  "memory_efficiency": {
    "cached_items_vs_notes_ratio": 1.87,
    "mapping_coverage_percent": 100.0
  }
}
```

## Best Practices

### 1. Regular Cache Maintenance

- Monitor cache statistics periodically
- Clean up stale entries automatically
- Rebuild cache after major system changes

### 2. Content Management

- Use meaningful content identifiers
- Include relevant metadata in hash tracking
- Consider content significance for caching decisions

### 3. Performance Optimization

- Let the system handle caching automatically
- Use cache statistics to optimize workflows
- Monitor performance improvements

### 4. Troubleshooting

- Check cache files if experiencing issues
- Use rebuild cache for corrupted data
- Monitor logs for hash collision warnings

## Security Considerations

### Hash Integrity

- **SHA-256**: Cryptographically secure hashing
- **Collision Resistance**: Extremely low probability of hash collisions
- **Content Verification**: Ensures data integrity

### File Security

- **Local Storage**: Cache files stored locally
- **No Sensitive Data**: Hashes don't contain original content
- **Cleanup Capability**: Can clear cache completely if needed

## API Endpoints

### GET `/cache/stats`

Returns detailed cache statistics and performance metrics.

### POST `/cache/clear?confirm=true`

Clears all cached data. Requires explicit confirmation.

### POST `/cache/rebuild`

Rebuilds the entire cache by reprocessing all content.

## Monitoring and Debugging

### Cache Hit Tracking

The system automatically tracks:

- Cache hit rates
- Performance improvements
- Memory usage efficiency
- Stale entry detection

### Log Messages

- `⚡ Using cached content processing for hash {hash}...`
- `🔄 Content changed for {path}, updating knowledge node`
- `🔗 Mapped note {path} to knowledge node {id}`
- `💾 Cache stats: {items} items, {mappings} mappings`

### Error Handling

- Graceful degradation when cache files are corrupted
- Automatic fallback to non-cached operations
- Comprehensive error logging

## Future Enhancements

### Planned Features

1. **Distributed Caching**: Support for shared cache across instances
2. **Cache Compression**: Reduce storage requirements
3. **Smart Expiration**: Time-based cache invalidation
4. **Advanced Analytics**: Detailed performance metrics

### Optimization Opportunities

1. **Memory Caching**: In-memory cache for frequently accessed items
2. **Incremental Updates**: Partial content change detection
3. **Batch Operations**: Bulk cache operations for efficiency

## Conclusion

The hash-based caching system provides significant performance improvements while maintaining data integrity and enabling intelligent content management. It's designed to be transparent to users while providing powerful optimization capabilities for the knowledge management agent.

For support or questions, refer to the test results in `test_hash_system.py` or examine the implementation in the `knowledge/hash_utils.py` module.
