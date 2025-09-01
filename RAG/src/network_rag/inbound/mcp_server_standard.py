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
from network_rag.services.knowledge_driven_health import KnowledgeDrivenHealthAnalyzer

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
        
        # Use knowledge-driven health analysis
        health_analyzer = KnowledgeDrivenHealthAnalyzer(document_controller)
        
        # Get device summaries using knowledge-based rules
        device_summaries = []
        for device in devices[:10]:  # Limit to 10 devices
            # Analyze health using knowledge base rules
            health = await health_analyzer.analyze_device_health(device, device_type="ftth_olt")
            device_summaries.append(health)
        
        # Build detailed result
        result_parts = [
            f"## Device Listing Result\n",
            f"Found **{len(devices)}** FTTH OLT devices"
        ]
        
        if region:
            result_parts.append(f" in **{region}** region")
        result_parts.append(".\n\n")
        
        # Add device table with enhanced health information
        result_parts.append("### Device Summary with Knowledge-Based Health Analysis\n")
        for i, summary in enumerate(device_summaries, 1):
            # Basic device info
            result_parts.append(f"{i}. **{summary['name']}** ")
            result_parts.append(f"({summary['region']}/{summary['environment']}) - ")
            
            # Health status indicator
            status_emoji = {
                'CRITICAL': '🔴',
                'WARNING': '⚠️',
                'HEALTHY': '✅',
                'UNKNOWN': '❓'
            }.get(summary.get('health_status', 'UNKNOWN'), '❓')
            result_parts.append(f"{status_emoji} {summary.get('health_status', 'UNKNOWN')} ")
            
            # Key metrics
            result_parts.append(f"[Score: {summary.get('health_score', 'N/A')}/100] ")
            result_parts.append(f"{summary.get('bandwidth_gbps', 0)}Gbps, ")
            result_parts.append(f"{summary.get('service_count', 0)} services")
            
            # Add risk level if critical or warning
            if summary.get('risk_level') in ['HIGH_RISK', 'MEDIUM_RISK']:
                result_parts.append(f" ⚡ {summary.get('risk_level', '')}")
            
            result_parts.append("\n")
            
            # Add recommendations if any
            if summary.get('recommendations'):
                for rec in summary['recommendations'][:1]:  # Show first recommendation
                    result_parts.append(f"   └─ {rec}\n")
        
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
        
        # Use knowledge-driven health analysis
        health_analyzer = KnowledgeDrivenHealthAnalyzer(document_controller)
        health = await health_analyzer.analyze_device_health(device, device_type="ftth_olt")
        
        # Health status emoji
        status_emoji = {
            'CRITICAL': '🔴',
            'WARNING': '⚠️',
            'HEALTHY': '✅',
            'UNKNOWN': '❓'
        }.get(health.get('health_status', 'UNKNOWN'), '❓')
        
        result_parts = [
            f"## Device Details: {device_name}\n\n",
            f"### Health Analysis {status_emoji}\n",
            f"**Status:** {health.get('health_status', 'UNKNOWN')}\n",
            f"**Health Score:** {health.get('health_score', 'N/A')}/100\n",
            f"**Risk Level:** {health.get('risk_level', 'UNKNOWN')}\n\n",
            f"### Configuration\n",
            f"**Region:** {health.get('region', 'Unknown')}\n",
            f"**Environment:** {health.get('environment', 'Unknown')}\n",
            f"**Bandwidth:** {health.get('bandwidth_gbps', 0)} Gbps\n",
            f"**Service Count:** {health.get('service_count', 0)}\n",
            f"**Inmanta Managed:** {'Yes' if health.get('managed_by_inmanta') else 'No'}\n",
            f"**Complete Config:** {'Yes' if health.get('complete_config') else 'No'}\n\n"
        ]
        
        # Add recommendations
        if health.get('recommendations'):
            result_parts.append("### Recommendations\n")
            for rec in health['recommendations']:
                result_parts.append(f"• {rec}\n")
            result_parts.append("\n")
        
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

@mcp.tool()
async def manage_health_rules(
    action: str = "list",
    device_type: Optional[str] = None,
    rule_content: Optional[str] = None
) -> str:
    """Manage health analysis rules in the MongoDB knowledge base.
    
    This tool allows viewing, understanding, and managing health rules stored in MongoDB.
    Health rules define how device health is analyzed and scored.
    
    Args:
        action: Action to perform - 'list', 'describe', 'search', or 'status'
        device_type: Type of device rules to manage (ftth_olt, mobile_modem, etc.)
        rule_content: Reserved for future rule updates (not implemented yet)
        
    Returns:
        Information about health rules or operation result
    """
    if not document_controller:
        return "Error: Document controller not initialized"
    
    try:
        if action == "list":
            # List health rules from MongoDB knowledge base
            response_parts = [
                "# Health Analysis Rules in MongoDB Knowledge Base\n\n"
            ]
            
            # Search for health rules in MongoDB
            health_docs = await document_controller.search_documents(
                query="health analysis framework rules",
                limit=10,
                use_vector_search=True
            )
            
            if not health_docs:
                return "No health analysis rules found in MongoDB knowledge base. Run system initialization to load them."
            
            rules_found = 0
            for doc in health_docs:
                doc_title = doc.title if hasattr(doc, 'title') else str(doc.get('title', ''))
                doc_id = doc.id if hasattr(doc, 'id') else doc.get('id', '')
                
                # Skip executable rules metadata documents
                if '_executable' in doc_id:
                    continue
                
                if 'health' in doc_title.lower() and 'analysis' in doc_title.lower():
                    rules_found += 1
                    response_parts.append(f"## {doc_title}\n")
                    response_parts.append(f"- **ID:** {doc_id}\n")
                    
                    # Try to determine device type from content
                    doc_content = doc.content if hasattr(doc, 'content') else doc.get('content', '')
                    if 'ftth_olt' in doc_content.lower() or 'ftth olt' in doc_content.lower():
                        response_parts.append(f"- **Device Type:** FTTH OLT\n")
                    elif 'mobile_modem' in doc_content.lower() or 'mobile modem' in doc_content.lower():
                        response_parts.append(f"- **Device Type:** Mobile Modem\n")
                    elif 'environment' in doc_content.lower() and 'specific' in doc_content.lower():
                        response_parts.append(f"- **Device Type:** Environment-Specific Rules\n")
                    
                    # Show keywords
                    keywords = getattr(doc, 'keywords', []) or doc.get('keywords', [])
                    if keywords:
                        response_parts.append(f"- **Keywords:** {', '.join(keywords[:5])}\n")
                    
                    # Show usefulness score
                    score = getattr(doc, 'usefulness_score', None) or doc.get('usefulness_score')
                    if score:
                        response_parts.append(f"- **Quality Score:** {score:.2f}\n")
                    
                    response_parts.append("\n")
            
            if rules_found == 0:
                return "No health analysis rules found in MongoDB. The documents may not be properly tagged."
            
            response_parts.append(f"📊 **Total Rules Found:** {rules_found}\n")
            response_parts.append(f"💾 **Storage:** MongoDB Knowledge Base\n")
            
            return "".join(response_parts)
        
        elif action == "describe" and device_type:
            # Describe specific device type rules from MongoDB
            search_query = f"health analysis rules {device_type}"
            health_docs = await document_controller.search_documents(
                query=search_query,
                limit=3,
                use_vector_search=True
            )
            
            if not health_docs:
                return f"No health rules found for device type '{device_type}' in MongoDB knowledge base."
            
            # Find the best matching document
            best_doc = None
            for doc in health_docs:
                doc_title = doc.title if hasattr(doc, 'title') else str(doc.get('title', ''))
                if device_type.lower() in doc_title.lower():
                    best_doc = doc
                    break
            
            if not best_doc:
                best_doc = health_docs[0]  # Use first document as fallback
            
            doc_title = best_doc.title if hasattr(best_doc, 'title') else best_doc.get('title', 'Unknown')
            doc_content = best_doc.content if hasattr(best_doc, 'content') else best_doc.get('content', '')
            doc_id = best_doc.id if hasattr(best_doc, 'id') else best_doc.get('id', '')
            
            response_parts = [
                f"# Health Rules: {doc_title}\n\n",
                f"**Document ID:** {doc_id}\n",
                f"**Source:** MongoDB Knowledge Base\n\n",
                "## Rule Content\n",
                f"{doc_content}\n\n"
            ]
            
            # Try to find executable rules metadata
            executable_docs = await document_controller.search_documents(
                query=f"executable rules {doc_id}",
                limit=2
            )
            
            for exec_doc in executable_docs:
                exec_content = exec_doc.content if hasattr(exec_doc, 'content') else exec_doc.get('content', '')
                if 'executable_rules' in exec_content:
                    try:
                        import json
                        metadata = json.loads(exec_content)
                        if 'executable_rules' in metadata:
                            exec_rules = metadata['executable_rules']
                            
                            response_parts.append("## Executable Rules (from MongoDB)\n")
                            
                            if 'summary_fields' in exec_rules:
                                response_parts.append("### Extracted Fields\n")
                                for field in exec_rules['summary_fields']:
                                    response_parts.append(f"- {field}\n")
                                response_parts.append("\n")
                            
                            if 'health_conditions' in exec_rules:
                                response_parts.append("### Health Conditions\n")
                                for status, conditions in exec_rules['health_conditions'].items():
                                    response_parts.append(f"**{status}:**\n")
                                    for cond in conditions[:2]:
                                        if isinstance(cond, dict):
                                            if 'condition' in cond:
                                                response_parts.append(f"- {cond['condition']}\n")
                                            else:
                                                field = cond.get('field', '')
                                                op = cond.get('operator', '')
                                                val = cond.get('value', '')
                                                response_parts.append(f"- {field} {op} {val}\n")
                                    response_parts.append("\n")
                            break
                    except json.JSONDecodeError:
                        continue
            
            return "".join(response_parts)
        
        elif action == "search":
            # Search for health rules by keyword
            search_term = device_type or "health"
            search_results = await document_controller.search_documents(
                query=f"{search_term} health rules",
                limit=5
            )
            
            response_parts = [f"# Search Results for '{search_term}'\n\n"]
            
            for doc in search_results:
                doc_title = doc.title if hasattr(doc, 'title') else str(doc.get('title', ''))
                doc_id = doc.id if hasattr(doc, 'id') else doc.get('id', '')
                
                if 'health' in doc_title.lower():
                    response_parts.append(f"- **{doc_title}** (ID: {doc_id})\n")
            
            return "".join(response_parts)
        
        elif action == "status":
            # Show status of health rules system
            response_parts = [
                "# Health Rules System Status\n\n",
                "## Knowledge Base Integration\n",
                "✅ **Storage:** MongoDB Knowledge Base\n",
                "✅ **Search:** Vector and keyword search enabled\n",
                "✅ **Caching:** Rule caching for performance\n",
                "✅ **Dynamic Loading:** Rules loaded from database at runtime\n\n"
            ]
            
            # Test search capability
            test_search = await document_controller.search_documents(
                query="health analysis",
                limit=1
            )
            
            if test_search:
                response_parts.append("✅ **Search Test:** Health rules found in knowledge base\n")
            else:
                response_parts.append("⚠️  **Search Test:** No health rules found - may need initialization\n")
            
            return "".join(response_parts)
        
        else:
            return """Supported actions:
- 'list': View all health rules in MongoDB
- 'describe': View specific device type rules (specify device_type)
- 'search': Search health rules by keyword (use device_type as search term)  
- 'status': Show health rules system status

Example: manage_health_rules(action="describe", device_type="ftth_olt")"""
            
    except Exception as e:
        return f"Health rule management error: {str(e)}"

if __name__ == "__main__":
    # This will be called when running the server directly
    mcp.run()