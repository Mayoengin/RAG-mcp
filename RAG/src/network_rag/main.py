# src/network_rag/main.py
"""Application entry point for the Network RAG system"""

import asyncio
import json
import sys
import signal
from typing import Optional
from pathlib import Path

from .infrastructure.config import load_config, get_config
from .infrastructure.container import initialize_system, shutdown_system, get_mcp_server, health_check
from .infrastructure.logging import setup_logging
from .models import NetworkRAGException


class NetworkRAGApplication:
    """Main application class for the Network RAG system"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = None
        self.container = None
        self.mcp_server = None
        self.running = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def initialize(self):
        """Initialize the application"""
        
        print("🚀 Starting Network RAG System...")
        
        try:
            # Load configuration
            print("📋 Loading configuration...")
            self.config = load_config(self.config_file)
            
            # Setup logging
            print("📝 Setting up logging...")
            setup_logging(self.config.logging)
            
            # Initialize dependency injection container
            print("🔧 Initializing services...")
            self.container = await initialize_system(self.config)
            
            # Get MCP server
            print("🌐 Starting MCP server...")
            self.mcp_server = await get_mcp_server()
            
            print("✅ System initialized successfully!")
            
            # Print system information
            await self._print_system_info()
            
        except Exception as e:
            print(f"❌ Failed to initialize system: {e}")
            await self._cleanup()
            raise
    
    async def _print_system_info(self):
        """Print system information"""
        
        print("\n" + "="*60)
        print("🏗️  NETWORK RAG SYSTEM - READY")
        print("="*60)
        
        print(f"Environment: {self.config.environment}")
        print(f"Debug Mode: {self.config.debug}")
        print(f"Database: {self.config.database.database_name}")
        print(f"LLM Provider: {self.config.llm.provider}")
        print(f"Embedding Model: {self.config.embedding.model_name}")
        print(f"MCP Server: {self.config.mcp.server_name} v{self.config.mcp.server_version}")
        
        # Health check
        health = await health_check()
        print(f"System Health: {health['overall_status'].upper()}")
        
        if self.config.mcp.enable_rest_api:
            print(f"REST API: http://{self.config.mcp.host}:{self.config.mcp.port}")
        
        print("\n🔧 Available Services:")
        service_info = await self.container.get_service_info()
        for service in service_info['created_services']:
            print(f"  ✓ {service}")
        
        print("\n🛠️  Available MCP Tools:")
        mcp_info = self.mcp_server.get_server_info()
        print(f"  📊 {len(mcp_info['capabilities'])} capabilities available")
        for capability in mcp_info['capabilities'][:3]:  # Show first 3
            print(f"    • {capability}")
        if len(mcp_info['capabilities']) > 3:
            print(f"    • ... and {len(mcp_info['capabilities']) - 3} more")
        
        print("\n" + "="*60)
    
    async def run_interactive_mode(self):
        """Run in interactive mode for testing"""
        
        print("🎮 Entering interactive mode...")
        print("Type 'help' for available commands, 'quit' to exit")
        
        self.running = True
        
        while self.running:
            try:
                user_input = input("\nNetworkRAG> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                elif user_input.lower() == 'help':
                    await self._show_help()
                
                elif user_input.lower() == 'health':
                    await self._show_health()
                
                elif user_input.lower() == 'status':
                    await self._show_status()
                
                elif user_input.startswith('query '):
                    query = user_input[6:]  # Remove 'query ' prefix
                    await self._handle_interactive_query(query)
                
                elif user_input.startswith('search '):
                    query = user_input[7:]  # Remove 'search ' prefix  
                    await self._handle_interactive_search(query)
                
                else:
                    print("Unknown command. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit gracefully.")
                continue
            
            except Exception as e:
                print(f"Error: {e}")
                continue
    
    async def _show_help(self):
        """Show help information"""
        
        print("\n📚 Available Commands:")
        print("  help              - Show this help message")
        print("  health            - Show system health status")
        print("  status            - Show system status and information")
        print("  query <text>      - Query network resources")
        print("  search <text>     - Search knowledge base")
        print("  quit/exit/q       - Exit the application")
        print("\n💡 Examples:")
        print("  query show me OLTs in HOBO production")
        print("  search FTTH configuration guide")
        print("  health")
    
    async def _show_health(self):
        """Show system health"""
        
        print("\n🏥 System Health Check:")
        health = await health_check()
        
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️", 
            "unhealthy": "❌",
            "not_initialized": "🔄"
        }
        
        overall_status = health.get("overall_status", "unknown")
        print(f"Overall Status: {status_emoji.get(overall_status, '❓')} {overall_status.upper()}")
        
        services = health.get("services", {})
        if services:
            print("\nService Status:")
            for service_name, service_health in services.items():
                status = service_health.get("status", "unknown")
                message = service_health.get("message", "")
                emoji = status_emoji.get(status, "❓")
                print(f"  {emoji} {service_name}: {status} - {message}")
    
    async def _show_status(self):
        """Show detailed system status"""
        
        print("\n📊 System Status:")
        
        # Container info
        if self.container:
            service_info = await self.container.get_service_info()
            print(f"Services Created: {service_info['services_created']}")
            print(f"Available Services: {len(service_info['available_services'])}")
        
        # MCP server info
        if self.mcp_server:
            mcp_info = self.mcp_server.get_server_info()
            print(f"MCP Tools Available: {mcp_info['tools_available']}")
            print(f"Active Conversations: {mcp_info['active_conversations']}")
        
        # Configuration summary
        print(f"Environment: {self.config.environment}")
        print(f"Debug Mode: {self.config.debug}")
    
    async def _handle_interactive_query(self, query: str):
        """Handle interactive network query"""
        
        print(f"\n🔍 Querying network resources: '{query}'")
        
        try:
            # Simulate MCP tool call
            mcp_request = {
                "jsonrpc": "2.0",
                "id": "interactive",
                "method": "tools/call",
                "params": {
                    "name": "query_network_resources",
                    "arguments": {
                        "query": query,
                        "include_recommendations": True,
                        "session_id": "interactive_session"
                    }
                }
            }
            
            response = await self.mcp_server.handle_mcp_request(mcp_request)
            
            if "result" in response:
                content = response["result"]["content"][0]["text"]
                print("\n📋 Results:")
                print(content)
            else:
                error = response.get("error", {})
                print(f"❌ Error: {error.get('message', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ Query failed: {e}")
    
    async def _handle_interactive_search(self, query: str):
        """Handle interactive knowledge base search"""
        
        print(f"\n📚 Searching knowledge base: '{query}'")
        
        try:
            # Simulate MCP tool call
            mcp_request = {
                "jsonrpc": "2.0",
                "id": "interactive",
                "method": "tools/call",
                "params": {
                    "name": "search_knowledge_base",
                    "arguments": {
                        "query": query,
                        "limit": 5
                    }
                }
            }
            
            response = await self.mcp_server.handle_mcp_request(mcp_request)
            
            if "result" in response:
                content = response["result"]["content"][0]["text"]
                print("\n📄 Search Results:")
                print(content)
            else:
                error = response.get("error", {})
                print(f"❌ Error: {error.get('message', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ Search failed: {e}")
    
    async def run_mcp_server(self):
        """Run as MCP server (for LLM integration)"""
        
        print("🔗 Running as MCP server for LLM integration...")
        print("Listening for MCP protocol messages on stdin/stdout")
        
        self.running = True
        
        while self.running:
            try:
                # Read MCP message from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON-RPC message
                try:
                    request = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # Handle MCP request
                response = await self.mcp_server.handle_mcp_request(request)
                
                # Send response to stdout
                print(json.dumps(response), flush=True)
            
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
    
    async def run_rest_api(self):
        """Run REST API server (if enabled)"""
        
        if not self.config.mcp.enable_rest_api:
            print("❌ REST API is disabled in configuration")
            return
        
        try:
            import uvicorn
            from fastapi import FastAPI, HTTPException
            from fastapi.responses import JSONResponse
            
            app = FastAPI(
                title="Network RAG API",
                description="Network Infrastructure RAG System REST API",
                version=self.config.mcp.server_version
            )
            
            @app.get("/health")
            async def health_endpoint():
                health = await health_check()
                return JSONResponse(health)
            
            @app.post("/query")
            async def query_endpoint(request_data: dict):
                try:
                    mcp_request = {
                        "jsonrpc": "2.0",
                        "id": "rest_api",
                        "method": "tools/call",
                        "params": {
                            "name": "query_network_resources",
                            "arguments": request_data
                        }
                    }
                    
                    response = await self.mcp_server.handle_mcp_request(mcp_request)
                    return response
                    
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))
            
            @app.get("/tools")
            async def tools_endpoint():
                mcp_request = {
                    "jsonrpc": "2.0",
                    "id": "rest_api",
                    "method": "tools/list"
                }
                
                response = await self.mcp_server.handle_mcp_request(mcp_request)
                return response
            
            print(f"🌐 Starting REST API server on {self.config.mcp.host}:{self.config.mcp.port}")
            
            config = uvicorn.Config(
                app,
                host=self.config.mcp.host,
                port=self.config.mcp.port,
                log_level="info" if self.config.debug else "warning"
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except ImportError:
            print("❌ FastAPI and uvicorn required for REST API. Install with:")
            print("   pip install fastapi uvicorn")
        except Exception as e:
            print(f"❌ Failed to start REST API server: {e}")
    
    async def _cleanup(self):
        """Cleanup resources"""
        
        print("🧹 Cleaning up resources...")
        
        try:
            await shutdown_system()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")
    
    async def shutdown(self):
        """Shutdown the application"""
        
        print("🛑 Shutting down Network RAG System...")
        self.running = False
        await self._cleanup()
        print("👋 Goodbye!")


async def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Network RAG System")
    parser.add_argument(
        "--config", 
        "-c", 
        help="Configuration file path"
    )
    parser.add_argument(
        "--mode", 
        "-m", 
        choices=["interactive", "mcp", "api"],
        default="interactive",
        help="Run mode: interactive (default), mcp (MCP server), or api (REST API)"
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check and exit"
    )
    
    args = parser.parse_args()
    
    app = NetworkRAGApplication(config_file=args.config)
    
    try:
        # Initialize application
        await app.initialize()
        
        # Health check mode
        if args.health_check:
            health = await health_check()
            print(json.dumps(health, indent=2))
            
            # Exit with appropriate code
            if health["overall_status"] == "healthy":
                sys.exit(0)
            else:
                sys.exit(1)
        
        # Run in selected mode
        if args.mode == "interactive":
            await app.run_interactive_mode()
        
        elif args.mode == "mcp":
            await app.run_mcp_server()
        
        elif args.mode == "api":
            await app.run_rest_api()
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    except NetworkRAGException as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())