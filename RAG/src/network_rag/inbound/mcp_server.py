# src/network_rag/inbound/mcp_server.py
"""MCP (Model Context Protocol) server adapter for LLM integration"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..controller.query_controller import QueryController
from ..controller.document_controller import DocumentController
from ..controller.learning_controller import LearningController
from ..controller.validation_controller import ValidationController
from ..models import NetworkRAGException


class MCPServerAdapter:
    """MCP server adapter providing LLM tool interface for the Network RAG system"""
    
    def __init__(
        self,
        query_controller: QueryController,
        document_controller: DocumentController,
        learning_controller: LearningController,
        validation_controller: ValidationController,
        server_name: str = "NetworkRAG",
        server_version: str = "1.0.0"
    ):
        self.query_controller = query_controller
        self.document_controller = document_controller
        self.learning_controller = learning_controller
        self.validation_controller = validation_controller
        self.server_name = server_name
        self.server_version = server_version
        
        # MCP protocol state
        self.capabilities = self._define_capabilities()
        self.tools = self._define_tools()
        self.active_conversations = {}
        self.request_counter = 0
    
    def _define_capabilities(self) -> Dict[str, Any]:
        """Define MCP server capabilities"""
        return {
            "tools": {
                "supported": True,
                "listChanged": True
            },
            "resources": {
                "supported": False
            },
            "prompts": {
                "supported": False
            },
            "logging": {
                "supported": True
            }
        }
    
    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define available MCP tools"""
        tools = []
        
        # =====================================
        # NETWORK QUERY TOOLS
        # =====================================
        tools.append({
            "name": "query_network_resources",
            "description": "Query and analyze FTTH OLT network resources with intelligent insights",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query for network resources (e.g., 'show OLTs in HOBO production')"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include actionable recommendations in the response",
                        "default": True
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation context"
                    }
                },
                "required": ["query"]
            }
        })
        
        # =====================================
        # KNOWLEDGE BASE TOOLS  
        # =====================================
        tools.append({
            "name": "search_knowledge_base",
            "description": "Search technical documentation and knowledge base using semantic similarity",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for technical documentation"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    },
                    "document_types": {
                        "type": "array",
                        "description": "Filter by document types",
                        "items": {
                            "type": "string",
                            "enum": ["config_guide", "troubleshooting", "best_practices", "api_reference", "network_docs", "user_manual"]
                        }
                    }
                },
                "required": ["query"]
            }
        })
        
        # =====================================
        # VALIDATION TOOLS
        # =====================================
        tools.append({
            "name": "validate_olt_configuration",
            "description": "Validate FTTH OLT configuration and provide compliance analysis",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "olt_name": {
                        "type": "string",
                        "description": "Name of the OLT to validate"
                    },
                    "olt_id": {
                        "type": "string", 
                        "description": "ID of the OLT to validate (alternative to name)"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include improvement recommendations",
                        "default": True
                    }
                },
                "anyOf": [
                    {"required": ["olt_name"]},
                    {"required": ["olt_id"]}
                ]
            }
        })
        
        # =====================================
        # CONVERSATION LEARNING TOOLS
        # =====================================
        tools.append({
            "name": "record_conversation_feedback",
            "description": "Record user feedback on assistant responses for continuous learning",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "string",
                        "description": "Conversation identifier"
                    },
                    "message_id": {
                        "type": "string",
                        "description": "Specific message being rated"
                    },
                    "feedback_type": {
                        "type": "string",
                        "description": "Type of feedback",
                        "enum": ["helpful", "not_helpful", "incorrect", "incomplete", "confusing"]
                    },
                    "rating": {
                        "type": "integer",
                        "description": "Optional numerical rating (1-5)",
                        "minimum": 1,
                        "maximum": 5
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional feedback comment"
                    }
                },
                "required": ["conversation_id", "message_id", "feedback_type"]
            }
        })
        
        # =====================================
        # SYSTEM ANALYTICS TOOLS
        # =====================================
        tools.append({
            "name": "get_system_analytics",
            "description": "Get system performance analytics and learning insights",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "time_range_days": {
                        "type": "integer",
                        "description": "Number of days to analyze",
                        "default": 30,
                        "minimum": 1,
                        "maximum": 365
                    },
                    "analysis_depth": {
                        "type": "string",
                        "description": "Depth of analysis to perform",
                        "enum": ["basic", "comprehensive"],
                        "default": "basic"
                    }
                },
                "required": []
            }
        })
        
        # =====================================
        # SIMPLE NETWORK TOOLS
        # =====================================
        tools.append({
            "name": "list_network_devices",
            "description": "List network devices by type with filtering options",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_type": {
                        "type": "string",
                        "description": "Type of network device",
                        "enum": ["ftth_olt", "lag", "pxc", "mobile_modem", "team", "all"],
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of devices to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "filter": {
                        "type": "string",
                        "description": "Optional filter by name or description"
                    }
                },
                "required": []
            }
        })

        tools.append({
            "name": "get_device_details",
            "description": "Get detailed information about a specific network device",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string", 
                        "description": "Name or ID of the device"
                    },
                    "device_type": {
                        "type": "string",
                        "description": "Type of device to search",
                        "enum": ["ftth_olt", "lag", "pxc", "mobile_modem", "team"],
                        "default": "ftth_olt"
                    }
                },
                "required": ["device_name"]
            }
        })
        
        return tools
    
    async def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP JSON-RPC request"""
        
        self.request_counter += 1
        
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            
            elif method == "tools/list":
                return await self._handle_list_tools(request_id)
            
            elif method == "tools/call":
                return await self._handle_tool_call(request_id, params)
            
            elif method == "logging/setLevel":
                return await self._handle_set_log_level(request_id, params)
            
            else:
                return self._create_error_response(
                    request_id, 
                    -32601, 
                    f"Method not found: {method}"
                )
        
        except Exception as e:
            return self._create_error_response(
                request_id,
                -32603,
                f"Internal error: {str(e)}"
            )
    
    async def _handle_initialize(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion", "2024-11-05")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": self.capabilities,
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version,
                    "description": "Network RAG system providing intelligent network resource analysis and knowledge management"
                }
            }
        }
    
    async def _handle_list_tools(self, request_id: str) -> Dict[str, Any]:
        """Handle tools/list request"""
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.tools
            }
        }
    
    async def _handle_tool_call(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request"""
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            if tool_name == "query_network_resources":
                result = await self._execute_network_query(arguments)
            
            elif tool_name == "search_knowledge_base":
                result = await self._execute_knowledge_search(arguments)
            
            elif tool_name == "validate_olt_configuration":
                result = await self._execute_olt_validation(arguments)
            
            elif tool_name == "record_conversation_feedback":
                result = await self._execute_record_feedback(arguments)
            
            elif tool_name == "get_system_analytics":
                result = await self._execute_system_analytics(arguments)
            
            # =====================================
            # SIMPLE NETWORK TOOL HANDLERS
            # =====================================
            elif tool_name == "list_network_devices":
                result = await self._execute_list_network_devices(arguments)
            
            elif tool_name == "get_device_details":
                result = await self._execute_get_device_details(arguments)
            
            else:
                return self._create_error_response(
                    request_id,
                    -32602,
                    f"Unknown tool: {tool_name}"
                )
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
            
        except Exception as e:
            return self._create_error_response(
                request_id,
                -32603,
                f"Tool execution failed: {str(e)}"
            )
    
    async def _handle_set_log_level(self, request_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logging/setLevel request"""
        
        level = params.get("level", "info")
        
        # In a full implementation, you would actually change the log level
        # For now, just acknowledge the request
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "success": True,
                "level": level
            }
        }
    
    # =====================================
    # TOOL EXECUTION METHODS
    # =====================================
    
    async def _execute_network_query(self, arguments: Dict[str, Any]) -> str:
        """Execute network resource query using actual local data"""
        
        query = arguments.get("query", "")
        include_recommendations = arguments.get("include_recommendations", True)
        session_id = arguments.get("session_id")
        
        response_parts = [
            f"# Network Query Results\n",
            f"**Query:** {query}\n\n"
        ]
        
        try:
            # Get network API adapter directly to fetch real data
            network_adapter = self.query_controller.network_port
            
            # Fetch actual FTTH OLT data from local files
            ftth_olts = await network_adapter.fetch_ftth_olts()
            
            # Also get other device types mentioned in query
            lag_data = await network_adapter._load_local_json('lag') if 'lag' in query.lower() else []
            pxc_data = await network_adapter._load_local_json('pxc') if 'pxc' in query.lower() else []
            mobile_data = await network_adapter._load_local_json('mobile_modem') if 'mobile' in query.lower() else []
            team_data = await network_adapter._load_local_json('team') if 'team' in query.lower() else []
            
            # Format FTTH OLT data
            if ftth_olts or 'ftth' in query.lower() or 'olt' in query.lower():
                response_parts.append("## FTTH OLT Devices Found\n")
                if ftth_olts:
                    for i, olt in enumerate(ftth_olts[:10]):  # Show first 10
                        health = olt.get_health_summary()
                        status_icon = "✅" if health.get('complete_config') else "⚠️"
                        response_parts.extend([
                            f"{status_icon} **{health['name']}**\n",
                            f"   - Environment: {health['environment']}\n",
                            f"   - Bandwidth: {health['bandwidth_gbps']}Gbps\n",
                            f"   - Managed by Inmanta: {'Yes' if health['managed_by_inmanta'] else 'No'}\n",
                            f"   - Service Count: {health['service_count']}\n\n"
                        ])
                else:
                    response_parts.append("No FTTH OLT devices found in local data.\n\n")
            
            # Format LAG data if relevant
            if lag_data:
                response_parts.append("## LAG Devices\n")
                for item in lag_data[:5]:
                    response_parts.extend([
                        f"- **{item.get('device_name', 'Unknown')}** (LAG ID: {item.get('lag_id', 'N/A')})\n",
                        f"  Description: {item.get('description', 'No description')}\n"
                    ])
                response_parts.append("\n")
            
            # Format PXC data if relevant
            if pxc_data:
                response_parts.append("## PXC Devices\n")
                for item in pxc_data[:5]:
                    response_parts.extend([
                        f"- **{item.get('device_name', 'Unknown')}** (PXC ID: {item.get('pxc_id', 'N/A')})\n",
                        f"  Description: {item.get('description', 'No description')}\n"
                    ])
                response_parts.append("\n")
            
            # Format Mobile data if relevant
            if mobile_data:
                response_parts.append("## Mobile Modems\n")
                for item in mobile_data[:5]:
                    response_parts.extend([
                        f"- **{item.get('serial_number', 'Unknown')}** ({item.get('hardware_type', 'Unknown')})\n",
                        f"  Subscriber: {item.get('mobile_subscriber_id', 'N/A')}\n"
                    ])
                response_parts.append("\n")
            
            # Format Team data if relevant
            if team_data:
                response_parts.append("## Teams\n")
                for item in team_data[:5]:
                    response_parts.extend([
                        f"- **{item.get('team_name', 'Unknown')}**\n",
                        f"  ID: {item.get('team_id', 'N/A')}\n"
                    ])
                response_parts.append("\n")
            
            # Add summary
            total_devices = len(ftth_olts) + len(lag_data) + len(pxc_data) + len(mobile_data) + len(team_data)
            response_parts.append(f"**Total devices found:** {total_devices}\n")
            
            # Add recommendations if requested
            if include_recommendations:
                response_parts.append("\n## Recommendations\n")
                if ftth_olts:
                    incomplete_olts = [olt for olt in ftth_olts if not olt.get_health_summary().get('complete_config')]
                    if incomplete_olts:
                        response_parts.append(f"- Review configuration for {len(incomplete_olts)} OLTs with incomplete configs\n")
                    
                    production_olts = [olt for olt in ftth_olts if olt.is_production()]
                    if production_olts:
                        response_parts.append(f"- Monitor {len(production_olts)} production OLTs for performance\n")
                
                response_parts.append("- Use `get_device_details` for specific device information\n")
        
        except Exception as e:
            response_parts.extend([
                "## Error\n",
                f"❌ Failed to retrieve network data: {str(e)}\n",
                "Please check the local JSON files and try again.\n"
            ])
        
        return "".join(response_parts)
    
    async def _execute_knowledge_search(self, arguments: Dict[str, Any]) -> str:
        """Execute knowledge base search"""
        
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        document_types = arguments.get("document_types")
        
        # Search documents
        documents = await self.document_controller.search_documents(
            query=query,
            limit=limit,
            use_vector_search=True
        )
        
        if not documents:
            return f"# Knowledge Base Search\n\nNo documents found matching '{query}'"
        
        # Format response
        response_parts = [
            f"# Knowledge Base Search Results\n",
            f"**Query:** {query}\n",
            f"**Found:** {len(documents)} documents\n\n"
        ]
        
        for i, doc in enumerate(documents, 1):
            response_parts.extend([
                f"## {i}. {doc.title}\n",
                f"**Type:** {doc.document_type.value.replace('_', ' ').title()}\n",
                f"**Quality Score:** {doc.usefulness_score:.2f}\n\n",
                f"{doc.get_content_preview(300)}\n\n"
            ])
            
            if doc.keywords:
                response_parts.append(f"**Keywords:** {', '.join(doc.keywords[:5])}\n\n")
        
        return "".join(response_parts)
    
    async def _execute_olt_validation(self, arguments: Dict[str, Any]) -> str:
        """Execute OLT configuration validation"""
        
        olt_name = arguments.get("olt_name")
        olt_id = arguments.get("olt_id")
        include_recommendations = arguments.get("include_recommendations", True)
        
        # First, get the OLT resource
        if olt_name:
            olt = await self.query_controller.network_port.get_ftth_olt_by_name(olt_name)
        elif olt_id:
            olt = await self.query_controller.network_port.get_ftth_olt_by_id(olt_id)
        else:
            return "# Validation Error\nEither olt_name or olt_id must be provided"
        
        if not olt:
            identifier = olt_name or olt_id
            return f"# OLT Not Found\nNo OLT found with identifier: {identifier}"
        
        # Validate the OLT
        validation_result = self.validation_controller.validate_ftth_olt(olt)
        
        # Format response
        compliance_emoji = "✅" if validation_result["is_valid"] else "❌"
        response_parts = [
            f"# OLT Configuration Validation\n",
            f"**OLT:** {olt.name}\n",
            f"**Status:** {compliance_emoji} {'Valid' if validation_result['is_valid'] else 'Invalid'}\n",
            f"**Compliance Score:** {validation_result['compliance_score']:.1%}\n\n"
        ]
        
        # Add errors
        if validation_result["errors"]:
            response_parts.append("## ❌ Critical Issues\n")
            for error in validation_result["errors"]:
                response_parts.append(f"- {error}\n")
            response_parts.append("\n")
        
        # Add warnings
        if validation_result["warnings"]:
            response_parts.append("## ⚠️ Warnings\n")
            for warning in validation_result["warnings"]:
                response_parts.append(f"- {warning}\n")
            response_parts.append("\n")
        
        # Add recommendations
        if include_recommendations and validation_result["recommendations"]:
            response_parts.append("## 💡 Recommendations\n")
            for rec in validation_result["recommendations"]:
                response_parts.append(f"- {rec}\n")
            response_parts.append("\n")
        
        # Add OLT summary
        health_summary = olt.get_health_summary()
        response_parts.extend([
            "## OLT Summary\n",
            f"- **Environment:** {health_summary['environment']}\n",
            f"- **Bandwidth:** {health_summary['bandwidth_gbps']}Gbps\n",
            f"- **Managed by Inmanta:** {'Yes' if health_summary['managed_by_inmanta'] else 'No'}\n",
            f"- **Service Count:** {health_summary['service_count']}\n"
        ])
        
        return "".join(response_parts)
    
    async def _execute_record_feedback(self, arguments: Dict[str, Any]) -> str:
        """Execute conversation feedback recording"""
        
        conversation_id = arguments.get("conversation_id", "")
        message_id = arguments.get("message_id", "")
        feedback_type = arguments.get("feedback_type", "")
        rating = arguments.get("rating")
        comment = arguments.get("comment")
        
        # Record feedback through learning controller
        from ..models import FeedbackType
        
        try:
            feedback_enum = FeedbackType(feedback_type)
            
            result = await self.learning_controller.process_intelligent_feedback(
                conversation_id=conversation_id,
                message_id=message_id,
                feedback_type=feedback_enum,
                rating=rating,
                comment=comment
            )
            
            if result["feedback_recorded"]:
                response_parts = [
                    "# Feedback Recorded Successfully\n",
                    f"**Type:** {feedback_type.replace('_', ' ').title()}\n"
                ]
                
                if rating:
                    response_parts.append(f"**Rating:** {rating}/5\n")
                
                if comment:
                    response_parts.append(f"**Comment:** {comment}\n")
                
                # Add insights if available
                intelligence = result.get("intelligence_analysis", {})
                if intelligence.get("learning_value"):
                    response_parts.append(f"\n**Learning Value:** {intelligence['learning_value'].title()}\n")
                
                recommendations = result.get("improvement_recommendations", [])
                if recommendations:
                    response_parts.append("\n## System Improvements Identified\n")
                    for rec in recommendations[:3]:
                        response_parts.append(f"- {rec.get('action', 'Improvement identified')}\n")
                
                return "".join(response_parts)
            
            else:
                return "# Feedback Recording Failed\nUnable to record feedback. Please check conversation and message IDs."
        
        except ValueError:
            return f"# Invalid Feedback Type\nFeedback type '{feedback_type}' is not valid. Use: helpful, not_helpful, incorrect, incomplete, or confusing"
        except Exception as e:
            return f"# Feedback Recording Error\n{str(e)}"
    
    async def _execute_system_analytics(self, arguments: Dict[str, Any]) -> str:
        """Execute system analytics"""
        
        time_range_days = arguments.get("time_range_days", 30)
        analysis_depth = arguments.get("analysis_depth", "basic")
        
        # Get analytics from learning controller
        analytics = await self.learning_controller.analyze_conversation_intelligence(
            time_range_days=time_range_days,
            analysis_depth=analysis_depth
        )
        
        # Format response
        response_parts = [
            f"# System Analytics Report\n",
            f"**Analysis Period:** Last {time_range_days} days\n",
            f"**Analysis Depth:** {analysis_depth.title()}\n\n"
        ]
        
        # Base metrics
        base_metrics = analytics["conversation_intelligence"]["base_metrics"]
        if base_metrics:
            total_conversations = base_metrics.get("total_conversations", 0)
            response_parts.extend([
                "## Key Metrics\n",
                f"- **Total Conversations:** {total_conversations}\n"
            ])
        
        # Success factors
        success_factors = analytics["conversation_intelligence"]["success_factors"]
        if success_factors.get("response_characteristics"):
            response_chars = success_factors["response_characteristics"]
            response_parts.extend([
                "\n## Success Factors\n",
                f"- **Optimal Response Length:** {response_chars.get('optimal_length_range', 'Unknown')}\n",
                f"- **Helpful Elements:** {', '.join(response_chars.get('helpful_structural_elements', []))}\n"
            ])
        
        # Learning progress
        learning_progress = analytics["learning_insights"]["learning_progress"]
        if learning_progress:
            trajectory = learning_progress.get("improvement_trajectory", "stable")
            response_parts.extend([
                "\n## Learning Progress\n",
                f"- **Improvement Trajectory:** {trajectory.title()}\n"
            ])
            
            current_focus = learning_progress.get("current_learning_focus", [])
            if current_focus:
                response_parts.append("- **Current Focus Areas:**\n")
                for focus in current_focus[:3]:
                    response_parts.append(f"  - {focus}\n")
        
        # Strategic recommendations
        strategic_recs = analytics["strategic_recommendations"]
        immediate_actions = strategic_recs.get("immediate_actions", [])
        if immediate_actions:
            response_parts.append("\n## Immediate Action Items\n")
            for action in immediate_actions[:3]:
                priority_emoji = "🔴" if action.get("priority") == "critical" else "🟡" if action.get("priority") == "high" else "🟢"
                response_parts.append(f"{priority_emoji} {action.get('action', 'Action item')}\n")
        
        return "".join(response_parts)
    
    # =====================================
    # SIMPLE NETWORK TOOL EXECUTION METHODS
    # =====================================
    
    async def _execute_list_network_devices(self, arguments: Dict[str, Any]) -> str:
        """Execute list network devices tool"""
        
        device_type = arguments.get("device_type", "all")
        limit = arguments.get("limit", 10)
        filter_text = arguments.get("filter", "")
        
        response_parts = [f"# Network Devices List\n"]
        
        if device_type == "all":
            response_parts.append(f"**Showing all device types** (limit: {limit})\n\n")
        else:
            response_parts.append(f"**Device Type:** {device_type.replace('_', ' ').title()} (limit: {limit})\n\n")
        
        try:
            # Get network API adapter from query controller
            network_adapter = self.query_controller.network_port
            
            devices_found = 0
            
            # Load different device types based on request
            if device_type in ["ftth_olt", "all"]:
                ftth_data = await network_adapter._load_local_json('ftth_olt')
                response_parts.append("## FTTH OLT Devices\n")
                
                for item in ftth_data[:limit if device_type == "ftth_olt" else 5]:
                    name = item.get('name', 'Unknown')
                    if not filter_text or filter_text.lower() in name.lower():
                        environment = item.get('environment', 'Unknown')
                        esi_name = item.get('cin', {}).get('esi_name', 'N/A')
                        response_parts.append(f"- **{name}** (Env: {environment})\n")
                        response_parts.append(f"  ESI: {esi_name}\n")
                        devices_found += 1
                response_parts.append("\n")
            
            if device_type in ["lag", "all"]:
                lag_data = await network_adapter._load_local_json('lag')
                response_parts.append("## LAG Devices\n")
                
                for item in lag_data[:limit if device_type == "lag" else 5]:
                    device_name = item.get('device_name', 'Unknown')
                    description = item.get('description', 'No description')
                    lag_id = item.get('lag_id', 'N/A')
                    if not filter_text or filter_text.lower() in device_name.lower() or filter_text.lower() in description.lower():
                        response_parts.append(f"- **{device_name}** (LAG ID: {lag_id})\n")
                        response_parts.append(f"  Description: {description}\n")
                        devices_found += 1
                response_parts.append("\n")
            
            if device_type in ["pxc", "all"]:
                pxc_data = await network_adapter._load_local_json('pxc')
                response_parts.append("## PXC Devices\n")
                
                for item in pxc_data[:limit if device_type == "pxc" else 5]:
                    device_name = item.get('device_name', 'Unknown')
                    description = item.get('description', 'No description')
                    pxc_id = item.get('pxc_id', 'N/A')
                    if not filter_text or filter_text.lower() in device_name.lower() or filter_text.lower() in description.lower():
                        response_parts.append(f"- **{device_name}** (PXC ID: {pxc_id})\n")
                        response_parts.append(f"  Description: {description}\n")
                        devices_found += 1
                response_parts.append("\n")
            
            if device_type in ["mobile_modem", "all"]:
                mobile_data = await network_adapter._load_local_json('mobile_modem')
                response_parts.append("## Mobile Modems\n")
                
                for item in mobile_data[:limit if device_type == "mobile_modem" else 5]:
                    serial = item.get('serial_number', 'Unknown')
                    hardware_type = item.get('hardware_type', 'Unknown')
                    subscriber_id = item.get('mobile_subscriber_id', 'N/A')
                    if not filter_text or filter_text.lower() in serial.lower() or filter_text.lower() in hardware_type.lower():
                        response_parts.append(f"- **{serial}** ({hardware_type})\n")
                        response_parts.append(f"  Subscriber: {subscriber_id}\n")
                        devices_found += 1
                response_parts.append("\n")
            
            if device_type in ["team", "all"]:
                team_data = await network_adapter._load_local_json('team')
                response_parts.append("## Teams\n")
                
                for item in team_data[:limit if device_type == "team" else 5]:
                    team_name = item.get('team_name', 'Unknown')
                    description = item.get('description', 'No description')
                    if not filter_text or filter_text.lower() in team_name.lower():
                        response_parts.append(f"- **{team_name}**\n")
                        if description:
                            response_parts.append(f"  Description: {description}\n")
                        devices_found += 1
                response_parts.append("\n")
            
            if devices_found == 0:
                response_parts.append("No devices found matching the criteria.\n")
            else:
                response_parts.append(f"**Total devices found:** {devices_found}\n")
            
        except Exception as e:
            response_parts.append(f"❌ Error loading device data: {str(e)}\n")
        
        return "".join(response_parts)
    
    async def _execute_get_device_details(self, arguments: Dict[str, Any]) -> str:
        """Execute get device details tool"""
        
        device_name = arguments.get("device_name", "")
        device_type = arguments.get("device_type", "ftth_olt")
        
        if not device_name:
            return "# Error\nDevice name is required"
        
        response_parts = [
            f"# Device Details\n",
            f"**Device:** {device_name}\n",
            f"**Type:** {device_type.replace('_', ' ').title()}\n\n"
        ]
        
        try:
            # Get network API adapter from query controller  
            network_adapter = self.query_controller.network_port
            
            # Load data for the specific device type
            data = await network_adapter._load_local_json(device_type)
            
            # Find the specific device
            device_found = None
            for item in data:
                if device_type == "ftth_olt":
                    if item.get('name', '').lower() == device_name.lower():
                        device_found = item
                        break
                elif device_type == "lag":
                    if item.get('device_name', '').lower() == device_name.lower():
                        device_found = item
                        break
                elif device_type == "pxc":
                    if item.get('device_name', '').lower() == device_name.lower():
                        device_found = item
                        break
                elif device_type == "mobile_modem":
                    if item.get('serial_number', '').lower() == device_name.lower():
                        device_found = item
                        break
                elif device_type == "team":
                    if item.get('team_name', '').lower() == device_name.lower():
                        device_found = item
                        break
            
            if not device_found:
                response_parts.append(f"❌ Device '{device_name}' not found in {device_type} data.\n")
                return "".join(response_parts)
            
            # Format device details based on type
            if device_type == "ftth_olt":
                response_parts.extend([
                    "## Configuration Details\n",
                    f"**ESI Name:** {device_found.get('cin', {}).get('esi_name', 'N/A')}\n",
                    f"**ESI:** {device_found.get('cin', {}).get('esi', 'N/A')}\n",
                    f"**Environment:** {device_found.get('environment', 'Unknown')}\n"
                ])
                
                # BNG information
                bng = device_found.get('bng', {})
                if bng:
                    response_parts.append("\n## BNG Configuration\n")
                    master = bng.get('node_master', {})
                    if master:
                        response_parts.append(f"**Master Node:** {master.get('name', 'N/A')} ({master.get('sys_ip', 'N/A')})\n")
                    slave = bng.get('node_slave', {})
                    if slave:
                        response_parts.append(f"**Slave Node:** {slave.get('name', 'N/A')} ({slave.get('sys_ip', 'N/A')})\n")
                
                # CIN information
                cin = device_found.get('cin', {})
                if cin.get('nodes'):
                    response_parts.append("\n## CIN Nodes\n")
                    for node in cin['nodes'][:3]:  # Show first 3 nodes
                        response_parts.append(f"**{node.get('name', 'Unknown')}** ({node.get('sys_ip', 'N/A')})\n")
                        ports = node.get('ports', [])
                        if ports:
                            response_parts.append(f"  Ports: {len(ports)} configured\n")
            
            elif device_type == "lag":
                response_parts.extend([
                    "## LAG Details\n",
                    f"**LAG ID:** {device_found.get('lag_id', 'N/A')}\n",
                    f"**Description:** {device_found.get('description', 'No description')}\n",
                    f"**Admin Key:** {device_found.get('admin_key', 'N/A')}\n"
                ])
            
            elif device_type == "pxc":
                response_parts.extend([
                    "## PXC Details\n",
                    f"**PXC ID:** {device_found.get('pxc_id', 'N/A')}\n",
                    f"**Description:** {device_found.get('description', 'No description')}\n"
                ])
            
            elif device_type == "mobile_modem":
                response_parts.extend([
                    "## Mobile Modem Details\n",
                    f"**Serial Number:** {device_found.get('serial_number', 'N/A')}\n",
                    f"**Hardware Type:** {device_found.get('hardware_type', 'Unknown')}\n",
                    f"**Subscriber ID:** {device_found.get('mobile_subscriber_id', 'N/A')}\n",
                    f"**Command ID:** {device_found.get('fnt_command_id', 'N/A')}\n"
                ])
            
            elif device_type == "team":
                response_parts.extend([
                    "## Team Details\n",
                    f"**Team ID:** {device_found.get('team_id', 'N/A')}\n",
                    f"**Description:** {device_found.get('description', 'No description')}\n",
                    f"**Contact Information:** {device_found.get('contact_information', 'Not available')}\n"
                ])
            
        except Exception as e:
            response_parts.append(f"❌ Error retrieving device details: {str(e)}\n")
        
        return "".join(response_parts)
    
    # =====================================
    # UTILITY METHODS
    # =====================================
    
    def _create_error_response(self, request_id: Optional[str], code: int, message: str) -> Dict[str, Any]:
        """Create JSON-RPC error response"""
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        
        return {
            "name": self.server_name,
            "version": self.server_version,
            "capabilities": list(self.capabilities.keys()),
            "tools_available": len(self.tools),
            "active_conversations": len(self.active_conversations),
            "total_requests": self.request_counter
        }
    
    def get_tool_list(self) -> List[str]:
        """Get list of available tool names"""
        
        return [tool["name"] for tool in self.tools]
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform MCP server health check"""
        
        try:
            # Test basic functionality
            test_request = {
                "jsonrpc": "2.0",
                "id": "health_check",
                "method": "tools/list"
            }
            
            response = await self.handle_mcp_request(test_request)
            
            return {
                "status": "healthy" if "result" in response else "unhealthy",
                "tools_count": len(self.tools),
                "capabilities": list(self.capabilities.keys()),
                "server_info": {
                    "name": self.server_name,
                    "version": self.server_version
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }