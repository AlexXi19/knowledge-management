# Knowledge Management Backend

A smart knowledge management system that intelligently categorizes and organizes your thoughts, links, and research content.

## Features

- 🤖 **AI-Powered Agent**: Intelligently processes and categorizes content
- 🕸️ **Knowledge Graph**: NetworkX-based graph structure for connecting related concepts
- 🔍 **Semantic Search**: ChromaDB integration with multiple embedding options
- 📝 **Smart Categorization**: Automatically categorizes content into relevant buckets
- 🌐 **Web Content Extraction**: Automatically extracts content from URLs
- 📊 **Real-time Processing**: Streaming responses for better user experience
- 🧠 **Flexible Embeddings**: Support for both OpenAI and local sentence-transformers

## Categories

The system automatically categorizes content into:

- **Ideas to Develop**: Incomplete thoughts and concepts that need development
- **Personal**: Personal reflections and experiences
- **Research**: Academic or professional research content
- **Reading List**: Links and articles to read later
- **Projects**: Project-related content
- **Learning**: Educational content and notes
- **Quick Notes**: Brief thoughts and reminders

## Installation

1. **Install uv and dependencies**:

   ```bash
   pip install uv
   uv sync
   ```

2. **Set up environment variables**:
   Create a `.env` file with the following variables:

   ```bash
   # Basic configuration
   KNOWLEDGE_BASE_PATH=./knowledge_base
   NOTES_DIRECTORY=./notes

   # Embedding configuration (choose one)
   # Option 1: Local embeddings (free, runs locally)
   EMBEDDING_PROVIDER=sentence_transformer
   EMBEDDING_MODEL=all-MiniLM-L6-v2

   # Option 2: OpenAI embeddings (requires API key, higher quality)
   # EMBEDDING_PROVIDER=openai
   # OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   # OPENAI_API_KEY=your_openai_api_key_here

   # Optional: For AI-powered categorization
   # OPENAI_API_KEY=your_openai_api_key_here
   ```

3. **Run the server**:

   ```bash
   uv run python run.py
   ```

   Or manually:

   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Embedding Providers

The system supports two embedding providers for semantic search:

### 🏠 Sentence Transformers (Default)

- **Cost**: Free
- **Performance**: Good for most use cases
- **Privacy**: Runs entirely locally
- **Setup**: No API key required
- **Models**: `all-MiniLM-L6-v2` (384 dimensions), `all-mpnet-base-v2` (768 dimensions)

```bash
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 🚀 OpenAI Embeddings

- **Cost**: ~$0.0001 per 1k tokens (very affordable)
- **Performance**: Superior quality and semantic understanding
- **Privacy**: Data sent to OpenAI
- **Setup**: Requires OpenAI API key
- **Models**:
  - `text-embedding-3-small` (1536 dimensions) - Best cost/performance
  - `text-embedding-3-large` (3072 dimensions) - Highest quality

```bash
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_api_key_here
```

### Testing Embeddings

Test your embedding setup:

```bash
# Test current configuration
uv run python -c "from knowledge.embedding_service import test_embedding_service; import asyncio; asyncio.run(test_embedding_service())"

# Test OpenAI embeddings (requires API key)
uv run python test_openai_embeddings.py
```

## API Endpoints

### Chat Endpoints

- **POST /chat**: Process a message and get categorized response
- **POST /chat/stream**: Stream processing updates in real-time

### Knowledge Management

- **GET /knowledge/graph**: Get the complete knowledge graph
- **GET /knowledge/categories**: Get all available categories
- **GET /knowledge/search**: Search the knowledge base

### Health Check

- **GET /health**: Server health check

## Example Usage

### Send a thought

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Creating your own future vs. waiting for it to happen"}'
```

Response:

```json
{
  "response": "Added to \"Ideas to Develop\" and tagged with Personal. This looks like a quick thought - great for future development!",
  "categories": ["Ideas to Develop", "Personal"],
  "knowledge_updates": [
    {
      "action": "added",
      "category": "Ideas to Develop",
      "content": "Creating your own future vs. waiting for it to happen",
      "node_id": "uuid-here"
    }
  ],
  "suggested_actions": ["Expand on this idea", "Find related concepts"]
}
```

### Add a link

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "https://example.com/interesting-article"}'
```

The system will automatically extract the web content and categorize it appropriately.

## Architecture

### Core Components

1. **KnowledgeAgent**: Main agent orchestrating the knowledge management
2. **KnowledgeGraph**: NetworkX-based graph with ChromaDB for semantic search
3. **EmbeddingService**: Flexible embedding provider (OpenAI or Sentence Transformers)
4. **ContentCategorizer**: Rule-based and AI-powered content categorization
5. **ContentProcessor**: Extracts structured information from various content types

### Data Flow

1. User sends message → FastAPI endpoint
2. KnowledgeAgent processes the message
3. ContentProcessor extracts structured information
4. ContentCategorizer determines appropriate categories
5. EmbeddingService generates semantic embeddings
6. KnowledgeGraph stores and links the content
7. Response generated with categorization and suggestions

## Configuration

### Environment Variables

- `EMBEDDING_PROVIDER`: Choose `openai` or `sentence_transformer`
- `OPENAI_API_KEY`: Required for OpenAI embeddings and AI categorization
- `OPENAI_EMBEDDING_MODEL`: OpenAI embedding model to use
- `EMBEDDING_MODEL`: Sentence transformer model to use
- `KNOWLEDGE_BASE_PATH`: Directory for persistent storage (default: ./knowledge_base)
- `NOTES_DIRECTORY`: Directory to mount your existing notes (default: ./notes)

### Switching Embedding Providers

To switch from sentence transformers to OpenAI embeddings:

1. Update your `.env` file:

   ```bash
   EMBEDDING_PROVIDER=openai
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   OPENAI_API_KEY=your_api_key_here
   ```

2. Restart the server:

   ```bash
   uv run python run.py
   ```

3. The system will create a new collection with OpenAI embeddings
4. Existing data remains accessible; new content uses OpenAI embeddings

### Customization

You can extend the system by:

1. **Adding custom categories** via the ContentCategorizer
2. **Creating custom embedding providers** by extending the EmbeddingProvider class
3. **Implementing custom content processors** for specific formats
4. **Adding new API endpoints** for specific use cases

## Development

### Project Structure

```
backend/
├── main.py                 # FastAPI application
├── run.py                  # Startup script
├── pyproject.toml          # uv package configuration
├── agent/
│   └── knowledge_agent.py  # Main agent implementation
├── knowledge/
│   ├── knowledge_graph.py  # Graph management
│   ├── embedding_service.py # Embedding providers
│   ├── categorizer.py      # Content categorization
│   └── content_processor.py # Content extraction
├── models/
│   └── chat_models.py      # Pydantic models
└── knowledge_base/         # Persistent storage (created automatically)
```

### Running in Development

```bash
# Install in development mode
uv sync --dev

# Run with auto-reload
uv run python run.py

# Or use uvicorn directly
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Integration with Frontend

The backend is designed to work with the React frontend in the `frontend/` directory. The frontend should send requests to:

- `http://localhost:8000/chat` for regular chat
- `http://localhost:8000/chat/stream` for streaming responses

## Troubleshooting

### Common Issues

1. **Import errors**: Run `uv sync` to install all dependencies
2. **ChromaDB issues**: Delete the `knowledge_base/` directory and restart
3. **OpenAI API errors**: Check your API key and ensure you have credits
4. **Port conflicts**: Change the port in `run.py` or `uvicorn` command
5. **Embedding errors**: Verify your embedding provider configuration

### Logs

The system logs important events to stdout. For production, consider using proper logging configuration.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).
