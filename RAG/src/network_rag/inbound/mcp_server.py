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
        # TODO: ADD YOUR CUSTOM TOOLS HERE
        # =====================================
        # This is where you can add additional tools specific to your use case.
        # Examples might include:
        # - Network topology visualization tools
        # - Performance monitoring tools
        # - Configuration deployment tools
        # - Custom reporting tools
        # - Integration with other network management systems
        
        # Template for adding a new tool:
        # tools.append({
        #     "name": "your_tool_name",
        #     "description": "Description of what your tool does",
        #     "inputSchema": {
        #         "type": "object",
        #         "properties": {
        #             "param1": {
        #                 "type": "string",
        #                 "description": "Description of parameter"
        #             }
        #         },
        #         "required": ["param1"]
        #     }
        # })
        
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
            # TODO: ADD YOUR CUSTOM TOOL HANDLERS HERE
            # =====================================
            # Add handlers for your custom tools:
            # elif tool_name == "your_tool_name":
            #     result = await self._execute_your_tool(arguments)
            
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
        """Execute network resource query"""
        
        query = arguments.get("query", "")
        include_recommendations = arguments.get("include_recommendations", True)
        session_id = arguments.get("session_id")
        
        # Create conversation context if session provided
        conversation_id = None
        if session_id:
            conversation_id = f"mcp_session_{session_id}_{int(datetime.utcnow().timestamp())}"
        
        # Execute query through controller
        query_result = await self.query_controller.process_query(
            query=query,
            conversation_id=conversation_id,
            user_context={"source": "mcp", "session_id": session_id}
        )
        
        # Format response for LLM consumption
        response_parts = [
            f"# Network Query Results\n",
            f"**Query:** {query}\n",
            f"**Confidence:** {query_result.get_confidence_level().value.replace('_', ' ').title()}\n\n",
            f"## Analysis\n{query_result.primary_answer}\n"
        ]
        
        # Add network intelligence if available
        if "network_intelligence" in query_result.supporting_data:
            network_data = query_result.supporting_data["network_intelligence"]
            response_parts.append("\n## Network Resources Found\n")
            
            for i, olt in enumerate(network_data[:5]):  # Limit to top 5
                status_icon = "⚠️" if olt.get("action_required") else "✅"
                response_parts.append(
                    f"{status_icon} **{olt['name']}** ({olt['environment']})\n"
                    f"   - Connection: {olt.get('connection_type', 'N/A')} | "
                    f"Bandwidth: {olt['bandwidth_gbps']}Gbps\n"
                    f"   - Config Complete: {'Yes' if olt.get('complete_config') else 'No'}\n"
                )
                
                if olt.get("insights", {}).get("issues"):
                    issues = olt["insights"]["issues"][:2]  # Top 2 issues
                    response_parts.append(f"   - Issues: {', '.join(issues)}\n")
        
        # Add recommendations if requested
        if include_recommendations and query_result.suggested_questions:
            response_parts.append("\n## Follow-up Suggestions\n")
            for suggestion in query_result.suggested_questions[:3]:
                response_parts.append(f"- {suggestion}\n")
        
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
    # TODO: ADD YOUR CUSTOM TOOL EXECUTION METHODS HERE
    # =====================================
    # Add execution methods for your custom tools:
    # 
    # async def _execute_your_tool(self, arguments: Dict[str, Any]) -> str:
    #     """Execute your custom tool"""
    #     
    #     param1 = arguments.get("param1", "")
    #     
    #     # Your tool logic here
    #     result = "Your tool result"
    #     
    #     return result
    
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