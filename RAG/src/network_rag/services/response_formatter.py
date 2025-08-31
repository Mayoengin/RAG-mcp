# src/network_rag/services/response_formatter.py
"""Response formatting service for consistent output across MCP tools"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseFormatter:
    """Centralized response formatting for MCP tools"""
    
    def format_network_analysis(
        self, 
        query: str,
        analysis_type: str,
        data: Dict[str, Any],
        confidence: str = "MEDIUM",
        recommendations: Optional[List[str]] = None
    ) -> str:
        """Format network analysis response"""
        
        parts = [
            f"# Network Analysis: {analysis_type.replace('_', ' ').title()}\n",
            f"**Query:** {query}\n",
            f"**Confidence:** {confidence}\n",
            f"**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        ]
        
        # Add main content
        if 'summary' in data:
            parts.extend([
                "## Summary\n",
                f"{data['summary']}\n\n"
            ])
        
        # Add sections
        for section_key, section_data in data.items():
            if section_key == 'summary':
                continue
                
            section_title = section_key.replace('_', ' ').title()
            parts.append(f"## {section_title}\n")
            
            if isinstance(section_data, list):
                for item in section_data:
                    parts.append(f"- {item}\n")
            elif isinstance(section_data, dict):
                for key, value in section_data.items():
                    parts.append(f"**{key}:** {value}\n")
            else:
                parts.append(f"{section_data}\n")
            
            parts.append("\n")
        
        # Add recommendations
        if recommendations:
            parts.extend([
                "## Recommendations\n"
            ])
            for rec in recommendations:
                parts.append(f"💡 {rec}\n")
        
        return "".join(parts)
    
    def format_device_list(
        self,
        device_type: str,
        devices: List[Dict[str, Any]], 
        total_count: int,
        filters_applied: Optional[Dict[str, str]] = None
    ) -> str:
        """Format device listing response"""
        
        parts = [
            f"# {device_type.replace('_', ' ').title()} Inventory\n",
            f"**Total Found:** {total_count}\n",
            f"**Displaying:** {len(devices)}\n"
        ]
        
        if filters_applied:
            parts.append("**Filters Applied:** ")
            filters = [f"{k}={v}" for k, v in filters_applied.items() if v]
            parts.append(f"{', '.join(filters)}\n" if filters else "None\n")
        
        parts.append("\n")
        
        # Device list
        if devices:
            for i, device in enumerate(devices, 1):
                status = self._get_device_status(device)
                parts.extend([
                    f"## {i}. {device.get('name', 'Unknown')}\n",
                    f"**Status:** {status}\n"
                ])
                
                # Add key fields based on device type
                if device_type == 'ftth_olt':
                    parts.extend([
                        f"**Environment:** {device.get('environment', 'N/A')}\n",
                        f"**Region:** {device.get('region', 'N/A')}\n"
                    ])
                elif device_type == 'lag':
                    parts.extend([
                        f"**LAG ID:** {device.get('lag_id', 'N/A')}\n",
                        f"**Description:** {device.get('description', 'N/A')}\n"
                    ])
                elif device_type == 'mobile_modem':
                    parts.extend([
                        f"**Hardware:** {device.get('hardware_type', 'N/A')}\n",
                        f"**Subscriber:** {device.get('mobile_subscriber_id', 'N/A')}\n"
                    ])
                
                parts.append("\n")
        else:
            parts.append("No devices found matching the criteria.\n")
        
        return "".join(parts)
    
    def format_device_details(
        self,
        device_name: str,
        device_type: str, 
        config_data: Dict[str, Any]
    ) -> str:
        """Format detailed device configuration response"""
        
        parts = [
            f"# Device Configuration: {device_name}\n",
            f"**Type:** {device_type.replace('_', ' ').title()}\n",
            f"**Status:** {self._get_device_status(config_data)}\n\n"
        ]
        
        # Configuration sections
        sections = {
            'basic_config': 'Basic Configuration',
            'network_config': 'Network Configuration', 
            'service_config': 'Service Configuration',
            'connection_config': 'Connection Configuration'
        }
        
        for section_key, section_title in sections.items():
            if section_key in config_data:
                parts.extend([
                    f"## {section_title}\n",
                    self._format_config_section(config_data[section_key]),
                    "\n"
                ])
        
        return "".join(parts)
    
    def format_error_response(
        self,
        error_type: str,
        message: str,
        suggestions: Optional[List[str]] = None
    ) -> str:
        """Format error response"""
        
        parts = [
            f"# Error: {error_type}\n",
            f"❌ {message}\n\n"
        ]
        
        if suggestions:
            parts.extend([
                "## Suggestions\n"
            ])
            for suggestion in suggestions:
                parts.append(f"💡 {suggestion}\n")
        
        return "".join(parts)
    
    def format_rag_guidance(self, guidance: Dict[str, Any]) -> List[str]:
        """Format RAG guidance information"""
        
        return [
            f"## Knowledge Base Guidance\n",
            f"**Confidence Level:** {guidance.get('confidence', 'UNKNOWN')}\n",
            f"**Recommended Tool:** {guidance.get('tool_recommendation', 'N/A')}\n",
            f"**Analysis Approach:** {guidance.get('approach', 'N/A')}\n",
            f"**Reasoning:** {guidance.get('reasoning', 'N/A')}\n",
            f"**Documents Analyzed:** {guidance.get('docs_analyzed', 0)}\n\n"
        ]
    
    def _get_device_status(self, device: Dict[str, Any]) -> str:
        """Determine device status with emoji"""
        
        # Check various status indicators
        if device.get('operational', True):
            if device.get('complete_config', True):
                return "✅ Operational"
            else:
                return "⚠️ Needs Configuration"
        else:
            return "❌ Issues Detected"
    
    def _format_config_section(self, section_data: Dict[str, Any]) -> str:
        """Format a configuration section"""
        
        lines = []
        for key, value in section_data.items():
            formatted_key = key.replace('_', ' ').title()
            if value is not None:
                lines.append(f"- **{formatted_key}:** {value}")
            else:
                lines.append(f"- **{formatted_key}:** Not configured")
        
        return "\n".join(lines)