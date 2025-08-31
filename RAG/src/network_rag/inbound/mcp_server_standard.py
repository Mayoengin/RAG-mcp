#!/usr/bin/env python3
"""
Standard MCP-compliant server for Network RAG System
Following official MCP SDK patterns with @mcp.tool decorators
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import re

# Add the src directory to the Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# MCP SDK imports
from mcp.server.fastmcp import FastMCP

# Network RAG imports
from network_rag.controller.query_controller import QueryController
from network_rag.controller.document_controller import DocumentController

# Create the MCP server instance
mcp = FastMCP("network-rag-server")

# Global variables for dependency injection (will be initialized)
query_controller: Optional[QueryController] = None
document_controller: Optional[DocumentController] = None

def initialize_controllers(qc: QueryController, dc: DocumentController):
    """Initialize the global controllers for use in MCP tools"""
    global query_controller, document_controller
    query_controller = qc
    document_controller = dc

@mcp.tool()
async def network_query(
    query: str,
    include_recommendations: bool = True
) -> str:
    """Execute intelligent network queries with multi-source data fusion.
    
    This tool provides comprehensive network analysis using RAG (Retrieval-Augmented Generation)
    combined with real network data. It can handle device inventory queries, specific device lookups,
    and complex network analysis requests.
    
    Args:
        query: The network query to analyze (e.g., "Show me FTTH OLTs in HOBO region")
        include_recommendations: Whether to include knowledge-based recommendations
        
    Returns:
        Formatted analysis with device data, LLM insights, and recommendations
    """
    if not query_controller:
        return "Error: Network RAG system not initialized"
    
    try:
        # Step 1: Get RAG analysis from Query Controller
        analysis_result = await query_controller.execute_intelligent_network_query({
            "query": query,
            "include_recommendations": include_recommendations
        })
        
        # Extract components from RAG analysis
        guidance = analysis_result['guidance']
        
        # Step 2: Build response with RAG metadata
        response_parts = [
            "# Network RAG Analysis\n",
            f"**Query:** {query}\n\n"
        ]
        
        # Add RAG guidance information
        if guidance.get('analysis_type'):
            response_parts.append(f"**Analysis Type:** {guidance['analysis_type']}\n")
            response_parts.append(f"**Confidence:** {guidance.get('confidence', 'UNKNOWN')}\n")
            if guidance.get('reasoning'):
                response_parts.append(f"**Reasoning:** {guidance['reasoning']}\n")
            response_parts.append("\n")
        
        # Step 3: Execute strategy based on analysis type
        analysis_type = guidance.get('analysis_type', 'unknown')
        
        if analysis_type == 'device_listing':
            strategy_result = await _execute_device_listing_strategy(query, guidance)
            response_parts.append(strategy_result)
            
        elif analysis_type == 'device_details':
            strategy_result = await _execute_device_details_strategy(query, guidance)
            response_parts.append(strategy_result)
            
        else:
            # Fallback for unknown analysis types
            response_parts.append(f"## Analysis Result\n")
            response_parts.append(f"The system identified this as a **{analysis_type}** query with ")
            response_parts.append(f"**{guidance.get('confidence', 'unknown')}** confidence.\n\n")
            
            if guidance.get('tool_recommendation'):
                response_parts.append(f"**Recommended Tool:** {guidance['tool_recommendation']}\n\n")
        
        # Step 4: Add recommendations
        if include_recommendations and guidance.get('recommendations'):
            response_parts.append("## Recommendations\n")
            for rec in guidance['recommendations']:
                response_parts.append(f"💡 {rec}\n")
        
        return "".join(response_parts)
        
    except Exception as e:
        return f"Network query execution error: {str(e)}"

@mcp.tool()
async def list_network_devices(
    device_type: str = "ftth_olt",
    region: Optional[str] = None,
    environment: Optional[str] = None,
    limit: int = 50
) -> str:
    """List network devices with filtering options.
    
    Retrieves and displays network devices based on specified criteria.
    Supports filtering by device type, geographical region, and environment.
    
    Args:
        device_type: Type of devices to list (default: ftth_olt)
        region: Filter by region (HOBO, GENT, ROES, ASSE)
        environment: Filter by environment (PRODUCTION, UAT, TEST)
        limit: Maximum number of devices to return (default: 50)
        
    Returns:
        Formatted list of network devices with health summaries
    """
    if not query_controller:
        return "Error: Network RAG system not initialized"
    
    try:
        filters = {}
        if region:
            filters["region"] = region.upper()
        if environment:
            filters["environment"] = environment.upper()
            
        if device_type == "ftth_olt":
            devices = await query_controller.network_port.fetch_ftth_olts(filters)
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

@mcp.tool()
async def get_device_details(
    device_name: Optional[str] = None,
    device_id: Optional[str] = None
) -> str:
    """Get detailed information about specific network devices.
    
    Retrieves comprehensive configuration and status information for a specific
    network device identified by name or ID.
    
    Args:
        device_name: Name of the device to query (e.g., "OLT17PROP01")
        device_id: ID of the device to query (alternative to device_name)
        
    Returns:
        Detailed device configuration, status, and health metrics
    """
    if not query_controller:
        return "Error: Network RAG system not initialized"
        
    if not device_name and not device_id:
        return "Error: Either device_name or device_id must be provided"
    
    try:
        if device_name:
            devices = await query_controller.network_port.fetch_ftth_olts({"name": device_name})
            device = devices[0] if devices else None
        else:
            device = await query_controller.network_port.get_ftth_olt_by_id(device_id)
        
        if not device:
            identifier = device_name or device_id
            return f"Device not found: {identifier}"
        
        health = device.get_health_summary()
        response_parts = [
            f"# Device Details: {device.name}\n\n",
            f"**Region:** {health['region']}\n",
            f"**Environment:** {health['environment']}\n",
            f"**Production:** {'Yes' if health.get('is_production', False) else 'No'}\n",
            f"**Complete Config:** {'Yes' if health['complete_config'] else 'No'}\n",
            f"**Bandwidth:** {health['bandwidth_gbps']} Gbps\n",
            f"**Managed by Inmanta:** {'Yes' if health['managed_by_inmanta'] else 'No'}\n",
            f"**Service Count:** {health['service_count']}\n"
        ]
        
        if 'completeness_score' in health:
            response_parts.append(f"**Completeness Score:** {health['completeness_score']:.1%}\n")
        
        return "".join(response_parts)
        
    except Exception as e:
        return f"Device details error: {str(e)}"

# Helper functions for strategy execution
async def _execute_device_listing_strategy(query: str, guidance: dict) -> str:
    """Execute device listing strategy with LLM analysis"""
    try:
        # Extract region from query
        region = _extract_region_from_query(query)
        
        # Prepare filters
        filters = {}
        if region:
            filters["region"] = region
        
        # Fetch devices
        devices = await query_controller.network_port.fetch_ftth_olts(filters)
        
        if not devices:
            return f"## Device Listing Result\nNo FTTH OLTs found matching your criteria.\n\n"
        
        # Get device summaries
        device_summaries = []
        for device in devices[:10]:  # Limit to 10 devices
            health = device.get_health_summary()
            device_summaries.append({
                "name": health["name"],
                "region": health["region"],
                "environment": health["environment"],
                "bandwidth_gbps": health["bandwidth_gbps"],
                "service_count": health["service_count"],
                "managed_by_inmanta": health["managed_by_inmanta"],
                "complete_config": health["complete_config"]
            })
        
        # Build detailed result
        result_parts = [
            f"## Device Listing Result\n",
            f"Found **{len(devices)}** FTTH OLT devices"
        ]
        
        if region:
            result_parts.append(f" in **{region}** region")
        result_parts.append(".\n\n")
        
        # Add device table
        result_parts.append("### Device Summary\n")
        for i, summary in enumerate(device_summaries, 1):
            result_parts.append(f"{i}. **{summary['name']}** ")
            result_parts.append(f"({summary['region']}/{summary['environment']}) - ")
            result_parts.append(f"{summary['bandwidth_gbps']}Gbps, ")
            result_parts.append(f"{summary['service_count']} services, ")
            result_parts.append(f"Inmanta: {'✅' if summary['managed_by_inmanta'] else '❌'}\n")
        
        if len(devices) > 10:
            result_parts.append(f"\n*Showing first 10 of {len(devices)} devices*\n")
        
        # Generate LLM analysis
        llm_analysis = await _generate_llm_analysis(query, device_summaries, guidance)
        if llm_analysis:
            result_parts.append(f"\n## LLM Analysis\n{llm_analysis}\n")
        
        return "".join(result_parts)
        
    except Exception as e:
        return f"## Device Listing Error\n{str(e)}\n\n"

async def _execute_device_details_strategy(query: str, guidance: dict) -> str:
    """Execute device details strategy"""
    try:
        # Try to extract device name from query
        device_name = _extract_device_name_from_query(query)
        
        if not device_name:
            return f"## Device Details Error\nCould not identify specific device name in query.\n\n"
        
        # Fetch device details
        devices = await query_controller.network_port.fetch_ftth_olts({"name": device_name})
        device = devices[0] if devices else None
        
        if not device:
            return f"## Device Details Error\nDevice '{device_name}' not found.\n\n"
        
        health = device.get_health_summary()
        result_parts = [
            f"## Device Details: {device_name}\n\n",
            f"**Region:** {health['region']}\n",
            f"**Environment:** {health['environment']}\n",
            f"**Bandwidth:** {health['bandwidth_gbps']} Gbps\n",
            f"**Service Count:** {health['service_count']}\n",
            f"**Inmanta Managed:** {'Yes' if health['managed_by_inmanta'] else 'No'}\n",
            f"**Complete Config:** {'Yes' if health['complete_config'] else 'No'}\n\n"
        ]
        
        return "".join(result_parts)
        
    except Exception as e:
        return f"## Device Details Error\n{str(e)}\n\n"

async def _generate_llm_analysis(query: str, device_summaries: list, guidance: dict) -> str:
    """Generate intelligent LLM analysis of network devices"""
    try:
        # Build context for LLM
        context_parts = [
            f"Query: {query}\n",
            f"Analysis Type: {guidance.get('analysis_type', 'unknown')}\n",
            f"Confidence: {guidance.get('confidence', 'unknown')}\n\n",
            "Device Data:\n"
        ]
        
        for i, device in enumerate(device_summaries, 1):
            context_parts.append(f"{i}. {device['name']} - {device['region']}/{device['environment']}\n")
            context_parts.append(f"   Bandwidth: {device['bandwidth_gbps']}Gbps, Services: {device['service_count']}\n")
            context_parts.append(f"   Inmanta: {'Yes' if device['managed_by_inmanta'] else 'No'}, ")
            context_parts.append(f"Complete Config: {'Yes' if device['complete_config'] else 'No'}\n\n")
        
        # Create messages for LLM (using dict format expected by LLM port)
        messages = [
            {
                "role": "system",
                "content": "You are a network infrastructure analyst. Analyze the provided network device data and provide insights, patterns, and recommendations based on the user's query. Focus on practical network engineering insights."
            },
            {
                "role": "user", 
                "content": "".join(context_parts) + f"\nProvide a detailed analysis addressing the query: '{query}'"
            }
        ]
        
        # Generate LLM response
        llm_response = await query_controller.llm_port.generate_response(messages)
        
        if llm_response and len(llm_response.strip()) > 50:  # Valid response
            return llm_response
        else:
            return "LLM analysis not available - using mock data mode or LLM service unavailable."
            
    except Exception as e:
        print(f"LLM analysis failed: {e}")
        return f"LLM analysis error: {str(e)}"

def _extract_region_from_query(query: str) -> Optional[str]:
    """Extract region filter from query"""
    query_lower = query.lower()
    regions = ["hobo", "gent", "roes", "asse"]
    
    for region in regions:
        if region in query_lower:
            return region.upper()
    return None

def _extract_device_name_from_query(query: str) -> Optional[str]:
    """Extract device name from query (simple implementation)"""
    query_upper = query.upper()
    
    # Look for OLT device patterns
    olt_pattern = r'(OLT\d+\w+\d+)'
    match = re.search(olt_pattern, query_upper)
    if match:
        return match.group(1)
    
    # Look for other device patterns
    device_pattern = r'([A-Z]+[A-Z0-9]+\d+)'
    match = re.search(device_pattern, query_upper)
    if match:
        return match.group(1)
    
    return None

if __name__ == "__main__":
    # This will be called when running the server directly
    mcp.run()