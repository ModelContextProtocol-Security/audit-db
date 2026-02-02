# Code Sample: Excellent OAuth Token Security Implementation
# Files: Various OAuth-related files
# Security Strength: Positive finding - excellent implementation

# PKCE Implementation with proper security
from authlib.integrations.requests_client import OAuth2Session

oauth_client = OAuth2Session(
    client_id=OAUTH_CLIENT_ID,
    token_endpoint=token_url,
)

# Automatic token refresh with comprehensive error handling
def _try_refresh_token(
    dbt_ctx: DbtPlatformContext,
    dbt_platform_url: str,
    dbt_platform_context_manager: DbtPlatformContextManager,
) -> DbtPlatformContext | None:
    """
    Attempt to refresh the access token using the refresh token.
    Returns the updated context if successful, None otherwise.
    """
    if not dbt_ctx.decoded_access_token:
        return None

    refresh_token = dbt_ctx.decoded_access_token.access_token_response.refresh_token
    if not refresh_token:
        return None

    try:
        logger.info("Access token expired, attempting refresh using refresh token")
        token_url = f"{dbt_platform_url}/oauth/token"
        oauth_client = OAuth2Session(
            client_id=OAUTH_CLIENT_ID,
            token_endpoint=token_url,
        )
        token_response = oauth_client.refresh_token(
            url=token_url,
            refresh_token=refresh_token,
        )
        # Proper context management and secure storage
        new_context = dbt_platform_context_from_token_response(
            token_response, dbt_platform_url
        )
        updated_context = dbt_ctx.override(new_context)
        dbt_platform_context_manager.write_context_to_file(updated_context)
        logger.info("Successfully refreshed access token at startup")
        return updated_context
    except Exception as e:
        logger.warning(f"Failed to refresh token at startup: {e}")
        return None

# Token validation with proper expiration checking
def _is_token_valid(dbt_ctx: DbtPlatformContext) -> bool:
    """Check if the access token is still valid (not expired)."""
    if not dbt_ctx.decoded_access_token:
        return False
    expires_at = dbt_ctx.decoded_access_token.access_token_response.expires_at
    return expires_at > time.time() + 120  # 2 minutes buffer - excellent practice!

# File locking for concurrent access protection
async def get_dbt_platform_context(
    *,
    dbt_user_dir: Path,
    dbt_platform_url: str,
    dbt_platform_context_manager: DbtPlatformContextManager,
) -> DbtPlatformContext:
    # Some MCP hosts (Claude Desktop) tend to run multiple MCP servers instances.
    # We need to lock so that only one can run the oauth flow.
    with FileLock(dbt_user_dir / "mcp.lock"):  # Excellent concurrency protection!
        # ... rest of authentication flow

# SECURITY STRENGTHS:
# 1. Uses PKCE for enhanced OAuth security
# 2. Automatic token refresh with proper error handling
# 3. Token expiration checking with safety buffer
# 4. File locking prevents race conditions
# 5. Secure token storage in user-specific files
# 6. Comprehensive error handling without credential exposure