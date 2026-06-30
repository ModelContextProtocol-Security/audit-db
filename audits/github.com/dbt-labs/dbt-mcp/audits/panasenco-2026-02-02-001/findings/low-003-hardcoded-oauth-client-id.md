# Finding: Hardcoded OAuth Client ID Limits Configuration Flexibility

**Finding ID**: low-004-hardcoded-oauth-client-id
**Severity**: Low
**Category**: Configuration Management
**CWE**: CWE-547 (Use of Hard-coded, Security-relevant Constants)
**CVSS Score**: 2.3

## Executive Summary
The OAuth client ID is hardcoded in source code, which limits configuration flexibility and makes it difficult to use different client IDs for different environments, though this does not represent a security vulnerability per the OAuth 2.0 specification.

## Technical Description
The file `src/dbt_mcp/oauth/client_id.py` contains a hardcoded OAuth client ID value. According to RFC 6749 Section 2.1, the client identifier is not a secret and is exposed to the resource owner, and must not be used alone for client authentication. However, hardcoding this value limits operational flexibility for different deployment scenarios.

## Evidence
```python
# File: src/dbt_mcp/oauth/client_id.py
OAUTH_CLIENT_ID = "34ec61e834cdffd9dd90a32231937821"
```

Per RFC 6749 Section 2.1:
> "The client identifier is not a secret; it is exposed to the resource owner and MUST NOT be used alone for client authentication."

## Impact Assessment
- **Confidentiality**: None - OAuth client IDs are not secrets per RFC specification
- **Integrity**: Low - Limited impact on system integrity
- **Availability**: Low - Potential service disruption during client ID changes
- **Exploitability**: Low - Client ID exposure is expected behavior per OAuth spec
- **Scope**: Configuration management and deployment flexibility

## Affected Components
- File: `src/dbt_mcp/oauth/client_id.py` (line 1)
- OAuth authentication configuration
- Deployment and environment management

## Reproduction Steps
1. Clone the repository
2. Navigate to `src/dbt_mcp/oauth/client_id.py`
3. Observe the hardcoded OAuth client ID value
4. Note that changing client ID requires code modification rather than configuration change

**Expected**: Client ID configurable via environment variables for deployment flexibility
**Actual**: Client ID is hardcoded requiring code changes for different configurations

## Risk Scenarios
1. **Configuration Inflexibility**: Different environments (dev, staging, prod) cannot easily use different client IDs
2. **Deployment Complexity**: Client ID changes require code changes and redeployment rather than configuration updates
3. **Multi-tenant Challenges**: Difficult to support multiple dbt Platform instances with different client IDs

## Recommendations

### Immediate Actions
- [ ] Move OAuth client ID to environment variable (e.g., `DBT_OAUTH_CLIENT_ID`)
- [ ] Provide default value for backward compatibility
- [ ] Update configuration documentation

### Short-term Improvements
- [ ] Add support for different client IDs per environment
- [ ] Document the OAuth configuration options
- [ ] Add validation for client ID format if needed

### Long-term Strategic Changes
- [ ] Consider supporting multiple OAuth client configurations
- [ ] Add OAuth client registration documentation
- [ ] Implement configuration validation for OAuth parameters

## Remediation Validation
1. Verify OAuth flows work with environment-variable-based client ID
2. Confirm backward compatibility if default value is provided
3. Test different client IDs can be used for different environments
4. Validate proper error handling when client ID is missing or invalid

## References
- [RFC 6749 Section 2.1 - Client Identifier](https://www.rfc-editor.org/rfc/rfc6749#section-2.1)
- [OAuth 2.0 Security Best Current Practice](https://tools.ietf.org/html/draft-ietf-oauth-security-topics)
- [CWE-547: Use of Hard-coded, Security-relevant Constants](https://cwe.mitre.org/data/definitions/547.html)

## Status Tracking
- [x] Identified: 2026-02-02
- [x] Documented: 2026-02-02
- [ ] Reported to maintainers:
- [ ] Acknowledged by maintainers:
- [ ] Fix available:
- [ ] Fix verified:
- [ ] Closed:

## Auditor Notes
This finding addresses configuration flexibility rather than security. Per RFC 6749, OAuth client identifiers are not secrets and their exposure is expected behavior. The low severity reflects operational concerns about deployment flexibility rather than security vulnerabilities.