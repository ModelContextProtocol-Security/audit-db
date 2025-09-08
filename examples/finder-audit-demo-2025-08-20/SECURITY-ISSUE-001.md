# Security Issue #001: Information Disclosure via Server Info Resource

## Issue Metadata
- **Issue ID:** SECURITY-001
- **Category:** Information Disclosure
- **Severity:** Low
- **CWE:** CWE-200 (Exposure of Sensitive Information)
- **CVSS Score:** 2.4/10.0 (Low)
- **AIVSS Score:** 2.8/10.0 (Low)
- **Status:** Open
- **Found Date:** 2025-08-20

## Issue Description
The server exposes internal configuration details through the `server://info` resource endpoint, which could provide reconnaissance information to potential attackers about the backend SearXNG instance and server configuration.

## Affected Code Location
**File:** `src/searxng_simple_mcp/server.py`
**Lines:** 108-122

```python
@mcp.resource("server://info")
def get_server_info() -> str:
    """Get information about the SearxNG server configuration."""
    return f"""
SearxNG MCP Server Information:
------------------------------
SearxNG Instance: {settings.searxng_url}        # ⚠️ EXPOSES BACKEND URL
Timeout: {settings.timeout} seconds             # ⚠️ EXPOSES TIMEOUT CONFIG
Default Result Count: {settings.default_result_count}
Default Language: {settings.default_language}
Default Format: {settings.default_format}
Log Level: {settings.log_level}                 # ⚠️ EXPOSES LOG LEVEL
    """
```

## Vulnerability Analysis

### Attack Vector
An MCP client can request the `server://info` resource to gather intelligence about:
- Backend SearXNG instance URL (`https://paulgo.io/`)
- Request timeout configurations
- Logging verbosity levels
- Default operational parameters

### Potential Impact
- **Reconnaissance:** Attackers learn backend infrastructure details
- **Target Identification:** Exposes third-party service dependencies
- **Configuration Inference:** Reveals operational security posture

## Risk Assessment by Usage Context

### Local Single-User MCP (Risk: Very Low - 1.5/10)
**Scenario:** User running MCP server locally for personal use
- ✅ **Acceptable:** User already has access to configuration files
- ✅ **Low Impact:** No additional risk beyond existing local access
- **Recommendation:** No action required

### Remote SSE-Enabled Multi-User (Risk: Medium - 5.2/10)
**Scenario:** MCP server running remotely with SSE transport serving multiple users
- ⚠️ **Concern:** Backend URL disclosure could enable direct attacks
- ⚠️ **Risk:** Multiple users can gather reconnaissance data
- **Recommendation:** Implement access controls or sanitize output

### Enterprise/Production Deployment (Risk: Medium-High - 6.8/10)
**Scenario:** Production deployment in corporate environment
- 🚨 **High Concern:** Violates information disclosure security policies
- 🚨 **Compliance Risk:** May conflict with security audit requirements
- **Recommendation:** Remove or restrict sensitive information exposure

## CVSS 4.0 Scoring Breakdown

**Base Score Metrics:**
- **Attack Vector (AV):** Network (0.85) - Accessible via MCP protocol
- **Attack Complexity (AC):** Low (0.77) - Simple resource request
- **Privileges Required (PR):** Low (0.62) - Requires MCP client access
- **User Interaction (UI):** None (0.85) - Automated access possible
- **Scope (S):** Unchanged (0.0) - Limited to configuration disclosure
- **Confidentiality Impact (C):** Low (0.22) - Configuration data leaked
- **Integrity Impact (I):** None (0.0) - No data modification
- **Availability Impact (A):** None (0.0) - No service disruption

**CVSS Base Score:** 2.4/10.0 (Low)

## AIVSS Factors (AI Considerations)

**AI-Specific Risk Factors:**
- **Agent Reconnaissance (AR):** Medium (+0.3) - AI agents could systematically gather intel
- **Backend Discovery (BD):** Low (+0.1) - Exposes backend service URLs
- **Configuration Intelligence (CI):** Low (+0.0) - Standard configuration exposure

**AIVSS Adjustment:** +0.4
**Final AIVSS Score:** 2.8/10.0 (Low)

## Code Examples

### Current Vulnerable Implementation
```python
@mcp.resource("server://info")
def get_server_info() -> str:
    """Get information about the SearXNG server configuration."""
    return f"""
SearxNG MCP Server Information:
------------------------------
SearxNG Instance: {settings.searxng_url}        # EXPOSED!
Timeout: {settings.timeout} seconds
Default Result Count: {settings.default_result_count}
Default Language: {settings.default_language}
Default Format: {settings.default_format}
Log Level: {settings.log_level}                 # EXPOSED!
    """
```

### Recommended Secure Implementation
```python
@mcp.resource("server://info")
def get_server_info() -> str:
    """Get information about the SearxNG server configuration."""
    return f"""
SearxNG MCP Server Information:
------------------------------
Server Status: Online
Default Result Count: {settings.default_result_count}
Default Language: {settings.default_language}
Default Format: {settings.default_format}
Server Version: {__version__}
    """
```

### Alternative: Conditional Information Disclosure
```python
@mcp.resource("server://info")
def get_server_info() -> str:
    """Get information about the SearXNG server configuration."""
    # Only show sensitive info in debug mode
    if settings.log_level.upper() == "DEBUG":
        return f"""
SearxNG MCP Server Information (DEBUG MODE):
------------------------------
SearxNG Instance: {settings.searxng_url}
Timeout: {settings.timeout} seconds
Default Result Count: {settings.default_result_count}
Default Language: {settings.default_language}
Default Format: {settings.default_format}
Log Level: {settings.log_level}
        """
    else:
        return f"""
SearxNG MCP Server Information:
------------------------------
Server Status: Online
Default Result Count: {settings.default_result_count}
Default Language: {settings.default_language}
Default Format: {settings.default_format}
        """
```

## Remediation Recommendations

### Immediate (Low Priority)
1. **Sanitize Information Exposure:**
   - Remove `searxng_url` from info output
   - Remove `log_level` from info output
   - Keep only non-sensitive configuration

### Short-term (Medium Priority)
1. **Implement Conditional Disclosure:**
   - Show detailed info only in debug mode
   - Add environment variable to control info verbosity
   
2. **Add Warning Documentation:**
   - Document information disclosure in security notes
   - Provide guidance on production deployment

### Long-term (Low Priority)
1. **Access Control Integration:**
   - Implement role-based access to server info
   - Add authentication checks for sensitive resources

## Testing Verification

### Test Case 1: Verify Information Sanitization
```python
def test_server_info_no_sensitive_data():
    info = get_server_info()
    assert "searxng_url" not in info.lower()
    assert "paulgo.io" not in info
    assert "log_level" not in info.lower()
```

### Test Case 2: Verify Conditional Disclosure
```python
def test_debug_mode_shows_details():
    # Set debug mode
    settings.log_level = "DEBUG"
    info = get_server_info()
    assert "searxng_url" in info.lower()
    
    # Set production mode
    settings.log_level = "ERROR"  
    info = get_server_info()
    assert "searxng_url" not in info.lower()
```

## Detection and Monitoring

### Log Pattern to Monitor
```
MCP Resource Request: server://info from client: <client_id>
```

### Automated Detection
```bash
# Check for sensitive information in resource output
grep -r "searxng_url\|log_level" src/ --include="*.py" | grep -v "config.py"
```

## References
- **CWE-200:** Information Exposure - https://cwe.mitre.org/data/definitions/200.html
- **OWASP Information Disclosure:** https://owasp.org/www-community/vulnerabilities/Information_Disclosure
- **MCP Resource Security:** https://github.com/modelcontextprotocol/servers#security