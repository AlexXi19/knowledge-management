# Knowledge Management System - Testing

This directory contains all test files for the knowledge management system, organized by functionality.

## Quick Start

```bash
# From the backend directory, run:
cd backend

# Quick test (recommended)
uv run python testing/simple_agent_chat.py

# Comprehensive agent test
uv run python testing/test_agent_conversations.py

# Architecture validation
uv run python testing/test_smolagents_best_practices.py
```

## Test Categories

### 🚀 **Agent & Conversation Tests**

- `simple_agent_chat.py` - Quick agent functionality testing
- `test_agent_conversations.py` - Comprehensive conversation testing
- `test_smolagents_best_practices.py` - Smolagents architecture validation

### 🔌 **API Integration Tests**

- `test_openrouter_integration.py` - OpenRouter API testing
- `test_anthropic_integration.py` - Anthropic Claude API testing
- `test_smolagents_integration.py` - Smolagents integration testing

### 🗂️ **System Tests**

- `test_hash_system.py` - Hash-based caching system
- `test_notes_system.py` - Notes management system
- `test_openai_embeddings.py` - OpenAI embeddings testing

### 🌐 **API & Endpoint Tests**

- `test_server_request.py` - Server request testing
- `test_chat_endpoint.py` - Chat endpoint testing
- `test_setup.py` - Basic setup testing

## Documentation

See `TESTING_GUIDE.md` for detailed usage instructions, configuration, and troubleshooting.

## Architecture Validation

Even without API keys, the tests validate:

- ✅ Smolagents best practices (ToolCallingAgent + CodeAgent)
- ✅ Complexity detection and intelligent routing
- ✅ Fallback mechanisms and error handling
- ✅ Hash-based caching and performance optimization
- ✅ Memory management and environment cleanup

## Configuration

Configure API keys for full functionality:

```bash
export OPENROUTER_API_KEY="your-key"     # Recommended
export ANTHROPIC_API_KEY="your-key"      # Alternative
export OPENAI_API_KEY="your-key"         # Alternative
```

The architecture works perfectly - it just needs API keys to unlock full AI capabilities! 🚀
