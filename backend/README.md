# Knowledge Management Backend

A powerful AI-driven knowledge management system powered by **smolagents** with comprehensive support for multiple LLM providers including **OpenRouter** (access to all models), **Anthropic Claude Sonnet**, OpenAI GPT, and HuggingFace models.

## 🚀 Supported AI Models

### 🌟 **OpenRouter** (Highest Priority - Recommended)

- **Access to 200+ AI Models** - Claude, GPT, Llama, Gemini, and more
- **Unified API** - Single interface for all major AI providers
- **Competitive Pricing** - Often 50%+ cheaper than direct APIs
- **Model Switching** - Easy to test and compare different models
- **Usage Tracking** - Built-in cost monitoring and analytics

### 🎯 **Anthropic Claude Sonnet**

- **Claude 3.5 Sonnet** - Latest and most capable model
- **Claude 3 Sonnet** - High-quality reasoning and analysis
- **Optimized for Knowledge Management** - Excellent categorization and analysis

### 🔧 **OpenAI GPT Models**

- **GPT-4o-mini** - Fast and cost-effective
- **GPT-4** - High-quality reasoning
- **GPT-3.5-turbo** - Balanced performance

### 🤗 **HuggingFace Models**

- **Llama 3.3 70B** - Open-source powerhouse
- **DialoGPT** - Conversational AI
- **Any HuggingFace model** - Flexible integration

## 🚀 Quick Start

### 1. Environment Setup

Choose your preferred AI provider and set the corresponding API key:

```bash
# Option 1: OpenRouter (Recommended - Access to ALL models)
export OPENROUTER_API_KEY=your_openrouter_api_key
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Optional, this is the default

# Option 2: Anthropic Claude Sonnet
export ANTHROPIC_API_KEY=your_anthropic_api_key
export CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Optional, this is the default

# Option 3: OpenAI GPT
export OPENAI_API_KEY=your_openai_api_key
export OPENAI_MODEL=gpt-4o-mini  # Optional, this is the default

# Option 4: HuggingFace (Free tier available)
export HF_TOKEN=your_huggingface_token

# Optional: Embedding configuration
export EMBEDDING_PROVIDER=openai  # or sentence_transformer (default)
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # if using OpenAI embeddings
```

### 2. Installation

```bash
# Install dependencies
uv add smolagents[toolkit,litellm] chromadb

# Run the system
uv run python run.py
```

### 3. Access the System

- **API Server**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Cache Management**: http://localhost:8000/cache/stats

## 🧠 Model Selection Priority

The system automatically selects the best available model in this order:

1. **OpenRouter** (if `OPENROUTER_API_KEY` is set) - **HIGHEST PRIORITY**
2. **Anthropic Claude** (if `ANTHROPIC_API_KEY` is set)
3. **HuggingFace Models** (if `HF_TOKEN` is set)
4. **OpenAI GPT** (if `OPENAI_API_KEY` is set)
5. **Free HuggingFace** (fallback, rate-limited)

## 💎 Why OpenRouter? (Recommended)

### 🎯 **Access to Every Major AI Model**

- **Claude 3.5 Sonnet** - Anthropic's latest model
- **GPT-4o** - OpenAI's most advanced model
- **Llama 3.1 405B** - Meta's largest open model
- **Gemini Pro** - Google's competitive model
- **200+ Models** - Including specialized and fine-tuned variants

### 💰 **Cost Advantages**

- **50%+ Savings** - Often half the cost of direct APIs
- **Pay-per-use** - No monthly minimums or commitments
- **Cost Tracking** - Built-in usage analytics and monitoring
- **Free Credits** - Get started with free tier

### 🔧 **Developer Experience**

- **Unified API** - One interface for all models
- **Model Switching** - Change models instantly via environment variable
- **Rate Limiting** - Built-in rate limiting and queue management
- **Reliability** - High uptime and automatic failover

### 📊 **Model Comparison**

- **A/B Testing** - Easy to compare model performance
- **Model Rankings** - See community model ratings
- **Performance Metrics** - Speed and quality comparisons
- **Model Discovery** - Find the best model for your use case

## 📋 Available OpenRouter Models

### **Popular Models for Knowledge Management**

```bash
# Claude Models (Excellent for analysis and reasoning)
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
export OPENROUTER_MODEL=anthropic/claude-3-haiku        # Faster, cheaper

# GPT Models (Great for general tasks)
export OPENROUTER_MODEL=openai/gpt-4o
export OPENROUTER_MODEL=openai/gpt-4o-mini             # Faster, cheaper

# Llama Models (Open source, great value)
export OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
export OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct  # Faster, cheaper

# Gemini Models (Google's latest)
export OPENROUTER_MODEL=google/gemini-flash-1.5
export OPENROUTER_MODEL=google/gemini-pro-1.5

# Specialized Models
export OPENROUTER_MODEL=perplexity/llama-3.1-sonar-large-128k-online  # Web search
export OPENROUTER_MODEL=microsoft/wizardlm-2-8x22b     # Reasoning
```

## 📋 Features

### 🔍 **Intelligent Knowledge Management**

- **Automated Content Categorization** using AI
- **Smart Note Creation and Updates**
- **Semantic Search** across your knowledge base
- **Knowledge Graph** visualization and relationships

### ⚡ **Performance Optimization**

- **Hash-based Caching** - 30%+ performance improvement
- **Content Change Detection** - Only processes modified content
- **Note-to-Knowledge Mapping** - Efficient relationship tracking
- **Intelligent Deduplication** - Prevents redundant processing

### 🛠 **Agent Capabilities**

- **12 Specialized Tools** for knowledge management
- **Multi-step Reasoning** with smolagents
- **Real-time Streaming** responses
- **Cache Management** and statistics

## 🧪 Testing

### Test OpenRouter Integration

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY=your_key_here

# Run OpenRouter-specific tests
uv run python test_openrouter_integration.py
```

### Test Anthropic Claude Integration

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY=your_key_here

# Run Claude-specific tests
uv run python test_anthropic_integration.py
```

### Test Hash Caching System

```bash
# Test the performance optimization system
uv run python test_hash_system.py
```

### Test Complete System

```bash
# Test all integrations
uv run python test_smolagents_integration.py
```

## 📊 API Endpoints

### Core Endpoints

- `POST /chat` - Chat with the AI agent (non-blocking)
- `POST /chat/async` - Start background chat processing
- `GET /chat/task/{task_id}` - Check background task status
- `POST /chat/stream` - Real-time streaming chat
- `GET /notes` - Get all notes
- `GET /knowledge/graph` - Get knowledge graph data
- `GET /search` - Search knowledge base

### Agent Management

- `GET /agent/info` - Agent information
- `GET /agent/logs` - Agent execution logs
- `POST /agent/reset` - Reset agent memory

### Task Management

- `GET /tasks` - List active background tasks
- `DELETE /tasks/{task_id}` - Cancel running task

### Cache Management

- `GET /cache/stats` - Cache statistics and performance metrics
- `POST /cache/clear` - Clear cache (requires confirmation)
- `POST /cache/rebuild` - Rebuild entire cache

### Concurrency Features

The server now supports:

- **AsyncIO Concurrency**: Single worker with asyncio event loop (Node.js-style)
- **Non-blocking requests**: Long-running chat operations don't block other endpoints
- **Background processing**: Use `/chat/async` for non-blocking chat with polling
- **Streaming**: `/chat/stream` provides live updates without blocking
- **Shared state**: Knowledge graph and caches efficiently shared in single process

This approach is similar to Node.js - single-threaded with an event loop for concurrent I/O operations, making it perfect for the file system and API operations that dominate this knowledge management system.

See `CONCURRENCY_IMPROVEMENTS.md` for detailed technical information.

## 🔧 Configuration

### Environment Variables

#### **AI Model Configuration (Priority Order)**

```bash
# OpenRouter (Priority 1 - Recommended)
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Optional

# Anthropic Claude (Priority 2)
ANTHROPIC_API_KEY=your_anthropic_key
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Optional

# HuggingFace (Priority 3)
HF_TOKEN=your_hf_token

# OpenAI GPT (Priority 4)
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini  # Optional
```

#### **System Configuration**

```bash
# Storage paths
KNOWLEDGE_BASE_PATH=./knowledge_base  # Vector database storage
NOTES_DIRECTORY=./notes              # Notes file storage

# Embedding configuration
EMBEDDING_PROVIDER=sentence_transformer  # or openai
EMBEDDING_MODEL=all-MiniLM-L6-v2        # For sentence transformers
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # For OpenAI
```

## 🏗 Architecture

### Core Components

1. **KnowledgeAgent** - smolagents-powered AI agent
2. **HashTracker** - Performance optimization system
3. **NotesManager** - File-based note management
4. **KnowledgeGraph** - Semantic relationships and vector search
5. **ContentProcessor** - Intelligent content analysis

### Data Flow

```
User Input → Agent (OpenRouter/Claude/GPT/Llama) → Tools → Knowledge Processing → Response
                ↓
Cache Check → Hash Comparison → Process if Changed → Update Cache
                ↓
Notes Storage ← Knowledge Graph ← Embeddings ← Content Analysis
```

## 🚀 Getting Started with OpenRouter

1. **Get an OpenRouter API Key** from [openrouter.ai](https://openrouter.ai)
2. **Set the environment variable**: `export OPENROUTER_API_KEY=your_key`
3. **Choose your model**: `export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet`
4. **Run the system**: `uv run python run.py`
5. **Verify OpenRouter is active**: Check the startup logs for "✅ Using OpenRouter model"

## 📚 Example Usage

### Chat with OpenRouter Models

```bash
# Using Claude via OpenRouter
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze this research paper about machine learning transformers"}'
```

### Switch Models Dynamically

```bash
# Switch to GPT-4o
export OPENROUTER_MODEL=openai/gpt-4o
uv run python run.py

# Switch to Llama
export OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
uv run python run.py
```

### Get Cache Statistics

```bash
curl http://localhost:8000/cache/stats
```

### Search Knowledge Base

```bash
curl "http://localhost:8000/search?query=machine%20learning&limit=5"
```

## 🔍 Troubleshooting

### OpenRouter Not Working?

1. Check your `OPENROUTER_API_KEY` is set correctly
2. Verify the model name in `OPENROUTER_MODEL` (default: anthropic/claude-3.5-sonnet)
3. Run `uv run python test_openrouter_integration.py` for diagnostics
4. Check [openrouter.ai/models](https://openrouter.ai/models) for available models

### Claude Not Working?

1. Check your `ANTHROPIC_API_KEY` is set correctly
2. Verify the model name in `CLAUDE_MODEL` (default: claude-3-5-sonnet-20241022)
3. Run `uv run python test_anthropic_integration.py` for diagnostics

### Performance Issues?

1. Check cache statistics: `curl http://localhost:8000/cache/stats`
2. Rebuild cache if needed: `curl -X POST http://localhost:8000/cache/rebuild`
3. Monitor hash system with `uv run python test_hash_system.py`

### Model Selection Issues?

The system will automatically fallback to other models if OpenRouter isn't available. Check the startup logs to see which model is being used.

## 📄 License

MIT License - Use freely for personal and commercial projects.

## 🤝 Support

- **Documentation**: See the `/docs` endpoints
- **Issues**: Check the test scripts for diagnostics
- **Performance**: Use cache management endpoints for optimization

---

**Powered by smolagents 🤖 | OpenRouter Integration 🌟 | Optimized for Claude Sonnet 🎯 | Built for Knowledge Workers 📚**
