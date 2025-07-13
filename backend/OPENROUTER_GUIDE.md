# OpenRouter Integration Guide

This guide explains how to use OpenRouter with your knowledge management system, including the recent fixes and proper setup instructions.

## 🚨 Fixed Issues

The OpenRouter integration has been **fixed** in the latest version. Previous issues were:

1. **Incorrect model naming**: Models need to be prefixed with `openrouter/`
2. **Wrong base URL configuration**: Should use environment variables, not constructor parameters
3. **Missing optional headers**: Site URL and app name were not properly configured

## 🛠️ Setup Instructions

### 1. Environment Variables

Set these environment variables in your system or `.env` file:

```bash
# Required
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional - Model selection (defaults to anthropic/claude-3.5-sonnet)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional - For OpenRouter rankings (recommended)
OR_SITE_URL=https://your-website.com
OR_APP_NAME=Knowledge-Management-System

# Optional - Enable debug mode for troubleshooting
DEBUG=true
```

### 2. Get Your OpenRouter API Key

1. Go to [OpenRouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Navigate to your API keys section
4. Create a new API key
5. Add some credits to your account

### 3. Available Models

Popular models you can use with OpenRouter:

```bash
# Anthropic Claude models
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
OPENROUTER_MODEL=anthropic/claude-3.5-haiku

# OpenAI models
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_MODEL=openai/gpt-4o-mini

# Open source models (often cheaper/free)
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_MODEL=google/gemini-flash-1.5
OPENROUTER_MODEL=microsoft/wizardlm-2-8x22b
```

### 4. Testing Your Setup

Run the test script to verify everything works:

```bash
cd backend
python test_scripts/test_openrouter_integration.py
```

## 📋 Configuration Examples

### Basic Configuration

```bash
# Minimal setup
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
```

### Advanced Configuration

```bash
# Full setup with rankings and debugging
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
export OR_SITE_URL="https://myknowledgeapp.com"
export OR_APP_NAME="Personal Knowledge Manager"
export DEBUG="true"
```

## 🔧 Technical Details

### How the Integration Works

1. **Model Priority**: OpenRouter has the highest priority in model selection
2. **LiteLLM Integration**: Uses LiteLLM's OpenRouter provider with proper prefixing
3. **Automatic Fallback**: If OpenRouter fails, falls back to other configured models
4. **Cost Tracking**: All OpenRouter usage is tracked through your OpenRouter dashboard

### Code Changes Made

The `_setup_openrouter_model` method was updated to:

```python
def _setup_openrouter_model(self):
    """Setup OpenRouter model (highest priority)"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    # Get the model name from environment or use default
    model_name = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    # Set up OpenRouter-specific environment variables
    os.environ["OPENROUTER_API_KEY"] = api_key

    # Optional: Set site URL and app name for OpenRouter rankings
    site_url = os.getenv("OR_SITE_URL", "")
    app_name = os.getenv("OR_APP_NAME", "Knowledge-Management-System")

    if site_url:
        os.environ["OR_SITE_URL"] = site_url
    if app_name:
        os.environ["OR_APP_NAME"] = app_name

    # For LiteLLM, OpenRouter models must be prefixed with "openrouter/"
    litellm_model_name = f"openrouter/{model_name}"

    try:
        # Create the LiteLLM model with proper OpenRouter configuration
        model = LiteLLMModel(
            model_id=litellm_model_name,
            api_key=api_key
        )

        print(f"🔗 OpenRouter model configured: {litellm_model_name}")
        return model

    except Exception as e:
        print(f"❌ Failed to setup OpenRouter model: {e}")
        return None
```

## 🎯 Usage Examples

### Direct LiteLLM Usage

If you want to use OpenRouter directly with LiteLLM (outside the knowledge agent):

```python
import os
from litellm import completion

# Set up environment
os.environ["OPENROUTER_API_KEY"] = "your-key-here"

# Make a request
response = completion(
    model="openrouter/anthropic/claude-3.5-sonnet",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Using OpenAI Client with OpenRouter

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="your-openrouter-api-key",
)

completion = client.chat.completions.create(
    extra_headers={
        "HTTP-Referer": "https://your-site.com",  # Optional
        "X-Title": "Your App Name",  # Optional
    },
    model="anthropic/claude-3.5-sonnet",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(completion.choices[0].message.content)
```

### Using Requests with OpenRouter

```python
import requests
import json

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer your-openrouter-api-key",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site.com",  # Optional
        "X-Title": "Your App Name",  # Optional
    },
    data=json.dumps({
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    })
)

print(response.json())
```

## 🐛 Troubleshooting

### Common Issues

1. **"Model not found" errors**

   - Make sure to prefix the model with `openrouter/` when using LiteLLM
   - Check that the model exists on OpenRouter

2. **Authentication errors**

   - Verify your API key is correct
   - Check that you have credits in your OpenRouter account

3. **Rate limiting**
   - OpenRouter has rate limits per model
   - Consider using cheaper/free models for testing

### Debug Mode

Enable debug mode for detailed error information:

```bash
export DEBUG=true
```

This will show detailed LiteLLM logs and help identify issues.

### Check Your Setup

Run the test script to verify everything:

```bash
cd backend
python test_scripts/test_openrouter_integration.py
```

### Check OpenRouter Dashboard

1. Go to [OpenRouter.ai](https://openrouter.ai)
2. Check your usage and spending
3. Verify your API key is active
4. Check rate limits for your models

## 💡 Tips and Best Practices

### Model Selection

- **For production**: Use reliable models like `anthropic/claude-3.5-sonnet`
- **For testing**: Use free models like `meta-llama/llama-3.1-8b-instruct:free`
- **For cost optimization**: Compare pricing on OpenRouter's model page

### Cost Management

- Monitor your usage on the OpenRouter dashboard
- Set up billing alerts
- Use cheaper models for simple tasks
- Consider using free models for development

### Performance Optimization

- Use appropriate models for your task complexity
- Set reasonable `max_tokens` limits
- Cache responses when possible
- Use OpenRouter's routing features for automatic failover

## 📊 Model Recommendations

### For Knowledge Management

| Task             | Recommended Model             | Why                         |
| ---------------- | ----------------------------- | --------------------------- |
| Note creation    | `anthropic/claude-3.5-haiku`  | Fast, good for simple tasks |
| Content analysis | `anthropic/claude-3.5-sonnet` | Excellent reasoning         |
| Quick searches   | `openai/gpt-4o-mini`          | Fast and cost-effective     |
| Complex research | `anthropic/claude-3.5-sonnet` | Best for detailed analysis  |

### Cost Comparison

Check current pricing at [OpenRouter.ai/models](https://openrouter.ai/models)

## 🔄 Migration from Other Providers

If you're switching from another provider:

1. Keep your old API keys as fallbacks
2. Test thoroughly with OpenRouter first
3. Monitor costs and performance
4. Gradually migrate your workflows

## 📚 Additional Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [LiteLLM OpenRouter Guide](https://docs.litellm.ai/docs/providers/openrouter)
- [OpenRouter Model Pricing](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run the test script with debug mode enabled
3. Check OpenRouter's status page
4. Review your OpenRouter dashboard for usage/billing issues

---

_This guide was last updated with the OpenRouter integration fixes. The system now properly supports OpenRouter with LiteLLM integration._
