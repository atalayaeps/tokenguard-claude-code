# TokenGuard — Claude Code Token Savings Kit

## Rules

### 1. CHECK FIRST
Before implementing anything, verify existing code with grep/read. Never assume something doesn't exist. A 100-token search prevents a 70K-token reimplementation.

### 2. GREP > AGENT
Use Grep or Read directly (~100 tokens) instead of launching exploration subagents (~40K tokens). Search first, explore only if search fails.

### 3. ONE AT A TIME
Build one module, test it, verify it works. Never accumulate multiple changes without testing. Each untested assumption compounds into expensive rollbacks.

### 4. ONLY WHAT'S ASKED
Do exactly what was requested. A bug fix is not an invitation to refactor three files. A simple feature doesn't need extra configurability or documentation changes.
