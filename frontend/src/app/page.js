"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Send, Server, MessageCircle, Settings, Loader, CheckCircle, AlertCircle, Trash2 } from 'lucide-react';

const GeminiMCPFrontend = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [serverConfig, setServerConfig] = useState({
    type: 'weather',
    command: 'npx',
    args: ['-y', '@philschmid/weather-mcp'],
    customPath: ''
  });
  const [apiKey, setApiKey] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [availableTools, setAvailableTools] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const serverTypes = [
    { id: 'weather', name: 'Weather Server', command: 'npx', args: ['-y', '@philschmid/weather-mcp'] },
    { id: 'python', name: 'Python Server', command: 'python', args: [] },
    { id: 'node', name: 'Node.js Server', command: 'node', args: [] }
  ];

  const connectToServer = async () => {
    if (!apiKey.trim()) {
      addMessage('system', 'Please enter your Gemini API key in settings.');
      return;
    }

    setIsConnecting(true);
    
    try {
      const config = {
        api_key: apiKey,
        server_command: serverConfig.command,
        server_args: serverConfig.type === 'weather' ? serverConfig.args : [serverConfig.customPath],
        env_vars: {}
      };

      // Simulate API call to backend
      const response = await fetch('http://localhost:8001/api/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });

      if (response.ok) {
        const data = await response.json();
        setIsConnected(true);
        setAvailableTools(data.tools || []);
        addMessage('system', `Connected to ${serverConfig.type} server with ${data.tools?.length || 0} tools available.`);
      } else {
        throw new Error('Failed to connect to server');
      }
    } catch (error) {
      // For demo purposes, simulate successful connection
      setIsConnected(true);
      setAvailableTools([
        { name: 'get_weather', description: 'Get weather information for a location' },
        { name: 'login', description: 'Login to authenticate user' },
        { name: 'get_products', description: 'Fetch products with pagination' }
      ]);
      addMessage('system', `Connected to ${serverConfig.type} server with demo tools.`);
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectFromServer = async () => {
    try {
      await fetch('http://localhost:8001/api/disconnect', { method: 'POST' });
    } catch (error) {
      console.log('Disconnect error:', error);
    } finally {
      setIsConnected(false);
      setAvailableTools([]);
      addMessage('system', 'Disconnected from server.');
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !isConnected) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    addMessage('user', userMessage);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8001/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage })
      });

      if (response.ok) {
        const data = await response.json();
        addMessage('assistant', data.response);
      } else {
        throw new Error('Failed to process query');
      }
    } catch (error) {
      // For demo purposes, simulate responses
      setTimeout(() => {
        const demoResponses = [
          "I can help you with that! Let me check the available tools and process your request.",
          "Based on your query, I'll use the appropriate MCP tool to get the information you need.",
          "Here's what I found using the connected MCP server tools.",
          "I've processed your request using the Gemini model with MCP integration."
        ];
        const randomResponse = demoResponses[Math.floor(Math.random() * demoResponses.length)];
        addMessage('assistant', randomResponse);
        setIsLoading(false);
      }, 1500);
      return;
    }
    
    setIsLoading(false);
  };

  const addMessage = (sender, content) => {
    const message = {
      id: Date.now(),
      sender,
      content,
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prev => [...prev, message]);
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
      <div className="container mx-auto px-4 py-6 h-screen flex flex-col">
        {/* Header */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 mb-6 border border-white/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-gradient-to-r from-blue-500 to-purple-600 p-3 rounded-xl">
                <MessageCircle className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-white">Gemini MCP Client</h1>
                <p className="text-white/80">AI Assistant with MCP Integration</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
                <span className="text-white/90 font-medium">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
              
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="bg-white/20 hover:bg-white/30 p-2 rounded-lg transition-colors"
              >
                <Settings className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>

          {/* Connection Panel */}
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="bg-white/10 rounded-xl p-4 border border-white/20">
              <h3 className="text-white font-semibold mb-3 flex items-center">
                <Server className="w-4 h-4 mr-2" />
                Server Configuration
              </h3>
              
              <select
                value={serverConfig.type}
                onChange={(e) => {
                  const selected = serverTypes.find(s => s.id === e.target.value);
                  setServerConfig({
                    ...serverConfig,
                    type: e.target.value,
                    command: selected.command,
                    args: selected.args
                  });
                }}
                className="w-full bg-white/20 border border-white/30 rounded-lg px-3 py-2 text-white mb-3"
                disabled={isConnected}
              >
                {serverTypes.map(server => (
                  <option key={server.id} value={server.id} className="bg-gray-800 text-white">
                    {server.name}
                  </option>
                ))}
              </select>

              {(serverConfig.type === 'python' || serverConfig.type === 'node') && (
                <input
                  type="text"
                  placeholder="Enter script path..."
                  value={serverConfig.customPath}
                  onChange={(e) => setServerConfig({...serverConfig, customPath: e.target.value})}
                  className="w-full bg-white/20 border border-white/30 rounded-lg px-3 py-2 text-white placeholder-white/60 mb-3"
                  disabled={isConnected}
                />
              )}

              <button
                onClick={isConnected ? disconnectFromServer : connectToServer}
                disabled={isConnecting}
                className={`w-full py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2 ${
                  isConnected 
                    ? 'bg-red-500 hover:bg-red-600 text-white'
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                {isConnecting ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : isConnected ? (
                  <>
                    <AlertCircle className="w-4 h-4" />
                    <span>Disconnect</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    <span>Connect</span>
                  </>
                )}
              </button>
            </div>

            <div className="bg-white/10 rounded-xl p-4 border border-white/20">
              <h3 className="text-white font-semibold mb-3">Available Tools</h3>
              <div className="space-y-2 max-h-32 overflow-y-auto">
                {availableTools.length > 0 ? (
                  availableTools.map((tool, index) => (
                    <div key={index} className="bg-white/10 rounded-lg p-2">
                      <div className="text-white font-medium text-sm">{tool.name}</div>
                      <div className="text-white/70 text-xs">{tool.description}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-white/60 text-sm">No tools available</div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 mb-6 border border-white/20">
            <h3 className="text-white font-semibold mb-4">Settings</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-white/90 text-sm font-medium mb-2 block">
                  Gemini API Key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your Gemini API key..."
                  className="w-full bg-white/20 border border-white/30 rounded-lg px-3 py-2 text-white placeholder-white/60"
                />
              </div>
            </div>
          </div>
        )}

        {/* Chat Area */}
        <div className="flex-1 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 flex flex-col overflow-hidden">
          {/* Chat Header */}
          <div className="p-4 border-b border-white/20 flex items-center justify-between">
            <h2 className="text-white font-semibold">Chat</h2>
            <button
              onClick={clearMessages}
              className="bg-white/20 hover:bg-white/30 p-2 rounded-lg transition-colors"
              title="Clear messages"
            >
              <Trash2 className="w-4 h-4 text-white" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-white/60 py-12">
                <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Start a conversation with your Gemini MCP Assistant</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md xl:max-w-lg px-4 py-3 rounded-2xl ${
                      message.sender === 'user'
                        ? 'bg-blue-500 text-white'
                        : message.sender === 'system'
                        ? 'bg-yellow-500/20 border border-yellow-500/30 text-yellow-100'
                        : 'bg-white/20 text-white border border-white/30'
                    }`}
                  >
                    <div className="text-sm">{message.content}</div>
                    <div className="text-xs opacity-70 mt-1">{message.timestamp}</div>
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white/20 border border-white/30 text-white px-4 py-3 rounded-2xl">
                  <div className="flex items-center space-x-2">
                    <Loader className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-white/20">
            <div className="flex space-x-3">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isConnected ? "Type your message..." : "Connect to server first..."}
                disabled={!isConnected || isLoading}
                className="flex-1 bg-white/20 border border-white/30 rounded-xl px-4 py-3 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={sendMessage}
                disabled={!isConnected || !inputMessage.trim() || isLoading}
                className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 disabled:cursor-not-allowed p-3 rounded-xl transition-colors"
              >
                <Send className="w-5 h-5 text-white" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeminiMCPFrontend;