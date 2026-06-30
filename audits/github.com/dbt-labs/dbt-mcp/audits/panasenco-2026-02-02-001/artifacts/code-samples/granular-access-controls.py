# Code Sample: Comprehensive Granular Access Controls
# Files: src/dbt_mcp/config/settings.py and config.py
# Security Strength: Excellent implementation of access controls

# TOOLSET-LEVEL CONTROLS
# Environment variables for disabling entire toolsets
class DbtMcpSettings(BaseSettings):
    # Disable tool settings
    disable_dbt_cli: bool = Field(False, alias="DISABLE_DBT_CLI")
    disable_dbt_codegen: bool = Field(True, alias="DISABLE_DBT_CODEGEN")
    disable_semantic_layer: bool = Field(False, alias="DISABLE_SEMANTIC_LAYER")
    disable_discovery: bool = Field(False, alias="DISABLE_DISCOVERY")
    disable_admin_api: bool = Field(False, alias="DISABLE_ADMIN_API")
    disable_sql: bool | None = Field(None, alias="DISABLE_SQL")
    disable_lsp: bool | None = Field(None, alias="DISABLE_LSP")

    # Individual tool controls
    disable_tools: list[ToolName] | None = Field(None, alias="DISABLE_TOOLS")
    enable_tools: list[ToolName] | None = Field(None, alias="DBT_MCP_ENABLE_TOOLS")

# AUTOMATIC SAFETY CONTROLS
@model_validator(mode="after")
def auto_disable(self) -> "DbtMcpSettings":
    """Auto-disable features based on required settings."""
    # Platform features
    if not self.actual_host:
        # Automatically disable platform features when host is missing
        object.__setattr__(self, "disable_semantic_layer", True)
        object.__setattr__(self, "disable_discovery", True)
        object.__setattr__(self, "disable_admin_api", True)
        object.__setattr__(self, "disable_sql", True)

    # CLI features
    cli_errors = validate_dbt_cli_settings(self)
    if cli_errors:
        # Automatically disable CLI features when configuration is invalid
        object.__setattr__(self, "disable_dbt_cli", True)
        object.__setattr__(self, "disable_dbt_codegen", True)
    return self

# TOOLSET MAPPING CONFIGURATION
TOOLSET_TO_DISABLE_ATTR = {
    Toolset.SEMANTIC_LAYER: "disable_semantic_layer",
    Toolset.ADMIN_API: "disable_admin_api",
    Toolset.DBT_CLI: "disable_dbt_cli",
    Toolset.DBT_CODEGEN: "disable_dbt_codegen",
    Toolset.DISCOVERY: "disable_discovery",
    Toolset.DBT_LSP: "disable_lsp",
    Toolset.SQL: "actual_disable_sql",
    Toolset.MCP_SERVER_METADATA: "disable_mcp_server_metadata",
}

# USAGE EXAMPLES:
# High-security production (only read-only tools):
# export DBT_MCP_ENABLE_TOOLS="get_all_models,get_model_details,get_lineage"

# Development environment (disable dangerous operations):
# export DISABLE_TOOLS="execute_sql,trigger_job_run,cancel_job_run"

# Analytics-only deployment:
# export DISABLE_DBT_CLI=true
# export DISABLE_ADMIN_API=true
# export DISABLE_SQL=true

# SECURITY STRENGTHS:
# 1. Multiple control granularities (toolset and individual tools)
# 2. Both allowlist (enable_tools) and blocklist (disable_tools) approaches
# 3. Automatic safety controls when configuration is incomplete
# 4. Environment-specific configuration support
# 5. Fail-safe defaults with comprehensive validation
# 6. Clear separation between tool categories