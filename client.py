import os
import asyncio
from datetime import datetime
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import google.generativeai as genai

class GeminiMCPClient:
    def __init__(self, api_key: str):
        """Initialize the Gemini MCP Client
        
        Args:
            api_key: Your Gemini API key
        """
        genai.configure(api_key=api_key)
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.conversation_history = []  # Store conversation history
        
    async def connect_to_server(self, server_command: str, server_args: list = None, env_vars: dict = None):
        """Connect to an MCP server
        
        Args:
            server_command: Command to run the server (e.g., "python", "node", "npx")
            server_args: Arguments for the server command
            env_vars: Environment variables for the server
        """
        if server_args is None:
            server_args = []
            
        # Create server parameters for stdio connection
        server_params = StdioServerParameters(
            command=server_command,
            args=server_args,
            env=env_vars
        )
        
        try:
            # Connect to the server
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            
            # Create session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # Initialize the connection
            await self.session.initialize()
            
            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            print(f"Connected to server with {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
                
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            raise
            
    async def process_query(self, query: str, model: str = "gemini-2.0-flash", temperature: float = 0) -> str:
        """Process a query using Gemini with MCP tools
        
        Args:
            query: The user's query
            model: Gemini model to use
            temperature: Temperature for generation (0 for deterministic)
            
        Returns:
            The model's response
        """
        if not self.session:
            raise ValueError("No active MCP session. Call connect_to_server() first.")
            
        try:
            # Get available tools from MCP session
            tools_response = await self.session.list_tools()
            mcp_tools = tools_response.tools
            
            # Convert MCP tools to Gemini function declarations
            function_declarations = []
            for tool in mcp_tools:
                # Define parameters based on tool name
                if tool.name == "login":
                    parameters = {
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "Username for login"
                            },
                            "password": {
                                "type": "string",
                                "description": "Password for login"
                            }
                        },
                        "required": ["username", "password"]
                    }
                elif tool.name == "get_products":
                    parameters = {
                        "type": "object",
                        "properties": {
                            "page": {
                                "type": "integer",
                                "description": "Page number for pagination"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of items per page"
                            }
                        },
                        "required": []
                    }
                else:
                    # For tools without parameters
                    parameters = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                
                function_declarations.append(
                    genai.types.FunctionDeclaration(
                        name=tool.name,
                        description=tool.description,
                        parameters=parameters
                    )
                )
            
            # Create tool with function declarations
            tool = genai.types.Tool(
                function_declarations=function_declarations
            )
            
            # Create GenerativeModel instance
            gemini_model = genai.GenerativeModel(model)
            
            # Add conversation history to the prompt
            history_prompt = ""
            if self.conversation_history:
                history_prompt = "Previous conversation:\n" + "\n".join(self.conversation_history) + "\n\nCurrent query: "
            
            # Generate content with tools
            response = await gemini_model.generate_content_async(
                history_prompt + query,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                ),
                tools=[tool],
            )
            
            # Handle tool calls if any
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        # Execute the tool call
                        tool_name = part.function_call.name
                        tool_args = part.function_call.args
                        
                        # Find the matching MCP tool
                        for mcp_tool in mcp_tools:
                            if mcp_tool.name == tool_name:
                                # Execute the tool
                                result = await self.session.call_tool(
                                    tool_name,
                                    tool_args
                                )
                                # Add to conversation history
                                self.conversation_history.append(f"User: {query}")
                                self.conversation_history.append(f"Assistant: Executed {tool_name} with args {tool_args}")
                                self.conversation_history.append(f"Result: {result}")
                                return str(result)
            
            # Add to conversation history
            self.conversation_history.append(f"User: {query}")
            self.conversation_history.append(f"Assistant: {response.text}")
            
            return response.text
            
        except Exception as e:
            print(f"Error processing query: {e}")
            raise
            
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nGemini MCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() in ['quit', 'exit']:
                    break
                    
                if not query:
                    continue
                    
                print("\nThinking...")
                response = await self.process_query(query)
                print(f"\nResponse: {response}")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

# Helper functions for different server types
def create_weather_server_params():
    """Create parameters for a weather MCP server"""
    return {
        'server_command': 'npx',
        'server_args': ['-y', '@philschmid/weather-mcp']
    }

def create_python_server_params(script_path: str, env_vars: dict = None):
    """Create parameters for a Python MCP server"""
    return {
        'server_command': 'python',
        'server_args': [script_path],
        'env_vars': env_vars
    }

def create_node_server_params(script_path: str, env_vars: dict = None):
    """Create parameters for a Node.js MCP server"""
    return {
        'server_command': 'node',
        'server_args': [script_path],
        'env_vars': env_vars
    }

# Example usage functions
async def weather_example():
    """Example using a weather MCP server"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    client = GeminiMCPClient(api_key)
    
    try:
        # Connect to weather server
        await client.connect_to_server(**create_weather_server_params())
        
        # Ask about weather
        current_date = datetime.now().strftime('%Y-%m-%d')
        query = f"What is the weather in London on {current_date}?"
        
        response = await client.process_query(query)
        print(f"Weather Response: {response}")
        
    finally:
        await client.cleanup()

async def interactive_session():
    """Start an interactive session with MCP server"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return
    
    print("Choose your MCP server:")
    print("1. Weather server (NPX)")
    print("2. Custom Python server")
    print("3. Custom Node.js server")
    
    choice = input("Enter choice (1-3): ").strip()
    
    client = GeminiMCPClient(api_key)
    
    try:
        if choice == "1":
            await client.connect_to_server(**create_weather_server_params())
        elif choice == "2":
            script_path = input("Enter path to Python server script: ").strip()
            await client.connect_to_server(**create_python_server_params(script_path))
        elif choice == "3":
            script_path = input("Enter path to Node.js server script: ").strip()
            await client.connect_to_server(**create_node_server_params(script_path))
        else:
            print("Invalid choice")
            return
            
        await client.chat_loop()
        
    finally:
        await client.cleanup()

# Main execution
async def main():
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode - connect to specific server
        server_type = sys.argv[1].lower()
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set")
            return
            
        client = GeminiMCPClient(api_key)
        
        try:
            if server_type == "weather":
                await client.connect_to_server(**create_weather_server_params())
            elif server_type.endswith('.py'):
                await client.connect_to_server(**create_python_server_params(server_type))
            elif server_type.endswith('.js'):
                await client.connect_to_server(**create_node_server_params(server_type))
            else:
                print("Unsupported server type. Use 'weather', or provide .py/.js file path")
                return
                
            await client.chat_loop()
            
        finally:
            await client.cleanup()
    else:
        # Interactive mode
        await interactive_session()

if __name__ == "__main__":
    asyncio.run(main())