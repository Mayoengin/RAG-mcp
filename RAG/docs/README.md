# 🚀 Network RAG System - Documentation

## 📚 Complete System Documentation

This directory contains comprehensive visualizations and documentation for the Network RAG System with Vectorized Health Knowledge.

### 📋 Available Documents

| Document | Description | Purpose |
|----------|-------------|---------|
| [**System Flow Visualization**](./system_flow_visualization.md) | Complete end-to-end system execution flow | Understanding how queries flow through the entire system |
| [**Knowledge Base Visualization**](./knowledge_base_visualization.md) | Detailed knowledge base structure and vectorization | Understanding how knowledge is stored, vectorized, and retrieved |
| This README | Navigation and overview | Quick reference to all documentation |

## 🎯 Quick Navigation

### 🔄 Want to understand the complete system flow?
**→ [System Flow Visualization](./system_flow_visualization.md)**
- High-level architecture diagram
- 6-phase detailed execution flow
- Component interaction patterns
- Performance metrics and timing

### 🧠 Want to understand the knowledge base structure?
**→ [Knowledge Base Visualization](./knowledge_base_visualization.md)**
- Knowledge base layers and components
- Vector embedding architecture (384D)
- Health rules structure and examples
- Query-time search process

## 📊 System Overview

```
🏗️ NETWORK RAG SYSTEM ARCHITECTURE

User Query
    ↓
📡 MCP Layer (Standard MCP Tools)
    ↓  
🧠 Intelligence Engine (RAG Fusion + Query Controller)
    ↓
🗄️ Knowledge Base (Vectorized Health Rules + Documents)
    ↓
🌐 Data Sources (Network Devices + Mock/Real Data)
    ↓
🤖 AI Services (LM Studio + Vector Engine)
    ↓
📋 Formatted Response (Health Analysis + LLM Insights)
```

## 🚀 Key Features Documented

### ✅ **Vectorized Health Knowledge**
- 384-dimensional embeddings for health rules
- Semantic similarity search with cosine distance
- MD5 hash-based vector generation with semantic boosting
- Real-time health rule matching and retrieval

### ✅ **Intelligent Query Processing** 
- RAG fusion with 4 parallel search strategies
- Automatic tool selection via pattern analysis
- Multi-strategy document retrieval and fusion
- Context-aware LLM integration

### ✅ **Network Device Integration**
- Real-time FTTH OLT data retrieval
- Regional filtering (HOBO, GENT, ROES, ASSE)
- Health scoring with knowledge-based rules
- Configuration issue detection and recommendations

### ✅ **LLM-Powered Analysis**
- LM Studio integration for intelligent responses
- Network engineering insights and recommendations
- Context-aware device assessment
- Detailed markdown response formatting

## 🎯 Documentation Usage Guide

### For **System Architects**:
Start with [System Flow Visualization](./system_flow_visualization.md) to understand the complete architecture and data flow patterns.

### For **Data Engineers**:
Focus on [Knowledge Base Visualization](./knowledge_base_visualization.md) to understand vector embeddings, storage structures, and search algorithms.

### For **Developers**:
Both documents provide implementation details, component interactions, and performance characteristics.

### For **Network Engineers**:
The health analysis sections in both documents explain how network device health is assessed using vectorized knowledge.

## 📈 Performance Characteristics

| Component | Typical Duration | Key Operations |
|-----------|------------------|----------------|
| System Initialization | ~2s | Health rules loading, LM Studio connection |
| Query Analysis | ~200ms | Pattern matching, tool selection |
| Knowledge Search | ~300ms | Vector similarity search |
| Data Retrieval | ~100ms | Network device fetching |
| Health Analysis | ~150ms/device | Vector search, rule evaluation |
| LLM Generation | ~4-6s | HTTP request to LM Studio (256 tokens) |
| Response Assembly | ~50ms | Markdown formatting |
| **Total Demo** | **~12-15 seconds** | **Complete system demonstration** |

## 🔍 Vector Search Details

- **Embedding Dimensions**: 384D vectors
- **Similarity Method**: Cosine distance calculation  
- **Search Algorithm**: Linear scan with similarity ranking
- **Semantic Enhancement**: Keyword-based dimension boosting
- **Typical Similarity Scores**: Range [-1, 1], demo shows -0.377

## 🌟 System Capabilities

### Current Implementation:
- ✅ 3 health rule types (FTTH OLT, Mobile Modem, Environment-specific)
- ✅ 4 network regions with filtering
- ✅ Real-time device health scoring
- ✅ LLM-powered intelligent analysis
- ✅ Knowledge-driven recommendations

### Future Expansion:
- 📈 Additional device types and vendors
- 📈 Historical trend analysis
- 📈 Predictive health modeling
- 📈 Real-time monitoring integration

---

## 🤝 Getting Started

1. **Understanding the System**: Start with [System Flow Visualization](./system_flow_visualization.md)
2. **Deep Dive into Knowledge**: Read [Knowledge Base Visualization](./knowledge_base_visualization.md) 
3. **Run the Demo**: Execute `python3 main.py` in the root directory
4. **Explore Interactively**: Choose interactive mode for custom queries

## 📞 Documentation Navigation

- 📊 **System Flow** → [system_flow_visualization.md](./system_flow_visualization.md)
- 🧠 **Knowledge Base** → [knowledge_base_visualization.md](./knowledge_base_visualization.md)
- 🏠 **Project Root** → [../README.md](../README.md) (if exists)
- 💻 **Main Demo** → [../main.py](../main.py)

---

*This documentation provides comprehensive coverage of the Network RAG System's architecture, components, and operational characteristics. Each document includes detailed diagrams, code examples, and performance metrics to support development, deployment, and maintenance activities.*