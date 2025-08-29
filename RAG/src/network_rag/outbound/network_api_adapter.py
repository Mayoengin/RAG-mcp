# src/network_rag/outbound/network_api_adapter.py
"""Network API adapter for FTTH OLT and network resource access"""

import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import FTTHOLTResource, Environment, ConnectionType, NetworkPort, NetworkAPIError


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
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper headers and timeout"""
        if self.session is None:
            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'NetworkRAG/1.0'
            }
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def fetch_ftth_olts(self, filters: Optional[Dict[str, Any]] = None) -> List[FTTHOLTResource]:
        """Fetch FTTH OLT resources with optional filters"""
        
        session = await self._get_session()
        
        try:
            # Build query parameters from filters
            params = self._build_query_params(filters)
            
            async with session.get(f"{self.base_url}/ftth_olt", params=params) as response:
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
            raise NetworkAPIError(
                api_endpoint="/ftth_olt",
                message=f"Network request failed: {str(e)}"
            )
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
    
    async def validate_network_config(self, config: Dict[str, Any])