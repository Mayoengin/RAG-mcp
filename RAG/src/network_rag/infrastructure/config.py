# src/network_rag/infrastructure/config.py
"""Configuration management for the network RAG system"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from ..models import ConfigurationError


@dataclass
class DatabaseConfig:
    """Database configuration"""
    connection_string: str
    database_name: str = "network_rag"
    max_connections: int = 100
    connection_timeout: int = 30


@dataclass 
class NetworkAPIConfig:
    """Network API configuration"""
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 100


@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "lm_studio"
    base_url: str = "http://localhost:1234"
    model_name: str = "local-model"
    timeout: int = 30
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    model_name: str = "all-MiniLM-L6-v2"
    cache_dir: Optional[str] = None
    max_workers: int = 4
    enable_caching: bool = True
    batch_size: int = 32


@dataclass
class MCPConfig:
    """MCP server configuration"""
    server_name: str = "NetworkRAG"
    server_version: str = "1.0.0"
    host: str = "localhost"
    port: int = 8080
    enable_rest_api: bool = False


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class SystemConfig:
    """Overall system configuration"""
    environment: str = "development"
    debug: bool = False
    data_dir: str = "./data"
    cache_dir: str = "./cache"
    log_dir: str = "./logs"
    
    # Component configurations
    database: DatabaseConfig
    network_api: NetworkAPIConfig
    llm: LLMConfig
    embedding: EmbeddingConfig
    mcp: MCPConfig
    logging: LoggingConfig


class ConfigManager:
    """Configuration manager with environment variable support"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._config: Optional[SystemConfig] = None
    
    def load_config(self) -> SystemConfig:
        """Load configuration from environment variables and files"""
        
        if self._config is not None:
            return self._config
        
        try:
            # Load from environment variables with fallbacks
            config_data = self._load_from_environment()
            
            # Override with config file if provided
            if self.config_file and Path(self.config_file).exists():
                file_config = self._load_from_file(self.config_file)
                config_data.update(file_config)
            
            # Create configuration objects
            self._config = self._create_system_config(config_data)
            
            # Validate configuration
            self._validate_config(self._config)
            
            return self._config
            
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to load configuration: {str(e)}"
            )
    
    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        
        return {
            # System configuration
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "data_dir": os.getenv("DATA_DIR", "./data"),
            "cache_dir": os.getenv("CACHE_DIR", "./cache"),
            "log_dir": os.getenv("LOG_DIR", "./logs"),
            
            # Database configuration
            "database": {
                "connection_string": os.getenv("MONGODB_URI", "mongodb://localhost:27017/network_rag"),
                "database_name": os.getenv("DATABASE_NAME", "network_rag"),
                "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "100")),
                "connection_timeout": int(os.getenv("DB_CONNECTION_TIMEOUT", "30"))
            },
            
            # Network API configuration
            "network_api": {
                "base_url": os.getenv("NETWORK_API_URL", "http://localhost:3000/api"),
                "api_key": os.getenv("NETWORK_API_KEY", ""),
                "timeout": int(os.getenv("NETWORK_API_TIMEOUT", "30")),
                "max_retries": int(os.getenv("NETWORK_API_MAX_RETRIES", "3")),
                "rate_limit_per_minute": int(os.getenv("NETWORK_API_RATE_LIMIT", "100"))
            },
            
            # LLM configuration
            "llm": {
                "provider": os.getenv("LLM_PROVIDER", "lm_studio"),
                "base_url": os.getenv("LM_STUDIO_API_URL", "http://localhost:1234"),
                "model_name": os.getenv("LLM_MODEL_NAME", "local-model"),
                "timeout": int(os.getenv("LLM_TIMEOUT", "30")),
                "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "4096")),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7"))
            },
            
            # Embedding configuration
            "embedding": {
                "model_name": os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                "cache_dir": os.getenv("EMBEDDING_CACHE_DIR"),
                "max_workers": int(os.getenv("EMBEDDING_MAX_WORKERS", "4")),
                "enable_caching": os.getenv("EMBEDDING_CACHING", "true").lower() == "true",
                "batch_size": int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
            },
            
            # MCP configuration
            "mcp": {
                "server_name": os.getenv("MCP_SERVER_NAME", "NetworkRAG"),
                "server_version": os.getenv("MCP_SERVER_VERSION", "1.0.0"),
                "host": os.getenv("MCP_HOST", "localhost"),
                "port": int(os.getenv("MCP_PORT", "8080")),
                "enable_rest_api": os.getenv("ENABLE_REST_API", "false").lower() == "true"
            },
            
            # Logging configuration
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                "file_path": os.getenv("LOG_FILE_PATH"),
                "max_file_size_mb": int(os.getenv("LOG_MAX_FILE_SIZE_MB", "10")),
                "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
            }
        }
    
    def _load_from_file(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON or YAML file"""
        
        file_path = Path(config_file)
        
        if not file_path.exists():
            raise ConfigurationError(
                config_key="config_file",
                message=f"Configuration file not found: {config_file}"
            )
        
        try:
            if file_path.suffix.lower() == '.json':
                import json
                with open(file_path, 'r') as f:
                    return json.load(f)
            
            elif file_path.suffix.lower() in ['.yml', '.yaml']:
                try:
                    import yaml
                    with open(file_path, 'r') as f:
                        return yaml.safe_load(f)
                except ImportError:
                    raise ConfigurationError(
                        config_key="yaml_support",
                        message="PyYAML not installed. Install with: pip install pyyaml"
                    )
            
            else:
                raise ConfigurationError(
                    config_key="config_file_format",
                    message=f"Unsupported config file format: {file_path.suffix}"
                )
                
        except Exception as e:
            raise ConfigurationError(
                config_key="config_file",
                message=f"Failed to load config file: {str(e)}"
            )
    
    def _create_system_config(self, config_data: Dict[str, Any]) -> SystemConfig:
        """Create SystemConfig from configuration data"""
        
        # Create component configurations
        database_config = DatabaseConfig(**config_data.get("database", {}))
        network_api_config = NetworkAPIConfig(**config_data.get("network_api", {}))
        llm_config = LLMConfig(**config_data.get("llm", {}))
        embedding_config = EmbeddingConfig(**config_data.get("embedding", {}))
        mcp_config = MCPConfig(**config_data.get("mcp", {}))
        logging_config = LoggingConfig(**config_data.get("logging", {}))
        
        return SystemConfig(
            environment=config_data.get("environment", "development"),
            debug=config_data.get("debug", False),
            data_dir=config_data.get("data_dir", "./data"),
            cache_dir=config_data.get("cache_dir", "./cache"),
            log_dir=config_data.get("log_dir", "./logs"),
            database=database_config,
            network_api=network_api_config,
            llm=llm_config,
            embedding=embedding_config,
            mcp=mcp_config,
            logging=logging_config
        )
    
    def _validate_config(self, config: SystemConfig):
        """Validate configuration values"""
        
        errors = []
        
        # Database validation
        if not config.database.connection_string:
            errors.append("Database connection string is required")
        
        # Network API validation
        if not config.network_api.base_url:
            errors.append("Network API base URL is required")
        
        if not config.network_api.api_key:
            errors.append("Network API key is required")
        
        # LLM validation
        if not config.llm.base_url:
            errors.append("LLM base URL is required")
        
        if config.llm.max_tokens < 100:
            errors.append("LLM max_tokens must be at least 100")
        
        if not (0.0 <= config.llm.temperature <= 2.0):
            errors.append("LLM temperature must be between 0.0 and 2.0")
        
        # Embedding validation
        if not config.embedding.model_name:
            errors.append("Embedding model name is required")
        
        if config.embedding.max_workers < 1:
            errors.append("Embedding max_workers must be at least 1")
        
        # MCP validation
        if not (1000 <= config.mcp.port <= 65535):
            errors.append("MCP port must be between 1000 and 65535")
        
        # Directory validation
        directories = [config.data_dir, config.cache_dir, config.log_dir]
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {directory}: {str(e)}")
        
        if errors:
            raise ConfigurationError(
                message=f"Configuration validation failed: {'; '.join(errors)}"
            )
    
    def get_config(self) -> SystemConfig:
        """Get loaded configuration"""
        
        if self._config is None:
            return self.load_config()
        
        return self._config
    
    def reload_config(self) -> SystemConfig:
        """Reload configuration"""
        
        self._config = None
        return self.load_config()
    
    def update_config(self, **kwargs):
        """Update configuration values"""
        
        if self._config is None:
            self.load_config()
        
        # Update configuration values
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        
        # Re-validate
        self._validate_config(self._config)


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> SystemConfig:
    """Get system configuration"""
    return config_manager.get_config()


def load_config(config_file: Optional[str] = None) -> SystemConfig:
    """Load configuration from file"""
    global config_manager
    config_manager = ConfigManager(config_file)
    return config_manager.load_config()


def reload_config() -> SystemConfig:
    """Reload configuration"""
    return config_manager.reload_config()