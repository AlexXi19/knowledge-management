# Notes-Focused Knowledge Management System

A smart knowledge management system that **creates and manages actual note files** while using AI to intelligently organize and connect your thoughts.

## 🎯 Core Philosophy

This system treats **notes as the primary artifact** - not just the knowledge graph. The AI agent:

1. **Creates actual note files** in organized directories
2. **Updates existing notes** when content is related
3. **Uses knowledge graph** to find connections between notes
4. **Provides semantic search** across all your notes
5. **Supports both fresh starts** and mounting existing note collections

## 🗂️ How It Works

### Note Creation & Organization

When you send a message to the system:

1. **Content Analysis**: Extracts key information, titles, and tags
2. **Intelligent Decision**: Decides whether to create a new note or update existing one
3. **Smart Categorization**: Places notes in appropriate folders
4. **Semantic Indexing**: Adds to knowledge graph for connections
5. **Related Notes**: Shows connections to existing content

### Directory Structure

```
notes/
├── ideas/                 # Ideas to Develop
│   ├── README.md
│   └── my-app-idea.md
├── personal/              # Personal reflections
│   ├── README.md
│   └── thoughts-on-life.md
├── research/              # Research content
│   ├── README.md
│   └── ai-paper-notes.md
├── reading-list/          # Links and articles
│   ├── README.md
│   └── interesting-articles.md
├── projects/              # Project-related
│   ├── README.md
│   └── project-planning.md
├── learning/              # Educational content
│   ├── README.md
│   └── course-notes.md
└── quick-notes/           # Quick captures
    ├── README.md
    └── daily-thoughts.md
```

### Note Format

Each note uses markdown with frontmatter:

```markdown
---
title: My App Idea
category: Ideas to Develop
tags: [app, productivity, notes]
created: 2024-01-15T10:30:00
updated: 2024-01-15T10:30:00
---

# My App Idea

This is my idea for a knowledge management app that automatically organizes thoughts.

## Key Features

- Automatic categorization
- Smart note linking
- Semantic search

## Update - 2024-01-15 14:30

Added more thoughts about the user interface...
```

## 🚀 Getting Started

### Option 1: Fresh Start

1. **Start the backend**:

   ```bash
   cd backend
   uv run python run.py
   ```

2. **The system will create**:
   - `notes/` directory with 7 categories
   - README files for each category
   - Empty structure ready for your content

### Option 2: Mount Existing Notes

1. **Set your notes directory**:

   ```bash
   # In backend/.env
   NOTES_DIRECTORY=/path/to/your/existing/notes
   ```

2. **Start the backend**:

   ```bash
   cd backend
   uv run python run.py
   ```

3. **The system will**:
   - Scan your existing notes
   - Parse frontmatter and content
   - Build knowledge graph from existing content
   - Organize notes by detected categories
   - Ready to extend and connect your content

## 💬 Using the System

### Chat Interface

Send messages to create and manage notes:

```bash
# Create a new note
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have an idea for a productivity app that uses AI to organize tasks"}'

# Response shows what happened
{
  "response": "📝 Created new note: 'Note from 2024-01-15 10:30'\n\n📁 Categorized as \"Ideas to Develop\"\n\n🏷️ Tagged with: app, productivity, ai",
  "categories": ["Ideas to Develop", "Personal"],
  "knowledge_updates": [...],
  "suggested_actions": ["Add more details to this note", "Create connections to related topics"]
}
```

### Example Interactions

**💡 Idea Development**

```
Input: "Building a better way to capture and organize thoughts while walking"
Output: Creates new note in Ideas to Develop folder with structured content
```

**🔗 Link Saving**

```
Input: "https://example.com/productivity-article - Great insights on focus techniques"
Output: Creates note in Reading List, extracts web content, adds summary
```

**📚 Research Notes**

```
Input: "Paper on transformer architectures shows attention mechanisms are key to understanding context"
Output: Creates note in Research folder, connects to related AI/ML content
```

**✏️ Note Updates**

```
Input: "More thoughts on the walking app - could integrate with voice recording"
Output: Updates existing related note instead of creating new one
```

## 🔧 API Endpoints

### Notes Management

- `GET /notes` - Get all notes
- `GET /notes/structure` - Get directory structure
- `GET /notes/search?query=...` - Search notes
- `GET /notes/{category}` - Get notes by category
- `GET /config/notes` - Get notes configuration

### Chat & Processing

- `POST /chat` - Process message and manage notes
- `POST /chat/stream` - Stream real-time processing
- `GET /knowledge/search` - Semantic search across notes

## 🧠 AI Features

### Smart Categorization

The system uses both rule-based and AI-powered categorization:

- **URLs** → Reading List
- **Research terms** → Research
- **Personal reflections** → Personal
- **Project mentions** → Projects
- **Learning content** → Learning
- **Quick thoughts** → Quick Notes
- **Incomplete ideas** → Ideas to Develop

### Content Processing

- **Title extraction** from content
- **Tag generation** based on content
- **Link extraction** and web content parsing
- **Duplicate detection** and smart merging
- **Related content** discovery

### Semantic Search

- **Embedding-based search** across all notes
- **Related note suggestions** when creating content
- **Cross-category connections** discovery
- **Content similarity** detection

## 📊 Embedding Options

Choose your embedding provider for semantic search:

### 🏠 Local Embeddings (Default)

```env
EMBEDDING_PROVIDER=sentence_transformer
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

- **Cost**: Free
- **Privacy**: Completely local
- **Performance**: Good for most use cases

### 🚀 OpenAI Embeddings

```env
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your_api_key_here
```

- **Cost**: ~$0.0001 per 1k tokens
- **Privacy**: Data sent to OpenAI
- **Performance**: Superior semantic understanding

## 🛠️ Development & Customization

### Adding Custom Categories

Edit `backend/knowledge/notes_manager.py`:

```python
self.categories = {
    "Ideas to Develop": "ideas",
    "Personal": "personal",
    "Research": "research",
    "Reading List": "reading-list",
    "Projects": "projects",
    "Learning": "learning",
    "Quick Notes": "quick-notes",
    "Custom Category": "custom"  # Add your own
}
```

### Custom Content Processors

Extend `backend/knowledge/content_processor.py` for specific formats:

```python
async def process_custom_format(self, content: str) -> Dict[str, Any]:
    # Your custom processing logic
    return {
        "title": "Extracted Title",
        "text": "Processed content",
        "tags": ["custom", "format"],
        "content_type": "custom"
    }
```

## 🧪 Testing

Test the complete system:

```bash
# Test notes system
cd backend
uv run python test_notes_system.py

# Test OpenAI embeddings (requires API key)
uv run python test_openai_embeddings.py

# Test embedding service
uv run python -c "from knowledge.embedding_service import test_embedding_service; import asyncio; asyncio.run(test_embedding_service())"
```

## 📁 File Structure

```
backend/
├── knowledge/
│   ├── notes_manager.py      # Core notes management
│   ├── embedding_service.py  # Flexible embedding providers
│   ├── knowledge_graph.py    # Graph + semantic search
│   ├── categorizer.py        # Smart categorization
│   └── content_processor.py  # Content extraction
├── agent/
│   └── knowledge_agent.py    # Main orchestrator
├── models/
│   └── chat_models.py        # Data models
├── main.py                   # FastAPI application
├── run.py                    # Startup script
└── notes/                    # Your notes directory
    ├── ideas/
    ├── personal/
    ├── research/
    ├── reading-list/
    ├── projects/
    ├── learning/
    └── quick-notes/
```

## 🔄 Workflow Examples

### Daily Knowledge Capture

1. **Morning Thoughts**: "Thinking about how to improve my morning routine"

   - Creates note in Personal category
   - Tags with: routine, productivity, morning

2. **Article Discovery**: "https://example.com/productivity-tips"

   - Creates note in Reading List
   - Extracts content and summary
   - Connects to existing productivity notes

3. **Project Ideas**: "App idea: voice-to-text for quick note capture"

   - Creates note in Ideas to Develop
   - Links to related app development notes
   - Suggests next steps

4. **Research Learning**: "Study on attention mechanisms in transformers"
   - Creates note in Research
   - Connects to existing AI/ML content
   - Builds knowledge graph connections

### Existing Notes Integration

If you have existing notes:

1. **Point to your directory**: Set `NOTES_DIRECTORY` in `.env`
2. **Start system**: It scans and indexes existing content
3. **Automatic organization**: Categorizes by folder structure
4. **Semantic connections**: Builds graph from existing content
5. **Enhanced functionality**: Adds AI-powered extensions

## 🌟 Key Benefits

### For New Users

- **Instant organization** with smart categories
- **No setup needed** - just start writing
- **AI-powered connections** between ideas
- **Searchable knowledge base** from day one

### For Existing Note-Takers

- **Preserves existing structure** while adding AI
- **Enhances current workflow** without disruption
- **Discovers hidden connections** in existing content
- **Extends notes** with smart suggestions

### For Teams

- **Shared knowledge base** with consistent structure
- **Collaborative note-taking** with AI assistance
- **Knowledge discovery** across team members
- **Standardized organization** with flexibility

## 🎯 Next Steps

1. **Start with backend**: `cd backend && uv run python run.py`
2. **Test with chat**: Send messages to create notes
3. **Explore structure**: Check `notes/` directory
4. **Customize categories**: Modify for your workflow
5. **Add embeddings**: Upgrade to OpenAI for better search
6. **Integrate frontend**: Connect React app for full UI

---

_This system transforms your knowledge management from passive storage to active, intelligent organization. Your notes become a living, connected knowledge base that grows smarter with every addition._
