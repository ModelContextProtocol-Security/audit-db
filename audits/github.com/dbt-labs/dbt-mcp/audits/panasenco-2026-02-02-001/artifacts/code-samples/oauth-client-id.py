# Code Sample: Hardcoded OAuth Client ID - Configuration Management Issue
# File: src/dbt_mcp/oauth/client_id.py
# Configuration Issue: LOW-003 - Hardcoded OAuth Client ID

OAUTH_CLIENT_ID = "34ec61e834cdffd9dd90a32231937821"

# CONFIGURATION CONCERN (NOT SECURITY):
# Per OAuth 2.0 RFC 6749 Section 2.1: "The client identifier is not a secret;
# it is exposed to the resource owner and MUST NOT be used alone for client authentication."
#
# However, hardcoding limits operational flexibility:
# 1. Prevents environment-specific client IDs (dev/staging/prod)
# 2. Makes client ID changes require code modifications
# 3. Complicates multi-tenant deployments
# 4. Reduces configuration flexibility

# RECOMMENDED APPROACH FOR OPERATIONAL FLEXIBILITY:
# import os
# OAUTH_CLIENT_ID = os.environ.get("DBT_OAUTH_CLIENT_ID", "34ec61e834cdffd9dd90a32231937821")
# # Provides default for backward compatibility while enabling configuration flexibility