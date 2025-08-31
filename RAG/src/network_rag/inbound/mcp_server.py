# src/network_rag/inbound/mcp_server.py
"""MCP (Model Context Protocol) server adapter for LLM integration"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..controller.query_controller import QueryController
from ..controller.document_controller import DocumentController
from ..controller.learning_controller import LearningController
from ..controller.validation_controller import ValidationController


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
        
        # client_info = params.get("clientInfo", {})  # Not used currently
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
        """Execute intelligent network resource query - DELEGATES TO BUSINESS LOGIC"""
        
        try:
            # ✅ PROPER ARCHITECTURE: Delegate to business logic layer
            return await self.query_controller.execute_intelligent_network_query(arguments)
            
        except Exception as e:
            # Handle protocol-level errors
            return f"# Network Query Error\n\n❌ **Error:** {str(e)}\n\n💡 **Suggestion:** Try a simpler query or check your connection."
    
    async def _execute_knowledge_search(self, arguments: Dict[str, Any]) -> str:
        """Execute knowledge base search"""
        
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        # document_types = arguments.get("document_types")  # Not used currently
        
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
    # RAG FUSION METHODS
    # =====================================
    
    async def _rag_fusion_search(self, query: str) -> Dict[str, Any]:
        """Use RAG fusion to search knowledge base and determine best approach"""
        
        try:
            # Multiple search strategies for higher confidence
            searches = [
                f"tool selection for: {query}",
                f"how to handle query: {query}",  
                f"MCP tool for {query}",
                f"network analysis approach for: {query}"
            ]
            
            all_results = []
            for search_query in searches:
                try:
                    documents = await self.document_controller.search_documents(
                        query=search_query,
                        limit=3,
                        use_vector_search=True
                    )
                    all_results.extend(documents)
                except Exception as e:
                    print(f"Search failed for '{search_query}': {e}")
                    continue
            
            if not all_results:
                return self._default_guidance(query)
            
            # Analyze results to determine guidance
            return await self._analyze_rag_results(query, all_results)
            
        except Exception as e:
            print(f"RAG fusion search failed: {e}")
            return self._default_guidance(query)
    
    async def _analyze_rag_results(self, query: str, documents: List) -> Dict[str, Any]:
        """Analyze RAG search results to provide guidance"""
        
        # Count tool mentions in the documents
        tool_mentions = {
            'list_network_devices': 0,
            'get_device_details': 0, 
            'query_network_resources': 0
        }
        
        analysis_patterns = {
            'device_listing': 0,
            'device_details': 0,
            'complex_analysis': 0
        }
        
        recommendations = []
        confidence_score = 0
        
        query_lower = query.lower()
        
        for doc in documents[:5]:  # Top 5 most relevant
            content = doc.content.lower() if hasattr(doc, 'content') else str(doc).lower()
            title = doc.title.lower() if hasattr(doc, 'title') else ""
            
            # Count tool mentions
            for tool_name in tool_mentions.keys():
                if tool_name in title or tool_name in content:
                    tool_mentions[tool_name] += 2  # Higher weight for matches
                    confidence_score += 1
            
            # Analyze patterns
            if any(word in content for word in ['inventory', 'count', 'list all', 'how many']):
                analysis_patterns['device_listing'] += 1
                
            if any(word in content for word in ['specific device', 'configuration', 'details for']):
                analysis_patterns['device_details'] += 1
                
            if any(word in content for word in ['impact', 'analysis', 'cross-reference', 'relationships']):
                analysis_patterns['complex_analysis'] += 1
            
            # Extract recommendations from content
            if 'recommendation' in content or 'use' in content:
                # Simple extraction - could be enhanced
                lines = content.split('\n')
                for line in lines:
                    if ('use' in line or 'recommend' in line) and len(line) < 150:
                        recommendations.append(line.strip())
        
        # Determine best tool
        best_tool = max(tool_mentions.items(), key=lambda x: x[1])
        best_analysis = max(analysis_patterns.items(), key=lambda x: x[1])
        
        # Calculate confidence
        total_docs = len(documents)
        confidence_level = "HIGH" if confidence_score > 3 else "MEDIUM" if confidence_score > 1 else "LOW"
        
        # Determine approach based on query patterns
        approach = self._determine_approach(query_lower, best_analysis[0])
        reasoning = self._generate_reasoning(query, best_tool[0], best_analysis[0])
        
        return {
            'confidence': confidence_level,
            'tool_recommendation': best_tool[0] if best_tool[1] > 0 else None,
            'analysis_type': best_analysis[0],
            'approach': approach,
            'reasoning': reasoning,
            'recommendations': recommendations[:3],  # Top 3 recommendations
            'docs_analyzed': total_docs
        }
    
    def _determine_approach(self, query_lower: str, analysis_type: str) -> str:
        """Determine the best approach based on query analysis"""
        
        if any(word in query_lower for word in ['how many', 'list all', 'show me all', 'count']):
            return "Device inventory and listing approach"
        elif any(word in query_lower for word in ['configuration of', 'details for', 'show me', 'get info']):
            return "Specific device configuration analysis"
        elif any(word in query_lower for word in ['impact', 'happens if', 'connected to', 'depends on']):
            return "Cross-system impact and dependency analysis"
        else:
            return f"Intelligent {analysis_type.replace('_', ' ')} approach"
    
    def _generate_reasoning(self, query: str, tool: str, analysis_type: str) -> str:
        """Generate reasoning for tool recommendation"""
        
        if 'list_network_devices' in tool:
            return "Query requests device inventory or counts - best served by listing tool"
        elif 'get_device_details' in tool:
            return "Query asks for specific device information - requires detailed configuration tool"
        elif 'query_network_resources' in tool:
            return "Query requires cross-system analysis or impact assessment - needs intelligent analysis"
        else:
            return f"Query pattern suggests {analysis_type.replace('_', ' ')} approach"
    
    def _default_guidance(self, query: str) -> Dict[str, Any]:
        """Provide default guidance when RAG search fails"""
        
        query_lower = query.lower()
        
        # Simple pattern matching as fallback
        if any(word in query_lower for word in ['how many', 'list', 'count', 'all']):
            return {
                'confidence': 'MEDIUM',
                'tool_recommendation': 'list_network_devices',
                'analysis_type': 'device_listing',
                'approach': 'Device inventory approach (fallback)',
                'reasoning': 'Query pattern suggests device listing',
                'recommendations': ['Use list_network_devices for inventory queries'],
                'docs_analyzed': 0
            }
        elif any(device in query_lower for device in ['olt17prop01', 'cinaalsa01', 'specific']):
            return {
                'confidence': 'MEDIUM', 
                'tool_recommendation': 'get_device_details',
                'analysis_type': 'device_details',
                'approach': 'Specific device analysis (fallback)',
                'reasoning': 'Query mentions specific device',
                'recommendations': ['Use get_device_details for specific devices'],
                'docs_analyzed': 0
            }
        else:
            return {
                'confidence': 'LOW',
                'tool_recommendation': 'query_network_resources',
                'analysis_type': 'complex_analysis',
                'approach': 'General network analysis (fallback)',
                'reasoning': 'Complex query requires intelligent analysis',
                'recommendations': ['Use complex analysis for unclear queries'],
                'docs_analyzed': 0
            }

    # =====================================
    # GUIDED EXECUTION METHODS
    # =====================================
    
    async def _execute_guided_device_listing(self, query: str, _guidance: Dict[str, Any]) -> List[str]:
        """Execute device listing guided by RAG results"""
        
        # Extract parameters from guidance and query
        device_type = "all"  # Default
        filter_text = ""
        
        query_lower = query.lower()
        
        # Determine device type from query
        if any(word in query_lower for word in ['ftth', 'olt']):
            device_type = "ftth_olt"
        elif 'lag' in query_lower:
            device_type = "lag"
        elif any(word in query_lower for word in ['mobile', 'modem']):
            device_type = "mobile_modem"
        elif 'team' in query_lower:
            device_type = "team"
        elif 'pxc' in query_lower:
            device_type = "pxc"
        
        # Extract filter from specific device mentions
        if 'cinaalsa01' in query_lower:
            filter_text = "CINAALSA01"
        elif 'hobo' in query_lower:
            filter_text = "HOBO"
        
        # Call the list_network_devices logic directly and convert to list
        result = await self._execute_list_network_devices({
            'device_type': device_type,
            'filter': filter_text,
            'limit': 10
        })
        
        return ["## RAG-Guided Device Listing\n", result]
    
    async def _execute_guided_device_details(self, query: str, _guidance: Dict[str, Any]) -> List[str]:
        """Execute device details guided by RAG results"""
        
        # Extract device name from query
        device_name = None
        device_type = "ftth_olt"  # Default
        
        query_lower = query.lower()
        
        # Look for specific device names
        if 'olt17prop01' in query_lower:
            device_name = "OLT17PROP01"
            device_type = "ftth_olt"
        elif 'cinaalsa01' in query_lower:
            device_name = "CINAALSA01" 
            device_type = "lag"
        elif 'mobile' in query_lower and any(serial in query_lower for serial in ['lpl', 'modem']):
            # Would need to extract serial number
            device_type = "mobile_modem"
        
        if device_name:
            # Call the get_device_details logic directly and convert to list
            result = await self._execute_get_device_details({
                'device_name': device_name,
                'device_type': device_type
            })
            return ["## RAG-Guided Device Details\n", result]
        else:
            return ["## Guided Analysis\nCould not identify specific device name in query. Please specify exact device name."]
    
    async def _execute_guided_complex_analysis(self, query: str, _guidance: Dict[str, Any]) -> List[str]:
        """Execute complex analysis guided by RAG results"""
        
        # Use the original intelligent analysis but with RAG guidance
        return await self._execute_original_analysis(query)
    
    async def _execute_original_analysis(self, query: str) -> List[str]:
        """Execute the original analysis logic as fallback"""
        
        query_lower = query.lower()
        
        # Get network API adapter
        network_adapter = self.query_controller.network_port
        
        # Fetch data
        ftth_olts = await network_adapter.fetch_ftth_olts()
        lag_data = await network_adapter._load_local_json('lag')
        pxc_data = await network_adapter._load_local_json('pxc')
        mobile_data = await network_adapter._load_local_json('mobile_modem')
        team_data = await network_adapter._load_local_json('team')
        
        # Original analysis logic
        if 'hobo' in query_lower and 'cinmecha01' in query_lower:
            return await self._analyze_hobo_cinmecha_connectivity(ftth_olts, [])
        elif 'cinaalsa01' in query_lower and 'lag' in query_lower:
            return await self._analyze_lag_correlations(lag_data, ftth_olts, team_data)
        elif 'nokia' in query_lower and 'mobile' in query_lower:
            return await self._analyze_nokia_mobile_infrastructure(mobile_data, team_data)
        else:
            return await self._smart_device_listing(query_lower, ftth_olts, lag_data, pxc_data, mobile_data, team_data)

    # =====================================
    # INTELLIGENT ANALYSIS METHODS
    # =====================================
    
    async def _analyze_hobo_cinmecha_connectivity(self, ftth_olts, response_parts):
        """Analyze HOBO region OLTs connected to CINMECHA01"""
        analysis_parts = ["## HOBO Region - CINMECHA01 Connectivity Analysis\n\n"]
        
        # Find HOBO region OLTs
        hobo_olts = [olt for olt in ftth_olts if olt.region.upper() == 'HOBO']
        cinmecha_connected = []
        
        for olt in hobo_olts:
            # Check raw data for CINMECHA01 connections
            olt_dict = olt.__dict__
            if any('CINMECHA01' in str(v) for v in olt_dict.values() if v):
                cinmecha_connected.append(olt)
        
        analysis_parts.append(f"**HOBO Region OLTs:** {len(hobo_olts)} found\n")
        analysis_parts.append(f"**Connected to CINMECHA01:** {len(cinmecha_connected)}\n\n")
        
        if cinmecha_connected:
            analysis_parts.append("### Connected FTTH OLTs:\n")
            for olt in cinmecha_connected[:5]:
                health = olt.get_health_summary()
                analysis_parts.extend([
                    f"🔗 **{health['name']}**\n",
                    f"   - Environment: {health['environment']}\n",
                    f"   - Managed by Inmanta: {'Yes' if health['managed_by_inmanta'] else 'No'}\n",
                    f"   - Config Complete: {'Yes' if health['complete_config'] else 'No'}\n\n"
                ])
        
        # Analyze redundancy
        analysis_parts.append("### Redundancy Analysis:\n")
        analysis_parts.append("- Single Point of Failure: CINMECHA01 node failure would impact connected OLTs\n")
        analysis_parts.append("- Recommendation: Verify BNG master/slave configurations\n")
        analysis_parts.append("- Critical: Review backup connectivity paths\n\n")
        
        return analysis_parts
    
    async def _analyze_lag_correlations(self, lag_data, ftth_olts, team_data):
        """Analyze LAG configurations and FTTH correlations"""
        analysis_parts = ["## CINAALSA01 LAG Analysis & FTTH Correlations\n\n"]
        
        # Filter LAGs for CINAALSA01
        cinaalsa_lags = [lag for lag in lag_data if lag.get('device_name') == 'CINAALSA01']
        
        analysis_parts.append(f"**CINAALSA01 LAG Configurations:** {len(cinaalsa_lags)} found\n\n")
        
        if cinaalsa_lags:
            analysis_parts.append("### LAG Details:\n")
            for lag in cinaalsa_lags[:10]:
                analysis_parts.extend([
                    f"- **LAG {lag.get('lag_id')}**: {lag.get('description', 'No description')}\n",
                    f"  Admin Key: {lag.get('admin_key', 'None')}\n"
                ])
            analysis_parts.append("\n")
        
        # Check for FTTH OLTs that might use these LAGs
        analysis_parts.append("### FTTH Uplink Dependencies:\n")
        dependent_olts = []
        for olt in ftth_olts:
            olt_dict = olt.__dict__
            if any('CINAALSA01' in str(v) or 'LAG' in str(v) for v in olt_dict.values() if v):
                dependent_olts.append(olt)
        
        if dependent_olts:
            analysis_parts.append(f"**Potentially dependent FTTH OLTs:** {len(dependent_olts)}\n")
            for olt in dependent_olts[:3]:
                health = olt.get_health_summary()
                analysis_parts.append(f"- {health['name']} ({health['environment']})\n")
        else:
            analysis_parts.append("No direct FTTH dependencies identified in current data.\n")
        
        # Team notification analysis
        analysis_parts.append("\n### Team Notification Strategy:\n")
        critical_teams = [team for team in team_data if team.get('team_name') in ['NAS', 'INFRA', 'IPOPS']]
        if critical_teams:
            analysis_parts.append("**Critical Teams to Notify:**\n")
            for team in critical_teams:
                analysis_parts.append(f"- {team.get('team_name')} (ID: {team.get('team_id')})\n")
        
        return analysis_parts
    
    async def _analyze_nokia_mobile_infrastructure(self, mobile_data, team_data):
        """Analyze Nokia mobile modems and team assignments"""
        analysis_parts = ["## Nokia Mobile Infrastructure Analysis\n\n"]
        
        # Filter Nokia devices
        nokia_modems = [modem for modem in mobile_data if 'Nokia' in modem.get('hardware_type', '')]
        
        analysis_parts.append(f"**Nokia Mobile Modems:** {len(nokia_modems)} found\n\n")
        
        if nokia_modems:
            analysis_parts.append("### Nokia Device Inventory:\n")
            subscriber_map = {}
            for modem in nokia_modems[:10]:
                serial = modem.get('serial_number', 'Unknown')
                subscriber = modem.get('mobile_subscriber_id', 'N/A')
                analysis_parts.append(f"- **{serial}** → Subscriber: {subscriber}\n")
                
                # Track subscriber patterns
                if subscriber != 'N/A':
                    subscriber_map[subscriber] = subscriber_map.get(subscriber, 0) + 1
            
            analysis_parts.append("\n### Subscriber Mapping Analysis:\n")
            for subscriber, count in subscriber_map.items():
                analysis_parts.append(f"- {subscriber}: {count} modem(s)\n")
        
        # Team infrastructure analysis
        analysis_parts.append("\n### Team Infrastructure Responsibilities:\n")
        mobile_team = next((team for team in team_data if team.get('team_name') == 'MOBILE'), None)
        if mobile_team:
            analysis_parts.append(f"**Mobile Team:** {mobile_team.get('team_name')} (ID: {mobile_team.get('team_id')})\n")
        
        # Integration points analysis
        analysis_parts.append("\n### Integration Points:\n")
        analysis_parts.append("- VPN Services: Mobile modems use VPN subscriber IDs\n")
        analysis_parts.append("- Network Convergence: Potential integration with FTTH for hybrid services\n")
        analysis_parts.append("- Management Overlap: Consider unified device management platform\n")
        
        return analysis_parts
    
    async def _trace_network_path(self, ftth_olts, lag_data, pxc_data):
        """Trace network path from specific OLT"""
        analysis_parts = ["## Network Path Tracing: OLT17PROP01\n\n"]
        
        # Find the specific OLT
        target_olt = next((olt for olt in ftth_olts if olt.name == 'OLT17PROP01'), None)
        
        if not target_olt:
            analysis_parts.append("❌ OLT17PROP01 not found in FTTH data\n")
            return analysis_parts
        
        health = target_olt.get_health_summary()
        analysis_parts.extend([
            f"**Source OLT:** {health['name']}\n",
            f"**Environment:** {health['environment']}\n",
            f"**Region:** {target_olt.region}\n\n"
        ])
        
        # Analyze connectivity from raw OLT data
        analysis_parts.append("### Network Path Analysis:\n")
        olt_dict = target_olt.__dict__
        
        # Look for BNG connections
        analysis_parts.append("**BNG Connectivity:**\n")
        if hasattr(target_olt, 'service_configs') and target_olt.service_configs:
            analysis_parts.append("- BNG nodes identified in service configuration\n")
        else:
            analysis_parts.append("- No BNG configuration found in current data\n")
        
        # Check for LAG connections
        related_lags = [lag for lag in lag_data if 'OLT17PROP01' in str(lag)]
        if related_lags:
            analysis_parts.append(f"\n**LAG Connections:** {len(related_lags)} potential\n")
        else:
            analysis_parts.append("\n**LAG Connections:** None identified in current data\n")
        
        # Check PXC connections
        hobo_pxcs = [pxc for pxc in pxc_data if 'HOBO' in pxc.get('device_name', '') or 'HOBO' in pxc.get('description', '')]
        if hobo_pxcs:
            analysis_parts.append(f"\n**PXC Cross-connects (HOBO region):** {len(hobo_pxcs)} found\n")
            for pxc in hobo_pxcs[:3]:
                analysis_parts.append(f"- {pxc.get('device_name')}: {pxc.get('description')}\n")
        
        # CINMECHA01 failure impact analysis
        analysis_parts.append("\n### CINMECHA01 Failure Impact Analysis:\n")
        analysis_parts.append("**Blast Radius Assessment:**\n")
        analysis_parts.append("- Primary Impact: OLTs directly connected to CINMECHA01\n")
        analysis_parts.append("- Secondary Impact: Services depending on affected OLTs\n")
        analysis_parts.append("- Recovery Strategy: Failover to CINMECHB02 if configured\n")
        
        return analysis_parts
    
    async def _analyze_configuration_completeness(self, ftth_olts, lag_data, pxc_data):
        """Analyze configuration completeness across devices"""
        analysis_parts = ["## Configuration Completeness Analysis\n\n"]
        
        # Analyze FTTH OLT configurations
        incomplete_olts = [olt for olt in ftth_olts if not olt.get_health_summary().get('complete_config')]
        production_incomplete = [olt for olt in incomplete_olts if olt.is_production()]
        test_incomplete = [olt for olt in incomplete_olts if not olt.is_production()]
        
        analysis_parts.extend([
            f"**Total FTTH OLTs:** {len(ftth_olts)}\n",
            f"**Incomplete Configurations:** {len(incomplete_olts)}\n",
            f"**Production Impact:** {len(production_incomplete)} devices\n",
            f"**Test Environment:** {len(test_incomplete)} devices\n\n"
        ])
        
        # Priority analysis
        analysis_parts.append("### Priority Classification:\n")
        
        if production_incomplete:
            analysis_parts.append("🔴 **CRITICAL (Production):**\n")
            for olt in production_incomplete[:5]:
                health = olt.get_health_summary()
                analysis_parts.append(f"- {health['name']}: Missing core configuration elements\n")
        
        if test_incomplete:
            analysis_parts.append("\n🟡 **MEDIUM (Test Environment):**\n")
            analysis_parts.append(f"- {len(test_incomplete)} test OLTs with incomplete configs\n")
        
        # Missing configuration elements analysis
        analysis_parts.append("\n### Missing Configuration Elements:\n")
        zero_bandwidth = [olt for olt in ftth_olts if olt.get_health_summary().get('bandwidth_gbps') == 0]
        no_services = [olt for olt in ftth_olts if olt.get_health_summary().get('service_count') == 0]
        
        analysis_parts.extend([
            f"- Bandwidth Configuration: {len(zero_bandwidth)} devices\n",
            f"- Service Configuration: {len(no_services)} devices\n",
            f"- Connection Type: Multiple devices missing connection specifications\n"
        ])
        
        # Remediation timeline
        analysis_parts.append("\n### Remediation Timeline:\n")
        analysis_parts.append("**Week 1:** Address critical production configurations\n")
        analysis_parts.append("**Week 2-3:** Complete test environment configurations\n")
        analysis_parts.append("**Week 4:** Validation and monitoring setup\n")
        
        return analysis_parts
    
    async def _smart_device_listing(self, query_lower, ftth_olts, lag_data, pxc_data, mobile_data, team_data):
        """Smart device listing based on query context"""
        analysis_parts = ["## Smart Device Analysis\n\n"]
        
        # Query-based filtering
        if 'status' in query_lower or 'health' in query_lower:
            analysis_parts.append("### Device Health Status:\n")
            for olt in ftth_olts[:5]:
                health = olt.get_health_summary()
                status = "🟢 Operational" if health['complete_config'] else "🟡 Needs Attention"
                analysis_parts.append(f"- **{health['name']}**: {status} ({health['environment']})\n")
        
        elif 'all' in query_lower and 'device' in query_lower:
            analysis_parts.extend([
                f"### Infrastructure Summary:\n",
                f"- FTTH OLTs: {len(ftth_olts)}\n",
                f"- LAG Devices: {len(lag_data)}\n",
                f"- PXC Cross-connects: {len(pxc_data)}\n",
                f"- Mobile Modems: {len(mobile_data)}\n",
                f"- Teams: {len(team_data)}\n\n"
            ])
        
        else:
            # Default intelligent summary
            analysis_parts.append("### Network Overview:\n")
            incomplete_count = len([olt for olt in ftth_olts if not olt.get_health_summary().get('complete_config')])
            analysis_parts.extend([
                f"**FTTH Infrastructure:** {len(ftth_olts)} OLTs ({incomplete_count} need configuration)\n",
                f"**Switching Infrastructure:** {len(lag_data)} LAG configurations\n",
                f"**Cross-connect Infrastructure:** {len(pxc_data)} PXC ports\n"
            ])
        
        return analysis_parts
    
    async def _generate_smart_recommendations(self, query_lower, ftth_olts, lag_data, pxc_data, mobile_data):
        """Generate context-aware recommendations"""
        recommendations = []
        
        if 'redundancy' in query_lower or 'failure' in query_lower:
            recommendations.extend([
                "- Implement diverse routing for critical OLT connections\n",
                "- Verify BNG failover mechanisms are properly configured\n",
                "- Test disaster recovery procedures for CINMECHA01 failure scenarios\n"
            ])
        
        elif 'configuration' in query_lower:
            incomplete_count = len([olt for olt in ftth_olts if not olt.get_health_summary().get('complete_config')])
            recommendations.extend([
                f"- Prioritize completing configurations for {incomplete_count} FTTH OLTs\n",
                "- Implement configuration management automation\n",
                "- Establish configuration validation procedures\n"
            ])
        
        elif 'team' in query_lower:
            recommendations.extend([
                "- Cross-train teams on mobile and FTTH infrastructure\n",
                "- Establish clear escalation procedures\n",
                "- Create unified monitoring dashboard for all infrastructure\n"
            ])
        
        else:
            # General recommendations
            incomplete_count = len([olt for olt in ftth_olts if not olt.get_health_summary().get('complete_config')])
            recommendations.extend([
                f"- Address {incomplete_count} incomplete OLT configurations\n",
                "- Implement comprehensive network monitoring\n",
                "- Enhance documentation for network topology\n"
            ])
        
        return recommendations
    
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