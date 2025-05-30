from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import os
from contextlib import asynccontextmanager
import sys

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your existing GeminiMCPClient
from client import GeminiMCPClient

app = FastAPI(title="Gemini MCP Client API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global client instance
client_instance: Optional[GeminiMCPClient] = None

# Pydantic models for request/response
class ServerConfig(BaseModel):
    api_key: str
    server_command: str
    server_args: List[str]
    env_vars: Optional[Dict[str, str]] = None

class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = "gemini-2.0-flash"
    temperature: Optional[float] = 0

class QueryResponse(BaseModel):
    response: str
    success: bool
    error: Optional[str] = None

class ConnectionResponse(BaseModel):
    success: bool
    message: str
    tools: Optional[List[Dict[str, str]]] = None

class Tool(BaseModel):
    name: str
    description: str

@app.get("/")
async def root():
    return {"message": "Gemini MCP Client API is running"}

@app.post("/api/connect", response_model=ConnectionResponse)
async def connect_to_server(config: ServerConfig):
    """Connect to an MCP server"""
    global client_instance
    
    try:
        # Initialize client
        client_instance = GeminiMCPClient(config.api_key)
        
        # Connect to server
        await client_instance.connect_to_server(
            server_command=config.server_command,
            server_args=config.server_args,
            env_vars=config.env_vars
        )
        
        # Get available tools
        if client_instance.session:
            tools_response = await client_instance.session.list_tools()
            tools = [
                {"name": tool.name, "description": tool.description} 
                for tool in tools_response.tools
            ]
        else:
            tools = []
        
        return ConnectionResponse(
            success=True,
            message="Successfully connected to MCP server",
            tools=tools
        )
        
    except Exception as e:
        # Clean up on failure
        if client_instance:
            await client_instance.cleanup()
            client_instance = None
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to MCP server: {str(e)}"
        )

@app.post("/api/disconnect")
async def disconnect_from_server():
    """Disconnect from the current MCP server"""
    global client_instance
    
    if client_instance:
        try:
            await client_instance.cleanup()
        except Exception as e:
            print(f"Error during cleanup: {e}")
        finally:
            client_instance = None
    
    return {"success": True, "message": "Disconnected from server"}

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a query using the connected MCP client"""
    global client_instance
    
    if not client_instance:
        raise HTTPException(
            status_code=400,
            detail="No active MCP connection. Please connect to a server first."
        )
    
    try:
        response = await client_instance.process_query(
            query=request.query,
            model=request.model,
            temperature=request.temperature
        )
        
        return QueryResponse(
            response=response,
            success=True
        )
        
    except Exception as e:
        return QueryResponse(
            response="",
            success=False,
            error=str(e)
        )

@app.get("/api/status")
async def get_status():
    """Get the current connection status"""
    global client_instance
    
    is_connected = client_instance is not None and client_instance.session is not None
    
    tools = []
    if is_connected:
        try:
            tools_response = await client_instance.session.list_tools()
            tools = [
                {"name": tool.name, "description": tool.description} 
                for tool in tools_response.tools
            ]
        except Exception:
            tools = []
    
    return {
        "connected": is_connected,
        "tools": tools,
        "conversation_history_length": len(client_instance.conversation_history) if client_instance else 0
    }

@app.get("/api/tools")
async def get_available_tools():
    """Get list of available tools from the connected server"""
    global client_instance
    
    if not client_instance or not client_instance.session:
        raise HTTPException(
            status_code=400,
            detail="No active MCP connection"
        )
    
    try:
        tools_response = await client_instance.session.list_tools()
        tools = [
            {"name": tool.name, "description": tool.description} 
            for tool in tools_response.tools
        ]
        return {"tools": tools}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools: {str(e)}"
        )

@app.delete("/api/conversation")
async def clear_conversation():
    """Clear the conversation history"""
    global client_instance
    
    if client_instance:
        client_instance.conversation_history = []
        return {"success": True, "message": "Conversation history cleared"}
    
    return {"success": False, "message": "No active client"}

@app.get("/api/conversation")
async def get_conversation():
    """Get the current conversation history"""
    global client_instance
    
    if client_instance:
        return {
            "conversation": client_instance.conversation_history,
            "length": len(client_instance.conversation_history)
        }
    
    return {"conversation": [], "length": 0}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Gemini MCP Client API"}

# Cleanup on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    global client_instance
    if client_instance:
        await client_instance.cleanup()

app.router.lifespan_context = lifespan

# Mount static files for frontend (optional)
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )