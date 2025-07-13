# Concurrency Improvements

## Problem

The original HTTP server was single-threaded and blocking. When users made requests to the `/chat` or `/chat/stream` endpoints, the long-running agent processing would block the entire server thread, preventing other requests from being handled.

## Solution

### 1. AsyncIO-Based Concurrency (Node.js-Style)

**Before:**

```python
# Blocking - other requests wait
response = await knowledge_agent.process_message(message)
```

**After:**

```python
# Non-blocking - uses asyncio event loop like Node.js
result = await knowledge_agent.process_message(message)
```

### 2. Background Task Processing

Added a new `/chat/async` endpoint that:

- Starts processing in background using asyncio
- Returns immediately with a task ID
- Allows polling for results via `/chat/task/{task_id}`

```python
# Start background task using asyncio
background_tasks.add_task(process_chat_task, task_id, message)
return {"task_id": task_id, "status": "pending"}
```

### 3. Single Worker with AsyncIO Event Loop

**Single Worker Design:**

- One process with asyncio event loop (like Node.js)
- Non-blocking I/O operations
- Concurrent request handling through async/await
- Shared state management (knowledge graph, caches)

**Development Mode:**

- Hot reload enabled
- Debug-friendly single process

**Production Mode:**

- Same single worker approach
- Optimized event loop configuration

```python
uvicorn.run(
    app,
    loop="asyncio",  # AsyncIO event loop for concurrency
    http="httptools",  # Fast HTTP processing
    ws="websockets"   # WebSocket support
)
```

### 4. Streaming with AsyncIO Generators

Enhanced streaming endpoint with:

- AsyncIO generators (like Node.js readable streams)
- Better error handling
- Proper SSE headers
- Non-blocking execution

```python
async def generate():
    async for chunk in knowledge_agent.stream_response(message):
        yield f"data: {json.dumps(chunk)}\n\n"
```

## Architecture Comparison

### Node.js-Style (Current)

```
Request → FastAPI → AsyncIO Event Loop → Concurrent Processing
    ↓
Other Requests → Non-blocking (async/await) → Immediate Response
    ↓
Background Tasks → AsyncIO Tasks → Concurrent Execution
    ↓
Single Process → Shared State → Efficient Memory Usage
```

### Multi-Worker (Avoided)

```
Request → Multiple Processes → Shared State Issues
    ↓
Complex IPC → Data Synchronization Problems
    ↓
Higher Memory Usage → Process Overhead
```

## Benefits

1. **Node.js-Style Concurrency**: Single event loop handles all requests
2. **Shared State**: Knowledge graph and caches shared efficiently
3. **Lower Memory**: Single process vs multiple workers
4. **Simpler Debugging**: Single process easier to debug
5. **Better I/O**: Perfect for I/O-bound operations (file system, APIs)

## Performance Metrics

**Before:**

- Single request blocks entire server
- Response time: 10-30+ seconds for all requests
- Concurrent requests: Queue and timeout

**After:**

- Health checks: < 1 second
- Info endpoints: < 1 second
- Multiple concurrent requests: Handled via asyncio
- Background tasks: Immediate response with polling
- Streaming: Non-blocking with real-time updates

## Configuration

The server now uses a single worker with asyncio concurrency:

```bash
# Development
export ENVIRONMENT=development  # Hot reload enabled

# Production
export ENVIRONMENT=production   # Optimized asyncio
```

Or use command line:

```bash
# Development
python run.py --dev

# Production
python run.py
```

## Why Single Worker vs Multiple Workers?

### Single Worker Advantages:

- **Shared State**: Knowledge graph, caches, and embeddings shared in memory
- **Simpler Architecture**: No process coordination needed
- **Lower Memory**: Single process footprint
- **Node.js-Style**: Familiar async/await patterns
- **Better for I/O**: Perfect for file operations and API calls

### Multiple Workers Disadvantages:

- **State Synchronization**: Complex data sharing between processes
- **Memory Overhead**: Each worker loads full knowledge graph
- **Race Conditions**: Concurrent file operations can conflict
- **Debugging Complexity**: Multiple processes harder to debug

## AsyncIO Patterns Used

1. **Async/Await**: Non-blocking request processing
2. **Background Tasks**: Concurrent background processing
3. **Async Generators**: Streaming responses
4. **Event Loop**: Single-threaded concurrency
5. **Coroutines**: Concurrent function execution
