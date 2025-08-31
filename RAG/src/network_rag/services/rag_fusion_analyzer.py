# src/network_rag/services/rag_fusion_analyzer.py
"""RAG Fusion analysis service for intelligent tool selection"""

from typing import Dict, Any, List
from ..controller.document_controller import DocumentController


class RAGFusionAnalyzer:
    """Handles RAG fusion search and tool recommendation logic"""
    
    def __init__(self, document_controller: DocumentController):
        self.document_controller = document_controller
    
    async def analyze_query_for_tool_selection(self, query: str) -> Dict[str, Any]:
        """Main entry point for RAG fusion analysis"""
        
        try:
            # Multiple search strategies for higher confidence
            documents = await self._perform_fusion_search(query)
            
            if documents:
                return await self._analyze_documents_for_guidance(query, documents)
            else:
                return self._fallback_guidance(query)
                
        except Exception as e:
            print(f"RAG fusion analysis failed: {e}")
            return self._fallback_guidance(query)
    
    async def _perform_fusion_search(self, query: str) -> List[Any]:
        """Perform multiple search strategies and combine results"""
        
        search_strategies = [
            f"tool selection for: {query}",
            f"how to handle query: {query}",  
            f"MCP tool for {query}",
            f"network analysis approach for: {query}"
        ]
        
        all_documents = []
        
        for search_query in search_strategies:
            try:
                documents = await self.document_controller.search_documents(
                    query=search_query,
                    limit=3,
                    use_vector_search=True
                )
                all_documents.extend(documents)
            except Exception as e:
                print(f"Search failed for '{search_query}': {e}")
                continue
        
        return all_documents
    
    async def _analyze_documents_for_guidance(self, query: str, documents: List[Any]) -> Dict[str, Any]:
        """Analyze search results to provide tool guidance"""
        
        # Tool mention analysis
        tool_scores = {
            'list_network_devices': 0,
            'get_device_details': 0, 
            'query_network_resources': 0
        }
        
        # Analysis type patterns
        analysis_patterns = {
            'device_listing': 0,
            'device_details': 0,
            'complex_analysis': 0
        }
        
        # PRIORITY: Score based on query content first (higher weight)
        query_lower = query.lower()
        
        # Device listing patterns - queries asking for multiple devices
        if any(word in query_lower for word in ['how many', 'count', 'list all', 'show all', 'inventory']):
            analysis_patterns['device_listing'] += 3  # Higher weight for query content
        if 'show me' in query_lower and any(word in query_lower for word in ['ftth olts', 'devices', 'olts']):
            analysis_patterns['device_listing'] += 3  # "Show me FTTH OLTs..." = listing
        if any(word in query_lower for word in ['olts in', 'devices in', 'ftth olts']) and any(word in query_lower for word in ['region', 'hobo', 'gent', 'asse']):
            analysis_patterns['device_listing'] += 4  # Regional device queries = listing
        
        # Device details patterns - queries about specific single devices
        if any(word in query_lower for word in ['specific', 'details for', 'configuration of']):
            analysis_patterns['device_details'] += 3
        if 'show me' in query_lower and any(word in query_lower for word in ['olt17prop01', 'specific device']):
            analysis_patterns['device_details'] += 3  # "Show me OLT17PROP01" = details
        
        # Complex analysis patterns
        if any(word in query_lower for word in ['impact', 'analysis', 'relationships', 'depends on']):
            analysis_patterns['complex_analysis'] += 3
        
        recommendations = []
        confidence_score = 0
        
        # Analyze top documents
        for doc in documents[:5]:
            content = self._get_document_content(doc).lower()
            title = self._get_document_title(doc).lower()
            
            # Score tool mentions
            for tool_name in tool_scores.keys():
                if tool_name in title or tool_name in content:
                    tool_scores[tool_name] += 2
                    confidence_score += 1
            
            # Score analysis patterns
            if any(word in content for word in ['inventory', 'count', 'list all', 'how many']):
                analysis_patterns['device_listing'] += 1
                
            if any(word in content for word in ['specific device', 'configuration', 'details for']):
                analysis_patterns['device_details'] += 1
                
            if any(word in content for word in ['impact', 'analysis', 'cross-reference', 'relationships']):
                analysis_patterns['complex_analysis'] += 1
            
            # Extract recommendations
            self._extract_recommendations(content, recommendations)
        
        # Determine best matches
        best_tool = max(tool_scores.items(), key=lambda x: x[1])
        best_analysis = max(analysis_patterns.items(), key=lambda x: x[1])
        
        # Calculate confidence
        confidence_level = self._calculate_confidence(confidence_score)
        
        return {
            'confidence': confidence_level,
            'tool_recommendation': best_tool[0] if best_tool[1] > 0 else None,
            'analysis_type': best_analysis[0],
            'approach': self._determine_approach(query, best_analysis[0]),
            'reasoning': self._generate_reasoning(best_tool[0], best_analysis[0]),
            'recommendations': recommendations[:3],
            'docs_analyzed': len(documents)
        }
    
    def _fallback_guidance(self, query: str) -> Dict[str, Any]:
        """Provide guidance when RAG search fails"""
        
        query_lower = query.lower()
        
        # Pattern-based fallback logic - improved pattern matching
        device_listing_score = 0
        device_details_score = 0
        
        # Device listing patterns
        if any(word in query_lower for word in ['how many', 'count', 'list all', 'show all', 'inventory']):
            device_listing_score += 3
        if 'show me' in query_lower and any(word in query_lower for word in ['ftth olts', 'devices', 'olts']):
            device_listing_score += 3
        if any(word in query_lower for word in ['olts in', 'devices in', 'ftth olts']) and any(word in query_lower for word in ['region', 'hobo', 'gent', 'asse']):
            device_listing_score += 4
            
        # Device details patterns  
        if any(word in query_lower for word in ['specific', 'details for', 'configuration of']):
            device_details_score += 3
        if 'show me' in query_lower and any(word in query_lower for word in ['olt17prop01', 'specific device']):
            device_details_score += 3
        if any(device in query_lower for device in ['olt17prop01', 'cinaalsa01', 'specific']):
            device_details_score += 3
            
        if device_listing_score > device_details_score and device_listing_score > 0:
            return {
                'confidence': 'MEDIUM',
                'tool_recommendation': 'list_network_devices',
                'analysis_type': 'device_listing',
                'approach': 'Device inventory approach (fallback)',
                'reasoning': 'Query pattern suggests device listing',
                'recommendations': ['Use list_network_devices for inventory queries'],
                'docs_analyzed': 0
            }
        elif device_details_score > 0:
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
    
    def _get_document_content(self, doc) -> str:
        """Extract content from document object"""
        if hasattr(doc, 'content'):
            return doc.content
        return str(doc)
    
    def _get_document_title(self, doc) -> str:
        """Extract title from document object"""
        if hasattr(doc, 'title'):
            return doc.title
        return ""
    
    def _extract_recommendations(self, content: str, recommendations: List[str]):
        """Extract recommendations from document content"""
        if 'recommendation' in content or 'use' in content:
            lines = content.split('\n')
            for line in lines:
                if ('use' in line or 'recommend' in line) and len(line) < 150:
                    cleaned = line.strip()
                    if cleaned and cleaned not in recommendations:
                        recommendations.append(cleaned)
    
    def _calculate_confidence(self, score: int) -> str:
        """Calculate confidence level based on score"""
        if score > 3:
            return "HIGH"
        elif score > 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _determine_approach(self, query: str, analysis_type: str) -> str:
        """Determine the best approach based on query analysis"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how many', 'list all', 'show me all', 'count']):
            return "Device inventory and listing approach"
        elif any(word in query_lower for word in ['configuration of', 'details for', 'show me', 'get info']):
            return "Specific device configuration analysis"
        elif any(word in query_lower for word in ['impact', 'happens if', 'connected to', 'depends on']):
            return "Cross-system impact and dependency analysis"
        else:
            return f"Intelligent {analysis_type.replace('_', ' ')} approach"
    
    def _generate_reasoning(self, tool: str, analysis_type: str) -> str:
        """Generate reasoning for tool recommendation"""
        
        if 'list_network_devices' in tool:
            return "Query requests device inventory or counts - best served by listing tool"
        elif 'get_device_details' in tool:
            return "Query asks for specific device information - requires detailed configuration tool"
        elif 'query_network_resources' in tool:
            return "Query requires cross-system analysis or impact assessment - needs intelligent analysis"
        else:
            return f"Query pattern suggests {analysis_type.replace('_', ' ')} approach"