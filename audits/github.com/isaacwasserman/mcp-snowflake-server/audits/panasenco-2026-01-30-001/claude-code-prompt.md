This is the relevant section of the prompt used to generate this audit.

---

The four pillars of the audit are safety, security, usability, and structure.

### Safety
When misuse of AI makes the news, it's often because the AI agent did something it wasn't supposed to.
Good MCP tools put in protections that allow the user to restrict the AI's actions.
Evaluate whether such protections are in place and how solid they are.

### Security
Study the skill reference document [mcp-server-top-10-risks.md](references/mcp-server-top-10-risks.md) to understand
real risks to focus the audit on.

### Usability
The safest and most secure tool is one you don't use at all.
Unfortunately we do have to use tools to achieve our goals.
Rather than giving a hard no recommendation in your audit, look for ways to say yes.
Are there any security measures, protections, or mitigations that will make the MCP server acceptable to use?

### Structure
The audit database is most useful when each audit conforms to the same structure.
Each audit should be parseable by humans, AI, and scripts.

Read the file `repos/external/audit-db/README.md`.
Study the reference audit in `repos/external/audit-db/audits/github.com/makenotion/notion-mcp-server`.

## !!! IMPORTANT !!! ##
- The user is not an adversary!
  These MCP servers run locally with the user's own credentials.
  There is no need to be concerned with user privilege escalation.
  There is no need to be worried about the user injecting malicious things into configuration files.
  If an attacker compromises the user's machine, they can just get the credentials directly, they don't need to
  compromise the MCP server.
- The AI agent is a potential adversary!
  AI agents can hallucinate and freak out, deleting production resources.
  AI agents can be manipulated through malicious prompts.
- MCP servers are not web servers!
  Do not blindly regurgitate concepts from the web application world and call that an audit.
  Focus on the real risks mentioned in the document.

** I can't stress this enough: Think about how MCP servers are actually deployed and used in your audit. **


## Conduct the audit
1.  Create a new folder for the audit in `repos/external/audit-db`.
2.  Follow the instructions and examples to conduct the audit.
    **Important points:**
    - Add a metadata.json in the server's root folder `repos/external/audit-db/audits/[domain]/[org]/[repo]`.
3.  Commit your audit findings.