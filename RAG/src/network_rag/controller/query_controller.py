# src/network_rag/controller/query_controller.py
"""Simplified query processing controller with only essential business logic"""

from typing import List, Dict, Any, Optional

from ..models import NetworkPort, VectorSearchPort, LLMPort
from ..services.rag_fusion_analyzer import RAGFusionAnalyzer


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
        self._document_controller = document_controller
    
    def initialize_rag_analyzer(self, document_controller):
        """Initialize RAG fusion analyzer with dependencies"""
        self.rag_analyzer = RAGFusionAnalyzer(document_controller)
    
    async def execute_intelligent_network_query(self, arguments: Dict[str, Any]) -> str:
        """Main entry point for RAG-enhanced intelligent network queries"""
        query = arguments.get("query", "")
        include_recommendations = arguments.get("include_recommendations", True)
        
        # Step 1: Use RAG fusion analysis for tool selection
        if self.rag_analyzer:
            guidance = await self.rag_analyzer.analyze_query_for_tool_selection(query)
        else:
            # RAG analyzer should always be initialized
            raise ValueError("RAG analyzer not initialized. Call initialize_rag_analyzer() first.")
        
        # Return RAG analysis results for external processing
        return {
            'query': query,
            'guidance': guidance,
            'include_recommendations': include_recommendations
        }
