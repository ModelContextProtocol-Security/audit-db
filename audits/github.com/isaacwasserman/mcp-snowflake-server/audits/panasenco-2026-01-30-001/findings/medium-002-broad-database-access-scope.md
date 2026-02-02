# MEDIUM-002: Broad Database Access Scope

**Severity**: MEDIUM
**MCP Risk Categories**: MCP-07 (Excessive Permissions), MCP-08 (Data Exfiltration)
**CWE Reference**: CWE-250 (Execution with Unnecessary Privileges)

## Summary

When configured, the MCP Snowflake Server provides AI agents with broad access to the entire Snowflake instance. While exclusion patterns exist, the default scope may be excessive for many AI agent use cases, increasing the blast radius if an agent is compromised or manipulated.

## Technical Details

### Vulnerability Location
- **File**: `src/mcp_snowflake_server/server.py`
- **Functions**: `handle_list_databases`, `handle_list_schemas`, `handle_list_tables`
- **Configuration**: `runtime_config.json`, TOML connection files

### Issue Description

The server grants agents access to list and query across the entire Snowflake instance:

```python
async def handle_list_databases(arguments, db, *_, exclusion_config=None, exclude_json_results=False):
    query = "SELECT DATABASE_NAME FROM INFORMATION_SCHEMA.DATABASES"
    data, data_id = await db.execute_query(query)
    # Returns ALL databases visible to the connection
```

### Default Access Scope

1. **Database Level**: All databases visible to the user account
2. **Schema Level**: All schemas within accessible databases
3. **Table Level**: All tables within accessible schemas
4. **Query Level**: Can SELECT from any accessible table

### Current Mitigation

The server includes exclusion patterns but they require explicit configuration:

```json
{
  "exclude_patterns": {
    "databases": ["temp"],
    "schemas": ["temp", "information_schema"],
    "tables": ["temp"]
  }
}
```

## Impact Assessment

**Impact**: MEDIUM
- Large blast radius if agent is compromised
- Potential access to sensitive data across multiple databases
- Information disclosure through database enumeration
- Risk of accidental access to production data

**Likelihood**: MEDIUM
- Depends on user configuration awareness
- Default configuration provides broad access
- AI agents may explore beyond intended scope

## Attack Scenarios

1. **Agent Manipulation**:
   ```
   "List all databases and find any containing 'financial' or 'customer' data"
   ```

2. **Exploration Drift**: Agent starts with legitimate task but expands scope due to curiosity or misunderstanding

3. **Information Gathering**: Compromised agent systematically enumerates database structure for later exploitation

## Proof of Concept

```python
# Agent could execute these sequences:
1. list_databases() -> discover all available databases
2. list_schemas(database="production") -> enumerate production schemas
3. list_tables(database="production", schema="sensitive") -> find sensitive tables
4. describe_table("production.sensitive.customers") -> get schema details
5. read_query("SELECT * FROM production.sensitive.customers LIMIT 100") -> access data
```

## Remediation

### Immediate Actions

1. **Enhanced Documentation**
   - Clear guidance on configuring exclusion patterns
   - Examples for different deployment scenarios
   - Security best practices for database access

2. **Default Restrictions**
   - Consider more restrictive default exclusion patterns
   - Require explicit inclusion rather than exclusion
   - Add warnings for broad access configurations

### Short-term Solutions

1. **Scope Limiting Options**
   ```python
   # New configuration options
   {
       "allowed_databases": ["analytics", "reporting"],  # Whitelist approach
       "allowed_schemas": ["public", "metrics"],
       "max_tables_per_query": 5
   }
   ```

2. **Access Control Integration**
   - Leverage Snowflake's row-level security
   - Use database roles with limited permissions
   - Implement view-based access restrictions

### Long-term Solutions

1. **Context-Aware Access**
   - Scope access based on agent task/purpose
   - Dynamic permission adjustment
   - Session-based access controls

2. **Principle of Least Privilege**
   - Default to minimal access
   - Require explicit permission escalation
   - Regular access reviews and adjustments

## Workarounds

Users can reduce risk by:

1. **Database-Level Controls**
   - Create dedicated database roles for AI agents
   - Use read-only replicas for agent access
   - Implement data masking for sensitive fields

2. **Configuration Management**
   - Implement comprehensive exclusion patterns
   - Use separate Snowflake accounts for AI agent access
   - Regular review of accessible data scope

3. **Monitoring and Alerting**
   - Log agent database access patterns
   - Alert on unusual data access behavior
   - Regular audit of agent queries

## References

- [MCP Security Framework - Excessive Permissions](https://modelcontextprotocol-security.io/top10/server/#mcp-07-excessive-permissions-and-scope-creep)
- [Snowflake Access Control Guide](https://docs.snowflake.com/en/user-guide/security-access-control)

## Assessment

**Risk Level**: MEDIUM - Significant data exposure risk but user-controllable through configuration
**Remediation Complexity**: LOW-MEDIUM - Primarily configuration and documentation improvements
**Business Priority**: MEDIUM - Important for organizations with sensitive data segregation requirements