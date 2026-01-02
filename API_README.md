# ChatGPTBox-Style Multi-AI API

A unified API that works as an adapter between multiple AI providers (OpenAI API, Gemini API, Anthropic API, Z.AI, etc.) and web chat interfaces. Inspired by the ChatGPTBox browser extension architecture.

## Features

### 🤖 Multiple Provider Support
- **API-based providers**: Codegen API, OpenAI, Anthropic, Gemini
- **Web automation providers**: Z.AI, Claude Web, Gemini Web, Custom URLs
- **Unified interface**: Same API for all providers

### 🌐 Web UI State Management
- **Input area tracking**: Monitors text input availability
- **Send button states**: Tracks button states (ready, progressing, disabled)
- **Response extraction**: Intelligent content extraction from web interfaces
- **Conversation history**: Maintains chat context across providers
- **New chat functionality**: Start fresh conversations

### 🔧 Custom Provider Support
- **Configurable selectors**: XPath/CSS selectors for any chat website
- **Predefined configs**: DeepSeek, Mistral, Perplexity, and more
- **Dynamic registration**: Add new providers at runtime

### 🚀 Real-time Features
- **Streaming responses**: Real-time message streaming
- **WebSocket support**: Live chat connections
- **Health monitoring**: Provider status and health checks

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd chatgptbox-multi-ai-api

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Basic Usage

```bash
# Start the server
python main.py

# Or with custom configuration
HOST=0.0.0.0 PORT=8080 python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Chat Completion

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "provider": "codegen-api"
  }'
```

### Streaming Chat

```bash
curl -X POST "http://localhost:8000/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about AI",
    "provider": "claude-web"
  }'
```

### List Providers

```bash
curl "http://localhost:8000/v1/providers"
```

### Health Check

```bash
curl "http://localhost:8000/v1/health"
```

## Provider Configuration

### API-based Providers

```python
# Codegen API
{
  "provider": "codegen-api",
  "message": "Your question here"
}

# OpenAI (via Codegen)
{
  "provider": "codegen-api",
  "model": "gpt-4",
  "message": "Your question here"
}
```

### Web Automation Providers

```python
# Claude Web Interface
{
  "provider": "claude-web",
  "message": "Your question here"
}

# Z.AI Web Interface
{
  "provider": "zai-web",
  "message": "Your question here"
}

# Gemini Web Interface
{
  "provider": "gemini-web",
  "message": "Your question here"
}
```

### Custom Web Providers

Add a custom provider for any chat website:

```bash
curl -X POST "http://localhost:8000/v1/providers/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-custom-ai",
    "base_url": "https://chat.example.com",
    "input_selector": "textarea[placeholder*=\"Type a message\"]",
    "send_button_selector": "button[type=\"submit\"]",
    "response_selector": ".message-content",
    "new_chat_selector": ".new-chat-button"
  }'
```

## WebSocket Usage

Connect to real-time chat:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client123');

ws.onopen = function() {
    // Send a message
    ws.send(JSON.stringify({
        provider: 'claude-web',
        message: 'Hello Claude!'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'chunk') {
        console.log('Received chunk:', data.content);
    } else if (data.type === 'complete') {
        console.log('Response complete');
    }
};
```

## UI State Variables

The system tracks these UI state variables for web providers:

```python
ui_state = {
    "input_available": bool,      # Can accept input
    "send_button_state": str,     # "initial", "progressing", "ready"
    "response_ready": bool,       # Response is available
    "conversation_active": bool,  # Chat session is active
    "login_required": bool,       # Login needed
    "rate_limited": bool         # Rate limit active
}
```

## Predefined Custom Providers

### DeepSeek

```python
{
  "provider": "custom-deepseek",
  "message": "Your question here"
}
```

### Mistral

```python
{
  "provider": "custom-mistral", 
  "message": "Your question here"
}
```

### Perplexity

```python
{
  "provider": "custom-perplexity",
  "message": "Your question here"
}
```

## Environment Variables

```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true

# API keys (if using API providers)
CODEGEN_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

## Architecture

### Provider Types

1. **API_BASED**: Direct API calls (Codegen, OpenAI, etc.)
2. **WEB_AUTOMATION**: Browser automation (Claude, Z.AI, etc.)
3. **CUSTOM_WEB**: Configurable web automation

### Core Components

- **BaseProvider**: Abstract base class for all providers
- **ProviderManager**: Manages provider lifecycle and routing
- **WebUIElements**: Configuration for web automation
- **ChatEndpoints**: FastAPI routes and WebSocket handlers

### Web Automation Flow

1. **Initialize**: Launch browser and navigate to chat URL
2. **Find Elements**: Locate input, send button, response areas
3. **Send Message**: Type message and click send
4. **Extract Response**: Monitor and extract AI response
5. **Stream Updates**: Provide real-time response streaming

## Testing

### Test All Providers

```bash
curl -X POST "http://localhost:8000/v1/test/dynamic-prompts"
```

### Test Specific Provider

```python
# Test Claude Web
python -c "
import asyncio
from src.providers.claude_web_provider import test_claude_web
asyncio.run(test_claude_web())
"

# Test Custom Provider
python -c "
import asyncio
from src.providers.custom_web_provider import test_custom_web
asyncio.run(test_custom_web())
"
```

## Advanced Usage

### Custom Selectors

For complex websites, you can use XPath selectors:

```python
{
  "name": "advanced-chat",
  "base_url": "https://complex-chat.com",
  "input_selector": "//div[@contenteditable='true']",
  "send_button_selector": "//button[contains(@class, 'send')]",
  "response_selector": "//div[contains(@class, 'response')]",
  "use_xpath": true
}
```

### Conversation History

Maintain context across messages:

```python
{
  "message": "What did I ask before?",
  "provider": "claude-web",
  "conversation_history": [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."}
  ]
}
```

### New Chat Sessions

Start fresh conversations:

```bash
curl -X POST "http://localhost:8000/v1/providers/claude-web/new-chat"
```

## Error Handling

The API provides detailed error information:

```json
{
  "content": "",
  "provider": "claude-web",
  "success": false,
  "error": "Claude rate limit active",
  "metadata": {
    "ui_state": {
      "rate_limited": true
    }
  }
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your provider or enhancement
4. Test thoroughly
5. Submit a pull request

### Adding New Providers

1. Inherit from `BaseProvider`
2. Implement required methods
3. Add to provider manager
4. Create tests

## License

MIT License - see LICENSE file for details

## Support

- GitHub Issues: Report bugs and feature requests
- Documentation: Check the `/docs` endpoint when running
- Examples: See the `examples/` directory

---

**Note**: This project is inspired by the ChatGPTBox browser extension and aims to provide similar functionality through a unified API interface.
