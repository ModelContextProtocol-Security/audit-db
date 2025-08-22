# Finding: Dynamic Parameter Handling Risk

**Finding ID**: medium-003-dynamic-parameter-handling  
**Severity**: Medium  
**Category**: Input Validation  
**CWE**: CWE-20 (Improper Input Validation)  
**CVSS Score**: 5.9 (Medium)

## Executive Summary
The server dynamically converts OpenAPI specifications to MCP tools and passes user input directly to HTTP operations without comprehensive validation, creating potential injection and manipulation risks.

## Technical Description
The system uses OpenAPI specifications to automatically generate MCP tool definitions and then passes user-provided parameters directly to HTTP operations. This dynamic approach, while powerful, creates potential security risks when user input is not sufficiently validated against the expected parameter types and constraints.

## Evidence
**Code Location**: `src/openapi-mcp-server/mcp/proxy.ts` lines 69-82

```typescript
// Handle tool calling
this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: params } = request.params

  // Find the operation in OpenAPI spec
  const operation = this.findOperation(name)
  if (!operation) {
    throw new Error(`Method ${name} not found`)
  }

  try {
    // Execute the operation - direct parameter passing
    const response = await this.httpClient.executeOperation(operation, params)
    // ...
  } catch (error) {
    // ...
  }
})
```

**HTTP Client Parameter Processing**: `src/openapi-mcp-server/client/http-client.ts` lines 88-122

```typescript
// Separate parameters based on their location
const urlParameters: Record<string, any> = {}
const bodyParams: Record<string, any> = formData || { ...params }

// Extract path and query parameters based on operation definition
if (operation.parameters) {
  for (const param of operation.parameters) {
    if ('name' in param && param.name && param.in) {
      if (param.in === 'path' || param.in === 'query') {
        if (params[param.name] !== undefined) {
          urlParameters[param.name] = params[param.name]  // Direct assignment
          if (!formData) {
            delete bodyParams[param.name]
          }
        }
      }
    }
  }
}
```

## Impact Assessment
- **Confidentiality**: Medium - Potential for unintended data access
- **Integrity**: Medium - Risk of data manipulation through parameter injection
- **Availability**: Low - DoS potential through malformed parameters
- **Exploitability**: Low - Requires understanding of OpenAPI spec structure
- **Scope**: All dynamically generated MCP tools and their parameters

## Affected Components
- File: `src/openapi-mcp-server/mcp/proxy.ts` (tool execution logic)
- File: `src/openapi-mcp-server/client/http-client.ts` (parameter processing)
- File: `src/openapi-mcp-server/openapi/parser.ts` (schema conversion)
- All automatically generated MCP tools from OpenAPI specifications

## Reproduction Steps
1. Examine generated MCP tools from Notion OpenAPI spec
2. Identify tools with complex parameter structures (nested objects, arrays)
3. Craft malicious parameter values:
   - SQL-like injection strings in text fields
   - Large integers for DoS attempts
   - Nested object manipulation
   - Array parameter manipulation
4. Execute MCP tool calls with crafted parameters
5. Observe parameter processing and forwarding to Notion API

## Risk Scenarios

**Parameter Injection**:
- Attacker provides unexpected parameter types or structures
- JSON injection in string parameters that get parsed
- Integer overflow in numeric parameters
- Array manipulation to cause processing errors

**OpenAPI Schema Bypass**:
- Parameters not properly validated against OpenAPI schema constraints
- Required parameter validation bypassed through undefined/null values
- Type coercion vulnerabilities in parameter processing
- Format validation bypass (email, UUID, etc.)

**Notion API Abuse**:
- Crafted parameters cause unintended Notion API behavior
- Bulk operation abuse through array parameter manipulation
- Resource exhaustion through large parameter payloads
- API rate limit bypass through parameter manipulation

## Recommendations

### Immediate Actions
- [ ] Implement parameter validation against OpenAPI schema constraints
- [ ] Add type checking and sanitization for all user inputs
- [ ] Validate required parameters and parameter formats
- [ ] Add size limits for arrays and string parameters

### Short-term Improvements
- [ ] Implement comprehensive input sanitization framework
- [ ] Add parameter logging for security monitoring
- [ ] Create parameter validation unit tests
- [ ] Implement rate limiting based on parameter complexity

### Long-term Strategic Changes
- [ ] Develop security-focused OpenAPI schema validation
- [ ] Implement parameter fuzzing in testing pipeline
- [ ] Add runtime parameter monitoring and anomaly detection
- [ ] Create secure parameter handling best practices guide

## Remediation Examples

**Parameter Validation Implementation**:
```typescript
import Ajv from 'ajv';

class ParameterValidator {
  private ajv: Ajv;
  
  constructor() {
    this.ajv = new Ajv({ 
      strict: true, 
      removeAdditional: true,
      coerceTypes: false 
    });
  }
  
  validateParameters(operation: OpenAPIV3.OperationObject, params: any): any {
    const schema = this.buildValidationSchema(operation);
    const validate = this.ajv.compile(schema);
    
    if (!validate(params)) {
      throw new Error(`Parameter validation failed: ${this.ajv.errorsText(validate.errors)}`);
    }
    
    return params; // Sanitized parameters
  }
  
  private buildValidationSchema(operation: OpenAPIV3.OperationObject) {
    // Convert OpenAPI parameter definitions to JSON Schema
    // with proper type validation, format checking, etc.
  }
}
```

**Input Sanitization**:
```typescript
function sanitizeParameter(value: any, parameterSchema: any): any {
  // Type validation
  if (parameterSchema.type === 'string' && typeof value !== 'string') {
    throw new Error('Invalid parameter type');
  }
  
  // Size limits
  if (parameterSchema.type === 'string' && value.length > 1000) {
    throw new Error('Parameter too long');
  }
  
  // Format validation
  if (parameterSchema.format === 'uuid' && !isValidUUID(value)) {
    throw new Error('Invalid UUID format');
  }
  
  return value;
}
```

## Remediation Validation
**Testing Steps**:
1. Implement parameter validation logic
2. Test with legitimate parameters - should pass validation
3. Test with malicious parameters - should be rejected
4. Verify error messages don't expose internal details
5. Performance test validation with complex parameter structures

**Success Criteria**:
- All parameters validated against OpenAPI schema constraints
- Malicious parameter injection attempts blocked
- Performance impact of validation is acceptable
- Error handling provides appropriate feedback without information disclosure

## References
- [OWASP: Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [CWE-20: Improper Input Validation](https://cwe.mitre.org/data/definitions/20.html)
- [OpenAPI 3.1 Specification: Parameter Objects](https://spec.openapis.org/oas/v3.1.0#parameter-object)

## Status Tracking
- [x] Identified: 2025-08-07
- [x] Documented: 2025-08-07
- [ ] Reported to maintainers: 
- [ ] Acknowledged by maintainers:
- [ ] Fix available:
- [ ] Fix verified:
- [ ] Closed:

## Auditor Notes
This finding represents an architectural security consideration rather than a traditional vulnerability. The dynamic parameter handling approach is powerful and enables the flexibility of the OpenAPI-to-MCP conversion, but it requires careful implementation of validation and sanitization to prevent security issues. The current implementation relies heavily on the OpenAPI specification for parameter constraints, which may not be sufficient for security-critical deployments.