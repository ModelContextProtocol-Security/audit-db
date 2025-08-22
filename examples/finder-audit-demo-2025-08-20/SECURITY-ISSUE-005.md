# Security Issue #005: Debug Information Exposure in Error Messages

## Issue Metadata
- **Issue ID:** SECURITY-005
- **Category:** Information Disclosure / Error Handling
- **Severity:** Low
- **CWE:** CWE-209 (Information Exposure Through Error Messages)
- **CVSS Score:** 2.1/10.0 (Low)
- **AIVSS Score:** 2.6/10.0 (Low)
- **Status:** Open
- **Found Date:** 2025-08-20

## Issue Description
The application exposes internal implementation details through error messages and debug logging, potentially providing reconnaissance information to attackers. Error handling reveals backend service details, internal URLs, and system configuration information.

## Affected Code Location

**File:** `src/searxng_simple_mcp/searxng_client.py`
**Lines:** 79, 84-87

```python
# Debug information in successful responses
logger.info(f"Response: {response.text[:100]}...")  # ⚠️ LOGS RESPONSE CONTENT

# Detailed exception information
except Exception as e:
    logger.exception("Unexpected error occurred")      # ⚠️ LOGS FULL STACK TRACE
    msg = f"Error during search: {e}"                  # ⚠️ EXPOSES EXCEPTION DETAILS
    raise ValueError(msg) from e                       # ⚠️ CHAINED EXCEPTION
```

**File:** `src/searxng_simple_mcp/server.py`
**Lines:** 99-103

```python
except Exception as e:
    error_msg = f"Unexpected error during search: {e}"  # ⚠️ EXPOSES EXCEPTION DETAILS
    logger.exception(error_msg)                         # ⚠️ FULL STACK TRACE TO LOGS
    if ctx:
        ctx.error(error_msg)                            # ⚠️ SENDS DETAILS TO CLIENT
    return error_msg                                    # ⚠️ RETURNS INTERNAL ERROR INFO
```

## Vulnerability Analysis

### Information Disclosed
1. **Backend Service Details:** SearXNG instance URLs and error responses
2. **Internal Implementation:** Stack traces revealing code structure
3. **System Configuration:** File paths, Python versions, library versions
4. **Network Information:** Connection details, timeout values
5. **Runtime State:** Variable values, function call chains

### Attack Vectors
1. **Reconnaissance:** Gather intelligence about backend systems
2. **Framework Identification:** Identify specific libraries and versions
3. **Path Discovery:** Learn internal file structures and configurations
4. **Error Amplification:** Use errors to map internal application flow

## Risk Assessment by Usage Context

### Local Single-User MCP (Risk: Very Low - 0.8/10)
**Scenario:** User running MCP server locally for personal use
- ✅ **User Environment:** User has local access anyway
- ✅ **Development Context:** Debug information helpful for troubleshooting
- **Recommendation:** Current behavior acceptable for development

### Remote SSE-Enabled Multi-User (Risk: Low-Medium - 4.2/10)
**Scenario:** MCP server running remotely with SSE transport serving multiple users
- ⚠️ **Information Leakage:** Internal details exposed to remote users
- ⚠️ **Reconnaissance Risk:** Multiple users can gather system intelligence
- **Recommendation:** Sanitize error messages for production

### Enterprise/Production Deployment (Risk: Medium - 5.8/10)
**Scenario:** Production deployment in corporate environment
- 🚨 **Security Policy Violation:** Detailed error messages violate security guidelines
- 🚨 **Internal Disclosure:** Corporate infrastructure details exposed
- **Recommendation:** Implement production error handling with generic messages

## CVSS 4.0 Scoring Breakdown

**Base Score Metrics:**
- **Attack Vector (AV):** Network (0.85) - Accessible via MCP protocol
- **Attack Complexity (AC):** Low (0.77) - Trigger errors with invalid input
- **Privileges Required (PR):** Low (0.62) - Requires MCP client access
- **User Interaction (UI):** None (0.85) - Automated error triggering
- **Scope (S):** Unchanged (0.0) - Limited to information disclosure
- **Confidentiality Impact (C):** Low (0.22) - Internal details disclosed
- **Integrity Impact (I):** None (0.0) - No data modification
- **Availability Impact (A):** None (0.0) - No service disruption

**CVSS Base Score:** 2.1/10.0 (Low)

## AIVSS Factors (Agentic AI Considerations)

**AI-Specific Risk Factors:**
- **Systematic Error Probing (SEP):** Low (+0.3) - AI agents could systematically trigger errors
- **Intelligence Gathering (IG):** Low (+0.2) - Automated collection of system intelligence
- **Context Inference (CI):** Very Low (+0.1) - Error details provide system context
- **Attack Surface Mapping (ASM):** Very Low (+0.1) - Helps map internal architecture

**AIVSS Adjustment:** +0.5
**Final AIVSS Score:** 2.6/10.0 (Low)

## Code Examples

### Current Vulnerable Implementation
```python
# Excessive debug logging
logger.info(f"Response: {response.text[:100]}...")  # ⚠️ RESPONSE CONTENT LOGGED

# Detailed error exposure
except Exception as e:
    logger.exception("Unexpected error occurred")    # ⚠️ FULL STACK TRACE
    msg = f"Error during search: {e}"                # ⚠️ EXCEPTION DETAILS
    raise ValueError(msg) from e                     # ⚠️ CHAINED EXCEPTION WITH DETAILS

# Client error exposure
except Exception as e:
    error_msg = f"Unexpected error during search: {e}"  # ⚠️ INTERNAL DETAILS
    if ctx:
        ctx.error(error_msg)                            # ⚠️ SENT TO CLIENT
    return error_msg                                    # ⚠️ RETURNED TO CALLER
```

### Recommended Secure Implementation

#### Option 1: Environment-Based Error Handling
```python
import os
from enum import Enum

class ErrorMode(Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    STAGING = "staging"

class SecureErrorHandler:
    def __init__(self):
        self.mode = ErrorMode(os.getenv("ERROR_MODE", "production"))
    
    def log_response(self, response):
        """Log response with appropriate detail level."""
        if self.mode == ErrorMode.DEVELOPMENT:
            logger.debug(f"Response: {response.text[:100]}...")
        else:
            logger.info(f"Response status: {response.status_code}, length: {len(response.text)}")
    
    def handle_exception(self, e: Exception, ctx=None) -> str:
        """Handle exceptions with appropriate disclosure level."""
        error_id = str(uuid.uuid4())[:8]  # Generate error ID for tracking
        
        if self.mode == ErrorMode.DEVELOPMENT:
            # Full details in development
            logger.exception(f"[{error_id}] Full error details")
            error_msg = f"Error [{error_id}]: {str(e)}"
        else:
            # Generic messages in production
            logger.error(f"[{error_id}] Search operation failed", exc_info=False)
            logger.debug(f"[{error_id}] Error details", exc_info=True)  # Full details to debug log only
            error_msg = f"Search operation failed [Error ID: {error_id}]"
        
        if ctx:
            ctx.error(error_msg)
        
        return error_msg

# Usage in server code
error_handler = SecureErrorHandler()

@mcp.tool()
async def web_search(...):
    try:
        results = await searxng_client.search(...)
        return results
    except Exception as e:
        return error_handler.handle_exception(e, ctx)

# Usage in client code
class SearxNGClient:
    def __init__(self, base_url: AnyHttpUrl, timeout: int):
        self.error_handler = SecureErrorHandler()
    
    async def search(self, query: str, ...):
        try:
            response = await client.get(...)
            response.raise_for_status()
            
            # Secure response logging
            self.error_handler.log_response(response)
            return response.json()
            
        except httpx.HTTPStatusError as e:
            # Specific HTTP error handling
            if e.response.status_code == 404:
                raise ValueError("SearXNG search endpoint not found") from None
            elif e.response.status_code >= 500:
                raise ValueError("SearXNG service temporarily unavailable") from None
            else:
                raise ValueError(f"Search request failed (HTTP {e.response.status_code})") from None
        except httpx.TimeoutException:
            raise ValueError("Search request timed out") from None
        except httpx.NetworkError:
            raise ValueError("Unable to connect to SearXNG service") from None
        except Exception as e:
            return self.error_handler.handle_exception(e)
```

#### Option 2: Structured Error Responses
```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging

@dataclass
class ErrorResponse:
    """Structured error response with controlled information disclosure."""
    message: str
    error_code: str
    error_id: str
    details: Optional[Dict[str, Any]] = None
    
    def to_client_safe(self) -> Dict[str, Any]:
        """Return client-safe version of error."""
        return {
            "error": True,
            "message": self.message,
            "error_code": self.error_code,
            "error_id": self.error_id
            # Note: 'details' excluded from client response
        }

class ProductionSafeLogging:
    """Production-safe logging that separates client and server information."""
    
    @staticmethod
    def log_search_request(query: str, client_id: str = None):
        """Log search request with privacy considerations."""
        # Hash query for privacy while maintaining uniqueness for debugging
        import hashlib
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        logger.info(f"Search request: query_hash={query_hash}, client={client_id}")
    
    @staticmethod
    def log_search_response(status_code: int, result_count: int, response_time: float):
        """Log response metrics without content disclosure."""
        logger.info(f"Search response: status={status_code}, results={result_count}, time={response_time:.2f}s")
    
    @staticmethod
    def log_error(error: Exception, error_id: str, context: Dict[str, Any] = None):
        """Log error with full details server-side only."""
        logger.error(
            f"Error [{error_id}]: {type(error).__name__}",
            extra={"error_id": error_id, "context": context}
        )
        logger.debug(f"Error [{error_id}] full details:", exc_info=True)

# Enhanced client implementation
class ProductionSearxNGClient(SearxNGClient):
    def __init__(self, base_url: AnyHttpUrl, timeout: int):
        super().__init__(base_url, timeout)
        self.logger = ProductionSafeLogging()
    
    async def search(self, query: str, ...):
        error_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        try:
            self.logger.log_search_request(query)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=self.timeout,
                )
                
                response.raise_for_status()
                data = response.json()
                
                response_time = time.time() - start_time
                result_count = len(data.get('results', []))
                self.logger.log_search_response(response.status_code, result_count, response_time)
                
                return data
                
        except httpx.HTTPStatusError as e:
            self.logger.log_error(e, error_id, {
                "status_code": e.response.status_code,
                "url": str(e.request.url),
                "method": e.request.method
            })
            
            # Client-friendly error messages
            if e.response.status_code == 429:
                raise ValueError("Search service is currently rate-limited. Please try again later.") from None
            elif e.response.status_code >= 500:
                raise ValueError("Search service is temporarily unavailable.") from None
            else:
                raise ValueError(f"Search request failed [Error: {error_id}]") from None
                
        except Exception as e:
            self.logger.log_error(e, error_id, {"query_length": len(query)})
            raise ValueError(f"Search operation failed [Error: {error_id}]") from None
```

#### Option 3: Configuration-Driven Error Levels
```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Error handling configuration
    error_detail_level: Literal["minimal", "standard", "detailed"] = Field(
        default="standard",
        description="Level of error detail to expose (minimal/standard/detailed)"
    )
    
    log_response_content: bool = Field(
        default=False,
        description="Whether to log response content (development only)"
    )
    
    error_tracking_enabled: bool = Field(
        default=True,
        description="Enable error tracking with unique error IDs"
    )

class ConfigurableErrorHandler:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def format_error_message(self, error: Exception, error_id: str) -> str:
        """Format error message based on configuration."""
        if self.settings.error_detail_level == "minimal":
            return "An error occurred during the search operation."
        elif self.settings.error_detail_level == "standard":
            return f"Search operation failed. Error ID: {error_id}"
        else:  # detailed
            return f"Search failed [{error_id}]: {type(error).__name__}: {str(error)}"
    
    def should_log_response_content(self) -> bool:
        """Determine if response content should be logged."""
        return (
            self.settings.log_response_content and 
            self.settings.log_level.upper() == "DEBUG"
        )
```

## Remediation Recommendations

### Immediate (Low Priority)
1. **Add Error ID Generation:**
   ```python
   import uuid
   
   def generate_error_id() -> str:
       """Generate unique error ID for tracking."""
       return str(uuid.uuid4())[:8]
   ```

2. **Separate Client and Server Error Messages:**
   ```python
   # Server-side logging (detailed)
   logger.error(f"[{error_id}] Search failed: {repr(e)}", exc_info=True)
   
   # Client-side message (generic)
   client_message = f"Search operation failed [Error: {error_id}]"
   ```

### Short-term (Medium Priority)
1. **Implement Environment-Based Error Modes:**
   - Development: Full error details
   - Staging: Moderate details with error IDs
   - Production: Generic messages only

2. **Add Response Content Filtering:**
   ```python
   def safe_log_response(response, max_length=100):
       if settings.log_level == "DEBUG":
           logger.debug(f"Response preview: {response.text[:max_length]}")
       else:
           logger.info(f"Response: {response.status_code}, {len(response.text)} bytes")
   ```

### Long-term (Lower Priority)
1. **Structured Logging Integration:**
   - Implement structured logging with consistent fields
   - Add correlation IDs for request tracking
   - Integration with monitoring systems

2. **Error Analytics:**
   ```python
   def track_error_patterns():
       """Track and analyze error patterns for monitoring."""
       # Implementation would integrate with monitoring systems
       pass
   ```

## Testing Verification

### Test Case 1: Error Message Security
```python
def test_error_message_security():
    """Test that error messages don't expose internal details."""
    client = SearxNGClient("https://invalid-searxng-url.com", 1)
    
    try:
        await client.search("test query")
    except ValueError as e:
        error_msg = str(e)
        
        # Should not contain internal paths
        assert "/app/" not in error_msg
        assert "python" not in error_msg.lower()
        
        # Should not contain full stack traces
        assert "Traceback" not in error_msg
        assert "File " not in error_msg
        
        # Should contain error ID for tracking
        assert "Error" in error_msg
```

### Test Case 2: Environment-Based Error Handling
```python
def test_development_vs_production_errors():
    """Test different error detail levels."""
    
    # Development mode - detailed errors
    os.environ["ERROR_MODE"] = "development"
    handler_dev = SecureErrorHandler()
    
    try:
        raise ValueError("Test error message")
    except Exception as e:
        dev_msg = handler_dev.handle_exception(e)
        assert "Test error message" in dev_msg
    
    # Production mode - generic errors
    os.environ["ERROR_MODE"] = "production"
    handler_prod = SecureErrorHandler()
    
    try:
        raise ValueError("Test error message")
    except Exception as e:
        prod_msg = handler_prod.handle_exception(e)
        assert "Test error message" not in prod_msg
        assert "Error ID:" in prod_msg
```

### Test Case 3: Logging Security
```python
def test_response_logging_security():
    """Test that response logging respects privacy settings."""
    
    with patch('logging.Logger.info') as mock_logger:
        client = SearxNGClient("https://example.com", 30)
        
        # Mock response
        mock_response = Mock()
        mock_response.text = "sensitive search results data"
        mock_response.status_code = 200
        
        client.safe_log_response(mock_response)
        
        # Should not log full response content in production
        logged_calls = [call.args[0] for call in mock_logger.call_args_list]
        assert not any("sensitive search results data" in call for call in logged_calls)
```

## Detection and Monitoring

### Log Analysis Patterns
```bash
# Monitor for information disclosure in logs
grep -i "traceback\|exception\|error.*:" /var/log/searxng-mcp.log

# Check for response content logging
grep -i "response:" /var/log/searxng-mcp.log | wc -l

# Monitor error frequency
grep -c "Error \[" /var/log/searxng-mcp.log
```

### Automated Security Checks
```python
def audit_error_handling():
    """Audit codebase for information disclosure in error handling."""
    issues = []
    
    # Check for direct exception exposure
    if "str(e)" in source_code or "repr(e)" in source_code:
        issues.append("Direct exception exposure found")
    
    # Check for response content logging
    if "response.text" in source_code:
        issues.append("Response content logging detected")
    
    # Check for stack trace logging
    if "exc_info=True" in source_code:
        issues.append("Stack trace logging enabled")
    
    return issues
```

### Production Monitoring
```yaml
# Prometheus alerting for error patterns
- alert: HighErrorRate
  expr: increase(searxng_mcp_errors_total[5m]) > 10
  for: 2m
  annotations:
    summary: "High error rate in SearXNG MCP server"

- alert: ErrorInformationDisclosure
  expr: increase(searxng_mcp_detailed_errors_total[1h]) > 5
  annotations:
    summary: "Detailed error messages being exposed"
```

## References
- **CWE-209:** Information Exposure Through Error Messages - https://cwe.mitre.org/data/definitions/209.html
- **OWASP Error Handling:** https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html
- **Python Logging Security:** https://docs.python.org/3/library/logging.html#security-considerations