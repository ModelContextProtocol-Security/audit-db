# Finding: Error Information Disclosure

**Finding ID**: medium-002-error-information-disclosure  
**Severity**: Medium  
**Category**: Information Disclosure  
**CWE**: CWE-209 (Generation of Error Message Containing Sensitive Information)  
**CVSS Score**: 5.3 (Medium)

## Executive Summary
Error handling mechanisms return detailed error information to clients, potentially disclosing sensitive system information, internal implementation details, and reconnaissance data useful for attackers.

## Technical Description
The server's error handling implementation forwards detailed error information from the Notion API and internal systems directly to MCP clients without sanitization. This includes HTTP response details, internal error messages, and system information that could aid attackers in reconnaissance activities.

## Evidence
**Code Location**: `src/openapi-mcp-server/mcp/proxy.ts` lines 84-105

```typescript
} catch (error) {
  console.error('Error in tool call', error)
  if (error instanceof HttpClientError) {
    console.error('HttpClientError encountered, returning structured error', error)
    const data = error.data?.response?.data ?? error.data ?? {}
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            status: 'error', // TODO: get this from http status code?
            ...(typeof data === 'object' ? data : { data: data }),
          }),
        },
      ],
    }
  }
  throw error
}
```

**Additional Evidence**: HTTP Client error handling in `src/openapi-mcp-server/client/http-client.ts`:

```typescript
} catch (error: any) {
  if (error.response) {
    console.error('Error in http client', error)
    const headers = new Headers()
    // ... header processing ...
    throw new HttpClientError(
      error.response.statusText || 'Request failed', 
      error.response.status, 
      error.response.data,  // ← Full response data forwarded
      headers
    )
  }
  throw error
}
```

## Impact Assessment
- **Confidentiality**: Medium - Internal system information disclosure
- **Integrity**: Low - No direct integrity impact
- **Availability**: Low - Minimal availability impact
- **Exploitability**: High - Easily triggered through malformed requests
- **Scope**: Internal application details, API responses, system configuration

## Affected Components
- File: `src/openapi-mcp-server/mcp/proxy.ts` (lines 84-105)
- File: `src/openapi-mcp-server/client/http-client.ts` (error handling)
- Function: MCP tool call error handling
- All API interaction error responses

## Reproduction Steps
1. Trigger an API error (invalid authentication, malformed request)
2. Send MCP tool call with invalid parameters
3. Observe detailed error response including:
   - HTTP status codes and messages
   - Notion API error details
   - Internal stack traces (in development mode)
   - System file paths or configuration details

**Example Error Response**:
```json
{
  "content": [{
    "type": "text",
    "text": "{\"status\":\"error\",\"object\":\"error\",\"code\":\"unauthorized\",\"message\":\"API token is invalid.\",\"request_id\":\"12345-abcd-6789\"}"
  }]
}
```

## Risk Scenarios

**API Reconnaissance**:
- Attacker probes various endpoints with invalid requests
- Error messages reveal API structure and available endpoints
- Authentication mechanisms and requirements disclosed
- Rate limiting and security controls identified

**System Information Gathering**:
- Error messages reveal internal file paths
- Stack traces disclose application structure
- Configuration details leaked through error context
- Technology stack and version information exposed

**Notion Workspace Enumeration**:
- Invalid database/page ID errors reveal workspace structure
- Permission errors disclose access control mechanisms
- API quota and rate limiting information exposed
- User account and integration details leaked

## Recommendations

### Immediate Actions
- [ ] Implement error message sanitization before returning to clients
- [ ] Create generic error responses for production environments
- [ ] Remove detailed API responses from client-facing errors
- [ ] Add error classification and appropriate response mapping

### Short-term Improvements
- [ ] Implement configurable error verbosity levels
- [ ] Create secure logging for detailed errors (server-side only)
- [ ] Develop error response filtering based on client context
- [ ] Add rate limiting for error-generating requests

### Long-term Strategic Changes
- [ ] Develop comprehensive error handling framework
- [ ] Implement error response templates for different scenarios
- [ ] Add security-focused error monitoring and alerting
- [ ] Create error handling best practices documentation

## Remediation Examples

**Error Sanitization Implementation**:
```typescript
function sanitizeError(error: any, isProduction: boolean): any {
  if (isProduction) {
    // Return generic error in production
    return {
      status: 'error',
      message: 'An error occurred while processing the request',
      code: 'internal_error'
    };
  }
  
  // Development: limited error details
  return {
    status: 'error',
    message: error.message || 'Request failed',
    type: error.constructor.name
  };
}
```

**Error Classification System**:
```typescript
enum ErrorClass {
  CLIENT_ERROR = 'client_error',
  AUTH_ERROR = 'authentication_error', 
  PERMISSION_ERROR = 'permission_error',
  SYSTEM_ERROR = 'system_error'
}

function classifyAndSanitizeError(error: any): any {
  switch (error.status) {
    case 401:
      return { status: 'error', class: ErrorClass.AUTH_ERROR, message: 'Authentication required' };
    case 403:
      return { status: 'error', class: ErrorClass.PERMISSION_ERROR, message: 'Access denied' };
    default:
      return { status: 'error', class: ErrorClass.SYSTEM_ERROR, message: 'Request failed' };
  }
}
```

## Remediation Validation
**Testing Steps**:
1. Implement error sanitization logic
2. Test various error conditions (auth, validation, system errors)
3. Verify production mode returns generic errors
4. Confirm detailed errors only logged server-side
5. Test that legitimate error information (like validation feedback) still available

**Success Criteria**:
- Production errors provide minimal information disclosure
- Internal system details not exposed to clients
- Useful error information still available for legitimate debugging
- Security monitoring captures detailed error information

## References
- [OWASP: Information Exposure Through Error Messages](https://owasp.org/www-community/Improper_Error_Handling)
- [CWE-209: Generation of Error Message Containing Sensitive Information](https://cwe.mitre.org/data/definitions/209.html)
- [NIST SP 800-53: System and Information Integrity](https://csrc.nist.gov/Projects/risk-management/sp800-53-controls/release-search#!/control?version=5.1&number=SI-11)

## Status Tracking
- [x] Identified: 2025-08-07
- [x] Documented: 2025-08-07
- [ ] Reported to maintainers: 
- [ ] Acknowledged by maintainers:
- [ ] Fix available:
- [ ] Fix verified:
- [ ] Closed:

## Auditor Notes
This finding represents a common development pattern that poses moderate security risks. While detailed error information is valuable for development and debugging, production deployments should implement error sanitization to prevent information disclosure. The current implementation would be appropriate for development environments but requires hardening for production use.