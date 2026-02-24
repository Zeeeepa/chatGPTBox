// config/loader.go
// 🔧 Configuration Loader Example - Go Implementation
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// SystemConfig represents the main system configuration
type SystemConfig struct {
	System     SystemSettings     `yaml:"system"`
	Services   ServicesConfig     `yaml:"services"`
	Database   DatabaseConfig     `yaml:"database"`
	Redis      RedisConfig        `yaml:"redis"`
	Logging    LoggingConfig      `yaml:"logging"`
	Providers  []ProviderConfig   `yaml:"providers,omitempty"`
	Stealth    []StealthProfile   `yaml:"stealth_profiles,omitempty"`
	UI         UIConfig           `yaml:"ui,omitempty"`
	Security   SecurityConfig     `yaml:"security,omitempty"`
}

type SystemSettings struct {
	Name        string `yaml:"name"`
	Version     string `yaml:"version"`
	Environment string `yaml:"environment"`
}

type ServicesConfig struct {
	CoreOrchestrator ServiceConfig `yaml:"core_orchestrator"`
	APIGateway       ServiceConfig `yaml:"api_gateway"`
	StealthProxy     ServiceConfig `yaml:"stealth_proxy"`
	Frontend         ServiceConfig `yaml:"frontend"`
}

type ServiceConfig struct {
	Enabled   bool   `yaml:"enabled"`
	Host      string `yaml:"host"`
	Port      int    `yaml:"port"`
	Workers   int    `yaml:"workers,omitempty"`
	RateLimit int    `yaml:"rate_limit,omitempty"`
}

type DatabaseConfig struct {
	Type           string `yaml:"type"`
	Host           string `yaml:"host"`
	Port           int    `yaml:"port"`
	Name           string `yaml:"name"`
	Username       string `yaml:"username"`
	Password       string `yaml:"password"`
	SSLMode        string `yaml:"ssl_mode"`
	MaxConnections int    `yaml:"max_connections"`
}

type RedisConfig struct {
	Host     string `yaml:"host"`
	Port     int    `yaml:"port"`
	Password string `yaml:"password"`
	DB       int    `yaml:"db"`
}

type LoggingConfig struct {
	Level  string `yaml:"level"`
	Format string `yaml:"format"`
	Output string `yaml:"output"`
	File   string `yaml:"file"`
}

type ProviderConfig struct {
	Name     string                 `yaml:"name"`
	Type     string                 `yaml:"type"`
	Enabled  bool                   `yaml:"enabled"`
	Priority int                    `yaml:"priority"`
	API      APIConfig              `yaml:"api"`
	Auth     AuthConfig             `yaml:"auth"`
	Model    ModelConfig            `yaml:"model"`
	Stealth  StealthConfig          `yaml:"stealth"`
	RateLimit RateLimitConfig       `yaml:"rate_limit"`
	Cost     CostConfig             `yaml:"cost"`
}

type APIConfig struct {
	BaseURL  string `yaml:"base_url"`
	Endpoint string `yaml:"endpoint"`
	Method   string `yaml:"method"`
}

type AuthConfig struct {
	Type   string `yaml:"type"`
	Token  string `yaml:"token,omitempty"`
	Header string `yaml:"header,omitempty"`
	Param  string `yaml:"param,omitempty"`
}

type ModelConfig struct {
	Name      string  `yaml:"name"`
	MaxTokens int     `yaml:"max_tokens"`
	Temperature float64 `yaml:"temperature"`
	TopP      float64 `yaml:"top_p,omitempty"`
}

type StealthConfig struct {
	Profile           string  `yaml:"profile"`
	Enabled           bool    `yaml:"enabled"`
	DetectionThreshold float64 `yaml:"detection_threshold"`
}

type RateLimitConfig struct {
	RequestsPerMinute int `yaml:"requests_per_minute"`
	RequestsPerHour   int `yaml:"requests_per_hour"`
}

type CostConfig struct {
	InputCostPer1KTokens  float64 `yaml:"input_cost_per_1k_tokens"`
	OutputCostPer1KTokens float64 `yaml:"output_cost_per_1k_tokens"`
	DailyBudget          float64 `yaml:"daily_budget"`
}

type StealthProfile struct {
	Name         string                 `yaml:"name"`
	Description  string                 `yaml:"description"`
	JA4Fingerprint JA4Config            `yaml:"ja4_fingerprint"`
	Headers      map[string]string      `yaml:"headers"`
	Timing       TimingConfig           `yaml:"timing"`
	Automation   AutomationConfig       `yaml:"automation"`
	Evasion      EvasionConfig          `yaml:"evasion"`
}

type JA4Config struct {
	JA4  string `yaml:"ja4"`
	JA4H string `yaml:"ja4h"`
	JA4X string `yaml:"ja4x"`
	JA4T string `yaml:"ja4t"`
}

type TimingConfig struct {
	MinDelay           int `yaml:"min_delay"`
	MaxDelay           int `yaml:"max_delay"`
	TypingSpeed        int `yaml:"typing_speed"`
	MouseMovementSpeed int `yaml:"mouse_movement_speed"`
}

type AutomationConfig struct {
	ViewportWidth     int     `yaml:"viewport_width"`
	ViewportHeight    int     `yaml:"viewport_height"`
	DeviceScaleFactor float64 `yaml:"device_scale_factor"`
	IsMobile          bool    `yaml:"is_mobile"`
	HasTouch          bool    `yaml:"has_touch"`
}

type EvasionConfig struct {
	WebdriverDetection   bool `yaml:"webdriver_detection"`
	AutomationDetection  bool `yaml:"automation_detection"`
	HeadlessDetection    bool `yaml:"headless_detection"`
	CanvasFingerprinting bool `yaml:"canvas_fingerprinting"`
	WebGLFingerprinting  bool `yaml:"webgl_fingerprinting"`
}

type UIConfig struct {
	Interface     InterfaceConfig     `yaml:"interface"`
	Enterprise    EnterpriseUIConfig  `yaml:"enterprise"`
	Customization CustomizationConfig `yaml:"customization"`
}

type InterfaceConfig struct {
	Theme           string                `yaml:"theme"`
	Language        string                `yaml:"language"`
	InputBox        InputBoxConfig        `yaml:"input_box"`
	ConversationCard ConversationCardConfig `yaml:"conversation_card"`
	RealTime        RealTimeConfig        `yaml:"real_time"`
	Accessibility   AccessibilityConfig   `yaml:"accessibility"`
}

type InputBoxConfig struct {
	AutoResize      bool              `yaml:"auto_resize"`
	MinHeight       string            `yaml:"min_height"`
	MaxHeight       string            `yaml:"max_height"`
	ResizeDirection string            `yaml:"resize_direction"`
	Shortcuts       map[string]string `yaml:"shortcuts"`
	Placeholder     PlaceholderConfig `yaml:"placeholder"`
	ButtonColors    ButtonColorsConfig `yaml:"button_colors"`
	BrowserSpecific BrowserSpecificConfig `yaml:"browser_specific"`
}

type PlaceholderConfig struct {
	Enabled  string `yaml:"enabled"`
	Disabled string `yaml:"disabled"`
}

type ButtonColorsConfig struct {
	Enabled  string `yaml:"enabled"`
	Disabled string `yaml:"disabled"`
}

type BrowserSpecificConfig struct {
	SafariAdaptations  bool `yaml:"safari_adaptations"`
	FirefoxAdaptations bool `yaml:"firefox_adaptations"`
	MobileAdaptations  bool `yaml:"mobile_adaptations"`
}

type ConversationCardConfig struct {
	WindowSize WindowSizeConfig `yaml:"window_size"`
	Scroll     ScrollConfig     `yaml:"scroll"`
	Messages   MessagesConfig   `yaml:"messages"`
	Export     ExportConfig     `yaml:"export"`
	Toolbar    ToolbarConfig    `yaml:"toolbar"`
}

type WindowSizeConfig struct {
	MinWidth  int `yaml:"min_width"`
	MaxWidth  int `yaml:"max_width"`
	MinHeight int `yaml:"min_height"`
	MaxHeight int `yaml:"max_height"`
}

type ScrollConfig struct {
	AutoScroll     bool `yaml:"auto_scroll"`
	ScrollMargin   int  `yaml:"scroll_margin"`
	SmoothScroll   bool `yaml:"smooth_scroll"`
	LockWhenAnswer bool `yaml:"lock_when_answer"`
}

type MessagesConfig struct {
	ShowTimestamps    bool `yaml:"show_timestamps"`
	ShowModelName     bool `yaml:"show_model_name"`
	MarkdownRendering bool `yaml:"markdown_rendering"`
	CodeHighlighting  bool `yaml:"code_highlighting"`
}

type ExportConfig struct {
	Formats         []string `yaml:"formats"`
	IncludeMetadata bool     `yaml:"include_metadata"`
}

type ToolbarConfig struct {
	ShowModelSelector bool `yaml:"show_model_selector"`
	ShowExportButton  bool `yaml:"show_export_button"`
	ShowClearButton   bool `yaml:"show_clear_button"`
	ShowFloatButton   bool `yaml:"show_float_button"`
	ShowArchiveButton bool `yaml:"show_archive_button"`
}

type RealTimeConfig struct {
	TypingIndicators     bool `yaml:"typing_indicators"`
	StreamingResponses   bool `yaml:"streaming_responses"`
	LiveWordCount        bool `yaml:"live_word_count"`
	ResponseTimeDisplay  bool `yaml:"response_time_display"`
}

type AccessibilityConfig struct {
	HighContrast         bool `yaml:"high_contrast"`
	LargeText            bool `yaml:"large_text"`
	KeyboardNavigation   bool `yaml:"keyboard_navigation"`
	ScreenReaderSupport  bool `yaml:"screen_reader_support"`
}

type EnterpriseUIConfig struct {
	UserManagement UserManagementConfig `yaml:"user_management"`
	AdminDashboard AdminDashboardConfig `yaml:"admin_dashboard"`
	StealthUI      StealthUIConfig      `yaml:"stealth_ui"`
	Audit          AuditConfig          `yaml:"audit"`
}

type UserManagementConfig struct {
	ShowUserAvatar bool `yaml:"show_user_avatar"`
	ShowUserRole   bool `yaml:"show_user_role"`
	ShowUsageStats bool `yaml:"show_usage_stats"`
}

type AdminDashboardConfig struct {
	Enabled             bool `yaml:"enabled"`
	RealTimeMetrics     bool `yaml:"real_time_metrics"`
	UserActivityMonitor bool `yaml:"user_activity_monitor"`
	CostTracking        bool `yaml:"cost_tracking"`
}

type StealthUIConfig struct {
	ShowStealthStatus        bool   `yaml:"show_stealth_status"`
	StealthIndicatorPosition string `yaml:"stealth_indicator_position"`
	DetectionAlerts          bool   `yaml:"detection_alerts"`
}

type AuditConfig struct {
	ShowConversationID bool `yaml:"show_conversation_id"`
	ShowRequestTrace   bool `yaml:"show_request_trace"`
	ExportAuditLogs    bool `yaml:"export_audit_logs"`
}

type CustomizationConfig struct {
	Branding BrandingConfig `yaml:"branding"`
	Layout   LayoutConfig   `yaml:"layout"`
	Advanced AdvancedConfig `yaml:"advanced"`
}

type BrandingConfig struct {
	LogoURL        string `yaml:"logo_url"`
	CompanyName    string `yaml:"company_name"`
	PrimaryColor   string `yaml:"primary_color"`
	SecondaryColor string `yaml:"secondary_color"`
}

type LayoutConfig struct {
	SidebarPosition string `yaml:"sidebar_position"`
	HeaderStyle     string `yaml:"header_style"`
	FooterEnabled   bool   `yaml:"footer_enabled"`
}

type AdvancedConfig struct {
	DeveloperMode      bool `yaml:"developer_mode"`
	DebugPanel         bool `yaml:"debug_panel"`
	PerformanceMetrics bool `yaml:"performance_metrics"`
}

type SecurityConfig struct {
	Authentication   AuthenticationConfig   `yaml:"authentication"`
	Authorization    AuthorizationConfig    `yaml:"authorization"`
	Encryption       EncryptionConfig       `yaml:"encryption"`
	RateLimiting     RateLimitingConfig     `yaml:"rate_limiting"`
	InputValidation  InputValidationConfig  `yaml:"input_validation"`
	Audit            SecurityAuditConfig    `yaml:"audit"`
	Headers          HeadersConfig          `yaml:"headers"`
	StealthSecurity  StealthSecurityConfig  `yaml:"stealth_security"`
}

type AuthenticationConfig struct {
	JWT    JWTConfig              `yaml:"jwt"`
	OAuth2 map[string]OAuth2Config `yaml:"oauth2"`
	APIKeys APIKeysConfig         `yaml:"api_keys"`
}

type JWTConfig struct {
	Secret            string `yaml:"secret"`
	Expiration        string `yaml:"expiration"`
	RefreshExpiration string `yaml:"refresh_expiration"`
	Algorithm         string `yaml:"algorithm"`
}

type OAuth2Config struct {
	Enabled      bool     `yaml:"enabled"`
	ClientID     string   `yaml:"client_id"`
	ClientSecret string   `yaml:"client_secret"`
	Scopes       []string `yaml:"scopes"`
	TenantID     string   `yaml:"tenant_id,omitempty"`
}

type APIKeysConfig struct {
	EncryptionKey      string `yaml:"encryption_key"`
	RotationInterval   string `yaml:"rotation_interval"`
	MaxKeysPerUser     int    `yaml:"max_keys_per_user"`
}

type AuthorizationConfig struct {
	Roles     map[string]RoleConfig     `yaml:"roles"`
	Resources map[string]ResourceConfig `yaml:"resources"`
}

type RoleConfig struct {
	Permissions []string `yaml:"permissions"`
}

type ResourceConfig struct {
	OwnerPermissions  []string `yaml:"owner_permissions"`
	SharedPermissions []string `yaml:"shared_permissions"`
	AdminPermissions  []string `yaml:"admin_permissions,omitempty"`
	UserPermissions   []string `yaml:"user_permissions,omitempty"`
}

type EncryptionConfig struct {
	AtRest    AtRestConfig    `yaml:"at_rest"`
	InTransit InTransitConfig `yaml:"in_transit"`
	Database  DatabaseEncryptionConfig `yaml:"database"`
}

type AtRestConfig struct {
	Algorithm   string `yaml:"algorithm"`
	KeyRotation string `yaml:"key_rotation"`
}

type InTransitConfig struct {
	TLSVersion   string   `yaml:"tls_version"`
	CipherSuites []string `yaml:"cipher_suites"`
}

type DatabaseEncryptionConfig struct {
	EncryptSensitiveFields bool     `yaml:"encrypt_sensitive_fields"`
	Fields                 []string `yaml:"fields"`
}

type RateLimitingConfig struct {
	Global    GlobalRateLimitConfig            `yaml:"global"`
	PerUser   map[string]UserRateLimitConfig   `yaml:"per_user"`
	Endpoints map[string]EndpointRateLimitConfig `yaml:"endpoints"`
}

type GlobalRateLimitConfig struct {
	RequestsPerMinute int `yaml:"requests_per_minute"`
	RequestsPerHour   int `yaml:"requests_per_hour"`
	RequestsPerDay    int `yaml:"requests_per_day"`
}

type UserRateLimitConfig struct {
	RequestsPerMinute int `yaml:"requests_per_minute"`
	RequestsPerHour   int `yaml:"requests_per_hour"`
}

type EndpointRateLimitConfig struct {
	RequestsPerMinute int `yaml:"requests_per_minute"`
	RequestsPerHour   int `yaml:"requests_per_hour"`
}

type InputValidationConfig struct {
	Messages      MessageValidationConfig `yaml:"messages"`
	FileUploads   FileUploadConfig        `yaml:"file_uploads"`
	APIParameters APIParametersConfig     `yaml:"api_parameters"`
}

type MessageValidationConfig struct {
	MaxLength      int      `yaml:"max_length"`
	AllowedFormats []string `yaml:"allowed_formats"`
	SanitizeHTML   bool     `yaml:"sanitize_html"`
	BlockScripts   bool     `yaml:"block_scripts"`
}

type FileUploadConfig struct {
	Enabled        bool     `yaml:"enabled"`
	MaxSize        string   `yaml:"max_size"`
	AllowedTypes   []string `yaml:"allowed_types"`
	ScanForMalware bool     `yaml:"scan_for_malware"`
}

type APIParametersConfig struct {
	StrictValidation    bool `yaml:"strict_validation"`
	RejectUnknownFields bool `yaml:"reject_unknown_fields"`
	MaxNestedDepth      int  `yaml:"max_nested_depth"`
}

type SecurityAuditConfig struct {
	Enabled bool                    `yaml:"enabled"`
	Events  []string                `yaml:"events"`
	Storage AuditStorageConfig      `yaml:"storage"`
	Format  AuditFormatConfig       `yaml:"format"`
}

type AuditStorageConfig struct {
	Type       string `yaml:"type"`
	Retention  string `yaml:"retention"`
	Encryption bool   `yaml:"encryption"`
}

type AuditFormatConfig struct {
	Timestamp bool `yaml:"timestamp"`
	UserID    bool `yaml:"user_id"`
	IPAddress bool `yaml:"ip_address"`
	UserAgent bool `yaml:"user_agent"`
	RequestID bool `yaml:"request_id"`
}

type HeadersConfig struct {
	CORS           CORSConfig           `yaml:"cors"`
	SecurityHeaders SecurityHeadersConfig `yaml:"security_headers"`
}

type CORSConfig struct {
	AllowedOrigins []string `yaml:"allowed_origins"`
	AllowedMethods []string `yaml:"allowed_methods"`
	AllowedHeaders []string `yaml:"allowed_headers"`
	Credentials    bool     `yaml:"credentials"`
}

type SecurityHeadersConfig struct {
	XFrameOptions           string `yaml:"x_frame_options"`
	XContentTypeOptions     string `yaml:"x_content_type_options"`
	XXSSProtection          string `yaml:"x_xss_protection"`
	StrictTransportSecurity string `yaml:"strict_transport_security"`
	ContentSecurityPolicy   string `yaml:"content_security_policy"`
}

type StealthSecurityConfig struct {
	DetectionEvents DetectionEventsConfig `yaml:"detection_events"`
	ProfileSecurity ProfileSecurityConfig `yaml:"profile_security"`
	SessionSecurity SessionSecurityConfig `yaml:"session_security"`
}

type DetectionEventsConfig struct {
	LogLevel         string `yaml:"log_level"`
	AlertThreshold   int    `yaml:"alert_threshold"`
	AutoRotateProfiles bool `yaml:"auto_rotate_profiles"`
}

type ProfileSecurityConfig struct {
	EncryptProfiles   bool    `yaml:"encrypt_profiles"`
	ProfileRotation   string  `yaml:"profile_rotation"`
	MaxDetectionRate  float64 `yaml:"max_detection_rate"`
}

type SessionSecurityConfig struct {
	EncryptSessions        bool   `yaml:"encrypt_sessions"`
	SessionTimeout         string `yaml:"session_timeout"`
	MaxConcurrentSessions  int    `yaml:"max_concurrent_sessions"`
}

// ConfigLoader handles loading and merging YAML configurations
type ConfigLoader struct {
	configDir string
}

// NewConfigLoader creates a new configuration loader
func NewConfigLoader(configDir string) *ConfigLoader {
	return &ConfigLoader{
		configDir: configDir,
	}
}

// LoadConfig loads the main configuration with optional scenario overrides
func (cl *ConfigLoader) LoadConfig(scenario string) (*SystemConfig, error) {
	// Load main configuration
	mainConfig, err := cl.loadMainConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to load main config: %w", err)
	}

	// Load scenario-specific overrides if specified
	if scenario != "" {
		scenarioConfig, err := cl.loadScenarioConfig(scenario)
		if err != nil {
			return nil, fmt.Errorf("failed to load scenario config '%s': %w", scenario, err)
		}
		
		// Merge scenario overrides
		if err := cl.mergeConfigs(mainConfig, scenarioConfig); err != nil {
			return nil, fmt.Errorf("failed to merge scenario config: %w", err)
		}
	}

	// Load additional configuration files
	if err := cl.loadAdditionalConfigs(mainConfig); err != nil {
		return nil, fmt.Errorf("failed to load additional configs: %w", err)
	}

	// Expand environment variables
	if err := cl.expandEnvironmentVariables(mainConfig); err != nil {
		return nil, fmt.Errorf("failed to expand environment variables: %w", err)
	}

	return mainConfig, nil
}

// loadMainConfig loads the main configuration file
func (cl *ConfigLoader) loadMainConfig() (*SystemConfig, error) {
	configPath := filepath.Join(cl.configDir, "main.yaml")
	return cl.loadConfigFile(configPath)
}

// loadScenarioConfig loads a scenario-specific configuration
func (cl *ConfigLoader) loadScenarioConfig(scenario string) (*SystemConfig, error) {
	configPath := filepath.Join(cl.configDir, "integration_examples.yaml")
	
	// Load the integration examples file
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read scenario config file: %w", err)
	}

	// Parse YAML documents (scenarios are separated by ---)
	docs := strings.Split(string(data), "---")
	
	for _, doc := range docs {
		doc = strings.TrimSpace(doc)
		if doc == "" {
			continue
		}

		var scenarioData map[string]interface{}
		if err := yaml.Unmarshal([]byte(doc), &scenarioData); err != nil {
			continue // Skip invalid documents
		}

		// Check if this is the requested scenario
		for key, value := range scenarioData {
			if strings.HasSuffix(key, "_scenario") {
				if scenarioMap, ok := value.(map[string]interface{}); ok {
					if name, exists := scenarioMap["name"]; exists && name == scenario {
						// Convert to SystemConfig
						var config SystemConfig
						configBytes, _ := yaml.Marshal(scenarioMap)
						if err := yaml.Unmarshal(configBytes, &config); err == nil {
							return &config, nil
						}
					}
				}
			}
		}
	}

	return nil, fmt.Errorf("scenario '%s' not found", scenario)
}

// loadConfigFile loads a single YAML configuration file
func (cl *ConfigLoader) loadConfigFile(path string) (*SystemConfig, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file %s: %w", path, err)
	}

	var config SystemConfig
	if err := yaml.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file %s: %w", path, err)
	}

	return &config, nil
}

// loadAdditionalConfigs loads providers, stealth profiles, UI, and security configs
func (cl *ConfigLoader) loadAdditionalConfigs(config *SystemConfig) error {
	// Load providers if not already loaded
	if len(config.Providers) == 0 {
		providers, err := cl.loadProvidersConfig()
		if err == nil {
			config.Providers = providers
		}
	}

	// Load stealth profiles if not already loaded
	if len(config.Stealth) == 0 {
		profiles, err := cl.loadStealthProfilesConfig()
		if err == nil {
			config.Stealth = profiles
		}
	}

	// Load UI config if not already loaded
	if config.UI == (UIConfig{}) {
		uiConfig, err := cl.loadUIConfig()
		if err == nil {
			config.UI = *uiConfig
		}
	}

	// Load security config if not already loaded
	if config.Security == (SecurityConfig{}) {
		securityConfig, err := cl.loadSecurityConfig()
		if err == nil {
			config.Security = *securityConfig
		}
	}

	return nil
}

// loadProvidersConfig loads the providers configuration
func (cl *ConfigLoader) loadProvidersConfig() ([]ProviderConfig, error) {
	configPath := filepath.Join(cl.configDir, "providers.yaml")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var providersData struct {
		Providers map[string]ProviderConfig `yaml:"providers"`
	}
	
	if err := yaml.Unmarshal(data, &providersData); err != nil {
		return nil, err
	}

	var providers []ProviderConfig
	for name, provider := range providersData.Providers {
		provider.Name = name
		providers = append(providers, provider)
	}

	return providers, nil
}

// loadStealthProfilesConfig loads the stealth profiles configuration
func (cl *ConfigLoader) loadStealthProfilesConfig() ([]StealthProfile, error) {
	configPath := filepath.Join(cl.configDir, "stealth_profiles.yaml")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var profilesData struct {
		StealthProfiles map[string]StealthProfile `yaml:"stealth_profiles"`
	}
	
	if err := yaml.Unmarshal(data, &profilesData); err != nil {
		return nil, err
	}

	var profiles []StealthProfile
	for name, profile := range profilesData.StealthProfiles {
		profile.Name = name
		profiles = append(profiles, profile)
	}

	return profiles, nil
}

// loadUIConfig loads the UI configuration
func (cl *ConfigLoader) loadUIConfig() (*UIConfig, error) {
	configPath := filepath.Join(cl.configDir, "ui.yaml")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var uiData struct {
		UI UIConfig `yaml:"ui"`
	}
	
	if err := yaml.Unmarshal(data, &uiData); err != nil {
		return nil, err
	}

	return &uiData.UI, nil
}

// loadSecurityConfig loads the security configuration
func (cl *ConfigLoader) loadSecurityConfig() (*SecurityConfig, error) {
	configPath := filepath.Join(cl.configDir, "security.yaml")
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}

	var securityData struct {
		Security SecurityConfig `yaml:"security"`
	}
	
	if err := yaml.Unmarshal(data, &securityData); err != nil {
		return nil, err
	}

	return &securityData.Security, nil
}

// mergeConfigs merges scenario overrides into the main configuration
func (cl *ConfigLoader) mergeConfigs(main, override *SystemConfig) error {
	// This is a simplified merge - in production, you'd want a more sophisticated merge
	// that handles nested structures properly
	
	if override.System.Environment != "" {
		main.System.Environment = override.System.Environment
	}
	
	// Merge services
	if override.Services.CoreOrchestrator.Workers != 0 {
		main.Services.CoreOrchestrator.Workers = override.Services.CoreOrchestrator.Workers
	}
	
	// Add more merge logic as needed for other fields
	
	return nil
}

// expandEnvironmentVariables expands ${VAR} patterns in configuration values
func (cl *ConfigLoader) expandEnvironmentVariables(config *SystemConfig) error {
	// Expand database credentials
	config.Database.Username = os.ExpandEnv(config.Database.Username)
	config.Database.Password = os.ExpandEnv(config.Database.Password)
	
	// Expand Redis password
	config.Redis.Password = os.ExpandEnv(config.Redis.Password)
	
	// Expand provider API keys
	for i := range config.Providers {
		config.Providers[i].Auth.Token = os.ExpandEnv(config.Providers[i].Auth.Token)
	}
	
	// Expand security settings
	config.Security.Authentication.JWT.Secret = os.ExpandEnv(config.Security.Authentication.JWT.Secret)
	
	for provider := range config.Security.Authentication.OAuth2 {
		oauth := config.Security.Authentication.OAuth2[provider]
		oauth.ClientID = os.ExpandEnv(oauth.ClientID)
		oauth.ClientSecret = os.ExpandEnv(oauth.ClientSecret)
		config.Security.Authentication.OAuth2[provider] = oauth
	}
	
	config.Security.Authentication.APIKeys.EncryptionKey = os.ExpandEnv(config.Security.Authentication.APIKeys.EncryptionKey)
	
	return nil
}

// Example usage function
func ExampleUsage() {
	// Initialize the configuration loader
	loader := NewConfigLoader("./config")
	
	// Load configuration for development scenario
	config, err := loader.LoadConfig("Local Development Setup")
	if err != nil {
		fmt.Printf("Error loading config: %v\n", err)
		return
	}
	
	// Use the configuration
	fmt.Printf("System: %s v%s (%s)\n", 
		config.System.Name, 
		config.System.Version, 
		config.System.Environment)
	
	fmt.Printf("Core Orchestrator: %s:%d (workers: %d)\n",
		config.Services.CoreOrchestrator.Host,
		config.Services.CoreOrchestrator.Port,
		config.Services.CoreOrchestrator.Workers)
	
	fmt.Printf("Database: %s@%s:%d/%s\n",
		config.Database.Username,
		config.Database.Host,
		config.Database.Port,
		config.Database.Name)
	
	fmt.Printf("Providers: %d configured\n", len(config.Providers))
	for _, provider := range config.Providers {
		fmt.Printf("  - %s (%s) - Priority: %d, Enabled: %t\n",
			provider.Name,
			provider.Type,
			provider.Priority,
			provider.Enabled)
	}
	
	fmt.Printf("Stealth Profiles: %d configured\n", len(config.Stealth))
	for _, profile := range config.Stealth {
		fmt.Printf("  - %s: %s\n", profile.Name, profile.Description)
	}
}
