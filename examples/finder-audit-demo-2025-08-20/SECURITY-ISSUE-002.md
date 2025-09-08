# Security Issue #002: No Rate Limiting on Search Operations

## Issue Metadata
- **Issue ID:** SECURITY-002
- **Category:** Resource Management / DoS Prevention
- **Severity:** Medium
- **CWE:** CWE-770 (Allocation of Resources Without Limits or Throttling)
- **CVSS Score:** 4.3/10.0 (Medium)
- **AIVSS Score:** 5.8/10.0 (Medium)
- **Status:** Open
- **Found Date:** 2025-08-20

## Issue Description
The web search functionality lacks rate limiting controls, allowing unlimited concurrent requests to the backend SearXNG service. This could lead to resource exhaustion, service degradation, or potential abuse of the underlying search infrastructure.

## Affected Code Location
**File:** `src/searxng_simple_mcp/server.py`
**Lines:** 45-106

```python
@mcp.tool()
async def web_search(
    query: str = Field(description="The search query string to look for on the web"),
    result_count: int = Field(
        default=settings.default_result_count,
        description="Maximum number of results to return",
        gt=0,
    ),
    # ... other parameters
) -> str | dict[str, Any]:
    """Performs a web search using SearxNG and returns formatted results."""
    # ⚠️ NO RATE LIMITING IMPLEMENTED
    # ⚠️ NO CONCURRENT REQUEST LIMITING
    # ⚠️ NO ABUSE PROTECTION
    
    try:
        results = await searxng_client.search(  # Unlimited calls possible
            query,
            categories=categories,
            language=language,
            time_range=time_range,
        )
        # ... processing logic
```

**File:** `src/searxng_simple_mcp/searxng_client.py`
**Lines:** 67-87

```python
async with httpx.AsyncClient() as client:  # ⚠️ No connection limits
    response = await client.get(
        f"{self.base_url}/search",
        params=params,
        timeout=self.timeout,  # Only timeout protection
    )
```

## Vulnerability Analysis

### Attack Vectors
1. **Resource Exhaustion:** Rapid-fire search requests consuming server resources
2. **Backend Overload:** Overwhelming the SearXNG instance with requests
3. **Economic DoS:** Causing high costs if backend service is metered
4. **Service Degradation:** Impacting legitimate users through resource competition

### Technical Details
- No request frequency limits per client/session
- No concurrent connection limits to backend
- No queue management for high-volume scenarios  
- No circuit breaker pattern for backend protection

## Risk Assessment by Usage Context

### Local Single-User MCP (Risk: Very Low - 1.8/10)
**Scenario:** User running MCP server locally for personal use
- ✅ **Self-Limited:** User controls their own request patterns
- ✅ **Resource Bounded:** Limited by local machine capabilities
- **Recommendation:** Optional - implement basic limits for stability

### Remote SSE-Enabled Multi-User (Risk: High - 7.4/10)
**Scenario:** MCP server running remotely with SSE transport serving multiple users
- 🚨 **Critical Concern:** Multiple users could overwhelm backend service
- 🚨 **Amplification Risk:** Each user could spawn multiple concurrent requests
- 🚨 **Economic Impact:** High costs from backend service abuse
- **Recommendation:** Implement comprehensive rate limiting immediately

### Enterprise/Production Deployment (Risk: Very High - 8.6/10)
**Scenario:** Production deployment in corporate environment
- 🚨 **Service Reliability:** Could cause cascading failures
- 🚨 **SLA Violations:** Uncontrolled resource usage affecting SLAs
- 🚨 **Security Policy:** Violates DoS protection requirements
- **Recommendation:** Mandatory rate limiting with monitoring and alerting

## CVSS 4.0 Scoring Breakdown

**Base Score Metrics:**
- **Attack Vector (AV):** Network (0.85) - Accessible via MCP protocol
- **Attack Complexity (AC):** Low (0.77) - Simple repeated requests
- **Privileges Required (PR):** Low (0.62) - Requires MCP client access
- **User Interaction (UI):** None (0.85) - Automated attacks possible
- **Scope (S):** Changed (1.0) - Affects backend service availability
- **Confidentiality Impact (C):** None (0.0) - No data disclosure
- **Integrity Impact (I):** None (0.0) - No data modification
- **Availability Impact (A):** Medium (0.56) - Service degradation possible

**CVSS Base Score:** 4.3/10.0 (Medium)

## AIVSS Factors (AI Considerations)

**AI-Specific Risk Factors:**
- **Autonomous Amplification (AA):** High (+1.2) - AI agents could generate high-volume automated requests
- **Tool Access Abuse (TAA):** Medium (+0.5) - Search tool could be misused for reconnaissance/scraping
- **Resource Competition (RC):** Medium (+0.3) - Multiple AI agents competing for search resources
- **Backend Service Risk (BSR):** Medium (+0.5) - Risk to third-party service infrastructure

**AIVSS Adjustment:** +1.5
**Final AIVSS Score:** 5.8/10.0 (Medium)

## Code Examples

### Current Vulnerable Implementation
```python
# NO RATE LIMITING
@mcp.tool()
async def web_search(query: str, ...):
    # Direct call - no limits
    results = await searxng_client.search(query, ...)
    return results

class SearxNGClient:
    async def search(self, query: str, ...):
        # No connection limiting
        async with httpx.AsyncClient() as client:
            response = await client.get(...)  # Unlimited concurrent calls
```

### Recommended Secure Implementation

#### Option 1: Simple Rate Limiting with AsyncLimiter
```python
from asyncio_throttle import Throttler

class RateLimitedSearxNGClient(SearxNGClient):
    def __init__(self, base_url: AnyHttpUrl, timeout: int, rate_limit: int = 10):
        super().__init__(base_url, timeout)
        # Allow 10 requests per minute
        self.throttler = Throttler(rate_limit=rate_limit, period=60)
        
    async def search(self, query: str, ...):
        # Apply rate limiting
        async with self.throttler:
            async with httpx.AsyncClient(
                limits=httpx.Limits(max_connections=5)  # Connection limiting
            ) as client:
                response = await client.get(...)
                return response.json()
```

#### Option 2: Token Bucket Rate Limiting
```python
import asyncio
import time
from typing import Dict

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        
    async def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        # Refill tokens based on time elapsed
        self.tokens = min(
            self.capacity,
            self.tokens + (now - self.last_refill) * self.refill_rate
        )
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# Global rate limiter per client
rate_limiters: Dict[str, TokenBucket] = {}

@mcp.tool()
async def web_search(query: str, ..., ctx: Context = None):
    client_id = ctx.session_id if ctx else "default"
    
    # Get or create rate limiter for this client
    if client_id not in rate_limiters:
        rate_limiters[client_id] = TokenBucket(capacity=10, refill_rate=0.2)  # 10 requests, refill 1 every 5 seconds
    
    rate_limiter = rate_limiters[client_id]
    
    # Check rate limit
    if not await rate_limiter.consume():
        raise ValueError("Rate limit exceeded. Please wait before making another request.")
    
    # Proceed with search
    results = await searxng_client.search(query, ...)
    return results
```

#### Option 3: Advanced Rate Limiting with Configuration
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class RateLimitConfig:
    requests_per_minute: int = 10
    burst_allowance: int = 3
    per_client_limit: bool = True
    global_limit: Optional[int] = 100  # Global requests per minute across all clients

class Settings(BaseSettings):
    # ... existing settings
    
    # Rate limiting configuration
    rate_limit_requests_per_minute: int = Field(
        default=10, 
        description="Maximum requests per minute per client"
    )
    rate_limit_burst_allowance: int = Field(
        default=3,
        description="Burst allowance for rate limiting"
    )
    rate_limit_global_limit: Optional[int] = Field(
        default=100,
        description="Global rate limit across all clients"
    )

# Enhanced server with configurable rate limiting
@mcp.tool()
async def web_search(query: str, ..., ctx: Context = None):
    # Apply rate limiting based on configuration
    await apply_rate_limiting(ctx, settings)
    
    # Proceed with search
    results = await searxng_client.search(query, ...)
    return results
```

## Remediation Recommendations

### Immediate (High Priority)
1. **Implement Basic Rate Limiting:**
   ```python
   # Add simple per-client rate limiting
   from collections import defaultdict
   import time
   
   request_timestamps = defaultdict(list)
   
   async def check_rate_limit(client_id: str, max_requests: int = 10, window: int = 60):
       now = time.time()
       timestamps = request_timestamps[client_id]
       
       # Remove old timestamps
       timestamps[:] = [t for t in timestamps if now - t < window]
       
       if len(timestamps) >= max_requests:
           raise ValueError(f"Rate limit exceeded: {max_requests} requests per {window} seconds")
           
       timestamps.append(now)
   ```

2. **Add Connection Limits:**
   ```python
   # Limit concurrent connections to backend
   async with httpx.AsyncClient(
       limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
   ) as client:
       # ... request logic
   ```

### Short-term (Medium Priority)
1. **Configuration-Based Limits:**
   - Add rate limiting settings to configuration
   - Support different limits for different deployment types
   - Add environment variables for production tuning

2. **Enhanced Error Handling:**
   ```python
   if not await rate_limiter.consume():
       if ctx:
           ctx.error("Rate limit exceeded. Please slow down your requests.")
       raise ValueError("Rate limit exceeded. Try again later.")
   ```

3. **Monitoring and Metrics:**
   - Log rate limiting events
   - Track request patterns per client
   - Monitor backend service health

### Long-term (Lower Priority)
1. **Advanced Rate Limiting:**
   - Implement sliding window rate limiting
   - Add priority queuing for different request types
   - Integration with external rate limiting services

2. **Circuit Breaker Pattern:**
   ```python
   class CircuitBreaker:
       def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
           self.failure_threshold = failure_threshold
           self.recovery_timeout = recovery_timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
   ```

## Testing Verification

### Test Case 1: Rate Limit Enforcement
```python
import pytest
import asyncio

async def test_rate_limiting():
    # Make requests up to the limit
    for i in range(10):
        result = await web_search(f"test query {i}")
        assert "error" not in result
    
    # Next request should be rate limited
    with pytest.raises(ValueError, match="Rate limit exceeded"):
        await web_search("rate limited query")
```

### Test Case 2: Rate Limit Recovery
```python
async def test_rate_limit_recovery():
    # Exhaust rate limit
    for i in range(10):
        await web_search(f"test query {i}")
    
    # Wait for rate limit window to reset
    await asyncio.sleep(61)  # Wait 61 seconds for 60-second window
    
    # Should be able to make requests again
    result = await web_search("recovery test")
    assert "error" not in result
```

### Test Case 3: Concurrent Request Limiting
```python
async def test_concurrent_limits():
    # Test connection pool limits
    tasks = [web_search(f"concurrent query {i}") for i in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Should not overwhelm backend
    successful = [r for r in results if not isinstance(r, Exception)]
    assert len(successful) > 0  # Some should succeed
```

## Detection and Monitoring

### Log Patterns to Monitor
```
Rate limit exceeded for client: <client_id>
High request volume detected: <requests_per_minute>
Backend service timeout increase detected
```

### Automated Detection
```bash
# Monitor for high-frequency requests
grep "Rate limit exceeded" logs/server.log | wc -l

# Check for backend service errors
curl -s ${SEARXNG_URL}/search?q=test | jq .error
```

### Metrics to Track
- Requests per minute per client
- Backend service response times
- Rate limiting trigger frequency
- Connection pool utilization

## References
- **CWE-770:** Allocation of Resources Without Limits - https://cwe.mitre.org/data/definitions/770.html
- **OWASP Rate Limiting:** https://cheatsheetseries.owasp.org/cheatsheets/Rate_Limiting_Cheat_Sheet.html
- **DoS Prevention Best Practices:** https://owasp.org/www-community/attacks/Denial_of_Service