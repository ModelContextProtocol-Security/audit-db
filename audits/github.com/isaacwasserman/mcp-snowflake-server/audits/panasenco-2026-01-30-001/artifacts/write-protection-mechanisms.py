# Write Protection Mechanisms in MCP Snowflake Server
# Extracted from isaacwasserman/mcp-snowflake-server v0.4.0
# Demonstrates multi-layered approach to preventing AI agent write access

# =============================================================================
# LAYER 1: Argument Parsing - Secure Defaults
# =============================================================================
# File: src/mcp_snowflake_server/__init__.py, lines 54-56

def parse_args():
    parser = argparse.ArgumentParser()

    # KEY SECURITY FEATURE: Write operations disabled by default
    parser.add_argument(
        "--allow_write",
        required=False,
        default=False,           # <-- SECURE DEFAULT
        action="store_true",
        help="Allow write operations on the database"
    )
    # ... other arguments


# =============================================================================
# LAYER 2: Write Query Handler - Explicit Permission Check
# =============================================================================
# File: src/mcp_snowflake_server/server.py, lines 267-274

async def handle_write_query(arguments, db, _, allow_write, __, **___):
    # SECURITY CHECK: Explicit write permission validation
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")

    # Additional validation to prevent SELECT in write tool
    if arguments["query"].strip().upper().startswith("SELECT"):
        raise ValueError("SELECT queries are not allowed for write_query")

    results, data_id = await db.execute_query(arguments["query"])
    return [types.TextContent(type="text", text=str(results))]


# =============================================================================
# LAYER 3: Create Table Handler - Same Protection Pattern
# =============================================================================
# File: src/mcp_snowflake_server/server.py, lines 277-284

async def handle_create_table(arguments, db, _, allow_write, __, **___):
    # SECURITY CHECK: Same explicit permission model
    if not allow_write:
        raise ValueError("Write operations are not allowed for this data connection")

    # Additional validation for CREATE TABLE only
    if not arguments["query"].strip().upper().startswith("CREATE TABLE"):
        raise ValueError("Only CREATE TABLE statements are allowed")

    results, data_id = await db.execute_query(arguments["query"])
    return [types.TextContent(type="text", text=f"Table created successfully. data_id = {data_id}")]


# =============================================================================
# LAYER 4: SQL Write Detection - Defense in Depth
# =============================================================================
# File: src/mcp_snowflake_server/server.py, lines 229-256
# File: src/mcp_snowflake_server/write_detector.py

async def handle_read_query(arguments, db, write_detector, *_, exclude_json_results=False):
    if not arguments or "query" not in arguments:
        raise ValueError("Missing query argument")

    # SECURITY CHECK: Prevent write operations in read tool
    # This protects against agent confusion or manipulation
    if write_detector.analyze_query(arguments["query"])["contains_write"]:
        raise ValueError("Calls to read_query should not contain write operations")

    data, data_id = await db.execute_query(arguments["query"])
    # ... return results

# The SQLWriteDetector class implementation:
class SQLWriteDetector:
    def __init__(self):
        # Define comprehensive write operation keywords
        self.dml_write_keywords = {"INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT", "REPLACE"}
        self.ddl_keywords = {"CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME"}
        self.dcl_keywords = {"GRANT", "REVOKE"}
        self.write_keywords = self.dml_write_keywords | self.ddl_keywords | self.dcl_keywords

    def analyze_query(self, sql_query: str) -> dict:
        """Sophisticated SQL analysis that even detects writes in CTEs"""
        parsed = sqlparse.parse(sql_query)
        found_operations = set()
        has_cte_write = False

        for statement in parsed:
            # Check for write operations in CTEs (WITH clauses)
            if self._has_cte(statement):
                cte_write = self._analyze_cte(statement)
                if cte_write:
                    has_cte_write = True
                    found_operations.add("CTE_WRITE")

            # Analyze the main query
            operations = self._find_write_operations(statement)
            found_operations.update(operations)

        return {
            "contains_write": bool(found_operations) or has_cte_write,
            "write_operations": found_operations,
            "has_cte_write": has_cte_write,
        }


# =============================================================================
# LAYER 5: Tool Filtering - Runtime Security Enforcement
# =============================================================================
# File: src/mcp_snowflake_server/server.py, lines 485-492

async def main(allow_write: bool = False, ...):
    # Define all tools with security tags
    all_tools = [
        Tool(name="read_query", ...),           # No security tags - always allowed
        Tool(name="list_databases", ...),      # No security tags - always allowed
        Tool(name="write_query", ..., tags=["write"]),      # Tagged as write operation
        Tool(name="create_table", ..., tags=["write"]),     # Tagged as write operation
    ]

    # SECURITY ENFORCEMENT: Filter out write tools when not explicitly allowed
    exclude_tags = []
    if not allow_write:
        exclude_tags.append("write")    # <-- KEY SECURITY DECISION

    allowed_tools = [
        tool for tool in all_tools
        if tool.name not in exclude_tools and
           not any(tag in exclude_tags for tag in tool.tags)  # <-- RUNTIME FILTERING
    ]

    logger.info("Allowed tools: %s", [tool.name for tool in allowed_tools])


# =============================================================================
# SECURITY ANALYSIS SUMMARY
# =============================================================================

"""
MULTI-LAYERED WRITE PROTECTION:

1. SECURE DEFAULTS (Layer 1):
   - --allow_write defaults to False
   - Requires explicit user consent for dangerous operations

2. HANDLER-LEVEL PROTECTION (Layers 2 & 3):
   - Every write handler explicitly checks allow_write flag
   - Immediate rejection if not authorized
   - Additional input validation per operation type

3. CROSS-TOOL PROTECTION (Layer 4):
   - SQLWriteDetector prevents write operations in read tools
   - Sophisticated parsing handles complex SQL including CTEs
   - Protects against agent confusion or manipulation

4. RUNTIME ENFORCEMENT (Layer 5):
   - Write tools completely unavailable when write=False
   - Tool registration filtered based on security tags
   - Agent cannot even attempt to call unavailable tools

5. FAIL-SAFE DESIGN:
   - System fails to secure state (no writes) by default
   - Multiple independent checks must all fail for security bypass
   - Clear error messages help legitimate users understand restrictions

WHY THIS IS EXCELLENT FOR AI AGENTS:
- Prevents hallucinated DELETE operations from causing damage
- Stops manipulated agents from modifying data accidentally
- Creates safe exploration environment for AI agent learning
- Requires explicit human consent (--allow_write) for dangerous operations
- Multiple layers ensure single point of failure doesn't compromise security

THREAT MODEL ALIGNMENT:
✅ Protects against AI agent hallucinations
✅ Prevents prompt injection leading to data modification
✅ Stops confused deputy write operations
✅ Limits blast radius of compromised agents
✅ Maintains usability for legitimate read operations
"""