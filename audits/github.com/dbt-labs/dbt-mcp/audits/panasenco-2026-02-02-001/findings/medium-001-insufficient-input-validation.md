# Finding: Insufficient Input Validation and Information Disclosure

**Finding ID**: medium-002-insufficient-input-validation
**Severity**: Medium
**Category**: Input Validation & Information Disclosure
**CWE**: CWE-20 (Improper Input Validation), CWE-209 (Information Exposure Through Error Messages)
**CVSS Score**: 5.8

## Executive Summary
Some tool parameters lack comprehensive validation, and detailed error messages may expose system internals. The combination of these issues could enable a compromised AI agent to probe system boundaries and potentially circumvent granular access controls through information gathered from validation failures.

## Technical Description
While the dbt-mcp server implements type checking through pydantic models, there are gaps in comprehensive input validation for certain parameters, particularly those passed to external systems. Additionally, error messages may expose system internals such as file paths, configuration details, and system architecture information.

In an MCP threat model where AI agents may be compromised through prompt injection or data poisoning, the combination of insufficient input validation and detailed error responses could enable a malicious agent to probe system boundaries and gather intelligence to circumvent intended access controls.

## Evidence
Analysis reveals two interconnected issues:

### Input Validation Gaps
1. **Tool Parameter Definitions**: Basic type checking but limited content validation
2. **Command Construction**: Parameters may be passed to external systems without sufficient sanitization
3. **Dynamic Parameter Handling**: Some tools accept flexible parameter structures

### Information Disclosure in Errors
From configuration validation (settings.py):
```python
# Validation errors that expose system internals:
raise ValueError(f"{field_name} directory does not exist: {v}")
raise ValueError(f"{field_name} path does not exist: {v}")
```

**Combined Risk Scenario**: A compromised AI agent could:
```python
# 1. Probe with invalid inputs to gather system information
tool_call(file_path="../../../../etc/passwd")  # Error reveals path structure
tool_call(file_path="/nonexistent/config")     # Error reveals expected locations

# 2. Use gathered intelligence to craft more sophisticated attacks
# that might bypass intended tool restrictions
```

## Impact Assessment
- **Confidentiality**: Medium - System reconnaissance through error messages could expose architecture details
- **Integrity**: Medium - Compromised AI agent could potentially find ways around access controls
- **Availability**: Medium - Malformed inputs could cause service disruption
- **Exploitability**: Medium - Requires AI agent compromise but provides systematic probing capabilities
- **Scope**: All tools that accept parameters, especially when combined with detailed error responses

## Affected Components
- Tool parameter processing throughout the application
- dbt CLI command construction
- API parameter handling
- GraphQL query parameter processing
- File path and resource name handling

## Reproduction Steps
1. Identify tools that accept user-controlled string parameters
2. Attempt to provide malformed inputs (special characters, SQL injection patterns, command injection patterns)
3. Observe how these inputs are processed and passed to downstream systems
4. Check if any validation errors or security issues occur

**Expected**: Comprehensive input validation with rejection of malicious patterns
**Actual**: Basic type checking but potentially insufficient content validation

## Risk Scenarios

### Primary Threat: Compromised AI Agent Reconnaissance
1. **System Probing**: Compromised AI agent systematically probes with invalid inputs to map system architecture through error responses
2. **Access Control Bypass Discovery**: Agent uses gathered intelligence to find creative ways around tool restrictions
3. **Privilege Escalation**: Agent leverages detailed error information to identify misconfigurations or unintended access paths

### Secondary Threats
1. **Command Injection**: Malicious parameters passed to dbt CLI could execute unintended commands
2. **SQL Injection**: Crafted inputs in SQL tools could manipulate database queries
3. **Path Traversal**: File path parameters combined with error disclosure could reveal unauthorized file access methods
4. **DoS via Input Manipulation**: Specially crafted inputs could cause application crashes

## Recommendations

### Immediate Actions (Defense Against Compromised AI Agents)
- [ ] Implement input validation for all tool parameters with strict content validation
- [ ] Sanitize error messages to remove system paths, configuration details, and architecture information
- [ ] Add generic error responses for validation failures while logging details separately
- [ ] Implement rate limiting for validation failures to prevent systematic probing

### Short-term Improvements
- [ ] Develop comprehensive parameter validation schemas with allowlist-based validation
- [ ] Implement error code system instead of descriptive messages for user-facing responses
- [ ] Add parameter encoding/escaping for external system calls
- [ ] Create separate logging channels for detailed errors vs user-visible responses

### Long-term Strategic Changes
- [ ] Implement a centralized input validation framework
- [ ] Add automated testing for input validation scenarios
- [ ] Implement runtime parameter monitoring and alerting
- [ ] Add parameter validation documentation and guidelines

## Remediation Validation
1. Test all tools with various malformed input patterns
2. Verify that malicious inputs are properly rejected
3. Confirm that valid inputs continue to work correctly
4. Test error handling for validation failures

## References
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [CWE-20: Improper Input Validation](https://cwe.mitre.org/data/definitions/20.html)
- [OWASP Command Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html)

## Status Tracking
- [x] Identified: 2026-02-02
- [x] Documented: 2026-02-02
- [ ] Reported to maintainers:
- [ ] Acknowledged by maintainers:
- [ ] Fix available:
- [ ] Fix verified:
- [ ] Closed:

## Auditor Notes
This finding addresses the MCP-specific threat model where AI agents may be compromised through prompt injection or data poisoning. The combination of insufficient input validation and detailed error responses creates a systematic reconnaissance capability for malicious agents. The medium severity reflects the defense-in-depth principle - even with granular access controls, minimizing information disclosure and hardening input validation provides critical protection against compromised AI agents attempting to circumvent intended constraints.