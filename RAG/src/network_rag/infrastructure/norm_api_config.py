# config/api_config.py
"""
API configuration management for Service Resource Agent.
Handles API endpoints, authentication, rate limiting, and connection settings.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ApiEnvironment(Enum):
    """API environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


@dataclass
class ApiEndpoint:
    """API endpoint configuration"""
    name: str
    url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 60


@dataclass
class ApiConfig:
    """Complete API configuration"""
    environment: ApiEnvironment
    base_url: str
    api_key: str
    endpoints: Dict[str, ApiEndpoint]
    default_timeout: int = 30
    default_max_retries: int = 3
    default_rate_limit: int = 60


class ApiConfigManager:
    """
    Manages API configurations for different environments and services.
    """
    
    # Default API configurations
    DEFAULT_CONFIGS = {
        ApiEnvironment.DEVELOPMENT: {
            "base_url": "http://normapi-devel.prd.inet.telenet.be:8123/service/resource/v2",
            "api_key": "cf712662-0816-11e4-8730-0050568546d8",
            "timeout": 60,
            "rate_limit": 30
        },
        ApiEnvironment.STAGING: {
            "base_url": "https://normapi-staging.prd.inet.telenet.be:9123/service/resource/v2", 
            "api_key": "staging-api-key-here",
            "timeout": 45,
            "rate_limit": 45
        },
        ApiEnvironment.PRODUCTION: {
            "base_url": "https://normapi.prd.inet.telenet.be:9123/service/resource/v2",
            "api_key": "production-api-key-here", 
            "timeout": 30,
            "rate_limit": 60
        }
    }
    
    # Resource endpoint definitions
    RESOURCE_ENDPOINTS = {
        "ftth_olt": ApiEndpoint(
            name="ftth_olt",
            url="/ftth_olt",
            timeout=45,  # FTTH OLT queries can be complex
            max_retries=2,
            rate_limit_per_minute=30  # Conservative for complex queries
        ),
        "lag": ApiEndpoint(
            name="lag", 
            url="/lag",
            timeout=20,
            max_retries=3,
            rate_limit_per_minute=60
        ),
        "pxc": ApiEndpoint(
            name="pxc",
            url="/pxc", 
            timeout=25,
            max_retries=3,
            rate_limit_per_minute=45
        ),
        "circuit": ApiEndpoint(
            name="circuit",
            url="/circuit",
            timeout=30,
            max_retries=2,
            rate_limit_per_minute=40
        ),
        "team": ApiEndpoint(
            name="team",
            url="/team",
            timeout=15,
            max_retries=3,
            rate_limit_per_minute=100  # Simple endpoint
        ),
        "mobile_modem": ApiEndpoint(
            name="mobile_modem",
            url="/mobile_modem", 
            timeout=20,
            max_retries=3,
            rate_limit_per_minute=50
        )
    }
    
    def __init__(self):
        """Initialize API configuration manager"""
        self._current_config: Optional[ApiConfig] = None
        self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # Determine environment
        env_str = os.getenv('API_ENVIRONMENT', 'development').lower()
        try:
            environment = ApiEnvironment(env_str)
        except ValueError:
            environment = ApiEnvironment.DEVELOPMENT
        
        # Get base configuration
        default_config = self.DEFAULT_CONFIGS[environment]
        
        # Override with environment variables
        base_url = os.getenv('RESOURCE_API_BASE_URL', default_config['base_url'])
        api_key = os.getenv('RESOURCE_API_KEY', default_config['api_key'])
        timeout = int(os.getenv('API_DEFAULT_TIMEOUT', default_config['timeout']))
        rate_limit = int(os.getenv('API_RATE_LIMIT_PER_MINUTE', default_config['rate_limit']))
        max_retries = int(os.getenv('API_MAX_RETRIES', 3))
        
        # Build endpoint configurations
        endpoints = {}
        for resource_name, endpoint_template in self.RESOURCE_ENDPOINTS.items():
            # Allow per-resource overrides
            resource_timeout = int(os.getenv(
                f'API_{resource_name.upper()}_TIMEOUT', 
                endpoint_template.timeout
            ))
            resource_rate_limit = int(os.getenv(
                f'API_{resource_name.upper()}_RATE_LIMIT',
                endpoint_template.rate_limit_per_minute
            ))
            
            endpoints[resource_name] = ApiEndpoint(
                name=endpoint_template.name,
                url=endpoint_template.url,
                api_key=api_key,
                timeout=resource_timeout,
                max_retries=endpoint_template.max_retries,
                rate_limit_per_minute=resource_rate_limit
            )
        
        # Create final configuration
        self._current_config = ApiConfig(
            environment=environment,
            base_url=base_url,
            api_key=api_key,
            endpoints=endpoints,
            default_timeout=timeout,
            default_max_retries=max_retries,
            default_rate_limit=rate_limit
        )
    
    def get_config(self) -> ApiConfig:
        """Get current API configuration"""
        if self._current_config is None:
            self._load_from_environment()
        return self._current_config
    
    def get_endpoint_config(self, resource_name: str) -> Optional[ApiEndpoint]:
        """
        Get configuration for a specific resource endpoint.
        
        Args:
            resource_name: Name of the resource (e.g., 'ftth_olt', 'lag')
            
        Returns:
            ApiEndpoint configuration or None if not found
        """
        config = self.get_config()
        return config.endpoints.get(resource_name)
    
    def get_full_url(self, resource_name: str) -> Optional[str]:
        """
        Get the complete URL for a resource endpoint.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            Complete URL string or None if resource not found
        """
        config = self.get_config()
        endpoint = config.endpoints.get(resource_name)
        
        if endpoint:
            return f"{config.base_url.rstrip('/')}{endpoint.url}"
        return None
    
    def get_headers(self, resource_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get HTTP headers for API requests.
        
        Args:
            resource_name: Optional resource name for resource-specific headers
            
        Returns:
            Dictionary of HTTP headers
        """
        config = self.get_config()
        headers = {
            'X-API-Key': config.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'ServiceResourceAgent/1.0'
        }
        
        # Add resource-specific headers if needed
        if resource_name:
            endpoint = config.endpoints.get(resource_name)
            if endpoint and endpoint.api_key:
                headers['X-API-Key'] = endpoint.api_key
        
        return headers
    
    def get_request_config(self, resource_name: str) -> Dict[str, Any]:
        """
        Get complete request configuration for a resource.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            Dictionary with URL, headers, timeout, and other request settings
        """
        config = self.get_config()
        endpoint = config.endpoints.get(resource_name)
        
        if not endpoint:
            # Fallback configuration
            return {
                'url': f"{config.base_url}/{resource_name}",
                'headers': self.get_headers(),
                'timeout': config.default_timeout,
                'max_retries': config.default_max_retries
            }
        
        return {
            'url': self.get_full_url(resource_name),
            'headers': self.get_headers(resource_name),
            'timeout': endpoint.timeout,
            'max_retries': endpoint.max_retries,
            'rate_limit_per_minute': endpoint.rate_limit_per_minute
        }
    
    def update_config(self, **kwargs):
        """
        Update current configuration with new values.
        
        Args:
            **kwargs: Configuration values to update
        """
        if 'base_url' in kwargs:
            self._current_config.base_url = kwargs['base_url']
        if 'api_key' in kwargs:
            self._current_config.api_key = kwargs['api_key']
        # Update other fields as needed
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """
        Validate current API configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        config = self.get_config()
        errors = []
        
        # Check required fields
        if not config.base_url:
            errors.append("Base URL is not configured")
        
        if not config.api_key or config.api_key == 'your-api-key-here':
            errors.append("API key is not configured or using placeholder value")
        
        # Validate URLs
        if not config.base_url.startswith(('http://', 'https://')):
            errors.append("Base URL must start with http:// or https://")
        
        # Check endpoint configurations
        for name, endpoint in config.endpoints.items():
            if endpoint.timeout <= 0:
                errors.append(f"Invalid timeout for endpoint {name}")
            if endpoint.rate_limit_per_minute <= 0:
                errors.append(f"Invalid rate limit for endpoint {name}")
        
        return len(errors) == 0, errors
    
    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current API environment.
        
        Returns:
            Dictionary with environment information
        """
        config = self.get_config()
        return {
            'environment': config.environment.value,
            'base_url': config.base_url,
            'api_key_configured': bool(config.api_key and config.api_key != 'your-api-key-here'),
            'endpoints_configured': len(config.endpoints),
            'default_timeout': config.default_timeout,
            'default_rate_limit': config.default_rate_limit
        }


# Global configuration manager instance
api_config_manager = ApiConfigManager()


def get_api_config() -> ApiConfig:
    """Get the global API configuration"""
    return api_config_manager.get_config()


def get_endpoint_config(resource_name: str) -> Optional[ApiEndpoint]:
    """Get endpoint configuration for a resource"""
    return api_config_manager.get_endpoint_config(resource_name)


def get_request_config(resource_name: str) -> Dict[str, Any]:
    """Get complete request configuration for a resource"""
    return api_config_manager.get_request_config(resource_name)