# Schema-Aware RAG System Flow Visualization

## 🔄 Complete System Flow Diagram

```mermaid
graph TD
    A[User Query: "How many FTTH OLTs in HOBO?"] --> B[MCP Server]
    B --> C[Query Controller]
    
    C --> D[Enhanced RAG Fusion Analyzer]
    D --> E[Traditional RAG Search]
    D --> F[Schema-Aware Analysis]
    
    E --> G[Knowledge Base Documents]
    G --> H[Document Embeddings]
    H --> I[Similar Documents Found]
    
    F --> J[Schema Registry]
    F --> K[Data Quality Service]
    F --> L[Schema-Aware Context Builder]
    
    J --> M[Identify Relevant Schemas<br/>ftth_olt, team]
    K --> N[Get Live Data Samples<br/>127 OLT records]
    K --> O[Assess Data Quality<br/>87% health score]
    L --> P[Build Rich Context]
    
    I --> Q[RAG Guidance]
    P --> R[Schema Context]
    
    Q --> S[Tool Selection Logic]
    R --> S
    
    S --> T{Data Quality Check}
    T -->|High Quality 87%| U[Execute: list_network_devices]
    T -->|Low Quality <50%| V[Execute: data_quality_report]
    
    U --> W[Network Port]
    W --> X[Fetch FTTH OLTs]
    X --> Y[Filter by HOBO region]
    Y --> Z[23 devices found]
    
    Z --> AA[Response Formatter]
    R --> AA
    Q --> AA
    
    AA --> BB[Rich LLM Context:<br/>• Query + Intent<br/>• Structured Data + Schema<br/>• Quality Metrics<br/>• Business Context]
    
    BB --> CC[LLM Processing]
    CC --> DD[Intelligent Response:<br/>"Based on current data...<br/>23 FTTH OLTs in HOBO<br/>21 Production, 2 UAT<br/>Data Quality: 🟢 87%"]
    
    DD --> EE[User Response]
    
    style A fill:#e1f5fe
    style DD fill:#e8f5e8
    style BB fill:#fff3e0
    style R fill:#f3e5f5
    style Q fill:#e0f2f1
```

## 🏗️ Component Architecture

```mermaid
graph TB
    subgraph "Protocol Layer"
        A[MCP Server] --> B[Tool Definitions]
    end
    
    subgraph "Business Logic Layer"
        C[Query Controller] --> D[RAG Fusion Analyzer]
        D --> E[Response Formatter]
    end
    
    subgraph "Schema-Aware Services"
        F[Schema Registry] --> G[Network Data Schemas]
        H[Data Quality Service] --> I[Quality Assessment]
        J[Schema-Aware Context Builder] --> K[Rich Context Generation]
    end
    
    subgraph "Data Layer"
        L[Network Port] --> M[Live FTTH Data]
        N[Vector Search Port] --> O[Knowledge Base]
        P[LLM Port] --> Q[Response Generation]
    end
    
    A --> C
    C --> F
    C --> H
    C --> J
    C --> L
    C --> N
    C --> P
    
    F --> J
    H --> J
    I --> D
    K --> E
    
    style F fill:#ffebee
    style H fill:#e8f5e8
    style J fill:#fff3e0
    style C fill:#e3f2fd
```

## 📊 Data Flow Through System

```mermaid
sequenceDiagram
    participant User
    participant MCP as MCP Server
    participant QC as Query Controller
    participant RAF as RAG Fusion Analyzer
    participant SR as Schema Registry
    participant DQS as Data Quality Service
    participant SAC as Schema-Aware Context
    participant NP as Network Port
    participant LLM as LLM Port
    
    User->>MCP: "How many FTTH OLTs in HOBO?"
    MCP->>QC: execute_intelligent_network_query()
    
    QC->>RAF: analyze_query_with_data_awareness()
    RAF->>SR: get_schemas_for_query_intent()
    SR-->>RAF: [ftth_olt_schema]
    
    RAF->>DQS: get_live_data_sample("ftth_olt")
    DQS->>NP: fetch_ftth_olts()
    NP-->>DQS: [127 OLT records]
    DQS-->>RAF: DataSample + Quality Metrics
    
    RAF->>SAC: build_context_for_query()
    SAC-->>RAF: SchemaAwareContext
    RAF-->>QC: (guidance, schema_context)
    
    QC->>NP: fetch_ftth_olts() [filtered by HOBO]
    NP-->>QC: [23 HOBO OLTs]
    
    QC->>LLM: generate_response(rich_context)
    Note over LLM: Context includes:<br/>- Query intent<br/>- Data + Schema<br/>- Quality metrics<br/>- Business context
    LLM-->>QC: Intelligent response
    QC-->>MCP: Formatted response
    MCP-->>User: "23 FTTH OLTs in HOBO (87% quality)"
```

## 🔍 Schema Context Building Process

```mermaid
graph LR
    A[Query: "FTTH OLTs in HOBO"] --> B[Schema Registry]
    B --> C[Identify: ftth_olt schema]
    C --> D[Get Schema Definition]
    
    A --> E[Data Quality Service]
    E --> F[Sample Live Data]
    F --> G[Assess Quality Metrics]
    G --> H[Completeness: 95%<br/>Freshness: 90%<br/>Overall: 87%]
    
    D --> I[Schema-Aware Context Builder]
    H --> I
    
    I --> J[Rich Context Object]
    J --> K[Available Data: 127 records<br/>Quality: 🟢 Good 87%<br/>Schema: ftth_olt fields<br/>Recommendations: Proceed]
    
    style J fill:#fff3e0
    style K fill:#e8f5e8
```

## 🧠 Traditional vs Schema-Aware Comparison

```mermaid
graph TB
    subgraph "❌ Traditional RAG Flow"
        A1[Query] --> B1[Document Search]
        B1 --> C1[Tool Selection by Pattern]
        C1 --> D1[Raw Data Fetch]
        D1 --> E1[Format to Text]
        E1 --> F1[LLM sees only text]
        F1 --> G1["Vague response:<br/>'Some OLTs exist'"]
    end
    
    subgraph "✅ Schema-Aware RAG Flow"
        A2[Query] --> B2[Document Search<br/>+ Schema Analysis<br/>+ Data Quality Check]
        B2 --> C2[Data-Aware Tool Selection]
        C2 --> D2[Structured Data + Schema]
        D2 --> E2[Rich Context Builder]
        E2 --> F2[LLM sees:<br/>Data + Schema + Quality]
        F2 --> G2["Intelligent response:<br/>'23 OLTs, 87% quality,<br/>3 need attention'"]
    end
    
    style G1 fill:#ffebee
    style G2 fill:#e8f5e8
```

## 🎯 Key Innovation Visualization

```mermaid
graph TD
    A[User Query] --> B{Enhanced RAG Analysis}
    
    B --> C[Traditional Search:<br/>Knowledge Base Documents]
    B --> D[NEW: Schema Analysis:<br/>Data Structure Understanding]
    B --> E[NEW: Data Quality:<br/>Live Data Assessment]
    
    C --> F[Tool Guidance]
    D --> G[Schema Context]
    E --> H[Quality Metrics]
    
    F --> I[Combined Intelligence]
    G --> I
    H --> I
    
    I --> J[LLM receives:<br/>🔍 What to do Tool guidance<br/>📊 What data looks like Schema<br/>✅ How reliable it is Quality<br/>🎯 Why it matters Business context]
    
    J --> K[Intelligent Response]
    
    style D fill:#ffebee
    style E fill:#e8f5e8
    style G fill:#fff3e0
    style H fill:#f3e5f5
    style J fill:#e3f2fd
```

## 📈 Data Quality Impact on Tool Selection

```mermaid
graph TD
    A[Query Analysis] --> B{Data Quality Check}
    
    B -->|Quality > 80%| C[✅ Execute Standard Tool<br/>High confidence response]
    B -->|Quality 50-80%| D[⚠️ Execute with Warning<br/>Mention data concerns]
    B -->|Quality < 50%| E[🔴 Recommend Data Refresh<br/>Switch to quality report tool]
    
    C --> F[User gets: Accurate analysis]
    D --> G[User gets: Analysis + quality warning]
    E --> H[User gets: Data health report instead]
    
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#ffebee
```

This visualization shows how your Schema-Aware RAG system transforms a simple query into intelligent, context-aware responses by combining traditional RAG with real-time data schema and quality awareness.