# src/network_rag/controller/query_controller.py
"""Simplified query processing controller with only essential business logic"""

from typing import List, Dict, Any, Optional

from ..models import NetworkPort, VectorSearchPort, LLMPort
from ..services.rag_fusion_analyzer import RAGFusionAnalyzer
from ..services.response_formatter import ResponseFormatter


class QueryController:
    """Simplified controller for query processing with RAG-enhanced intelligence"""
    
    def __init__(
        self,
        network_port: NetworkPort,
        vector_search_port: VectorSearchPort,
        llm_port: LLMPort,
        document_controller=None
    ):
        self.network_port = network_port
        self.vector_search_port = vector_search_port
        self.llm_port = llm_port
        self.rag_analyzer = None
        self.response_formatter = ResponseFormatter()
        self._document_controller = document_controller
    
    def initialize_rag_analyzer(self, document_controller, context_builder=None):
        """Initialize RAG fusion analyzer with dependencies"""
        self.rag_analyzer = RAGFusionAnalyzer(document_controller, context_builder)
    
    async def execute_intelligent_network_query(self, arguments: Dict[str, Any]) -> str:
        """Main entry point for RAG-enhanced intelligent network queries with schema awareness"""
        query = arguments.get("query", "")
        include_recommendations = arguments.get("include_recommendations", True)
        
        # Step 1: Use enhanced RAG fusion with data awareness
        if self.rag_analyzer:
            if hasattr(self.rag_analyzer, 'analyze_query_with_data_awareness'):
                guidance, schema_context = await self.rag_analyzer.analyze_query_with_data_awareness(query)
            else:
                guidance = await self.rag_analyzer.analyze_query_for_tool_selection(query)
                schema_context = None
        else:
            guidance = self._fallback_tool_guidance(query)
            schema_context = None
        
        # Step 2: Build response with schema context
        response_parts = [
            "# Schema-Aware Network Analysis\n",
            f"**Query:** {query}\n\n"
        ]
        
        if schema_context:
            response_parts.append(self._format_schema_context_summary(schema_context))
        
        if guidance.get('docs_analyzed', 0) > 0:
            response_parts.extend(self.response_formatter.format_rag_guidance(guidance))
        
        # Step 3: Execute the recommended strategy
        try:
            if guidance['analysis_type'] == 'device_listing':
                result = await self._execute_device_listing_strategy(query, guidance, schema_context)
            elif guidance['analysis_type'] == 'device_details':
                result = await self._execute_device_details_strategy(query, guidance, schema_context)
            else:
                result = await self._execute_complex_analysis_strategy(query, guidance, schema_context)
            
            response_parts.append(result)
            
        except Exception as e:
            error_response = self.response_formatter.format_error_response(
                "Analysis Error",
                f"Failed to execute analysis: {str(e)}",
                ["Try a more specific query", "Check device names for typos"]
            )
            response_parts.append(error_response)
        
        # Step 4: Add knowledge-based recommendations
        if include_recommendations and guidance.get('recommendations'):
            response_parts.extend([
                "\n## Knowledge-Based Recommendations\n"
            ])
            for rec in guidance['recommendations']:
                response_parts.append(f"💡 {rec}\n")
        
        return "".join(response_parts)
    
    def _fallback_tool_guidance(self, query: str) -> Dict[str, Any]:
        """Provide tool guidance when RAG analyzer is not available"""
        query_lower = query.lower()
        
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
    
    def _format_schema_context_summary(self, schema_context) -> str:
        """Format schema context for display"""
        if not schema_context:
            return ""
        
        try:
            parts = ["## 📊 Data Context\n\n"]
            
            # Data availability
            if hasattr(schema_context, 'data_samples') and schema_context.data_samples:
                total_records = sum(
                    sample.record_count for sample in schema_context.data_samples.values()
                    if hasattr(sample, 'record_count')
                )
                data_sources = len(schema_context.data_samples)
                parts.append(f"**Available Data:** {total_records} records across {data_sources} data sources\n\n")
            
            # Data quality
            if hasattr(schema_context, 'quality_metrics') and schema_context.quality_metrics:
                parts.append("**Data Quality:**\n")
                for schema_name, metrics in schema_context.quality_metrics.items():
                    if hasattr(metrics, 'overall_score'):
                        score = metrics.overall_score
                        status = "🟢 Good" if score >= 0.8 else "🟡 Fair" if score >= 0.6 else "🔴 Poor"
                        parts.append(f"- **{schema_name}:** {status} ({score:.1%})\n")
                parts.append("\n")
            
            # Schema info
            if hasattr(schema_context, 'relevant_schemas') and schema_context.relevant_schemas:
                schema_names = [schema.name for schema in schema_context.relevant_schemas]
                parts.append(f"**Relevant Schemas:** {', '.join(schema_names)}\n\n")
            
            # Recommendations
            if hasattr(schema_context, 'recommendations') and schema_context.recommendations:
                parts.append("**Data Recommendations:**\n")
                for rec in schema_context.recommendations[:2]:  # Limit to 2
                    parts.append(f"💡 {rec}\n")
                parts.append("\n")
            
            return "".join(parts)
            
        except Exception as e:
            return f"## 📊 Data Context\n\n*Context formatting error: {str(e)}*\n\n"
    
    async def _execute_device_listing_strategy(self, query: str, guidance: Dict[str, Any], schema_context=None) -> str:
        """Execute device listing strategy"""
        return await self._execute_original_device_listing_strategy(query, guidance)
    
    async def _execute_device_details_strategy(self, query: str, guidance: Dict[str, Any], schema_context=None) -> str:
        """Execute device details strategy"""
        return await self._execute_original_device_details_strategy(query, guidance)
    
    async def _execute_complex_analysis_strategy(self, query: str, guidance: Dict[str, Any], schema_context=None) -> str:
        """Execute complex analysis strategy"""
        return await self._execute_original_complex_analysis_strategy(query, guidance)
    
    async def _execute_original_device_listing_strategy(self, query: str, guidance: Dict[str, Any]) -> str:
        """Execute device listing with LLM intelligence"""
        try:
            # Extract region filter from query
            region_filter = self._extract_region_from_query(query)
            filters = {"region": region_filter} if region_filter else {}
            
            # Fetch FTTH OLT devices
            devices = await self.network_port.fetch_ftth_olts(filters)
            
            if not devices:
                return self.response_formatter.format_error_response(
                    "No Devices Found",
                    f"No FTTH OLT devices found" + (f" in {region_filter} region" if region_filter else ""),
                    ["Check region name spelling", "Try removing region filter", "Verify device availability"]
                )
            
            # Build context for LLM
            device_summaries = []
            for device in devices:
                summary = device.get_health_summary()
                device_summaries.append({
                    "name": summary["name"],
                    "region": summary["region"], 
                    "environment": summary["environment"],
                    "bandwidth_gbps": summary["bandwidth_gbps"],
                    "service_count": summary["service_count"],
                    "managed_by_inmanta": summary["managed_by_inmanta"],
                    "esi_name": summary.get("esi_name", "ESI_" + summary['name']),
                    "connection_type": summary.get("connection_type", "N/A"),
                    "complete_config": summary.get("complete_config", False)
                })
            
            # Generate LLM analysis
            messages = [
                {
                    "role": "system", 
                    "content": "You are a network infrastructure analyst. Analyze the FTTH OLT device data and provide insights about the deployment, configuration status, and any recommendations."
                },
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nFTTH OLT Devices Found: {len(device_summaries)}\n\nDevice Details:\n" + 
                              "\n".join([f"- {d['name']}: {d['region']} region, {d['environment']} environment, "
                                        f"{d['bandwidth_gbps']}Gbps, {d['service_count']} services, "
                                        f"Inmanta managed: {d['managed_by_inmanta']}" for d in device_summaries])
                }
            ]
            
            llm_response = await self.llm_port.generate_response(messages)
            return llm_response
            
        except Exception as e:
            return self.response_formatter.format_error_response(
                "Device Listing Error",
                f"Failed to list devices: {str(e)}",
                ["Check network connectivity", "Verify device filters", "Try a simpler query"]
            )
    
    async def _execute_original_device_details_strategy(self, query: str, guidance: Dict[str, Any]) -> str:
        """Execute device details with LLM intelligence"""
        try:
            # Try to extract device name from query
            device_name = self._extract_device_name_from_query(query)
            
            if not device_name:
                return self.response_formatter.format_error_response(
                    "Device Not Specified",
                    "Could not identify specific device from query",
                    ["Include device name (e.g., 'OLT17PROP01')", "Use format: 'Show me details for [device_name]'"]
                )
            
            # Fetch all devices and find the specific one
            devices = await self.network_port.fetch_ftth_olts()
            target_device = None
            
            for device in devices:
                if device.name.upper() == device_name.upper():
                    target_device = device
                    break
            
            if not target_device:
                return self.response_formatter.format_error_response(
                    "Device Not Found",
                    f"FTTH OLT device '{device_name}' not found",
                    ["Check device name spelling", "Verify device exists", "Try listing all devices first"]
                )
            
            # Get detailed device information
            device_summary = target_device.get_health_summary()
            
            # Generate LLM analysis
            messages = [
                {
                    "role": "system",
                    "content": "You are a network infrastructure analyst. Provide detailed analysis of the specific FTTH OLT device, including configuration assessment, performance insights, and recommendations."
                },
                {
                    "role": "user", 
                    "content": f"Query: {query}\n\nDevice Details for {device_summary['name']}:\n" +
                              f"- Region: {device_summary['region']}\n" +
                              f"- Environment: {device_summary['environment']}\n" +
                              f"- Bandwidth: {device_summary['bandwidth_gbps']}Gbps\n" +
                              f"- Service Count: {device_summary['service_count']}\n" +
                              f"- Inmanta Managed: {device_summary['managed_by_inmanta']}\n" +
                              f"- ESI Name: {device_summary.get('esi_name', 'ESI_' + device_summary['name'])}\n" +
                              f"- Connection Type: {device_summary.get('connection_type', 'N/A')}\n" +
                              f"- Complete Config: {device_summary.get('complete_config', False)}"
                }
            ]
            
            llm_response = await self.llm_port.generate_response(messages)
            return llm_response
            
        except Exception as e:
            return self.response_formatter.format_error_response(
                "Device Details Error",
                f"Failed to get device details: {str(e)}",
                ["Check device name", "Verify network connectivity", "Try a simpler query"]
            )
    
    async def _execute_original_complex_analysis_strategy(self, query: str, guidance: Dict[str, Any]) -> str:
        """Execute complex analysis with comprehensive intelligence"""
        try:
            # Fetch comprehensive data
            devices = await self.network_port.fetch_ftth_olts()
            
            if not devices:
                return self.response_formatter.format_error_response(
                    "No Data Available",
                    "No FTTH OLT devices available for analysis",
                    ["Check network connectivity", "Verify data sources", "Contact system administrator"]
                )
            
            # Build comprehensive context
            analysis_context = {
                "total_devices": len(devices),
                "regions": {},
                "environments": {},
                "bandwidth_distribution": {},
                "management_status": {"inmanta_managed": 0, "unmanaged": 0},
                "service_stats": {"total_services": 0, "avg_services": 0},
                "configuration_issues": []
            }
            
            # Analyze devices
            total_services = 0
            for device in devices:
                summary = device.get_health_summary()
                
                # Regional distribution
                region = summary["region"]
                analysis_context["regions"][region] = analysis_context["regions"].get(region, 0) + 1
                
                # Environment distribution  
                env = summary["environment"]
                analysis_context["environments"][env] = analysis_context["environments"].get(env, 0) + 1
                
                # Bandwidth distribution
                bw = f"{summary['bandwidth_gbps']}Gbps"
                analysis_context["bandwidth_distribution"][bw] = analysis_context["bandwidth_distribution"].get(bw, 0) + 1
                
                # Management status
                if summary["managed_by_inmanta"]:
                    analysis_context["management_status"]["inmanta_managed"] += 1
                else:
                    analysis_context["management_status"]["unmanaged"] += 1
                
                # Service statistics
                services = summary["service_count"]
                total_services += services
                
                # Configuration issues
                if not summary.get("complete_config", True):
                    analysis_context["configuration_issues"].append({
                        "device": summary["name"],
                        "issue": "Incomplete configuration",
                        "managed": summary["managed_by_inmanta"]
                    })
            
            analysis_context["service_stats"]["total_services"] = total_services
            analysis_context["service_stats"]["avg_services"] = total_services / len(devices) if devices else 0
            
            # Generate comprehensive LLM analysis
            messages = [
                {
                    "role": "system",
                    "content": "You are a senior network infrastructure consultant. Provide comprehensive analysis of the FTTH OLT network deployment with strategic insights, operational recommendations, and executive-level summary."
                },
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nComprehensive Network Analysis:\n\n" +
                              f"Total FTTH OLT Devices: {analysis_context['total_devices']}\n\n" +
                              f"Regional Distribution: {dict(analysis_context['regions'])}\n" +
                              f"Environment Distribution: {dict(analysis_context['environments'])}\n" +
                              f"Bandwidth Distribution: {dict(analysis_context['bandwidth_distribution'])}\n\n" +
                              f"Management Status: {analysis_context['management_status']['inmanta_managed']} Inmanta-managed, " +
                              f"{analysis_context['management_status']['unmanaged']} unmanaged\n\n" +
                              f"Service Statistics: {analysis_context['service_stats']['total_services']} total services, " +
                              f"{analysis_context['service_stats']['avg_services']:.1f} average per device\n\n" +
                              f"Configuration Issues: {len(analysis_context['configuration_issues'])} devices with issues\n" +
                              f"Issues: {analysis_context['configuration_issues'][:3]}"
                }
            ]
            
            llm_response = await self.llm_port.generate_response(messages)
            return llm_response
            
        except Exception as e:
            return self.response_formatter.format_error_response(
                "Complex Analysis Error",
                f"Failed to perform analysis: {str(e)}",
                ["Check network connectivity", "Verify data availability", "Try a simpler query"]
            )
    
    def _extract_region_from_query(self, query: str) -> Optional[str]:
        """Extract region filter from query"""
        query_lower = query.lower()
        regions = ["hobo", "gent", "roes", "asse"]
        
        for region in regions:
            if region in query_lower:
                return region.upper()
        return None
    
    def _extract_device_name_from_query(self, query: str) -> Optional[str]:
        """Extract device name from query"""
        import re
        
        # Look for OLT device pattern (e.g., OLT17PROP01)
        olt_pattern = r'\bOLT\d+[A-Z]+\d+\b'
        matches = re.findall(olt_pattern, query.upper())
        
        if matches:
            return matches[0]
        
        # Look for other device patterns
        device_patterns = [r'\bCINAALSA\d+\b', r'\bSRPTRO\d+\b']
        for pattern in device_patterns:
            matches = re.findall(pattern, query.upper())
            if matches:
                return matches[0]
        
        return None