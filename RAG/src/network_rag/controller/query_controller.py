# src/network_rag/controller/query_controller.py
"""Query processing controller with comprehensive business logic"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import (
    QueryResult, ResultSource, SourceType, Message, MessageRole,
    NetworkPort, VectorSearchPort, LLMPort, ConversationPort,
    NetworkRAGException
)


class QueryController:
    """Central business logic for query processing and multi-source data fusion"""
    
    def __init__(
        self,
        network_port: NetworkPort,
        vector_search_port: VectorSearchPort,
        llm_port: LLMPort,
        conversation_port: ConversationPort
    ):
        self.network_port = network_port
        self.vector_search_port = vector_search_port
        self.llm_port = llm_port
        self.conversation_port = conversation_port
    
    async def process_query(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """
        Main business logic for processing user queries with multi-source intelligence
        
        Business Rules:
        1. Analyze query intent to determine required data sources
        2. Fetch data from multiple sources in parallel for efficiency
        3. Fuse data intelligently based on source reliability
        4. Generate contextual response using LLM
        5. Calculate confidence based on data quality
        """
        
        start_time = datetime.utcnow()
        query_id = f"query_{int(start_time.timestamp())}"
        
        result = QueryResult(
            query_id=query_id,
            original_query=query,
            processed_query=self._preprocess_query(query),
            primary_answer="",
            conversation_id=conversation_id,
            user_context=user_context or {}
        )
        
        try:
            # Business Rule: Intelligent query analysis
            query_intent = await self._analyze_query_intent(query)
            result.query_intent = query_intent.get("primary_intent", "information_request")
            
            # Business Rule: Multi-source data retrieval
            data_tasks = []
            
            if query_intent.get("needs_network_data", False):
                data_tasks.append(self._fetch_network_intelligence(query, result))
            
            if query_intent.get("needs_knowledge_base", True):
                data_tasks.append(self._fetch_knowledge_intelligence(query, result))
            
            if conversation_id and query_intent.get("needs_conversation_context", False):
                data_tasks.append(self._fetch_conversation_intelligence(conversation_id, result))
            
            # Execute all data gathering tasks concurrently
            await asyncio.gather(*data_tasks, return_exceptions=True)
            
            # Business Rule: Contextual response generation
            messages = await self._build_intelligent_context(query, result, conversation_id)
            llm_response = await self.llm_port.generate_response(messages)
            
            result.primary_answer = llm_response
            result.add_source(SourceType.LLM_GENERATION, "primary_llm", 0.85)
            
            # Business Rule: Multi-factor confidence calculation
            result.overall_confidence = result.calculate_overall_confidence()
            result.completeness_score = self._calculate_completeness_score(result)
            
            # Business Rule: Generate follow-up suggestions
            await self._generate_follow_up_suggestions(result)
            
            # Record processing metrics
            end_time = datetime.utcnow()
            result.processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return result
            
        except Exception as e:
            return self._handle_query_error(result, e)
    
    async def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Business logic for intelligent query intent analysis
        
        Business Rules:
        - Network queries: Contain equipment, configuration, or operational terms
        - Knowledge queries: Ask for explanations, procedures, or guidance  
        - Context queries: Reference previous conversation elements
        - Hybrid queries: Require multiple data sources
        """
        query_lower = query.lower()
        
        # Domain-specific keyword analysis
        network_indicators = {
            "equipment": ["olt", "ftth", "router", "switch", "node", "device"],
            "operational": ["status", "health", "performance", "bandwidth", "connection"],
            "configuration": ["config", "setup", "configure", "parameter", "setting"],
            "location": ["region", "hobo", "gent", "antwerp", "brussels", "site"],
            "management": ["inmanta", "managed", "control", "monitor"]
        }
        
        knowledge_indicators = {
            "explanatory": ["what", "how", "why", "explain", "describe", "define"],
            "procedural": ["steps", "procedure", "process", "guide", "tutorial"],
            "troubleshooting": ["problem", "issue", "error", "fix", "resolve", "debug"],
            "best_practices": ["best", "recommend", "should", "practice", "standard"]
        }
        
        context_indicators = ["previous", "earlier", "before", "mentioned", "continue", "also", "last"]
        
        # Calculate intent scores
        network_score = self._calculate_keyword_score(query_lower, network_indicators)
        knowledge_score = self._calculate_keyword_score(query_lower, knowledge_indicators)
        context_score = sum(1 for word in context_indicators if word in query_lower)
        
        # Business rules for intent classification
        needs_network_data = network_score > 0 or any(
            keyword in query_lower for keyword in ["show", "list", "find", "get"]
        )
        
        needs_knowledge_base = (
            knowledge_score > 0 or 
            len(query.split()) > 5 or  # Complex queries likely need documentation
            "?" in query
        )
        
        needs_conversation_context = context_score > 0
        
        # Determine primary intent
        if network_score > knowledge_score:
            primary_intent = "network_query"
        elif knowledge_score > network_score:
            primary_intent = "knowledge_query"
        elif context_score > 0:
            primary_intent = "context_query"
        else:
            primary_intent = "general_query"
        
        return {
            "primary_intent": primary_intent,
            "needs_network_data": needs_network_data,
            "needs_knowledge_base": needs_knowledge_base,
            "needs_conversation_context": needs_conversation_context,
            "network_score": network_score,
            "knowledge_score": knowledge_score,
            "context_score": context_score,
            "complexity": "high" if len(query.split()) > 10 else "medium" if len(query.split()) > 5 else "low"
        }
    
    async def _fetch_network_intelligence(self, query: str, result: QueryResult) -> None:
        """
        Business logic for intelligent network data retrieval and analysis
        
        Business Rules:
        - Extract precise filters from natural language
        - Prioritize production systems in results
        - Enrich data with health and configuration analysis
        - Provide actionable insights, not just raw data
        """
        try:
            filters = self._extract_smart_network_filters(query)
            olts = await self.network_port.fetch_ftth_olts(filters)
            
            if olts:
                # Business Rule: Intelligent data transformation
                network_intelligence = []
                
                for olt in olts[:15]:  # Limit for performance
                    health_summary = olt.get_health_summary()
                    
                    # Business Rule: Add actionable insights
                    insights = self._generate_olt_insights(olt)
                    
                    intelligence_record = {
                        **health_summary,
                        "insights": insights,
                        "priority_level": "high" if olt.is_production() else "medium",
                        "action_required": len(insights.get("issues", [])) > 0
                    }
                    
                    network_intelligence.append(intelligence_record)
                
                # Business Rule: Organize by priority
                network_intelligence.sort(
                    key=lambda x: (x["priority_level"] == "high", x["action_required"]),
                    reverse=True
                )
                
                result.supporting_data["network_intelligence"] = network_intelligence
                
                # Business Rule: Dynamic confidence based on data quality
                data_quality_score = self._assess_network_data_quality(network_intelligence)
                confidence = min(0.95, 0.7 + (data_quality_score * 0.25))
                
                result.add_source(
                    SourceType.NETWORK_API, 
                    "ftth_intelligence_engine", 
                    confidence,
                    source_name="FTTH Network Intelligence",
                    content_summary=f"Analyzed {len(network_intelligence)} network resources with insights",
                    olt_count=len(olts),
                    filters_applied=filters,
                    data_quality_score=data_quality_score
                )
                
        except Exception as e:
            result.supporting_data["network_error"] = str(e)
            result.add_limitation(f"Network data unavailable: {str(e)}")
    
    async def _fetch_knowledge_intelligence(self, query: str, result: QueryResult) -> None:
        """
        Business logic for intelligent knowledge base search and context building
        
        Business Rules:
        - Use semantic search for better relevance
        - Prioritize recent and highly-rated documents
        - Provide contextual snippets, not just titles
        - Include related topics for exploration
        """
        try:
            query_embedding = await self.llm_port.generate_embedding(result.processed_query)
            
            # Business Rule: Multi-tier search strategy
            similar_docs = await self.vector_search_port.similarity_search(
                query_embedding, 
                limit=8,
                threshold=0.6
            )
            
            if similar_docs:
                knowledge_intelligence = []
                
                for doc, similarity in similar_docs:
                    # Business Rule: Quality-based filtering
                    quality_metrics = doc.get_quality_metrics()
                    
                    if quality_metrics["usefulness_score"] < 0.3 and similarity < 0.8:
                        continue  # Skip low-quality, low-relevance docs
                    
                    intelligence_record = {
                        "title": doc.title,
                        "document_type": doc.document_type.value,
                        "content_preview": doc.get_content_preview(400),
                        "relevance_score": round(similarity, 3),
                        "quality_score": round(quality_metrics["usefulness_score"], 2),
                        "keywords": doc.keywords[:6],  # Top keywords only
                        "is_recent": quality_metrics["days_since_update"] < 30,
                        "view_count": quality_metrics["view_count"]
                    }
                    
                    knowledge_intelligence.append(intelligence_record)
                
                # Business Rule: Sort by combined relevance and quality
                knowledge_intelligence.sort(
                    key=lambda x: (x["relevance_score"] * 0.7 + x["quality_score"] * 0.3),
                    reverse=True
                )
                
                result.supporting_data["knowledge_intelligence"] = knowledge_intelligence
                
                # Business Rule: Confidence based on best matches
                if knowledge_intelligence:
                    best_match = knowledge_intelligence[0]
                    confidence = min(0.9, best_match["relevance_score"] + best_match["quality_score"] * 0.2)
                    
                    result.add_source(
                        SourceType.KNOWLEDGE_BASE,
                        "knowledge_intelligence_engine", 
                        confidence,
                        source_name="Knowledge Intelligence Engine",
                        content_summary=f"Found {len(knowledge_intelligence)} relevant documents",
                        best_relevance=best_match["relevance_score"],
                        avg_quality=sum(d["quality_score"] for d in knowledge_intelligence) / len(knowledge_intelligence)
                    )
                
        except Exception as e:
            result.supporting_data["knowledge_error"] = str(e)
            result.add_limitation(f"Knowledge search unavailable: {str(e)}")
    
    async def _fetch_conversation_intelligence(self, conversation_id: str, result: QueryResult) -> None:
        """
        Business logic for intelligent conversation context extraction
        
        Business Rules:
        - Focus on relevant recent exchanges
        - Extract key topics and unresolved questions
        - Maintain conversation continuity
        - Respect user privacy and context boundaries
        """
        try:
            conversation = await self.conversation_port.get_conversation(conversation_id)
            
            if conversation:
                # Business Rule: Extract relevant context intelligently
                recent_messages = conversation.get_recent_messages(6)
                key_topics = conversation.extract_key_topics()
                
                context_intelligence = {
                    "conversation_summary": {
                        "duration_minutes": round(conversation.get_duration_minutes(), 1),
                        "turn_count": conversation.get_turn_count(),
                        "satisfaction_score": round(conversation.calculate_satisfaction_score(), 2),
                        "main_topics": key_topics
                    },
                    "recent_context": [
                        {
                            "role": msg.role.value,
                            "content_summary": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content,
                            "timestamp": msg.timestamp.isoformat(),
                            "is_recent": msg.is_recent(minutes=15)
                        }
                        for msg in recent_messages
                        if msg.role != MessageRole.SYSTEM
                    ]
                }
                
                result.supporting_data["conversation_intelligence"] = context_intelligence
                
                # Business Rule: Context confidence based on recency and relevance
                recent_count = sum(1 for msg in recent_messages if msg.is_recent(minutes=30))
                context_confidence = min(0.8, 0.3 + (recent_count / len(recent_messages)) * 0.5)
                
                result.add_source(
                    SourceType.CONVERSATION_HISTORY,
                    conversation_id,
                    context_confidence,
                    source_name="Conversation Context Intelligence",
                    content_summary=f"Context from {len(recent_messages)} recent messages",
                    topics=key_topics,
                    satisfaction=conversation.calculate_satisfaction_score()
                )
                
        except Exception as e:
            result.supporting_data["conversation_error"] = str(e)
            result.add_limitation(f"Conversation context unavailable: {str(e)}")
    
    async def _build_intelligent_context(
        self, 
        query: str, 
        result: QueryResult, 
        conversation_id: Optional[str]
    ) -> List[Message]:
        """
        Business logic for building optimal LLM context with intelligence
        
        Business Rules:
        - Provide domain expertise in system prompt
        - Structure context for optimal LLM comprehension
        - Balance detail with token efficiency
        - Include actionable insights and recommendations
        """
        
        messages = []
        
        # Business Rule: Expert system prompt with domain knowledge
        system_content = """You are an expert network infrastructure consultant specializing in FTTH OLT equipment and telecommunications systems. You provide intelligent analysis, actionable recommendations, and clear explanations.

EXPERTISE AREAS:
- FTTH OLT configuration and troubleshooting
- Network performance analysis and optimization  
- Infrastructure planning and best practices
- Technical documentation and guidance

RESPONSE PRINCIPLES:
- Lead with key insights and actionable recommendations
- Use clear, professional language appropriate for technical audiences
- Structure complex information logically with headings and bullets when helpful
- Provide specific examples and practical steps
- Acknowledge limitations and suggest alternative approaches when needed
- Focus on business value and operational impact

When provided with network data, analyze it for:
- Configuration completeness and compliance
- Performance and capacity insights
- Potential issues and recommendations
- Operational priorities and next steps"""
        
        messages.append(Message(
            id=f"system_{int(datetime.utcnow().timestamp())}_{hash(system_content[:50]) % 10000}",
            role=MessageRole.SYSTEM,
            content=system_content
        ))
        
        # Business Rule: Add conversation context intelligently
        if conversation_id and "conversation_intelligence" in result.supporting_data:
            context_data = result.supporting_data["conversation_intelligence"]
            
            if context_data["recent_context"]:
                context_summary = "CONVERSATION CONTEXT:\n"
                for ctx in context_data["recent_context"][-3:]:  # Last 3 exchanges
                    role_icon = "👤" if ctx["role"] == "user" else "🤖"
                    context_summary += f"{role_icon} {ctx['content_summary']}\n"
                
                messages.append(Message(
                    id=f"context_{int(datetime.utcnow().timestamp())}_{hash(context_summary[:50]) % 10000}",
                    role=MessageRole.SYSTEM,
                    content=context_summary
                ))
        
        # Business Rule: Structure intelligence for optimal LLM processing
        context_parts = ["CURRENT QUERY:", f"'{query}'", ""]
        
        # Network intelligence
        if "network_intelligence" in result.supporting_data:
            network_data = result.supporting_data["network_intelligence"]
            context_parts.extend([
                "🌐 NETWORK ANALYSIS:",
                f"Found {len(network_data)} FTTH OLT resources for analysis"
            ])
            
            # Show high-priority items first
            priority_items = [item for item in network_data if item.get("priority_level") == "high"][:3]
            for item in priority_items:
                status_icon = "⚠️" if item.get("action_required") else "✅"
                context_parts.append(
                    f"{status_icon} {item['name']}: {item['environment']}, "
                    f"{item.get('connection_type', 'N/A')}, {item['bandwidth_gbps']}Gbps"
                )
                
                if item.get("insights", {}).get("issues"):
                    context_parts.append(f"   Issues: {', '.join(item['insights']['issues'][:2])}")
            
            context_parts.append("")
        
        # Knowledge intelligence  
        if "knowledge_intelligence" in result.supporting_data:
            docs = result.supporting_data["knowledge_intelligence"]
            context_parts.extend([
                "📚 KNOWLEDGE BASE:",
                f"Found {len(docs)} relevant technical documents"
            ])
            
            # Show top 2 most relevant
            for doc in docs[:2]:
                context_parts.append(
                    f"📄 {doc['title']} (relevance: {doc['relevance_score']:.2f})"
                )
                context_parts.append(f"   {doc['content_preview'][:150]}...")
            
            context_parts.append("")
        
        # Build final user message
        user_content = "\n".join(context_parts)
        messages.append(Message(
            id=f"user_{int(datetime.utcnow().timestamp())}_{hash(user_content[:50]) % 10000}",
            role=MessageRole.USER,
            content=user_content
        ))
        
        return messages
    
    def _preprocess_query(self, query: str) -> str:
        """Business rule: Clean and normalize query for better processing"""
        # Remove extra whitespace and normalize
        processed = " ".join(query.strip().split())
        
        # Expand common abbreviations
        abbreviations = {
            "OLT": "Optical Line Terminal",
            "FTTH": "Fiber To The Home", 
            "PRD": "Production",
            "UAT": "User Acceptance Testing"
        }
        
        for abbr, full in abbreviations.items():
            if abbr in processed and full not in processed:
                processed = processed.replace(abbr, f"{abbr} ({full})")
        
        return processed
    
    def _calculate_keyword_score(self, query: str, keyword_categories: Dict[str, List[str]]) -> float:
        """Business rule: Calculate weighted keyword relevance score"""
        score = 0.0
        for category, keywords in keyword_categories.items():
            category_matches = sum(1 for keyword in keywords if keyword in query)
            # Weight categories differently
            weight = 1.5 if category in ["equipment", "operational"] else 1.0
            score += category_matches * weight
        return score
    
    def _extract_smart_network_filters(self, query: str) -> Dict[str, Any]:
        """Business rule: Extract network filters using NLP techniques"""
        filters = {}
        query_lower = query.lower()
        
        # Region extraction with synonyms
        region_mapping = {
            "hobo": "HOBO", "hoboken": "HOBO",
            "gent": "GENT", "ghent": "GENT", 
            "antwerp": "ANTWERP", "antwerpen": "ANTWERP",
            "brussels": "BRUSSELS", "brussel": "BRUSSELS"
        }
        
        for variant, canonical in region_mapping.items():
            if variant in query_lower:
                filters["region"] = canonical
                break
        
        # Environment detection
        env_patterns = {
            "production": ["production", "prod", "prd", "live"],
            "uat": ["uat", "test", "testing", "staging"],
            "test": ["test", "dev", "development"]
        }
        
        for env, patterns in env_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                filters["environment"] = env.upper() if env != "uat" else "UAT"
                break
        
        # Management type
        if any(word in query_lower for word in ["inmanta", "managed"]):
            filters["managed_by_inmanta"] = True
        
        # Connection type patterns
        if any(word in query_lower for word in ["10g", "10 gbps"]):
            if any(word in query_lower for word in ["4x", "quad", "four"]):
                filters["connection_type"] = "4x10G"
            else:
                filters["connection_type"] = "1x10G"
        elif any(word in query_lower for word in ["100g", "100 gbps"]):
            filters["connection_type"] = "1x100G"
        
        return filters
    
    def _generate_olt_insights(self, olt) -> Dict[str, Any]:
        """Business rule: Generate actionable insights for OLT"""
        insights = {
            "issues": [],
            "recommendations": [],
            "status": "healthy"
        }
        
        # Configuration analysis
        if not olt.has_complete_config():
            insights["issues"].append("Incomplete configuration detected")
            insights["recommendations"].append("Complete OLT configuration setup")
            insights["status"] = "attention_required"
        
        # Environment-specific rules
        if olt.is_production() and not olt.managed_by_inmanta:
            insights["recommendations"].append("Consider Inmanta management for production OLT")
        
        # Capacity analysis
        bandwidth = olt.calculate_bandwidth_gbps()
        if bandwidth < 10:
            insights["issues"].append("Low bandwidth capacity")
            insights["recommendations"].append("Evaluate bandwidth upgrade options")
        
        return insights
    
    def _assess_network_data_quality(self, network_data: List[Dict[str, Any]]) -> float:
        """Business rule: Assess quality of network data for confidence calculation"""
        if not network_data:
            return 0.0
        
        quality_factors = []
        
        for item in network_data:
            # Completeness factor
            completeness = 1.0 if item.get("complete_config") else 0.5
            quality_factors.append(completeness)
            
            # Recency factor (production systems are more critical)
            priority_boost = 0.2 if item.get("priority_level") == "high" else 0.0
            quality_factors.append(min(1.0, completeness + priority_boost))
        
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def _calculate_completeness_score(self, result: QueryResult) -> float:
        """Business rule: Calculate how complete the answer appears to be"""
        score = 0.0
        
        # Answer length factor
        if len(result.primary_answer) > 200:
            score += 0.3
        elif len(result.primary_answer) > 100:
            score += 0.2
        elif len(result.primary_answer) > 50:
            score += 0.1
        
        # Source diversity factor
        source_types = set(source.source_type for source in result.sources)
        score += min(0.4, len(source_types) * 0.1)
        
        # Supporting data factor
        if result.supporting_data:
            score += min(0.3, len(result.supporting_data) * 0.1)
        
        return min(1.0, score)
    
    async def _generate_follow_up_suggestions(self, result: QueryResult) -> None:
        """Business rule: Generate intelligent follow-up suggestions"""
        # Based on query intent and available data
        if "network_intelligence" in result.supporting_data:
            network_data = result.supporting_data["network_intelligence"]
            
            # Suggest related queries based on the data
            if any(item.get("action_required") for item in network_data):
                result.add_suggested_question("What are the specific steps to resolve these configuration issues?")
            
            regions = set(item.get("region") for item in network_data if item.get("region"))
            if len(regions) == 1:
                region = list(regions)[0]
                result.add_suggested_question(f"Show me performance trends for {region} region")
                result.add_suggested_question(f"What are the best practices for {region} OLT management?")
            
            # Topic suggestions
            result.add_related_topic("FTTH OLT Configuration")
            result.add_related_topic("Network Performance Monitoring")
            result.add_related_topic("Infrastructure Best Practices")
        
        if "knowledge_intelligence" in result.supporting_data:
            docs = result.supporting_data["knowledge_intelligence"]
            
            # Extract common topics from found documents
            all_keywords = []
            for doc in docs[:3]:  # Top 3 documents
                all_keywords.extend(doc.get("keywords", []))
            
            # Add unique keywords as related topics
            unique_topics = list(set(all_keywords))[:5]
            for topic in unique_topics:
                result.add_related_topic(topic.title())
    
    def _handle_query_error(self, result: QueryResult, error: Exception) -> QueryResult:
        """Business rule: Handle query processing errors gracefully"""
        error_message = f"I encountered an issue processing your query: {str(error)}"
        
        # Provide helpful error context
        if "network" in str(error).lower():
            error_message += "\n\nThis appears to be a network connectivity issue. Please try again in a moment."
        elif "timeout" in str(error).lower():
            error_message += "\n\nThe query took longer than expected. Try a more specific query for faster results."
        else:
            error_message += "\n\nPlease try rephrasing your question or contact support if the issue persists."
        
        result.primary_answer = error_message
        result.overall_confidence = 0.0
        result.completeness_score = 0.0
        result.add_limitation("Query processing failed due to technical error")
        
        return result