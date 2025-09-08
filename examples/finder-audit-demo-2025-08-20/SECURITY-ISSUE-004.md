# Security Issue #004: Unvalidated External URL Dependencies

## Issue Metadata
- **Issue ID:** SECURITY-004
- **Category:** Supply Chain Security / External Dependencies
- **Severity:** Low-Medium
- **CWE:** CWE-829 (Inclusion of Functionality from Untrusted Control Sphere)
- **CVSS Score:** 3.1/10.0 (Low)
- **AIVSS Score:** 4.2/10.0 (Low-Medium)
- **Status:** Open
- **Found Date:** 2025-08-20

## Issue Description
The server configuration allows arbitrary external SearXNG URLs to be specified without validation, verification, or allowlisting. This could enable attacks where malicious actors provide compromised or malicious SearXNG instances that return crafted search results or collect sensitive search queries.

## Affected Code Location
**File:** `src/searxng_simple_mcp/config.py`
**Lines:** 35-38

```python
# SearxNG instance URL
searxng_url: AnyHttpUrl = Field(
    default=DEFAULT_SEARXNG_URL, 
    description="URL of the SearxNG instance to use"  # ⚠️ NO URL VALIDATION/ALLOWLISTING
)
```

**File:** `src/searxng_simple_mcp/searxng_client.py`  
**Lines:** 18-27, 68-74

```python
def __init__(self, base_url: AnyHttpUrl, timeout: int) -> None:
    """Initialize the SearxNG client."""
    self.base_url = str(base_url).rstrip("/")  # ⚠️ ACCEPTS ANY URL
    self.timeout = timeout

# Later used directly without validation
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{self.base_url}/search",  # ⚠️ UNVALIDATED EXTERNAL REQUEST
        params=params,
        timeout=self.timeout,
    )
```

## Vulnerability Analysis

### Attack Vectors
1. **Data Exfiltration:** Malicious SearXNG instance logs all search queries
2. **Response Manipulation:** Attacker-controlled responses influence AI behavior
3. **Reconnaissance:** Malicious instance gathers intelligence about usage patterns
4. **Injection Attacks:** Crafted responses exploit client-side processing
5. **Man-in-the-Middle:** Unverified HTTPS endpoints could be compromised

### Technical Details
- No URL allowlisting or domain validation
- No certificate pinning or additional TLS verification
- No response content validation or sanitization
- Configuration change could redirect to malicious services
- Default URL is external third-party service (https://paulgo.io/)

## Risk Assessment by Usage Context

### Local Single-User MCP (Risk: Very Low - 1.5/10)
**Scenario:** User running MCP server locally for personal use
- ✅ **User Control:** User explicitly configures trusted SearXNG instances
- ✅ **Limited Exposure:** Personal search queries, user aware of risk
- **Recommendation:** Optional allowlisting for additional security

### Remote SSE-Enabled Multi-User (Risk: Medium - 6.1/10)
**Scenario:** MCP server running remotely with SSE transport serving multiple users
- ⚠️ **Shared Configuration:** Single URL configuration affects all users
- ⚠️ **Data Privacy:** Multiple users' search queries at risk
- ⚠️ **Trust Boundary:** Users may not be aware of external dependency
- **Recommendation:** Implement URL allowlisting and validation

### Enterprise/Production Deployment (Risk: Medium-High - 7.3/10)
**Scenario:** Production deployment in corporate environment
- 🚨 **Data Governance:** Corporate search queries sent to external services
- 🚨 **Compliance Risk:** May violate data handling policies
- 🚨 **Supply Chain Risk:** Dependency on external third-party service
- **Recommendation:** Mandatory allowlisting, consider self-hosted SearXNG

## CVSS 4.0 Scoring Breakdown

**Base Score Metrics:**
- **Attack Vector (AV):** Network (0.85) - Requires network access to malicious service
- **Attack Complexity (AC):** Medium (0.44) - Requires deployment of malicious SearXNG
- **Privileges Required (PR):** Low (0.62) - Requires configuration access
- **User Interaction (UI):** None (0.85) - Automatic on search requests
- **Scope (S):** Changed (1.0) - Affects external data/privacy
- **Confidentiality Impact (C):** Low (0.22) - Search queries disclosed
- **Integrity Impact (I):** Low (0.22) - Response manipulation possible
- **Availability Impact (A):** None (0.0) - No service disruption

**CVSS Base Score:** 3.1/10.0 (Low)

## AIVSS Factors (AI Considerations)

**AI-Specific Risk Factors:**
- **Data Intelligence Harvesting (DIH):** Medium (+0.8) - AI search patterns valuable for intelligence
- **Response Influence (RI):** Low (+0.3) - Malicious responses could influence AI decisions
- **Automated Request Patterns (ARP):** Low (+0.2) - AI agents create predictable patterns
- **Context Leakage (CL):** Low (+0.2) - Search queries may contain sensitive context

**AIVSS Adjustment:** +1.1
**Final AIVSS Score:** 4.2/10.0 (Low-Medium)

## Code Examples

### Current Vulnerable Implementation
```python
# Configuration accepts any URL
class Settings(BaseSettings):
    searxng_url: AnyHttpUrl = Field(
        default="https://paulgo.io/",  # ⚠️ External third-party service
        description="URL of the SearxNG instance to use"  # ⚠️ No restrictions
    )

# Client uses URL without validation
class SearxNGClient:
    def __init__(self, base_url: AnyHttpUrl, timeout: int):
        self.base_url = str(base_url).rstrip("/")  # ⚠️ Direct usage
        
    async def search(self, query: str, ...):
        # Direct request to potentially untrusted URL
        response = await client.get(f"{self.base_url}/search", ...)  # ⚠️ No validation
```

### Recommended Secure Implementation

#### Option 1: URL Allowlisting
```python
from pydantic import field_validator
from typing import Set

class Settings(BaseSettings):
    searxng_url: AnyHttpUrl = Field(
        default="https://paulgo.io/",
        description="URL of the SearXNG instance to use"
    )
    
    # Allowlisted SearXNG instances
    allowed_searxng_domains: Set[str] = Field(
        default={
            "paulgo.io",
            "searx.tiekoetter.com", 
            "search.privacyguides.org",
            "localhost",
            "127.0.0.1"
        },
        description="Allowed SearXNG domain names"
    )
    
    @field_validator('searxng_url')
    @classmethod
    def validate_searxng_url(cls, v, info):
        """Validate SearXNG URL against allowlist."""
        from urllib.parse import urlparse
        
        parsed = urlparse(str(v))
        allowed_domains = info.data.get('allowed_searxng_domains', set())
        
        if parsed.hostname not in allowed_domains:
            raise ValueError(
                f"SearXNG URL domain '{parsed.hostname}' not in allowlist: {allowed_domains}"
            )
            
        # Enforce HTTPS in production
        if parsed.scheme != 'https' and parsed.hostname not in ['localhost', '127.0.0.1']:
            raise ValueError("SearXNG URL must use HTTPS for remote instances")
            
        return v
```

#### Option 2: Enhanced Validation with Certificate Pinning
```python
import ssl
import hashlib
from typing import Optional, Dict

class SecureSearxNGClient(SearxNGClient):
    def __init__(
        self, 
        base_url: AnyHttpUrl, 
        timeout: int,
        cert_fingerprints: Optional[Dict[str, str]] = None
    ):
        super().__init__(base_url, timeout)
        self.cert_fingerprints = cert_fingerprints or {}
        
    def _create_ssl_context(self, hostname: str) -> Optional[ssl.SSLContext]:
        """Create SSL context with certificate pinning if configured."""
        if hostname not in self.cert_fingerprints:
            return None
            
        context = ssl.create_default_context()
        expected_fingerprint = self.cert_fingerprints[hostname]
        
        def verify_cert(cert_der, hostname, _):
            cert_sha256 = hashlib.sha256(cert_der).hexdigest()
            if cert_sha256 != expected_fingerprint:
                raise ssl.CertificateError(
                    f"Certificate fingerprint mismatch for {hostname}"
                )
        
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        return context
    
    async def search(self, query: str, ...):
        from urllib.parse import urlparse
        
        parsed_url = urlparse(self.base_url)
        ssl_context = self._create_ssl_context(parsed_url.hostname)
        
        async with httpx.AsyncClient(verify=ssl_context) as client:
            response = await client.get(...)
            
            # Validate response structure
            self._validate_response(response)
            return response.json()
    
    def _validate_response(self, response):
        """Validate SearXNG response structure."""
        if response.status_code != 200:
            raise ValueError(f"Invalid response status: {response.status_code}")
            
        try:
            data = response.json()
        except ValueError:
            raise ValueError("Response is not valid JSON")
        
        # Check for expected SearXNG response structure
        if not isinstance(data, dict):
            raise ValueError("Response is not a JSON object")
            
        if 'results' not in data:
            raise ValueError("Response missing 'results' field")
            
        if not isinstance(data['results'], list):
            raise ValueError("'results' field is not an array")
```

#### Option 3: Configuration with Environment-Based Allowlists
```python
class Settings(BaseSettings):
    searxng_url: AnyHttpUrl = Field(
        default="https://paulgo.io/",
        description="URL of the SearXNG instance to use"
    )
    
    # Environment-configurable allowlist
    searxng_allowed_domains: str = Field(
        default="paulgo.io,searx.tiekoetter.com,localhost,127.0.0.1",
        description="Comma-separated list of allowed SearXNG domains"
    )
    
    # Strict mode for production
    searxng_strict_validation: bool = Field(
        default=True,
        description="Enable strict URL validation and HTTPS enforcement"
    )
    
    @field_validator('searxng_url')
    @classmethod
    def validate_searxng_url(cls, v, info):
        """Comprehensive URL validation."""
        from urllib.parse import urlparse
        import re
        
        url_str = str(v)
        parsed = urlparse(url_str)
        
        # Get validation settings
        allowed_domains_str = info.data.get('searxng_allowed_domains', '')
        allowed_domains = [d.strip() for d in allowed_domains_str.split(',') if d.strip()]
        strict_validation = info.data.get('searxng_strict_validation', True)
        
        # Domain validation
        if parsed.hostname not in allowed_domains:
            raise ValueError(
                f"Domain '{parsed.hostname}' not in allowlist. "
                f"Allowed: {allowed_domains}. "
                f"Set SEARXNG_MCP_SEARXNG_ALLOWED_DOMAINS to modify."
            )
        
        # Protocol validation
        if strict_validation and parsed.scheme != 'https':
            if parsed.hostname not in ['localhost', '127.0.0.1', '::1']:
                raise ValueError(
                    f"HTTPS required for remote domains in strict mode. "
                    f"Got: {parsed.scheme}://{parsed.hostname}"
                )
        
        # Path validation (prevent path traversal)
        if '..' in parsed.path or '//' in parsed.path:
            raise ValueError("Invalid characters in URL path")
            
        # Port validation (prevent unusual ports)
        if parsed.port and parsed.port not in [80, 443, 8080, 8443]:
            if strict_validation:
                raise ValueError(f"Unusual port {parsed.port} not allowed in strict mode")
        
        return v
```

## Remediation Recommendations

### Immediate (Medium Priority)
1. **Implement Basic URL Validation:**
   ```python
   @field_validator('searxng_url')
   @classmethod
   def validate_url(cls, v):
       parsed = urlparse(str(v))
       # Enforce HTTPS for remote URLs
       if parsed.hostname not in ['localhost', '127.0.0.1'] and parsed.scheme != 'https':
           raise ValueError("Remote SearXNG instances must use HTTPS")
       return v
   ```

2. **Add Configuration Warning:**
   ```python
   # In Settings class
   def __post_init__(self):
       if not self.searxng_url.startswith('https://'):
           logger.warning(
               "Using non-HTTPS SearXNG URL. Search queries will be sent unencrypted."
           )
   ```

### Short-term (Medium Priority)
1. **Implement Domain Allowlisting:**
   - Add environment variable for allowed domains
   - Validate URLs against allowlist during configuration loading
   - Provide clear error messages for rejected URLs

2. **Response Validation:**
   ```python
   def _validate_searxng_response(self, data: dict) -> bool:
       """Validate that response looks like genuine SearXNG output."""
       required_fields = ['results', 'query']
       return all(field in data for field in required_fields)
   ```

### Long-term (Lower Priority)
1. **Certificate Pinning:**
   - Implement certificate fingerprint validation
   - Add configuration for trusted certificates
   - Monitor for certificate changes

2. **Self-Hosted SearXNG Recommendation:**
   ```python
   # Add deployment documentation
   def recommend_self_hosted():
       """Provide guidance on deploying self-hosted SearXNG."""
       return """
       For production deployments, consider self-hosting SearXNG:
       
       1. Deploy SearXNG using Docker:
          docker run -d -p 8080:8080 searxng/searxng
          
       2. Configure internal URL:
          export SEARXNG_MCP_SEARXNG_URL=http://localhost:8080
          
       3. Benefits:
          - No external data sharing
          - Full control over search sources
          - Custom configuration options
       """
   ```

## Testing Verification

### Test Case 1: URL Validation
```python
def test_url_validation():
    # Valid URLs should be accepted
    valid_urls = [
        "https://paulgo.io/",
        "https://searx.tiekoetter.com/",
        "http://localhost:8080/"
    ]
    for url in valid_urls:
        settings = Settings(searxng_url=url)
        assert settings.searxng_url == url
    
    # Invalid URLs should be rejected
    invalid_urls = [
        "http://malicious-searxng.evil.com/",
        "https://not-in-allowlist.com/",
        "ftp://searxng.example.com/"
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError):
            Settings(searxng_url=url)
```

### Test Case 2: Response Validation
```python
async def test_response_validation():
    client = SecureSearxNGClient("https://paulgo.io/", 30)
    
    # Valid response should be accepted
    valid_response = {
        "results": [{"title": "Test", "url": "https://example.com"}],
        "query": "test query"
    }
    assert client._validate_searxng_response(valid_response)
    
    # Invalid response should be rejected
    invalid_responses = [
        {},  # Missing fields
        {"results": "not an array"},  # Wrong type
        {"query": "test"}  # Missing results
    ]
    for response in invalid_responses:
        assert not client._validate_searxng_response(response)
```

### Test Case 3: Configuration Security
```python
def test_configuration_security():
    # Test that environment variables are properly validated
    os.environ['SEARXNG_MCP_SEARXNG_URL'] = 'http://malicious.com/'
    
    with pytest.raises(ValueError, match="not in allowlist"):
        Settings()
    
    # Test that allowlist can be modified
    os.environ['SEARXNG_MCP_SEARXNG_ALLOWED_DOMAINS'] = 'malicious.com,paulgo.io'
    settings = Settings(searxng_url='https://malicious.com/')
    assert 'malicious.com' in settings.searxng_allowed_domains
```

## Detection and Monitoring

### Configuration Monitoring
```python
def audit_searxng_configuration():
    """Audit current SearXNG configuration for security issues."""
    settings = Settings()
    issues = []
    
    # Check URL security
    if not str(settings.searxng_url).startswith('https://'):
        issues.append("SearXNG URL does not use HTTPS")
    
    # Check domain allowlist
    parsed = urlparse(str(settings.searxng_url))
    if parsed.hostname not in TRUSTED_DOMAINS:
        issues.append(f"SearXNG domain '{parsed.hostname}' not in trusted list")
    
    return issues
```

### Runtime Monitoring
```bash
# Monitor external requests
netstat -an | grep :443 | grep ESTABLISHED

# Log external URL access
tail -f /var/log/searxng-mcp.log | grep "SearXNG request"
```

### Security Scanning
```yaml
# GitHub Actions workflow to validate configuration
- name: Validate SearXNG Configuration
  run: |
    python -c "
    from src.searxng_simple_mcp.config import Settings
    settings = Settings()
    assert str(settings.searxng_url).startswith('https://'), 'Non-HTTPS URL detected'
    print('✅ Configuration security validated')
    "
```

## References
- **CWE-829:** Inclusion of Functionality from Untrusted Control Sphere - https://cwe.mitre.org/data/definitions/829.html
- **OWASP Supply Chain Security:** https://owasp.org/www-project-software-component-verification-standard/
- **Certificate Pinning Best Practices:** https://owasp.org/www-community/controls/Certificate_and_Public_Key_Pinning
- **SearXNG Security Documentation:** https://docs.searxng.org/admin/installation.html#security