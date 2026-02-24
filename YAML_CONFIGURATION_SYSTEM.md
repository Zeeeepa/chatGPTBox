# 🔧 YAML Configuration System
## **Enterprise Stealth AI Management System**

This document provides comprehensive YAML configuration examples for the enterprise stealth AI management system that combines ChatGPTBox UI patterns with advanced stealth capabilities.

## 📋 **Configuration Architecture**

The system uses a multi-layered YAML configuration approach:
- **Main Config**: Core system settings
- **Providers Config**: AI service provider definitions
- **Stealth Profiles**: Stealth technique configurations
- **UI Config**: Interface and user experience settings
- **Security Config**: Authentication and encryption settings

---

## 🎯 **1. Main System Configuration**

```yaml
# config/main.yaml
system:
  name: "Enterprise Stealth AI Manager"
  version: "1.0.0"
  environment: "production" # development, staging, production
  
  # Core Services
  services:
    core_orchestrator:
      enabled: true
      host: "localhost"
      port: 8080
      workers: 4
      
    api_gateway:
      enabled: true
      host: "localhost"
      port: 8082
      rate_limit: 1000 # requests per minute
      
    stealth_proxy:
      enabled: true
      host: "localhost"
      port: 8081
      
    frontend:
      enabled: true
      host: "localhost"
      port: 3000
      
  # Database Configuration
  database:
    type: "postgresql"
    host: "localhost"
    port: 5432
    name: "ai_service_manager"
    username: "${DB_USERNAME}"
    password: "${DB_PASSWORD}"
    ssl_mode: "require"
    max_connections: 100
    
  # Redis Configuration
  redis:
    host: "localhost"
    port: 6379
    password: "${REDIS_PASSWORD}"
    db: 0
    
  # Logging
  logging:
    level: "info" # debug, info, warn, error
    format: "json"
    output: "stdout"
    file: "/var/log/ai-manager.log"
```

---

## 🤖 **2. AI Service Providers Configuration**

```yaml
# config/providers.yaml
providers:
  # OpenAI Configuration
  openai_gpt4:
    name: "OpenAI GPT-4"
    type: "openai"
    enabled: true
    priority: 1
    
    # Connection Details
    api:
      base_url: "https://api.openai.com/v1"
      endpoint: "/chat/completions"
      method: "POST"
      
    # Authentication
    auth:
      type: "bearer_token"
      token: "${OPENAI_API_KEY}"
      
    # Model Configuration
    model:
      name: "gpt-4"
      max_tokens: 4096
      temperature: 0.7
      top_p: 1.0
      
    # Stealth Configuration
    stealth:
      profile: "chrome_latest"
      enabled: true
      detection_threshold: 0.1
      
    # Rate Limiting
    rate_limit:
      requests_per_minute: 60
      requests_per_hour: 3600
      
    # Cost Management
    cost:
      input_cost_per_1k_tokens: 0.03
      output_cost_per_1k_tokens: 0.06
      daily_budget: 100.0
      
  # Claude Configuration
  anthropic_claude:
    name: "Anthropic Claude"
    type: "claude"
    enabled: true
    priority: 2
    
    api:
      base_url: "https://api.anthropic.com/v1"
      endpoint: "/messages"
      method: "POST"
      
    auth:
      type: "api_key"
      header: "x-api-key"
      token: "${ANTHROPIC_API_KEY}"
      
    model:
      name: "claude-3-sonnet-20240229"
      max_tokens: 4096
      temperature: 0.7
      
    stealth:
      profile: "firefox_latest"
      enabled: true
      detection_threshold: 0.15
      
    rate_limit:
      requests_per_minute: 50
      requests_per_hour: 2000
      
    cost:
      input_cost_per_1k_tokens: 0.015
      output_cost_per_1k_tokens: 0.075
      daily_budget: 80.0
      
  # Google Gemini Configuration
  google_gemini:
    name: "Google Gemini Pro"
    type: "gemini"
    enabled: true
    priority: 3
    
    api:
      base_url: "https://generativelanguage.googleapis.com/v1beta"
      endpoint: "/models/gemini-pro:generateContent"
      method: "POST"
      
    auth:
      type: "api_key"
      param: "key"
      token: "${GOOGLE_API_KEY}"
      
    model:
      name: "gemini-pro"
      max_tokens: 2048
      temperature: 0.9
      
    stealth:
      profile: "safari_latest"
      enabled: true
      detection_threshold: 0.2
      
    rate_limit:
      requests_per_minute: 60
      requests_per_hour: 1500
      
    cost:
      input_cost_per_1k_tokens: 0.0005
      output_cost_per_1k_tokens: 0.0015
      daily_budget: 50.0
      
  # Custom API Configuration
  custom_api:
    name: "Custom Local Model"
    type: "custom"
    enabled: false
    priority: 4
    
    api:
      base_url: "http://localhost:11434/v1"
      endpoint: "/chat/completions"
      method: "POST"
      
    auth:
      type: "none"
      
    model:
      name: "llama2"
      max_tokens: 2048
      temperature: 0.8
      
    stealth:
      profile: "none"
      enabled: false
      
    rate_limit:
      requests_per_minute: 100
      requests_per_hour: 6000
      
    cost:
      input_cost_per_1k_tokens: 0.0
      output_cost_per_1k_tokens: 0.0
      daily_budget: 0.0
```

---

## 🛡️ **3. Stealth Profiles Configuration**

```yaml
# config/stealth_profiles.yaml
stealth_profiles:
  # Chrome Latest Profile
  chrome_latest:
    name: "Chrome Latest"
    description: "Latest Chrome browser fingerprint"
    
    # JA4+ Fingerprint Configuration
    ja4_fingerprint:
      ja4: "t13d1516h2_8daaf6152771_b0da82dd1658"
      ja4h: "ge11nn05enus_9ed1ff1f7b03_cd8dafe26982"
      ja4x: "1728_1301_1302_1303_c02b_c02f_c02c_c030_cca9_cca8_c013_c014_009c_009d_002f_0035"
      ja4t: "1460_64_1_1_1_1_1_1_1_1_1_1_1_1_1_1"
      
    # Browser Headers
    headers:
      user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
      accept_language: "en-US,en;q=0.9"
      accept_encoding: "gzip, deflate, br"
      sec_ch_ua: '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
      sec_ch_ua_mobile: "?0"
      sec_ch_ua_platform: '"Windows"'
      sec_fetch_dest: "document"
      sec_fetch_mode: "navigate"
      sec_fetch_site: "none"
      sec_fetch_user: "?1"
      upgrade_insecure_requests: "1"
      
    # Timing Configuration
    timing:
      min_delay: 100
      max_delay: 300
      typing_speed: 50
      mouse_movement_speed: 200
      
    # Browser Automation Settings
    automation:
      viewport_width: 1920
      viewport_height: 1080
      device_scale_factor: 1.0
      is_mobile: false
      has_touch: false
      
    # Detection Evasion
    evasion:
      webdriver_detection: true
      automation_detection: true
      headless_detection: true
      canvas_fingerprinting: true
      webgl_fingerprinting: true
      
  # Firefox Latest Profile
  firefox_latest:
    name: "Firefox Latest"
    description: "Latest Firefox browser fingerprint"
    
    ja4_fingerprint:
      ja4: "t13d1715h2_5b57614c22b0_3d5424432c57"
      ja4h: "ge11nn05enus_9ed1ff1f7b03_cd8dafe26982"
      ja4x: "1728_1301_1302_1303_c02b_c02f_c02c_c030_cca9_cca8_c013_c014_009c_009d_002f_0035"
      ja4t: "1460_64_1_1_1_1_1_1_1_1_1_1_1_1_1_1"
      
    headers:
      user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
      accept_language: "en-US,en;q=0.5"
      accept_encoding: "gzip, deflate, br"
      dnt: "1"
      upgrade_insecure_requests: "1"
      
    timing:
      min_delay: 150
      max_delay: 400
      typing_speed: 45
      mouse_movement_speed: 180
      
    automation:
      viewport_width: 1920
      viewport_height: 1080
      device_scale_factor: 1.0
      is_mobile: false
      has_touch: false
      
    evasion:
      webdriver_detection: true
      automation_detection: true
      headless_detection: true
      canvas_fingerprinting: true
      webgl_fingerprinting: true
      
  # Safari Latest Profile
  safari_latest:
    name: "Safari Latest"
    description: "Latest Safari browser fingerprint"
    
    ja4_fingerprint:
      ja4: "t13d1516h2_8daaf6152771_b0da82dd1658"
      ja4h: "ge11nn05enus_9ed1ff1f7b03_cd8dafe26982"
      ja4x: "1728_1301_1302_1303_c02b_c02f_c02c_c030_cca9_cca8_c013_c014_009c_009d_002f_0035"
      ja4t: "1460_64_1_1_1_1_1_1_1_1_1_1_1_1_1_1"
      
    headers:
      user_agent: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
      accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
      accept_language: "en-US,en;q=0.9"
      accept_encoding: "gzip, deflate, br"
      
    timing:
      min_delay: 120
      max_delay: 350
      typing_speed: 55
      mouse_movement_speed: 220
      
    automation:
      viewport_width: 1440
      viewport_height: 900
      device_scale_factor: 2.0
      is_mobile: false
      has_touch: false
      
    evasion:
      webdriver_detection: true
      automation_detection: true
      headless_detection: true
      canvas_fingerprinting: true
      webgl_fingerprinting: true
```

## 📁 **Complete Configuration File Structure**

```
config/
├── main.yaml                    # Core system configuration
├── providers.yaml               # AI service provider definitions  
├── stealth_profiles.yaml        # Stealth technique configurations
├── ui.yaml                      # ChatGPTBox-inspired UI settings
├── security.yaml                # Authentication and encryption
├── integration_examples.yaml    # Real-world scenario examples
└── loader.go                    # Configuration loader implementation
```

## 🚀 **Usage Examples**

### **1. Load Development Configuration**
```go
loader := NewConfigLoader("./config")
config, err := loader.LoadConfig("Local Development Setup")
```

### **2. Load Production Configuration**
```go
config, err := loader.LoadConfig("Enterprise Production Environment")
```

### **3. Load High-Security Configuration**
```go
config, err := loader.LoadConfig("Government/Military High-Security Setup")
```

### **4. Load Multi-Tenant SaaS Configuration**
```go
config, err := loader.LoadConfig("Multi-Tenant SaaS Platform")
```

### **5. Load Edge/On-Premise Configuration**
```go
config, err := loader.LoadConfig("Edge/On-Premise Deployment")
```

## 🔧 **Environment Variables**

Create a `.env` file with your configuration:

```bash
# Database Configuration
DB_USERNAME=ai_manager
DB_PASSWORD=your_secure_password_here

# Redis Configuration  
REDIS_PASSWORD=your_redis_password_here

# JWT Configuration
JWT_SECRET=your_jwt_secret_key_here

# API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here

# OAuth2 Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Encryption Keys
API_KEY_ENCRYPTION_KEY=your-32-character-encryption-key-here
```

## 🐳 **Docker Deployment**

Use the provided `docker-compose.yaml` for complete system deployment:

```bash
# Copy environment template
cp .env.example .env

# Edit your configuration
nano .env

# Deploy the system
docker-compose up -d
```

## 🎯 **Key Features**

✅ **ChatGPTBox UI Integration** - Advanced InputBox and ConversationCard components
✅ **Multi-Provider Support** - OpenAI, Claude, Gemini, and custom APIs
✅ **Advanced Stealth Profiles** - JA4+ fingerprinting and browser evasion
✅ **Enterprise Security** - JWT, OAuth2, RBAC, and encryption
✅ **Scenario-Based Configuration** - 5 real-world deployment examples
✅ **Environment Variable Support** - Secure credential management
✅ **Docker Compose Ready** - Complete containerized deployment
✅ **Go Configuration Loader** - Type-safe configuration loading with merging

This comprehensive YAML configuration system makes the entire enterprise stealth AI management system fully configurable and deployable across multiple scenarios while maintaining ChatGPTBox's excellent UI patterns and adding military-grade stealth capabilities! 🛡️⚡
