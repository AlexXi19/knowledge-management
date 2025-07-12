# Knowledge Management Tool Setup Guide

This guide will help you set up and run your complete knowledge management tool with a React frontend and intelligent backend.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- Git
- uv (Python package manager)

## Quick Start

### 1. Set up the Backend

First, install uv (if you don't have it):

```bash
pip install uv
# or use: curl -LsSf https://astral.sh/uv/install.sh | sh
```

Navigate to the backend directory:

```bash
cd backend
```

Install Python dependencies with uv:

```bash
uv sync
```

The backend comes with a basic `.env` file. You can configure it for different needs:

### Option 1: Local Embeddings (Default - Free)

```bash
# Uses sentence transformers locally (no API key needed)
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Option 2: OpenAI Embeddings (Higher Quality)

```bash
# Edit backend/.env
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_openai_api_key_here
```

### Test Your Embedding Setup

```bash
# Test current configuration
cd backend
uv run python -c "from knowledge.embedding_service import test_embedding_service; import asyncio; asyncio.run(test_embedding_service())"

# Test OpenAI embeddings (requires API key)
uv run python test_openai_embeddings.py
```

Start the backend server:

```bash
uv run python run.py
```

The backend will be available at `http://localhost:8000`

### 2. Set up the Frontend

In a new terminal, navigate to the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
bun install
```

Start the frontend development server:

```bash
bun dev
```

The frontend will be available at `http://localhost:5173`

## Testing the System

1. Open your browser and go to `http://localhost:5173`
2. Try these example messages:

### Personal Thought:

```
Creating your own future vs. waiting for it to happen
```

### Link:

```
https://example.com/interesting-article
```

### Research Note:

```
Research shows that active goal-setting increases success rates by 42%. Key methodology: longitudinal study over 5 years with 1000 participants.
```

### Quick Note:

```
Remember to backup database daily
```

## What Happens?

The system will:

1. **Analyze** your input using content processing
2. **Categorize** it into appropriate buckets (Ideas to Develop, Personal, Reading List, etc.)
3. **Generate semantic embeddings** using your chosen provider (local or OpenAI)
4. **Store** it in the knowledge graph with semantic embeddings
5. **Connect** it to related content you've previously added using semantic similarity
6. **Respond** with what it did and suggest next actions

## Categories

Your content will be automatically organized into:

- **Ideas to Develop** - Incomplete thoughts that need expansion
- **Personal** - Personal reflections and experiences
- **Research** - Academic or professional research content
- **Reading List** - Links and articles to read later
- **Projects** - Project-related content
- **Learning** - Educational content and notes
- **Quick Notes** - Brief thoughts and reminders

## Advanced Features

### Knowledge Graph

Access the knowledge graph at: `http://localhost:8000/knowledge/graph`

### Search

Search your knowledge base at: `http://localhost:8000/knowledge/search?query=your_search_term`

### Categories

View all categories at: `http://localhost:8000/knowledge/categories`

## File Structure

```
knowledge-management/
├── frontend/          # React frontend
│   ├── src/
│   │   ├── App.tsx   # Main chat interface
│   │   └── ...
│   └── package.json
├── backend/          # Python backend
│   ├── main.py       # FastAPI server
│   ├── run.py        # Startup script
│   ├── pyproject.toml # uv package configuration
│   ├── agent/        # Knowledge agent
│   ├── knowledge/    # Knowledge graph & processing
│   ├── models/       # Data models
│   └── knowledge_base/ # Persistent storage (created automatically)
└── setup.md         # This file
```

## Troubleshooting

### Backend Issues

**Import errors:**

```bash
uv sync
```

**Port already in use:**

```bash
# Change port in backend/run.py or backend/main.py
uv run uvicorn main:app --port 8001
```

**ChromaDB issues:**

```bash
# Delete and recreate the knowledge base
rm -rf backend/knowledge_base
uv run python run.py
```

### Frontend Issues

**Connection refused:**

- Make sure the backend is running on `http://localhost:8000`
- Check the browser console for errors

**Build errors:**

```bash
# Clear cache and reinstall
rm -rf node_modules
bun install
```

## Embedding Options

The system supports two embedding providers for semantic search:

### 🏠 Sentence Transformers (Default)

- **Cost**: Free
- **Performance**: Good for most use cases
- **Privacy**: Runs entirely locally
- **Setup**: No API key required
- **Model**: all-MiniLM-L6-v2 (384 dimensions)

### 🚀 OpenAI Embeddings

- **Cost**: ~$0.0001 per 1k tokens (very affordable)
- **Performance**: Superior quality and semantic understanding
- **Privacy**: Data sent to OpenAI (consider for sensitive content)
- **Setup**: Requires OpenAI API key
- **Models**:
  - `text-embedding-3-small` (1536 dimensions) - Best cost/performance
  - `text-embedding-3-large` (3072 dimensions) - Highest quality

### When to Use Each:

- **Start with Sentence Transformers** for testing and development
- **Upgrade to OpenAI** for production or when you need superior semantic understanding
- **OpenAI embeddings** are particularly good at understanding context and relationships

## Package Management with UV

This project now uses `uv` for Python package management, which offers several benefits:

### Why UV?

- **🚀 Fast**: 10-100x faster than pip
- **🔒 Secure**: Built-in dependency resolution and lock files
- **🧹 Clean**: Automatic virtual environment management
- **📦 Modern**: Uses `pyproject.toml` standard
- **🔄 Reliable**: Reproducible builds with `uv.lock`

### UV Commands

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Run a script
uv run python script.py

# Install development dependencies
uv sync --dev

# Update dependencies
uv sync --upgrade
```

## Customization

### Add Custom Categories

Edit `backend/knowledge/categorizer.py` to add your own categories:

```python
"My Custom Category": {
    "keywords": ["custom", "specific", "keywords"],
    "patterns": [r"\bcustom_pattern\b"],
    "description": "Description of what this category contains"
}
```

### Modify the Agent

Edit `backend/agent/knowledge_agent.py` to customize the agent behavior, add new tools, or change the response format.

### Change the UI

The frontend uses Tailwind CSS and shadcn/ui components. Edit `frontend/src/App.tsx` to customize the interface.

## Production Deployment

For production deployment:

1. **Backend**: Use a proper WSGI server like Gunicorn
2. **Frontend**: Build and serve with a web server like Nginx
3. **Database**: Consider using a proper database instead of local files
4. **Security**: Add authentication and proper CORS configuration

## Support

If you encounter issues:

1. Check the console logs in both frontend and backend
2. Verify all dependencies are installed with `uv sync`
3. Ensure both servers are running on the correct ports
4. Check the API documentation at `http://localhost:8000/docs`

## Next Steps

Once you have the system running:

1. **Add your existing notes** to the `backend/notes/` directory
2. **Customize categories** to match your workflow
3. **Set up regular backups** of your knowledge base
4. **Explore the API** to build custom integrations
5. **Upgrade to Python 3.10+** to use smolagents for enhanced AI capabilities

## Future Enhancements

When you upgrade to Python 3.10+, you can add:

- **smolagents integration** for advanced AI agent capabilities
- **Multi-agent workflows** for complex knowledge processing
- **Custom tools** for specialized knowledge management tasks

Happy knowledge managing! 🚀
