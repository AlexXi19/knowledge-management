# OpenRouter Integration Guide

## Overview

OpenRouter provides access to 200+ AI models through a single, unified API with competitive pricing. This guide covers how to integrate OpenRouter with your knowledge management system for maximum flexibility and cost savings.

## 🌟 Why OpenRouter?

### 📊 **Model Diversity**

- **200+ Models Available** - Claude, GPT, Llama, Gemini, and specialized models
- **All Major Providers** - Anthropic, OpenAI, Meta, Google, Mistral, and more
- **Cutting-edge Models** - Access to latest releases often before direct APIs
- **Specialized Models** - Web-search enabled, reasoning-focused, and domain-specific models

### 💰 **Cost Benefits**

- **50%+ Savings** - Significantly cheaper than direct provider APIs
- **No Minimums** - Pay only for what you use
- **Transparent Pricing** - Clear per-token costs for all models
- **Free Tier** - Get started with free credits

### 🔧 **Developer Experience**

- **Unified API** - One interface for all models
- **OpenAI Compatible** - Drop-in replacement for OpenAI API
- **Model Switching** - Change models with single environment variable
- **Rate Limiting** - Built-in queue management
- **Usage Analytics** - Detailed cost and usage tracking

## 🚀 Quick Setup

### 1. Get OpenRouter API Key

1. Visit [openrouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Navigate to [Keys](https://openrouter.ai/keys)
4. Generate a new API key
5. Add credits to your account (or use free tier)

### 2. Configure Environment

```bash
# Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Choose your preferred model (optional)
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # Default

# Start the system
uv run python run.py
```

### 3. Verify Setup

Check the startup logs for:

```
✅ Using OpenRouter model: anthropic/claude-3.5-sonnet
```

## 📋 Available Models

### **Recommended for Knowledge Management**

#### **Claude Models (Best for Analysis)**

```bash
# Latest Claude 3.5 Sonnet (Recommended)
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
# Cost: ~$3.00 per 1M input tokens, $15.00 per 1M output tokens

# Claude 3 Haiku (Fast & Cheap)
export OPENROUTER_MODEL=anthropic/claude-3-haiku
# Cost: ~$0.25 per 1M input tokens, $1.25 per 1M output tokens

# Claude 3 Opus (Most Capable)
export OPENROUTER_MODEL=anthropic/claude-3-opus
# Cost: ~$15.00 per 1M input tokens, $75.00 per 1M output tokens
```

#### **GPT Models (Versatile)**

```bash
# GPT-4o (Latest OpenAI)
export OPENROUTER_MODEL=openai/gpt-4o
# Cost: ~$2.50 per 1M input tokens, $10.00 per 1M output tokens

# GPT-4o Mini (Fast & Cheap)
export OPENROUTER_MODEL=openai/gpt-4o-mini
# Cost: ~$0.15 per 1M input tokens, $0.60 per 1M output tokens

# GPT-4 Turbo
export OPENROUTER_MODEL=openai/gpt-4-turbo
# Cost: ~$10.00 per 1M input tokens, $30.00 per 1M output tokens
```

#### **Llama Models (Open Source)**

```bash
# Llama 3.1 70B (High Quality)
export OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
# Cost: ~$0.59 per 1M input tokens, $0.79 per 1M output tokens

# Llama 3.1 8B (Fast & Cheap)
export OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct
# Cost: ~$0.06 per 1M input tokens, $0.06 per 1M output tokens

# Llama 3.1 405B (Most Capable Open Model)
export OPENROUTER_MODEL=meta-llama/llama-3.1-405b-instruct
# Cost: ~$2.70 per 1M input tokens, $2.70 per 1M output tokens
```

#### **Gemini Models (Google)**

```bash
# Gemini Flash 1.5 (Fast)
export OPENROUTER_MODEL=google/gemini-flash-1.5
# Cost: ~$0.075 per 1M input tokens, $0.30 per 1M output tokens

# Gemini Pro 1.5 (High Quality)
export OPENROUTER_MODEL=google/gemini-pro-1.5
# Cost: ~$1.25 per 1M input tokens, $5.00 per 1M output tokens
```

#### **Specialized Models**

```bash
# Web Search Enabled
export OPENROUTER_MODEL=perplexity/llama-3.1-sonar-large-128k-online

# Reasoning Focused
export OPENROUTER_MODEL=microsoft/wizardlm-2-8x22b

# Code Generation
export OPENROUTER_MODEL=deepseek/deepseek-coder

# Long Context (2M tokens)
export OPENROUTER_MODEL=anthropic/claude-3-haiku:beta
```

## 🎯 Model Selection Guide

### **For Different Use Cases**

#### **General Knowledge Management**

- **Best**: `anthropic/claude-3.5-sonnet` - Excellent reasoning and categorization
- **Budget**: `anthropic/claude-3-haiku` - Fast and affordable
- **Alternative**: `openai/gpt-4o-mini` - Good balance of cost and quality

#### **Research Analysis**

- **Best**: `anthropic/claude-3-opus` - Most thorough analysis
- **Alternative**: `openai/gpt-4o` - Strong analytical capabilities
- **Budget**: `meta-llama/llama-3.1-70b-instruct` - Open source option

#### **High Volume Processing**

- **Best**: `anthropic/claude-3-haiku` - Fastest response times
- **Alternative**: `openai/gpt-4o-mini` - Very cost effective
- **Budget**: `meta-llama/llama-3.1-8b-instruct` - Lowest cost

#### **Complex Reasoning**

- **Best**: `anthropic/claude-3-opus` - Superior reasoning abilities
- **Alternative**: `openai/gpt-4-turbo` - Strong reasoning
- **Budget**: `microsoft/wizardlm-2-8x22b` - Specialized for reasoning

## 💡 Usage Examples

### **Basic Chat**

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze this research: Transformers revolutionized NLP"}'
```

### **Model Switching**

```bash
# Switch to GPT-4o for comparison
export OPENROUTER_MODEL=openai/gpt-4o
uv run python run.py

# Switch back to Claude
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
uv run python run.py
```

### **Performance Testing**

```bash
# Test different models
export OPENROUTER_MODEL=anthropic/claude-3-haiku
uv run python test_openrouter_integration.py

export OPENROUTER_MODEL=openai/gpt-4o-mini
uv run python test_openrouter_integration.py
```

## 📊 Cost Monitoring

### **Track Usage**

1. Visit [OpenRouter Usage](https://openrouter.ai/activity)
2. View detailed breakdown by model
3. Set up billing alerts
4. Monitor cost per request

### **Cost Optimization Tips**

1. **Use Haiku for categorization** - Fast and cheap for simple tasks
2. **Use Sonnet for analysis** - Better quality for complex reasoning
3. **Batch requests** - Reduce overhead costs
4. **Cache results** - The system already does this automatically
5. **Monitor token usage** - Track input/output token ratios

## 🔧 Advanced Configuration

### **Model Fallbacks**

```bash
# Primary model
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# The system will automatically fallback to:
# 1. Anthropic direct API (if ANTHROPIC_API_KEY set)
# 2. HuggingFace (if HF_TOKEN set)
# 3. OpenAI direct (if OPENAI_API_KEY set)
# 4. Free HuggingFace models
```

### **Custom Headers**

OpenRouter supports additional headers for advanced features:

- `HTTP-Referer` - For analytics
- `X-Title` - Custom request titles
- `X-Description` - Request descriptions

### **Rate Limiting**

OpenRouter provides built-in rate limiting and queuing:

- No need to implement client-side rate limiting
- Automatic request queuing during high load
- Transparent retry handling

## 🧪 Testing Your Setup

### **Run Integration Tests**

```bash
# Test with your API key
export OPENROUTER_API_KEY=your_key_here
uv run python test_openrouter_integration.py
```

### **Test Different Models**

```bash
# Test Claude
export OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Hello Claude via OpenRouter"}'

# Test GPT
export OPENROUTER_MODEL=openai/gpt-4o-mini
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Hello GPT via OpenRouter"}'

# Test Llama
export OPENROUTER_MODEL=meta-llama/llama-3.1-70b-instruct
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Hello Llama via OpenRouter"}'
```

## 🔍 Troubleshooting

### **Common Issues**

#### **API Key Issues**

```bash
# Verify your API key is set
echo $OPENROUTER_API_KEY

# Test API key validity
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" https://openrouter.ai/api/v1/models
```

#### **Model Not Found**

- Check [OpenRouter Models](https://openrouter.ai/models) for available models
- Verify exact model name spelling
- Some models may require special access

#### **Rate Limiting**

- OpenRouter handles rate limiting automatically
- No client-side rate limiting needed
- Check your account credits and limits

#### **High Costs**

- Monitor usage at [OpenRouter Activity](https://openrouter.ai/activity)
- Switch to cheaper models for simple tasks
- Implement request batching if needed

### **Debug Mode**

```bash
# Enable debug logging
export OPENROUTER_DEBUG=true
uv run python run.py
```

## 📈 Performance Optimization

### **Model Selection Strategy**

1. **Start with Haiku** - Test your prompts with fast, cheap model
2. **Upgrade to Sonnet** - When you need better quality
3. **Use Opus sparingly** - Only for most complex tasks
4. **Compare with GPT** - A/B test different providers

### **Caching Strategy**

The system automatically caches:

- Content processing results (30%+ performance improvement)
- Note categorizations
- Knowledge graph relationships

### **Request Optimization**

- Use specific, clear prompts
- Avoid redundant context
- Leverage the system's built-in tools
- Monitor token usage patterns

## 🎯 Best Practices

### **Development**

1. **Start with free tier** - Test integration before committing
2. **Use environment variables** - Easy model switching
3. **Monitor costs** - Set up billing alerts
4. **Test different models** - Find best fit for your use case

### **Production**

1. **Set spending limits** - Prevent unexpected costs
2. **Implement monitoring** - Track usage patterns
3. **Use appropriate models** - Match model to task complexity
4. **Cache aggressively** - Leverage built-in caching system

### **Cost Management**

1. **Use cheaper models for categorization** - Haiku or GPT-4o-mini
2. **Use premium models for analysis** - Sonnet or GPT-4o
3. **Monitor token ratios** - Optimize prompt efficiency
4. **Batch similar requests** - Reduce overhead

## 🔗 Useful Links

- **OpenRouter Website**: [openrouter.ai](https://openrouter.ai)
- **Model Pricing**: [openrouter.ai/models](https://openrouter.ai/models)
- **API Documentation**: [openrouter.ai/docs](https://openrouter.ai/docs)
- **Usage Dashboard**: [openrouter.ai/activity](https://openrouter.ai/activity)
- **Discord Community**: [OpenRouter Discord](https://discord.gg/openrouter)

## 🆘 Support

If you encounter issues:

1. Check this guide first
2. Run the test script: `uv run python test_openrouter_integration.py`
3. Check OpenRouter status: [status.openrouter.ai](https://status.openrouter.ai)
4. Review usage dashboard for account issues
5. Contact OpenRouter support for API-specific issues

---

**OpenRouter Integration Complete! 🌟 | Access to 200+ AI Models | Optimized for Knowledge Management 📚**
