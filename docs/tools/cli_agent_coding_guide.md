# CLI Agent Coding Guide (Claude Code, Codex, Cursor, etc.)

Goal: Turn AI IDEs and CLI agents into reliable “shoot-and-forget” helpers for real projects, using patterns inspired by Claude Code’s feature set.

---

## 1. Core Philosophy

1. Treat the agent as a teammate that owns a task end-to-end. Judge it by the final PR, not the vibe of the chat.:contentReference[oaicite:0]{index=0}  
1. Keep a small, curated “constitution” file in the repo (like `CLAUDE.md`) with guardrails and pointers, not a full manual.:contentReference[oaicite:1]{index=1}  
1. Prefer simple CLIs and scripts over complex, brittle tool graphs. Let the agent write glue code and scripts as needed.:contentReference[oaicite:2]{index=2}  
1. Use logs, settings, and GH Actions as feedback loops to refine your tools and docs over time.:contentReference[oaicite:3]{index=3}  

---

## 2. Project “Constitution” (`CLAUDE.md` / `AGENTS.md`)

Use a single root file as the primary contract between your repo and any coding agent.

### 2.1 Purpose

1. Define how this repo works at a high level.  
1. Document only the tools and flows that many engineers actually use (for example, ≥30%).:contentReference[oaicite:4]{index=4}  
1. Act as a forcing function: if a tool needs a page of explanation, fix the tool (simplify the CLI) instead of bloating the doc.:contentReference[oaicite:5]{index=5}  

### 2.2 Content Guidelines

1. Start with guardrails and recurring mistakes, not an exhaustive manual.:contentReference[oaicite:6]{index=6}  
1. Don’t `@`-embed large docs into this file. Instead:
   1. Explain when to read a specific doc.
   1. Link it by path and describe the trigger (for example, “On `FooBarError`, see `docs/foo/troubleshooting.md`.").:contentReference[oaicite:7]{index=7}  
1. Avoid bare “never do X” rules. Always pair them with a recommended alternative (for example, “Never use `--foo`; use `baz run` instead.”).:contentReference[oaicite:8]{index=8}  
1. Mirror this file to `AGENTS.md` (or similar) so other AI IDEs can reuse the same guidance.:contentReference[oaicite:9]{index=9}  

---

## 3. Context Management Workflows

Use explicit workflows instead of trusting opaque auto-compaction.

### 3.1 Inspect Context

1. Run the tool’s “context inspector” (for Claude: `/context`) mid-session to see where the context window is going.:contentReference[oaicite:10]{index=10}  
1. Treat context like disk space: you have a baseline cost for repo metadata, then working space for your change.

### 3.2 Simple Restart: Clear and Catch Up

1. Use a “clear” command to wipe chat history (for Claude: `/clear`).:contentReference[oaicite:11]{index=11}  
1. Immediately run a “catch up” command that:
   1. Reads all files changed in your current branch.
   1. Re-establishes what you are working on.:contentReference[oaicite:12]{index=12}  

### 3.3 Document & Clear (For Large Tasks)

1. Ask the agent to dump its current plan and progress into a `.md` file.  
1. Clear the session.  
1. Start a new session by:
   1. Having it read the summary `.md`.
   1. Continuing from there.:contentReference[oaicite:13]{index=13}  

Avoid auto-compaction if you can; keep resets explicit and documented.

---

## 4. Commands, Subagents, and Delegation

### 4.1 Custom Slash Commands

Use them as shortcuts, not a second programming language.

1. Keep a minimal set of commands (for example, `/catchup`, `/pr`).:contentReference[oaicite:14]{index=14}  
1. Avoid long, complex command catalogs that users have to memorize. If you need a lot of ceremony, your core flows and docs probably need to be simplified.:contentReference[oaicite:15]{index=15}  

### 4.2 Subagents vs. Clones

Be careful when hiding context behind specialized subagents.

1. Subagents can gatekeep context (tests, deploy instructions) from the main agent. It now has to call a subagent just to understand how to validate its own work.:contentReference[oaicite:16]{index=16}  
1. Subagents hard-code human workflows; you’re telling the agent exactly how to delegate, which reduces flexibility.:contentReference[oaicite:17]{index=17}  
1. Prefer “master-clone” style:
   1. Put all key context into `CLAUDE.md` / `AGENTS.md`.
   1. Let the main agent spawn clones (for Claude: `Task(...)` / `Explore(...)`) to parallelize work.:contentReference[oaicite:18]{index=18}  

---

## 5. Sessions, Hooks, and Planning

### 5.1 Resume & History

1. Use resume/continue features to:
   1. Reboot a crashed session.
   1. Ask “what did we do here?” days later.:contentReference[oaicite:19]{index=19}  
1. Periodically analyze raw session logs for:
   1. Common exceptions.
   1. Repeated permission prompts.
   1. Error patterns that should be fixed in tools or docs.:contentReference[oaicite:20]{index=20}  

### 5.2 Hooks (Guardrails at Commit Time)

1. Use hooks as deterministic rules that complement the softer guidance in `CLAUDE.md`.:contentReference[oaicite:21]{index=21}  
1. Prefer **block-at-submit** hooks:
   1. Wrap `git commit` (or equivalent) with a hook that:
      - Runs tests or checks.
      - Only allows commit after everything passes.:contentReference[oaicite:22]{index=22}  
1. Use **hint hooks** to give non-blocking feedback for suboptimal behavior.:contentReference[oaicite:23]{index=23}  
1. Avoid blocking mid-edit. Let the agent finish its plan, then validate the final diff at commit time.:contentReference[oaicite:24]{index=24}  

### 5.3 Planning Mode

1. Always use planning mode (or equivalent) for large changes.:contentReference[oaicite:25]{index=25}  
1. For small projects, rely on the built-in planner to:
   1. Agree on a design.
   1. Define checkpoints where the agent must stop and show progress.:contentReference[oaicite:26]{index=26}  
1. For bigger orgs, consider a custom planning tool that:
   1. Outputs plans in your internal design format.
   1. Bakes in privacy, security, and architectural best practices.:contentReference[oaicite:27]{index=27}  

---

## 6. Skills, MCP, and Scripting

### 6.1 Skills as Scripting Abstractions

1. Think in three layers of autonomy:
   1. Single Prompt – all context in one mega prompt (brittle).  
   1. Tool Calling – many small tools that mimic APIs (better, but can be rigid).  
   1. Scripting – give access to binaries/scripts; agent writes code to orchestrate them.:contentReference[oaicite:28]{index=28}  
1. Skills are a clean way to package the scripting layer: a discoverable catalog of CLIs and scripts, documented in something like `SKILL.md`.:contentReference[oaicite:29]{index=29}  

### 6.2 MCP as a Secure Gateway

1. Don’t mirror full REST APIs into MCP with dozens of near-duplicate tools.:contentReference[oaicite:30]{index=30}  
1. Use MCP for what actually needs a secure boundary:
   1. Download raw or sensitive data.
   1. Perform gated actions.
   1. Run code inside a controlled environment.:contentReference[oaicite:31]{index=31}  
1. Keep MCP tools few and high-level; let scripting and skills handle the rest of the workflow.:contentReference[oaicite:32]{index=32}  

---

## 7. SDK, Automation, and GitHub Actions

### 7.1 SDK as an Agent Framework

Use the agent SDK (for example, Claude Code SDK) when you need more than interactive chat.

1. Batch / parallel edits:
   1. Write scripts that call the CLI with focused prompts (for example, “in /pathA, change all refs from foo to bar”), running multiple tasks in parallel.:contentReference[oaicite:33]{index=33}  
1. Internal chat tools:
   1. Wrap complex processes in simple chat UIs for non-technical users.
   1. Use the SDK to handle “try normal installer; on error, let the agent fix it”.:contentReference[oaicite:34]{index=34}  
1. Rapid agent prototyping:
   1. Prototype new agents (for security, data analysis, ops, etc.) with the SDK before committing to a full platform.:contentReference[oaicite:35]{index=35}  

### 7.2 GitHub Action Integration

1. Run the agent in CI via a GitHub Action:
   1. Full control over container and environment.
   1. Strong sandboxing and auditability.:contentReference[oaicite:36]{index=36}  
1. Build “PR-from-anywhere” flows:
   1. Trigger via Slack, Jira, alerts, etc.
   1. Let the GHA run the agent to produce a tested PR.:contentReference[oaicite:37]{index=37}  
1. Mine GHA logs:
   1. Regularly query agent logs for recurring mistakes.
   1. Feed insights back into `CLAUDE.md`, skills, and CLIs.:contentReference[oaicite:38]{index=38}  

---

## 8. Settings and Advanced Tuning

Maintain a `settings.json` (or equivalent) for agent and network behavior.

1. Proxies:
   1. Use `HTTPS_PROXY` / `HTTP_PROXY` for debugging raw traffic or sandboxing background agents.:contentReference[oaicite:39]{index=39}  
1. Timeouts:
   1. Increase tool/bash timeouts if you routinely run long commands.:contentReference[oaicite:40]{index=40}  
1. API Keys:
   1. Prefer centralized, usage-based API keys (enterprise-style) over per-seat keys when possible.:contentReference[oaicite:41]{index=41}  
1. Permissions:
   1. Periodically audit the list of commands the agent may auto-run. Tighten or expand as workflows evolve.:contentReference[oaicite:42]{index=42}  

---

## 9. Quick Checklist

- [ ] Root-level “constitution” file (`CLAUDE.md` / `AGENTS.md`) with guardrails and main flows.  
- [ ] Clear context workflows: inspect, clear, catch up, document & clear.  
- [ ] Minimal, meaningful slash commands; no giant command catalogs.  
- [ ] Hooks that enforce testing and checks at commit time, not mid-edit.  
- [ ] Planning mode (or equivalent) used for all large changes.  
- [ ] Skills and CLIs documented as a scripting layer; MCP used only as a secure data/action gateway.  
- [ ] SDK and GH Actions integrated for batch edits, internal tools, and PR automation.  
- [ ] `settings.json` (or equivalent) maintained for proxies, timeouts, keys, and permissions.
