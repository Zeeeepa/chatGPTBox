# 🚀 Multi-Chat WebUI Hub

A comprehensive multi-interface chat system that integrates various AI services including Claude Web, GitHub Copilot, Z.AI instances, and OpenAI API proxy. This system provides a unified web interface to interact with multiple AI chat services simultaneously.

## 🌟 Features

### 🤖 Multiple AI Interfaces
- **Claude Web Interface**: Browser automation for Claude AI chat
- **GitHub Copilot Code Interface**: Code assistance and suggestions
- **Z.AI Instances (3x)**: Multiple OpenAI API-connected instances with different configurations
- **OpenAI Proxy Interface**: Direct OpenAI API access with proxy capabilities

### 🎯 Key Capabilities
- **Real-time WebSocket Communication**: Instant messaging with all interfaces
- **Session Management**: Persistent chat sessions with activity tracking
- **Configuration Management**: Flexible configuration system for all interfaces
- **Multi-Instance Support**: Run multiple instances of the same interface type
- **Responsive Web UI**: Modern, mobile-friendly interface
- **Status Monitoring**: Real-time health checks and status indicators

## 🏗️ Architecture

```
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── interfaces/             # Interface implementations
│   │   ├── base_interface.py   # Abstract base interface
│   │   ├── claude_web.py       # Claude web automation
│   │   ├── copilot_code.py     # GitHub Copilot integration
│   │   ├── zai_interface.py    # Z.AI OpenAI API integration
│   │   └── openai_proxy.py     # Direct OpenAI API proxy
│   └── utils/
│       ├── config_manager.py   # Configuration management
│       └── session_manager.py  # Session and WebSocket management
├── templates/
│   ├── index.html             # Main interface selection page
│   └── interface.html         # Chat interface template
├── config/                    # Configuration files (auto-created)
└── requirements.txt           # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API Key (for Z.AI and OpenAI Proxy interfaces)
- Playwright browsers (for web automation)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd multi-chat-webui-hub
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers**
```bash
playwright install
```

4. **Set environment variables**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export CLAUDE_URL="https://claude.ai/chat"  # Optional
export GITHUB_URL="https://github.com"      # Optional
```

5. **Run the application**
```bash
python src/main.py
```

6. **Access the web interface**
Open your browser and navigate to `http://localhost:8000`

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for Z.AI and OpenAI Proxy interfaces
- `CLAUDE_URL`: Claude AI chat URL (default: https://claude.ai/chat)
- `GITHUB_URL`: GitHub URL (default: https://github.com)
- `HEADLESS_BROWSER`: Run browsers in headless mode (default: true)
- `BROWSER_TIMEOUT`: Browser operation timeout in ms (default: 30000)

### Interface Configurations

#### Z.AI Instances
The system automatically creates 3 Z.AI instances with different configurations:

1. **Z.AI GPT-4 Standard**: Balanced performance with GPT-4
2. **Z.AI GPT-3.5 Fast**: Quick responses with GPT-3.5-turbo
3. **Z.AI GPT-4 Creative**: High creativity with GPT-4 (temperature: 0.9)

#### Custom Configuration Files
Configuration files are automatically created in the `config/` directory:
- `zai_instance_1.json`: Z.AI GPT-4 Standard config
- `zai_instance_2.json`: Z.AI GPT-3.5 Fast config
- `zai_instance_3.json`: Z.AI GPT-4 Creative config
- `claude_web.json`: Claude web interface config
- `copilot_code.json`: GitHub Copilot config
- `openai_proxy.json`: OpenAI proxy config

## 🎮 Usage

### Web Interface
1. Navigate to `http://localhost:8000`
2. Select an interface from the grid
3. Start chatting with the AI

### API Endpoints
- `GET /`: Main interface selection page
- `GET /interface/{interface_id}`: Chat interface page
- `WebSocket /ws/{interface_id}`: Real-time chat communication
- `GET /api/interfaces`: List all available interfaces
- `GET /api/interfaces/{interface_id}/status`: Get interface status
- `POST /api/interfaces/{interface_id}/message`: Send message (HTTP)

### WebSocket Communication
```javascript
// Connect to interface
const ws = new WebSocket('ws://localhost:8000/ws/zai_instance_1');

// Send message
ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Hello, AI!',
    session_id: 'optional-session-id'
}));

// Receive response
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('AI Response:', data.response.message);
};
```

## 🔌 Interface Details

### Claude Web Interface
- **Type**: `claude_web`
- **Technology**: Playwright browser automation
- **Features**: Direct Claude AI web interface interaction
- **Requirements**: Internet connection, browser automation

### GitHub Copilot Code Interface
- **Type**: `copilot_code`
- **Technology**: Playwright + GitHub integration
- **Features**: Code suggestions, GitHub authentication
- **Requirements**: GitHub account, Copilot subscription

### Z.AI Interface
- **Type**: `zai`
- **Technology**: OpenAI API integration
- **Features**: Multiple model support, configurable parameters
- **Requirements**: OpenAI API key

### OpenAI Proxy Interface
- **Type**: `openai_proxy`
- **Technology**: Direct OpenAI API calls
- **Features**: Rate limiting, streaming responses, model selection
- **Requirements**: OpenAI API key

## 🛠️ Development

### Adding New Interfaces
1. Create a new interface class inheriting from `BaseInterface`
2. Implement required methods: `initialize()`, `send_message()`, `get_status()`, `cleanup()`
3. Add interface configuration to `ConfigManager`
4. Register interface in `main.py`

### Example Interface Implementation
```python
from .base_interface import BaseInterface

class MyCustomInterface(BaseInterface):
    async def initialize(self) -> bool:
        # Initialize your interface
        return True
    
    async def send_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        # Process message and return response
        return {
            "success": True,
            "message": "AI response",
            "session_id": session_id
        }
    
    async def get_status(self) -> Dict[str, Any]:
        # Return interface status
        return {"healthy": True}
    
    async def cleanup(self) -> None:
        # Clean up resources
        pass
```

## 📊 Monitoring

### Health Checks
- Interface status monitoring
- Session activity tracking
- WebSocket connection management
- Automatic cleanup of expired sessions

### Logging
All interfaces provide comprehensive logging:
- Connection status
- Message processing
- Error handling
- Performance metrics

## 🔒 Security

### Session Management
- Unique session IDs
- Automatic session expiration
- WebSocket connection tracking
- Secure session data handling

### API Security
- Rate limiting on OpenAI interfaces
- Input validation
- Error message sanitization
- Secure configuration management

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Key Issues**
   - Ensure `OPENAI_API_KEY` environment variable is set
   - Check API key validity and quota

2. **Browser Automation Issues**
   - Run `playwright install` to install browsers
   - Check if websites are accessible
   - Verify headless mode settings

3. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify port 8000 is available
   - Check browser WebSocket support

4. **Interface Not Responding**
   - Check interface status at `/api/interfaces/{id}/status`
   - Review logs for error messages
   - Restart the application

### Debug Mode
Enable debug logging by setting environment variable:
```bash
export DEBUG=true
python src/main.py
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

**Built with ❤️ for the AI community**
