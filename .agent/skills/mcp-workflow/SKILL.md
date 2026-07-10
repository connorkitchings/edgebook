---
name: mcp-workflow
description: "Use MCP (Model Context Protocol) servers with fallback CLI commands when servers are offline."
metadata:
  trigger-keywords: "mcp, model context protocol, deployment, server, railway, vercel"
  trigger-patterns: "^mcp, ^deployment, ^deploy, ^railway, ^vercel"
---

# MCP Workflow Skill

Use MCP (Model Context Protocol) servers for tool integration with fallback CLI commands when servers are offline.

---

## When to Use

- Deploying to cloud platforms (Railway, Vercel, etc.)
- Managing infrastructure via MCP
- Automating workflows with MCP tools
- Checking service status

**Do NOT use when:**
- MCP servers are confirmed offline (use CLI fallbacks)
- Simple local operations (use direct commands)

---

## Inputs

### Required
- MCP server: Which server to use (railway, vercel, sentry)
- Operation: What action to perform
- Target: Project/service to operate on

### Optional
- Fallback: Whether to use CLI fallback
- Parameters: Operation-specific parameters

---

## Steps

### Step 1: Check MCP Status

**What to do:**
Verify MCP server availability before starting.

**Pattern:**
```text
Always check .agent/CONTEXT.md or .codex/MCP.md for MCP status:
- Server: online/offline
- Last checked: timestamp
- Fallback available: yes/no
```

**Example Context Entry:**
```markdown
## MCP Status (Feb 2026)

**Railway MCP**: Offline (site intentionally offline)
**Vercel MCP**: Offline (site intentionally offline)
**Sentry MCP**: Offline (site intentionally offline)

Use CLI fallbacks for all operations.
```

### Step 2: Choose Approach

**What to do:**
Select MCP or CLI based on status.

**Decision Tree:**
```
Is MCP server available?
├── Yes → Use MCP commands
│   └── More powerful, integrated context
└── No → Use CLI fallback
    └── Standard CLI commands
```

### Step 3: MCP Operations (If Online)

**What to do:**
Use MCP server for operations.

**Example Operations:**

```python
# Railway MCP examples
railway.up()           # Deploy
railway.logs()         # View logs
railway.status()       # Check status

# Vercel MCP examples
vercel.deploy()        # Deploy frontend
vercel.env.set()       # Set environment variable
vercel.domains.list()  # List domains

# Sentry MCP examples
sentry.issues.list()   # List issues
sentry.releases.create() # Create release
```

### Step 4: CLI Fallbacks (If Offline)

**What to do:**
Use standard CLI commands when MCP unavailable.

**Railway CLI:**
```bash
# Deploy
railway up

# View logs
railway logs

# Environment variables
railway variables
railway variables set KEY=value

# Status
railway status

# Connect to service
railway connect
```

**Vercel CLI:**
```bash
# Deploy
vercel --prod

# Environment variables
vercel env add KEY
vercel env ls

# Domains
vercel domains ls

# Logs
vercel logs

# List deployments
vercel ls
```

**Sentry CLI:**
```bash
# Create release
sentry-cli releases new $VERSION

# Upload source maps
sentry-cli releases files $VERSION upload-sourcemaps ./dist

# Finalize release
sentry-cli releases finalize $VERSION

# List issues
sentry-cli issues list
```

### Step 5: Verify Operation

**What to do:**
Confirm operation completed successfully.

**Verification:**
```bash
# Check deployment status
railway status
vercel ls

# Check logs for errors
railway logs --tail
vercel logs

# Test endpoint
curl https://your-app-url/health
```

---

## Validation

### Success Criteria
- [ ] MCP status checked before operation
- [ ] Appropriate method chosen (MCP or CLI)
- [ ] Operation completed without errors
- [ ] Status verified after operation
- [ ] Any issues documented

### Verification Commands
```bash
# Check service status
railway status
vercel ls

# Check health endpoint
curl https://your-app.up.railway.app/health

# Check logs
railway logs --tail 50
```

---

## Rollback

### If Deployment Fails

**Railway:**
```bash
# View previous deployments
railway deployments

# Rollback to previous
railway rollback <deployment-id>

# Or redeploy
railway up
```

**Vercel:**
```bash
# List deployments
vercel ls

# Promote previous deployment
vercel --prod <deployment-url>
```

---

## Common Mistakes

1. **Not checking MCP status**: Always verify before starting
2. **Wrong CLI version**: Ensure CLI is installed and up to date
3. **Missing auth**: Log in to CLI first (`railway login`, `vercel login`)
4. **Wrong project**: Verify correct project is selected
5. **No verification**: Always check deployment succeeded

---

## Related Skills

- **Database Migration**: If deployment includes migrations
- **Release Checklist**: For production deployment process
- **Test CI**: For CI/CD workflows

---

## Links

- **Context**: `.agent/CONTEXT.md`
- **Agent Guidance**: `.agent/AGENTS.md`
- **MCP Docs**: `.codex/MCP.md`
- **Railway Docs**: https://docs.railway.app/
- **Vercel Docs**: https://vercel.com/docs

---

## Examples

### Example 1: Deploy with Fallback

**Scenario:** Deploy backend to Railway, MCP offline.

**Steps:**
1. Check MCP status → Offline
2. Use CLI: `railway up`
3. Monitor logs: `railway logs --tail`
4. Verify: `curl https://app.up.railway.app/health`

### Example 2: Set Environment Variables

**Scenario:** Add database URL to Railway.

**MCP (if online):**
```python
railway.env.set("DATABASE_URL", "postgresql://...")
```

**CLI Fallback:**
```bash
railway variables set DATABASE_URL="postgresql://..."
railway variables  # Verify
```

---

**Remember: Always have a fallback plan for MCP operations!**
