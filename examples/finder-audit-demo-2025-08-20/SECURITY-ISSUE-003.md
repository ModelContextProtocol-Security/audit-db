# Security Issue #003: Container Running as Root User

## Issue Metadata
- **Issue ID:** SECURITY-003
- **Category:** Container Security / Privilege Escalation
- **Severity:** Medium
- **CWE:** CWE-250 (Execution with Unnecessary Privileges)
- **CVSS Score:** 4.8/10.0 (Medium)
- **AIVSS Score:** 5.3/10.0 (Medium)
- **Status:** Open
- **Found Date:** 2025-08-20

## Issue Description
The Docker container runs the MCP server process as the root user, violating the principle of least privilege. If the container or application is compromised, an attacker would have root privileges within the container, potentially enabling container escape or amplifying the impact of other vulnerabilities.

## Affected Code Location
**File:** `Dockerfile`
**Lines:** 1-33 (entire file - no non-root user specified)

```dockerfile
# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# ... dependency installation ...

# ⚠️ NO USER DIRECTIVE - DEFAULTS TO ROOT
# ⚠️ PROCESS RUNS WITH UID 0 (ROOT)

# Uses the transport protocol specified by TRANSPORT_PROTOCOL env var
CMD ["sh", "-c", "fastmcp run src/searxng_simple_mcp/server.py --transport ${TRANSPORT_PROTOCOL:-stdio}"]
# ⚠️ COMMAND EXECUTES AS ROOT USER
```

## Vulnerability Analysis

### Attack Vectors
1. **Container Escape:** Root privileges increase likelihood of successful container escape
2. **Privilege Amplification:** Any code execution vulnerability becomes more severe
3. **File System Compromise:** Root access allows modification of system files
4. **Process Manipulation:** Ability to interact with other container processes
5. **Resource Abuse:** Unlimited access to container resources

### Technical Details
- Process runs with UID 0 (root) and GID 0 (root)
- Full read/write access to container filesystem
- Ability to modify system configurations
- Access to privileged system calls
- No isolation from container runtime

## Risk Assessment by Usage Context

### Local Single-User MCP (Risk: Low - 2.1/10)
**Scenario:** User running MCP server locally for personal use
- ⚠️ **Limited Impact:** Local container with user-controlled environment
- ✅ **Contained Risk:** Limited to local machine compromise
- **Recommendation:** Best practice to fix, but lower priority

### Remote SSE-Enabled Multi-User (Risk: High - 7.2/10)  
**Scenario:** MCP server running remotely with SSE transport serving multiple users
- 🚨 **High Risk:** Remote container with network exposure
- 🚨 **Multi-User Impact:** Compromise affects multiple users
- 🚨 **Lateral Movement:** Potential for container escape to host
- **Recommendation:** Fix immediately before production deployment

### Enterprise/Production Deployment (Risk: Very High - 8.5/10)
**Scenario:** Production deployment in corporate environment
- 🚨 **Critical Risk:** Violates container security best practices
- 🚨 **Compliance Issues:** Fails security policy requirements
- 🚨 **Blast Radius:** Container escape could impact entire host
- **Recommendation:** Mandatory fix for production deployment

## CVSS 4.0 Scoring Breakdown

**Base Score Metrics:**
- **Attack Vector (AV):** Local (0.55) - Requires container access/compromise
- **Attack Complexity (AC):** Low (0.77) - Standard privilege escalation techniques
- **Privileges Required (PR):** High (0.27) - Requires initial container compromise
- **User Interaction (UI):** None (0.85) - Automated exploitation possible
- **Scope (S):** Changed (1.0) - Could affect container host
- **Confidentiality Impact (C):** High (0.56) - Full container filesystem access
- **Integrity Impact (I):** High (0.56) - Can modify system files
- **Availability Impact (A):** Medium (0.22) - Can disrupt container services

**CVSS Base Score:** 4.8/10.0 (Medium)

## AIVSS Factors (AI Considerations)

**AI-Specific Risk Factors:**
- **Persistent Agent Risk (PAR):** Medium (+0.3) - AI agents often run long-term processes
- **Tool Access Amplification (TAA):** Low (+0.1) - Limited additional tool access from root
- **Container Escape Impact (CEI):** Medium (+0.4) - AI workloads often in multi-tenant environments
- **Autonomous Operation Risk (AOR):** Low (+0.1) - Limited autonomous system interaction

**AIVSS Adjustment:** +0.5
**Final AIVSS Score:** 5.3/10.0 (Medium)

## Code Examples

### Current Vulnerable Implementation
```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# ... dependency installation steps ...

# ⚠️ NO USER DIRECTIVE - RUNS AS ROOT BY DEFAULT
CMD ["sh", "-c", "fastmcp run src/searxng_simple_mcp/server.py --transport ${TRANSPORT_PROTOCOL:-stdio}"]
```

### Recommended Secure Implementation

#### Option 1: Simple Non-Root User
```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Create non-root user early in build process
RUN groupadd -r searxng && useradd -r -g searxng -u 1000 searxng

# Install the project into `/app`
WORKDIR /app

# Install dependencies as root (required for system packages)
RUN --mount=type=cache,target=.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Add project source code
ADD . /app

# Install project
RUN --mount=type=cache,target=.cache/uv \
    uv sync --frozen --no-dev

# Change ownership of application directory to non-root user
RUN chown -R searxng:searxng /app

# Switch to non-root user
USER searxng

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run as non-root user
CMD ["sh", "-c", "fastmcp run src/searxng_simple_mcp/server.py --transport ${TRANSPORT_PROTOCOL:-stdio}"]
```

#### Option 2: Minimal User with Specific UID
```dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Create minimal non-root user with specific UID for security scanning
RUN adduser --system --no-create-home --uid 10000 --group searxng

# Install the project into `/app`
WORKDIR /app

# Install dependencies (as root)
RUN --mount=type=cache,target=.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Add project source and install
ADD . /app
RUN --mount=type=cache,target=.cache/uv \
    uv sync --frozen --no-dev && \
    chown -R searxng:searxng /app

# Switch to non-root user before CMD
USER 10000:10000

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
CMD ["sh", "-c", "fastmcp run src/searxng_simple_mcp/server.py --transport ${TRANSPORT_PROTOCOL:-stdio}"]
```

#### Option 3: Multi-Stage Build with Distroless Base
```dockerfile
# Build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app
RUN --mount=type=cache,target=.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

ADD . /app
RUN --mount=type=cache,target=.cache/uv \
    uv sync --frozen --no-dev

# Runtime stage with distroless (automatically non-root)
FROM gcr.io/distroless/python3-debian12

# Copy from builder stage
COPY --from=builder --chown=nonroot:nonroot /app /app
WORKDIR /app

# Distroless images run as non-root by default (UID 65532)
USER nonroot
ENV PATH="/app/.venv/bin:$PATH"
CMD ["/app/.venv/bin/python", "-m", "fastmcp", "run", "src/searxng_simple_mcp/server.py"]
```

## Remediation Recommendations

### Immediate (High Priority)
1. **Add Non-Root User to Dockerfile:**
   ```dockerfile
   # Add before CMD directive
   RUN groupadd -r searxng && useradd -r -g searxng searxng
   RUN chown -R searxng:searxng /app
   USER searxng
   ```

2. **Verify User Switch Works:**
   ```bash
   # Test that application still functions with non-root user
   docker build -t searxng-mcp-test .
   docker run --rm searxng-mcp-test whoami
   # Should output 'searxng' not 'root'
   ```

### Short-term (Medium Priority)
1. **Security Hardening:**
   ```dockerfile
   # Additional hardening measures
   RUN adduser --system --no-create-home --shell /bin/false searxng
   
   # Make filesystem read-only where possible
   RUN chmod -R a-w /app/src
   
   # Remove unnecessary packages
   RUN apt-get remove -y --purge apt-utils && apt-get autoremove -y
   ```

2. **Runtime Security Options:**
   ```bash
   # Run container with additional security options
   docker run \
     --read-only \
     --tmpfs /tmp:noexec,nosuid,size=100m \
     --user 1000:1000 \
     --cap-drop=ALL \
     searxng-mcp
   ```

### Long-term (Lower Priority)
1. **Distroless Base Images:**
   - Migrate to distroless base images for minimal attack surface
   - Automatic non-root execution
   - No shell or package manager

2. **Security Scanning Integration:**
   ```yaml
   # GitHub Actions security scanning
   - name: Run container security scan
     uses: aquasecurity/trivy-action@master
     with:
       image-ref: 'searxng-mcp:latest'
       format: 'sarif'
   ```

## Testing Verification

### Test Case 1: Verify Non-Root Execution
```bash
# Build and test container
docker build -t searxng-test .
docker run --rm searxng-test whoami
# Expected: searxng (or numeric UID, not root)

docker run --rm searxng-test id
# Expected: uid=1000(searxng) gid=1000(searxng) groups=1000(searxng)
```

### Test Case 2: Verify Application Functionality
```bash
# Test that the application still works
docker run --rm -e TRANSPORT_PROTOCOL=stdio searxng-test &
# Send MCP request to verify functionality
```

### Test Case 3: Security Verification
```bash
# Verify limited privileges
docker run --rm searxng-test touch /root/test 2>&1
# Expected: Permission denied

docker run --rm searxng-test cat /etc/shadow 2>&1  
# Expected: Permission denied
```

### Test Case 4: File Permissions
```python
def test_container_user():
    """Test that container runs as non-root user."""
    result = subprocess.run(
        ["docker", "run", "--rm", "searxng-test", "id", "-u"],
        capture_output=True,
        text=True
    )
    uid = int(result.stdout.strip())
    assert uid != 0, "Container should not run as root (UID 0)"
    assert uid >= 1000, "Container should use non-system UID"
```

## Detection and Monitoring

### Container Runtime Detection
```bash
# Check running container user
docker exec <container_id> whoami

# Inspect container security context
docker inspect <container_id> | jq '.[0].Config.User'
```

### Security Scanning
```bash
# Use tools like Trivy to detect root execution
trivy image --severity HIGH,CRITICAL searxng-mcp:latest

# Use Docker Bench Security
docker run --rm --privileged \
  -v /var/run/docker.sock:/var/run/docker.sock \
  docker/docker-bench-security
```

### Kubernetes Security Policies
```yaml
# Pod Security Policy to enforce non-root
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
spec:
  runAsUser:
    rule: MustRunAsNonRoot
  runAsGroup:
    rule: MustRunAs
    ranges:
      - min: 1000
        max: 65535
```

## References
- **CWE-250:** Execution with Unnecessary Privileges - https://cwe.mitre.org/data/definitions/250.html
- **Docker Security Best Practices:** https://docs.docker.com/develop/security-best-practices/
- **NIST Container Security Guide:** https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf
- **Distroless Images:** https://github.com/GoogleContainerTools/distroless