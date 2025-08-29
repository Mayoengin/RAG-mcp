# src/network_rag/infrastructure/container.py
"""Dependency injection container for the network RAG system"""

import asyncio
from typing import Dict, Any, Optional, TypeVar, Type, Callable
from functools import lru_cache

from .config import get_config, SystemConfig
from ..models import ConfigurationError, NetworkRAGException

# Import all adapters and controllers
from ..outbound.mongodb_adapter import MongoDBAdapter
from ..outbound.network_api_adapter import NetworkAPIAdapter
from ..outbound.lm_studio_adapter import LMStudioAdapter
from ..outbound.embedding_adapter import SentenceTransformersAdapter
from ..inbound.mcp_server import MCPServerAdapter

from ..controller.query_controller import QueryController
from ..controller.document_controller import DocumentController
from ..controller.learning_controller import LearningController
from ..controller.validation_controller import ValidationController

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container with lazy initialization and lifecycle management"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._initialized = False
        
        # Register service factories
        self._register_factories()
    
    def _register_factories(self):
        """Register service factory functions"""
        
        # Infrastructure adapters
        self._factories["mongodb_adapter"] = self._create_mongodb_adapter
        self._factories["network_api_adapter"] = self._create_network_api_adapter
        self._factories["lm_studio_adapter"] = self._create_lm_studio_adapter
        self._factories["embedding_adapter"] = self._create_embedding_adapter
        
        # Business controllers
        self._factories["query_controller"] = self._create_query_controller
        self._factories["document_controller"] = self._create_document_controller
        self._factories["learning_controller"] = self._create_learning_controller
        self._factories["validation_controller"] = self._create_validation_controller
        
        # Inbound adapters
        self._factories["mcp_server"] = self._create_mcp_server
    
    async def initialize(self):
        """Initialize the container and core services"""
        
        if self._initialized:
            return
        
        try:
            # Initialize core infrastructure adapters first
            await self._initialize_infrastructure()
            
            # Then initialize business controllers
            await self._initialize_controllers()
            
            # Finally initialize inbound adapters
            await self._initialize_inbound_adapters()
            
            self._initialized = True
            
        except Exception as e:
            await self._cleanup_on_failure()
            raise ConfigurationError(
                message=f"Container initialization failed: {str(e)}"
            )
    
    async def _initialize_infrastructure(self):
        """Initialize infrastructure adapters"""
        
        # Initialize MongoDB adapter
        mongodb = await self.get_service("mongodb_adapter")
        await mongodb.initialize()
        
        # Initialize embedding adapter
        embedding = await self.get_service("embedding_adapter")
        await embedding.initialize()
        
        # Initialize LM Studio adapter (no explicit initialization needed)
        await self.get_service("lm_studio_adapter")
        
        # Initialize network API adapter (no explicit initialization needed)
        await self.get_service("network_api_adapter")
    
    async def _initialize_controllers(self):
        """Initialize business controllers"""
        
        # Controllers don't need async initialization, but we get them to ensure creation
        await self.get_service("query_controller")
        await self.get_service("document_controller")
        await self.get_service("learning_controller")
        await self.get_service("validation_controller")
    
    async def _initialize_inbound_adapters(self):
        """Initialize inbound adapters"""
        
        # Initialize MCP server
        await self.get_service("mcp_server")
    
    async def get_service(self, service_name: str) -> Any:
        """Get service by name with lazy initialization"""
        
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        if service_name not in self._factories:
            raise ConfigurationError(
                config_key="service_name",
                message=f"Unknown service: {service_name}"
            )
        
        try:
            # Create service using factory
            service = await self._create_service(service_name)
            
            # Store as singleton
            self._singletons[service_name] = service
            
            return service
            
        except Exception as e:
            raise ConfigurationError(
                config_key=service_name,
                message=f"Failed to create service {service_name}: {str(e)}"
            )
    
    async def _create_service(self, service_name: str) -> Any:
        """Create service using registered factory"""
        
        factory = self._factories[service_name]
        
        # Handle both sync and async factories
        if asyncio.iscoroutinefunction(factory):
            return await factory()
        else:
            return factory()
    
    # Service factory methods
    
    def _create_mongodb_adapter(self) -> MongoDBAdapter:
        """Create MongoDB adapter"""
        
        return MongoDBAdapter(
            connection_string=self.config.database.connection_string,
            database_name=self.config.database.database_name
        )
    
    def _create_network_api_adapter(self) -> NetworkAPIAdapter:
        """Create network API adapter"""
        
        return NetworkAPIAdapter(
            base_url=self.config.network_api.base_url,
            api_key=self.config.network_api.api_key,
            timeout=self.config.network_api.timeout,
            max_retries=self.config.network_api.max_retries
        )
    
    def _create_lm_studio_adapter(self) -> LMStudioAdapter:
        """Create LM Studio adapter"""
        
        return LMStudioAdapter(
            base_url=self.config.llm.base_url,
            model_name=self.config.llm.model_name,
            timeout=self.config.llm.timeout
        )
    
    def _create_embedding_adapter(self) -> SentenceTransformersAdapter:
        """Create embedding adapter"""
        
        cache_dir = self.config.embedding.cache_dir or f"{self.config.cache_dir}/embeddings"
        
        return SentenceTransformersAdapter(
            model_name=self.config.embedding.model_name,
            cache_dir=cache_dir,
            max_workers=self.config.embedding.max_workers,
            enable_caching=self.config.embedding.enable_caching
        )
    
    async def _create_query_controller(self) -> QueryController:
        """Create query controller with dependencies"""
        
        network_port = await self.get_service("network_api_adapter")
        vector_search_port = await self.get_service("mongodb_adapter")
        llm_port = await self.get_service("lm_studio_adapter")
        conversation_port = await self.get_service("mongodb_adapter")
        
        return QueryController(
            network_port=network_port,
            vector_search_port=vector_search_port,
            llm_port=llm_port,
            conversation_port=conversation_port
        )
    
    async def _create_document_controller(self) -> DocumentController:
        """Create document controller with dependencies"""
        
        knowledge_port = await self.get_service("mongodb_adapter")
        vector_search_port = await self.get_service("mongodb_adapter")
        llm_port = await self.get_service("lm_studio_adapter")
        
        return DocumentController(
            knowledge_port=knowledge_port,
            vector_search_port=vector_search_port,
            llm_port=llm_port
        )
    
    async def _create_learning_controller(self) -> LearningController:
        """Create learning controller with dependencies"""
        
        conversation_port = await self.get_service("mongodb_adapter")
        llm_port = await self.get_service("lm_studio_adapter")
        
        return LearningController(
            conversation_port=conversation_port,
            llm_port=llm_port
        )
    
    def _create_validation_controller(self) -> ValidationController:
        """Create validation controller"""
        
        return ValidationController()
    
    async def _create_mcp_server(self) -> MCPServerAdapter:
        """Create MCP server with dependencies"""
        
        query_controller = await self.get_service("query_controller")
        document_controller = await self.get_service("document_controller")
        learning_controller = await self.get_service("learning_controller")
        validation_controller = await self.get_service("validation_controller")
        
        return MCPServerAdapter(
            query_controller=query_controller,
            document_controller=document_controller,
            learning_controller=learning_controller,
            validation_controller=validation_controller,
            server_name=self.config.mcp.server_name,
            server_version=self.config.mcp.server_version
        )
    
    async def _cleanup_on_failure(self):
        """Cleanup services on initialization failure"""
        
        # Close services that have been created
        for service in self._singletons.values():
            if hasattr(service, 'close'):
                try:
                    if asyncio.iscoroutinefunction(service.close):
                        await service.close()
                    else:
                        service.close()
                except Exception:
                    pass  # Ignore cleanup errors
        
        self._singletons.clear()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        
        health_status = {
            "overall_status": "healthy",
            "services": {},
            "timestamp": "2024-01-01T00:00:00Z"  # Would use real timestamp
        }
        
        # Check MongoDB adapter
        try:
            mongodb = await self.get_service("mongodb_adapter")
            # Basic health check - could check connection
            health_status["services"]["mongodb"] = {
                "status": "healthy",
                "message": "MongoDB adapter operational"
            }
        except Exception as e:
            health_status["services"]["mongodb"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check Network API adapter
        try:
            network_api = await self.get_service("network_api_adapter")
            api_health = await network_api.get_api_health()
            health_status["services"]["network_api"] = {
                "status": api_health.get("status", "unknown"),
                "message": "Network API connectivity checked"
            }
            
            if api_health.get("status") != "healthy":
                health_status["overall_status"] = "degraded"
                
        except Exception as e:
            health_status["services"]["network_api"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check LLM adapter
        try:
            llm = await self.get_service("lm_studio_adapter")
            model_info = await llm.get_model_info()
            health_status["services"]["llm"] = {
                "status": "healthy" if "error" not in model_info else "unhealthy",
                "message": f"LLM model: {model_info.get('model_name', 'unknown')}"
            }
        except Exception as e:
            health_status["services"]["llm"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check embedding adapter
        try:
            embedding = await self.get_service("embedding_adapter")
            embed_info = await embedding.get_model_info()
            health_status["services"]["embedding"] = {
                "status": "healthy" if "error" not in embed_info else "unhealthy",
                "message": f"Embedding model: {embed_info.get('model_name', 'unknown')}"
            }
        except Exception as e:
            health_status["services"]["embedding"] = {
                "status": "unhealthy",
                "message": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        return health_status
    
    async def get_service_info(self) -> Dict[str, Any]:
        """Get information about all services"""
        
        service_info = {
            "container_initialized": self._initialized,
            "services_created": len(self._singletons),
            "available_services": list(self._factories.keys()),
            "created_services": list(self._singletons.keys()),
            "configuration": {
                "environment": self.config.environment,
                "debug": self.config.debug,
                "database_name": self.config.database.database_name,
                "llm_provider": self.config.llm.provider,
                "embedding_model": self.config.embedding.model_name,
                "mcp_server": self.config.mcp.server_name
            }
        }
        
        return service_info
    
    async def close(self):
        """Close container and cleanup all services"""
        
        # Close all services in reverse dependency order
        service_close_order = [
            "mcp_server",
            "learning_controller",
            "document_controller", 
            "query_controller",
            "validation_controller",
            "embedding_adapter",
            "lm_studio_adapter",
            "network_api_adapter",
            "mongodb_adapter"
        ]
        
        for service_name in service_close_order:
            if service_name in self._singletons:
                service = self._singletons[service_name]
                
                try:
                    if hasattr(service, 'close'):
                        if asyncio.iscoroutinefunction(service.close):
                            await service.close()
                        else:
                            service.close()
                except Exception as e:
                    # Log error but continue cleanup
                    print(f"Error closing service {service_name}: {e}")
        
        self._singletons.clear()
        self._initialized = False


class ContainerManager:
    """Global container manager"""
    
    def __init__(self):
        self._container: Optional[ServiceContainer] = None
        self._config: Optional[SystemConfig] = None
    
    async def initialize_container(self, config: Optional[SystemConfig] = None) -> ServiceContainer:
        """Initialize global service container"""
        
        if self._container is not None:
            return self._container
        
        try:
            # Use provided config or load from environment
            if config is None:
                config = get_config()
            
            self._config = config
            
            # Create and initialize container
            self._container = ServiceContainer(config)
            await self._container.initialize()
            
            return self._container
            
        except Exception as e:
            # Cleanup on failure
            if self._container:
                await self._container.close()
                self._container = None
            
            raise NetworkRAGException(
                message=f"Container initialization failed: {str(e)}"
            )
    
    def get_container(self) -> ServiceContainer:
        """Get initialized container"""
        
        if self._container is None:
            raise NetworkRAGException(
                message="Container not initialized. Call initialize_container() first."
            )
        
        return self._container
    
    async def get_service(self, service_name: str) -> Any:
        """Get service from container"""
        
        container = self.get_container()
        return await container.get_service(service_name)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        
        if self._container is None:
            return {
                "overall_status": "not_initialized",
                "message": "Container not initialized"
            }
        
        return await self._container.health_check()
    
    async def shutdown(self):
        """Shutdown container and cleanup"""
        
        if self._container:
            await self._container.close()
            self._container = None
        
        self._config = None


# Global container manager instance
container_manager = ContainerManager()


# Convenience functions
async def initialize_system(config: Optional[SystemConfig] = None) -> ServiceContainer:
    """Initialize the entire system"""
    return await container_manager.initialize_container(config)


def get_container() -> ServiceContainer:
    """Get the initialized service container"""
    return container_manager.get_container()


async def get_service(service_name: str) -> Any:
    """Get service from global container"""
    return await container_manager.get_service(service_name)


async def health_check() -> Dict[str, Any]:
    """Perform system health check"""
    return await container_manager.health_check()


async def shutdown_system():
    """Shutdown the entire system"""
    await container_manager.shutdown()


# Convenience service getters with type hints
async def get_query_controller() -> QueryController:
    """Get query controller"""
    return await get_service("query_controller")


async def get_document_controller() -> DocumentController:
    """Get document controller"""
    return await get_service("document_controller")


async def get_learning_controller() -> LearningController:
    """Get learning controller"""
    return await get_service("learning_controller")


async def get_validation_controller() -> ValidationController:
    """Get validation controller"""
    return await get_service("validation_controller")


async def get_mcp_server() -> MCPServerAdapter:
    """Get MCP server"""
    return await get_service("mcp_server")


# Context manager for system lifecycle
class SystemContext:
    """Context manager for system initialization and cleanup"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config
        self.container: Optional[ServiceContainer] = None
    
    async def __aenter__(self) -> ServiceContainer:
        """Initialize system on context entry"""
        self.container = await initialize_system(self.config)
        return self.container
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup system on context exit"""
        await shutdown_system()
        self.container = None


# Usage example:
# async def main():
#     async with SystemContext() as container:
#         query_controller = await get_query_controller()
#         result = await query_controller.process_query("show me OLTs in HOBO")
#         print(result.primary_answer)