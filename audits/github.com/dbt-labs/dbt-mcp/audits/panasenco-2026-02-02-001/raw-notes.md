# Raw Audit Notes: dbt-mcp Security Assessment

**Date**: 2026-02-02
**Auditor**: Panasenco
**Target**: dbt-labs/dbt-mcp (commit: 702bc31)

## Initial Assessment Notes

### Architecture Overview
- MCP server for dbt integration
- Multiple tool sets: CLI, Platform APIs, Semantic Layer, Admin API
- OAuth 2.0 + PKCE authentication
- Environment-based configuration
- Modular tool registration system

### Security-Positive Observations
1. **Excellent OAuth Implementation**
   - PKCE properly implemented
   - Automatic token refresh
   - Secure token storage
   - File locking for concurrency
   - Good error handling

2. **Strong Communication Security**
   - All HTTPS communications
   - Modern httpx client library
   - Proper certificate validation
   - No HTTP fallbacks

3. **Good Configuration Management**
   - Environment-based settings
   - Comprehensive validation
   - Auto-disable for missing deps
   - Clear error messages

### Security Concerns Identified

1. **HIGH: Hardcoded OAuth Client ID**
   - File: `src/dbt_mcp/oauth/client_id.py`
   - Client ID: "34ec61e834cdffd9dd90a32231937821"
   - Should be environment variable
   - Impacts credential rotation

2. **MEDIUM: Broad Token Scopes**
   - Single OAuth token for all operations
   - May violate least privilege
   - No scope validation per tool
   - Risk of excessive permissions

3. **MEDIUM: Input Validation Gaps**
   - Basic type checking via pydantic
   - May lack content validation
   - Parameters passed to external systems
   - Potential injection risks

4. **LOW: Dependency Pinning**
   - Some deps use minimum versions
   - Could lead to inconsistent builds
   - Security deps properly pinned
   - Web framework deps unpinned

5. **LOW: Error Information Disclosure**
   - File paths in error messages
   - Configuration details in errors
   - May aid reconnaissance
   - Good credential redaction

## MCP Top 10 Risk Assessment

| Risk | Severity | Status | Notes |
|------|----------|--------|-------|
| MCP-01: Prompt Injection | Low | ✅ | Structured APIs, no LLM processing |
| MCP-02: Confused Deputy | Low | ✅ | Token-based auth, env isolation |
| MCP-03: Tool Poisoning | Medium | ⚠️ | Hardcoded client ID risk |
| MCP-04: Credential Exposure | Medium | ⚠️ | Good handling, scope concerns |
| MCP-05: Insecure Config | Low | ✅ | Excellent config management |
| MCP-06: Supply Chain | Low | ✅ | Good dependency practices |
| MCP-07: Excessive Permissions | Medium | ⚠️ | Broad token scopes |
| MCP-08: Data Exfiltration | Low | ✅ | Controlled API access |
| MCP-09: Context Spoofing | Low | ✅ | Structured interfaces |
| MCP-10: Insecure Comm | Low | ✅ | Proper HTTPS implementation |

## Code Review Highlights

### Authentication Flow (settings.py)
```python
# Excellent token validation
def _is_token_valid(dbt_ctx):
    expires_at = dbt_ctx.decoded_access_token.access_token_response.expires_at
    return expires_at > time.time() + 120  # 2-minute buffer!
```

### OAuth Client ID Issue (client_id.py)
```python
OAUTH_CLIENT_ID = "34ec61e834cdffd9dd90a32231937821"  # SECURITY ISSUE
```

### Tool Configuration (tool_names.py)
- Comprehensive tool enumeration
- Good separation of concerns
- All tools use same auth token (concern)

### Dependencies (pyproject.toml)
- Security libs pinned: authlib==1.6.6, pyjwt==2.10.1
- Web libs unpinned: fastapi>=0.116.1, uvicorn>=0.31.1

## Recommendations Priority

### High Priority (Security Fixes)
1. Move OAuth client ID to environment variable
2. Implement client ID validation
3. Review and minimize OAuth token scopes

### Medium Priority (Hardening)
1. Enhance input validation for tool parameters
2. Implement scope validation for sensitive operations
3. Pin web framework dependencies

### Low Priority (Security Hygiene)
1. Sanitize error messages for path disclosure
2. Add comprehensive audit logging
3. Implement token rotation policies

## Overall Assessment

**Risk Level**: Medium
**Production Ready**: Yes, with hardening
**Architecture Quality**: Excellent
**Security Practices**: Generally strong

The dbt-mcp server demonstrates strong security engineering with excellent OAuth implementation and secure communication practices. The identified issues are addressable and don't prevent production deployment with appropriate hardening.

## Audit Completeness

- [x] Authentication mechanisms reviewed
- [x] Input validation assessed
- [x] Communication security verified
- [x] Configuration management evaluated
- [x] Dependency analysis completed
- [x] MCP Top 10 risks assessed
- [x] Code samples documented
- [x] Recommendations prioritized