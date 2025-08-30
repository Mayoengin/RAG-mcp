# src/network_rag/outbound/network_api_adapter.py
"""Network API adapter for FTTH OLT and network resource access"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from ..models import FTTHOLTResource, Environment, ConnectionType, NetworkPort, NetworkAPIError
from ..infrastructure.norm_api_config import get_api_config, get_request_config


class NetworkAPIAdapter(NetworkPort):
    """Adapter for network API access and FTTH OLT resource management"""
    
    def __init__(
        self, 
        base_url: str, 
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        
        # Check if using local files instead of API
        self.use_local_files = base_url.startswith("file://") or api_key == "local_files"
        
        # Local JSON file paths
        if self.use_local_files:
            self.local_data_path = Path("/Users/mayo.eid/Desktop/RAG")
            self.local_files = {
                'ftth_olt': self.local_data_path / 'ftth_olt.json',
                'lag': self.local_data_path / 'lag.json',
                'pxc': self.local_data_path / 'pxc.json',
                'circuit': self.local_data_path / 'circuit.json',
                'team': self.local_data_path / 'team.json',
                'mobile_modem': self.local_data_path / 'mobile_modem.json'
            }
        
        # Load NORM API configuration (only if not using local files)
        if not self.use_local_files:
            self.norm_config = get_api_config()
            self.resource_configs = {
                'ftth_olt': get_request_config('ftth_olt'),
                'lag': get_request_config('lag'),
                'pxc': get_request_config('pxc'),
                'circuit': get_request_config('circuit'),
                'team': get_request_config('team'),
                'mobile_modem': get_request_config('mobile_modem')
            }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper headers and timeout"""
        if self.session is None and not self.use_local_files:
            # Use NORM API headers configuration
            from ..infrastructure.norm_api_config import api_config_manager
            headers = api_config_manager.get_headers()
            headers['User-Agent'] = 'NetworkRAG/1.0'
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def _load_local_json(self, resource_type: str) -> List[Dict[str, Any]]:
        """Load data from local JSON file"""
        if not self.use_local_files:
            raise ValueError("Local files not enabled")
        
        file_path = self.local_files.get(resource_type)
        if not file_path or not file_path.exists():
            print(f"Warning: Local file not found: {file_path}")
            return []
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Handle different JSON structures
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'data' in data:
                    return data['data']
                elif isinstance(data, dict):
                    return [data]  # Single object
                else:
                    return []
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")
            return []
    
    async def fetch_ftth_olts(self, filters: Optional[Dict[str, Any]] = None) -> List[FTTHOLTResource]:
        """Fetch FTTH OLT resources with optional filters"""
        
        # Use local files if configured
        if self.use_local_files:
            try:
                raw_olts = await self._load_local_json('ftth_olt')
                
                # Convert raw data to domain models
                olts = []
                for raw_olt in raw_olts:
                    try:
                        olt = self._convert_raw_to_domain_model(raw_olt)
                        
                        # Apply client-side filtering if needed
                        if self._matches_filters(olt, filters):
                            olts.append(olt)
                    
                    except Exception as e:
                        # Log conversion error but continue processing others
                        print(f"Warning: Failed to convert OLT {raw_olt.get('name', 'unknown')}: {e}")
                        continue
                
                return olts
                
            except Exception as e:
                raise NetworkAPIError(
                    api_endpoint="local_file:ftth_olt.json",
                    message=f"Local file fetch failed: {str(e)}"
                )
        
        # Original API logic
        session = await self._get_session()
        
        for attempt in range(self.max_retries):
            try:
                # Build query parameters from filters
                params = self._build_query_params(filters)
                
                # Use NORM API configuration for FTTH OLT endpoint
                ftth_olt_config = self.resource_configs.get('ftth_olt')
                api_url = ftth_olt_config['url'] if ftth_olt_config else f"{self.base_url}/ftth_olt"
                
                async with session.get(api_url, params=params) as response:
                    await self._check_response_status(response, "fetch_ftth_olts")
                    
                    data = await response.json()
                    raw_olts = data.get("data", [])
                    
                    # Convert raw data to domain models
                    olts = []
                    for raw_olt in raw_olts:
                        try:
                            olt = self._convert_raw_to_domain_model(raw_olt)
                            
                            # Apply client-side filtering if needed
                            if self._matches_filters(olt, filters):
                                olts.append(olt)
                        
                        except Exception as e:
                            # Log conversion error but continue processing others
                            print(f"Warning: Failed to convert OLT {raw_olt.get('name', 'unknown')}: {e}")
                            continue
                    
                    return olts
                    
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:  # Last attempt
                    raise NetworkAPIError(
                        api_endpoint="/ftth_olt",
                        message=f"Network request failed after {self.max_retries} attempts: {str(e)}"
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
                
            except Exception as e:
                raise NetworkAPIError(
                    api_endpoint="/ftth_olt",
                    message=f"FTTH OLT fetch failed: {str(e)}"
                )
    
    async def get_ftth_olt_by_id(self, olt_id: str) -> Optional[FTTHOLTResource]:
        """Get specific FTTH OLT by ID"""
        
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.base_url}/ftth_olt/{olt_id}") as response:
                if response.status == 404:
                    return None
                
                await self._check_response_status(response, "get_ftth_olt_by_id")
                
                data = await response.json()
                return self._convert_raw_to_domain_model(data)
                
        except aiohttp.ClientError as e:
            raise NetworkAPIError(
                api_endpoint=f"/ftth_olt/{olt_id}",
                message=f"Network request failed: {str(e)}"
            )
        except Exception as e:
            raise NetworkAPIError(
                api_endpoint=f"/ftth_olt/{olt_id}",
                message=f"Failed to get OLT by ID: {str(e)}"
            )
    
    async def get_ftth_olt_by_name(self, olt_name: str) -> Optional[FTTHOLTResource]:
        """Get specific FTTH OLT by name"""
        
        # Use fetch with name filter
        try:
            olts = await self.fetch_ftth_olts({"name": olt_name})
            return olts[0] if olts else None
            
        except Exception as e:
            raise NetworkAPIError(
                api_endpoint="/ftth_olt",
                message=f"Failed to get OLT by name: {str(e)}"
            )
    
    async def get_network_status(self, resource_ids: List[str]) -> Dict[str, str]:
        """Get real-time status for network resources"""
        
        session = await self._get_session()
        
        try:
            # For batch status requests, use POST with resource IDs
            payload = {"resource_ids": resource_ids}
            
            async with session.post(f"{self.base_url}/status/batch", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("status_results", {})
                else:
                    # Fallback: individual status requests
                    return await self._get_individual_statuses(resource_ids)
                    
        except Exception as e:
            # Fallback: individual status requests
            try:
                return await self._get_individual_statuses(resource_ids)
            except Exception:
                raise NetworkAPIError(
                    api_endpoint="/status",
                    message=f"Status check failed: {str(e)}"
                )
    
    async def validate_network_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate network configuration"""
        
        session = await self._get_session()
        
        try:
            payload = {"configuration": config}
            
            async with session.post(f"{self.base_url}/validate", json=payload) as response:
                await self._check_response_status(response, "validate_network_config")
                
                data = await response.json()
                return {
                    "is_valid": data.get("valid", False),
                    "errors": data.get("errors", []),
                    "warnings": data.get("warnings", []),
                    "suggestions": data.get("suggestions", [])
                }
                
        except Exception as e:
            raise NetworkAPIError(
                api_endpoint="/validate",
                message=f"Configuration validation failed: {str(e)}"
            )
    
    async def get_network_statistics(
        self, 
        resource_id: str, 
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get network statistics for a resource"""
        
        session = await self._get_session()
        
        try:
            params = {}
            if time_range:
                params["time_range"] = time_range
            
            async with session.get(
                f"{self.base_url}/statistics/{resource_id}", 
                params=params
            ) as response:
                await self._check_response_status(response, "get_network_statistics")
                
                data = await response.json()
                return {
                    "resource_id": resource_id,
                    "time_range": time_range or "1h",
                    "metrics": data.get("metrics", {}),
                    "performance": data.get("performance", {}),
                    "utilization": data.get("utilization", {}),
                    "collected_at": data.get("timestamp", datetime.utcnow().isoformat())
                }
                
        except Exception as e:
            raise NetworkAPIError(
                api_endpoint=f"/statistics/{resource_id}",
                message=f"Statistics retrieval failed: {str(e)}"
            )
    
    async def search_network_resources(
        self, 
        query: str, 
        resource_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Search across network resources"""
        
        session = await self._get_session()
        
        try:
            payload = {
                "query": query,
                "resource_types": resource_types or ["ftth_olt"],
                "limit": limit
            }
            
            async with session.post(f"{self.base_url}/search", json=payload) as response:
                await self._check_response_status(response, "search_network_resources")
                
                data = await response.json()
                
                # Organize results by resource type
                organized_results = {}
                for resource_type in payload["resource_types"]:
                    organized_results[resource_type] = data.get(resource_type, [])
                
                return organized_results
                
        except Exception as e:
            raise NetworkAPIError(
                api_endpoint="/search",
                message=f"Network search failed: {str(e)}"
            )
    
    async def get_api_health(self) -> Dict[str, Any]:
        """Check API health and connectivity using NORM API endpoints"""
        
        # Use local files health check if configured
        if self.use_local_files:
            try:
                start_time = datetime.utcnow()
                
                # Check if local files exist and are readable
                ftth_olt_data = await self._load_local_json('ftth_olt')
                
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                return {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "api_version": "Local JSON Files",
                    "timestamp": end_time.isoformat(),
                    "details": {
                        "data_source": "local_files",
                        "ftth_olt_records": len(ftth_olt_data),
                        "local_files_available": [
                            name for name, path in self.local_files.items()
                            if path.exists()
                        ]
                    }
                }
                
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": f"Local files check failed: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "data_source": "local_files",
                        "local_files_missing": [
                            name for name, path in self.local_files.items()
                            if not path.exists()
                        ]
                    }
                }
        
        # Original API health check
        session = await self._get_session()
        
        try:
            start_time = datetime.utcnow()
            
            # Try FTTH OLT endpoint as health check since NORM might not have /health
            ftth_olt_config = self.resource_configs.get('ftth_olt')
            health_url = ftth_olt_config['url'] if ftth_olt_config else f"{self.base_url}/ftth_olt"
            
            # Add limit=1 to get minimal response for health check
            params = {"limit": 1}
            
            async with session.get(health_url, params=params) as response:
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        "status": "healthy",
                        "response_time_ms": response_time,
                        "api_version": "NORM API v2",
                        "timestamp": end_time.isoformat(),
                        "details": {
                            "endpoint_tested": "ftth_olt",
                            "data_count": len(data.get("data", []) if isinstance(data, dict) else [])
                        }
                    }
                elif response.status == 401:
                    return {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "status_code": response.status,
                        "error": "Authentication failed - check API key",
                        "timestamp": end_time.isoformat()
                    }
                elif response.status == 403:
                    return {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "status_code": response.status,
                        "error": "Access forbidden - check permissions",
                        "timestamp": end_time.isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {
                        "status": "unhealthy",
                        "response_time_ms": response_time,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}: {error_text[:100]}",
                        "timestamp": end_time.isoformat()
                    }
                    
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Helper methods
    
    def _build_query_params(self, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Build query parameters from filters"""
        if not filters:
            return {}
        
        params = {}
        
        # Map domain filters to API parameters
        filter_mapping = {
            "region": "region",
            "environment": "env",
            "managed_by_inmanta": "managed",
            "connection_type": "connection",
            "name": "name"
        }
        
        for domain_key, api_key in filter_mapping.items():
            if domain_key in filters:
                params[api_key] = filters[domain_key]
        
        return params
    
    def _convert_raw_to_domain_model(self, raw_data: Dict[str, Any]) -> FTTHOLTResource:
        """Convert raw API data to domain model"""
        
        try:
            # Map API response to domain model fields
            domain_data = {
                "name": raw_data.get("name", ""),
                "ftth_olt_id": raw_data.get("id", raw_data.get("olt_id", "")),
                "region": raw_data.get("region", ""),
                "environment": Environment(raw_data.get("environment", "TEST")),
                "managed_by_inmanta": raw_data.get("managed_by_inmanta", False),
                "service_configs": raw_data.get("service_configs", {}),
                "created_at": self._parse_datetime(raw_data.get("created_at")),
                "updated_at": self._parse_datetime(raw_data.get("updated_at"))
            }
            
            # Handle connection type mapping
            if "connection_type" in raw_data:
                connection_str = raw_data["connection_type"]
                try:
                    domain_data["connection_type"] = ConnectionType(connection_str)
                except ValueError:
                    # Handle API variations
                    connection_mapping = {
                        "10G": ConnectionType.SINGLE_10G,
                        "10g": ConnectionType.SINGLE_10G,
                        "4x10G": ConnectionType.QUAD_10G,
                        "4x10g": ConnectionType.QUAD_10G,
                        "100G": ConnectionType.SINGLE_100G,
                        "100g": ConnectionType.SINGLE_100G
                    }
                    domain_data["connection_type"] = connection_mapping.get(connection_str)
            
            # Handle host address
            if "host_address" in raw_data:
                domain_data["host_address"] = raw_data["host_address"]
            elif "oam_host" in raw_data:
                domain_data["host_address"] = raw_data["oam_host"]
            elif "management_ip" in raw_data:
                domain_data["host_address"] = raw_data["management_ip"]
            
            return FTTHOLTResource(**domain_data)
            
        except Exception as e:
            raise ValueError(f"Failed to convert raw data to domain model: {e}")
    
    def _matches_filters(self, olt: FTTHOLTResource, filters: Optional[Dict[str, Any]]) -> bool:
        """Check if OLT matches client-side filters"""
        if not filters:
            return True
        
        # Additional client-side filtering for complex criteria
        for key, value in filters.items():
            if key == "bandwidth_min" and olt.calculate_bandwidth_gbps() < value:
                return False
            elif key == "has_complete_config" and value != olt.has_complete_config():
                return False
            elif key == "is_production" and value != olt.is_production():
                return False
        
        return True
    
    async def _get_individual_statuses(self, resource_ids: List[str]) -> Dict[str, str]:
        """Fallback method to get statuses individually"""
        session = await self._get_session()
        statuses = {}
        
        # Use semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)
        
        async def get_single_status(resource_id: str):
            async with semaphore:
                try:
                    async with session.get(f"{self.base_url}/status/{resource_id}") as response:
                        if response.status == 200:
                            data = await response.json()
                            return resource_id, data.get("status", "unknown")
                        else:
                            return resource_id, "error"
                except Exception:
                    return resource_id, "unreachable"
        
        # Execute all status requests concurrently
        tasks = [get_single_status(resource_id) for resource_id in resource_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple):
                resource_id, status = result
                statuses[resource_id] = status
            else:
                # Handle exceptions
                pass
        
        return statuses
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> datetime:
        """Parse datetime string from API response"""
        if not datetime_str:
            return datetime.utcnow()
        
        try:
            # Try common datetime formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",  # ISO with microseconds
                "%Y-%m-%dT%H:%M:%SZ",     # ISO without microseconds
                "%Y-%m-%d %H:%M:%S",      # SQL datetime
                "%Y-%m-%d"                # Date only
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            return datetime.utcnow()
            
        except Exception:
            return datetime.utcnow()
    
    async def _check_response_status(self, response: aiohttp.ClientResponse, operation: str):
        """Check response status and raise appropriate exceptions"""
        if response.status >= 400:
            error_text = await response.text()
            
            if response.status == 401:
                raise NetworkAPIError(
                    api_endpoint=str(response.url),
                    status_code=response.status,
                    message=f"Authentication failed for {operation}"
                )
            elif response.status == 403:
                raise NetworkAPIError(
                    api_endpoint=str(response.url),
                    status_code=response.status,
                    message=f"Access forbidden for {operation}"
                )
            elif response.status == 429:
                raise NetworkAPIError(
                    api_endpoint=str(response.url),
                    status_code=response.status,
                    message=f"Rate limit exceeded for {operation}"
                )
            elif response.status >= 500:
                raise NetworkAPIError(
                    api_endpoint=str(response.url),
                    status_code=response.status,
                    message=f"Server error during {operation}: {error_text}"
                )
            else:
                raise NetworkAPIError(
                    api_endpoint=str(response.url),
                    status_code=response.status,
                    message=f"HTTP {response.status} error during {operation}: {error_text}"
                )
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None