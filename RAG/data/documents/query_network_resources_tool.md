# query_network_resources MCP Tool

## Purpose
The `query_network_resources` tool performs intelligent analysis of network infrastructure, cross-referencing multiple data sources to provide insights, impact analysis, and complex relationship mapping. Use this tool for advanced network intelligence questions.

## When to Use This Tool

### Question Patterns That Should Use This Tool:
- "What happens if [device] fails?"
- "Which devices are connected to [device]?"
- "Show me the network path from [device A] to [device B]"
- "What's the impact of [device] going down?"
- "Analyze the blast radius of [failure scenario]"
- "Which devices have incomplete configurations?"
- "How are [device type A] connected to [device type B]?"
- "Map dependencies between [components]"

### Example Queries:
- "What would happen if CINMECHA01 goes down?"
- "Which FTTH OLTs are connected to BNGASSE90?"
- "Show me incomplete configurations and prioritize them"
- "Map the network path from OLT17PROP01 to BNG"
- "Which devices depend on CINAALSA01 LAG configurations?"
- "Analyze mobile modem integration with FTTH infrastructure"

## Tool Parameters

### Required Parameters:
- **query**: Natural language description of what you want to analyze

### Optional Parameters:
- **include_recommendations**: 
  - Type: boolean
  - Default: true
  - Whether to include actionable recommendations
  
- **session_id**: 
  - Type: string
  - Optional session tracking for conversation context

## Types of Analysis This Tool Performs

### Impact Analysis:
- Identifies devices that would be affected by failures
- Maps primary and secondary impact zones
- Suggests recovery strategies
- Highlights single points of failure

### Connectivity Mapping:
- Traces network paths between devices
- Identifies intermediate connections (LAGs, PXCs)
- Maps CIN node to FTTH OLT relationships
- Shows BNG to OLT connectivity

### Configuration Analysis:
- Identifies incomplete or missing configurations
- Prioritizes fixes by production impact
- Suggests remediation timelines
- Compares configuration completeness across devices

### Cross-Reference Analysis:
- Links LAG devices to FTTH OLTs
- Maps team responsibilities to device types
- Connects mobile infrastructure to core network
- Identifies integration points between systems

## Data Sources This Tool Accesses
The tool intelligently combines data from:
- **FTTH OLT configurations** (devices across multiple regions)
- **LAG configurations** (link aggregation groups across devices)
- **PXC cross-connects** (cross-connect ports for integration)
- **Mobile modem data** (Nokia hardware platforms)
- **Team assignments** (operational teams for network management)

## Response Format Structure

### Analysis Header:
- Query being analyzed
- Type of analysis performed

### Device-Specific Sections:
- **FTTH OLT Analysis**: Regional distribution, connectivity status
- **LAG Device Analysis**: Configuration details, dependencies  
- **PXC Analysis**: Cross-connect mappings, integration points
- **Mobile Infrastructure**: Hardware inventory, VPN subscribers
- **Team Structure**: Responsibilities and escalation paths

### Intelligence Sections:
- **Connectivity Analysis**: How devices are connected
- **Impact Assessment**: What fails if device goes down
- **Dependency Mapping**: Which devices depend on others
- **Configuration Status**: Completeness and issues

### Recommendations:
- **Immediate Actions**: Critical fixes needed now
- **Short-term Planning**: Improvements for next 1-4 weeks  
- **Long-term Strategy**: Architectural improvements

## Typical Use Cases

### Failure Impact Analysis:
```
Query: "What happens if CINMECHA01 fails?"
Analysis Type: Impact assessment and blast radius
Result: 
- Lists affected FTTH OLTs
- Shows backup CIN node options
- Identifies service disruption scope
- Provides recovery recommendations
```

### Network Path Tracing:
```
Query: "Map network path from OLT17PROP01 to BNG"
Analysis Type: Connectivity mapping
Result:
- Traces OLT → CIN → LAG → BNG path
- Identifies intermediate devices
- Shows redundancy options
- Highlights potential bottlenecks
```

### Configuration Management:
```
Query: "Show incomplete configurations by priority"
Analysis Type: Configuration analysis  
Result:
- Lists devices with missing configs
- Prioritizes by production impact
- Suggests remediation timeline
- Identifies common configuration gaps
```

### Integration Analysis:
```
Query: "How do mobile modems integrate with FTTH?"
Analysis Type: Cross-system integration
Result:
- Maps mobile modem VPN subscribers
- Shows FTTH infrastructure overlap
- Identifies potential integration points
- Suggests unified management approach
```

## What This Tool Does NOT Do
- Does not provide simple device counts (use list_network_devices)
- Does not show single device details (use get_device_details)
- Does not make configuration changes
- Does not access real-time operational data

## Intelligence Keywords That Trigger Advanced Analysis

### Regional Analysis:
- Keywords: "HOBO", "GENT", "region", "area"
- Triggers region-specific device analysis

### Connectivity Analysis:  
- Keywords: "connected", "path", "routing", "connectivity"
- Triggers network path mapping

### Impact Analysis:
- Keywords: "fails", "down", "impact", "blast radius", "affects"
- Triggers failure impact assessment

### Configuration Analysis:
- Keywords: "incomplete", "configuration", "missing", "setup"
- Triggers configuration completeness analysis

### Team/Responsibility Analysis:
- Keywords: "team", "responsible", "notify", "escalation"
- Triggers organizational analysis

## Data Interpretation Guidance

### Status Indicators:
- **✅ Operational**: Device fully configured and operational
- **⚠️ Needs Attention**: Incomplete configuration or issues
- **❌ Critical**: Major problems requiring immediate attention

### Priority Levels:
- **🔴 Critical**: Production impact, immediate action required
- **🟡 High**: Significant impact, address within days
- **🟢 Medium**: Minor impact, address during maintenance

### Confidence Indicators:
- **High Confidence**: Analysis based on complete data
- **Medium Confidence**: Analysis based on partial data
- **Low Confidence**: Limited data available, assumptions made

## Advanced Query Examples

### Multi-Device Analysis:
```
"Which LAG devices support FTTH OLTs and what's the redundancy?"
→ Cross-references LAG and FTTH data for dependency mapping
```

### Team-Based Analysis:
```  
"If MOBILE team is unavailable, which other teams can handle mobile infrastructure?"
→ Analyzes team responsibilities and backup capabilities
```

### Capacity Planning:
```
"Show me HOBO region capacity utilization and expansion needs"
→ Analyzes current deployment and growth requirements
```

### Technology Integration:
```
"How should we integrate Nokia mobile modems with existing FTTH infrastructure?"
→ Provides architectural recommendations for convergence
```