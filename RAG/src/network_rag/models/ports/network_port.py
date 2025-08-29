# src/network_rag/models/ports/network_port.py
"""Network API access port interface"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..ftth_olt_resource import FTTHOLTResource


class NetworkPort(ABC):
    """Interface for network API access and operations"""
    
    @abstractmethod
    async def fetch_ftth_olts(self, filters: Optional[Dict[str, Any]] = None) -> List[FTTHOLTResource]:
        """
        Fetch FTTH OLT resources with optional filters
        
        Args:
            filters: Optional filters like region, environment, managed_by_inmanta
            
        Returns:
            List of FTTHOLTResource objects
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def get_ftth_olt_by_id(self, olt_id: str) -> Optional[FTTHOLTResource]:
        """
        Get specific FTTH OLT by ID
        
        Args:
            olt_id: Unique OLT identifier
            
        Returns:
            FTTHOLTResource if found, None otherwise
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def get_ftth_olt_by_name(self, olt_name: str) -> Optional[FTTHOLTResource]:
        """
        Get specific FTTH OLT by name
        
        Args:
            olt_name: OLT name identifier
            
        Returns:
            FTTHOLTResource if found, None otherwise
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def get_network_status(self, resource_ids: List[str]) -> Dict[str, str]:
        """
        Get real-time status for network resources
        
        Args:
            resource_ids: List of resource identifiers
            
        Returns:
            Dictionary mapping resource_id to status string
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def validate_network_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate network configuration
        
        Args:
            config: Network configuration to validate
            
        Returns:
            Validation result with errors and warnings
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def get_network_statistics(self, resource_id: str, time_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Get network statistics for a resource
        
        Args:
            resource_id: Network resource identifier
            time_range: Optional time range (e.g., "1h", "24h", "7d")
            
        Returns:
            Statistics dictionary
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def search_network_resources(
        self, 
        query: str, 
        resource_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across network resources
        
        Args:
            query: Search query string
            resource_types: Optional list of resource types to search
            limit: Maximum number of results per type
            
        Returns:
            Dictionary mapping resource type to list of matching resources
            
        Raises:
            NetworkAPIError: When API call fails
        """
        pass
    
    @abstractmethod
    async def get_api_health(self) -> Dict[str, Any]:
        """
        Check API health and connectivity
        
        Returns:
            Health status information
            
        Raises:
            NetworkAPIError: When health check fails
        """
        pass