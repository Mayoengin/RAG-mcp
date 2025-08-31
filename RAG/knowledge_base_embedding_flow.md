# Knowledge Base Embedding & Retrieval Flow

## 🔍 Complete Knowledge Base Architecture

```mermaid
graph TB
    subgraph "Document Ingestion Pipeline"
        A[Document Creation] --> B[Content Validation]
        B --> C[Auto-Generate Keywords]
        C --> D[LLM Embedding Generation]
        D --> E[Vector Index Storage]
        E --> F[Document Storage]
    end
    
    subgraph "Query Processing Pipeline"  
        G[User Query] --> H[Query Embedding]
        H --> I[Vector Similarity Search]
        I --> J[Cosine Similarity Calculation]
        J --> K[Business Value Ranking]
        K --> L[Quality Filtering]
    end
    
    subgraph "Storage Layer"
        M[MongoDB Documents Collection]
        N[MongoDB Vector Index Collection] 
        O[LLM Service for Embeddings]
    end
    
    F --> M
    E --> N
    D --> O
    H --> O
    I --> N
    L --> M
    
    style A fill:#e3f2fd
    style G fill:#f3e5f5
    style M fill:#e8f5e8
    style N fill:#fff3e0
```

## 📊 Document Embedding Process

```mermaid
sequenceDiagram
    participant Admin as Admin/System
    participant DC as Document Controller
    participant LLM as LLM Port
    participant KB as Knowledge Port
    participant VS as Vector Search Port
    participant Mongo as MongoDB
    
    Admin->>DC: create_document(title, content, type)
    
    DC->>DC: validate_content_quality()
    Note over DC: Business Rule: Content ≥50 chars, Title ≥5 chars
    
    DC->>LLM: extract_keywords(content, max=8)
    LLM-->>DC: ["FTTH", "OLT", "configuration", ...]
    
    DC->>LLM: generate_embedding(content)
    Note over LLM: Creates 384-dimensional vector
    LLM-->>DC: [0.123, -0.456, 0.789, ...]
    
    DC->>KB: store_document(document)
    KB->>Mongo: Insert into documents collection
    Mongo-->>KB: document_id
    KB-->>DC: document_id
    
    DC->>VS: index_document(document, embedding)
    VS->>Mongo: Insert into vector_index collection
    Note over Mongo: Stores: doc_id, embedding, metadata
    Mongo-->>VS: success
    VS-->>DC: success
    
    DC-->>Admin: document_id
```

## 🔍 Knowledge Retrieval Process

```mermaid
sequenceDiagram
    participant User as User Query
    participant QC as Query Controller
    participant DC as Document Controller  
    participant LLM as LLM Port
    participant VS as Vector Search Port
    participant Mongo as MongoDB
    
    User->>QC: "How to configure FTTH OLT?"
    QC->>DC: search_documents(query, use_vector_search=True)
    
    DC->>LLM: generate_embedding(query)
    Note over LLM: Query → 384-dimensional vector
    LLM-->>DC: query_embedding
    
    DC->>VS: similarity_search(query_embedding, limit=20, threshold=0.5)
    
    VS->>Mongo: Find documents in vector_index
    Note over Mongo: Calculate cosine similarity for all docs
    
    loop For Each Document
        VS->>VS: calculate_cosine_similarity(query_vec, doc_vec)
        Note over VS: similarity = dot(A,B) / (||A|| * ||B||)
    end
    
    VS->>Mongo: Get full documents where similarity ≥ 0.5
    Mongo-->>VS: [(doc1, 0.87), (doc2, 0.72), ...]
    VS-->>DC: similarity_results
    
    DC->>DC: apply_business_ranking()
    Note over DC: Rank by: relevance*0.5 + quality*0.3 + recency*0.2
    
    DC->>DC: filter_by_quality()
    Note over DC: Filter: usefulness_score > 0.3
    
    DC-->>QC: [top_relevant_documents]
    QC-->>User: Enhanced response with context
```

## 🗄️ MongoDB Storage Structure

```mermaid
graph LR
    subgraph "Documents Collection"
        A["Document {<br/>id: 'doc_123',<br/>title: 'FTTH OLT Setup',<br/>content: 'Full text...',<br/>document_type: 'guide',<br/>keywords: ['FTTH', 'OLT'],<br/>usefulness_score: 0.85,<br/>view_count: 42,<br/>created_at: timestamp<br/>}"]
    end
    
    subgraph "Vector Index Collection"
        B["Vector Index {<br/>document_id: 'doc_123',<br/>title: 'FTTH OLT Setup',<br/>document_type: 'guide',<br/>embedding: [0.123, -0.456, ...],<br/>keywords: ['FTTH', 'OLT'],<br/>usefulness_score: 0.85<br/>}"]
    end
    
    subgraph "Database Indexes"
        C["Text Indexes:<br/>• title, content (full-text)<br/>• document_type<br/>• keywords<br/>• usefulness_score<br/><br/>Vector Indexes:<br/>• document_id (unique)<br/>• document_type"]
    end
    
    A -.->|Links via document_id| B
    A --> C
    B --> C
    
    style A fill:#e8f5e8
    style B fill:#fff3e0
    style C fill:#f3e5f5
```

## 🧮 Vector Similarity Calculation

```mermaid
graph TD
    A["Query: 'FTTH OLT configuration'"] --> B[LLM Embedding Service]
    B --> C["Query Vector:<br/>[0.2, -0.1, 0.8, 0.3, ...]<br/>(384 dimensions)"]
    
    D["Document: 'FTTH OLT Setup Guide'"] --> E[Stored Embedding]
    E --> F["Doc Vector:<br/>[0.18, -0.08, 0.75, 0.28, ...]<br/>(384 dimensions)"]
    
    C --> G[Cosine Similarity Calculation]
    F --> G
    
    G --> H["Similarity = dot(query, doc) / (||query|| × ||doc||)<br/>= 0.87 (High similarity)"]
    
    H --> I{Threshold Check}
    I -->|≥ 0.5| J[Include in Results]
    I -->|< 0.5| K[Exclude from Results]
    
    style C fill:#e3f2fd
    style F fill:#f3e5f5
    style H fill:#e8f5e8
```

## 📈 Business Value Ranking Algorithm

```mermaid
graph TD
    A[Vector Search Results] --> B[Business Value Calculator]
    
    B --> C[Relevance Score<br/>similarity × 0.5]
    B --> D[Quality Score<br/>usefulness_score × 0.3]
    B --> E[Recency Score<br/>0.2 if fresh, 0.1 if stale]
    
    C --> F[Final Business Value]
    D --> F
    E --> F
    
    F --> G[Sort by Business Value DESC]
    G --> H[Apply Quality Filter<br/>usefulness_score > 0.3]
    H --> I[Return Top Results]
    
    style F fill:#fff3e0
    style I fill:#e8f5e8
```

## 🔄 RAG Fusion Integration

```mermaid
graph TB
    subgraph "Enhanced RAG Process"
        A[User Query] --> B[RAG Fusion Analyzer]
        B --> C[Knowledge Base Search]
        B --> D[Schema Analysis]
        
        C --> E[Vector Similarity Search]
        E --> F[Document Embeddings]
        F --> G[Relevant Documents Found]
        
        D --> H[Live Data Context]
        
        G --> I[Combined Intelligence]
        H --> I
        
        I --> J[Rich Context for LLM]
    end
    
    subgraph "Knowledge Base Components"
        K[Document Storage<br/>MongoDB documents]
        L[Vector Index<br/>MongoDB vector_index]
        M[Embedding Service<br/>LLM Port]
    end
    
    E --> L
    F --> K
    E --> M
    
    style I fill:#fff3e0
    style J fill:#e8f5e8
```

## 🎯 Key Technical Details

### **Embedding Specifications:**
- **Dimension:** 384 (default, configurable)
- **Model:** Via LLM Port (configurable service)
- **Storage:** MongoDB `vector_index` collection
- **Similarity:** Cosine similarity calculation

### **Search Pipeline:**
1. **Query Embedding:** Convert text to 384-dim vector
2. **Similarity Search:** Calculate cosine similarity with all docs
3. **Filtering:** Apply quality threshold (usefulness_score > 0.3)
4. **Ranking:** Business value = relevance×0.5 + quality×0.3 + recency×0.2
5. **Return:** Top ranked documents

### **Business Rules:**
- **Content Quality:** Minimum 50 characters content, 5 characters title
- **Auto-Keywords:** LLM extracts up to 8 keywords per document
- **Similarity Threshold:** 0.5 for search inclusion
- **Quality Filter:** usefulness_score > 0.3 for results
- **Staleness:** Documents >90 days considered stale

### **Performance Features:**
- **MongoDB Indexes:** Full-text, document_type, keywords, scores
- **Batch Operations:** Bulk similarity searches supported
- **Caching:** Vector embeddings stored for reuse
- **Async:** Full async/await throughout pipeline

## 🔍 Example Search Flow

```
Query: "How many FTTH OLTs in HOBO region?"
    ↓
1. Generate embedding: [0.2, -0.1, 0.8, ...]
    ↓
2. MongoDB vector_index search
    ↓
3. Calculate similarities:
   - "FTTH OLT Management Guide" → 0.87
   - "HOBO Region Network Setup" → 0.82
   - "OLT Configuration Best Practices" → 0.78
    ↓
4. Business ranking:
   - Guide: 0.87×0.5 + 0.9×0.3 + 0.2 = 0.905
   - Setup: 0.82×0.5 + 0.85×0.3 + 0.1 = 0.765
    ↓
5. Return top 3 documents to RAG system
    ↓
6. Combine with live data context
    ↓
7. Generate intelligent response
```

This shows how your knowledge base uses semantic vector search to find the most relevant documentation and combine it with live network data for truly intelligent responses.