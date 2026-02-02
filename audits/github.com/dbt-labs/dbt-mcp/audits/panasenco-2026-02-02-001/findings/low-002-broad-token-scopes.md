# Finding: Broad OAuth Token Scopes May Violate Principle of Least Privilege

**Finding ID**: low-003-broad-token-scopes
**Severity**: Low
**Category**: Access Control & Authorization
**CWE**: CWE-266 (Incorrect Privilege Assignment)
**CVSS Score**: 3.9

## Executive Summary
The OAuth authentication flow may request broader permissions than necessary for specific MCP server operations, violating the principle of least privilege and potentially exposing more data and functionality than required.

## Technical Description
The dbt-mcp server uses OAuth tokens to access dbt Platform APIs and while all authenticated operations use the same token, the server provides extensive tool disabling capabilities that allow users to implement principle of least privilege by restricting which tools are available. However, there is no automatic scope validation to ensure tokens have minimal required permissions.

## Evidence
From the settings and authentication code:
- OAuth tokens are used for multiple tool sets (Discovery, Semantic Layer, Admin API, SQL execution)
- Single token used for all operations regardless of required permissions
- No automatic scope validation to verify token has minimal required permissions

However, extensive tool disabling capabilities provide mitigation:
```python
# Toolset-level disabling (from settings.py):
DISABLE_SEMANTIC_LAYER = "disable_semantic_layer"
DISABLE_ADMIN_API = "disable_admin_api"
DISABLE_SQL = "disable_sql"
DISABLE_DBT_CLI = "disable_dbt_cli"

# Individual tool disabling:
DISABLE_TOOLS = "comma-separated list of tool names"
DBT_MCP_ENABLE_TOOLS = "allowlist mode - only specified tools enabled"
```

High-privilege operations that can be disabled:
```python
# From tool_names.py - These can all be individually disabled:
EXECUTE_SQL = "execute_sql"  # Can execute arbitrary SQL
TRIGGER_JOB_RUN = "trigger_job_run"  # Can trigger production jobs
CANCEL_JOB_RUN = "cancel_job_run"  # Can cancel running jobs
```

## Impact Assessment
- **Confidentiality**: Low - Read access can be limited by disabling discovery/semantic layer tools
- **Integrity**: Low - Write operations can be disabled (SQL execution, job management)
- **Availability**: Low - Administrative tools can be disabled to prevent service disruption
- **Exploitability**: Low - Requires compromised token, and impact is mitigated by tool disabling
- **Scope**: Configurable based on enabled toolsets

## Affected Components
- File: `src/dbt_mcp/config/settings.py` - Token provider implementation
- File: `src/dbt_mcp/oauth/token_provider.py` - Token management
- All tool implementations that use OAuth authentication
- dbt Platform API interactions

## Reproduction Steps
1. Configure dbt-mcp with OAuth authentication
2. Authenticate and obtain an OAuth token
3. Observe that the same token is used for all operations
4. Note that no scope validation prevents high-privilege operations
5. Verify that disabling specific tools doesn't restrict token permissions

**Expected**: Different scopes or tokens for different privilege levels
**Actual**: Single token used for all operations with potentially broad permissions

## Risk Scenarios
1. **Token Compromise**: If an OAuth token is compromised, attacker gains access to all platform capabilities the token allows
2. **Privilege Escalation**: Users or AI agents may inadvertently access data or functions beyond their intended scope
3. **Lateral Movement**: Broad permissions enable movement across different dbt Platform resources
4. **Data Exfiltration**: Excessive read permissions may expose sensitive data beyond requirements
5. **Service Disruption**: Broad administrative permissions could allow disruption of production workflows

## Recommendations

### Immediate Actions
- [ ] Document recommended tool disabling configurations for different security levels
- [ ] Disable unused toolsets in production deployments (use `DISABLE_*` environment variables)
- [ ] Implement allowlist mode (`DBT_MCP_ENABLE_TOOLS`) for high-security environments

### Short-term Improvements
- [ ] Implement tool-specific scope validation
- [ ] Add permission checking before executing sensitive operations
- [ ] Create different OAuth clients/scopes for different tool sets
- [ ] Add scope-based tool filtering to ensure consistency

### Long-term Strategic Changes
- [ ] Implement fine-grained permission model with role-based access
- [ ] Add support for multiple OAuth tokens with different scopes
- [ ] Implement dynamic scope request based on enabled tools
- [ ] Add permission auditing and monitoring capabilities

## Remediation Validation
1. Verify scope validation is implemented for sensitive operations
2. Test that tools respect permission boundaries
3. Confirm that minimal necessary scopes are requested during OAuth flow
4. Validate that scope violations are properly detected and blocked

## References
- [OAuth 2.0 Security Best Current Practice - Principle of Least Privilege](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics#section-4.15.1)
- [NIST SP 800-63B - Authentication and Lifecycle Management](https://pages.nist.gov/800-63-3/sp800-63b.html)
- [CWE-266: Incorrect Privilege Assignment](https://cwe.mitre.org/data/definitions/266.html)

## Status Tracking
- [x] Identified: 2026-02-02
- [x] Documented: 2026-02-02
- [ ] Reported to maintainers:
- [ ] Acknowledged by maintainers:
- [ ] Fix available:
- [ ] Fix verified:
- [ ] Closed:

## Auditor Notes
This finding addresses a common issue in OAuth implementations where convenience is prioritized over security. However, the extensive tool disabling capabilities significantly mitigate this concern by allowing users to implement principle of least privilege. The severity is low because users can effectively control the attack surface by disabling unused tools. The architectural pattern of providing granular controls is actually a security strength.