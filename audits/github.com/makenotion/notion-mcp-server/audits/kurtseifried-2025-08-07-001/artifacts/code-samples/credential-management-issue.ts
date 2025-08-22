// HIGH-001: Credential Management - Environment Variable Usage
// File: src/openapi-mcp-server/mcp/proxy.ts (lines 88-106)

private parseHeadersFromEnv(): Record<string, string> {
  // First try OPENAPI_MCP_HEADERS (existing behavior)
  const headersJson = process.env.OPENAPI_MCP_HEADERS
  if (headersJson) {
    try {
      const headers = JSON.parse(headersJson)
      if (typeof headers !== 'object' || headers === null) {
        console.warn('OPENAPI_MCP_HEADERS environment variable must be a JSON object, got:', typeof headers)
      } else if (Object.keys(headers).length > 0) {
        // Only use OPENAPI_MCP_HEADERS if it contains actual headers
        return headers
      }
      // If OPENAPI_MCP_HEADERS is empty object, fall through to try NOTION_TOKEN
    } catch (error) {
      console.warn('Failed to parse OPENAPI_MCP_HEADERS environment variable:', error)
      // Fall through to try NOTION_TOKEN
    }
  }

  // Alternative: try NOTION_TOKEN
  const notionToken = process.env.NOTION_TOKEN  // ← SECURITY ISSUE: Credential in env var
  if (notionToken) {
    return {
      'Authorization': `Bearer ${notionToken}`,
      'Notion-Version': '2022-06-28'
    }
  }

  return {}
}

// SECURITY CONCERN: Credentials stored in environment variables are:
// 1. Visible in process listings (ps aux | grep notion)
// 2. Accessible via /proc/PID/environ
// 3. Logged in process dumps and core files
// 4. Visible to other processes in some containerized environments
// 5. Potentially leaked in error messages or logs