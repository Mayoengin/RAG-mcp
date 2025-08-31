# src/network_rag/inbound/mcp_server.py
"""MCP (Model Context Protocol) server adapter for LLM integration - Simplified"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..controller.query_controller import QueryController
from ..controller.document_controller import DocumentController


class MCPServerAdapter:
    """Simplified MCP server adapter providing LLM tool interface for the Network RAG system"""
    
    def __init__(
        self,
        query_controller: QueryController,
        document_controller: DocumentController,
        server_name: str = "NetworkRAG",
        server_version: str = "1.0.0"
    ):
        self.query_controller = query_controller
        self.document_controller = document_controller
        self.server_name = server_name
        self.server_version = server_version
        
        # MCP protocol state
        self.capabilities = {
            "tools": {
                "network_query": "Execute intelligent network queries with multi-source data fusion",
                "list_network_devices": "List network devices with filtering options",
                "get_device_details": "Get detailed information about specific network devices"
            }
        }
    
    async def _execute_network_query(self, arguments: Dict[str, Any]) -> str:
        """Execute the main network query"""
        query = arguments.get("query", "")
        include_recommendations = arguments.get("include_recommendations", True)
        
        if not query:
            return "Error: No query provided"
        
        try:
            response = await self.query_controller.execute_intelligent_network_query({
                "query": query,
                "include_recommendations": include_recommendations
            })
            return response
        except Exception as e:
            return f"Query execution error: {str(e)}"
    
    async def _execute_list_devices(self, arguments: Dict[str, Any]) -> str:
        """List network devices with optional filtering"""
        device_type = arguments.get("device_type", "ftth_olt")
        region = arguments.get("region")
        environment = arguments.get("environment") 
        limit = arguments.get("limit", 50)
        
        try:
            filters = {}
            if region:
                filters["region"] = region.upper()
            if environment:
                filters["environment"] = environment.upper()
                
            if device_type == "ftth_olt":
                devices = await self.query_controller.network_port.fetch_ftth_olts(filters)
                device_list = [device.get_health_summary() for device in devices[:limit]]
                
                response_parts = [
                    f"# Network Device List\n",
                    f"**Device Type:** {device_type.upper()}\n",
                    f"**Count:** {len(device_list)}\n"
                ]
                
                if filters:
                    filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()])
                    response_parts.append(f"**Filters:** {filter_desc}\n")
                
                response_parts.append("\n## Devices\n")
                for i, device in enumerate(device_list, 1):
                    response_parts.append(
                        f"{i}. **{device['name']}** - {device['region']} region, "
                        f"{device['environment']} env, Inmanta: {device['managed_by_inmanta']}\n"
                    )
                
                return "".join(response_parts)
            else:
                return f"Device type '{device_type}' not supported"
                
        except Exception as e:
            return f"Device listing error: {str(e)}"
    
    async def _execute_get_device_details(self, arguments: Dict[str, Any]) -> str:
        """Get detailed information about a specific device"""
        device_name = arguments.get("device_name")
        device_id = arguments.get("device_id")
        
        if not device_name and not device_id:
            return "Error: Either device_name or device_id must be provided"
        
        try:
            if device_name:
                devices = await self.query_controller.network_port.fetch_ftth_olts({"name": device_name})
                device = devices[0] if devices else None
            else:
                device = await self.query_controller.network_port.get_ftth_olt_by_id(device_id)
            
            if not device:
                identifier = device_name or device_id
                return f"Device not found: {identifier}"
            
            health = device.get_health_summary()
            response_parts = [
                f"# Device Details: {device.name}\n\n",
                f"**Region:** {health['region']}\n",
                f"**Environment:** {health['environment']}\n",
                f"**Production:** {'Yes' if health['is_production'] else 'No'}\n",
                f"**Complete Config:** {'Yes' if health['complete_config'] else 'No'}\n",
                f"**Bandwidth:** {health['bandwidth_gbps']} Gbps\n",
                f"**Managed by Inmanta:** {'Yes' if health['managed_by_inmanta'] else 'No'}\n",
                f"**Service Count:** {health['service_count']}\n",
                f"**Completeness Score:** {health['completeness_score']:.1%}\n"
            ]
            
            return "".join(response_parts)
            
        except Exception as e:
            return f"Device details error: {str(e)}"