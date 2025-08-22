// HIGH-002: Network Exposure - Binding to All Interfaces
// File: scripts/start-server.ts (lines 147-151)

// SECURITY ISSUE: Server binds to all interfaces by default
app.listen(port, '0.0.0.0', () => {  // ← Binds to ALL interfaces
  console.log(`MCP Server listening on port ${port}`)
  console.log(`Endpoint: http://0.0.0.0:${port}/mcp`)
  console.log(`Health check: http://0.0.0.0:${port}/health`)
  console.log(`Authentication: Bearer token required`)
})

// SECURITY CONCERNS:
// 1. Service accessible from all network interfaces
// 2. In cloud deployments, may be accessible from internet
// 3. Corporate networks may allow unintended internal access
// 4. Container deployments may expose service beyond intended scope
// 5. Increases attack surface unnecessarily

// RECOMMENDED SECURE ALTERNATIVES:

// Option 1: Bind to localhost only
app.listen(port, '127.0.0.1', () => {
  console.log(`MCP Server listening on localhost:${port}`)
})

// Option 2: Bind to specific interface
app.listen(port, '10.0.1.100', () => {
  console.log(`MCP Server listening on 10.0.1.100:${port}`)
})

// Option 3: Make binding configurable
const bindAddress = process.env.BIND_ADDRESS || '127.0.0.1'
app.listen(port, bindAddress, () => {
  console.log(`MCP Server listening on ${bindAddress}:${port}`)
})

// Option 4: Add configuration parameter
function parseArgs() {
  // ... existing arg parsing ...
  let bindAddress = '127.0.0.1' // Default to localhost
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--bind-address' && i + 1 < args.length) {
      bindAddress = args[i + 1]
      i++
    }
  }
  
  return { transport, port, authToken, bindAddress }
}