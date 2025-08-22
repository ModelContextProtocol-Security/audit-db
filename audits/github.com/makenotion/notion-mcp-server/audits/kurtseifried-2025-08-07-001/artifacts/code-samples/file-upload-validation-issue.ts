// MEDIUM-001: File Upload Path Validation Issue
// File: src/openapi-mcp-server/client/http-client.ts (lines 42-65)

private async prepareFileUpload(operation: OpenAPIV3.OperationObject, params: Record<string, any>): Promise<FormData | null> {
  const fileParams = isFileUploadParameter(operation)
  if (fileParams.length === 0) return null

  const formData = new FormData()

  // Handle file uploads
  for (const param of fileParams) {
    const filePath = params[param]  // ← User-controlled file path
    if (!filePath) {
      throw new Error(`File path must be provided for parameter: ${param}`)
    }
    switch (typeof filePath) {
      case 'string':
        addFile(param, filePath)  // ← No path validation
        break
      case 'object':
        if(Array.isArray(filePath)) {
          let fileCount = 0
          for(const file of filePath) {
            addFile(param, file)  // ← No validation on array elements
            fileCount++
          }
          break
        }
        //deliberate fallthrough
      default:
        throw new Error(`Unsupported file type: ${typeof filePath}`)
    }
    
    function addFile(name: string, filePath: string) {
      try {
        const fileStream = fs.createReadStream(filePath)  // ← SECURITY ISSUE: Direct path usage
        formData.append(name, fileStream)
      } catch (error) {
        throw new Error(`Failed to read file at ${filePath}: ${error}`)
      }
    }
  }

  return formData
}

// SECURITY CONCERNS:
// 1. Path traversal attacks: ../../etc/passwd
// 2. Unauthorized file access: /home/user/.ssh/id_rsa
// 3. System file access: /proc/version, /etc/shadow
// 4. Information disclosure via error messages
// 5. No restriction to allowed directories

// POTENTIAL ATTACKS:
// - ../../../etc/passwd (Linux system files)
// - C:\\Windows\\System32\\config\\SAM (Windows system files)  
// - /proc/self/environ (process environment variables)
// - ~/.ssh/id_rsa (SSH private keys)
// - /var/log/auth.log (system logs)

// RECOMMENDED SECURE IMPLEMENTATION:

import path from 'path';

const ALLOWED_UPLOAD_DIRS = ['/tmp/mcp-uploads', './user-files'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

function validateAndSanitizeFilePath(filePath: string): string {
  // 1. Check for path traversal attempts
  if (filePath.includes('..') || filePath.includes('~')) {
    throw new Error('Invalid file path: path traversal detected');
  }
  
  // 2. Resolve the path
  const resolvedPath = path.resolve(filePath);
  
  // 3. Check if path is within allowed directories
  const isAllowed = ALLOWED_UPLOAD_DIRS.some(allowedDir => {
    const resolvedAllowed = path.resolve(allowedDir);
    return resolvedPath.startsWith(resolvedAllowed);
  });
  
  if (!isAllowed) {
    throw new Error('File path not in allowed directory');
  }
  
  // 4. Check file exists and get stats
  const stats = fs.statSync(resolvedPath);
  if (!stats.isFile()) {
    throw new Error('Path is not a regular file');
  }
  
  if (stats.size > MAX_FILE_SIZE) {
    throw new Error('File too large');
  }
  
  return resolvedPath;
}

function secureAddFile(name: string, filePath: string) {
  try {
    const safePath = validateAndSanitizeFilePath(filePath);
    const fileStream = fs.createReadStream(safePath);
    formData.append(name, fileStream);
  } catch (error) {
    // Sanitized error message - don't reveal file system details
    throw new Error(`File upload failed: ${error.message}`);
  }
}