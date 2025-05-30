# Project Documentation

## Overview
This project implements a client-server architecture using MCP (Model Control Protocol) for a Student Management System. The system consists of two main components: a server implementation (`main.py`) and a client implementation (`client.py`).

## Components

### 1. Server (mcp-project/main.py)
The server component implements a FastMCP-based API with the following features:

#### Authentication System
- **Login Function**: `login(username: str, password: str)`
  - Handles user authentication
  - Returns JWT token upon successful login
  - Stores authentication token globally

#### Product Management
- **Get Products**: `get_products(skip: int = 0, limit: int = 100)`
  - Retrieves products with pagination support
  - Requires authentication
  - Returns product data in JSON format

#### Session Management
- **Logout**: `logout()`
  - Clears authentication token
  - Ends user session
- **Auth Status**: `get_auth_status()`
  - Checks current authentication status
  - Returns token preview if authenticated

### 2. Client (client.py)
The client component implements a Gemini AI-powered MCP client with the following features:

#### Core Functionality
- **GeminiMCPClient Class**
  - Manages connection to MCP server
  - Handles tool execution
  - Maintains conversation history
  - Integrates with Google's Gemini AI

#### Key Methods
1. **Connection Management**
   - `connect_to_server(server_command, server_args, env_vars)`
   - Establishes connection with MCP server
   - Lists available tools

2. **Query Processing**
   - `process_query(query, model, temperature)`
   - Processes user queries using Gemini AI
   - Handles tool calls and responses
   - Maintains conversation context

3. **Interactive Features**
   - `chat_loop()`
   - Provides interactive command-line interface
   - Handles user input and responses

#### Helper Functions
- Server parameter creation for different environments:
  - `create_weather_server_params()`
  - `create_python_server_params(script_path, env_vars)`
  - `create_node_server_params(script_path, env_vars)`

## Technical Details

### Dependencies
- FastMCP
- httpx
- google.generativeai
- asyncio
- typing
- contextlib

### API Endpoints
- Base URL: `http://127.0.0.1:8000`
- Authentication: `/auth/login`
- Products: `/api/v1/products/`

### Security Features
- JWT-based authentication
- Secure token storage
- Token expiration handling
- Environment variable configuration

## Usage

### Server Setup
1. Run the server:
```python
python mcp-project/main.py
```

### Client Setup
1. Set up environment variables:
```bash
export GEMINI_API_KEY="your_api_key"
```

2. Initialize and run the client:
```python
client = GeminiMCPClient(api_key)
await client.connect_to_server("python", ["mcp-project/main.py"])
await client.chat_loop()
```

## Error Handling
- Connection errors
- Authentication failures
- API response errors
- Tool execution errors

## Best Practices
1. Always authenticate before accessing protected endpoints
2. Handle token expiration gracefully
3. Use appropriate error handling
4. Maintain conversation history for context
5. Clean up resources properly using AsyncExitStack 